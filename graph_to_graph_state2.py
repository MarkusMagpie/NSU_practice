import csv
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from qutip import basis, tensor, expand_operator, Qobj
from qutip.qip.operations import cnot, hadamard_transform
from collections import defaultdict, deque
import os



def cnot_manual():
    return Qobj([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dims=[[2,2],[2,2]])

def normalize_edge(u, v):
    return (u, v) if u < v else (v, u)


class GraphState:
    def __init__(self, vertices, edges):
        self.vertices = list(vertices)
        self.edges = [normalize_edge(u, v) for u, v in edges]
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
                print(f"\tкомпонента {i+1}: {comp}")

            self.state_vector = self.build_tensor_product(components)



    # массив коплексных амплитуд в порядке базисных состояний QuTiP
    def get_amplitudes(self):
        if self.state_vector is None:
            return None
        return self.state_vector.full().flatten() # извлечение амплитуд из вектора |psi>. Получаю одномерный массив из 2^N элементов

    # сохранялка в csv файл всех базисных состояний
    def save_amplitudes(self, filename):
        if self.state_vector is None:
            raise RuntimeError("состояние не построено")

        N = int(np.log2(len(self.state_vector.full())))
        amps = self.state_vector.full().flatten()
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['базис', 'амплитуда'])
            for b in range(2**N):
                basis_str = format(b, '0{}b'.format(N))
                writer.writerow([basis_str, amps[b]])

    # визуализация графов (входных/локально дополненных)
    def visualize(self, filename=None, subdir=None, show=True):
        G = nx.Graph()
        G.add_nodes_from(self.vertices)
        G.add_edges_from(self.edges)

        plt.figure(figsize=(8, 6))
        pos = nx.spring_layout(G, seed=42)
        
        nx.draw_networkx_nodes(G, pos, node_size=800, node_color='lightblue', edgecolors='black')
        nx.draw_networkx_edges(G, pos, width=2, edge_color='gray')
        nx.draw_networkx_labels(G, pos, font_size=14, font_weight='normal', font_family='sans-serif')
        
        plt.title("Граф", fontsize=16)
        plt.axis('off')

        if filename:
            if subdir:
                os.makedirs(subdir, exist_ok=True)
                full_path = os.path.join(subdir, filename)
            else:
                full_path = filename
            plt.savefig(full_path, dpi=300, bbox_inches='tight')
            print(f"Граф сохранён в файл: {full_path}")

        if show:
            plt.show()
        else:
            plt.close()

    @staticmethod
    def apply_local_complementation(edges, vertex):
        # сбор соседей вершины vertex
        neighbors = set()
        for u, v in edges:
            if u == vertex:
                neighbors.add(v)
            elif v == vertex:
                neighbors.add(u)

        # новое множество ребер (не инцидентные vertex)
        new_edges = set()
        for u, v in edges:
            if u != vertex and v != vertex:
                new_edges.add((u, v))

        # инвертирование ребер между соседями
        nb_list = list(neighbors)
        for i in range(len(nb_list)):
            for j in range(i+1, len(nb_list)):
                a, b = nb_list[i], nb_list[j]
                e = normalize_edge(a, b)
                if e in new_edges:
                    new_edges.remove(e)
                else:
                    new_edges.add(e)

        # + ребра от vertex к соседям
        for nb in neighbors:
            new_edges.add(normalize_edge(vertex, nb))

        return new_edges

    # создание нового графа полученного локальным дополнением в вершине vertex
    def local_complementation(self, vertex):
        if vertex not in self.vertices:
            raise ValueError("вершина не найдена")
    
        new_edges = self.apply_local_complementation(self.edges, vertex)

        return GraphState(self.vertices, list(new_edges))
    
    # на выходе - orbit_states - список всех graph states LC эквив данному (включая исходное)
    def lc_orbit(self):
        start_edges = frozenset(self.edges) # неизменяемое представление рёбер исходного графа (+ ключ в словаре visited_edges)
        visited_edges = set() # множество уже обработанных ребер
        visited_edges.add(start_edges) 
        queue = [start_edges] # очередь ребер для bfs которые нужно обработать
        orbit_states = [self]

        while queue:
            current_edges = queue.pop(0)
            
            # для каждой вершины применяется локальное дополнение
            for v in self.vertices:
                new_edges_set = self.apply_local_complementation(set(current_edges), v)
                new_edges_frozen = frozenset(new_edges_set)
                
                if new_edges_frozen not in visited_edges:
                    visited_edges.add(new_edges_frozen)
                    queue.append(new_edges_frozen)
                    orbit_states.append(GraphState(self.vertices, list(new_edges_set)))
        return orbit_states
    
    # вычисление ранга Шмидта для подмножества subset над полем F_2
    def schmidt_rank(self, subset):
        # 1
        subset = set(subset)
        complement = set(self.vertices) - subset # множество вершин которые не входят в subset
        if not complement or not subset:
            return 0

        # 2 - построение M = Γ_AB матрицы смежности 
        subset_list = list(subset)
        comp_list = list(complement)

        rows = []
        for a in subset_list:
            row = []
            for b in comp_list:
                if (a, b) in self.edges or (b, a) in self.edges:
                    row.append(1)
                else:
                    row.append(0)
            rows.append(row)

        M = np.array(rows, dtype=int) 

        # 3 - вычисление ранга над F_2 методом Гаусса
        # https://mathprofi.ru/metod_gaussa_dlya_chainikov.html
        row, col = M.shape
        rank = 0
        M = M.copy()
        for c in range(col):
            # поиск строки с 1 в столбце c, начиная с rank
            pivot = None
            for r in range(rank, row):
                if M[r, c] == 1:
                    pivot = r
                    break
            if pivot is None:
                continue

            if pivot != rank:
                M[[rank, pivot]] = M[[pivot, rank]]

            # проход по всем строкам, если в ней в столбце c есть 1, xor с строкой rank -> обнуление единиц в столбце c
            for r in range(row):
                if r != rank and M[r, c] == 1:
                    M[r] ^= M[rank]
            rank += 1

        return rank
    
    # сбор рангов Шмидта для всех возможных разбиений вершин графа на две группы
    # возвращает словарь где ключ - размер меньшей части разбиения, значение - список рангов для всех таких разбиений
    def schmidt_rank_list(self):
        n = len(self.vertices)
        ranks_by_size = defaultdict(list)

        for mask in range(1, (1 << n) - 1):
            # бит i = 1 -> вершина с индексом i входит в подмножество 
            subset_indices = [] # список индексов вершин в подмножестве
            for i in range(n):
                if (mask >> i) & 1:
                    subset_indices.append(i)

            size = len(subset_indices)
            # разбиение (A, B) и (B, A) дают одинаковый ранг Шмидта (ранг матрицы Γ_AB не меняется при транспонировании), 
            # достаточно рассматривать только те подмножества, размер которых не превосходит половины всех вершин
            if size <= n // 2: 
                subset_vertices = []
                for i in subset_indices:
                    subset_vertices.append(self.vertices[i])   
                rank = self.schmidt_rank(subset_vertices)
                ranks_by_size[size].append(rank)

        return dict(ranks_by_size)
    
    def max_schmidt_rank(self):
        rank_dict = self.schmidt_rank_list()
        max_rank = 0
        for ranks in rank_dict.values():
            if ranks:
                max_rank = max(max_rank, max(ranks))
        
        return max_rank



