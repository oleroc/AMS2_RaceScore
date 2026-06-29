#!/usr/bin/env python3
"""
Fix missing Races → Sessions foreign key constraint
"""

import sqlite3
import os

def fix_races_sessions_foreign_key():
    db_path = 'RaceDB.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Fixing Races → Sessions foreign key constraint...")
        
        # Check current Races table structure
        cursor.execute("PRAGMA foreign_key_list(Races)")
        current_fks = cursor.fetchall()
        has_sessions_fk = any(fk[2] == 'Sessions' for fk in current_fks)
        
        if has_sessions_fk:
            print("✅ Foreign key already exists - no fix needed!")
            conn.close()
            return
        
        # Create backup of Races table
        print("  📋 Creating backup of Races table...")
        cursor.execute("CREATE TABLE Races_temp AS SELECT * FROM Races")
        
        # Drop original Races table
        print("  🗑️  Dropping original Races table...")
        cursor.execute("DROP TABLE Races")
        
        # Recreate Races table with proper foreign key
        print("  🔨 Recreating Races table with foreign key...")
        cursor.execute('''
            CREATE TABLE Races (
                RaceID INTEGER PRIMARY KEY,
                mTranslatedTrackVariation TEXT,
                mLapsInEvent INTEGER,
                RaceDate TEXT DEFAULT (date('now')),
                SessionID INTEGER,
                IsCompleted BOOLEAN DEFAULT 0,
                CompletedAt DATETIME NULL,
                IPAddress TEXT DEFAULT '127.0.0.1',
                FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID) ON DELETE SET NULL
            )
        ''')
        
        # Copy data back from backup
        print("  📥 Restoring data from backup...")
        cursor.execute('''
            INSERT INTO Races 
            SELECT * FROM Races_temp
        ''')
        
        # Drop backup table
        cursor.execute("DROP TABLE Races_temp")
        
        # Recreate indexes for Races table
        print("  📊 Recreating indexes...")
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_races_session ON Races(SessionID)",
            "CREATE INDEX IF NOT EXISTS idx_races_date ON Races(RaceDate)",
            "CREATE INDEX IF NOT EXISTS idx_races_completed ON Races(IsCompleted)",
            "CREATE INDEX IF NOT EXISTS idx_races_ip ON Races(IPAddress)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        conn.commit()
        
        # Verify the fix
        cursor.execute("PRAGMA foreign_key_list(Races)")
        new_fks = cursor.fetchall()
        has_sessions_fk = any(fk[2] == 'Sessions' for fk in new_fks)
        
        if has_sessions_fk:
            print("✅ Foreign key constraint successfully added!")
            print("  • Races.SessionID → Sessions.SessionID ON DELETE SET NULL")
        else:
            print("❌ Failed to add foreign key constraint")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error fixing foreign key: {e}")

if __name__ == "__main__":
    fix_races_sessions_foreign_key()
