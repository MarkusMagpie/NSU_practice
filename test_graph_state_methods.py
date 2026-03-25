from graph_to_graph_state2 import GraphState
from qutip import basis, tensor, rand_ket, Qobj
import numpy as np
import itertools

def format_state_string(psi, n_terms=5):
    N = int(np.log2(len(psi.full())))

    amps = psi.full().flatten()

    # индексы с ненулевой амплитудой
    nonzero_amps = []
    for i,a in enumerate(amps):
        if np.abs(a) > 0:
            nonzero_amps.append(i)
    
    terms = []
    for idx in nonzero_amps[:n_terms]:
        sign = '+' if amps[idx].real > 0 else '-'
        basis_str = format(idx, '0{}b'.format(N))
        terms.append(f"{sign} |{basis_str}>")

    if len(nonzero_amps) > n_terms:
        terms.append("...")
    state_str = "|psi> = (1/sqrt({}))(".format(2**N) + " ".join(terms).lstrip('+') + " )"
    return state_str

"""
тестирование метода is_graph_state от 2 до max_n вершин 
"""
def test_is_graph_state(max_n=7, num_trials=5):
    for n in range(2, max_n+1):
        print(f"\n{'='*50}")
        print(f"ТЕСТИРОВАНИЕ ДЛЯ N = {n} ВЕРШИН")
        print('='*50)
        
        vertices = list(range(1, n+1))
        all_edges = list(itertools.combinations(vertices, 2)) # 2значные комбинации, где элементы - vertices
        num_edges = len(all_edges)

        print(f"\n[1] проверка на случайных графах ({num_trials} испытаний):")
        success_count = 0
        for trial in range(num_trials):
            mask = np.random.randint(0, 2, num_edges) # маска ребер - состоит из num_edges бит, где 1 - ребро есть, 0 - нет
            edges = []
            for i in range(num_edges):
                if mask[i]:
                    edges.append(all_edges[i])
            gs = GraphState(vertices, edges)
            psi = gs.state_vector

            found, found_gs = GraphState.is_graph_state(psi, vertices, verbose=False)

            if found and set(found_gs.edges) == set(edges):
                print(f"    {trial+1}: графовое состояние найдено! Найденный граф: V = {found_gs.vertices}, E = {found_gs.edges}")
                success_count += 1
            else:
                print(f"    {trial+1}: графовое состояние НЕ было распознано!")

        if success_count == num_trials:
            print(f"    Результат: все {num_trials} графовые состояния произвольных графов были распознаны")
        else:
            print(f"    Результат: распознано {success_count} из {num_trials} графовых состояний")



        print(f"\n[2] состояния с равными модулями вероятностных амплитуд, произвольными фазами ({num_trials} испытаний):")
        found_graph_count = 0
        for trial in range(num_trials):
            phases = np.random.choice([1, -1], size=2**n) # случайные фазы
            amp = 1.0 / np.sqrt(2**n) * phases
            random_psi = Qobj(arg=amp.reshape(len(amp),1), dims=[[2]*n, [1]*n]) # state vector
            
            found, found_state = GraphState.is_graph_state(random_psi, vertices, verbose=False)
            
            state_str = format_state_string(random_psi, n_terms=min(8, 2**n))
            print(f"    {trial+1}: {state_str}")
            if found:
                found_graph_count += 1
                print(f"    {trial+1}: состояние является графовым")
                print(f"        Найденный граф: V = {found_state.vertices}, E = {found_state.edges}")
                found_state.visualize() # визуализация графа найденного графового состояния

            else:
                print(f"    {trial+1}: состояние не является графовым")
        print(f"    Результат: {num_trials - found_graph_count} из {num_trials} состояний с равными модулями вероятностных амплитуд и произвольными фазами отвергнуты")



        print(f"\n[3] случайные состояния ({num_trials} испытаний):")
        found_graph_count2 = 0
        for trial in range(num_trials):
            random_psi = rand_ket(2**n) # rand_ket(n) - creates a random ket vector of dimension n
            # print(f"    {trial+1}: амплитуды случайного состояния: {random_psi.full().flatten()}")
            
            found, _ = GraphState.is_graph_state(random_psi, vertices, verbose=False)
            
            state_str = format_state_string(random_psi, n_terms=min(8, 2**n))
            print(f"    {trial+1}: {state_str}")
            if not found:
                print(f"    {trial+1}: случайное состояние признано не графовым")
            else:
                print(f"    {trial+1}: графовое состояние найдено! Найденный граф: V = {_.vertices}, E = {_.edges}")
                found_graph_count2 += 1
        print(f"    {num_trials - found_graph_count2} из {num_trials} случайных состояний отвергнуты")



