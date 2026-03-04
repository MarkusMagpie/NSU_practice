import csv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from qutip import basis, tensor, expand_operator, Qobj
from qutip.qip.operations import cnot, hadamard_transform
from collections import defaultdict, deque



def cnot_manual():
    return Qobj([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dims=[[2,2],[2,2]])



class GraphState:
    def __init__(self, vertices, edges):
        self.vertices = list(vertices)
        self.edges = list(edges)
        self.validate_input()
        self.state_vector = None
        
        self.build()

    def validate_input(self):
        vert_set = set(self.vertices)
        for u, v in self.edges:
            if u not in vert_set or v not in vert_set:
                raise ValueError(f"ребро ({u}, {v}) содержит вершину, которая отсутствует в списке вершин")

    # на выходе имею список списков вершин, где каждый подсписок это компонента связности
    def find_connected_components(self):
        adj = defaultdict(list)
        for u, v in self.edges:
            adj[u].append(v)
            adj[v].append(u)

        visited = set()
        components = []
        
        for v in self.vertices:
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

    # графовое состояние одной связной компоеннты
    def build_single_component(self, vertices, edges):
        N = len(vertices) # сколько вершин
        # generate |0> and |1> states in 2-dimensional Hilbert space
        # два базисных состояния кубита
        q0 = basis(2, 0)
        q1 = basis(2, 1)
        # начальное состояние: |+> 
        plus = (q0 + q1).unit()
        # тензорное произведение начальных состоянийй: |+>^{⊗N}
        psi = tensor([plus] * N)
        dims = [2] * N  # размерности всех кубитов (у всех 2) - параметр для функции expand_operator()

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

    # стройит тензорное произведение состояний для графа с несколькими компонентами связности
    def build_tensor_product(self, components):
        comp_states = [] # состояния компонент
        current_order = [] # порядок вершин после тензорного произведения

        for comp in components:
            # ребра внутри компоненты
            comp_edges = []
            for (u, v) in self.edges:
                if u in comp and v in comp:
                    comp_edges.append((u, v))
            state = self.build_single_component(comp, comp_edges)
            comp_states.append(state)
            current_order.extend(comp)

        psi_temp = tensor(comp_states)

        # перестановка к исходному порядку
        perm=[]
        for v in self.vertices:
            perm.append(current_order.index(v))
        psi = psi_temp.permute(perm) # Permutes the tensor structure of a composite object in the given order (perm)
        return psi

    def build(self):
        components = self.find_connected_components()

        if len(components) == 1:
            self.state_vector = self.build_single_component(self.vertices, self.edges)
        else:
            print("граф содержит несколько компонент связности:")
            for i, comp in enumerate(components):
                print(f"компонента {i+1}: {comp}")
            print()

            self.state_vector = self.build_tensor_product(components)



    # массив коплексных амплитуд в порядке базисных состояний QuTiP
    def get_amplitudes(self):
        if self.state_vector is None:
            return None
        return self.state_vector.full().flatten()

    # сохранялка в csv файл всех базисных состояний
    def save_amplitudes(self, filename):
        if self.state_vector is None:
            raise RuntimeError("состояние не построено")

        N = int(np.log2(len(self.state_vector.full())))
        amps = self.state_vector.full().flatten() # извлечение амплитуд из вектора |psi>. Получаю одномерный массив из 2^N элементов
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['basis', 'amplitude'])
            for b in range(2**N):
                basis_str = format(b, '0{}b'.format(N))
                writer.writerow([basis_str, amps[b]])

    # визуализация входного графа
    def visualize(self, filename=None):
        G = nx.Graph()
        G.add_nodes_from(self.vertices)
        G.add_edges_from(self.edges)

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



if __name__ == '__main__':
    # V = [1, 2, 3, 4]
    # E = [(1, 2), (2, 3), (3, 4)]
    V = [1, 2, 3, 4, 5, 6]
    E = [(1, 2), (2, 3), (4, 5), (5, 6)]

    # экземпляр класса
    gs = GraphState(V, E)
    gs.visualize(filename='input_graph.png')
    gs.save_amplitudes('graph_state_via_gates.csv')
    print("Вероятностные амплитуды сохранены в graph_state_via_gates.csv")

    # можно получить массив амплитуд отдельно при необходимости геттером
    amps = gs.get_amplitudes()
    print("полученные вероятностные амплитуды: \n", amps)