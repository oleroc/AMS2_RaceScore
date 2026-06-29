from re import L, T; from timeit import Timer; import sys, re, requests, sqlite3, queue, json, time, traceback, logging, os, asyncio, aiohttp, math, base64, configparser, tempfile
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QTabWidget, QSpacerItem, QMessageBox, QLineEdit
from PyQt5.QtGui import QPixmap, QIcon, QFontDatabase
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer, QObject, QEvent
from datetime import datetime
from file_base64_strings import (Driver_Statistics_Background_img_base64, High_scores_Background_img_base64, Race_results_Background_img_base64, Race_scores_Background_img_base64, liverace_liveview_img_base64, liverace_status_img_base64, icon_base64, sui_generis_rg_font_base64)
if os.path.exists('debug.log'): # Set up logging
    os.remove('debug.log')
logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 


class ConfigManager:
    def __init__(self, db_queue):
        self.config_file = 'config.ini'
        self.__version__ = "1.5.4"
        self.__author__ = "RockyTM"
        self.__email__ = "post@drs.no"
        self.__date__ = "2024-09-15"
        self.__description__ = "Script for getting Race Data from AMS2"
        self.config = configparser.ConfigParser()
        self.db_queue = db_queue

    def update_config_file(self, gui_window):
        # Define the required sections and fields
        required_fields = {
            'config': {
                'ip_address': '127.0.0.1',
                'width': '1150',
                'height': '1150',
                'titlebar': 'True',
                'write_cp_scores': 'False',
                'version': self.__version__,
                'author': self.__author__,
                'email': self.__email__,
                'path_to_cp_scores': 'C:\\force\\gui\\',
                'extra_data': 'False'
            },
            'Score Table': {
                '1_place': '25',
                '2_place': '18',
                '3_place': '15',
                '4_place': '12',
                '5_place': '10',
                '6_place': '8',
                '7_place': '6',
                '8_place': '4',
                '9_place': '2',
                '10_place': '1',
                'best_lap': '5'
            }
        }

        try:
            if not os.path.exists(self.config_file):
                self.config.read_dict(required_fields) # If config file does not exist, create it with all default values
                with open(self.config_file, 'w') as configfile: self.config.write(configfile)
                self.add_comments()
                print(f"Config file created with all default settings at {self.config_file}.")
                logging.info(f"Config file created with all default settings at {self.config_file}.")
            else:
                self.config.read(self.config_file) # Read the existing config file
                existing_version = self.config['config'].get('version')
                current_version_parts = self.__version__.split(".")
                existing_version_parts = existing_version.split(".")
                if existing_version != self.__version__ and existing_version != None: # Check if the existing version matches the current version
                    if current_version_parts[1] != existing_version_parts[1]:
                        response = gui_window.show_version_update_message(existing_version, self.__version__)  # Call the method in the GUI class to show the message
                        if response:self.db_queue.put(('delete_db', ()))  # If OK was clicked, proceed
                        else:
                            print("User canceled the version update. Exiting program.")
                            sys.exit()  # Quit the program
                    self.config['config']['version'] = self.__version__  # Update the version information
                    changes_made = True
                    print(f"Version updated from {existing_version} to {self.__version__}.")
                    logging.info(f"Version updated from {existing_version} to {self.__version__}.")
                        
                else: changes_made = False
                for section, fields in required_fields.items(): # Check for missing sections and fields
                    if not self.config.has_section(section):
                        self.config.add_section(section)
                        changes_made = True
                    for field, value in fields.items():
                        if not self.config.has_option(section, field):
                            self.config.set(section, field, value)
                            changes_made = True
                if changes_made: # Save the updated config file if changes were made
                    with open(self.config_file, 'w') as configfile: self.config.write(configfile)
                    self.add_comments()
                    print(f"Config file at {self.config_file} updated with missing fields.")
                    logging.info(f"Config file at {self.config_file} updated with missing fields.")
                    self.config.read(self.config_file) # Read the updated config file
                else: logging.info("All required fields are already present in the config file.")
                    
        except (configparser.Error, IOError) as e:
            print(f"An error occurred while ensuring required fields in the config file: {e}")
            logging.info(f"An error occurred while ensuring required fields in the config file: {e}")
            return None

    def add_comments(self): # Now, add comments manually after specific fields
        with open(self.config_file, 'r+') as configfile:
            lines = configfile.readlines()
            configfile.seek(0)
            for line in lines: 
                configfile.write(line)
                if line.strip().startswith('ip_address'):
                    configfile.write("; The IP address of game running the API\n")
                elif line.strip().startswith('write_cp_scores'):
                    configfile.write("; Should be False, unless you have an external app that needs to read from files instead of DB (True/False)\n")
            configfile.truncate()

    def read_cp_status(self):
        #config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file) #Read the existing config file
            return self.config.get('config', 'write_cp_scores', fallback='False').strip().lower() == 'true' # Return the data from the config and convert to boolean
        except (configparser.Error, IOError) as e:
            print(f"An error occurred while accessing the config file: {e}")
            logging.info(f"An error occurred while accessing the config file: {e}")
            return None   
        
    def read_ip_address(self):
        #config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file) #Read the existing config file
            return self.config['config']['ip_address'] # Return the IP address from the config
        except (configparser.Error, IOError) as e:
            print(f"An error occurred while accessing the config file: {e}")
            logging.info(f"An error occurred while accessing the config file: {e}")
            return None
        
    def rad_config_file(self):
        #config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file) #Read the existing config file

            return self.config
        except (configparser.Error, IOError) as e:
            print(f"An error occurred while accessing the config file: {e}")
            logging.info(f"An error occurred while accessing the config file: {e}")
            return None

    def get_metadata(self):
        return {
            'version': self.__version__,
            'author': self.__author__,
            'email': self.__email__,
            'date': self.__date__,
            'description': self.__description__,
        }
    
