from qutip import basis, tensor, ket2dm, ptrace, partial_transpose
import numpy as np

from quantum_tools import entropy, check_eigenvalues
from database import ExperimentDB

# generate |0> and |1> states in 2-dimensional Hilbert space
q0 = basis(2, 0)
q1 = basis(2, 1)

def build_g_abcd(a, b, c, d):
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

    psi = (coeff_ad_plus * (_0000 + _1111) +
           coeff_ad_minus * (_0011 + _1100) +
           coeff_bc_plus * (_0101 + _1010) +
           coeff_bc_minus * (_0110 + _1001))

    psi = psi.unit()
    return psi

def main():
    db = ExperimentDB()
    experiment_id = None
    
    try:
        a = float(1)
        b = float(0)
        c = float(0)
        d = float(0)
        
        print("="*70)
        print("ЗАПУСК ЭКСПЕРИМЕНТА G_abcd")
        print(f"Параметры: a={a}, b={b}, c={c}, d={d}")
        print("="*70)
        
        # сохранение эксперимента в БД
        parameters = {
            "a": a,
            "b": b,
            "c": c,
            "d": d,
            "state_family": "G_abcd"
        }
        
        experiment_id = db.save_experiment(
            name="Анализ 4-кубитного состояния G_abcd",
            description="генерация состояния и анализ запутанности кубитов",
            parameters=parameters
        )
        
        if experiment_id is None:
            print("не удалось сохранить эксперимент в БД. Продолжаем без сохранения.")
        
        # генерация состояния
        psi = build_g_abcd(a, b, c, d)
        amps = psi.full().flatten()
        rho = ket2dm(psi)
        
        print("\nАмплитуды:")
        non_zero_indices = np.where(np.abs(amps) > 0)[0]
        for i in non_zero_indices:
            print(f"|{bin(i)[2:].zfill(4)}>: {amps[i]}")
        
        print(f"\nСлед матрицы плотности: {np.real(np.trace(rho.full())):.6f}")
        
        # проверка полной сепарабельности
        tol = 1e-9
        single_entropies = []
        is_fully_separable = False
        
        for qubit in range(4):
            rho_i = ptrace(rho, [qubit])
            ev = rho_i.eigenenergies()
            s = entropy(ev)
            single_entropies.append(s)
        
        print("\nЭнтропии отдельных кубитов:", np.round(single_entropies, 6))
        
        if all(abs(s) < tol for s in single_entropies):
            is_fully_separable = True
            print("Состояние полностью сепарабельно.")
        else:
            print("Состояние не полностью сепарабельно (есть квантовые корреляции).")
        
        # анализ запутанности 
        subsystems = {
            'AB': [0, 1],
            'AC': [0, 2],
            'AD': [0, 3],
            'BC': [1, 2],
            'BD': [1, 3],
            'CD': [2, 3]
        }
        
        entangled_count = 0
        pairwise_results = {}
        
        for name, indices in subsystems.items():
            sub_rho = ptrace(rho, indices)
            sub_evals = sub_rho.eigenenergies()
            ent = entropy(sub_evals)
            
            sub_pt = partial_transpose(sub_rho, [0, 1])
            pt_evals = sub_pt.eigenenergies()
            
            # PPT критерий
            is_entangled = any(ev < 0 for ev in pt_evals)
            
            pairwise_results[name] = {
                "entropy": float(ent),
                "entangled": is_entangled,
                "pt_negative_eigenvalues": [float(ev) for ev in pt_evals if ev < 0]
            }
            
            if is_entangled:
                entangled_count += 1
        
        if is_fully_separable:
            classification = "fully_separable"
        else:
            if entangled_count == len(subsystems):
                classification = "W-type (все пары запутаны)"
            else:
                classification = f"GHZ-type (запутаны {entangled_count}/{len(subsystems)} пар)"
        
        print(f"\nКлассификация: {classification}")
        
        # сбор результатов для сохранения в БД
        results = {
            "single_entropies": [float(s) for s in single_entropies],
            "pairwise_entanglement": pairwise_results,
            "classification": classification,
            "entangled_count": entangled_count
        }
        
        # обновление статуса эксперимента в БД
        if experiment_id:
            db.update_status(experiment_id, "completed", results)
        
        print("\n" + "="*70)
        print("ЭКСПЕРИМЕНТ УСПЕШНО ЗАВЕРШЁН")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\nОШИБКА В ЭКСПЕРИМЕНТЕ: {e}")
        import traceback
        traceback.print_exc()
        
        # обновление статуса на "failed" в случае ошибки
        if experiment_id:
            db.update_status(experiment_id, "failed")
        
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\nПрограмма завершена успешно")
    else:
        print("\nПрограмма завершена с ошибкой")