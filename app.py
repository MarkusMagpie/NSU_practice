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

@app.route('/check_graph_state', methods=['POST'])
def check_graph_state():
    data = request.get_json()
    vertices = data['vertices']
    amplitudes = data['amplitudes']
    amps = np.array(amplitudes, dtype=complex)
    n = len(vertices)
    psi = Qobj(amps, dims=[[2]*n, [1]*n])
    is_graph, found_state = GraphState.is_graph_state(psi, vertices)
    
    if is_graph:
        return jsonify({'is_graph': True, 'edges': found_state.edges})
    else:
        return jsonify({'is_graph': False, 'edges': None})

@app.route('/schmidt_ranks', methods=['POST'])
def schmidt_ranks():
    data = request.get_json()
    vertices = data['vertices']
    edges = data['edges']
    gs = GraphState(vertices, edges)
    rank_list = gs.schmidt_rank_list()
    max_rank = gs.max_schmidt_rank()

    return jsonify({'rank_list': rank_list, 'max_rank': max_rank})



if __name__ == '__main__':
    app.run(debug=True)