import csv
import numpy as np
from qutip import basis, tensor, expand_operator, Qobj
from qutip.qip.operations import cnot, hadamard_transform

def cnot_manual():
    return Qobj([[1,0,0,0], [0,1,0,0], [0,0,0,1], [0,0,1,0]], dims=[[2,2],[2,2]])

def build_graph_state_with_gates(vertices, edges):
    N = len(vertices) # сколько кубитов
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
    V = [1, 2, 3, 4]
    E = [(1, 2), (2, 3), (3, 4)]
    state = build_graph_state_with_gates(V, E)
    filename='graph_state_via_gates.csv'
    save_amplitudes(state, filename)
    print("амплитуды сохранены в", filename)