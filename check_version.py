import sqlite3

# Check current database version
conn = sqlite3.connect('RaceDB.db')
cursor = conn.cursor()

try:
    cursor.execute('SELECT Value FROM DatabaseMetadata WHERE Key = ?', ('schema_version',))
    result = cursor.fetchone()
    print(f"Current database version: {result[0] if result else 'Not found'}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
