import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from graph_to_graph_state2 import GraphState
from itertools import combinations
from collections import defaultdict
from qutip import basis, tensor

def parse_signs_input(n):
    total = 2 ** n
    signs = [1] * total  # signs[0] = +|0^n>
    print(f"Введите фазовые знаки для {total - 1} состояний в лексикографическом порядке (кроме |{'0'*n}>) через пробел (+/-):")
    line = input().strip()
    parts = line.split()
    if len(parts) != total - 1:
        print(f"нужно {total - 1} знаков. Поэтому используем все '+' по умолчанию.")
        return signs
    for i, p in enumerate(parts, start=1):
        signs[i] = 1 if p == '+' else -1
    return signs

def check_separable_signs(signs, n):
    # t_i = знак для состояния с единицей на i-й позиции
    t = [0] * n
    for i in range(n):
        idx = 1 << i
        t[i] = signs[idx]
    
    mismatches = []
    for mask in range(1 << n):
        expected = 1
        for i in range(n):
            if mask & (1 << i):
                expected *= t[i]
                
        if signs[mask] != expected:
            mismatches.append(mask)
    if len(mismatches) == 0:
        return True, mismatches, t
    return False, mismatches, t

# def find_separable_blocks(signs, n):
#     # 1 - t_i = знак для состояния с единицей на i-й позиции
#     t = [0] * n
#     for i in range(n):
#         idx = 1 << i
#         t[i] = signs[idx]

#     # 2 - несовпадающие маски
#     mismatches = []
#     for mask in range(1 << n):
#         expected = 1
#         for i in range(n):
#             if mask & (1 << i):
#                 expected *= t[i]
#         if signs[mask] != expected:
#             mismatches.append(mask)
    
#     # 3 - граф связей для несовпадающих масок
#     adj = defaultdict(set)
#     for mask in mismatches:
#         # биты входящие в mask
#         bits = [i for i in range(n) if mask & (1 << i)]
#         # все пары между этими битами
#         for a, b in combinations(bits, 2):
#             adj[a].add(b)
#             adj[b].add(a)

#     # 4 - компоненты связности
#     visited = [False] * n
#     blocks = []
#     for i in range(n):
#         if not visited[i]:
#             stack = [i]
#             comp = []
#             while stack:
#                 v = stack.pop()
#                 if visited[v]:
#                     continue
#                 visited[v] = True
#                 comp.append(v)
#                 for nb in adj.get(v, []):
#                     if not visited[nb]:
#                         stack.append(nb)
#             # i изолирован
#             if not comp:
#                 comp = [i]
#             blocks.append(sorted(comp))

#     blocks.sort()

#     return blocks

def find_blocks_recursive(signs, indices):
    if len(indices) <= 1:
        return [indices]

    t = {i: signs[1 << i] for i in indices}

    # шаг 1 - несовпадения на уровне пар кубитов
    adj = defaultdict(set)
    for a, b in combinations(indices, 2):
        mask = (1 << a) | (1 << b)
        expected = t[a] * t[b]
        if signs[mask] != expected:
            adj[a].add(b)
            adj[b].add(a)

    visited = set()
    components = []
    for v in indices:
        if v not in visited:
            stack = [v]
            comp = []
            while stack:
                node = stack.pop()
                if node in visited: 
                    continue
                visited.add(node)
                comp.append(node)
                for nb in adj.get(node, []):
                    if nb not in visited:
                        stack.append(nb)
            components.append(comp)
    if not components:
        return [[i] for i in indices]

    # шаг 2 - перестройка решетки - проверка связей между компонентами связности
    comp_masks = [sum(1 << i for i in comp) for comp in components]
    comp_signs = [signs[mask] for mask in comp_masks]

    comp_adj = defaultdict(set)
    for i in range(len(comp_masks)):
        for j in range(i+1, len(comp_masks)):
            combined = comp_masks[i] | comp_masks[j]
            expected = comp_signs[i] * comp_signs[j]
            if signs[combined] != expected:
                comp_adj[i].add(j)
                comp_adj[j].add(i)

    visited_comp = set()
    final_blocks = []
    for i in range(len(components)):
        if i not in visited_comp:
            stack = [i]
            block = []
            while stack:
                node = stack.pop()
                if node in visited_comp: 
                    continue
                visited_comp.add(node)
                block.extend(components[node])
                for nb in comp_adj.get(node, []):
                    if nb not in visited_comp:
                        stack.append(nb)
            final_blocks.append(block)

    if len(final_blocks) == 1 and set(final_blocks[0]) == set(indices):
        return [indices]

    result = []
    for block in final_blocks:
        if len(block) <= 1:
            result.append(block)
        else:
            result.extend(find_blocks_recursive(signs, block))
    return result

def find_partition_blocks(signs, n):
    return find_blocks_recursive(signs, list(range(n)))