def test_from_amplitudes(max_n=7, num_trials=5, verbose=False):
    for n in range(2, max_n+1):
        print(f"\n{'='*50}")
        print(f"ТЕСТИРОВАНИЕ from_amplitudes ДЛЯ N = {n} ВЕРШИН")
        print('='*50)

        vertices = list(range(1, n+1))
        all_edges = list(itertools.combinations(vertices, 2))
        num_edges = len(all_edges)

        print(f"\n[1] случайные графы ({num_trials} испытаний):")
        success_count = 0
        for trial in range(num_trials):
            mask = np.random.randint(0, 2, num_edges) # маска ребер - состоит из num_edges бит, где 1 - ребро есть, 0 - нет
            edges = []
            for i in range(num_edges):
                if mask[i]:
                    edges.append(all_edges[i])
            gs = GraphState(vertices, edges)
            amps = gs.get_amplitudes()

            found, found_gs = GraphState.from_amplitudes(amps, tol=1e-8)

            if found and set(found_gs.edges) == set(edges):
                if verbose:
                    print(f"    {trial+1}: графовое состояние распознано, Найденный граф: V = {found_gs.vertices}, E = {found_gs.edges}")
                success_count += 1
            else:
                if verbose:
                    print(f"    {trial+1}: графовое состояние НЕ распознано")
        print(f"    Результат: распознано {success_count} из {num_trials} графовых состояний")



        print(f"\n[2] случайные амплитуды ({num_trials} испытаний):")
        false_positive = 0
        for trial in range(num_trials):
            raw = np.random.randn(2**n) + 1j * np.random.randn(2**n)
            amps = raw / np.linalg.norm(raw)

            if verbose:
                print(f"    {trial+1}: случайные амплитуды: {amps}")

            found, _ = GraphState.from_amplitudes(amps, tol=1e-8)
            
            if found:
                false_positive += 1
                if verbose:
                    print(f"    {trial+1}: случайные амплитуды - амплитуды графового состояния")
            else:
                if verbose:
                    print(f"    {trial+1}: случайные амплитуды - не амплитуды графового состояния")
        print(f"    Результат: {false_positive} ложных срабатываний из {num_trials}")



def test_separability(max_n=7, num_trials=5, verbose=False):
    for n in range(2, max_n+1):
        print(f"\n{'='*50}")
        print(f"ТЕСТИРОВАНИЕ СЕПАРАБЕЛЬНОСТИ ДЛЯ N = {n} ВЕРШИН")
        print('='*50)

        vertices = list(range(1, n+1))
        all_edges = list(itertools.combinations(vertices, 2))
        num_edges = len(all_edges)

        print(f"\n[1] is_separable (True для несвязных графов; False для связных):")
        correct_sep = 0
        for trial in range(num_trials):
            mask = np.random.randint(0, 2, num_edges)
            edges = [all_edges[i] for i in range(num_edges) if mask[i]]

            if verbose:
                print(f"    {trial+1}: Граф: V = {vertices}, E = {edges}")
            
            gs = GraphState(vertices, edges)
            
            
            components = gs.find_connected_components()
            expected = len(components) > 1

            sep, comps = gs.is_separable()
            
            if sep == expected:
                correct_sep += 1
                if verbose:
                    res = 'несвязный' if expected else 'связный'
                    print(f"    {trial+1}: OK (граф {res}, is_separable={sep})")
            else:
                if verbose:
                    print(f"    {trial+1}: ОШИБКА (ожидалось {expected}, получено {sep})")
        print(f"    Результат: правильных ответов {correct_sep} из {num_trials}")



        print(f"\n[2] is_fully_separable (True для графов без ребер; False иначе):")
        correct_full = 0
        for trial in range(num_trials):
            mask = np.random.randint(0, 2, num_edges)
            edges = [all_edges[i] for i in range(num_edges) if mask[i]]

            if verbose:
                print(f"    {trial+1}: Граф: V = {vertices}, E = {edges}")

            gs = GraphState(vertices, edges)

            expected = (len(edges) == 0)
            full = gs.is_fully_separable()
            if full == expected:
                correct_full += 1
                if verbose:
                    res = 'без ребер' if expected else 'с ребрами'
                    print(f"    {trial+1}: OK (граф {res}, is_fully_separable={full})")
            else:
                if verbose:
                    print(f"    {trial+1}: ОШИБКА (ожидалось {expected}, получено {full})")
        print(f"    Результат: правильных ответов {correct_full} из {num_trials}")



def run_all_tests(max_n=7, num_trials=3, verbose=False):
    print("\n" + "="*80)
    print("ЗАПУСК ВСЕХ ТЕСТОВ")
    print("="*80)
    test_is_graph_state(max_n, num_trials, verbose)
    test_from_amplitudes(max_n, num_trials, verbose)
    test_separability(max_n, num_trials, verbose)



if __name__ == '__main__':
    # test_is_graph_state(5,3)
    # test_from_amplitudes(5, 3, True)
    test_separability(5, 3, True)
    # run_all_tests(max_n=5, num_trials=3, verbose=True)