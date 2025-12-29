import numpy as np

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
    