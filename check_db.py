#!/usr/bin/env python3
import sqlite3
import os

def check_database():
    if not os.path.exists('RaceDB.db'):
        print("❌ Database file 'RaceDB.db' not found!")
        return
    
    conn = sqlite3.connect('RaceDB.db')
    cursor = conn.cursor()
    
    print('🔍 DATABASE STRUCTURE ANALYSIS')
    print('=' * 50)
    
    # 1. Check all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    print(f'📋 Tables ({len(tables)}): {", ".join(tables)}')
    print()
    
    # 2. Check database version
    try:
        cursor.execute("SELECT Value FROM DatabaseMetadata WHERE Key = 'schema_version'")
        version = cursor.fetchone()
        print(f'📊 Database Version: {version[0] if version else "Unknown"}')
    except:
        print('⚠️  Database Version: Legacy (no metadata table)')
    print()
    
    # 3. Detailed table analysis
    for table in tables:
        if table != 'sqlite_sequence':
            # Get table structure
            cursor.execute(f'PRAGMA table_info({table})')
            columns = cursor.fetchall()
            
            # Get record count
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            count = cursor.fetchone()[0]
            
            print(f'📁 {table} ({count} records):')
            for col in columns:
                col_name, col_type = col[1], col[2]
                print(f'   • {col_name}: {col_type}')
            print()
    
    # 4. Check foreign keys
    print('🔗 FOREIGN KEY CONSTRAINTS:')
    print('-' * 30)
    for table in ['Races', 'Participants', 'Laps', 'SessionParticipants', 'HighScore']:
        if table in tables:
            cursor.execute(f'PRAGMA foreign_key_list({table})')
            fks = cursor.fetchall()
            if fks:
                print(f'{table}:')
                for fk in fks:
                    print(f'   • {fk[3]} → {fk[2]}.{fk[4]}')
            else:
                print(f'{table}: No foreign keys')
    print()
    
    # 5. Check indexes
    print('📈 PERFORMANCE INDEXES:')
    print('-' * 25)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
    indexes = [row[0] for row in cursor.fetchall()]
    if indexes:
        for idx in indexes:
            print(f'   • {idx}')
    else:
        print('   No custom indexes found')
    print()
    
    # 6. Sample data check
    print('📊 DATA SAMPLE CHECK:')
    print('-' * 20)
    
    # Check Drivers
    if 'Drivers' in tables:
        cursor.execute('SELECT Name, Phone FROM Drivers LIMIT 3')
        drivers = cursor.fetchall()
        print(f'Drivers sample: {len(drivers)} shown')
        for driver in drivers:
            print(f'   • {driver[0]} (Phone: {driver[1]})')
    
    # Check Sessions
    if 'Sessions' in tables:
        cursor.execute('SELECT SessionID, CreatedAt, ParticipantCount FROM Sessions LIMIT 3')
        sessions = cursor.fetchall()
        print(f'Sessions sample: {len(sessions)} shown')
        for session in sessions:
            print(f'   • Session {session[0]}: {session[1]} ({session[2]} participants)')
    
    conn.close()
    print('✅ Database check completed successfully!')

if __name__ == '__main__':
    check_database()
