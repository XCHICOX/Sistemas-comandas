import sqlite3

conn = sqlite3.connect('databases/user_databases/espetocarioca.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS mesa_01 (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_nome TEXT NOT NULL,
    valor_de_entrada REAL NOT NULL,
    quantidade INTEGER NOT NULL
);
''')

conn.commit()
conn.close()