class DatabaseThread(QThread):
    race_data_loaded_signal = pyqtSignal(object, object, object)
    load_race_on_start_signal = pyqtSignal(object, object)
    score_data_signal = pyqtSignal(object, object, object)
    load_sessionid_on_start_signal = pyqtSignal(object)
    write_cp_signal = pyqtSignal(object, object)
    load_highscores_on_start_signal = pyqtSignal(object)
    highscore_data_loaded_signal = pyqtSignal(object)
    drivers_signal = pyqtSignal(object)

    def __init__(self, db_queue, config_manager):
        super().__init__()
        self.db_queue = db_queue
        self.running = True
        self.config_manager = config_manager
        self.db_name = 'RaceDB.db'
        self.conn = None

    def run(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        #self.cursor.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
        self.create_database()
        #self.migrate_laps_table()
        while self.running:
            try:
                operation, args = self.db_queue.get()
                logging.info(f"Operation: {operation} Args: {args}")
                print(f"DB Queue Called: {operation} ")
                if operation == 'stop':
                    self.running = False
                    self.conn.close()  # Close the connection after the race ends
                    self.conn = None
                    break
                else: self.process_queue(operation, *args)
            except Exception as e: logging.error(f"DB Unpack failed: Operation: {operation} Message: {e}")
            finally: 
                self.db_queue.task_done()

    def process_queue(self, operation, *args):
        try:
            if operation == 'write_race':self.write_race(*args)
            elif operation == 'insert_lap_data': self.insert_lap_data(*args)
            elif operation == 'finalize_race': self.finalize_race(*args)
            elif operation == 'delete_race': self.delete_race(*args)
            elif operation == 'delete_driver': self.delete_driver(*args)
            elif operation == 'get_latest_race_id': self.get_latest_race_id(*args)
            elif operation == 'get_latest_session_id': self.get_latest_session_id(*args)
            elif operation == 'load_selected_race': self.load_selected_race(*args)
            elif operation == 'load_race_data_on_start': self.load_race_data_on_start(*args)
            elif operation == 'load_sessionid_on_start': self.load_sessionid_on_start(*args)
            elif operation == 'load_score_data': self.load_score_data(*args)
            elif operation == 'delete_db': self.delete_db()
            elif operation == 'delete_all_races': self.delete_all_races()
            elif operation == 'load_highscores_on_start': self.load_highscores_on_start()
            elif operation == 'load_highscores': self.load_highscores(*args)
            elif operation == 'load_driver_statistics_on_start': self.load_driver_statistics_on_start()
            else: 
                logging.error(f"DB Unknown operation: {operation}")
                print(f"DB Unknown operation: {operation}")

        except Exception as e:
            logging.error(f"DB Operation failed: {e}")
            print(f"DB Operation failed: {e}")
                
    def create_database(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Races (
                RaceID INTEGER PRIMARY KEY,
                mTranslatedTrackVariation TEXT,
                mLapsInEvent INTEGER,
                RaceDate TEXT DEFAULT (date('now')),
                SessionID INTEGER
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Participants (
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
        self.cursor.execute('''
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
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS Drivers (
                DriverID INTEGER PRIMARY KEY,
                Name TEXT UNIQUE,
                Phone INTEGER UNIQUE,
                RaceDate TEXT DEFAULT (date('now'))
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS HighScore (
                HighScoreID INTEGER PRIMARY KEY AUTOINCREMENT,
                phone INTEGER,
                Name TEXT,
                lapnumber INTEGER,
                BestLap REAL,
                mTrackvariation TEXT,
                MCarName TEXT,
                FOREIGN KEY (phone) REFERENCES Drivers(Phone) ON DELETE CASCADE,
                FOREIGN KEY (Name) REFERENCES Drivers(Name)
            )
        ''')
        self.conn.commit()    

    def delete_all_races(self):
        self.cursor.execute('DELETE FROM Laps')
        self.cursor.execute('DELETE FROM Participants')
        self.cursor.execute('DELETE FROM races')
        # Commit the transaction to close it before running VACUUM
        self.connection.commit()
        # Optionally, reset auto-increment counters for the tables
        self.cursor.execute('DELETE FROM sqlite_sequence WHERE name="Laps"')
        self.cursor.execute('DELETE FROM sqlite_sequence WHERE name="Participants"')
        self.cursor.execute('DELETE FROM sqlite_sequence WHERE name="races"')
        self.connection.commit()
        self.cursor.execute('VACUUM')  # Optional: to reclaim space after deleting rows
        self.connection.commit()

    def delete_db(self):
        # Close the current database connection
        self.conn.close()

        # Delete the database file
        if os.path.exists(self.db_name):
            os.remove(self.db_name)
            print(f"Database file {self.db_name} deleted.")
            logging.info(f"Database file {self.db_name} deleted.")
        else:
            print(f"Database file {self.db_name} does not exist.")
            logging.info(f"Database file {self.db_name} does not exist.")

        # Recreate the database (reopen connection and reinitialize)
            # Reopen the database connection
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()    
        self.create_database()
        self.conn.commit()

    def load_score_data(self,session_id):
        try:
            logging.info("DB Executing race query for get score data ...")
            self.cursor.execute('''
                SELECT *
                FROM Races
                WHERE SessionID = ?
           
           ''', (session_id,))
            
            race_table = self.cursor.fetchall()
            logging.info(f"DB Race table: {race_table} where session id: {session_id}")
            race_ids = [race[0] for race in race_table]  # This will give you a list of all race IDs
            logging.info(f"DB List of all Race_ids: {race_ids}")
            if not race_ids: # Check if race_ids is empty
                print(f"Race_ids fetched: {race_ids}")  # Debugging output
                logging.info(f"DB check if race id's are empty Race_ids fetched: {race_ids}")
                logging.info("DB No Race id's, emitting None")
                self.score_data_signal.emit(None, None, None)
                return
            query = '''
                SELECT *
                FROM laps
                WHERE RaceID IN ({})
            '''.format(','.join('?' * len(race_ids)))
            self.cursor.execute(query, race_ids)
            laps = self.cursor.fetchall()
            logging.info(f"DB Laps fetched: {laps} with {race_ids}")
            if not laps:
                print("DB No scores found, emitting None.")
                logging.info("DB No scores found, emitting None.")
                self.score_data_signal.emit(None, None, None)
                return
            query = '''
                SELECT *
                FROM participants
                WHERE RaceID IN ({})
            '''.format(','.join('?' * len(race_ids)))
            self.cursor.execute(query, race_ids)
            participants = self.cursor.fetchall()
            logging.info(f"DB Best Participants fetched: {participants} with {race_ids}")
            if not participants:
                print("DB No participants found, emitting None.")
                logging.info("DB No best laps list found, emitting None.")
                self.score_data_signal.emit(None, None, None)
                return
            if laps and race_table and participants:
               logging.info("DB Emitting score data signal")
               self.score_data_signal.emit(race_table, participants,laps,)
            else:
               logging.info("DB No laps, race_tables or participants found, emitting None")
               self.score_data_signal.emit(None, None, None)
               
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            self.score_data_signal.emit(None, None, None)

    def delete_race(self, race_id, callback):
        try:
            print(f"DB Raceid to delete: {race_id}")
            logging.info(f"DB Race_iD Race_ID: {race_id}")
            self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
            self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
            self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
            self.conn.commit()
            if callback:
                    logging.info(f"DB Callback {race_id}")
                    callback(race_id)  # Pass the deleted race_id back to the main thread
            else:
                if callback:
                    logging.info("DB Callback None")
                    callback(None)  # No race found
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback:
                callback(None)

    def delete_driver(self, driver_name, callback):
        try:
            self.cursor.execute('DELETE FROM Drivers WHERE Name = ?', (driver_name,))
            self.conn.commit()
            if callback:
                callback(driver_name)  # Pass the deleted driver name back to the main thread
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback:
                callback(None)

    def load_driver_statistics_on_start(self):
        logging.info("DB Load driver statistics on start")
        print("DB Load driver statistics on start")
        try:
            self.cursor.execute('''
                SELECT Name, Lapnumber, BestLap, MTrackvariation, mCarName
                FROM HighScore
                ORDER BY Name ASC
                ''')
            driverdata = self.cursor.fetchall()
            if driverdata:
                self.drivers_signal.emit(driverdata)
            else:
                self.drivers_signal.emit(None)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            self.drivers_signal.emit(None)

    def load_highscores(self, car, track):
        print(f"DB Load High Scores: Track: {track} Car: {car}")
        try:
            self.cursor.execute('''
                SELECT Name, lapnumber, BestLap, mTrackvariation, MCarName
                FROM HighScore
                WHERE mTrackvariation = ? AND MCarName = ?
                ORDER BY BestLap ASC
            ''', (track, car))
            high_scores = self.cursor.fetchall()
            print(f"DB High Scores fetched: {high_scores}")
            logging.info(f"DB High Scores fetched: {high_scores}")
            if high_scores:
                logging.info("DB High Scores found, emitting signal")
                self.highscore_data_loaded_signal.emit(high_scores)
            else:
                logging.info("DB No High Scores found, emitting None")
                self.highscore_data_loaded_signal.emit(None)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            self.highscore_data_loaded_signal.emit(None)

    def load_highscores_on_start(self):
        try:
            self.cursor.execute('''
                SELECT Name, lapnumber, BestLap, mTrackvariation, MCarName
                FROM HighScore
                ORDER BY mTrackvariation ASC
            ''')
            high_scores = self.cursor.fetchall()
            logging.info(f"DB High Scores fetched: {high_scores}")
            if high_scores:
                logging.info("DB High Scores found, emitting signal")
                self.load_highscores_on_start_signal.emit(high_scores)
            else:
                logging.info("DB No High Scores found, emitting None")
                self.load_highscores_on_start_signal.emit(None)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            self.load_highscores_on_start_signal.emit(None)

    def load_race_data_on_start(self, callback=None):    
        try:
            self.cursor.execute('''
                SELECT RaceID, mTranslatedTrackVariation, mLapsInEvent, RaceDate
                FROM Races
                ORDER BY RaceID ASC
            ''')
            races = self.cursor.fetchall()
            if races:
                for race in races:
                    race_id = race[0]
                    self.cursor.execute('SELECT COUNT(*) FROM Laps WHERE RaceID = ?', (race_id,)) # Check if there are any laps recorded for the last RaceID
                    rows_in_race = self.cursor.fetchone()[0]  # This will give the count of laps
                    
                    self.cursor.execute('SELECT COUNT(*) FROM Participants WHERE RaceID = ?', (race_id,)) # check if there are any participants in the race
                    rows_in_participants = self.cursor.fetchone()[0]  # This will give the count of participants
                    if rows_in_race == 0 or rows_in_participants == 0: # delete race if there are not laps or participants
                        print(f"DB Raceid to delete: {race_id}")
                        logging.info(f" No Rows or participants, DB Race id to delete: {race_id}")
                        self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
                        self.conn.commit() 
                        print(f"DB No laps or participants, race deleted with race_id:{race_id}")
                        logging.info(f"DB No laps or participants, race deleted with race_id:{race_id}")
                logging.info(f"DB Load race data on start all Races: {races}")
                self.cursor.execute('''
                    SELECT RaceID, mCarNames
                    FROM Participants
                    ORDER BY RaceID ASC
                ''')
                participants = self.cursor.fetchall()
                logging.info(f"DB Paticipants carNames and RaceID fetched: {participants}")
                if participants:
                    self.load_race_on_start_signal.emit(races,participants) # Emit the signal with the results in the main thread
                    logging.info(f"DB Load race on start signal emitted")
                else:
                    logging.info(f"DB No participants found, emitting None")
                    print("DB No participants found, emitting None")
                    self.load_race_on_start_signal.emit(None, None)
            else:
                logging.info(f"DB No races found, emitting None")
                print("DB No races found, emitting None")
                self.load_race_on_start_signal.emit(None, None)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"DB Load Race on start failed:  {e}")
            if callback:
                callback.emit([])  # Emit an empty list in case of error

    def load_sessionid_on_start(self):
        try:
            self.cursor.execute('''
                SELECT DISTINCT sessionID
                FROM Races
                ORDER BY RaceID ASC
            ''')
            sessionids = self.cursor.fetchall()
            logging.info(f"DB Load session id on start sessionids: {sessionids} fetched from Races")
            sessionids = [sessionid[0] for sessionid in sessionids]
            logging.info(f"DB Load session id on start, last session ID: {sessionids}")
            if sessionids:
                logging.info(f"DB Session ID valid, emitting signal")
                self.load_sessionid_on_start_signal.emit(sessionids) # Emit the signal with the results in the main thread
            else:
                print(f"DB Session ID not fetched: {sessionids}")
                logging.info(f"DB Session ID not fetched: {sessionids}, emitting empty list")
                self.load_sessionid_on_start_signal.emit([1])
        except Exception as e:
            logging.error(f"DB Load_session_id_on_start failed: {e}")
            print(f"DB Load_session_id_on_start failed: {e}")
            self.load_sessionid_on_start_signal.emit([1])
        
    def load_selected_race(self, race_id, callback = None):
        try:
            self.cursor.execute('''
                SELECT RaceID, mTranslatedTrackVariation, mLapsInEvent, sessionID
                FROM Races
                WHERE RaceID = ?
            ''', (race_id,))
            race = self.cursor.fetchone()
            logging.info(f"DB Load selected race: {race}")
            if race:
                logging.info(f"DB Race valid, fetching participants and laps with raceID: {race[0]}")
                self.cursor.execute('''
                    SELECT mName, mRacePosition, mFastestLapTimes, mLastLapTimes, mCarNames, flags, PitStops
                    FROM Participants
                    WHERE RaceID = ?
                    ORDER BY mRacePosition ASC
                ''', (race[0],))
                participants = self.cursor.fetchall()
                logging.info(f"DB Load selected race participants: {participants} fetched with raceID:{race[0]}")
                
                self.cursor.execute('''
                    SELECT LapID, RaceID, mName, LapNumber, LapTime
                    FROM Laps
                    WHERE RaceID = ?
                ''', (race[0],))
                laps = self.cursor.fetchall()
                logging.info(f"DB Load selected race laps: {laps}")
                logging.info(f"DB Load selected race signal emitted") # Call the callback with the fetched data
                self.race_data_loaded_signal.emit(race, participants, laps)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Load Selected Races failed: {e}")
            if callback: callback(None)
            
    def get_latest_session_id(self, callback=None):
        try:
            self.cursor.execute('SELECT MAX(SessionID) FROM Races')
            result = self.cursor.fetchone()
            session_id = result[0]
            self.cursor.execute('select MAX(RaceDate) from Races')
            result = self.cursor.fetchone()
            dato = result[0]
            logging.info(f"DB Date result: {dato}")
            logging.info(f"DB Session ID result: {session_id}")
            if session_id:
                if callback:
                    logging.info("DB Invoking callback with session_id")
                    callback(session_id, dato)
            else:
                if callback:
                    print("DB No Session ID. Invoking callback with session_id None")
                    logging.info("DB No Session ID. Invoking callback with session_id None")
                    callback(1, None)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Database operation get_latest_session_id failed: {e}")
            if callback:
                callback(None, None)
                print(f"DB no session stored, sending default 1: {e}")
                logging.info(f"DB no session stored, sending default 1: {e}")
                
    def get_latest_race_id(self, callback =None):
        try:
            self.cursor.execute('SELECT RaceID FROM Races ORDER BY RaceID DESC LIMIT 1')
            result = self.cursor.fetchone()
            logging.info(f"DB Last RaceID in races, Result: {result}")
            if result:
                logging.info("DB Result is valid")
                last_race_id = result[0]  # Extract the RaceID from the tuple
                logging.info(f"DB Result valid, calling back last_race_id:{last_race_id}")
                if callback and callable(callback): callback(last_race_id)
                else: 
                    logging.info(f"No Callback, returning Rac_id: {last_race_id}")
                    return last_race_id  # Return the race ID if no valid callback is provided

            else:
                return None  # Return None if no race ID was found
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Database operation failed: {e}")
            if callback and callable(callback):callback(None) 

    def write_race(self, data, session_id):
        try:
            track_info = f"{data['eventInformation']['mTranslatedTrackLocation']} - {data['eventInformation']['mTranslatedTrackVariation']}" # Concatenate mTranslatedTrackLocation and mTranslatedTrackVariation
            logging.info(f"DB track_info to write:{track_info}")
            print(f"DB track_info to write:{track_info}")
            self.cursor.execute('''
                INSERT OR IGNORE INTO Races (mTranslatedTrackVariation, mLapsInEvent, SessionID)
                VALUES (?, ?, ?)
            ''', (track_info, data['eventInformation']['mLapsInEvent'], session_id,))
            # write drivers
            for participant in data['participants']['mParticipantInfo']:
                # Step 1: Check if the driver already exists by name
                self.cursor.execute('''
                    SELECT Phone FROM Drivers WHERE Name = ?
                ''', (participant['mName'],))
                
                existing_driver_phone = self.cursor.fetchone()

                if existing_driver_phone:
                    # Step 2: Driver exists, update RaceDate
                    self.cursor.execute('''
                        UPDATE Drivers
                        SET RaceDate = date('now')
                        WHERE Name = ?
                    ''', (participant['mName'],))
                else:
                    # Step 3: Driver doesn't exist, get the latest phone number
                    self.cursor.execute('''
                        SELECT MAX(Phone) FROM Drivers
                    ''')
                    latest_phone = self.cursor.fetchone()[0]
                    
                    # If no phone numbers exist, start from 90000001
                    if latest_phone is None:
                        new_phone = 90000001
                    else:
                        new_phone = latest_phone + 1

                    # Step 4: Insert new driver with incremented phone number
                    self.cursor.execute('''
                        INSERT INTO Drivers (Name, Phone, RaceDate)
                        VALUES (?, ?, date('now'))
                    ''', (participant['mName'], new_phone))       
            logging.info("DB Race Written to DB")
            print("DB Race Written to DB")
            self.conn.commit()
        except Exception as e:
            print(f"Failed to write race data to the database: Program Crash! {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            self.conn.close()  # Ensure the connection is closed
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")
            
    def insert_lap_data(self, race_id, name, current_lap, lap_time, track, car):
        print("DB Insert Lap DATA entered")
        try:
            logging.info(f"DB Def insert lap data entered, data to be written:Race_id:{race_id}, p_name:{name}, lap:{current_lap}, lap time:{lap_time}")
            self.cursor.execute('''
                INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
                VALUES (?, ?, ?, ?)
            ''', (race_id, name, current_lap, lap_time))
            logging.info("DB Lap data written")

            # Step 1: Get the driver by name
            self.cursor.execute('''
                SELECT Name
                FROM Drivers
                WHERE Name = ?
            ''', (name,))
            result = self.cursor.fetchone()
            logging.info(f"DB Driver name fetched: {result}")
            self.cursor.execute('''
                SELECT Phone FROM Drivers WHERE Name = ?
                ''', (name,))
            phone = self.cursor.fetchone()
            logging.info(f"DB Phone number fetched: {phone}")
            if phone:
                phone = phone[0]
            if result:
                driver_name = result[0]  # Get the driver's name

                # Step 2: Check if driver has a record in HighScore for this track and car
                self.cursor.execute('''
                    SELECT BestLap
                    FROM HighScore
                    WHERE Name = ? AND mTrackvariation = ? AND MCarName = ?
                ''', (driver_name, track, car))
                
                highscore_result = self.cursor.fetchone()

                if highscore_result:
                    best_lap_time = highscore_result[0]

                    # Step 3: Check if the new lap time is better than the existing one
                    if lap_time < best_lap_time:
                        # Step 4: Update the high score if the new lap time is better
                        self.cursor.execute('''
                            UPDATE HighScore
                            SET lapnumber = ?, BestLap = ?
                            WHERE Name = ? AND mTrackvariation = ? AND MCarName = ?
                        ''', (current_lap, lap_time, driver_name, track, car))
                        logging.info("DB HighScore updated with a new best lap time")
                else:
                    # Step 4: Insert a new high score if no record exists for this track and car
                    self.cursor.execute('''
                        INSERT INTO HighScore (phone, Name, lapnumber, BestLap, mTrackvariation, MCarName)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (phone, driver_name, current_lap, lap_time, track, car))
                    logging.info("DB New HighScore inserted")
                
                # Commit the changes
                self.conn.commit()

        except Exception as e:
            print(f"Failed to write Lap data to the database: Program Crash! {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            self.conn.close()  # Ensure the connection is closed
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")
            
    def finalize_race(self, data, lap_times_dict, flags_dict, pit_stops_dict):
        try:
            logging.info(f"DB Def finalize entered")
            participants = data['participants']['mParticipantInfo']
            logging.info(f"Finalizing DB, Lap times dict:{lap_times_dict} flags: {flags_dict}")    
            race_id = self.get_latest_race_id() # Get the RaceID for the last
            print(f"Finalizing Race with Race ID: {race_id}")
            self.cursor.execute('SELECT COUNT(*) FROM Laps WHERE RaceID = ?', (race_id,)) # Check if there are any laps recorded for the last RaceID
            rows_in_race = self.cursor.fetchone()[0]  # This will give the count of laps
            if rows_in_race == 0:
                logging.info("DB No rows, returning")
                print("No Rows in DB, returning")
                return
            driver_total_times_dict = {}
            for driver, lap_times in lap_times_dict.items():
                driver_total_times_dict[driver] = sum(lap_times)
            ranked_drivers = self.calculate_score(participants, flags_dict, driver_total_times_dict)
            for participant in participants:
                participant_name = participant['mName']
                if participant['mFastestLapTimes'] == -123.0:
                    participant['mFastestLapTimes'] = None
                if participant['mLastLapTimes'] == -123.0:
                    participant['mLastLapTimes'] = None
                flags_data = flags_dict.get(participant_name, None) # Retrieve the flag data for this participant from the dictionary
                if participant_name in driver_total_times_dict:
                    laps_completed = len(lap_times_dict.get(participant_name, 0))
                else:
                    laps_completed = 0
                if participant_name in driver_total_times_dict: driver_total_times = driver_total_times_dict[participant_name]
                else: driver_total_times = 0
                if participant['mName'] in pit_stops_dict: pit_stops = sum(pit_stops_dict[participant['mName']].values())
                else: pit_stops = 0

                self.cursor.execute('''
                    INSERT OR REPLACE INTO Participants (
                        RaceID, mName, mCarNames, mRacePosition, mFastestLapTimes, mLastLapTimes, mLapsCompleted, flags, TotalTime, CalculatedPosition, PitStops
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    race_id,
                    participant_name,
                    participant['mCarNames'],
                    participant['mRacePosition'],
                    participant['mFastestLapTimes'],
                    participant['mLastLapTimes'],
                    laps_completed,
                    flags_data,
                    driver_total_times,
                    ranked_drivers.index(participant_name) + 1,
                    pit_stops
                ))
            self.conn.commit()
            read_cp_status = self.config_manager.read_cp_status()
            print(f"Read CP Status: {read_cp_status}")
            if read_cp_status:
                logging.info("DB Emitted write_cp_signal")
                self.write_cp_signal.emit(ranked_drivers, lap_times_dict)
        except Exception as e:
            print(f"DB Failed to Finalize race data to the database: {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            self.conn.close()  # Ensure the connection is closed
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("DB An error occurred")

    def calculate_score(self, participants, flags, driver_total_times):
            config = configparser.ConfigParser() # Load the score table from the config file
            config.read('config.ini')
            driver_flags = {}
            driver_laps_completed = {}
            driver_race_positions = {}
            # Retrieve flags and best lap times from the participants table for the current race
            for participant in participants:
                mName = participant['mName']
                flag = flags.get(mName)  # Flags column in the participants table
                if flag == 'DNF' and mName not in driver_total_times:
                    driver_total_times[mName] = 0  # Assign a total time of 0
                # Store the specific flag values
                if flag == 'Falsestart':
                    driver_flags[mName] = 'Falsestart'
                elif flag == 'DNF':
                    driver_flags[mName] = 'DNF'
                else:
                    driver_flags[mName] = 'No Flag'
                # Store the flag  for each driver
                driver_flags[mName] = flag if flag else "No Flag"
                driver_laps_completed[mName] =  participant['mLapsCompleted']
                driver_race_positions[mName] = participant['mRacePosition']   
            # Custom flag priority function
            def flag_priority(flag):
                if flag == 'No Flag' or flag is None:
                    return 0  # Highest priority
                elif flag == 'DNF':
                    return 1  # Medium priority
                elif flag == 'Falsestart':
                    return 2  # Lowest priority
                return 3  # Default (in case there's an unexpected flag)
            # Rank drivers based on custom flag priority and total race time
            ranked_drivers = sorted(
            driver_total_times.keys(),
            key=lambda x: (
                flag_priority(driver_flags.get(x, "No Flag")),
                -driver_laps_completed.get(x, 0) if driver_flags.get(x) == "DNF" else 0,
                driver_race_positions.get(x, float('inf')) if driver_flags.get(x) == "DNF" else 0,
                float('inf') if driver_flags.get(x) != "No Flag" else driver_total_times[x]
                    )
                )
            logging.info(f"Ranked drivers: {ranked_drivers}")
            return ranked_drivers

    def stop(self):
        self.running = False
        self.db_queue.put(('stop', None))
        if hasattr(self, 'session') and self.session:
            self.session.close()  # Safely close the session
        self.quit()  # Stop the event loop if it's running
        self.wait()  # Wait until the thread has fully exited        
        
class ControlPanel(QObject):
    def __init__(self, db_thread, config_manager):
        super().__init__()
        self.running = True
        self.config_manager= config_manager
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.file_path = self.config['config']['path_to_cp_scores'] + 'score.txt'
        self.best_lap_file_path =  self.config['config']['path_to_cp_scores'] + 'bestlap.txt'
        self.driver_file_path =  self.config['config']['path_to_cp_scores'] + 'drivers.txt'
        self.db_thread = db_thread
        
        #signalling
        self.db_thread.write_cp_signal.connect(self.process_signal) # Connect the signal to a slot that updates Session ID
        

    def process_signal(self, ranked_drivers, lap_times_dict):
        best_lap_time = float('inf') #find the best lap driver
        for driver, lap_times in lap_times_dict.items(): # Iterate over the dictionary to find the best lap time
            if lap_times:  # Ensure the driver has lap times
                min_lap_time = min(lap_times)  # Find the best lap time for this driver
                if min_lap_time < best_lap_time:  # Compare with the current best lap time
                    best_lap_time = min_lap_time
                    best_driver = driver
        driver_names = self.read_driver_names(self.driver_file_path)  # Read the driver names from the file
        driver_scores = self.map_scores_to_drivers(driver_names, ranked_drivers)  # Map scores to drivers
        self.write_race_results(driver_scores, self.file_path)  # Write the race results to the file
        self.write_best_lap_driver(best_driver, self.best_lap_file_path)  # Write the best lap driver to the file
        logging.info("Control Panel process signal completed")
        print("Control Panel process signal completed")
            
    def read_driver_names(self, file_path):
        with open(file_path, 'r') as f: # Read the driver names from the specified file
            line = f.readline().strip()
            driver_names = line.split(';')
            driver_names = [name.split(' (')[0] for name in driver_names]  # Remove any part after "("
            driver_names = [name.strip() for name in driver_names] # Remove any leading or trailing whitespace
        return driver_names

    def map_scores_to_drivers(self,driver_names, ranked_drivers):
        ranked_drivers = [name.split(' (')[0] for name in ranked_drivers] # Remove any part after "("
        ranked_drivers = [name.rstrip() for name in ranked_drivers] # Remove any leading or trailing whitespace
        driver_scores = {name: 0 for name in driver_names} # Map the race positions to the driver names
        for drivers in ranked_drivers:
            driver_name = drivers.split(',')[0]  
            if driver_name in driver_scores:
                driver_scores[driver_name] = ranked_drivers.index(drivers) + 1
        return driver_scores

    def write_race_results(self,driver_scores, file_path):
        line = ';'.join(str(driver_scores[name]) for name in driver_scores) + ';' # Write the race results to the specified file
        os.makedirs(os.path.dirname(file_path), exist_ok=True) # Ensure the directory exists
        with open(file_path, 'a') as f: # Append the results to the file
            f.write(line + '\n')
        print("Race results written to file.")
        logging.info("Race results written to file.")

    def write_best_lap_driver(self,best_driver, file_path):
        if best_driver: # Write the best lap driver to the specified file
            with open(file_path, 'a') as f:
                f.write(best_driver + '\n')

    def stop(self):
        self.running = False
        self.session.close()
        self.quit()
        self.wait()        
        
class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal()
    qualify_finished = pyqtSignal()
    flags_updated = pyqtSignal(dict)
    initialize = pyqtSignal()
    error_occurred = pyqtSignal(str)   # New signal for errors
    connection_restored = pyqtSignal()  # Signal to clear error message
    ip_address_updated = pyqtSignal(str) # Signal to update IP address
    race_message_updated = pyqtSignal(str) # Signal to update label text
    
    def __init__(self, race_monitor_app, tab_widget ,db_queue, config_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager= config_manager
        self.ip_address = self.config_manager.read_ip_address()   #threading.Thread.__init__(self)   
        self.race_monitor_app = race_monitor_app
        self.db_queue = db_queue
        self.tab_widget = tab_widget  # Store the reference to tab_widget
        #self.session = aiohttp.ClientSession() # Create a session object to reuse the connection to the API
        
         #variable initialization
        self.previous_game_state = None
        self.previous_race_state = None
        self.running = True
        self.first_time_run = True
        self.race_id = 0
        self.race_may_not_be_finished = False
        self.session_id = 0
        self.session = None
        self.pit_stops_dict = {}
        self.previous_ipaddress = None
        self.connecton_restored_message_shown = False
        
        #Signalling
        self.race_monitor_app.session_id_updated.connect(self.set_session_id) # Connect the signal to a slot that updates Session ID
        self.race_monitor_app.pit_stops_updated.connect(self.update_pit_stops) # Connect the signal to a slot that updates pit stops

    def run(self):
        # Start the asyncio event loop in this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_main_loop())  # Run your async method
        loop.close()
        
    async def run_main_loop(self):
        race_not_finished_message_shown = False
        index = 0
        while self.running:
            try:
                if self.first_time_run and not self.race_may_not_be_finished: self.initialize.emit() #Load selected race after start.
                if not self.running: break
                if self.session is None: self.session = aiohttp.ClientSession()
                data = await self.get_api_data()
                await asyncio.sleep(5)
                if not self.running: break
                if self.session is not None: await self.session.close()
                self.session = None
                print(F"Waiting... Loop number {index}")
                # logging.info(f"Waiting... Loop number {index}")
                index += 1
                if data is None:
                    self.first_time_run = False
                    continue
                participants = data.get('participants', {}).get('mParticipantInfo', []) # Fetch participants data
                if not participants and self.first_time_run and not self.race_may_not_be_finished:
                    self.first_time_run = False
                    race_not_finished_message_shown = False
                    logging.info(f"MT No participants found, Still waiting for race start.")
                    print(f"MT Waiting for race start.....")
                    index = 0
                    continue  # Restart loop if participants list is empty
                else:
                    if self.race_may_not_be_finished and participants:
                        if not race_not_finished_message_shown:
                            print("Race not finished yet....")
                            race_not_finished_message_shown = True
                        continue
                    if self.race_may_not_be_finished:
                        print("Race Finished!")
                        self.race_may_not_be_finished = False
                        continue

                if participants:
                    self.race_loop_first_time = True
                    self.first_time_run = False
                    # check if it is qualify or race
                    if data['gameStates']['mSessionState'] == 3:
                        print("Qualifying Starting")
                        logging.info("Qualifying")
                        await self.qualify_running(data) # Start the qualifying running loop
                        #self.race_message_updated.emit("Qualifying Finished...")
                        self.qualify_finished.emit()
                        Qualifying_finished = True
                        print("Qualifying Finished")
                    else:
                        print("Starting Race Loop")
                        await self.race_running(data) # Start the race running loop
                        print("Race Loop Finished")
                        self.first_time_run = True
                        self.race_not_finished_message_shown = False
                
            except Exception as e:
                logging.error(f"An error occurred while monitoring race state: {e}")
                print(f"MT An error occurred while monitoring race state: {e}")
                await asyncio.sleep(5)   
                
    def set_race_id(self, latest_race_id):
        logging.info(f"MT Def set_race_id entered")
        global app
        print(f"MT Fetch race ID after write Race. Race_id: {latest_race_id}")
        if latest_race_id is None:
            print(f"MT Race_id is None, program crash!")
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")
        else:
            self.race_id = latest_race_id
            print(f"MT Monitorthread Race ID received from DB Race id: {self.race_id}")
            logging.info(f"MT Race ID received from DB Race id: {self.race_id}")

    def update_pit_stops(self, pit_stops_dict):
        self.pit_stops_dict = pit_stops_dict
        print(f"MT Pit stops updated: {self.pit_stops_dict}")
        logging.info(f"MT Pit stops updated: {self.pit_stops_dict}")

    def set_session_id(self, new_session_id):
        logging.info(f"MT Def set_session_id entered")
        if new_session_id is None:
            print(f"Should never happen: MT Session ID is None, setting to 1")
            logging.info(f"Should never happen: MT Session ID is None, setting to 1")
            self.session_id = 1
        else:            
            self.session_id = new_session_id
            print(f"MT Monitorapp Session ID updated to {self.session_id}") 
            logging.info(f"MT Monitorapp Session ID updated to {self.session_id}")
    
    async def get_api_data(self):
        if not self.running: return
        if self.session is None: self.session = aiohttp.ClientSession()
        error_message_shown = False
        
        self.no_server_connection = True
        while self.no_server_connection:
            self.ip_address = self.config_manager.read_ip_address()  # Read IP address before each API call
            if self.previous_ipaddress != self.ip_address:
                self.previous_ipaddress = self.ip_address
                self.ip_address_updated.emit(self.ip_address)
                print(f"MT Ipadress changed, new ipadress {self.ip_address}")
                logging.info(f"MT Ipadress changed, new ipadress {self.ip_address}")
            try:
                if not self.running or self.session is None: return
                async with self.session.get(f'http://{self.ip_address}:8180/crest2/v1/api', timeout=3) as response:
                    if not self.running or self.session is None: return
                    data = await response.json()
                    if response.status == 200: #Ensure the response content is valid JSON
                        try:
                            if data is None:
                                raise ValueError("MT Received None as data. Possible issue with API response.")
                            else:
                                self.no_server_connection = False
                                if not self.connecton_restored_message_shown:
                                    print("Connection Restored")
                                    logging.info("Connection Restored")
                                    self.connection_restored.emit() # Emit signal for successful connection restoration to clear the error message
                                    self.connecton_restored_message_shown = True
                                current_game_state = data['gameStates']['mGameState']
                                current_race_state = data['gameStates']['mRaceState']
                                if current_race_state != self.previous_race_state:
                                    print(f"MT Race state changed to {current_game_state}")  # Ensure console output remains
                                    logging.info(f"MT RMA Race state changed to {current_race_state}")
                                    self.previous_race_state = current_race_state
                                if current_game_state != self.previous_game_state:
                                    print(f"MT Game state changed to {current_game_state}")  # Ensure console output remains
                                    logging.info(f"MT RMA Game state changed to {current_game_state}")
                                    self.previous_game_state = current_game_state
                                if not self.running or self.session is None: return
                                return data # return if the response is valid
                        except ValueError as ve:
                            if not error_message_shown:
                                logging.error(f"MT Error parsing JSON response: {ve}")
                                print(f"MT Error parsing JSON response: {ve}")
                                error_message_shown = True
                                self.connecton_restored_message_shown = False
                            await asyncio.sleep(2)  # Wait for 5 seconds before fetching the next data
                    else:
                        if not error_message_shown:
                            logging.error(f"Unexpected status code {response.status} received from the API.")
                            print(f"MT Unexpected status code {response.status} received from the API.")
                            self.error_occurred.emit(f'Game Not Started: Unexpected status code {response.status}')
                            error_message_shown = True
                            self.connecton_restored_message_shown = False
                        await asyncio.sleep(5)  # Wait for 5 seconds before fetching the next data
            except asyncio.CancelledError:
                logging.info("Operation cancelled due to application shutdown.")
                return None
            except Exception as e:
                self.error_occurred.emit(f'Connection Error: Check IP Address in Config.ini:')
                if not error_message_shown:
                    logging.error(f"An error occurred while fetching API Data {e}")
                    print(f"MT An error occurred while fetcing API Data: {e}")
                    error_message_shown = True
                    self.connecton_restored_message_shown = False
                await asyncio.sleep(5)
            finally: self.no_server_connection = True
                
    async def qualify_running(self, data):
        print("Qualify Running!")
        logging.info("Qualify Running!")
        while data['gameStates']['mSessionState'] == 3:
            #self.race_message_updated.emit("Qualifying Running...")
            if not self.running: break
            data = await self.get_api_data()
            if data is not None: self.data_updated.emit(data)

    async def race_running(self, data):
        if not self.running: return
        race_in_session = True
        if data is not None: self.data_updated.emit(data)
        lap_times_dict = {} # Clear the lap times dictionary ready for next race.
        last_lap_counts = {} # Clear the last lap counts dictionary
        driver_total_times = {} # Clear the driver total times dictionary
        driver_flags ={} # Clear the driver flags dictionary
        QMetaObject.invokeMethod(self.tab_widget, "setCurrentIndex", Qt.QueuedConnection, Q_ARG(int, 0)) #Switch to Score View tab
        print(f"MT Race is STARTING!!!!!!.")
        logging.info(f"MT Race is STARTING!!!!!!.")
        #print(f"MT Data to be written to database: race index: {race_index} Sesson id: {self.session_id}")
        logging.info(f"MT Data to be written to database: race index: {self.race_id} Sesson id: {self.session_id}")
        self.track_location = data['eventInformation']['mTranslatedTrackVariation']+ ' - ' + data['eventInformation']['mTranslatedTrackLocation']
        while self.session_id == 0:
            await asyncio.sleep(0.5)
            print(f"MT Waiting for session ID to be updated. Current session ID: {self.session_id}")
            logging.info(f"MT Waiting for session ID to be updated. Current session ID: {self.session_id}")
        self.db_queue.put(('write_race', (data, self.session_id)))
        print(f"MT Session ID received: {self.session_id} Race written to database.")
        self.db_queue.put(('get_latest_race_id', (self.set_race_id,)))  # Only pass the necessary data, not the function
        while self.race_id == 0:
            await asyncio.sleep(0.5)
            print(f"MT Waiting for race ID to be updated. Current Race ID: {self.race_id}")
        print(f"MT Race ID received: {self.race_id}, entering live view loop.")
        logging.info(f"MT Race written to database., asked for race ID: {self.race_id}, entering live view loop.")
        elapsed_time = []
        round_counter = 0        
        while race_in_session:
            if not self.running: break
            start_time = time.time()     #loop while race is running
            try:
                if self.race_loop_first_time: logging.info(f"MT RaceID is: {self.race_id}.")
                previous_data = data # Store the previous data
                data = await self.get_api_data()
                if data == None:
                    print(f"MT Data is None, skipping")
                    logging.info(f"MT Data is None, skipping")
                    continue
                participants = data.get('participants', {}).get('mParticipantInfo', [])  # Proceed with processing the valid data 
                if not participants or all(participant.get('mCurrentLap', 0) > data['eventInformation']['mLapsInEvent'] for participant in participants):  # Check if all participants have completed every lap or if there is data.
                    if not participants:                                                       
                        data = previous_data # Revert to the previous data if no participants are found
                        logging.info(f"MT No participants found , Race is over. Break loop")
                        print(f"MT No participants found, Race is over.")
                        race_in_session = False
                    else:                              
                        logging.info(f"MT All participants finished, Race is over,Sending Data one last time, breaking the loop")
                        print(f"MT All participants finished race, Race is over. Sending Data one last time.")
                        self.race_may_not_be_finished = True
                        race_in_session = False
                if not self.running: break
                if data is not None: self.data_updated.emit(data) #Send the data to Live view
                for participant in participants:
                    if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                    if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0   
                    if (participant.get('mCurrentLap', 0) > last_lap_counts.get(participant['mName'], 1)) and (participant.get('mLastLapTimes') != -123):
                        if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                        if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0                                    
                        driver_total_times[participant['mName']] += participant.get('mLastLapTimes', 0)
                        self.db_queue.put(('insert_lap_data', (self.race_id, participant['mName'], participant.get('mCurrentLap', 0) - 1,participant.get('mLastLapTimes'), self.track_location, participant['mCarNames']))) #insert lap into Table
                        lap_times_dict[participant['mName']].append(participant.get('mLastLapTimes', None))
                        logging.info(f"MT Storing lap time for {participant['mName']}: Lap {participant.get('mCurrentLap', 0)}, Time {participant.get('mLastLapTimes', 0)},Last Lap:{participant.get('mLastLapTimes', None)} Driver Total Time: {driver_total_times[participant['mName']]} ")
                    else:
                        if (participant.get('mSpeeds',0) >10) and (data['gameStates']['mRaceState'] == 1) and (driver_flags.get(participant['mName'],None) != 'Falsestart'):
                            print(f"MT Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            logging.info(f"MT Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            driver_flags[participant['mName']] = 'Falsestart'
                            if driver_flags is not None: self.flags_updated.emit(driver_flags)
                    last_lap_counts[participant['mName']] = participant.get('mCurrentLap', 0)
                self.race_loop_first_time = False
            except Exception as e:
                logging.error(f"An error occurred while processing participant data: {e}")
                print(f"MT An error occurred while processing participant data: {e}")
                raise
            end_time = time.time()
            elapsed_time.append(end_time - start_time)
            round_counter += 1
        # Race loop has ended    
        average_time = sum(elapsed_time) / len(elapsed_time)
        max_time = max(elapsed_time)
        min_time = min(elapsed_time)
        print(f"MT Api Fetch time, average execution time: {average_time:.6f} seconds, maximum execution time: {max_time:.6f} seconds, minimum execution time: {min_time:.6f} seconds")
        if self.session is not None: await self.session.close()
        self.session = None
        print(f"MT Race Ended Finalizing Race for: Race_{self.race_id} with Driver Total times: {driver_total_times}")
        logging.info(f"MT Race Ended Finalizing Race for: Race_{self.race_id} with Driver Total times: {driver_total_times}")
        if data is not None: participants = data.get('participants', {}).get('mParticipantInfo', [])
        if not driver_total_times:
            print(f"MT No reason to write race, no one finished, no driver_total_times.")
            logging.info(f"MT No reason to write race, no one finished, no driver_total_times.")
            self.race_may_not_be_finished = True
            self.race_finished.emit() # no reason to write the race, no one finished
        else:
            try:                
                for participant in participants:
                    participant_name = participant['mName']
                    logging.info(f"MT Participant: {participant['mName']}, Race Position: {participant.get('mRacePosition', 0)}")
                    participant_name = participant['mName']
                    if data is None or not self.running: return
                    if participant['mCurrentLap'] <= data['eventInformation']['mLapsInEvent']: # Driver has fewer laps less than he should, either False start Or DNF
                        if driver_flags is not None:
                            logging.info(f"MT Participant: {participant_name}, Flags: {driver_flags}")
                            if driver_flags.get(participant_name) != 'Falsestart': # Check if the participant has a 'Falsestart' flag
                                print(f"MT Adding DNF to Flags for {participant_name}")
                                logging.info(f"MT Adding DNF to Flags for {participant_name}")
                                driver_flags[participant_name] = 'DNF'
                                if driver_flags is not None: self.flags_updated.emit(driver_flags) 
                                await asyncio.sleep(0.5)
                self.db_queue.put(('finalize_race', (data, lap_times_dict,driver_flags, self.pit_stops_dict))) # Write final data to DB
                if data is not None: self.data_updated.emit(data) #Send the data to Live view to update the flags
                self.race_finished.emit()
                print("MT Race finished emitted")
            except Exception as e:
                logging.error(f"MT An error occurred while finalizing race: {e}")
                print(f"MT An error occurred while finalizing race: {e}")
                await asyncio.sleep(5)
                
    async def stop(self):
        if self.session:
            await self.session.close()  # Close the session when stopping
            self.session = None
        self.running = False
        print("Starting pending all tasks")
        pending = asyncio.all_tasks(loop=asyncio.get_event_loop())
        for task in pending: task.cancel()
        print("all tasks cancelled")
        self.quit()
        self.wait()

class RaceMonitorApp(QMainWindow):
    session_id_updated = pyqtSignal(int)  # Signal to update the SessionID
    pit_stops_updated = pyqtSignal(dict)  # Signal to update the pit stops
    #delete_db = pyqtSignal()  # Signal to delete the database
    def __init__(self):
        super().__init__()
        self.db_queue = queue.Queue()
        self.config_manager = ConfigManager(self.db_queue)
        self.update_config_file = self.config_manager.update_config_file(self)
        self.db_thread = DatabaseThread(self.db_queue, self.config_manager)
        self.temp_dir = tempfile.gettempdir()
        self.font_filename = os.path.join(self.temp_dir, "temp_font.ttf")
        print(f"Font file will be written to: {self.font_filename}")
        self.initUI() # Initialize the GUI
        self.monitor_thread = MonitorThread(self, self.tab_widget, self.db_queue, self.config_manager)
        self.control_panel = ControlPanel(self.db_thread, self.config_manager)
        self.monitor_thread.start()
        self.db_thread.start()
 
        #Variable initialization
        self.live_first_time_run =True
        self.session_id_dropdown = None
        self.racestarted = False
        self.all_driver_dropdown_items = []
        
        # Signal connections
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.flags_updated.connect(self.update_flags)
        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.qualify_finished.connect(self.qualify_finished)
        self.monitor_thread.initialize.connect(self.initialize_dropdown)
        self.monitor_thread.error_occurred.connect(self.show_error_message)  # Connect the error signal
        self.monitor_thread.connection_restored.connect(self.handle_connection_restored)  # Connection restored
        self.db_thread.load_race_on_start_signal.connect(self.handle_race_data_on_start) # Get data to populate select races dropdown
        self.db_thread.load_sessionid_on_start_signal.connect(self.handle_sessionid_data) # Get data to populate session ID dropdown
        self.db_thread.load_highscores_on_start_signal.connect(self.handle_high_scores_data_on_start) # Get data to populate high scores table
        self.db_thread.race_data_loaded_signal.connect(self.on_race_loaded)  # queue.put already directs this to the correct function
        self.db_thread.highscore_data_loaded_signal.connect(self.on_highscore_loaded)  # queue.put already directs this to the correct function
        self.db_thread.drivers_signal.connect(self.handle_driver_statistics_on_start)  # Connect the signal to the slot that updates the driver statistics
        self.db_thread.score_data_signal.connect(self.calculate_score) # Connect the signal to the slot that sends score data
        self.monitor_thread.ip_address_updated.connect(self.update_ip_address)  # Connect the signal to the slot that updates the IP address
        self.monitor_thread.race_message_updated.connect(self.update_race_message)  # Connect the signal to the slot that updates the race message
        
        #Set the Status view as the default tab
        self.tab_widget.setCurrentIndex(2)
        self.tab_widget.setCurrentIndex(1)
        # Call the function to load race data 
        self.db_queue.put(('get_latest_session_id', (self.set_session_id,)))

    def base64_to_qicon(self, base64_str):
        """Convert a base64 string to a QIcon object."""
        image_data = base64.b64decode(base64_str)
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        return QIcon(pixmap)

    def base64_to_pixmap(self, base64_str):
        """Convert a base64 string to a QPixmap object."""
        image_data = base64.b64decode(base64_str)
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        return pixmap

    def base64_to_font(self, base64_str):
        """Convert a base64 string to a QFont object."""
        font_data = base64.b64decode(base64_str)
        
        # Write the decoded font data to the system's temp file
        with open(self.font_filename, "wb") as font_file:
            font_file.write(font_data)
        
        # Load the font into QFontDatabase
        font_id = QFontDatabase.addApplicationFont(self.font_filename)
        
        if font_id == -1:
            print("Failed to load font!")
        else:
            print(f"Font loaded successfully with ID: {font_id}")
        
        # Return the font family name
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        return font_family

    def show_version_update_message(self, existing_version, new_version):
            # Create the message box
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("Version Update")
            msg_box.setText(f"Version {new_version} will delete existing Race Data! \n Do you want to Delete?")
            msg_box.setInformativeText(f"Your current version: {existing_version}")
            msg_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            msg_box.setDefaultButton(QMessageBox.Ok)

            # Show the message box and get the response
            response = msg_box.exec_()

            if response == QMessageBox.Ok:
                return True  # OK was clicked
            else:
                return False  # Cancel was clicked 

    def initUI(self):
        self.labels = {}
        self.session_id = None
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        # Convert images to base64 strings once during initialization
        self.window_icon = QIcon(self.base64_to_qicon(icon_base64))
        self.live_background_image = self.base64_to_pixmap(liverace_liveview_img_base64)  # Background for Live view
        self.result_background_image = self.base64_to_pixmap(Race_results_Background_img_base64)  # Background for Results view
        self.final_background_image = self.base64_to_pixmap(Race_scores_Background_img_base64)  # Background for Final view
        self.live_status_image = self.base64_to_pixmap(liverace_status_img_base64)
        self.highscore_background_image = self.base64_to_pixmap(High_scores_Background_img_base64)
        self.driver_statistics_background_image = self.base64_to_pixmap(Driver_Statistics_Background_img_base64) 
        self.window_icon = self.base64_to_qicon(icon_base64)
        self.setWindowIcon(self.window_icon)
        self.font_family = self.base64_to_font(sui_generis_rg_font_base64)

        #Colors
        self.color_values = '#FFD700'
        self.color_labels = '#FFFFFF'
        self.color_dnf = '#00FF00'
        self.color_falsestart = '#FF0000'
        self.color_pitstop = '#0000ff'
        self.color_gold = '#e9c20c'
        self.color_silver = '#C0C0C0'
        self.color_bronze = '#CD7F32'
        self.color_scores = '#000000'
        self.color_lastpos = '#00FF00'   

        # GUI Initialization
        if not self.config.get('config', 'titlebar', fallback='False').strip().lower() == 'true':
            self.setWindowFlags(Qt.FramelessWindowHint)  # Remove the window frame
        self.setWindowTitle("Live Race Data")
        self.setGeometry(100, 100, int(self.config['config']['width']), int(self.config['config']['height']))
        self.setFixedSize(int(self.config['config']['width']), int(self.config['config']['height'])) # Set fixed size to prevent autoresizing
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Fully transparent
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
        background-position: center;
        background-repeat: no-repeat;
        """)

        self.tab_widget = QTabWidget(self.central_widget)

        # Apply the translucent style to the tab buttons.
        '''
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                background: transparent;  /* Transparent background for the pane */
                border: 0px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 50);  /* Slightly translucent tabs */
                color: black;
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 100);  /* Less translucent when selected */
            }
         """)
        '''
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.addWidget(self.tab_widget)

        # Apply the translucent style to the tab panes.
        #'''
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { 
                background: rgba(0, 0, 0, 0);  /* Makes the pane itself fully transparent */
                border: 0px;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 100);  /* Light translucent background for tabs */
                color: black;  /* Text color */
                padding: 5px;
            }
            QTabBar::tab:selected {
                background: rgba(255, 255, 255, 150);  /* Slightly less transparent when selected */
            }
        """)
        # '''

        # Create widgets for each tab
        self.live_view_widget = QWidget()
        self.results_view_widget = QWidget()
        self.final_view_widget = QWidget()
        self.highscore_view_widget = QWidget()
        self.driver_statistics_widget = QWidget()
        # Set up layouts for each tab
        self.live_view_layout = QVBoxLayout(self.live_view_widget)
        self.results_view_layout = QVBoxLayout(self.results_view_widget)
        self.final_view_layout = QVBoxLayout(self.final_view_widget)
        self.highscore_view_layout = QVBoxLayout(self.highscore_view_widget)
        self.driver_statistics_layout = QVBoxLayout(self.driver_statistics_widget)
        #self.live_view_layout.setAlignment(Qt.AlignTop)
        #self.live_view_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Add live view and results view to the tab widget and give the tabs a name
        self.tab_widget.addTab(self.live_view_widget, "Live Race Data")
        self.tab_widget.addTab(self.results_view_widget, "Previous Races")
        self.tab_widget.addTab(self.final_view_widget, "Accumulated Score")
        self.tab_widget.addTab(self.highscore_view_widget, "High Scores")
        self.tab_widget.addTab(self.driver_statistics_widget, "Driver Statistics")

        # Add your existing widgets and layout configurations to the appropriate tab layouts
        self.setup_live_view() # Initialize the live view
        self.setup_final_view() # Initialize the final view
        self.setup_result_view() # Initialize the result view
        self.setup_highscore_view() # Initialize the highscore view
        self.setup_driver_statistics_view() # Initialize the driver statistics view
        self.tab_widget.setCurrentIndex(1) #Set the Status view as the default tab

        # Connect tab change to background update
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Create a QLabel to display the background image
        self.background_label = QLabel(self.central_widget)
        self.background_label.setPixmap(self.live_status_image)
        self.background_label.setGeometry(0, 0, int(self.config['config']['width']), int(self.config['config']['height']))
        #self.result_background_label.setGeometry(0,0,int(self.width()), int(self.height()))
        self.background_label.setScaledContents(True)  # Adjusts the image size to the window
        self.background_label.lower()  # Ensure the background stays behind other widgets
        self.layout.setAlignment(Qt.AlignTop)

        # Add Dropdown for selecting Track
        self.track_dropdown = QComboBox(self)
        self.labels['track_dropdown'] = self.track_dropdown
        self.track_dropdown.setStyleSheet("""
             font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)
        self.track_dropdown.setFixedSize(600, 30)
        self.track_dropdown.currentIndexChanged.connect(self.update_dropdowns)
        self.layout.addWidget(self.track_dropdown, alignment=Qt.AlignTop)

        # Add Dropdown for selecting Car
        self.car_dropdown = QComboBox(self)
        self.labels['car_dropdown'] = self.car_dropdown
        self.car_dropdown.setStyleSheet("""
             font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)
        self.car_dropdown.setFixedSize(600, 30)
        #self.car_dropdown.currentIndexChanged.connect(self.update_dropdowns)
        self.layout.addWidget(self.car_dropdown, alignment=Qt.AlignTop)
        
        # Add Dropdown for selecting Drivers
        self.driver_dropdown = QComboBox(self)
        self.labels['driver_dropdown'] = self.driver_dropdown
        self.driver_dropdown.setEditable(True)
        #self.driver_dropdown.lineEdit().installEventFilter(self)  # Install event filter
        line_edit = self.driver_dropdown.lineEdit()
        line_edit.textEdited.connect(self.filter_dropdown)
        line_edit.installEventFilter(self)
        line_edit.setFocusPolicy(Qt.StrongFocus)
        self.driver_dropdown.setFocusPolicy(Qt.StrongFocus) # Ensure the dropdown can receive focus
        self.driver_dropdown.setStyleSheet("""
             font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)
        self.driver_dropdown.setFixedSize(600, 30)
        #self.driver_dropdown.currentIndexChanged.connect(self.load_selected_driver)
        self.driver_dropdown.activated.connect(self.load_selected_driver)
        self.layout.addWidget(self.driver_dropdown, alignment=Qt.AlignTop)

        #Add Dropdown for selecting previous races
        self.dropdown = QComboBox(self)
        self.labels['dropdown'] = self.dropdown
        self.dropdown.setStyleSheet("""
            font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)        
        self.dropdown.setFixedSize(600, 30)
        #self.dropdown.currentIndexChanged.connect(self.load_selected_race)
        self.dropdown.activated.connect(self.load_selected_race)
        self.layout.addWidget(self.dropdown, alignment=Qt.AlignTop)

        #Add Dropdown for selecting Sessions
        self.dropdown_sessionid = QComboBox(self)
        # Add button for Writing all scores
        self.write_score_button = QPushButton("Write All Scores for this session", self)
        self.write_score_button.setStyleSheet("""
            QPushButton {                                      
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            }                                  
            QPushButton:hover {
            background-color: #b33b3b;  /* Slightly lighter shade for hover state */
            }
            QPushButton:focus {
            outline: none;
            border: 2px solid #ff0000;  /* Red border to indicate focus */
            }
            QPushButton:pressed {
            background-color: #801919;  /* Darker shade for pressed state */
            border: 2px solid #5d1a1a;  /* Darker border for pressed state */
            }
        """)
        self.labels['write_score_button'] = self.write_score_button
        self.write_score_button.clicked.connect(self.write_all_scores)
        self.layout.addWidget(self.write_score_button, alignment=Qt.AlignTop)
        self.labels['dropdown_sessionid'] = self.dropdown_sessionid
        self.dropdown_sessionid.setStyleSheet("""
            font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)        
        self.dropdown_sessionid.setFixedSize(400, 30)
        #self.dropdown_sessionid.currentIndexChanged.connect(self.display_score)
        self.dropdown_sessionid.activated.connect(self.display_score)
        self.layout.addWidget(self.dropdown_sessionid, alignment=Qt.AlignTop) 

        # Add button for loading high scores
        self.load_high_scores_button = QPushButton("Load High Scores", self)
        self.labels['load_high_scores_button'] = self.load_high_scores_button
        self.load_high_scores_button.setStyleSheet("""
            QPushButton {                                      
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            }                                  
            QPushButton:hover {
            background-color: #b33b3b;  /* Slightly lighter shade for hover state */
            }
            QPushButton:focus {
            outline: none;
            border: 2px solid #ff0000;  /* Red border to indicate focus */
            }
            QPushButton:pressed {
            background-color: #801919;  /* Darker shade for pressed state */
            border: 2px solid #5d1a1a;  /* Darker border for pressed state */
            }
        """) 
        self.load_high_scores_button.setFixedSize(150, 30)
        self.load_high_scores_button.clicked.connect(self.load_selected_highscore)
        self.layout.addWidget(self.load_high_scores_button, alignment=Qt.AlignTop)

        # Add button for deleting driver
        self.delete_driver_button = QPushButton("Delete Driver", self)
        self.labels['delete_driver_button'] = self.delete_driver_button
        self.delete_driver_button.setStyleSheet("""
             QPushButton {                                      
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            }                                  
            QPushButton:hover {
            background-color: #b33b3b;  /* Slightly lighter shade for hover state */
            }
            QPushButton:focus {
            outline: none;
            border: 2px solid #ff0000;  /* Red border to indicate focus */
            }
            QPushButton:pressed {
            background-color: #801919;  /* Darker shade for pressed state */
            border: 2px solid #5d1a1a;  /* Darker border for pressed state */
            }
        """)
        self.delete_driver_button.setFixedSize(150, 30)
        self.delete_driver_button.clicked.connect(self.delete_selected_driver)
        self.layout.addWidget(self.delete_driver_button, alignment=Qt.AlignTop)
        
        # Add the Delete button
        self.delete_button = QPushButton("Delete Selected Race", self)
        self.labels['delete_button'] = self.delete_button
        self.delete_button.setStyleSheet("""
            QPushButton {                                      
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            }                                  
            QPushButton:hover {
            background-color: #b33b3b;  /* Slightly lighter shade for hover state */
            }
            QPushButton:focus {
            outline: none;
            border: 2px solid #ff0000;  /* Red border to indicate focus */
            }
            QPushButton:pressed {
            background-color: #801919;  /* Darker shade for pressed state */
            border: 2px solid #5d1a1a;  /* Darker border for pressed state */
            }
        """)        
        self.delete_button.setFixedSize(150, 30)
        self.delete_button.clicked.connect(self.delete_selected_race)
        self.layout.addWidget(self.delete_button) 

        # Add the Delete all races button
        self.delete_all_races_button = QPushButton("Delete All Races", self)
        self.labels['delete_all_races_button'] = self.delete_all_races_button
        self.delete_all_races_button.setStyleSheet("""
            QPushButton {                                      
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            }                                  
            QPushButton:hover {
            background-color: #b33b3b;  /* Slightly lighter shade for hover state */
            }
            QPushButton:focus {
            outline: none;
            border: 2px solid #ff0000;  /* Red border to indicate focus */
            }
            QPushButton:pressed {
            background-color: #801919;  /* Darker shade for pressed state */
            border: 2px solid #5d1a1a;  /* Darker border for pressed state */
            }
        """)        
        self.delete_all_races_button.setFixedSize(150, 30)
        self.delete_all_races_button.clicked.connect(self.delete_all_races)
        self.layout.addWidget(self.delete_all_races_button)

        # Add the New Session button
        self.new_session_button = QPushButton("Start New Session", self)
        self.labels['new_session_button'] = self.new_session_button
        self.new_session_button.setStyleSheet("""
            QPushButton {                                      
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            }                                  
            QPushButton:hover {
            background-color: #b33b3b;  /* Slightly lighter shade for hover state */
            }
            QPushButton:focus {
            outline: none;
            border: 2px solid #ff0000;  /* Red border to indicate focus */
            }
            QPushButton:pressed {
            background-color: #801919;  /* Darker shade for pressed state */
            border: 2px solid #5d1a1a;  /* Darker border for pressed state */
            }
        """)
        self.new_session_button.setFixedSize(150, 30)
        self.new_session_button.clicked.connect(self.start_new_session)
        self.layout.addWidget(self.new_session_button) 

        # Add the previous Session button
        self.previous_session_button = QPushButton("Previous Session", self)
        self.labels['previous_session_button'] = self.previous_session_button
        self.previous_session_button.setStyleSheet("""
            QPushButton {                                      
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            }                                  
            QPushButton:hover {
            background-color: #b33b3b;  /* Slightly lighter shade for hover state */
            }
            QPushButton:focus {
            outline: none;
            border: 2px solid #ff0000;  /* Red border to indicate focus */
            }
            QPushButton:pressed {
            background-color: #801919;  /* Darker shade for pressed state */
            border: 2px solid #5d1a1a;  /* Darker border for pressed state */
            }
        """)
        self.previous_session_button.setFixedSize(150, 30)
        self.previous_session_button.clicked.connect(self.previous_session)
        self.layout.addWidget(self.previous_session_button) 

        # Status label for connection issues
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
        self.layout.addWidget(self.status_label)  # Add the status label below the delete button
        
        self.tab_widget_mapping = {  # Widget visibility mapping for each tab
            0: [],  # Widgets for Live View
            1: ['dropdown', 'delete_button', 'delete_all_races_button',  ],  # Widgets for Results View
            2: ['new_session_button', 'dropdown_sessionid', 'previous_session_button', 'write_score_button' ],  # Widgets for Score View
            3: ['car_dropdown', 'track_dropdown', 'load_high_scores_button'],  # Widgets for High Scores
            4: ['driver_dropdown', 'delete_driver_button']  # Widgets for Driver Statistics
        }        

    def filter_dropdown(self, text):
        
        while self.driver_dropdown.count() > 1: # Clear the current dropdown items
            self.driver_dropdown.removeItem(1)

        # Add items back that match the typed text
        for item in self.all_driver_dropdown_items:
            if text.lower() in item.lower():  # Case-insensitive search
                self.driver_dropdown.addItem(item)

        # Set the current text in the line edit widget
        self.driver_dropdown.lineEdit().setText(text)
        # Keep the cursor at the end of the text
        self.driver_dropdown.lineEdit().setCursorPosition(len(text))

    def eventFilter(self, obj, event):
        # Check if the event is a focus in event on the edit line
        if obj == self.driver_dropdown.lineEdit() and event.type() == QEvent.MouseButtonPress:
            print("Edit line focused, calling clear_driver_dropdown...")
            self.clear_driver_dropdown()  # Call your method
            return True  # Indicate that the event was handled
        # Pass other events to the default handler
        return super().eventFilter(obj, event)

    def delete_db(self):
        logging.info("RMA Delete DB def entered")
        #print("RMA Delete DB def entered
        self.db_queue.put(('delete_db', ()))
        self.set_delete_db_mode(True)
        QTimer.singleShot(5000, lambda: self.set_delete_db_mode(False))

    def delete_all_races(self):
        logging.info("RMA Delete all reaces def entered")
        #print("RMA Delete DB def entered
        self.db_queue.put(('delete_all_races', ()))
        self.set_delete_all_races_mode(True)
        QTimer.singleShot(1000, self.after_timer_race_deleted)
        QTimer.singleShot(5000, lambda: self.set_delete_all_races_mode(False))

    def set_delete_all_races_mode(self, is_active):
        logging.info("RMA Def set_delete_db_mode entered")
        if is_active:
            self.delete_all_races_button.setText("Deleting all races...")
            print ("Deleting all Races...")
            '''
            self.delete_all_races_button.setStyleSheet("""
                font-size: 14px;
                background-color: #d9534f;  # Bootstrap's danger color
                color: white;
                margin-bottom: 5px;                             
                border: 2px solid darkred;
                border-radius: 5px;
            """)
            '''
            self.delete_all_races_button.setEnabled(False)
        else:
            self.initialize_dropdown()
            self.delete_all_races_button.setText("Delete All Races")
            print ("Deleting all Races Completed...")
            self.delete_all_races_button.setStyleSheet("""
                 font-size: 14px;
                 background-color: #a32d2d;
                 color: white;
                 margin-bottom: 5px;                             
                 border: 2px solid black;  /* Change the border color */
                 border-radius: 5px;  /* Optional: rounded corners */
            """) 
            
            self.delete_all_races_button.setEnabled(True)          
        
    def set_delete_db_mode(self, is_active):
        logging.info("RMA Def set_delete_db_mode entered")
        if is_active:
            self.delete_all_button.setText("Deleting DB...")
            print ("Deleting DB...")
            '''
            self.delete_all_button.setStyleSheet("""
                font-size: 14px;
                background-color: #d9534f;  # Bootstrap's danger color
                color: white;
                margin-bottom: 5px;                             
                border: 2px solid darkred;
                border-radius: 5px;
            """)
            '''
            self.delete_all_button.setEnabled(False)
        else:
            self.initialize_dropdown()
            self.delete_all_button.setText("Delete All Data")
            print ("Deleting DB Completed...")
            self.delete_all_button.setStyleSheet("""
                 font-size: 14px;
                 background-color: #a32d2d;
                 color: white;
                 margin-bottom: 5px;                             
                 border: 2px solid black;  /* Change the border color */
                 border-radius: 5px;  /* Optional: rounded corners */
            """) 
            
            self.delete_all_button.setEnabled(True)  
            
    def update_flags(self, flags):
        logging.info("RMA Flags updated def entered")
        #print("RMA Flags updated def entered")
        self.driver_flags=flags # Update the flags label with the message
        
    def initialize_dropdown(self):
        logging.info("RMA Initialize Dropdown def entered")
        #print("RMA Initialize Dropdown def entered")
        self.db_queue.put(('load_race_data_on_start',())) #Send the request to the DatabaseThread to load race data on start
        self.db_queue.put(('load_sessionid_on_start',())) #Send the request to the DatabaseThread to load session ID on start
        self.db_queue.put(('load_highscores_on_start',())) #Send the request to the DatabaseThread to load highscore data on start
        self.db_queue.put(('load_driver_statistics_on_start',())) #Send the request to the DatabaseThread to load score data on start
    
    def update_ip_address(self, ip_address):
        logging.info("RMA Update IP Address def entered")
        #print("RMA Update IP Address def entered")
        #self.ip_address = ip_address
        ip_last_segment = ip_address.split('.')[-1]
        if len(ip_last_segment) > 1:
            if int(ip_last_segment[-2:]) < 10 :
                self.tab_widget.setTabText(0, f"Live Race Data: Sim-{ip_last_segment[-1]}")
            else:
                self.tab_widget.setTabText(0, f"Live Race Data: Sim-{ip_last_segment[-2:]}")
        else:
            self.tab_widget.setTabText(0, f"Live Race Data: Sim-{ip_last_segment}")
        # QTimer.singleShot(5000, lambda: self.status_label.clear())

    def set_session_id(self, new_session_id, dato):
        logging.info("RMA Def set_session_id entered")
        if new_session_id is None:
            print(f"Session ID not found in the database, setting to 1")
            logging.info(f"RMA Session ID not found in the database, setting to 1")
            self.session_id = 1
            self.session_id_updated.emit(self.session_id)
        else:
            print(f"Session ID fetched: ({new_session_id})")
            logging.info(f"RMA Session ID fetched: ({new_session_id})")
            dato = datetime.strptime(dato, "%Y-%m-%d").date()
            if dato != datetime.now().date():
                logging.info(f"Date from DB: {dato}")
                print(datetime.now().date())
                print(f"Session ID is not for today, setting to +1")
                logging.info(f"RMA Session ID is not for today, setting to +1")
                self.session_id = new_session_id + 1
            else:
                self.session_id = new_session_id
            self.session_id_updated.emit(self.session_id)
            if self.session_id > 1:
                self.db_queue.put(('load_score_data',(self.session_id-1,))) # Get the score data for the current session ID
            else:
                self.db_queue.put(('load_score_data',(self.session_id,))) # Get the score data for the current session ID
                    
    def handle_race_data_on_start(self, races, participants):
        logging.info("RMA Def handle race data on start entered")
        print("RMA Def handle_race_data_on_start entered")
        self.dropdown.clear()  # Clear the dropdown first
        if races:
            for race in races:
                race_id, track_variation, laps_in_event, race_date = race
                # Find participants for the current race
                race_participants = [p for p in participants if p[0] == race_id]
                # Format participant car names and ensure uniqueness
                cars = ', '.join(sorted(set([p[1] for p in race_participants]))) if race_participants else "No participants"
                # Combine race and participant information into the dropdown item
                item_text = f"Race_{race_id} - {race_date} - {track_variation} Laps:{laps_in_event} - {cars}"
                self.dropdown.blockSignals(True)
                self.dropdown.addItem(item_text)
                self.dropdown.setCurrentIndex(self.dropdown.count() - 1)  # Load the latest race results by default
                self.dropdown.blockSignals(False)
            print(f"Number of races loaded: {len(races)}")
            if not len(races) >1: self.load_selected_race()
            else: self.results_heading.setText("\n Select a Race to View previous races") 
        else:  
            self.results_name.setText("No Races in DB")
            self.final_heading.setText("\n All races Deleted")     

    def handle_high_scores_data_on_start(self, high_scores):
        logging.info("RMA Def handle high scores data entered")
        print("RMA Def handle high scores data entered")
        self.car_dropdown.clear()  # Clear the dropdown first
        self.track_dropdown.clear()  # Clear the dropdown first
        self.highscores_dict = {}  # Dictionary to store high scores
        self.car_dropdown.blockSignals(True)
        self.track_dropdown.blockSignals(True)
        if high_scores:
            for high_score in high_scores:
                name, lapnumber, bestlap, track,car = high_score
                if track not in self.highscores_dict: self.highscores_dict[track] = set() # If the track is not in the dictionary, add it with an empty set
                self.highscores_dict[track].add(car)# Add the car to the set of cars for the given track
                if car not in [self.car_dropdown.itemText(i) for i in range(self.car_dropdown.count())]: self.car_dropdown.addItem(car) # Check if the car is already in the dropdown before adding
                if track not in [self.track_dropdown.itemText(i) for i in range(self.track_dropdown.count())]: self.track_dropdown.addItem(track) # Check if the track is already in the dropdown before adding
                self.car_dropdown.setCurrentIndex(self.car_dropdown.count() - 1)  # Load the latest
                self.track_dropdown.setCurrentIndex(self.track_dropdown.count() - 1)  # Load the latest
            if not len(high_scores) >1: self.load_selected_highscore()
            #else: self.highscore_heading.setText("Select a Car to View High Scores")
            print(f"Number of high scores loaded: {len(high_scores)}")
            #print(f"High Scores Dictionary: {self.highscores_dict}")
        else:
            self.highscore_name.setText("No High Scores in DB")
        self.car_dropdown.blockSignals(False)
        self.track_dropdown.blockSignals(False)

    def load_selected_highscore(self):
        logging.info("RMA load_selected_highscore def entered")
        print("RMA load_selected_highscore def entered")
        selected_car = self.car_dropdown.currentText()
        selected_track = self.track_dropdown.currentText()
        print(f"Selected Car: {selected_car} Selected Track: {selected_track}")
        if self.car_dropdown.currentIndex() >= 0 and self.track_dropdown.currentIndex() >= 0:
            self.db_queue.put(('load_highscores', (selected_car, selected_track)))
            print(f"Load score for {selected_car} on {selected_track}")
            logging.info(f"RMA Load score for {selected_car} on {selected_track}")
        else:
            print(f"Car or Track not selected:{selected_car} {selected_track}")
            logging.info(f"Car or Track not selected:{selected_car} {selected_track}")

    def update_dropdowns(self):
            logging.info("RMA update dropdowns def entered")
            print("RMA update dropdowns def entered")
            self.car_dropdown.blockSignals(True)
            self.track_dropdown.blockSignals(True)
            sender = self.sender()
            
            # Clear the dropdowns before repopulating
            if sender == self.track_dropdown:
                self.car_dropdown.clear()
                selected_track = self.track_dropdown.currentText()

                # Populate the car dropdown based on the selected track
                if selected_track in self.highscores_dict:
                    cars_for_track = self.highscores_dict[selected_track]
                    for car in cars_for_track:
                        self.car_dropdown.addItem(car)

            elif sender == self.car_dropdown:
                self.track_dropdown.clear()
                selected_car = self.car_dropdown.currentText()

                # Populate the track dropdown based on the selected car
                for track, cars in self.highscores_dict.items():
                    if selected_car in cars:
                        self.track_dropdown.addItem(track)
            self.car_dropdown.blockSignals(False)
            self.track_dropdown.blockSignals(False)

    def clear_driver_dropdown(self):
        logging.info("RMA clear driver dropdown def entered")
        print("RMA clear driver dropdown def entered")
        self.driver_dropdown.blockSignals(True)
        self.driver_dropdown.setItemText(0, "")
        self.driver_dropdown.setCurrentIndex(0)
        self.driver_dropdown.blockSignals(False)

    def handle_driver_statistics_on_start(self, driverdata):
        logging.info("RMA Def handle driver statistics on start entered")
        print("RMA Def handle driver statistics on start entered")
        self.driver_dropdown.clear()  # Clear the dropdown first
        self.driver_dropdown.addItem("Select a driver or type a driver name...")
        self.driver_dropdown.blockSignals(True)
        self.driverdata = driverdata  # Store the driver data in a class variable
        if driverdata:
            for driver in driverdata:
                driver_name, lapnumber, bestlap, track, car = driver
                if driver_name not in [self.driver_dropdown.itemText(i) for i in range(self.driver_dropdown.count())]: self.driver_dropdown.addItem(driver_name)
            self.driver_dropdown.setCurrentIndex(0)
            print(f"Number of Highscores loaded: {len(driverdata)}")
            if len(driverdata) == 2: self.load_selected_driver()
            else: self.driver_statistics_heading.setText("\n Select a Driver to View Driver Statistics")
            self.all_driver_dropdown_items = [self.driver_dropdown.itemText(i) for i in range(1, self.driver_dropdown.count())]
        else:
            self.driver_statistics_heading.setText("\n No Driver Statistics in DB")
        self.driver_dropdown.blockSignals(False)

    def load_selected_driver(self):
        logging.info("RMA on driver statistics loaded def entered")
        print("RMA on driver statistics loaded def entered")
        selected_driver = self.driver_dropdown.currentText()
        if self.driver_dropdown.currentIndex() > 0:
            print(f"RMA Load driver statistics for {selected_driver} with index {self.driver_dropdown.currentIndex()}")
            logging.info(f"RMA Load driver statistics for {selected_driver}")
            driver = selected_driver
            heading = (f"<br><span style='color:{self.color_labels}'>Driver:</span> <span style='color:{self.color_values}'>{driver}</span><br>")
            loaded_lap = ''
            loaded_bestlap = ''
            loaded_track = ''
            loaded_car = ''
            if any(driver == record[0] for record in self.driverdata):
                print(f"Driver found: {driver}")
                for name, lapnumber, bestlap, track, car in self.driverdata:
                    if name == driver:
                        places = 1
                        loaded_track += (f"<span style='color:{self.color_values};'>{track}</span><br>")
                        loaded_car += (f"<span style='color:{self.color_pitstop};'>{car}</span><br>")       
                        loaded_bestlap += (f"<span style='color:{self.color_gold};'>{self.format_lap_time(bestlap)}</span><br>")
                        loaded_lap += (f"<span style='color:{self.color_scores};'>{lapnumber}</span><br>")
                        if places > 40: break
                        places += 1
                self.driver_statistics_heading.setText(heading)
                self.driver_statistics_track.setText(loaded_track)
                self.driver_statistics_car.setText(loaded_car)
                self.driver_statistics_laptime.setText(loaded_bestlap)            
                self.driver_statistics_lap.setText(loaded_lap)
                self.driver_dropdown.setItemText(0, "Select a driver or type a driver name...")
            else:
                self.driver_statistics_heading.setText("Driver not found")
                self.driver_statistics_track.setText("")
                self.driver_statistics_car.setText("")            
                self.driver_statistics_laptime.setText("")
                self.driver_statistics_lap.setText("")
        else:
            print(f"Driver not selected:{selected_driver}")
            logging.info(f"Driver not selected:{selected_driver}")
            return
        
    def load_selected_race(self): # Function to be called when the data is loaded
        #print("Load Selected race def entered")
        logging.info("RMA Load Selected race def entered")
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            match = re.search(r"Race_(\d+)", race_text)
            race_id = int(match.group(1))  # The number after "Race_"
            #print(f"Selected race: {race_id} from {race_text}")
            self.db_queue.put(('load_selected_race', (race_id,) )) # Queue the operation to DatabaseThread
            #print(f"Signal Sent")
            logging.info(f"RMA Load selected race Signal Sent")
        else:
            print(f"Race not selected:{selected_index}")   
            logging.info(f"Race not selected:{selected_index}")
        
    def on_race_loaded(self, race, participants, laps):
        logging.info("RMA on race loaded def entered")
        race_id, track_variation, laps_in_event, session_id = race # Function to be called when the data is loaded
        #print(f"Signal received")
        logging.info(f"RMA Load selected race Signal received")
        loaded_names = ''
        loaded_places = ''
        loaded_flags = ''
        loaded_pitstops = ''
        loaded_totals = ''
        loaded_bestlap = ''
        loaded_points = ''
        best_lap_time = {}

        if race_id:
            logging.info(f"RMA Load Selected Race, RaceID: {race_id}")
            #print(f"Load Selected Race, RaceID: {race_id}")
            displayed_participants = set()
            car_name = participants[0][4] if participants and participants[0][4] else "Unknown Car"
            heading = (f"<span style='color:{self.color_labels}'>Race No:</span> "
                         f"<span style='color:{self.color_values}'> {race_id} </span> "
                        f"<span style='color:{self.color_labels}'>Laps: </span> "
                        f"<span style='color:{self.color_values}'> {laps_in_event} </span> "
                        f"<span style='color:{self.color_labels}'>session_id: </span> "
                        f"<span style='color:{self.color_values}'>{session_id}</span><br> "
                        f"<span style='color:{self.color_labels}'>Track: </span> "
                        f"<span style='color:#ffd700;'> {track_variation} </span><br> "
                        f"<span style='color:{self.color_labels}'>Car: </span> "
                        f"<span style='color:#ffd700;'> {car_name} </span><br>")


            score_table = {int(k.split('_')[0]): int(v) for k, v in self.config['Score Table'].items() if k != 'best_lap'}
            place = 1
            for participant in participants:
                name, race_position, best_lap, last_lap, car, flags, pits = participant
                participant_laps = [lap for lap in laps if lap[2] == name]
                best_lap_time[name] = best_lap
                #if participant_laps:  # Check if the list is not empty
                #    best_lap_time[participant] = min(lap[4] for lap in participant_laps)  # Find the best (minimum) lap time
                total_time_seconds = sum(lap[4] for lap in participant_laps)
                total_time_str = self.format_lap_time(total_time_seconds)
                best_lap_str = self.format_lap_time(best_lap)
                   
                if name in displayed_participants:
                    continue  # Skip duplicate participant names

                # Add participant info to the result string
                displayed_participants.add(name)
                #spaces = (f"<br> {'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' if int(race_position) > 9 else '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'}")
                if flags == None: flags = ''
                if pits == 0: pits = ''
                loaded_places += (f"<span style='color:{self.color_labels};'>{race_position}</span><br>")
                loaded_names += (f"<span style='color:{self.color_labels};'>{name}</span><br>")
                loaded_flags += (f"<span style='color:{self.color_dnf if flags == 'DNF' else self.color_falsestart};'> {flags} </span><br>")          
                loaded_pitstops += (f"<span style='color:{self.color_pitstop};'> {pits} </span><br>")
                loaded_totals += (f"<span style='color:{self.color_values};'> {total_time_str} </span><br>")
                loaded_bestlap += (f"<span style='color:{self.color_values};'> {best_lap_str} </span><br>")
                loaded_points += str(score_table.get(place, 0)) + "<br>"
                place += 1 

            best_participant = min((participant for participant in best_lap_time if best_lap_time[participant] is not None), key=best_lap_time.get)
            best_time = best_lap_time[best_participant]
            loaded_names += (f"<br><span style='color:{self.color_labels};'>Best Lap: </span><span style='color:{self.color_values};'> {best_participant} - {self.format_lap_time(best_time)} </span><br>")

            self.results_heading.setText(heading)  # Update the UI with the loaded results            
            self.results_places.setText(loaded_places) 
            self.results_name.setText(loaded_names)
            self.results_flags.setText(loaded_flags)
            self.results_pitstops.setText(loaded_pitstops)
            self.results_bestlap.setText(loaded_bestlap)
            self.results_total.setText(loaded_totals) 
            self.results_points.setText(loaded_points) 

    def on_highscore_loaded(self, high_scores):
        logging.info("RMA Def on highscore loaded entered")
        print("RMA Def on highscore loaded entered")
        print(f"self.track_dropdown: {self.track_dropdown.currentText()} self.car_dropdown: {self.car_dropdown.currentText()}" )
        heading = (f"<span style='color:{self.color_labels}'>Track: </span><span style='color:{self.color_values}'>{self.track_dropdown.currentText() if self.track_dropdown.currentText() is not None else self.track_dropdown.currentText()} </span><br><span style='color:{self.color_labels}'>Car: </span><span style='color:{self.color_values}'> {self.car_dropdown.currentText()}</span><br>" ) # Update the heading with track variation and car names
        if high_scores:
            loaded_names = ''
            loaded_lap = ''
            loaded_place = ''
            place = 1
            for high_score in high_scores:
                name, lapnumber, bestlap, track, car = high_score
                loaded_names += (f"<span style='color:{self.color_labels};'>{name}</span><br>")
                loaded_lap += (f"<span style='color:{self.color_values};'>{self.format_lap_time(bestlap)}</span><br>")
                loaded_place += (f"<span style='color:{self.color_labels};'>{place} </span><br>")
                place += 1
                if place > 20: break
            best_lap = (f"{high_scores[0][0]} - {self.format_lap_time((high_scores[0][2]))}")
            print(f"Best Lap: {best_lap}")
            loaded_names += (f"<br><span style='color:{self.color_labels};'>Best Lap: </span><span style='color:{self.color_values};'> {best_lap} </span><br>")
            self.highscore_heading.setText(heading)
            self.highscore_places.setText(loaded_place)    
            self.highscore_name.setText(loaded_names)
            self.highscore_laptime.setText(loaded_lap)
        else:
            self.highscore_name.setText("No High Scores in DB")
            self.highscore_laptime.setText("No High Scores in DB")
        self.db_queue.put(('load_highscores_on_start',())) #Send the request to the DatabaseThread to load highscore data on start

    def handle_sessionid_data(self, sessionids):
        logging.info("RMA Def handle sessionid data entered")
        self.dropdown_sessionid.clear()  # Add this line to clear the dropdown
        self.sessionids = sessionids
        if sessionids:
            for session_id in sessionids:
                if len(sessionids) >1: self.dropdown_sessionid.blockSignals(True)
                self.dropdown_sessionid.addItem(f"Session ID - {session_id}")
                if len(sessionids) >1: self.dropdown_sessionid.blockSignals(False)
                
    def on_tab_changed(self, index):
        logging.info("RMA Def on_tab_changed entered")
        #print("RMA Def on_tab_changed entered")
        for widget_list in self.tab_widget_mapping.values(): # Hide all widgets first
            for widget_name in widget_list:
                if widget_name in self.labels:  # Check if the widget exists in the labels dictionary
                     self.labels[widget_name].hide()
        for widget_name in self.tab_widget_mapping.get(index, []): # Show only the widgets associated with the active tab
            if widget_name in self.labels:
                if self.racestarted != True:
                    self.labels[widget_name].show()
                else:
                    if (widget_name != 'new_session_button') and (widget_name != 'previous_session_button'):
                        self.labels[widget_name].show()
                
        if index == 0: self.update_background('live') # Handle other tab-specific logic, like background updates
        elif index == 1 or index ==2 or index == 3: self.update_background('status')
        elif index == 4:
            self.update_background('status')
            if self.all_driver_dropdown_items: # Check if the driver dropdown items have been loaded 
                for item in self.all_driver_dropdown_items:
                    self.driver_dropdown.addItem(item)
                self.driver_dropdown.setItemText(0, "Select a driver or type a driver name...")
                self.driver_dropdown.setCurrentIndex(0)

    def update_background(self, view):
        logging.info("RMA Def update_background entered")
        if view == 'status': self.background_label.setPixmap(self.live_status_image)
        elif view == 'live': self.background_label.setPixmap(self.live_background_image)

    def handle_connection_restored(self):
        logging.info("RMA Def handle_connection_restored entered")
        print("RMA Def handle_connection_restored entered")
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()

    def show_error_message(self, message): # Check if the error label already exists with the same message
        logging.info("RMA Def show_error_message entered")
        print ("RMA Def show_error_message entered")
        if hasattr(self, 'error_label') and self.error_label.text() == message: return  # Do not create a new label if the message is the same
        if hasattr(self, 'error_label'): self.error_label.deleteLater()  # Remove the existing error label
           
        # Create the error label with the new message
        self.error_label = QLabel(message, self)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setFixedSize(1060, 35)
        self.error_label.setStyleSheet("font-size: 18px; color: red; background-color: yellow; padding: 10px;")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_error_visibility)
        self.timer.start(500)  # Blink every 500 ms

    def toggle_error_visibility(self):
        #logging.info("RMA Def toggle_error_visibility entered")
        #print("RMA Def toggle_error_visibility entered")
        if hasattr(self, 'error_label') and self.error_label is not None:
            if self.error_label.isVisible(): self.error_label.setVisible(False)
            else: self.error_label.setVisible(True)
 
    def update_race_message(self, message):
        #print(f"RMA Race Message: {message}")
        #logging.info(f"RMA RaceMessage: {message}")
        self.live_status_label.setText(f"{message}")  # Update the status label  

    def setup_live_view(self): # Setup your live view widgets here
        logging.info("RMA Def setup_live_view entered")
        self.live_heading = QLabel(f"Waiting for a new race to start...Current Session: {self.session_id}", self.live_view_widget)
        self.live_heading.setStyleSheet("font-size: 16px;font-weight:bold; color: black;")
        self.live_view_layout.addWidget(self.live_heading, alignment=Qt.AlignTop)
        self.live_heading.setMinimumSize(200, 50)  # Set this to a size that you believe should fit your text
        
        # Add Race Status label for live updates
        self.live_status_label = QLabel("Race Messages here", self.live_view_widget)
        self.live_status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
        self.live_status_label.setMinimumSize(500, 50)  # Set this to a size that you believe should fit your text
        self.live_status_label.move(10, -10)

        # Add top times/speed label for live updates
        self.live_best_label = QLabel("Top Speed and Time", self.live_view_widget)
        self.live_best_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
        self.live_best_label.setMinimumSize(600, 50)  # Set this to a size that you believe should fit your text
        self.live_best_label.move(400, -10)
        self.layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add participant labels for live updates
        self.participant_labels = {}
        for i in range(20):  # Assuming 20 participants max
            self.participant_labels[i] = QLabel("", self.live_view_widget)
            self.live_view_layout.addWidget(self.participant_labels[i])
            self.participant_labels[i].hide()  # Hide labels initially
        # You can add other live view specific components here as per the original design.

    def setup_result_view(self): # Content label for displaying loaded results
        logging.info("RMA Def setup_result_view entered")
        #Create the Previous Races graphics
        self.result_background_label = QLabel(self.results_view_widget)
        pixmap = QPixmap(self.result_background_image)
        self.result_background_label.setPixmap(pixmap)
        font_name = self.font_family

        # Resize the QLabel to the new size
        self.results_view_layout.addWidget(self.result_background_label)
        self.result_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add the content label for displaying the Header Data
        self.results_heading = QLabel("\n Select a race to view previous races", self.results_view_widget)
        self.results_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.results_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_heading.move(30, 15)

        # Add the content label for displaying the loaded results
        self.results_places = QLabel("#", self.results_view_widget)
        self.results_places.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_places.setMinimumSize(100, 900)  # Set this to a size that you believe should fit your text
        self.results_places.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_places.move(60, 165)

        # Add the content label for displaying the loaded results
        self.results_name = QLabel("Name", self.results_view_widget)
        self.results_name.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_name.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.results_name.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_name.move(100, 165)

        self.results_flags = QLabel("Flags", self.results_view_widget)
        self.results_flags.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_flags.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.results_flags.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_flags.move(490, 165)

        self.results_pitstops = QLabel("Pits", self.results_view_widget)
        self.results_pitstops.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_pitstops.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.results_pitstops.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.results_pitstops.move(620, 165)

        self.results_bestlap = QLabel("Lap", self.results_view_widget)
        self.results_bestlap.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_bestlap.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.results_bestlap.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_bestlap.move(720, 165)

        self.results_total = QLabel("Total", self.results_view_widget)
        self.results_total.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_total.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.results_total.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_total.move(845, 165)

        self.results_points = QLabel("#", self.results_view_widget)
        self.results_points.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.results_points.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.results_points.setAlignment(Qt.AlignHCenter| Qt.AlignTop)
        self.results_points.move(965, 165) 
        
    def setup_final_view(self): # Content label for displaying Final results
        logging.info("RMA Def setup_final_view entered")
        font_name = self.font_family
        self.final_background_label = QLabel(self.final_view_widget)
        pixmap = QPixmap(self.final_background_image)
        self.final_background_label.setPixmap(pixmap)
        self.final_view_layout.addWidget(self.final_background_label)
        self.final_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.final_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))
  
        #self.final_content = QLabel("No race data available", self.final_view_widget)
        #self.final_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        #self.final_view_layout.addWidget(self.final_content)
        #self.final_view_layout.addStretch(1)

        # Add the content label for displaying the Header Data
        self.final_heading = QLabel("Select a session to view scores", self.final_view_widget)
        self.final_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.final_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_heading.move(30, 15)

        # Add the content label for displaying the loaded results
        self.final_places = QLabel("#", self.final_view_widget)
        self.final_places.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_places.setMinimumSize(100, 900)  # Set this to a size that you believe should fit your text
        self.final_places.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_places.move(60, 165)

        # Add the content label for displaying the loaded results
        self.final_name = QLabel("Name", self.final_view_widget)
        self.final_name.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_name.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.final_name.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_name.move(100, 165)
 
        self.final_lastpos = QLabel("LastPos", self.final_view_widget)
        self.final_lastpos.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_lastpos.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.final_lastpos.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_lastpos.move(490, 165)

        self.final_points = QLabel("#", self.final_view_widget)
        self.final_points.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_points.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_points.setAlignment(Qt.AlignHCenter| Qt.AlignTop)
        self.final_points.move(620, 165)  

        self.final_gold = QLabel("Gold", self.final_view_widget)
        self.final_gold.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_gold.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_gold.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.final_gold.move(720, 165)

        self.final_silver = QLabel("Silver", self.final_view_widget)
        self.final_silver.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_silver.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_silver.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.final_silver.move(820, 165)

        self.final_bronze = QLabel("Bronze", self.final_view_widget)
        self.final_bronze.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.final_bronze.setMinimumSize(15, 900)  # Set this to a size that you believe should fit your text
        self.final_bronze.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        self.final_bronze.move(920, 165)

    def setup_highscore_view(self): # Content label for displaying Final results
        logging.info("RMA Def setup_higscore_view entered")
        font_name = self.font_family
        self.highscore_background_label = QLabel(self.highscore_view_widget)
        pixmap = QPixmap(self.highscore_background_image)
        self.highscore_background_label.setPixmap(pixmap)
        self.highscore_view_layout.addWidget(self.highscore_background_label)
        self.highscore_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.highscore_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add the content label for displaying the Header Data
        self.highscore_heading = QLabel("\n Select a track and car to view high Scores", self.highscore_view_widget)
        self.highscore_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.highscore_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_heading.move(30, 15)
        
        # Add the content label for displaying places
        self.highscore_places = QLabel("#", self.highscore_view_widget)
        self.highscore_places.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_places.setMinimumSize(100, 900)  # Set this to a size that you believe should fit your text
        self.highscore_places.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_places.move(60, 165)

        # Add the content label for displaying the loaded results
        self.highscore_name = QLabel("Name", self.highscore_view_widget)
        self.highscore_name.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_name.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.highscore_name.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_name.move(100, 165)
 
        self.highscore_laptime = QLabel("Laptime", self.highscore_view_widget)
        self.highscore_laptime.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.highscore_laptime.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.highscore_laptime.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_laptime.move(490, 165)

    def setup_driver_statistics_view(self): # Content label for displaying Final results
        logging.info("RMA Def setup_higscore_view entered")
        font_name = self.font_family
        self.driver_statistics_background_label = QLabel(self.driver_statistics_widget)
        pixmap = QPixmap(self.driver_statistics_background_image)
        self.driver_statistics_background_label.setPixmap(pixmap)
        self.driver_statistics_layout.addWidget(self.driver_statistics_background_label)
        self.driver_statistics_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.driver_statistics_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Add the content label for displaying the Header Data
        self.driver_statistics_heading = QLabel("Select a driver to view statistics", self.driver_statistics_widget)
        self.driver_statistics_heading.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.driver_statistics_heading.setMinimumSize(650, 200)  # Set this to a size that you believe should fit your text
        self.driver_statistics_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_heading.move(30, 15)
        

        # Add the content label for displaying the loaded results
        self.driver_statistics_track = QLabel("Track", self.driver_statistics_widget)
        self.driver_statistics_track.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_track.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_track.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_track.move(45, 165)

        # Add the content label for displaying the loaded results
        self.driver_statistics_car = QLabel("Car", self.driver_statistics_widget)
        self.driver_statistics_car.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_car.setMinimumSize(1000, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_car.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_car.move(520, 165)
        

        self.driver_statistics_laptime = QLabel("Laptime", self.driver_statistics_widget)
        self.driver_statistics_laptime.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_laptime.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_laptime.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_laptime.move(900, 165)

        self.driver_statistics_lap = QLabel("Lap", self.driver_statistics_widget)
        self.driver_statistics_lap.setStyleSheet(f"font-family:{font_name};font-size: 14px;")
        self.driver_statistics_lap.setMinimumSize(150, 900)  # Set this to a size that you believe should fit your text
        self.driver_statistics_lap.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_lap.move(1015, 165)   

    def on_first_live_view_run(self, data):
        logging.info("RMA Def on_first_live_view_run entered")
        self.event_info = data['eventInformation'] # Extract event information and participant details from the data
        participants = data['participants']['mParticipantInfo']
        sessionstate = data['gameStates']['mSessionState']
        if len(self.sessionids) < 1: self.final_heading.setText("Score - Waiting for a new race to finish...")
    
        self.current_lap = {}
        self.previous_current_lap = {}
        self.best_lap_time = 999
        self.best_top_speed = 0
        self.lap_time ={}
        self.lap_list = {}
        self.total_time_seconds = {}
        self.driver_flags = {}
        self.top_speed = {}
        self.best_lap_driver = ""
        self.top_speed_driver = ""
        
        heading_text = f"{self.event_info['mTranslatedTrackLocation']} - {self.event_info['mTranslatedTrackVariation']} ({'Qualify' if sessionstate == 3 else self.event_info['mLapsInEvent']}) - {participants[0]['mCarNames']} - {len(participants)} Drivers - Session ID: {self.session_id}" # Create the heading text
        self.live_heading.setText(heading_text)
        if sessionstate == 3: self.live_status_label.setText("Qualifying in progress ...")
        else:
            self.live_status_label.setText("Waiting for Green Light...")  # Update the status label
        self.live_best_label.setText("Top Speed and Time")  # Update the status label
        self.new_session_button.hide()
        self.previous_session_button.hide()
        self.racestarted = True
        self.pit_stop = {}
        self.pit_stops = ""
        self.background_color = "#333333"  # Default background color
        self.top_background_color = "#a80baa"  # Default top background color
        self.race_started = False
        self.session_id_updated.emit(self.session_id)
        for i in range(20): self.participant_labels[i].hide()  # Hide labels initially  # Assuming 20 participants max
        
    def update_live_view(self, data):
        if self.live_first_time_run: self.on_first_live_view_run(data)
        participants = data['participants'].get('mParticipantInfo', None)
        if not participants: return
        sorted_participants = sorted( participants[:data['participants']['mNumParticipants']], key=lambda p: (float('inf') if self.driver_flags.get(p['mName']) == 'Falsestart' else p['mRacePosition']))
        if data['gameStates']['mRaceState'] == 2 and not self.race_started:
            self.live_status_label.setText("Green Light! GO GO GO")
            self.race_started = True
        elif data['gameStates']['mRaceState'] == 3 or data['gameStates']['mRaceState'] == 6: self.live_status_label.setText("Race Ending....")  # Update the status label"self.live_status_label.setText
        sessionstate = data['gameStates']['mSessionState']
        
        for i, participant in enumerate(sorted_participants): # Loop through each participant to update their corresponding label
            self.current_lap[participant['mName']] = participant['mCurrentLap'] 
            if participant['mLastLapTimes'] != -123 and participant['mName'] in self.previous_current_lap:
                if self.current_lap[participant['mName']] != self.previous_current_lap.get(participant['mName'], None):
                    self.live_status_label.setText(f"{participant['mName']} is now on lap {participant ['mCurrentLap']}{' (Qualify)'if sessionstate==3 else ""}")  # Update the status label
                    self.lap_time[participant['mName']] = participant['mLastLapTimes']
                    if participant['mName'] not in self.lap_list:
                        self.lap_list[participant['mName']] = [self.format_lap_time(self.lap_time[participant['mName']])]
                        self.total_time_seconds[participant['mName']] = self.lap_time[participant['mName']]
                    else:
                        self.lap_list[participant['mName']].append(self.format_lap_time(self.lap_time[participant['mName']]))
                        self.total_time_seconds[participant['mName']] += self.lap_time[participant['mName']]
                    self.previous_current_lap[participant['mName']] = self.current_lap[participant['mName']]
            else: self.previous_current_lap[participant['mName']] = 1
            if participant['mName'] in self.lap_list: lap_times_str = ", ".join(self.lap_list[participant['mName']])
            else: lap_times_str = "No Valid Lap!" 
            last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
            if participant['mName'] in self.total_time_seconds: total_time_str = self.format_lap_time(self.total_time_seconds[participant['mName']])
            else: total_time_str = "No Valid Lap!"
            flag = self.driver_flags.get(participant['mName'], None) # Check if the participant has a flag in self.driver_flags
            if not flag: flag = "" # If the participant has no flag, set it to an empty string
            if i < 20: label = self.participant_labels[i]
            label.setStyleSheet(f"font-size: 14px; background-color: {self.top_background_color if participant['mFastestLapTimes'] <= self.best_lap_time and participant['mCurrentLap'] > 1 else self.background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;") 
            participant_text = self.create_participant_text(participant,flag, last_lap_str, lap_times_str, sessionstate, total_time_str) # Create the participant text using the utility function
            if self.live_first_time_run: label.show()  # Sets all labels to the default background color if no valid lap times are found and it is first run.                   
            label.setText(participant_text)  # Update the existing label with the new participant text and styling
            label.show()  # Make the label visible
        self.live_first_time_run = False
       
    def format_lap_time(self, lap_time): # Helper function to format lap time from seconds to 'MM:SS.ss' format.
        if lap_time is None or lap_time == -123.0: return "N/A"
        minutes = int(lap_time // 60)
        seconds = lap_time % 60
        return f"{minutes}:{seconds:05.2f}"
    
    def create_participant_text(self, participant,flag, last_lap_str, lap_times_str, sessionstate, total_time_str=""): # Helper function to create participant text with custom styling.self.initialize_dropdown
        if self.top_speed.get(participant['mName'],-1000) <math.floor(participant['mSpeeds']): self.top_speed[participant['mName']] = math.floor(participant['mSpeeds'])
        speed_time_updated = False
        lap_time_updated = False
        if math.floor(participant['mSpeeds']) > self.best_top_speed:
            self.best_top_speed = math.floor(participant['mSpeeds'])
            self.top_speed_driver = participant['mName']    
            speed_time_updated = True
        if participant['mFastestLapTimes'] < self.best_lap_time and participant['mCurrentLap'] > 1 and participant['mFastestLapTimes'] != -123:
            self.best_lap_time = participant['mFastestLapTimes']
            self.best_lap_driver = participant['mName']
            print(f"RMA New best Lap Time: {self.format_lap_time(self.best_lap_time)}")
            self.live_status_label.setText(f"{participant['mName']} just got a new best lap time{' (Qualify)'if sessionstate==3 else ""}: {self.format_lap_time(self.best_lap_time)}")
            lap_time_updated = True
        if lap_time_updated or speed_time_updated:
            self.live_best_label.setText(    
            f"Top Speed:  {self.top_speed_driver} {self.best_top_speed *3.6:.0f} Km/t "
            f" Best Lap: {self.best_lap_driver} {self.format_lap_time(self.best_lap_time) if self.best_lap_time != 999 else 'No Valid Lap!'}")
            speed_time_updated = False
            lap_time_updated = False
        fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])
        lap_times_split = lap_times_str.split(", ")
        lap_times_newstr = [] # Rebuild the string, inserting a <br> after every 8 lap times
        for i in range(len(lap_times_split)): lap_times_newstr.append(lap_times_split[i])
        if len(lap_times_newstr) > 17: lap_times_newstr = lap_times_newstr[len(lap_times_newstr) - 16:]
        lap_times_str = ", ".join(lap_times_newstr)

        if participant['mCurrentLap'] -1 == self.event_info['mLapsInEvent'] and sessionstate != 3: race_status = "<span style='color:#FF0000;font-weight:bold'>(Finished!)</span>"
        else: race_status = ""
        flag_text = f" <span style='color:#e73c3c;font-weight:bold'>({flag})</span>" if flag else ''
        pit = f"<span style='color:#00FF00;font-weight:bold'>(PIT)</span>" if participant['mPitModes'] != 0 else ''
        if participant['mName'] not in self.pit_stop: self.pit_stop[participant['mName']] = {}
        self.pit_stops = (f"<span style='color:#00fff0'>Pits: </span><span style='color:#FFD700'>{sum(self.pit_stop[participant['mName']].values())}</span>" if sum(self.pit_stop[participant['mName']].values()) > 0 else "")
        if participant['mPitModes'] == 2 and  participant['mCurrentLap'] not in self.pit_stop[participant['mName']]:
            self.pit_stop[participant['mName']][participant['mCurrentLap']] = 1
            self.pit_stops_updated.emit(self.pit_stop)
            self.live_status_label.setText(f"{participant['mName']} entered PIT")
            print(f"RMA Pit Stop added for {participant['mName']} number of pitstops:{sum(self.pit_stop[participant['mName']].values())} all pit pit stop: {self.pit_stop}")
            print (f"RMA Number of pitstops for participant {participant['mName']}: {sum(self.pit_stop[participant['mName']].values())}")
            logging.info(f"RMA Pit Stop added for {participant['mName']} number of pitstops:{sum(self.pit_stop[participant['mName']].values())} all pit pit stop: {self.pit_stop}")
        spaces = (f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'&nbsp;&nbsp;' if participant['mRacePosition'] > 9 else ''}<span style='color:#00FF00;'>")
        return (
        f"<span style='font-weight:bold; color:#FFFFFF;'>{participant['mRacePosition']}</span>: "
        f"<span style='color:#FFFFFF;font-weight:bold'>{participant['mName']} {race_status} {flag_text} {pit} {self.pit_stops} </span>"
        #f"<span style='color:#00fff0;'>Speed: <span style='color:#FFD700;'>({participant['mPitModes']}) {participant['mSpeeds'] *3.6:.0f} Km/t</span> - "
        f"<span style='color:#00fff0;'>Speed: <span style='color:#FFD700;'>{participant['mSpeeds'] *3.6:.0f} Km/t</span> - "
        f"<span style='color:#00fff0;'>Car: <span style='color:#FFD700;'>{participant['mCarNames']}</span> - "
        f"<span style='color:#00fff0;'>Top Speed: <span style='color:#FFD700;'>{self.top_speed[participant['mName']] *3.6:.0f}</span> - "
        f"<span style='color:#00fff0;'>Lap: <span style='color:#FFD700;'>{participant['mCurrentLap']}</span> - "  
        f"<span style='color:#00fff0;'>Last Lap: <span style='color:#FFD700;'>{last_lap_str}</span> - "
        f"<span style='color:#00fff0;'>Best: <span style='color:#FFD700;'>{fastest_lap_str}</span> - "
        f"<span style='color:#00fff0;'>Total: <span style='color:#FFD700;'>[{total_time_str}]</span>"
        f"{spaces}<span style='color:#00fff0;'>Laptimes: <span style='color:#00FF00;'>[{lap_times_str}]</span>")

    def display_final_results(self): # Display the score data in the final view
        logging.info("RMA Def display_final_results entered")
        self.live_status_label.setText("Waiting for a new race to start...")  # Update the status label"
        self.racestarted =False
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop() 
        self.live_first_time_run =True
        self.initialize_dropdown()

    def qualify_finished(self):
        logging.info("RMA Def qualify_finished entered")
        self.live_status_label.setText("Qualifying Finished! Waiting for Race to start...")  # Update the status label"
        self.racestarted = False
        self.live_first_time_run = True

    def display_score(self):
        logging.info(f"RMA Display Score Result def entered")
        print(f"RMA Display score Result")
        self.selected_index = self.dropdown_sessionid.currentIndex()
        if self.selected_index >= 0:
            sessionid_text = self.dropdown_sessionid.itemText(self.selected_index)
            logging.info(f"RMA Selected Session: {sessionid_text}")
            self.session_id_dropdown = sessionid_text.split(" - ")[-1]       
        if hasattr(self, 'error_label'): # Clear any existing error message if the connection is successful
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()
        if self.session_id_dropdown != None:
            logging.info(f"RMA Get score Data. Session ID: {self.session_id_dropdown}")
            self.db_queue.put(('load_score_data',(self.session_id_dropdown,))) #Get data I need to calculate score (New Session ID button must not be pushed before this))
        logging.info(f"RMA Accumulated Score for Session {self.session_id_dropdown}")
        
    def calculate_score(self, races, participants, laps):
        logging.info("RMA Def calculate_score entered")
        processed_race_ids = set()  # Add this line at the start of the method
        race_scores = {}  # Dictionary to store the score for each participant in each race
        total_scores = {}  # Dictionary to accumulate total scores for each participant across all races
        race_scores = {}  # Dictionary to store the score for each participant in each race
        last_positions = {}  # To store the last position of each driver
        medal_counts = {'gold': {}, 'silver': {}, 'bronze': {}}  # To count gold, silver, and bronze medals
        score_table = {int(k.split('_')[0]): int(v) for k, v in self.config['Score Table'].items() if k != 'best_lap'} # Extract scoring rules
        best_lap_bonus = int(self.config['Score Table']['best_lap'])
        
        if races: # Iterate over each race
            for race in races:
                race_id = race[0]  # Assuming race_id is the first element in the race tuple
                processed_race_ids.add(race_id)  # Add this inside the loop that iterates over each race
                race_scores[race_id] = {} # Initialize the race-specific data
                driver_total_times = {} # Dictionary to store the total time for each driver in the
                driver_flags = {} # Dictionary to store the flag for each driver
                best_lap_times = {} # Dictionary to store the best lap time for each driver
                driver_laps_completed = {} # Dictionary to store the number of laps completed by each driver
                driver_race_positions = {} # Dictionary to store the race position for each driver
                race_participants = [p for p in participants if p[0] == race_id] # Checking to see if there are any participants in this race
                if not race_participants:
                    print(f"No participants found for race {race_id}. Skipping score calculation for this race.")
                    logging.info(f"RMA No participants found for race {race_id}. Skipping score calculation for this race.")
                    continue               
                # Retrieve flags and best lap times from the participants table for the current race
                for participant in participants:
                    participant_race_id = participant[0]
                    if participant_race_id != race_id:
                        continue  # Only consider participants from the current race
                    mName = participant[1]
                    flag = participant[7]  # Flags column in the participants table
                    driver_total_times[mName] = participant[8]
                    if flag == 'DNF' and mName not in driver_total_times:
                        driver_total_times[mName] = 0  # Assign a total time of 0
                    # Store the specific flag values
                    if flag == 'Falsestart':
                        driver_flags[mName] = 'Falsestart'
                    elif flag == 'DNF':
                        driver_flags[mName] = 'DNF'
                    else:
                        driver_flags[mName] = 'No Flag'
                    best_lap = participant[4]  # Best lap time in the participants table
                    # Store the flag  for each driver
                    driver_flags[mName] = flag if flag else "No Flag"
                    best_lap_times[mName] = best_lap if best_lap else float('inf') 
                    driver_laps_completed[mName] = participant[6]
                    driver_race_positions[mName] = participant[3]
                # Custom flag priority function
                def flag_priority(flag):
                    if flag == 'No Flag' or flag is None:
                       return 0  # Highest priority
                    elif flag == 'DNF':
                        return 1  # Medium priority
                    elif flag == 'Falsestart':
                        return 2  # Lowest priority
                    return 3  # Default (in case there's an unexpected flag)
                # Rank drivers based on custom flag priority and total race time
                self.ranked_drivers = sorted(
                driver_total_times.keys(),
                key=lambda x: (
                    flag_priority(driver_flags.get(x, "No Flag")),
                    -driver_laps_completed.get(x, 0) if driver_flags.get(x) == "DNF" else 0,
                    driver_race_positions.get(x, float('inf')) if driver_flags.get(x) == "DNF" else 0,
                    float('inf') if driver_flags.get(x) != "No Flag" else driver_total_times[x]))
                place = 1
                for mName in self.ranked_drivers:
                    race_scores[race_id][mName] = score_table.get(place, 0)  # Assign points based on position
                    last_positions[mName] = place # Track the last position for each driver
                    if place == 1: # Track gold, silver, and bronze medals
                        medal_counts['gold'][mName] = medal_counts['gold'].get(mName, 0) + 1
                    elif place == 2:
                        medal_counts['silver'][mName] = medal_counts['silver'].get(mName, 0) + 1
                    elif place == 3:
                        medal_counts['bronze'][mName] = medal_counts['bronze'].get(mName, 0) + 1
                    place += 1
                # Determine the driver with the best lap time in the race
                if best_lap_times:  # Ensure there are lap times to compare
                    best_lap_driver = min(best_lap_times.items(), key=lambda x: x[1])[0]
                    # Award the best lap bonus to that driver
                    if best_lap_times[best_lap_driver] < float('inf'):
                        if best_lap_driver in race_scores[race_id]:
                            race_scores[race_id][best_lap_driver] += best_lap_bonus
                        else:
                            race_scores[race_id][best_lap_driver] = best_lap_bonus
            # Aggregate the scores across all races
            for race_id, scores in race_scores.items():
                for mName, score in scores.items():
                    if mName not in total_scores:
                        total_scores[mName] = 0
                    total_scores[mName] += score
            self.format_score_view(total_scores, len(processed_race_ids), last_positions, medal_counts, races) # Update the UI with the calculated scores
            logging.info(f"Ranked drivers: {self.ranked_drivers}")
        else:
            self.session_id = 1
            self.session_id_updated.emit(self.session_id)
            #self.final_heading.setText(f"<span style='color:{self.color_labels}'>Next Race will be session: </span><span style='color:{self.color_values}'>{self.session_id}</span>")
            self.final_heading.setText("\n All races Deleted")
            self.final_places.setText('') 
            self.final_name.setText('')  
            self.final_lastpos.setText('')  
            self.final_points.setText('')
            self.final_gold.setText('')
            self.final_silver.setText('')
            self.final_bronze.setText('')

    def format_score_view(self, total_scores, race_count, last_positions, medal_counts, races):
        logging.info("RMA Def format_score_view entered")
        print(f"RMA Def format_score_view entered")
        loaded_names = ''
        loaded_places = ''
        loaded_lastpos = ''
        loaded_gold = ''
        loaded_silver = ''
        loaded_bronze = ''
        loaded_points = ''
        sorted_scores = sorted(total_scores.items(), key=lambda x: x[1], reverse=True) # Sort the drivers by their total score, highest to lowest
        race_ids =  [race[0] for race in races]
        race_ids_str = f"({', '.join(map(str, race_ids))})"

        heading = (f"<span style='color:{self.color_labels}'>Session:</span><span style='color:{self.color_values}'> {self.session_id_dropdown if self.session_id_dropdown is not None else self.session_id-1}</span>  <span style='color:{self.color_labels}'>Next Race will be session: </span><span style='color:{self.color_values}'> {self.session_id}</span><br>" # Update the heading with track variation and car names
            f"<span style='color:{self.color_labels}'>Number of Races: </span> "     
            f"<span style='color:{self.color_values}'> {race_count} </span> <br>"
            f"<span style='color:{self.color_labels}; font-size: 16px;'>Races: </span>"
            f"<span style='color:{self.color_values}; font-size: 16px;'> {race_ids_str} </span>")

        for i, (mName, score) in enumerate(sorted_scores, start=1):
            last_pos = last_positions.get(mName, 'N/A')
            gold = medal_counts['gold'].get(mName, 0)
            silver = medal_counts['silver'].get(mName, 0)
            bronze = medal_counts['bronze'].get(mName, 0)
            # Add participant info to the result string
            #print(f"RMA Participant: {mName} - Score: {score} - Last Position: {last_pos} - Gold: {gold} - Silver: {silver} - Bronze: {bronze}")

            loaded_places += (f"<span style='color:{self.color_labels};'>{i}</span><br>")
            loaded_names += (f"<span style='color:{self.color_labels};'>{mName}</span><br>")
            loaded_lastpos += (f"<span style='color:{self.color_lastpos};'> {last_pos} </span><br>")
            loaded_points += (f"<span style='color:{self.color_scores};'> {score} </span><br>")                      
            loaded_gold += (f"<span style='color:{self.color_gold};'> {gold} </span><br>")
            loaded_silver += (f"<span style='color:{self.color_silver};'> {silver} </span><br>")
            loaded_bronze += (f"<span style='color:{self.color_bronze};'> {bronze} </span><br>")

        if not self.racestarted: self.live_status_label.setText("Score Calculated! for session: " + str(self.session_id))
        self.final_heading.setText(heading)  # Update the UI with the loaded results        
        self.final_places.setText(loaded_places)
        self.final_name.setText(loaded_names)
        self.final_lastpos.setText(loaded_lastpos)
        self.final_points.setText(loaded_points)
        self.final_gold.setText(loaded_gold) 
        self.final_silver.setText(loaded_silver)
        self.final_bronze.setText(loaded_bronze) 

    def delete_selected_race(self):
        logging.info(f"RMA Delete selected race def entered")
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            match = re.search(r"Race_(\d+)", race_text)
            race_id = int(match.group(1))  # The number after "Race_"

            def on_race_deleted(race_id):
                print("Should only see this once")
                logging.info("RMA Should only see this once")
                if race_id is not None:
                    self.initialize_dropdown()
                else:
                    print(f"on_race_deleted:Race_id is None:{race_id}")
                    logging.info(f"on_race_deleted:Race_id is None:{race_id}")
            self.set_delete_mode(True)  # Activates delete mode
            self.db_queue.put(('delete_race', (race_id, on_race_deleted))) #Send request to DatabaseThread
            QTimer.singleShot(1000,lambda: self.set_delete_mode(False))
            QTimer.singleShot(1000, self.after_timer_race_deleted)

    def after_timer_race_deleted(self):
        new_text= "\n" "Race Deleted"
        self.results_heading.setText(new_text)
        self.results_places.setText('') 
        self.results_name.setText('')
        self.results_flags.setText('')
        self.results_pitstops.setText('')
        self.results_bestlap.setText('')
        self.results_total.setText('') 
        self.results_points.setText('') 

    def delete_selected_driver(self):
        logging.info(f"RMA Delete selected driver def entered")
        selected_index = self.driver_dropdown.currentIndex()
        if selected_index > 0:
            driver_text = self.driver_dropdown.itemText(selected_index)

            def on_driver_deleted(driver_text):
                print("Should only see this once")
                logging.info("RMA Should only see this once")
                if driver_text is not None:
                    self.initialize_dropdown()
                else:
                    print(f"on_driver_deleted:Driver_text is None:{driver_text}")
                    logging.info(f"on_driver_deleted:Driver_text is None:{driver_text}")

            self.db_queue.put(('delete_driver', (driver_text, on_driver_deleted))) #Send request to DatabaseThread
            QTimer.singleShot(1000, self.after_timer_driver_deleted)

    def after_timer_driver_deleted(self):
        new_text= "\n" "Driver Deleted"
        self.driver_statistics_heading.setText(new_text)
        self.driver_statistics_track.setText('') 
        self.driver_statistics_car.setText('')
        self.driver_statistics_laptime.setText('')
        self.driver_statistics_lap.setText('')

    def set_delete_mode(self, is_active):
        logging.info("RMA Def set_delete_mode entered")
        if is_active:
            self.delete_button.setText("Deleting Race...")
            '''
            self.delete_button.setStyleSheet("""
                font-size: 14px;
                background-color: #d9534f;  # Bootstrap's danger color
                color: white;
                margin-bottom: 5px;                             
                border: 2px solid darkred;
                border-radius: 5px;
            """)
            '''
            self.delete_button.setEnabled(False)
        else:
            self.delete_button.setText("Delete Selected Race")
            self.delete_button.setStyleSheet("""
                 font-size: 14px;
                 background-color: #a32d2d;
                 color: white;
                 margin-bottom: 5px;                             
                 border: 2px solid black;  /* Change the border color */
                 border-radius: 5px;  /* Optional: rounded corners */
            """)        
            self.delete_button.setEnabled(True)         

    def start_new_session(self):
        logging.info(f"RMA Start New Session entered")
        self.display_score()
        logging.info("RMA Def start_new_session entered")
        self.session_id += 1
        #self.final_heading.setText(f"Accumulated Score for Session {self.session_id_dropdown} Next Race will be session: {self.session_id}")
        logging.info(f"Self selected index: {self.selected_index}")
        self.session_id_updated.emit(self.session_id)
    
    def write_all_scores(self):
        logging.info("RMA Def write_score_button entered") 
        
    def previous_session(self):
        logging.info("RMA Def go back session entered")
        self.session_id -= 1
        if self.session_id <1: self.session_id = 1
        self.db_queue.put(('load_score_data',(self.session_id_dropdown,))) # Get the score data for the current session ID
        #self.final_heading.setText(f"Accumulated Score for Session {self.session_id_dropdown} Next Race will be session: {self.session_id}")

        print(f"Self selected index: {self.selected_index}")
        self.session_id_updated.emit(self.session_id)

    def closeEvent(self, event):
        self.stop()
        event.accept()
        
    def stop(self):
        print("Closing the application...")
        app.quit() # Quit the application immediately.
        if hasattr(self, 'db_thread') and self.db_thread.isRunning(): # Stop the database thread if it exists and is running
            logging.info("Stopping DatabaseThread...")
            self.db_thread.stop()
            self.db_thread.wait()  # Wait for the thread to finish
            print("Database thread stopped.")
        logging.info("Stopping MonitorThread...")
        print("Stopping MonitorThread...")
        if hasattr(self, 'monitor_thread'):
            try:
                self.monitor_thread.data_updated.disconnect()
                self.monitor_thread.race_finished.disconnect()
            except TypeError:
                pass  # Signals might already be disconnected or not connected
        if hasattr(self, 'monitor_thread') and self.monitor_thread.isRunning(): # Stop the monitor thread if it exists and is running
                self.monitor_thread.running = False
                print("Running self monitor thread stop")
                self.monitor_thread.wait()  # Wait for the thread to finish
                print("Monitor thread stopped.")
                pass  # Signals might already be disconnected or not connected
        logging.info("RaceMonitorApp stopped successfully.") # Log completion of stopping sequence

def main():
    global app
    app = QApplication(sys.argv)
    ex = RaceMonitorApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address