"""
signs - список знаков для всех 2^n базисов
t - список однокубитных знаков (длина n)
n - число кубитов
"""
def visualize_separability(signs, t, n, filename=None, return_fig=False):
    # граф где узлы - базисные состояния, ребра - связи между уровнями
    G = nx.Graph()
    levels = [[] for _ in range(n+1)]

    for mask in range(2**n):
        w = bin(mask).count('1')
        levels[w].append(mask)
        G.add_node(mask, weight=w, sign=signs[mask], expected=1)
        # ожидаемый знак
        exp = 1
        for i in range(n):
            if mask & (1 << i):
                exp *= t[i]
        G.nodes[mask]['expected'] = exp

    # ребра: маска с маской у которой удален один бит 
    for mask in range(2**n):
        w = bin(mask).count('1')
        if w == 0: continue
        for i in range(n):
            if mask & (1 << i):
                parent = mask ^ (1 << i)
                G.add_edge(mask, parent)

    # позиционирование вершин 
    pos = {} # словарь для хранения координат
    for w in range(n+1):
        nodes = levels[w]
        if not nodes: continue
        nodes_sorted = sorted(nodes)
        num = len(nodes_sorted)
        if num == 1:
            x_coords = [0]
        else:
            x_coords = np.linspace(-(num-1)/2, (num-1)/2, num)
        y = w # высота уровня = вес узла
        for i, node in enumerate(nodes_sorted):
            pos[node] = (x_coords[i], y)

    fig = plt.figure(figsize=(10, 8))
    node_colors = []
    for node in G.nodes:
        if G.nodes[node]['sign'] == G.nodes[node]['expected']:
            node_colors.append('lightgreen')
        else:
            node_colors.append('lightcoral')
    nx.draw_networkx_nodes(G, pos, node_size=800, node_color=node_colors, edgecolors='black')
    nx.draw_networkx_edges(G, pos, width=1)

    labels = {mask: f"|{mask:0{n}b}>" for mask in G.nodes}
    nx.draw_networkx_labels(G, pos, labels, font_size=8)
    plt.axis('equal')

    if filename:
        plt.savefig(filename, dpi=150, bbox_inches='tight')
    
    if return_fig:
        return fig
    else:
        plt.show()

def test_find_blocks():
    test_cases = [
        (4, [(1,2),(3,4)], [[0,1],[2,3]]),
        (4, [(1,2),(2,3),(3,4)], [[0,1,2,3]]),
        (4, [], [[0],[1],[2],[3]]),

        (5, [(i,i+1) for i in range(1,5)], [[0,1,2,3,4]]),
        (5, [], [[0],[1],[2],[3],[4]]),

        (6, [(1,2),(3,4),(5,6)], [[0,1],[2,3],[4,5]]),
        (6, [(i,i+1) for i in range(1,6)], [[0,1,2,3,4,5]]),
        (6, [], [[0],[1],[2],[3],[4],[5]]),

        (7, [(i,i+1) for i in range(1,7)], [[0,1,2,3,4,5,6]]),
        (7, [], [[0],[1],[2],[3],[4],[5],[6]]),
    ]

    for n, edges, expected_blocks in test_cases:
        vertices = list(range(1, n+1))
        gs = GraphState(vertices, edges)
        amps = gs.get_amplitudes()
        signs = [1 if a.real > 0 else -1 for a in amps]

        blocks = find_blocks_recursive(signs, list(range(n)))

        blocks_sorted = [sorted(b) for b in blocks]
        expected_sorted = [sorted(b) for b in expected_blocks]

        if sorted(blocks_sorted) == sorted(expected_sorted):
            print(f"тест прошел. n={n}, {edges}: {blocks}")
        else:
            print(f"тест не прошел. n={n}, {edges}: ожидалось {expected_blocks}, получено {blocks}")

    b00 = basis([2,2], [0,0])
    b11 = basis([2,2], [1,1])

    bell_plus = (b00 + b11).unit()
    bell_minus = (b00 - b11).unit()

    state = tensor(bell_plus, bell_minus)
    amps = state.full().flatten()
    signs = [1 if a.real > 0 else -1 for a in amps]

    blocks = find_blocks_recursive(signs, list(range(4)))
    print(blocks)

    b00 = tensor(basis(2,0), basis(2,0))
    b01 = tensor(basis(2,0), basis(2,1))
    b10 = tensor(basis(2,1), basis(2,0))
    b11 = tensor(basis(2,1), basis(2,1))
    bell = (b00 + b01 + b10 - b11).unit()
    state = tensor(bell, bell)
    amps = state.full().flatten()
    signs = [1 if a.real > 0 else -1 for a in amps]
    blocks = find_blocks_recursive(signs, list(range(4)))
    print(blocks) 


def main():
    # gs = GraphState([1,2,3], [(1,2),(2,3)])
    # amps = gs.get_amplitudes()
    # signs3 = [1 if a.real > 0 else -1 for a in amps]
    # print("Знаки:", signs3[1:])

    # gs = GraphState([1,2,3,4], [(1,2),(2,3),(3,4)])
    # amps = gs.get_amplitudes()
    # signs4 = [1 if a.real > 0 else -1 for a in amps]
    # print("Знаки:", signs4[1:])

    # print_signs_for_two_bell_pairs()

    # n = int(input("Введите число кубитов (n от 1 до 7): "))
    # if n < 1 or n > 7:
    #     print("n должно быть от 1 до 7")
    #     return
    # signs = parse_signs_input(n)

    # is_sep, mismatches, t = check_separable_signs(signs, n)
    # print("\nРезультат:")
    # if is_sep:
    #     print("состояние сепарабельно")
    #     print("Разложение на однокубитные состояния:")
    #     for i in range(n):
    #         sign_char = '+' if t[i] == 1 else '-'
    #         print(f"\tкубит {i+1}: |0> + {sign_char}|1>")
    # else:
    #     print("cостояние запутано")
    
    # visualize_separability(signs, t, n, filename="separability_pyramid.png")

    test_find_blocks()

if __name__ == "__main__":
    main()