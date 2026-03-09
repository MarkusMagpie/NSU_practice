from graph_to_graph_state2 import GraphState
from qutip import rand_ket

if __name__ == '__main__':
    # V = [1,2,3,4]
    # E = [(1,2),(2,3),(3,4)]

    # gs = GraphState(V, E)
    # psi = gs.state_vector
    # is_graph, found_state = GraphState.is_graph_state(psi, V)
    # if is_graph:
    #     print("Графовое состояние найдено!")
    #     print(f"Найденный граф: V={found_state.vertices}, E={found_state.edges}")
    # else :
    #     print("Графовое состояние не найдено!")



    # print()

    V = [1, 2, 3, 4]
    E = [(1, 2), (1, 3), (1, 4)]

    gs_star = GraphState(V, E)
    psi_star = gs_star.state_vector
    print("\nПроверка графа-звезды:")
    is_graph_star, found_star = GraphState.is_graph_state(psi_star, V, verbose=True)
    if is_graph_star:
        print("Графовое состояние найдено!")
        print(f"Найденный граф: V={found_star.vertices}, E={found_star.edges}")
    else:
        print("Графовое состояние не найдено!")


    print()

    # проверка случайного состояние (равномерной суперпозиции всех базисных состояний)
    random_psi = rand_ket(2**len(V)) # rand_ket(n) - creates a random ket vector of dimension n
    print("\nПроверка случайного состояния (ne fact chto grafovogo):")
    is_graph2, found_state2 = GraphState.is_graph_state(random_psi, V, verbose=True)
    if is_graph2:
        print("Графовое состояние найдено!")
        print(f"Найденный граф: V={found_state2.vertices}, E={found_state2.edges}")
    else :
        print("Графовое состояние не найдено!")