if __name__ == '__main__':
    V = [1, 2, 3, 4, 5, 6]
    E = [(1, 2), (2, 3), (4, 5), (5, 6)]
    # V = [1,2,3,4]
    # E = [(1,2),(2,3),(3,4)]

    # экземпляр класса
    gs = GraphState(V, E)
    gs.visualize(filename='input_graph.png')
    gs.save_amplitudes('graph_state_via_gates.csv')
    print("Вероятностные амплитуды сохранены в graph_state_via_gates.csv")

    # можно получить массив амплитуд отдельно при необходимости геттером
    # amps = gs.get_amplitudes()
    # print("полученные вероятностные амплитуды: \n", amps)

    # orbit = gs.lc_orbit()
    # print(f"найдено {len(orbit)} состояний в LC орбите!")
    # for i, state in enumerate(orbit):
    #     state.visualize(filename=f'lc_orbit_{i}.png', subdir='lc_orbit', show=False)

    rank_list = gs.schmidt_rank_list()
    print("ранги Шмидта для каждого размера меньшей части:")
    for size, ranks in sorted(rank_list.items()):
        print(f"\tразмер {size}: {ranks}")
    max_rank = gs.max_schmidt_rank()
    print(f"максимальный ранг Шмидта: {max_rank}")

    # gs_lc = gs.local_complementation(2)
    # gs_lc.visualize(filename='lc_vertex_2.png', subdir='lc_results', show=True)
    # print("ребра после локального дополнения в вершине 2:", gs_lc.edges)