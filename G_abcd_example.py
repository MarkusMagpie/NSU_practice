from qutip import basis, tensor, ket2dm, ptrace, partial_transpose
import numpy as np

# generate |0> and |1> states in 2-dimensional Hilbert space
# два базисных состояния кубита
q0 = basis(2, 0)
q1 = basis(2, 1)

def check_eigenvalues(sub_evals):
    print("проверка условий собственных значений (>=0 && sum=1):")
    if any(ev < 0 for ev in sub_evals) or abs(sum(sub_evals) - 1) > 1e-6:
        print("ошибка в собственных значениях!")
    else:
        print("собственные значения верны!")

def entropy(sub_evals):
    res = 0
    for ev in sub_evals:
        if ev != 0:
            res += ev * np.log2(ev)
    if res != 0:
        res *= -1
    return res

# построение вектора квантового состояния |psi> для 4 кубитов в форме G_abcd
def build_g_abcd(a, b, c, d):
    #тензорным произведением объединяю |0> и |1> в состояния |0000>, |1111>, |0011>, |1100>, |0101>, |1010>, |0110>, |1001>
    _0000 = tensor(q0, q0, q0, q0)
    _1111 = tensor(q1, q1, q1, q1)
    _0011 = tensor(q0, q0, q1, q1)
    _1100 = tensor(q1, q1, q0, q0)
    _0101 = tensor(q0, q1, q0, q1)
    _1010 = tensor(q1, q0, q1, q0)
    _0110 = tensor(q0, q1, q1, q0)
    _1001 = tensor(q1, q0, q0, q1)

    coeff_ad_plus = (a + d) / 2.0
    coeff_ad_minus = (a - d) / 2.0
    coeff_bc_plus = (b+c) / 2.0
    coeff_bc_minus = (b-c) / 2.0

    # линейная комбинация восьми базисных векторов
    psi = (coeff_ad_plus * (_0000 + _1111) +
           coeff_ad_minus * (_0011 + _1100) +
           coeff_bc_plus * (_0101 + _1010) +
           coeff_bc_minus * (_0110 + _1001))

    # деление пси на норму - нормализация
    psi = psi.unit()

    return psi



# коэффициенты
a = float(1)
b = float(0)
c = float(0)
d = float(0)

psi = build_g_abcd(a, b, c, d)
amps = psi.full().flatten() # извлечение амплитуд из вектора |psi>. Получаю одномерный массив из 16 элементов
# rho - объект Qobj 16x16
rho = ket2dm(psi)  # преобразование веткора состояния |psi> в матрицу плотности |psi><psi|

print("Амплитуды:")
non_zero_indices = np.where(np.abs(amps) > 0)[0]
for i in non_zero_indices:
    print(f"|{bin(i)[2:].zfill(4)}>: {amps[i]}")

# вывод матрицы плотности |psi><psi|
print("\ndensity matrix:")
print(rho.full())
print("Trace rho:", np.real(np.trace(rho.full())))

# np.savetxt('rho.txt', rho.full())



# проверка полной сепарабельности
tol = 1e-9
single_entropies = []
is_fully_separable = False
for qubit in range(4):
    rho_i = ptrace(rho, [qubit]) # reduced density matrix for 1 qubit
    ev = rho_i.eigenenergies() # собственные значения одноместной редукции
    s = entropy(ev) # моя катстомная функция вычисления энтропии фон Неймана
    single_entropies.append(s)

print("\nПроверка энтропий запутанности отдельных кубитов:", np.round(single_entropies, 12))
if all(abs(s) < tol for s in single_entropies):
    is_fully_separable = True
else:
    print("Состояние не полностью сепарабельно (есть квантовые корреляции).")

if is_fully_separable:
    print("\nКлассификация: полностью сепарабельное состояние. Пропускаю дальнейшую проверку.")
else:



    # теперь - какая запутанность? Вычисляю приведенные матрицы плотностей для пар кубитов
    # индексы кубитов: 0=A, 1=B, 2=C, 3=D
    subsystems = {
        'AB': [0, 1],
        'AC': [0, 2],
        'AD': [0, 3],
        'BC': [1, 2],
        'BD': [1, 3],
        'CD': [2, 3]
    }

    entangled_count = 0

    for name, indices in subsystems.items():
        # reduced density matrix для подсистемы из 2 кубитов (4x4 Qobj)
        sub_rho = ptrace(rho, indices)
        
        # собственные значения reduced density matrix (>=0 && sum=1)
        sub_evals = sub_rho.eigenenergies() # массив собственных значений
        print(f"\nподсистема {name}:")
        print("собственные значения:")
        print(sub_evals)
        check_eigenvalues(sub_evals)
        ent = entropy(sub_evals)
        print(f"энтропия запутанности: {ent}")
        
        # partial transpose по второму кубиту в паре (маска [0,1] значит транспонировать по 2 кубиту)
        sub_pt = partial_transpose(sub_rho, [0, 1])
        
        # собственные значения partial transpose
        pt_evals = sub_pt.eigenenergies()
        print("собственные значения partial transpose:")
        print(pt_evals)
        
        # PPT
        if any(ev < 0 for ev in pt_evals):
            print(f"подсистема {name} запутанна (отрицательные eigenvalues в PT)!")
            entangled_count += 1
        else:
            print(f"подсистема {name} не запутанна.")

    print("\nКлассификация:")
    if entangled_count == len(subsystems):
        print("Все подсистемы запутанны -> состояние W-type.")
    else:
        print(f"Запутанных подсистем: {entangled_count}/{len(subsystems)} -> состояние GHZ-type.")