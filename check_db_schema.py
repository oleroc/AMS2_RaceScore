#!/usr/bin/env python3
"""
Database Schema Inspector for RaceMonitor v1.7.0
Verifies that database migration created proper table structure with foreign keys
"""

import sqlite3
import os

def check_database_schema():
    db_path = 'RaceDB.db'
    
    if not os.path.exists(db_path):
        print(f"❌ Database file {db_path} not found!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 RaceMonitor v1.7.0 Database Schema Analysis")
        print("=" * 60)
        
        # Check database version
        print("\n📋 DATABASE VERSION:")
        try:
            cursor.execute("SELECT Value FROM DatabaseMetadata WHERE Key = 'schema_version'")
            version = cursor.fetchone()
            if version:
                print(f"✅ Schema Version: {version[0]}")
            else:
                print("⚠️  No version information found")
        except sqlite3.OperationalError:
            print("⚠️  DatabaseMetadata table not found (legacy database)")
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = cursor.fetchall()
        
        print(f"\n📊 TABLES FOUND ({len(tables)}):")
        for table in tables:
            print(f"  • {table[0]}")
        
        # Check each table structure
        expected_tables = ['Races', 'Sessions', 'SessionParticipants', 'Participants', 'Laps', 'Drivers', 'HighScore', 'DatabaseMetadata']
        
        print(f"\n🔧 TABLE STRUCTURE ANALYSIS:")
        
        for table_name in expected_tables:
            print(f"\n--- {table_name} ---")
            try:
                # Get table info
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                
                if columns:
                    print("  Columns:")
                    for col in columns:
                        col_id, name, data_type, not_null, default, pk = col
                        pk_str = " (PRIMARY KEY)" if pk else ""
                        null_str = " NOT NULL" if not_null else ""
                        default_str = f" DEFAULT {default}" if default else ""
                        print(f"    • {name}: {data_type}{null_str}{default_str}{pk_str}")
                    
                    # Get foreign keys
                    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
                    foreign_keys = cursor.fetchall()
                    
                    if foreign_keys:
                        print("  Foreign Keys:")
                        for fk in foreign_keys:
                            fk_id, seq, ref_table, from_col, to_col, on_update, on_delete, match = fk
                            print(f"    • {from_col} → {ref_table}({to_col}) ON DELETE {on_delete}")
                    else:
                        print("  Foreign Keys: None")
                        
                    # Get indexes
                    cursor.execute(f"PRAGMA index_list({table_name})")
                    indexes = cursor.fetchall()
                    
                    if indexes:
                        print("  Indexes:")
                        for idx in indexes:
                            idx_seq, idx_name, unique, origin, partial = idx
                            unique_str = " (UNIQUE)" if unique else ""
                            print(f"    • {idx_name}{unique_str}")
                
                else:
                    print("  ❌ Table not found")
                    
            except sqlite3.OperationalError as e:
                print(f"  ❌ Error: {e}")
        
        # Check data counts
        print(f"\n📈 DATA SUMMARY:")
        for table_name in [t[0] for t in tables if t[0] != 'sqlite_sequence']:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"  • {table_name}: {count} records")
            except sqlite3.OperationalError:
                print(f"  • {table_name}: Error reading")
        
        # Verify critical v1.7.0 features
        print(f"\n🎯 V1.7.0 FEATURE VERIFICATION:")
        
        # Check if Sessions table exists with proper structure
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Sessions'")
        if cursor.fetchone():
            print("  ✅ Sessions table exists (multi-race support)")
        else:
            print("  ❌ Sessions table missing")
            
        # Check if SessionParticipants table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SessionParticipants'")
        if cursor.fetchone():
            print("  ✅ SessionParticipants table exists (50% matching algorithm)")
        else:
            print("  ❌ SessionParticipants table missing")
            
        # Check if Races table has new columns
        cursor.execute("PRAGMA table_info(Races)")
        races_columns = [col[1] for col in cursor.fetchall()]
        
        new_columns = ['IsCompleted', 'CompletedAt', 'IPAddress']
        for col in new_columns:
            if col in races_columns:
                print(f"  ✅ Races.{col} column exists")
            else:
                print(f"  ❌ Races.{col} column missing")
        
        # Check foreign key constraints
        cursor.execute("PRAGMA foreign_key_list(Races)")
        races_fks = cursor.fetchall()
        has_sessions_fk = any(fk[2] == 'Sessions' for fk in races_fks)
        
        if has_sessions_fk:
            print("  ✅ Races → Sessions foreign key exists")
        else:
            print("  ❌ Races → Sessions foreign key missing")
        
        # Check performance indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        indexes = cursor.fetchall()
        
        if indexes:
            print(f"  ✅ Performance indexes created ({len(indexes)} indexes)")
            for idx in indexes:
                print(f"    • {idx[0]}")
        else:
            print("  ⚠️  No performance indexes found")
        
        print(f"\n✅ Database schema analysis complete!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error analyzing database: {e}")

if __name__ == "__main__":
    check_database_schema()
