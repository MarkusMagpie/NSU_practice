import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from graph_to_graph_state2 import GraphState

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



def main():
    gs = GraphState([1,2,3], [(1,2),(2,3)])
    amps = gs.get_amplitudes()
    signs3 = [1 if a.real > 0 else -1 for a in amps]
    print("Знаки:", signs3[1:])

    gs = GraphState([1,2,3,4], [(1,2),(2,3),(3,4)])
    amps = gs.get_amplitudes()
    signs4 = [1 if a.real > 0 else -1 for a in amps]
    print("Знаки:", signs4[1:])



    n = int(input("Введите число кубитов (n от 1 до 7): "))
    if n < 1 or n > 7:
        print("n должно быть от 1 до 7")
        return
    signs = parse_signs_input(n)

    is_sep, mismatches, t = check_separable_signs(signs, n)
    print("\nРезультат:")
    if is_sep:
        print("состояние сепарабельно")
        print("Разложение на однокубитные состояния:")
        for i in range(n):
            sign_char = '+' if t[i] == 1 else '-'
            print(f"\tкубит {i+1}: |0> + {sign_char}|1>")
    else:
        print("cостояние запутано")
    
    visualize_separability(signs, t, n, filename="separability_pyramid.png")

if __name__ == "__main__":
    main()