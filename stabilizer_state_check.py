from graph_to_graph_state2 import GraphState
from graph_state_check import format_state_string
from qutip import basis, tensor, rand_ket, Qobj
import numpy as np
import itertools

def test_is_stabilizer_state(max_n=5, num_trials=5):
    for n in range(2, max_n+1):
        print(f"\n{'='*50}")
        print(f"ТЕСТИРОВАНИЕ СТАБИЛИЗАТОРНОСТИ ДЛЯ N = {n} КУБИТОВ")
        print('='*50)
        
        vertices = list(range(1, n+1))
        all_edges = list(itertools.combinations(vertices, 2))
        num_edges = len(all_edges)

        print(f"\n[1] случайные графовые состояния ({num_trials} испытаний):")
        success_count = 0
        for trial in range(num_trials):
            mask = np.random.randint(0, 2, num_edges)
            edges = [all_edges[i] for i in range(num_edges) if mask[i]]
            gs = GraphState(vertices, edges)
            psi = gs.state_vector

            state_str = format_state_string(psi, n_terms=min(8, 2**n))
            print(f"    {trial+1}: {state_str}")

            is_stab, gens = GraphState.is_stabilizer_state(psi, vertices)
            if is_stab:
                success_count += 1
                print(f"    {trial+1}: OK (состояние стабилизаторное), найденные генераторы: {gens}")
            else:
                print(f"    {trial+1}: ОШИБКА (состояние не распознано как стабилизаторное)")
        print(f"    Результат: {success_count} из {num_trials} графовых состояний распознаны")



        # print(f"\n[2] состояния с равными модулями вероятностных амплитуд, произвольными фазами ({num_trials} испытаний):")
        # found_stabilizer_states = 0
        # for trial in range(num_trials):
        #     phases = np.random.choice([1, -1], size=2**n)
        #     amp = 1.0 / np.sqrt(2**n) * phases
        #     random_psi = Qobj(amp.reshape(-1,1), dims=[[2]*n, [1]*n])
            
        #     is_stab, _ = GraphState.is_stabilizer_state(random_psi, vertices, verbose=False)
            
        #     if is_stab:
        #         found_stabilizer_states += 1
        #         print(f"    {trial+1}: состояние признано стабилизаторным, найденные генераторы: {gens}")
        #     else:
        #         print(f"    {trial+1}: состояние не является стабилизаторным")
        # print(f"    Результат: {found_stabilizer_states} найдено стабилизаторных состояний из {num_trials}.")



        # 3. Полностью случайные состояния
        # print(f"\n[3] полностью случайные состояния ({num_trials} испытаний):")
        # false_positive2 = 0
        # for trial in range(num_trials):
        #     random_psi = rand_ket(2**n)
        #     is_stab, _ = GraphState.is_stabilizer_state(random_psi, vertices, verbose=False)
        #     if is_stab:
        #         false_positive2 += 1
        #         print(f"    {trial+1}: ЛОЖНОЕ СРАБАТЫВАНИЕ (случайное состояние ошибочно признано стабилизаторным)")
        #     else:
        #         print(f"    {trial+1}: OK (случайное состояние не стабилизаторное)")
        # print(f"    Результат: {false_positive2} ложных срабатываний из {num_trials}.")



        if n == 3:
            print(f"\n[4] известные тестовые случаи (n=3):")
            zero = basis(2,0)
            one = basis(2,1)
            ghz = (tensor(zero,zero,zero) + tensor(one,one,one)).unit()

            is_stab_ghz, gens_ghz = GraphState.is_stabilizer_state(ghz, vertices)
            
            if is_stab_ghz:
                print(f"    GHZ: OK (состояние стабилизаторное), генераторы: {gens_ghz}")
            else:
                print(f"    GHZ: ОШИБКА (состояние не распознано как стабилизаторное)")



            w_state = (tensor(zero,zero,one) + tensor(zero,one,zero) + tensor(one,zero,zero)).unit()
            
            is_stab_w, _ = GraphState.is_stabilizer_state(w_state, vertices)
            
            if is_stab_w:
                print(f"    W: ОШИБКА (состояние распознано как стабилизаторное)")
            else:
                print(f"    W: OK (состояние не стабилизаторное)")

if __name__ == '__main__':
    # n = 3
    # zero = basis(2,0)
    # one = basis(2,1)
    # ghz = (tensor(zero,zero,zero) + tensor(one,one,one)).unit()


    # is_stab, gens = GraphState.is_stabilizer_state(ghz, [1,2,3])
    # if is_stab:
    #     print("состояние является стабилизатором!")
    #     print(f"найденные генераторы: {gens}")
    # else:
    #     print("состояние не является стабилизатором (ошибка)")
    # print(gens) 

    test_is_stabilizer_state(max_n=3, num_trials=3)