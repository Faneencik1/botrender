import sqlite3

# Создание базы и таблицы
def init_db():
    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            message TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

# Сохранение сообщения
def save_message(user_id, username, message):
    conn = sqlite3.connect("messages.db")
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO messages (user_id, username, message)
        VALUES (?, ?, ?)
    ''', (user_id, username, message))
    conn.commit()
    conn.close()
