import sqlite3

conn = sqlite3.connect('appointments.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        notes TEXT
    )
''')

conn.commit()
conn.close()
