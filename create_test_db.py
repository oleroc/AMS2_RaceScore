#!/usr/bin/env python3
"""
Test migration utility functionality
"""
import sqlite3
import os

# Create a legacy v1.6.0 database for testing
test_db = "test_legacy_v16.db"

if os.path.exists(test_db):
    os.remove(test_db)

conn = sqlite3.connect(test_db)
cursor = conn.cursor()

# Create v1.6.0 structure (with SessionID but without v1.7.0 features)
cursor.execute('''
    CREATE TABLE Races (
        RaceID INTEGER PRIMARY KEY,
        mTranslatedTrackVariation TEXT,
        mLapsInEvent INTEGER,
        RaceDate TEXT DEFAULT (date('now')),
        SessionID INTEGER
    )
''')

cursor.execute('''
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
        PRIMARY KEY (RaceID, mName)
    )
''')

cursor.execute('''
    CREATE TABLE Laps (
        LapID INTEGER PRIMARY KEY AUTOINCREMENT,
        RaceID INTEGER,
        mName TEXT,
        LapNumber INTEGER,
        LapTime REAL
    )
''')

# Add some test data
cursor.execute("INSERT INTO Races VALUES (1, 'Spielberg GP - Austria', 10, '2025-08-05', 1)")
cursor.execute("INSERT INTO Participants VALUES (1, 'TestDriver', 'McLaren MP4/13', 1, 85.5, 87.2, 10, '', 850.0, 1, 0)")
cursor.execute("INSERT INTO Laps VALUES (1, 1, 'TestDriver', 1, 87.2)")

conn.commit()
conn.close()

print(f"Created legacy v1.6.0 test database: {test_db}")
print("Now testing migration...")
