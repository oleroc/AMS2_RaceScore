#!/usr/bin/env python3
"""
AMS2 RaceScore Database Migration Utility v1.7.0
Standalone migration script to upgrade database from older versions to v1.7.0

This script handles:
- Version detection (1.5.0, 1.6.0 -> 1.7.0)
- Multi-race monitoring table creation
- Data preservation and validation
- Foreign key constraint establishment
- Performance index creation
- Database integrity verification

Usage:
    python migrate_to_v1_7_0.py [database_file]
    
If no database file specified, uses default 'RaceDB.db'
"""

import sqlite3
import os
import sys
import logging
from datetime import datetime, timedelta
import json

class DatabaseMigrator:
    def __init__(self, db_name='RaceDB.db'):
        self.db_name = db_name
        self.target_version = '1.7.0'
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('migration.log'),
                logging.StreamHandler()
            ]
        )
        
        # Connect to database
        try:
            self.conn = sqlite3.connect(self.db_name)
            self.cursor = self.conn.cursor()
            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")
            print(f"✅ Connected to database: {self.db_name}")
            logging.info(f"Connected to database: {self.db_name}")
        except Exception as e:
            print(f"❌ Failed to connect to database: {e}")
            logging.error(f"Failed to connect to database: {e}")
            sys.exit(1)
    
    def detect_current_version(self):
        """Detect the current database version"""
        try:
            # Check if DatabaseMetadata table exists (v1.7.0+)
            self.cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='DatabaseMetadata'
            ''')
            metadata_exists = self.cursor.fetchone()
            
            if metadata_exists:
                self.cursor.execute('''
                    SELECT Value FROM DatabaseMetadata WHERE Key = 'schema_version'
                ''')
                result = self.cursor.fetchone()
                return result[0] if result else '1.0.0'
            else:
                # Legacy database - detect version by structure
                return self.detect_legacy_version()
                
        except Exception as e:
            logging.error(f"Failed to detect database version: {e}")
            return '1.0.0'
    
    def detect_legacy_version(self):
        """Detect version of legacy database by structure"""
        try:
            # Check if SessionID column exists in Races table
            self.cursor.execute("PRAGMA table_info(Races)")
            races_columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'SessionID' in races_columns:
                return '1.6.0'
            else:
                return '1.5.0'
                
        except Exception:
            return '1.0.0'
    
    def version_compare(self, version1, version2):
        """Compare two version strings. Returns -1 if v1 < v2, 0 if equal, 1 if v1 > v2"""
        def normalize(v):
            return [int(x) for x in v.split('.')]
        
        v1_parts = normalize(version1)
        v2_parts = normalize(version2)
        
        # Pad with zeros if lengths differ
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        if v1_parts < v2_parts:
            return -1
        elif v1_parts > v2_parts:
            return 1
        else:
            return 0
    
    def backup_database(self):
        """Create a backup of the current database"""
        try:
            backup_name = f"{self.db_name}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create backup using SQLite backup API
            with sqlite3.connect(backup_name) as backup_conn:
                self.conn.backup(backup_conn)
            
            print(f"✅ Database backed up to: {backup_name}")
            logging.info(f"Database backed up to: {backup_name}")
            return backup_name
            
        except Exception as e:
            print(f"❌ Failed to create backup: {e}")
            logging.error(f"Failed to create backup: {e}")
            return None
    
    def analyze_current_schema(self):
        """Analyze and display current database schema"""
        print("\n📋 Current Database Schema Analysis:")
        print("=" * 50)
        
        try:
            # Get all tables
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in self.cursor.fetchall()]
            print(f"Tables: {', '.join(tables)}")
            
            # Get record counts
            for table in tables:
                if table != 'sqlite_sequence':
                    self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = self.cursor.fetchone()[0]
                    print(f"  {table}: {count} records")
            
            # Check for v1.7.0 specific structures
            v170_tables = ['Sessions', 'SessionParticipants', 'DatabaseMetadata']
            missing_tables = [table for table in v170_tables if table not in tables]
            if missing_tables:
                print(f"Missing v1.7.0 tables: {', '.join(missing_tables)}")
            
            # Check Races table structure if it exists
            if 'Races' in tables:
                self.cursor.execute("PRAGMA table_info(Races)")
                races_columns = [col[1] for col in self.cursor.fetchall()]
                v170_columns = ['IsCompleted', 'CompletedAt', 'IPAddress', 'SessionID']
                missing_columns = [col for col in v170_columns if col not in races_columns]
                if missing_columns:
                    print(f"Missing Races columns: {', '.join(missing_columns)}")
                    
        except Exception as e:
            print(f"❌ Schema analysis failed: {e}")
            logging.error(f"Schema analysis failed: {e}")
    
    def migrate_to_v170(self, from_version):
        """Migrate database to version 1.7.0"""
        try:
            print(f"\n🔄 Starting Migration from v{from_version} to v{self.target_version}")
            print("=" * 60)
            
            # Step 1: Create DatabaseMetadata table
            print("📝 Creating DatabaseMetadata table...")
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS DatabaseMetadata (
                    Key TEXT PRIMARY KEY,
                    Value TEXT,
                    UpdatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Step 2: Check if we need table recreation for foreign keys
            needs_recreation = self.check_foreign_key_compatibility()
            
            if needs_recreation:
                print("🔧 Complex migration required - recreating tables with proper foreign keys...")
                self.recreate_tables_with_foreign_keys()
            else:
                print("✨ Simple migration - adding new columns and tables...")
                self.simple_migration()
            
            # Step 3: Create new v1.7.0 tables
            print("🆕 Creating new v1.7.0 tables...")
            self.create_v170_tables()
            
            # Step 4: Migrate existing session data
            print("📦 Migrating existing session data...")
            self.migrate_existing_sessions()
            
            # Step 5: Create performance indexes
            print("⚡ Creating performance indexes...")
            self.create_performance_indexes()
            
            # Step 6: Update database version
            print("🏷️  Updating database version...")
            self.cursor.execute('''
                INSERT OR REPLACE INTO DatabaseMetadata (Key, Value, UpdatedAt)
                VALUES ('schema_version', ?, CURRENT_TIMESTAMP)
            ''', (self.target_version,))
            
            # Step 7: Verify migration
            print("🔍 Verifying migration...")
            self.verify_migration()
            
            self.conn.commit()
            
            print(f"\n✅ Migration completed successfully!")
            print(f"Database upgraded from v{from_version} to v{self.target_version}")
            logging.info(f"Migration completed successfully from v{from_version} to v{self.target_version}")
            
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            logging.error(f"Migration failed: {e}")
            self.conn.rollback()
            raise
    
    def check_foreign_key_compatibility(self):
        """Check if we need to recreate tables for foreign key constraints"""
        try:
            # Check if Sessions table exists
            self.cursor.execute('''
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='Sessions'
            ''')
            sessions_exists = self.cursor.fetchone()
            
            if not sessions_exists:
                return True
            
            # Check if Races table has proper foreign key to Sessions
            self.cursor.execute("PRAGMA foreign_key_list(Races)")
            races_fks = self.cursor.fetchall()
            
            has_sessions_fk = any(fk[2] == 'Sessions' for fk in races_fks)
            
            # Check if Races table has SessionID column
            self.cursor.execute("PRAGMA table_info(Races)")
            races_columns = [col[1] for col in self.cursor.fetchall()]
            
            if 'SessionID' in races_columns and not has_sessions_fk:
                return True
                
            return False
            
        except Exception as e:
            logging.error(f"Error checking foreign key compatibility: {e}")
            return False
    
    def simple_migration(self):
        """Simple migration - just add missing columns"""
        # Add new columns to Races table
        self.add_column_if_not_exists('Races', 'IsCompleted', 'BOOLEAN DEFAULT 0')
        self.add_column_if_not_exists('Races', 'CompletedAt', 'DATETIME NULL')
        self.add_column_if_not_exists('Races', 'IPAddress', 'TEXT DEFAULT "127.0.0.1"')
        self.add_column_if_not_exists('Races', 'SessionID', 'INTEGER')
    
    def recreate_tables_with_foreign_keys(self):
        """Recreate tables with proper foreign key constraints"""
        print("  📋 Backing up existing data...")
        
        # Create backup tables
        tables_to_backup = ['Races', 'Participants', 'Laps']
        for table in tables_to_backup:
            try:
                self.cursor.execute(f'CREATE TABLE {table}_backup AS SELECT * FROM {table}')
                print(f"    ✅ Backed up {table}")
            except Exception as e:
                print(f"    ⚠️  Failed to backup {table}: {e}")
        
        print("  🗑️  Dropping old tables...")
        # Drop in reverse dependency order
        for table in ['Laps', 'Participants', 'Races']:
            try:
                self.cursor.execute(f'DROP TABLE IF EXISTS {table}')
                print(f"    ✅ Dropped {table}")
            except Exception as e:
                print(f"    ⚠️  Failed to drop {table}: {e}")
        
        print("  🏗️  Creating new tables with foreign keys...")
        
        # FIRST: Create Sessions table (required for foreign keys)
        self.cursor.execute('''
            CREATE TABLE Sessions (
                SessionID INTEGER PRIMARY KEY,
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                CompletedAt DATETIME NULL,
                IsCompleted BOOLEAN DEFAULT 0,
                ParticipantCount INTEGER DEFAULT 0,
                ActiveIPs TEXT DEFAULT ''
            )
        ''')
        
        # THEN: Create Races table with foreign key to Sessions
        self.cursor.execute('''
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
        
        # Create Participants table with foreign key
        self.cursor.execute('''
            CREATE TABLE Participants (
                RaceID INTEGER,
                mName TEXT,
                mCarNames TEXT,
                mRacePosition INTEGER,
                mFastestLapTimes REAL,
                mLastLapTimes REAL,
                mLapsCompleted INT,            
                flags TEXT,
                TotalTime REAL,            
                CalculatedPosition INT,
                PitStops INT DEFAULT 0,            
                PRIMARY KEY (RaceID, mName),
                FOREIGN KEY (RaceID) REFERENCES Races(RaceID) ON DELETE CASCADE
            )
        ''')
        
        # Create Laps table with foreign keys
        self.cursor.execute('''
            CREATE TABLE Laps (
                LapID INTEGER PRIMARY KEY AUTOINCREMENT,
                RaceID INTEGER,
                mName TEXT,
                LapNumber INTEGER,
                LapTime REAL,
                FOREIGN KEY (RaceID, mName) REFERENCES Participants(RaceID, mName) ON DELETE CASCADE,
                FOREIGN KEY (RaceID) REFERENCES Races(RaceID) ON DELETE CASCADE
            )
        ''')
        
        print("  📥 Restoring data from backups...")
        
        # Restore data from backups
        self.restore_data_from_backups()
        
        print("  🧹 Cleaning up backup tables...")
        # Clean up backup tables
        for table in tables_to_backup:
            try:
                self.cursor.execute(f'DROP TABLE IF EXISTS {table}_backup')
            except Exception:
                pass
    
    def restore_data_from_backups(self):
        """Restore data from backup tables"""
        try:
            # First, create sessions for existing data (if any SessionIDs exist)
            self.cursor.execute('SELECT DISTINCT SessionID FROM Races_backup WHERE SessionID IS NOT NULL')
            existing_sessions = self.cursor.fetchall()
            
            for (session_id,) in existing_sessions:
                # Get earliest race date for this session
                self.cursor.execute('''
                    SELECT MIN(RaceDate) FROM Races_backup WHERE SessionID = ?
                ''', (session_id,))
                created_at = self.cursor.fetchone()[0]
                
                # Insert into Sessions table
                self.cursor.execute('''
                    INSERT OR IGNORE INTO Sessions 
                    (SessionID, CreatedAt, IsCompleted, ParticipantCount)
                    VALUES (?, ?, 1, 0)
                ''', (session_id, created_at))
            
            # Restore Races data with all columns (including new ones with defaults)
            self.cursor.execute('''
                INSERT INTO Races (
                    RaceID, mTranslatedTrackVariation, mLapsInEvent, 
                    RaceDate, SessionID, IsCompleted, CompletedAt, IPAddress
                )
                SELECT 
                    RaceID, mTranslatedTrackVariation, mLapsInEvent,
                    RaceDate, SessionID, 0, NULL, '127.0.0.1'
                FROM Races_backup
            ''')
            
            # Restore Participants data
            self.cursor.execute('INSERT INTO Participants SELECT * FROM Participants_backup')
            
            # Restore Laps data
            self.cursor.execute('INSERT INTO Laps SELECT * FROM Laps_backup')
            
            print("    ✅ Data restoration completed")
            
        except Exception as e:
            print(f"    ❌ Data restoration failed: {e}")
            raise
    
    def create_v170_tables(self):
        """Create new tables introduced in v1.7.0"""
        # Sessions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Sessions (
                SessionID INTEGER PRIMARY KEY,
                CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                CompletedAt DATETIME NULL,
                IsCompleted BOOLEAN DEFAULT 0,
                ParticipantCount INTEGER DEFAULT 0,
                ActiveIPs TEXT DEFAULT ''
            )
        ''')
        
        # SessionParticipants table for 50% matching
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS SessionParticipants (
                SessionID INTEGER,
                ParticipantName TEXT,
                FirstSeenAt DATETIME DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (SessionID, ParticipantName),
                FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID) ON DELETE CASCADE
            )
        ''')
        
        print("    ✅ Created Sessions and SessionParticipants tables")
    
    def migrate_existing_sessions(self):
        """Migrate existing session data to new Sessions table"""
        try:
            # Get all unique session IDs from existing Races
            self.cursor.execute('SELECT DISTINCT SessionID FROM Races WHERE SessionID IS NOT NULL')
            existing_sessions = self.cursor.fetchall()
            
            migrated_count = 0
            for (session_id,) in existing_sessions:
                # Get earliest race date for this session
                self.cursor.execute('''
                    SELECT MIN(RaceDate) FROM Races WHERE SessionID = ?
                ''', (session_id,))
                created_at = self.cursor.fetchone()[0]
                
                # Get participant count for this session
                self.cursor.execute('''
                    SELECT COUNT(DISTINCT mName) FROM Participants p
                    JOIN Races r ON p.RaceID = r.RaceID
                    WHERE r.SessionID = ?
                ''', (session_id,))
                participant_count = self.cursor.fetchone()[0]
                
                # Insert into Sessions table
                self.cursor.execute('''
                    INSERT OR IGNORE INTO Sessions 
                    (SessionID, CreatedAt, IsCompleted, ParticipantCount)
                    VALUES (?, ?, 1, ?)
                ''', (session_id, created_at, participant_count))
                
                # Populate SessionParticipants
                self.cursor.execute('''
                    INSERT OR IGNORE INTO SessionParticipants (SessionID, ParticipantName)
                    SELECT DISTINCT ?, p.mName FROM Participants p
                    JOIN Races r ON p.RaceID = r.RaceID
                    WHERE r.SessionID = ?
                ''', (session_id, session_id))
                
                migrated_count += 1
            
            print(f"    ✅ Migrated {migrated_count} existing sessions")
            logging.info(f"Migrated {migrated_count} existing sessions")
            
        except Exception as e:
            print(f"    ❌ Failed to migrate existing sessions: {e}")
            logging.error(f"Failed to migrate existing sessions: {e}")
    
    def create_performance_indexes(self):
        """Create performance indexes for multi-race monitoring"""
        indexes = [
            ("idx_races_session", "CREATE INDEX IF NOT EXISTS idx_races_session ON Races(SessionID)"),
            ("idx_races_date", "CREATE INDEX IF NOT EXISTS idx_races_date ON Races(RaceDate)"),
            ("idx_races_completed", "CREATE INDEX IF NOT EXISTS idx_races_completed ON Races(IsCompleted)"),
            ("idx_races_ip", "CREATE INDEX IF NOT EXISTS idx_races_ip ON Races(IPAddress)"),
            ("idx_sessions_completed", "CREATE INDEX IF NOT EXISTS idx_sessions_completed ON Sessions(IsCompleted)"),
            ("idx_sessions_created", "CREATE INDEX IF NOT EXISTS idx_sessions_created ON Sessions(CreatedAt)"),
            ("idx_session_participants", "CREATE INDEX IF NOT EXISTS idx_session_participants ON SessionParticipants(SessionID)"),
            ("idx_participants_race", "CREATE INDEX IF NOT EXISTS idx_participants_race ON Participants(RaceID)"),
            ("idx_laps_race", "CREATE INDEX IF NOT EXISTS idx_laps_race ON Laps(RaceID)"),
            ("idx_laps_name", "CREATE INDEX IF NOT EXISTS idx_laps_name ON Laps(mName)")
        ]
        
        created_count = 0
        for index_name, index_sql in indexes:
            try:
                self.cursor.execute(index_sql)
                created_count += 1
            except Exception as e:
                print(f"    ⚠️  Failed to create index {index_name}: {e}")
        
        print(f"    ✅ Created {created_count}/{len(indexes)} performance indexes")
    
    def add_column_if_not_exists(self, table_name, column_name, column_definition):
        """Add a column to a table if it doesn't already exist"""
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if column_name not in columns:
                self.cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}")
                print(f"    ✅ Added column {column_name} to {table_name}")
                
        except Exception as e:
            print(f"    ❌ Failed to add column {column_name} to {table_name}: {e}")
    
    def verify_migration(self):
        """Verify that migration was successful"""
        try:
            # Check database version
            self.cursor.execute('''
                SELECT Value FROM DatabaseMetadata WHERE Key = 'schema_version'
            ''')
            result = self.cursor.fetchone()
            version = result[0] if result else 'Unknown'
            
            if version != self.target_version:
                raise Exception(f"Version mismatch: expected {self.target_version}, got {version}")
            
            # Check required tables exist
            required_tables = ['Races', 'Participants', 'Laps', 'Sessions', 'SessionParticipants', 'DatabaseMetadata']
            self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in self.cursor.fetchall()]
            
            missing_tables = [table for table in required_tables if table not in existing_tables]
            if missing_tables:
                raise Exception(f"Missing required tables: {missing_tables}")
            
            # Check foreign key constraints
            self.cursor.execute("PRAGMA foreign_key_check")
            fk_violations = self.cursor.fetchall()
            if fk_violations:
                print(f"    ⚠️  Found {len(fk_violations)} foreign key violations")
                for violation in fk_violations[:5]:  # Show first 5
                    print(f"        {violation}")
            else:
                print("    ✅ All foreign key constraints verified")
            
            # Get final record counts
            print("    📊 Final record counts:")
            for table in required_tables:
                if table != 'sqlite_sequence':
                    self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = self.cursor.fetchone()[0]
                    print(f"        {table}: {count} records")
            
            print(f"    ✅ Migration verification completed - Database is now v{version}")
            
        except Exception as e:
            print(f"    ❌ Migration verification failed: {e}")
            raise
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("📪 Database connection closed")

