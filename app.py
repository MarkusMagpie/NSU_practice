from flask import Flask, render_template, request, jsonify
import networkx as nx
from graph_to_graph_state2 import GraphState
import numpy as np
from qutip import Qobj
from entanglement_algorithm import check_separable_signs, visualize_separability
import matplotlib.pyplot as plt

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/build_state', methods=['POST'])
def build_state():
    data = request.get_json()
    vertices = data['vertices'] # пример сипска: [1,2,3,4]
    edges = data['edges'] # [(1,2),(2,3)]
    gs = GraphState(vertices, edges)
    amps = gs.get_amplitudes()
    
    # возвращаю все амплитуды
    return jsonify({
        'amplitudes': [str(a) for a in amps],
        'edges': edges,
        'vertices': vertices
    })

@app.route('/schmidt_ranks', methods=['POST'])
def schmidt_ranks():
    data = request.get_json()
    vertices = data['vertices']
    edges = data['edges']
    gs = GraphState(vertices, edges)
    rank_list = gs.schmidt_rank_list()
    max_rank = gs.max_schmidt_rank()

    return jsonify({'rank_list': rank_list, 'max_rank': max_rank})

@app.route('/check_graph')
def check_graph():
    return render_template('check_graph.html')

@app.route('/check_graph_submit', methods=['POST'])
def check_graph_submit():
    try: 
        data = request.get_json()
        n = data['n']  # число кубитов
        signs = data['signs']  # список знаков амплитуд например длины 2^n
        # амплитуды: 1/sqrt(2^n) * (+1 или -1)
        if '0' in signs:
            return jsonify({'is_graph': False, 'edges': None})
        
        norm = 1.0 / np.sqrt(2**n)
        amplitudes = [norm if s == '+' else -norm for s in signs]
        is_graph, found_state = GraphState.from_amplitudes(amplitudes)
        
        if is_graph:
            edges = [list(edge) for edge in found_state.edges]
            return jsonify({'is_graph': True, 'edges': edges})
        else:
            return jsonify({'is_graph': False, 'edges': None})
    except Exception as e: 
        print("Error in check_graph_submit:", e)
        import traceback
        traceback.print_exc()
        return jsonify({'is_graph': False, 'edges': None}), 500
    
@app.route('/check_stabilizer')
def check_stabilizer():
    return render_template('check_stabilizer.html')

@app.route('/check_stabilizer_submit', methods=['POST'])
def check_stabilizer_submit():
    data = request.get_json()
    n = data['n']
    signs = data['signs']  # список +/-/0
    nonzero_count = sum(1 for s in signs if s != '0')
    if nonzero_count == 0:
        return jsonify({'is_stabilizer': False, 'reason': 'Все амплитуды нулевые'})
    norm = 1.0 / np.sqrt(nonzero_count)
    amplitudes = []
    for s in signs:
        if s == '+':
            amplitudes.append(norm)
        elif s == '-':
            amplitudes.append(-norm)
        else:
            amplitudes.append(0.0)
    psi = Qobj(amplitudes, dims=[[2]*n, [1]*n])
    vertices = list(range(1, n+1))
    result = GraphState.is_stabilizer_state_detailed(psi, vertices)

    return jsonify(result)

@app.route('/check_separable')
def check_separable():
    return render_template('check_separable.html')

@app.route('/check_separable_submit', methods=['POST'])
def check_separable_submit():
    data = request.get_json()
    n = data['n']
    signs_str = data['signs'] # список строк '+', '-', '0'
    signs = []
    for s in signs_str:
        if s == '+':
            signs.append(1)
        elif s == '-':
            signs.append(-1)
        else:
            signs.append(0)
    is_sep, mismatches, t = check_separable_signs(signs, n)

    # Генерируем пирамиду в виде изображения (base64 или сохраняем временный файл)
    import io
    import base64
    fig = visualize_separability(signs, t, n, return_fig=True) # модифицируем функцию
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode()
    plt.close(fig)
    return jsonify({
        'is_separable': is_sep,
        't': t,
        'mismatches': mismatches,
        'image': img_base64
    })



if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=True)