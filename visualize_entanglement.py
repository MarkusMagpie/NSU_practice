import matplotlib.pyplot as plt
import networkx as nx
import json
import sys

from database import ExperimentDB

class EntanglementVisualizer:
    def __init__(self):
        self.db = ExperimentDB()

    # получаю данные об конкретном эксперименте из субд по id 
    def get_experiment_data(self, experiment_id):
        try:
            import psycopg2

            conn = psycopg2.connect(
                host="localhost",
                database="quantum_experiments",
                user="quantum_user",
                password="quantum_password"
            )
            cursor = conn.cursor()

            query = """
            SELECT name, parameters, results
            FROM experiments
            WHERE id = %s
            """
            cursor.execute(query, (experiment_id,))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result:
                name, parameters_json, results_json = result
                # parameters = json.loads(parameters_json)
                if (isinstance(parameters_json, dict)):
                    parameters = parameters_json
                else:
                    parameters = {}

                if results_json is None:
                    results = {}
                else:
                    # уже словарь?
                    results = results_json if isinstance(results_json, dict) else {}

                return {
                    'id': experiment_id,
                    'name': name,
                    'parameters': parameters,
                    'results': results
                }
            else:
                print(f"Эксперимент с ID {experiment_id} не найден")
                return None
                
        except Exception as e:
            print(f"ошибка получения данных: {e}")
            return None

    # собственно создание с помощью networkx графа запутанности кубитов
    def create_entanglement_graph(self, experiment_data, output_file=None):
        if not experiment_data: return None
        
        results = experiment_data['results']
        pairwise = results.get('pairwise_entanglement', {})

        # граф с 4 кубитами A,B,C,D
        G = nx.Graph()
        
        # вершины-кубиты
        qubits = ['A', 'B', 'C', 'D']
        G.add_nodes_from(qubits)

        # рёбра между запутанными кубитами
        entangled_edges = []
        non_entangled_edges = []
        
        for pair, data in pairwise.items():
            qubit1, qubit2 = pair[0], pair[1]  # 'AB' делится на 'A' и 'B'
            is_entangled = data.get('entangled', False)
            entropy = data.get('entropy', 0)
            
            if is_entangled:
                entangled_edges.append((qubit1, qubit2))
                G.add_edge(qubit1, qubit2, weight=entropy, entangled=True)
            else:
                non_entangled_edges.append((qubit1, qubit2))

        # создание графика
        plt.figure(figsize=(10, 8))

        # позиционирую вершины в виде квадрата
        pos = {
            'A': (0, 1),
            'B': (1, 1),
            'C': (0, 0),
            'D': (1, 0)
        }

        # рисовашки вершин
        nx.draw_networkx_nodes(G, pos, node_size=2000, 
                              node_color='blue', 
                              edgecolors='black',
                              node_shape='o')
        
        # подписание вершин
        nx.draw_networkx_labels(G, pos, font_size=16, font_color='white', font_weight='bold')

        # рисовашки ребер запутанности (жирные синие линии)
        nx.draw_networkx_edges(G, pos, 
                              edgelist=entangled_edges,
                              width=3, 
                              edge_color='red',
                              style='solid',
                              label='запутанные пары')
        
        # рисовашки НЕзапутанных пар (пунктирные серые линии)
        if non_entangled_edges:
            nx.draw_networkx_edges(G, pos,
                                  edgelist=non_entangled_edges,
                                  width=1,
                                  edge_color='gray',
                                  style='dashed',
                                  alpha=0.5,
                                  label='НЕ запутанные пары')
        
        title = f"Граф запутанности\nЭксперимент #{experiment_data['id']}: {experiment_data['name']}"
        plt.title(title, fontsize=14, pad=20)

        # + информация о классификации
        classification = results.get('classification', 'Неизвестно')
        entangled_count = results.get('entangled_count', 0)
        info_text = f"классификация: {classification}\запутанных пар: {entangled_count}/6"
        plt.figtext(0.5, 0.02, info_text, ha='center', fontsize=12)
        
        # легенда
        plt.legend(loc='upper right', fontsize=12)

        # сохраняю И/ИЛИ показываю граф
        if output_file:
            plt.savefig(output_file, dpi=300, bbox_inches='tight')
            print(f"граф сохранён в файл: {output_file}")
        
        plt.show()

        # данные графа для дальнейшего использования
        return {
            'graph': G,
            'entangled_edges': entangled_edges,
            'non_entangled_edges': non_entangled_edges,
            'entangled_count': entangled_count
        }

    # основная функция для визуализации эксперимента
    def visualize_experiment(self, experiment_id, save_to_file=None):
        print(f"визуализация эксперимента #{experiment_id}...")
        
        # данные из БД
        experiment_data = self.get_experiment_data(experiment_id)
        if not experiment_data:
            print("не удалося получить данные эксперимента")
            return None
        
        print(f"Данные получены: {experiment_data['name']}")
        print(f"Классификация: {experiment_data['results'].get('classification', 'Неизвестно')}")

        graph_info = self.create_entanglement_graph(experiment_data, output_file=save_to_file)
        
        return graph_info



def main():
    if len(sys.argv) < 2:
        print("как использовать: python3 visualize_entanglement.py <experiment_id> [output_file]")
        print("например: python3 visualize_entanglement.py 8 graph.png")
        sys.exit(1)
    
    experiment_id = int(sys.argv[1])
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    else :
        output_file = None
    
    visualizer = EntanglementVisualizer()
    visualizer.visualize_experiment(experiment_id, output_file)

if __name__ == "__main__":
    main()