from graph_to_graph_state2 import GraphState
from qutip import rand_ket, Qobj
import numpy as np
import itertools


if __name__ == '__main__':
    # V = [1,2,3,4]
    # E = [(1,2),(2,3),(3,4)]
    # E = [(1,2),(1,3),(1,4)]

    test_is_graph_state(5, 3)

    # V = [1,2,3]
    # E = [(1,2),(2,3)]
    # gs = GraphState(V, E)
    # psi = gs.state_vector
    # found, found_gs = GraphState.is_graph_state(psi, V, verbose=False)
    # if found:
    #     print("состояние является графовым!")
    #     print(f"найденный граф: V={found_gs.vertices}, E={found_gs.edges}")
    # else:
    #     print("состояние не является графовым (ошибка)")