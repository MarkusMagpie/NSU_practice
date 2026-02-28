import csv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from qutip import basis, tensor, expand_operator, Qobj
from qutip.qip.operations import cnot, hadamard_transform

def cnot_manual():
    return Qobj([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dims=[[2,2],[2,2]])

def visualize_input_graph(vertices, edges, filename=None):
    G = nx.Graph()
    G.add_nodes_from(vertices)
    G.add_edges_from(edges)

    plt.figure(figsize=(8, 6))
    pos = nx.spring_layout(G, seed=42)

    nx.draw_networkx_nodes(G, pos, node_size=800, node_color='lightblue', edgecolors='black')
    nx.draw_networkx_edges(G, pos, width=2, edge_color='gray')
    nx.draw_networkx_labels(G, pos, font_size=14, font_weight='bold')

    plt.title("Входной граф", fontsize=16)
    plt.axis('off')

    if filename:
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"Граф сохранён в файл: {filename}")

    plt.show()

# на выходе имею список списков вершин, где каждый подсписок это компонента связности
def find_connected_components(vertices, edges):
    from collections import defaultdict, deque
    adj = defaultdict(list)
    for u, v in edges:
        adj[u].append(v)
        adj[v].append(u)

    visited = set()
    components = []
    
    for v in vertices:
        if v not in visited:
            # BFS
            # https://www.geeksforgeeks.org/dsa/breadth-first-search-or-bfs-for-a-graph/
            queue = deque([v])
            comp = []
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                comp.append(node)
                # добавляю непосещенных ссодев в очередь 
                for nei in adj[node]:
                    if nei not in visited:
                        queue.append(nei)
            components.append(comp)
    return components

def build_graph_state_with_gates(vertices, edges):
    N = len(vertices) # сколько вершин
    # generate |0> and |1> states in 2-dimensional Hilbert space
    # два базисных состояния кубита
    q0 = basis(2, 0)
    q1 = basis(2, 1)
    # начальное состояние: |+> 
    plus = (q0 + q1).unit()
    # тензорное произведение начальных состоянийй: |+>^{⊗N}
    psi = tensor([plus] * N)
    dims = [2] * N  # размерности всех кубитов (у всех 2) - для функции expand_operator()

    # для каждого ребра буду применять H*Cnot*H
    for a, b in edges:
        # индексы кубитов на которых нужно применить гейты
        i = vertices.index(a)
        j = vertices.index(b)

        H = hadamard_transform() # 2*2 матрица Адамара
        # https://qutip.org/docs/4.5/apidoc/functions.html#qutip.qip.gates.expand_operator
        H_j = expand_operator(H, dims, j) # расширяю H на N кубитов, чтобы он действовал только на кубит с индексом j

        CNOT_ij = cnot() # 4*4 матрица CNOT (управляющий кубит i, контролирующий кубит j) 
        CNOT_full = expand_operator(CNOT_ij, dims, [i, j])  # расширяю Cnot на N кубитов, чтобы он действовал только на кубиты i, j

        """
        последовательно применяю операторы к текущему состоянию psi. Сначала H на j, затем CNOT на паре (i,j), затем снова H на j. 
            Это эквивалентно применению U_{ij} к текущему состоянию        
        """
        psi = H_j * psi
        psi = CNOT_full * psi
        psi = H_j * psi

    return psi

# стройит состояние для графа с несколькими компонентами связности
def build_tensor_product_state(components, edges, full_vertices):
    comp_states = [] # состояния компонент
    current_order = [] # порядок вершин после тензорного произведения

    for comp in components:
        # ребра внутри компоненты
        comp_edges = []
        for (u, v) in edges:
            if u in comp and v in comp:
                comp_edges.append((u, v))
        state = build_graph_state_with_gates(comp, comp_edges)
        comp_states.append(state)
        current_order.extend(comp)

    psi_temp = tensor(comp_states)

    # перестановка к исходному порядку
    perm=[]
    for v in full_vertices:
        perm.append(current_order.index(v))
    psi = psi_temp.permute(perm)
    return psi


def build_graph_state(vertices, edges):
    components = find_connected_components(vertices, edges)

    if len(components) == 1:
        return build_graph_state_with_gates(vertices, edges)
    else:
        print("граф содержит несколько компонент связности:")
        for i, comp in enumerate(components):
            print(f"компонента {i+1}: {comp}")
        
        return build_tensor_product_state(components, edges, vertices)

def save_amplitudes(psi, filename):
    N = int(np.log2(len(psi.full())))
    amps = psi.full().flatten() # извлечение амплитуд из вектора |psi>. Получаю одномерный массив из 2^N элементов
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['basis', 'amplitude'])
        for b in range(2**N):
            basis_str = format(b, '0{}b'.format(N))
            writer.writerow([basis_str, amps[b]])



if __name__ == '__main__':
    # V = [1, 2, 3, 4]
    # E = [(1, 2), (2, 3), (3, 4)]
    V = [1, 2, 3, 4, 5, 6]
    E = [(1, 2), (2, 3), (4, 5), (5, 6)]

    visualize_input_graph(V, E, filename='input_graph.png')

    state = build_graph_state(V, E)
    filename='graph_state_via_gates.csv'
    save_amplitudes(state, filename)
    print("амплитуды сохранены в", filename)