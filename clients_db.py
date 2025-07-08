import psycopg2


def create_db(conn):
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS phones;
            DROP TABLE IF EXISTS clients;
        """)
        conn.commit()

        cur.execute("""
            CREATE TABLE clients (
                id SERIAL PRIMARY KEY,
                first_name VARCHAR(50),
                last_name VARCHAR(50),
                email VARCHAR(100) UNIQUE
            );
        """)

        cur.execute("""
            CREATE TABLE phones (
                id SERIAL PRIMARY KEY,
                client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
                phone VARCHAR(20)
            );
        """)
        conn.commit()
        print("Структура БД создана.")


def add_client(conn, first_name, last_name, email, phones=None):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO clients (first_name, last_name, email)
            VALUES (%s, %s, %s)
            RETURNING id;
        """, (first_name, last_name, email))
        client_id = cur.fetchone()[0]

        if phones:
            for phone in phones:
                cur.execute("""
                    INSERT INTO phones (client_id, phone)
                    VALUES (%s, %s);
                """, (client_id, phone))
        
        conn.commit()
        print(f"✅ Клиент {first_name} {last_name} добавлен с ID {client_id}")

def add_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO phones (client_id, phone)
            VALUES (%s, %s);
        """, (client_id, phone))
        conn.commit()
        print(f"📱 Телефон {phone} добавлен клиенту с ID {client_id}")

def change_client(conn, client_id, first_name=None, last_name=None, email=None, phones=None):
    with conn.cursor() as cur:
        # Изменение имени
        if first_name:
            cur.execute("""
                UPDATE clients SET first_name = %s WHERE id = %s;
            """, (first_name, client_id))

        # Изменение фамилии
        if last_name:
            cur.execute("""
                UPDATE clients SET last_name = %s WHERE id = %s;
            """, (last_name, client_id))

        # Изменение email
        if email:
            cur.execute("""
                UPDATE clients SET email = %s WHERE id = %s;
            """, (email, client_id))

        # Обновление телефонов: удалим старые и добавим новые
        if phones is not None:
            cur.execute("""
                DELETE FROM phones WHERE client_id = %s;
            """, (client_id,))
            for phone in phones:
                cur.execute("""
                    INSERT INTO phones (client_id, phone) VALUES (%s, %s);
                """, (client_id, phone))

        conn.commit()
        print(f"✏️ Данные клиента с ID {client_id} обновлены.")

def delete_phone(conn, client_id, phone):
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM phones WHERE client_id = %s AND phone = %s;
        """, (client_id, phone))
        conn.commit()
        print(f"❌ Телефон {phone} удалён у клиента с ID {client_id}.")

def delete_client(conn, client_id):
    with conn.cursor() as cur:
        cur.execute("""
            DELETE FROM clients WHERE id = %s;
        """, (client_id,))
        conn.commit()
        print(f"🗑️ Клиент с ID {client_id} удалён.")

def find_client(conn, first_name=None, last_name=None, email=None, phone=None):
    with conn.cursor() as cur:
        query = """
            SELECT c.id, c.first_name, c.last_name, c.email, p.phone
            FROM clients c
            LEFT JOIN phones p ON c.id = p.client_id
            WHERE TRUE
        """
        params = []

        if first_name:
            query += " AND c.first_name ILIKE %s"
            params.append(first_name)
        if last_name:
            query += " AND c.last_name ILIKE %s"
            params.append(last_name)
        if email:
            query += " AND c.email ILIKE %s"
            params.append(email)
        if phone:
            query += " AND p.phone = %s"
            params.append(phone)

        cur.execute(query, params)
        results = cur.fetchall()

        if results:
            print("🔎 Найденные клиенты:")
            for row in results:
                print(f"ID: {row[0]}, Имя: {row[1]}, Фамилия: {row[2]}, Email: {row[3]}, Телефон: {row[4]}")
        else:
            print("🚫 Клиент не найден.")


# подключение
with psycopg2.connect(database="clients_db", user="postgres", password="19071993") as conn:
    create_db(conn)

    # Добавим клиента
    add_client(conn, "Иван", "Петров", "ivan.petrov@example.com", ["+79001112233", "+79004445566"])

    # Добавим ещё один телефон этому клиенту
    add_phone(conn, 1, "+79007778899")

    # Изменим клиента
    change_client(conn, 1, first_name="Иванка", email="ivanka@example.com", phones=["+79009998877"])

    delete_phone(conn, 1, "+79009998877")

    delete_client(conn, 1)

    find_client(conn, email="ivan.petrov@example.com")  # Проверим, что не найдёт (мы удалили)

conn.close()
