import numpy as np
from qutip import ptrace, entropy_vn, basis, tensor, partial_transpose
import time

def entropy(sub_evals):
    res = 0
    for ev in sub_evals:
        if ev != 0:
            res += ev * np.log2(ev)
    if res != 0:
        res *= -1
    return res

# проверка чистого состояния psi на полную сепарабельность
def is_fully_separable(psi, tol=1e-8):
    n = int(np.log2(len(psi.full()))) # число кубитов

    for i in range(n):
        rho_i = ptrace(psi, i) # reduced density matrix for i-th qubit
        von_neumann_entropy = entropy_vn(rho_i)
        if von_neumann_entropy > tol:
            # если состояние запутано то ред. матрица хотя бы одного кубита будет смешанной (ранг >1) и ее энтропия будет >0
            return False
        
    return True

# psi_bell = (tensor(basis(2,0), basis(2,0)) + tensor(basis(2,1), basis(2,1))).unit()
# print(is_fully_separable(psi_bell)) # false

# psi_sep = tensor(basis(2,0), (basis(2,0)+basis(2,1)).unit())
# print(is_fully_separable(psi_sep)) # true

def has_entanglement_ppt(psi):
    n = int(np.log2(len(psi.full())))

    for i in range(n):
        for j in range(i+1, n):
            # reduced density matrix для подсистемы из 2 кубитов
            rho_ij = ptrace(psi, [i, j])

            # partial transpose по второму кубиту в паре (маска [0,1] значит транспонировать по 2 кубиту)
            rho_pt = partial_transpose(rho_ij, [0, 1])
            
            # собственные значения partial transpose
            evals = rho_pt.eigenenergies()

            # ppt
            if any(e < 0 for e in evals):
                return True
    
    return False

def has_entanglement_ppt2(psi, use_symmetry=True):
    n = int(np.log2(len(psi.full())))

    def check_pair(i, j):
        rho_ij = ptrace(psi, [i, j])
        rho_pt = partial_transpose(rho_ij, [0, 1])
        evals = rho_pt.eigenenergies()
        return any(e < 0 for e in evals)

    if not use_symmetry:
        for i in range(n):
            for j in range(i+1, n):
                if check_pair(i, j):
                    return True
        return False

    # проверка на симметрию: все ли редуцированные матрицы пар одинаковы
    # матрица для первой пары (0,1)
    ref_rho = ptrace(psi, [0, 1])
    symmetric = True
    for i in range(n):
        for j in range(i+1, n):
            if i == 0 and j == 1:
                continue

            rho_ij = ptrace(psi, [i, j])

            if not np.allclose(ref_rho.full(), rho_ij.full(), atol=1e-8):
                symmetric = False
                break
        if not symmetric:
            break

    if symmetric:
        return check_pair(0, 1)
    else:
        for i in range(n):
            for j in range(i+1, n):
                if check_pair(i, j):
                    return True
        return False
    
def benchmark(psi, use_symmetry):
    start = time.time()
    res = has_entanglement_ppt2(psi, use_symmetry=use_symmetry)
    elapsed = time.time() - start
    return res, elapsed



if __name__ == "__main__":
    n = 7
    zero = basis(2,0)
    one = basis(2,1)
    ghz = (tensor([zero]*n) + tensor([one]*n)).unit()

    # psi_sep = tensor(basis(2,0), (basis(2,0)+basis(2,1)).unit())
    
    res1, t1 = benchmark(ghz, use_symmetry=False)
    print(f"обычный PPT: {res1}, время {t1:.6f}s")

    res2, t2 = benchmark(ghz, use_symmetry=True)
    print(f"симметричный PPT: {res2}, время {t2:.6f}s")