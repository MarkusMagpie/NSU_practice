from flask import Flask, render_template, request, jsonify
import networkx as nx
from graph_to_graph_state2 import GraphState
import numpy as np
from qutip import Qobj

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
    data = request.get_json()
    n = data['n']  # число кубитов
    signs = data['signs']  # список знаков амплитуд например длины 2^n
    # амплитуды: 1/sqrt(2^n) * (+1 или -1)
    norm = 1.0 / np.sqrt(2**n)
    amplitudes = [norm * (1 if s == '+' else -1) for s in signs]
    is_graph, found_state = GraphState.from_amplitudes(amplitudes)
    
    if is_graph:
        return jsonify({'is_graph': True, 'edges': found_state.edges})
    else:
        return jsonify({'is_graph': False, 'edges': None})
    
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



if __name__ == '__main__':
    app.run(debug=True)