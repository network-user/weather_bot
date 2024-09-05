import sqlite3

connection = sqlite3.connect('telegram_bot_database.db')
cursor = connection.cursor()

cursor.execute('''
    CREATE TABLE POGODA
    (
    id INTEGER,
    name TEXT,
    city TEXT
    )
''')

connection.close()