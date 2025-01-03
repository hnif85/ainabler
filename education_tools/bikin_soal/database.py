import sqlite3

# Connect to SQLite database
conn = sqlite3.connect('D:/MyProject/AI.nabler/education_tools/bikin_soal/education.db')
c = conn.cursor()

# Add new column 'kelas' to the table if it doesn't exist
c.execute('''
    ALTER TABLE generated_questions ADD COLUMN kelas INTEGER DEFAULT 12
''')

# Update existing rows to set 'kelas' to 12
c.execute('''
    UPDATE generated_questions SET kelas = 12 WHERE kelas IS NULL
''')

# Close connection
conn.close()
