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
    
    # сохранение информации о запуске эксперимента
    def save_experiment(self, name, description, parameters):
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            
            # SQL request для вставки
            query = """
            INSERT INTO experiments (name, description, parameters, status, created_at, results)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
            """
            
            #выполнение запроса
            cursor.execute(query, (
                name,
                description,
                json.dumps(parameters),
                'running',
                datetime.now(),
                json.dumps({}),
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
    
    # обновить статус эксперимента
    def update_status(self, experiment_id, status, results=None):
        try:
            conn = psycopg2.connect(**self.connection_params)
            cursor = conn.cursor()
            
            if results:
                # обнова двух полей: status и results
                query = """
                UPDATE experiments 
                SET status = %s, 
                    results = %s 
                WHERE id = %s
                """
                cursor.execute(query, (status, json.dumps(results), experiment_id))
            else:
                # только статус
                query = "UPDATE experiments SET status = %s WHERE id = %s"
                cursor.execute(query, (status, experiment_id))
            
            conn.commit()
            print(f"Статус эксперимента {experiment_id} обновлён на '{status}'")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"Ошибка обновления статуса: {e}")