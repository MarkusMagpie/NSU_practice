from graph_to_graph_state2 import GraphState
from qutip import basis, tensor

if __name__ == '__main__':
    n = 3
    zero = basis(2,0)
    one = basis(2,1)
    ghz = (tensor(zero,zero,zero) + tensor(one,one,one)).unit()


    is_stab, gens = GraphState.is_stabilizer_state(ghz, [1,2,3])
    print(is_stab)
    print(gens) 