import sqlite3

conn = sqlite3.connect('articles.db')

c = conn.cursor()

c.execute('ALTER TABLE articles ADD COLUMN model TEXT')

conn.commit()
conn.close()