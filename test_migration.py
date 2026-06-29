import sqlite3

# Temporarily downgrade database version to test migration
conn = sqlite3.connect('RaceDB.db')
cursor = conn.cursor()

try:
    cursor.execute('UPDATE DatabaseMetadata SET Value = ? WHERE Key = ?', ('1.6.0', 'schema_version'))
    conn.commit()
    print("Database version set to 1.6.0 for testing")
    
    # Verify the change
    cursor.execute('SELECT Value FROM DatabaseMetadata WHERE Key = ?', ('schema_version',))
    result = cursor.fetchone()
    print(f"Current database version: {result[0] if result else 'Not found'}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
