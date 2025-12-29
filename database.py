import psycopg2
import json
from datetime import datetime

class ExperimentDB:
    def __init__(self):
        self.connection_params = {
            'host': 'localhost',
            'database': 'quantum_experiments',
            'user': 'quantum_user',
            'password': 'quantum_password'
        }
    
    def save_experiment(self, name, description, parameters):
        # сохранение информации о запуске эксперимента
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            
            # SQL request для вставки
            query = """
            INSERT INTO experiments (name, description, parameters, status, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id;
            """
            
            #выполнение запроса
            cursor.execute(query, (
                name,
                description,
                json.dumps(parameters),
                'running',
                datetime.now()
            ))
            
            # ID новой записи
            experiment_id = cursor.fetchone()[0]
            
            # сохранение изменений
            conn.commit()
            
            print(f"Эксперимент сохранён в БД. ID: {experiment_id}")
            
            # закрытие соединения
            cursor.close()
            conn.close()
            
            return experiment_id
            
        except Exception as e:
            print(f"Ошибка сохранения эксперимента: {e}")
            return None
    
    def update_status(self, experiment_id, status, results=None):
        # Обновить статус эксперимента
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            
            if results:
                # есть результаты -> сохраняю их в поле results
                results_json = json.dumps(results)
                query = "UPDATE experiments SET status = %s, parameters = parameters || %s WHERE id = %s"
                cursor.execute(query, (status, json.dumps({"results": results}), experiment_id))
            else:
                query = "UPDATE experiments SET status = %s WHERE id = %s"
                cursor.execute(query, (status, experiment_id))
            
            conn.commit()
            print(f"Статус эксперимента {experiment_id} обновлён на '{status}'")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Ошибка обновления статуса: {e}")