def main():
    """Main migration function"""
    print("🚀 AMS2 RaceScore Database Migration Utility v1.7.0")
    print("=" * 60)
    
    # Get database file from command line or use default
    db_file = sys.argv[1] if len(sys.argv) > 1 else 'RaceDB.db'
    
    if not os.path.exists(db_file):
        print(f"❌ Database file not found: {db_file}")
        sys.exit(1)
    
    migrator = None
    try:
        # Initialize migrator
        migrator = DatabaseMigrator(db_file)
        
        # Detect current version
        current_version = migrator.detect_current_version()
        print(f"📋 Current database version: {current_version}")
        
        # Check if migration is needed
        if migrator.version_compare(current_version, migrator.target_version) >= 0:
            print(f"✅ Database is already at or newer than v{migrator.target_version}")
            print("No migration needed!")
            return
        
        # Analyze current schema
        migrator.analyze_current_schema()
        
        # Ask for confirmation
        print(f"\n⚠️  Migration Required:")
        print(f"   From: v{current_version}")
        print(f"   To:   v{migrator.target_version}")
        print("\nThis migration will:")
        print("   • Add multi-race monitoring capabilities")
        print("   • Create Sessions and SessionParticipants tables")
        print("   • Add performance indexes")
        print("   • Preserve all existing race data")
        print("   • Create automatic backup")
        
        response = input("\nProceed with migration? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("Migration cancelled by user")
            return
        
        # Create backup
        backup_file = migrator.backup_database()
        if not backup_file:
            response = input("Failed to create backup. Continue anyway? (y/N): ").strip().lower()
            if response not in ['y', 'yes']:
                print("Migration cancelled due to backup failure")
                return
        
        # Run migration
        success = migrator.migrate_to_v170(current_version)
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print(f"   Database upgraded from v{current_version} to v{migrator.target_version}")
            if backup_file:
                print(f"   Backup saved to: {backup_file}")
            print("\nYour AMS2 RaceScore application now supports multi-race monitoring!")
        
    except KeyboardInterrupt:
        print("\n❌ Migration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        logging.error(f"Migration failed: {e}")
        sys.exit(1)
    finally:
        if migrator:
            migrator.close()

if __name__ == "__main__":
    main()
