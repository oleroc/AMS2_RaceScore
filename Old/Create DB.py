def create_database():
    conn = sqlite3.connect('RaceDB.db')
    cursor = conn.cursor()

    # Create Races table with a RaceDate column
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Races (
            RaceID INTEGER PRIMARY KEY,
            RaceIndex TEXT UNIQUE,
            mTranslatedTrackVariation TEXT,
            mLapsInEvent INTEGER,
            RaceDate TEXT DEFAULT (date('now')),
            SessionID INTEGER,
        )
    ''')

    # Create Participants table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Participants (
            RaceID INTEGER,
            mName TEXT,
            mCarNames TEXT,
            mRacePosition INTEGER,
            mFastestLapTimes REAL,
            mLastLapTimes REAL,
            PRIMARY KEY (RaceID, mName),
            FOREIGN KEY (RaceID) REFERENCES Races(RaceID) ON DELETE CASCADE
        )
    ''')

    # Create Laps table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Laps (
            LapID INTEGER PRIMARY KEY AUTOINCREMENT,
            RaceID INTEGER,
            mName TEXT,
            LapNumber INTEGER,
            LapTime REAL,
            FOREIGN KEY (RaceID) REFERENCES Races(RaceID) ON DELETE CASCADE,
            FOREIGN KEY (mName) REFERENCES Participants(mName) ON DELETE CASCADE
        )
    ''')

    # Create Drivers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Drivers (
            Phone INTEGER PRIMARY KEY,
            Name TEXT UNIQUE       
        )
    ''')

    # Create Score table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Score (
            ScoreID INTEGER PRIMARY KEY AUTOINCREMENT,
            RaceID INTEGER,
            mName TEXT,
            place INTEGER,
            score INTEGER,
            SessionID INTEGER,
            FOREIGN KEY (RaceID) REFERENCES Races(RaceID) ON DELETE CASCADE,
            FOREIGN KEY (mName) REFERENCES Participants(mName) ON DELETE CASCADE,
            FOREIGN KEY (SessionID) REFERENCES Sessions(SessionID) ON DELETE CASCADE
        )
    ''')

    # Create HighScore table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS HighScore (
            HighScoreID INTEGER PRIMARY KEY AUTOINCREMENT,
            phone INTEGER,
            Name TEXT,
            place INTEGER,
            BestLap REAL,
            mTrackvariation TEXT,
            MCarName TEXT,
            FOREIGN KEY (phone) REFERENCES Drivers(Phone) ON DELETE CASCADE,
            FOREIGN KEY (Name) REFERENCES Drivers(Name)
        )
    ''')
 
     
    conn.commit()
    conn.close()
