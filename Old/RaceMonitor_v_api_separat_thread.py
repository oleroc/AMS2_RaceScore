from re import L, T
import sys
from timeit import Timer
import re
import requests
import sqlite3
import queue
import json
import time
import traceback
import logging
import os
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QTabWidget, QSpacerItem
from PyQt5.QtGui import QPixmap, QIcon
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer, QObject
from datetime import datetime

if os.path.exists('debug.log'): # Set up logging
    os.remove('debug.log')
    logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

def resource_path(relative_path):
    """
    Get the absolute path to a resource, works for development and for PyInstaller.
    
    Args:
        relative_path (str): The relative path to the resource file.

    Returns:
        str: The absolute path to the resource.
    """
    # When the application is bundled by PyInstaller and running as an executable,
    # resources are extracted to a temporary folder. We access them via sys._MEIPASS.
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temporary folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # If we are running in development (not bundled), use the relative path
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

class ConfigManager:
    def __init__(self):
        self.config_file = 'config.ini'
        self.__version__ = "1.3.2"
        self.__author__ = "RockyTM"
        self.__email__ = "post@drs.no"
        self.__date__ = "2024-08-23"
        self.__description__ = "Script for getting Race Data from AMS2"

    
    def update_config_file(self):
        config = configparser.ConfigParser()
        try:
            # Check if the config file exists
            if not os.path.exists(self.config_file):
                # Create a new config file with default settings
                config['config'] = {
                    'ip_address': '127.0.0.1',
                    'version': self.__version__  # Add version information
                }
                # Add or update the 'Score Table' section
                config['Score Table'] = {
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
                with open(self.config_file, 'w') as configfile:
                    config.write(configfile)

                print(f"Config file created with default settings at {self.config_file}.")
                logging.info(f"Config file created with default settings at {self.config_file}.")
            else:
                # Read the existing config file
                config.read(self.config_file)

                # Update the version information
                config['config']['version'] = self.__version__

                with open(self.config_file, 'w') as configfile:
                    config.write(configfile)

                print(f"Config file at {self.config_file} updated with version {self.__version__}.")
                logging.info(f"Config file at {self.config_file} updated with version {self.__version__}.")
        
        except (configparser.Error, IOError) as e:
            print(f"An error occurred while accessing the config file: {e}")
            logging.info(f"An error occurred while accessing the config file: {e}")
            return None
        
    def check_version(self)
        config = configparser.ConfigParser()
        config.read(self.config_file)
        return config['config']['version']
                
    def read_ip_address(self):
        config = configparser.ConfigParser()
        try:
            config.read(self.config_file) #Read the existing config file
            return config['config']['ip_address'] # Return the IP address from the config
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
    #laps_fetched_signal = pyqtSignal(str, list, int)
    load_race_on_start_signal = pyqtSignal(list, list)
    score_data_signal = pyqtSignal(object, object, object)
    load_sessionid_on_start_signal = pyqtSignal(object)
    def __init__(self, db_queue):
        super().__init__()
        self.db_queue = db_queue
        self.running = True

    def run(self):
        self.conn = sqlite3.connect('RaceDB.db')
        self.cursor = self.conn.cursor()
        self.create_database()
        #logging.info(f"Create DB Thread ID in operation: {threading.get_ident()}")
        #print(f"Create DB Thread ID in operation: {threading.get_ident()}")
        while self.running:
            try:
                operation, args = self.db_queue.get()
                #print(f"Operation: {operation} Args: {args}")
                logging.info(f"Operation: {operation} Args: {args}")
                print(f"DB Queue Called: {operation} ")
                if operation == 'stop':
                    break
                if operation == 'write_race': self.write_race(*args)
                elif operation == 'insert_lap_data': self.insert_lap_data(*args)
                elif operation == 'finalize_race': self.finalize_race(*args)
                elif operation == 'delete_race': self.delete_race(*args)
                elif operation == 'get_latest_race_id': self.get_latest_race_id(*args)
                elif operation == 'get_latest_session_id': self.get_latest_session_id(*args)
                elif operation == 'load_selected_race': self.load_selected_race(*args)
                elif operation == 'load_race_data_on_start': self.load_race_data_on_start(*args)
                elif operation =='load_sessionid_on_start': self.load_sessionid_on_start(*args)
                elif operation == 'get_score_data': self.get_score_data(*args)
                elif operation == 'delete_db': self.delete_db()

            except Exception as e:
                logging.error(f"DB Unpack failed:Operation: {operation} Message: {e}")
                #print(f"Unpack failed:Operation: {operation} Message: {e}")
            finally:
                self.db_queue.task_done()
        # Close the connection when the thread stops
        self.conn.close()
        
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
                Phone INTEGER PRIMARY KEY,
                Name TEXT UNIQUE,
                RaceDate TEXT DEFAULT (date('now'))
            )
        ''')
        self.cursor.execute('''
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
        self.conn.commit()

    def delete_db(self):
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';") # Fetch all table names in the database
        tables = self.cursor.fetchall()
        for table in tables: # Drop all tables
            self.cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
            print(f"Table {table[0]} deleted.")
            logging.info(f"Table {table[0]} deleted.")
            self.create_database()
            self.conn.commit()

    def get_score_data(self,session_id):
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
                self.score_data_signal.emit(None)
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
                self.score_data_signal.emit(None)
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

    def load_race_data_on_start(self,callback=None):    
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
                self.load_sessionid_on_start_signal.emit([])
        except Exception as e:
            logging.error(f"DB Load_session_id_on_start failed: {e}")
            print(f"DB Load_session_id_on_start failed: {e}")
            self.load_sessionid_on_start_signal.emit([])
        
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
                    SELECT mName, mRacePosition, mFastestLapTimes, mLastLapTimes, mCarNames, flags
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
            logging.info(f"DB Session ID result: {session_id}")
            if session_id:
                if callback:
                    logging.info("DB Invoking callback with session_id")
                    callback(session_id)
            else:
                if callback:
                    print("DB No Session ID. Invoking callback with session_id None")
                    logging.info("DB No Session ID. Invoking callback with session_id None")
                    callback(None)        
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Database operation get_latest_session_id failed: {e}")
            if callback:
                callback(None)
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
                    print(f"No Callback, returning Race_id: {last_race_id}")
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
            ''', (track_info, data['eventInformation']['mLapsInEvent'], session_id))         
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
            
    def insert_lap_data(self, race_id, participant_name, current_lap, lap_time):
        try:
            logging.info(f"DB Def insert lap data entered, data to be written:Race_id:{race_id}, p_name:{participant_name}, lap:{current_lap}, lap time:{lap_time}")
            self.cursor.execute('''
                INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
                VALUES (?, ?, ?, ?)
            ''', (race_id, participant_name, current_lap, lap_time))
            logging.info("DB Lap data written")
            self.conn.commit()
        except Exception as e:
            print(f"Failed to write Lap data to the database: Program Crash! {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            self.conn.close()  # Ensure the connection is closed
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")
            
    def finalize_race(self, data, lap_times_dict, flags_dict):
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
            ranked_drivers = self.calculate_score(participants, lap_times_dict, flags_dict, driver_total_times_dict)
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
                self.cursor.execute('''
                    INSERT OR REPLACE INTO Participants (
                        RaceID, mName, mCarNames, mRacePosition, mFastestLapTimes, mLastLapTimes, mLapsCompleted, flags, TotalTime, CalculatedPosition
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    ranked_drivers.index(participant_name) + 1
                ))
            self.conn.commit()
        except Exception as e:
            print(f"Failed to Finalize race data to the database: {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            self.conn.close()  # Ensure the connection is closed
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")

    def calculate_score(self, participants, laps, flags, driver_total_times):
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
        
class ControlPanel(QThread):
    def __init__(self, db_queue):
        super().__init__()
        self.db_queue = db_queue
        self.running = True
        self.file_path = 'C:\\force\\gui\\score.txt'
        self.best_lap_file_path = 'C:\\force\\gui\\bestlap.txt'
        self.driver_file_path = 'C:\\force\\gui\\drivers.txt'
        self.db_queue = db_queue

    def read_driver_names(file_path):
        with open(file_path, 'r') as f: # Read the driver names from the specified file
            line = f.readline().strip()
            driver_names = line.split(';')
            driver_names = [name.split(' (')[0] for name in driver_names]  # Remove any part after "("
        return driver_names

    def map_scores_to_drivers(driver_names, race_data):
        driver_scores = {name: 0 for name in driver_names} # Map the race positions to the driver names
        for participant in race_data['participants']['mParticipantInfo']:
            driver_name = participant['mName'].split(' (')[0]  # Remove any part after "("
            if driver_name in driver_scores:
                driver_scores[driver_name] = participant['mRacePosition']
        return driver_scores

    def write_race_results(driver_scores, file_path):
        line = ';'.join(str(driver_scores[name]) for name in driver_scores) + ';' # Write the race results to the specified file
        os.makedirs(os.path.dirname(file_path), exist_ok=True) # Ensure the directory exists
        with open(file_path, 'a') as f: # Append the results to the file
            f.write(line + '\n')
        print("Race results written to file.")

    def write_best_lap_driver(best_driver, file_path):
        if best_driver: # Write the best lap driver to the specified file
            with open(file_path, 'a') as f:
                f.write(best_driver + '\n')
            print(f"Best lap driver {best_driver} written to file.")
        else:
            print("No valid best lap driver found.")

    def stop(self):
        self.running = False
        self.session.close()
        self.quit()
        self.wait()      
class api_data(QThread):
    def __init__(self,api_queue):
        super().__init__()
        self.api_queue = api_queue
        self.ip_address = self.config_manager.read_ip_address()   #threading.Thread.__init__(self)
        self.previous_game_state = None
        self.previous_race_state = None
        self.running = True
        
    def run(self):

        while self.running:
            try:
                operation, args = self.api_queue.get()
                #print(f"Operation: {operation} Args: {args}")
                logging.info(f"API Operation: {operation} Args: {args}")
                print(f"API Queue Called: {operation} ")
                if operation == 'stop':
                    break
                if operation == 'get_api_data': self.get_api_data(*args)

            except Exception as e:
                logging.error(f"DB Unpack failed:Operation: {operation} Message: {e}")
                #print(f"Unpack failed:Operation: {operation} Message: {e}")
            finally:
                self.api_queue.task_done()       
    def get_api_data(self, callback = None):
        error_massage_shown = False
        self.no_server_connection = True
        while self.no_server_connection:
            self.ip_address = self.config_manager.read_ip_address()  # Read IP address before each API call
            previous_ipaddress = self.ip_address
            if previous_ipaddress != self.ip_address:
                print(f"MT Ipadress changed, new ipadress {self.ip_address}")
                logging.info(f"MT Ipadress changed, new ipadress {self.ip_address}")
            try:
                with self.session.get(f'http://{self.ip_address}:8180/crest2/v1/api') as response:
                    data = response.json() 
                    if response.status_code == 200: #Ensure the response content is valid JSON
                        try:
                            data = response.json()
                            if data is None:
                                raise ValueError("MT Received None as data. Possible issue with API response.")
                            else:
                                self.no_server_connection = False
                                self.connection_restored.emit() # Emit signal for successful connection restoration to clear the error message
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
                                return data  # return the data if the response is valid
                        except ValueError as ve:
                            if not error_massage_shown:
                                logging.error(f"MT Error parsing JSON response: {ve}")
                                print(f"MT Error parsing JSON response: {ve}")
                                error_massage_shown = True
                            time.sleep(5)  # Wait for 5 seconds before fetching the next data
                            continue  # Skip this loop iteration and try again
                    else:
                        if not error_massage_shown:
                            logging.error(f"Unexpected status code {response.status_code} received from the API.")
                            print(f"MT Unexpected status code {response.status_code} received from the API.")
                            self.error_occurred.emit(f'Game Not Started: {str(e)}')
                            error_massage_shown = True
                        self.no_server_connection = True
                        time.sleep(5)  # Wait for 5 seconds before fetching the next data
                        continue  # Skip this loop iteration and try again

            except requests.exceptions.ConnectionError:
                if not error_massage_shown:
                    logging.error(f"MT Connection error: Unable to reach the server at {self.ip_address}. Retrying in 2 seconds.")
                    print(f"MT Connection error: Unable to reach the server at {self.ip_address}. Retrying in 2 seconds.")
                    self.error_occurred.emit('Connection Error: Unable to reach server')
                    error_massage_shown = True
                self.no_server_connection = True
                time.sleep(2)
                
            except requests.exceptions.Timeout:
                if not error_massage_shown:
                    logging.error(f"MT Timeout error: The server at {self.ip_address} did not respond. Retrying in 2 seconds.")
                    print(f"MT Timeout error: The server at {self.ip_address} did not respond. Retrying in 2 seconds.")
                    self.error_occurred.emit('Timeout Error: Server did not respond')
                    error_massage_shown = True
                self.no_server_connection = True
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                if not error_massage_shown:
                    logging.error(f"Request error: An error occurred - {str(e)}. Retrying in 2 seconds.")
                    print(f"MT Request error: An error occurred - {str(e)}. Retrying in 2 seconds.")
                    self.error_occurred.emit(f'Request Error: {str(e)}')
                    error_massage_shown = True
                self.no_server_connection = True
                time.sleep(2)
                
    def stop(self):
        self.running = False
        self.session.close()
        self.quit()
        self.wait()

        
class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal()
    flags_updated = pyqtSignal(dict)
    initialize = pyqtSignal()
    error_occurred = pyqtSignal(str)   # New signal for errors
    connection_restored = pyqtSignal()  # Signal to clear error message
    
    def __init__(self, race_monitor_app, tab_widget ,db_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager()
        self.update_config_file = self.config_manager.update_config_file()
        self.ip_address = self.config_manager.read_ip_address()   #threading.Thread.__init__(self)   
        self.race_monitor_app = race_monitor_app
        self.db_queue = db_queue
        self.tab_widget = tab_widget  # Store the reference to tab_widget
        self.previous_game_state = None
        self.previous_race_state = None
        self.viewing_race_id = None
        self.running = True
        self.first_time_run = True
        self.session = requests.Session()
        self.race_id = 0
        self.race_may_not_be_finished = False
        self.session_id = 0
        
        #Signalling
        self.race_monitor_app.session_id_updated.connect(self.set_session_id) # Connect the signal to a slot that updates Session ID
      
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
               
    def race_running(self, data):
        self.data_updated.emit(data)
        lap_times_dict = {} # Clear the lap times dictionary ready for next race.
        last_lap_counts = {} # Clear the last lap counts dictionary
        driver_total_times = {} # Clear the driver total times dictionary
        driver_flags ={} # Clear the driver flags dictionary
        QMetaObject.invokeMethod(self.tab_widget, "setCurrentIndex", Qt.QueuedConnection, Q_ARG(int, 0)) #Switch to Score View tab
        print(f"MT Race is STARTING!!!!!!.")
        logging.info(f"MT Race is STARTING!!!!!!.")
        #print(f"MT Data to be written to database: race index: {race_index} Sesson id: {self.session_id}")
        logging.info(f"MT Data to be written to database: race index: {self.race_id} Sesson id: {self.session_id}")
        while self.session_id == 0:
            time.sleep(1)
            print(f"MT Waiting for session ID to be updated. Current session ID: {self.session_id}")
        self.db_queue.put(('write_race', (data, self.session_id)))
        self.db_queue.put(('get_latest_race_id', (self.set_race_id,)))  # Only pass the necessary data, not the function
        while self.race_id == 0:
            time.sleep(1)
            print(f"MT Waiting for race ID to be updated. Current Race ID: {self.race_id}")
        print(f"MT Race written to database., asked for race ID: {self.race_id}, entering live view loop.")
        logging.info(f"MT Race written to database., asked for race ID: {self.race_id}, entering live view loop.")        
        while self.running: #loop while race is running
            try:
                if self.race_loop_first_time: logging.info(f"MT RaceID is: {self.race_id}.")
                previous_data = data # Store the previous data
                data = self.get_api_data() # Get API Data
                participants = data.get('participants', {}).get('mParticipantInfo', [])  # Proceed with processing the valid data 
                if not participants or all(participant.get('mCurrentLap', 0) > data['eventInformation']['mLapsInEvent'] for participant in participants):  # Check if all participants have completed every lap or if there is data.
                    if not participants:                                                       
                        data = previous_data # Revert to the previous data if no participants are found
                        logging.info(f"MT No participants found , Race is over. Break loop")
                        print(f"MT No participants found, Race is over.")
                        break # Race is over, break the loop
                    else:                              
                        logging.info(f"MT All participants finished, Race is over,Sending Data one last time, breaking the loop")
                        print(f"MT All participants finished race, Race is over. Sending Data one last time.")
                        self.race_may_not_be_finished = True
                        break # Race is over, break the loop
                self.data_updated.emit(data) #Send the data to Live view 
                           
                for participant in participants:
                    if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                    if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0   
                    if (participant.get('mCurrentLap', 0) > last_lap_counts.get(participant['mName'], 1)) and (participant.get('mLastLapTimes') != -123):
                        if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                        if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0                                    
                        driver_total_times[participant['mName']] += participant.get('mLastLapTimes', 0)
                        self.db_queue.put(('insert_lap_data', (self.race_id, participant['mName'], participant.get('mCurrentLap', 0) - 1,participant.get('mLastLapTimes')))) #insert lap into Table
                        lap_times_dict[participant['mName']].append(participant.get('mLastLapTimes', None))
                        logging.info(f"MT Storing lap time for {participant['mName']}: Lap {participant.get('mCurrentLap', 0)}, Time {participant.get('mLastLapTimes', 0)},Last Lap:{participant.get('mLastLapTimes', None)} Driver Total Time: {driver_total_times[participant['mName']]} ")
                    else:
                        if (participant.get('mSpeeds',0) >10) and (data['gameStates']['mRaceState'] == 1) and (driver_flags.get(participant['mName'],None) != 'Falsestart'):
                            print(f"MT Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            logging.info(f"MT Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            driver_flags[participant['mName']] = 'Falsestart'
                            self.flags_updated.emit(driver_flags)
                    last_lap_counts[participant['mName']] = participant.get('mCurrentLap', 0)
                self.race_loop_first_time = False
            except Exception as e:
                logging.error(f"An error occurred while processing participant data: {e}")
                print(f"MT An error occurred while processing participant data: {e}")
                raise
        logging.info(f"MT Race Race_{self.race_id} has ended.")
        print(f"MT Race Ended Finalizing Race for: Race_{self.race_id}")
        logging.info(f"MT Race Ended Finalizing Race for: Race_{self.race_id}")
        participants = data.get('participants', {}).get('mParticipantInfo', [])
        logging.info(f"MT Driver Total times: {driver_total_times}")
                    
        if not driver_total_times:
            print(f"MT No reason to write race, no one finished, no driver_total_times.")
            logging.info(f"MT No reason to write race, no one finished, no driver_total_times.")
            self.race_may_not_be_finished = True
            self.first_time_run = True
            self.race_finished.emit() # no reason to write the race, no one finished
        else:
            try:
                for participant in participants:
                    participant_name = participant['mName']
                    logging.info(f"MT Participant: {participant['mName']}, Race Position: {participant.get('mRacePosition', 0)}")
                    participant_name = participant['mName']
                    if participant['mCurrentLap'] <= data['eventInformation']['mLapsInEvent']: # Driver has fewer laps less than he should, either False start Or DNF
                        print(f"MT Participant: {participant_name}, Flags: {driver_flags}")
                        logging.info(f"MT Participant: {participant_name}, Flags: {driver_flags}")
                        if driver_flags.get(participant_name) != 'Falsestart': # Check if the participant has a 'Falsestart' flag
                            print(f"MT Adding DNF to Flags for {participant_name}")
                            logging.info(f"MT Adding DNF to Flags for {participant_name}")
                            driver_flags[participant_name] = 'DNF'
                            self.flags_updated.emit(driver_flags)
                            time.sleep(1)
                self.db_queue.put(('finalize_race', (data, lap_times_dict,driver_flags)))
                self.data_updated.emit(data) #Send the data to Live view to update the flags
                self.first_time_run = True
                self.race_finished.emit()
            except Exception as e:
                logging.error(f"An error occurred while finalizing race: {e}")
                print(f"MT An error occurred while finalizing race: {e}")
                time.sleep(5)
                
    def run(self):
        while self.running:
            try:
                if self.first_time_run and not self.race_may_not_be_finished:
                    self.initialize.emit() #Load selected race after start.
                    logging.info("Dropdowns initialized")
                time.sleep(5)  # Wait for 5 seconds before fetching the next data
                data = self.get_api_data()
                participants = data.get('participants', {}).get('mParticipantInfo', []) # Fetch participants data    
                if not participants and self.first_time_run and not self.race_may_not_be_finished:
                    self.first_time_run = False
                    logging.info(f"MT No participants found, Still waiting for race start.")
                    print(f"MT Waiting for race start.....")
                    time.sleep(5) # Wait for some time before retrying
                    continue  # Restart loop if participants list is empty
                if self.race_may_not_be_finished and participants:
                    print("Race not finished yet.")
                    continue
                else:
                    if self.race_may_not_be_finished:
                        print("Race Finished!")
                        self.race_may_not_be_finished = False
                if participants:
                    self.race_loop_first_time = True
                    self.race_running(data)
                    
            except Exception as e:
                logging.error(f"An error occurred while monitoring race state: {e}")
                print(f"MT An error occurred while monitoring race state: {e}")
                time.sleep(5)
    
    def stop(self):
        self.running = False
        self.session.close()
        self.quit()
        self.wait()

class RaceMonitorApp(QMainWindow):
    session_id_updated = pyqtSignal(int)  # Signal to update the SessionID
    delete_db = pyqtSignal()  # Signal to delete the database
    def __init__(self):
        super().__init__()
         # Define all image paths using resource_path
        liverace_liveview_img_path = resource_path('LiveRace_LiveView.jpg')
        liverace_status_img_path = resource_path('LiveRace_Status')
        icon_path = resource_path('RockyTM.ico') # Set the window icon
        self.setWindowIcon(QIcon(icon_path))
        # Initialize QPixmap objects for each image
        self.live_background_image = QPixmap(liverace_liveview_img_path)  # Background for Live view
        self.live_status_image = QPixmap(liverace_status_img_path)
        self.db_queue = queue.Queue()
        self.api_queue = queue.Queue()
        self.api_thread = api_data(self.api_queue)
        self.db_thread = DatabaseThread(self.db_queue)
        self.api_thread.start()
        self.db_thread.start()
        self.setWindowTitle("Live Race Data")
        self.setGeometry(100, 100, 1400, 900)
        self.setFixedSize(1400, 900) # Set fixed size to prevent autoresizing
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Fully transparent
        self.labels = {}
        self.session_id = None
        self.live_first_time_run =True
        self.session_id_dropdown = None
        self.racestarted = False
 
        #Get DB values
        self.db_queue.put(('get_latest_session_id', (self.set_session_id,)))
        
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
        background-position: center;
        background-repeat: no-repeat;
        """)

        self.tab_widget = QTabWidget(self.central_widget)
        self.monitor_thread = MonitorThread(self, self.tab_widget, self.db_queue)
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.flags_updated.connect(self.update_flags)
        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.initialize.connect(self.initialize_dropdown)
        self.monitor_thread.error_occurred.connect(self.show_error_message)  # Connect the error signal
        self.monitor_thread.connection_restored.connect(self.handle_connection_restored)  # Connection restored
        self.db_thread.load_race_on_start_signal.connect(self.handle_race_data_on_start) # Get data to populate select races dropdown
        self.db_thread.load_sessionid_on_start_signal.connect(self.handle_sessionid_data) # Get data to populate session ID dropdown
        self.db_thread.race_data_loaded_signal.connect(self.on_race_loaded)  # queue.put already directs this to the correct function
        self.db_thread.score_data_signal.connect(self.calculate_score) # Connect the signal to the slot that sends score data
        self.monitor_thread.start()

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
        # Set up layouts for each tab
        self.live_view_layout = QVBoxLayout(self.live_view_widget)
        self.results_view_layout = QVBoxLayout(self.results_view_widget)
        self.final_view_layout = QVBoxLayout(self.final_view_widget)
        #self.live_view_layout.setAlignment(Qt.AlignTop)
        #self.live_view_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Add live view and results view to the tab widget and give the tabs a name
        self.tab_widget.addTab(self.live_view_widget, "Live Race Data")
        self.tab_widget.addTab(self.results_view_widget, "Previous Races")
        self.tab_widget.addTab(self.final_view_widget, "Accumulated Score")
        
        # Add your existing widgets and layout configurations to the appropriate tab layouts
        self.setup_live_view() # Initialize the live view
        self.setup_final_view() # Initialize the final view
        self.setup_result_view() # Initialize the result view
        self.tab_widget.setCurrentIndex(1) #Set the Status view as the default tab

        # Connect tab change to background update
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        # Load the background image
        self.status_background_image = QPixmap(liverace_status_img_path)  # Background for Status view
        self.live_background_image = QPixmap(liverace_liveview_img_path)  # Background for Live view

        # Create a QLabel to display the background image
        self.background_label = QLabel(self.central_widget)
        self.background_label.setPixmap(self.status_background_image)
        self.background_label.setGeometry(0, 0, 1400, 900)
        self.background_label.setScaledContents(True)  # Adjusts the image size to the window
        self.background_label.lower()  # Ensure the background stays behind other widgets
        self.layout.setAlignment(Qt.AlignTop)
        
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
        self.dropdown.currentIndexChanged.connect(self.load_selected_race)
        self.layout.addWidget(self.dropdown, alignment=Qt.AlignTop)
         # Add a spacer below the dropdown to push it up
        #self.layout.addSpacerItem(QSpacerItem(1, 1, QSizePolicy.Minimum, QSizePolicy.Expanding))
        #self.layout.addSpacing(40)  # Adjust the value as needed
        self.layout.addSpacing(10) 
        #Add Dropdown for selecting Sessions
        self.dropdown_sessionid = QComboBox(self)
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
        self.dropdown_sessionid.currentIndexChanged.connect(self.display_score)
        self.layout.addWidget(self.dropdown_sessionid, alignment=Qt.AlignTop) 

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

        # Add the Delete DB button
        self.delete_all_button = QPushButton("Delete All Data", self)
        self.labels['delete_all_button'] = self.delete_all_button
        self.delete_all_button.setStyleSheet("""
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
        self.delete_all_button.setFixedSize(150, 30)
        self.delete_all_button.clicked.connect(self.delete_db)
        self.layout.addWidget(self.delete_all_button)

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
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
        self.layout.addWidget(self.status_label)  # Add the status label below the delete button
        self.tab_widget_mapping = {  # Widget visibility mapping for each tab
            0: [],  # Widgets for Live View
            1: ['dropdown', 'delete_button', 'delete_all_button' ],  # Widgets for Results View
            2: ['new_session_button', 'dropdown_sessionid', 'previous_session_button' ],  # Widgets for Score View
        }        

        self.status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);") # Call the function to load race data
        #Set the Status view as the default tab
        self.tab_widget.setCurrentIndex(2)
        self.tab_widget.setCurrentIndex(1)
    
    def delete_db(self):
        logging.info("RMA Delete DB def entered")
        self.set_delete_db_mode(True)
        self.db_queue.put(('delete_db', ()))
        time.sleep(5)
        self.initialize_dropdown()
        self.set_delete_db_mode(False)
        
    def update_flags(self, flags):
        logging.info("RMA Flags updated def entered")
        #print("RMA Flags updated def entered")
        self.driver_flags=flags # Update the flags label with the message
        
    def initialize_dropdown(self):
        logging.info("RMA Initialize Dropdown def entered")
        #print("RMA Initialize Dropdown def entered")
        self.db_queue.put(('load_race_data_on_start',())) #Send the request to the DatabaseThread to load race data on start
        self.db_queue.put(('load_sessionid_on_start',())) 

    def set_session_id(self, new_session_id):
        logging.info("RMA Def set_session_id entered")
        if new_session_id is None:
            print(f"Session ID not found in the database, setting to 1")
            logging.info(f"RMA Session ID not found in the database, setting to 1")
            self.session_id = 1
            self.session_id_updated.emit(self.session_id)
        else:
            print(f"Session ID fetched: ({new_session_id})")
            logging.info(f"RMA Session ID fetched: ({new_session_id})")
            self.session_id = new_session_id
            self.session_id_updated.emit(self.session_id)
        #self.final_heading.setText(f"Accumulated Score for Session: {self.session_id}")
            
    def handle_race_data_on_start(self, races, participants):
        logging.info("RMA Def handle race data on start entered")
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
        else: self.results_content.setText("Select a Race to View previous results") 
            
        
    def load_selected_race(self): # Function to be called when the data is loaded
        #print("Load Selected race def entered")
        logging.info("RMA Load Selected race def entered")
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            match = re.search(r"Race_(\d+)", race_text)
            race_id = int(match.group(1))  # The number after "Race_"
            #print(f"Selected race: {race_id} from {race_text}")
            self.viewing_race_id = None  # Reset viewing_race_id before loading
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
        if race_id:
            self.viewing_race_id = race_id  # Set the viewing_race_id with the loaded race_id
            logging.info(f"RMA Load Selected Race, RaceID: {self.viewing_race_id}")
            #print(f"Load Selected Race, RaceID: {self.viewing_race_id}")
                
            displayed_participants = set()
            car_name = participants[0][4] if participants and participants[0][4] else "Unknown Car"
            loaded_results = (f"<span style='font-weight:bold;'>Race No: {race_id} "
                                f"Track: {track_variation} Laps: {laps_in_event} "
                                f"Car: {car_name} session_id: {session_id}:</span><br>")

            for participant in participants:
                name, race_position, fastest_lap, last_lap, car, flags = participant
                participant_laps = [lap for lap in laps if lap[2] == name]
                if participant_laps:  # Check if the list is not empty
                    best_lap_time = min(lap[4] for lap in participant_laps)  # Find the best (minimum) lap time

                    lap_times_str = ", ".join(
                        f"<span style='font-weight:bold; color:#1e8449;'>{int(lap[4] // 60)}:{lap[4] % 60:05.2f}</span>" 
                        if lap[4] == best_lap_time 
                        else f"{int(lap[4] // 60)}:{lap[4] % 60:05.2f}"
                        for lap in participant_laps
                    )
                else:
                    lap_times_str = "No laps recorded"  # Or handle as appropriate
                total_time_seconds = sum(lap[4] for lap in participant_laps)
                total_time_str = self.format_lap_time(total_time_seconds)
                   
                if name in displayed_participants:
                    continue  # Skip duplicate participant names

                # Add participant info to the result string
                loaded_results += (
                f"<span style='font-weight:bold;'>{race_position}: {name} -  </span>"
                f"Flag: <span style='font-weight:normal; color:#78281f;'>{participant[5]}</span> - "
                f"<span style='font-weight:bold;'>Total: <span style='font-weight:bold; color:#2e86c1;'>{total_time_str}</span> - " 
                f"<span style='font-weight:bold;'>Laps: <span style='font-weight:normal; color:#1e8449;'></span>"
                f"<span style='font-weight:normal; color:#1e8449;'>[{lap_times_str}]<br></span>"
                )
                displayed_participants.add(name)

            self.results_content.setTextFormat(Qt.RichText)
            self.results_content.setText(loaded_results)  # Update the UI with the loaded results
            #self.display_score()
            
    def handle_sessionid_data(self, sessionids):
        logging.info("RMA Def handle sessionid data entered")
        self.dropdown_sessionid.clear()  # Add this line to clear the dropdown
        self.sessionids = sessionids
        if sessionids:
            self.final_content.setText("Select a Session to View Accumulated Score")
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
        elif index == 1: self.update_background('status')

    def update_background(self, view):
        logging.info("RMA Def update_background entered")
        if view == 'status': self.background_label.setPixmap(self.status_background_image)
        elif view == 'live': self.background_label.setPixmap(self.live_background_image)

    def clear_error_message(self):
        #logging.info("RMA Def clear_error_message entered")
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()

    def handle_connection_restored(self):
        #logging.info("RMA Def handle_connection_restored entered")
        self.clear_error_message() # Clear the error message immediately upon restoring the connection
        
    def update_status_message(self, message):
        logging.info("RMA Def update_status_message entered")
        self.status_label.setText(message) # Update the status label with the message

    def blink_status_message(self):
        logging.info("RMA Def blink_status_message entered")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_status_visibility)
        self.timer.start(500)  # Blink every 500 ms

    def toggle_status_visibility(self):
        logging.info("RMA Def toggle_status_visibility entered")
        if self.status_label.isVisible(): self.status_label.setVisible(False)
        else: self.status_label.setVisible(True)
   
    def show_error_message(self, message): # Check if the error label already exists with the same message
        logging.info("RMA Def show_error_message entered")
        if hasattr(self, 'error_label') and self.error_label.text() == message: return  # Do not create a new label if the message is the same
        if hasattr(self, 'error_label'): self.error_label.deleteLater()  # Remove the existing error label
           
        # Create the error label with the new message
        self.error_label = QLabel(message, self)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setFixedSize(1060, 35)
        self.error_label.setStyleSheet("font-size: 18px; color: red; background-color: yellow; padding: 10px;")
        self.blink_error_message()

    def blink_error_message(self):
        logging.info("RMA Def blink_error_message entered")
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_error_visibility)
        self.timer.start(500)  # Blink every 500 ms

    def toggle_error_visibility(self):
        if hasattr(self, 'error_label') and self.error_label is not None:
            if self.error_label.isVisible(): self.error_label.setVisible(False)
            else: self.error_label.setVisible(True)

    def setup_live_view(self): # Setup your live view widgets here
        logging.info("RMA Def setup_live_view entered")
        self.live_heading = QLabel(f"Waiting for a new race to start...Current Session: {self.session_id}", self.live_view_widget)
        self.live_heading.setStyleSheet("font-size: 16px;font-weight:bold; color: black;")
        self.live_view_layout.addWidget(self.live_heading, alignment=Qt.AlignTop)
        self.live_heading.setMinimumSize(200, 50)  # Set this to a size that you believe should fit your text
        # Add Race Status label for live updates
        self.live_status_label = QLabel("Race Messages here", self.live_view_widget)
        self.live_status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
        self.live_view_layout.addWidget(self.live_status_label, alignment=Qt.AlignTop)  # Add the status label below Heading
        #self.live_status_label.hide()  # Hide the status label initially
        self.live_status_label.setMinimumSize(200, 50)  # Set this to a size that you believe should fit your text
        # Add participant labels for live updates
        self.participant_labels = {}
        for i in range(20):  # Assuming 20 participants max
            self.participant_labels[i] = QLabel("", self.live_view_widget)
            self.live_view_layout.addWidget(self.participant_labels[i])
            self.participant_labels[i].hide()  # Hide labels initially
        # You can add other live view specific components here as per the original design.

    def setup_result_view(self): # Content label for displaying loaded results
        logging.info("RMA Def setup_result_view entered")
        self.results_content = QLabel("No race data available", self.results_view_widget)
        self.results_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        self.results_view_layout.addWidget(self.results_content)
        self.results_view_layout.addStretch(1)
        
    def setup_final_view(self): # Content label for displaying Final results
        logging.info("RMA Def setup_final_view entered")
        
        self.final_heading = QLabel(f"Session: {self.session_id}", self.final_view_widget)
        self.final_heading.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        self.final_view_layout.addWidget(self.final_heading)

        self.final_content = QLabel("No race data available", self.final_view_widget)
        self.final_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        self.final_view_layout.addWidget(self.final_content)
        self.final_view_layout.addStretch(1)
       
    def on_first_live_view_run(self, data):
        logging.info("RMA Def on_first_live_view_run entered")
        print("First Live View Run")
        self.event_info = data['eventInformation'] # Extract event information and participant details from the data
        participants = data['participants']['mParticipantInfo']
        if len(self.sessionids) < 1:
            self.final_content.setText("Score - Waiting for a new race to finish...")
        self.current_lap = {}
        self.previous_current_lap = {}
        self.current_bestlap_name = None
        self.previous_best_lap_time = None
        self.best_lap_time = None
        self.lap_time ={}
        self.lap_list = {}
        self.total_time_seconds = {}
        self.driver_flags = {}
        heading_text = f"{self.event_info['mTranslatedTrackLocation']} - {self.event_info['mTranslatedTrackVariation']} ({self.event_info['mLapsInEvent']}) - {participants[0]['mCarNames']} -  {len(participants)} Drivers - Session ID: {self.session_id}  " # Update the heading with track variation and car names
        self.live_heading.setText(heading_text)
        self.live_status_label.setText("Waiting for Green Light...")  # Update the status label"
        self.new_session_button.hide()
        self.previous_session_button.hide()
        self.racestarted = True
        self.background_color = "#333333"  # Default background color
        self.top_background_color = "#A7DB8D"  # Default top background color
        self.race_started = False
        self.session_id_updated.emit(self.session_id)
        
    def update_live_view(self, data):
        if self.live_first_time_run: 
            self.on_first_live_view_run(data)
        participants = data['participants']['mParticipantInfo']
        #sorted_participants = sorted(participants[:data['participants']['mNumParticipants']], key=lambda p: p['mRacePosition']) # Sort participants by race position
        sorted_participants = sorted(
            participants[:data['participants']['mNumParticipants']],
            key=lambda p: (
                float('inf') if self.driver_flags.get(p['mName']) == 'Falsestart' else p['mRacePosition']
            )
        )


        if data['gameStates']['mRaceState'] == 2 and not self.race_started:
            self.live_status_label.setText("Green Light! GO GO GO")
            self.race_started = True
        else:    
            if data['gameStates']['mRaceState'] == 3 or data['gameStates']['mRaceState'] == 6:
                self.live_status_label.setText("Race Ending....")  # Update the status label"self.live_status_label.setText
        valid_lap_times = [p['mFastestLapTimes'] for p in sorted_participants if p['mFastestLapTimes'] != -123] # Find the valid Lap Times
        if valid_lap_times:
            self.previous_best_lap_time = self.best_lap_time
            self.best_lap_time = min((time for time in valid_lap_times if time is not None), default=None)

        for i, participant in enumerate(sorted_participants): 
            self.current_lap[participant['mName']] = participant['mCurrentLap'] # Loop through each participant to update their corresponding label
    
            if participant['mLastLapTimes'] != -123 and participant['mName'] in self.previous_current_lap:
                if self.current_lap[participant['mName']] != self.previous_current_lap.get(participant['mName'], None):
                    self.lap_time[participant['mName']] = participant['mLastLapTimes']
                    if participant['mName'] not in self.lap_list:
                        self.lap_list[participant['mName']] = [self.format_lap_time(self.lap_time[participant['mName']])]
                        self.total_time_seconds[participant['mName']] = self.lap_time[participant['mName']]
                    else:
                        self.lap_list[participant['mName']].append(self.format_lap_time(self.lap_time[participant['mName']]))
                        self.total_time_seconds[participant['mName']] += self.lap_time[participant['mName']]
                    self.previous_current_lap[participant['mName']] = self.current_lap[participant['mName']]
            else:
                self.previous_current_lap[participant['mName']] = 1
                
            if participant['mName'] in self.lap_list: lap_times_str = ", ".join(self.lap_list[participant['mName']])
            else: lap_times_str = "No Valid Lap!"
            last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
            fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])
            if participant['mName'] in self.total_time_seconds: total_time_str = self.format_lap_time(self.total_time_seconds[participant['mName']])
            else: total_time_str = "No Valid Lap!"
            flag = self.driver_flags.get(participant['mName'], None) # Check if the participant has a flag in self.driver_flags
            if not flag: flag = "" # If the participant has no flag, set it to an empty string
            label = self.participant_labels[i]
            label.setStyleSheet(f"font-size: 14px; background-color: {self.background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;") # set default background color
            participant_text = self.create_participant_text(participant,flag, last_lap_str, fastest_lap_str, lap_times_str, total_time_str) # Create the participant text using the utility function
            if self.live_first_time_run: label.show()  # Sets all labels to the default background color if no valid lap times are found and it is first run.                   
            if participant['mFastestLapTimes'] == self.best_lap_time: #sets the best lap time participant to a different color
                label.setStyleSheet(f"font-size: 14px; background-color: {self.top_background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                if self.previous_best_lap_time != self.best_lap_time: 
                    print(f"New best Lap Time: {self.format_lap_time(self.best_lap_time)}")
                    self.live_status_label.setText(f"Best time: {participant['mName']} Best Lap in race: {self.format_lap_time(self.best_lap_time)}")
            label.setText(participant_text)  # Update the existing label with the new participant text and styling
            label.show()  # Make the label visible
        self.live_first_time_run = False
       
    def format_lap_time(self, lap_time): #Helper function to format lap time from seconds to 'MM:SS.ss' format.
        if lap_time is None or lap_time == -123.0:
            return "No Valid Lap!"
        minutes = int(lap_time // 60)
        seconds = lap_time % 60
        return f"{minutes}:{seconds:05.2f}"
    
    def create_participant_text(self, participant,flag, last_lap_str, fastest_lap_str, lap_times_str, total_time_str=""): #Helper function to create participant text with custom styling.self.initialize_dropdown
        if participant['mCurrentLap'] -1 == self.event_info['mLapsInEvent']:
            race_status = "<span style='color:#FF0000;font-weight:bold'>(Finished!)</span>"
        else:
            race_status = ""
        flag_text = f" <span style='color:#FF0000;font-weight:bold'>({flag})</span>" if flag else ""
        return (
        f"<span style='font-weight:bold; color:#FFFFFF;'>{participant['mRacePosition']}</span>: "
        f"<span style='color:#FFFFFF;font-weight:bold'>{participant['mName']} {race_status} {flag_text}</span> - "
        f"<span style='color:#FFFFA0;'>Last Lap: <span style='color:#00FF00;'>{last_lap_str}</span> - "
        f"<span style='color:#FFFFA0;'>Best Lap: <span style='color:#FFD700;'>{fastest_lap_str}</span> - "
        f"<span style='color:#FFFFA0;'>Laptimes: <span style='color:#FFFFFF;'>[{lap_times_str}]</span> - "
        f"<span style='color:#FFFFA0;'>Total Time: <span style='color:#FFFFFF;'>[{total_time_str}]</span>"
        )
    
    def display_final_results(self): # Display the score data in the final view
        logging.info("RMA Def display_final_results entered")
        self.live_status_label.setText("Waiting for a new race to start...")  # Update the status label"
        self.racestarted =False
        #self.initialize_dropdown()
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop() 
        #self.tab_widget.setCurrentIndex(2) #Switch to Final View tab
        self.live_first_time_run =True
        
    def display_score(self):
        logging.info(f"RMA Display Score Result def entered")
        print(f"RMA Display score Result")
        self.selected_index = self.dropdown_sessionid.currentIndex()
        if self.selected_index >= 0:
            sessionid_text = self.dropdown_sessionid.itemText(self.selected_index)
            logging.info(f"RMA Selected Session: {sessionid_text}")
            self.session_id_dropdown = sessionid_text.split(" - ")[-1]       
        # Clear any existing error message if the connection is successful
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive():
          self.timer.stop()
        if self.session_id_dropdown != None:
            logging.info(f"RMA Get score Data. Session ID: {self.session_id_dropdown}")
            self.db_queue.put(('get_score_data', self.session_id_dropdown,)) #Get data I need to calculate score (New Session ID button must not be pushed before this))
        self.final_heading.setText(f"Accumulated Score for Session {self.session_id_dropdown} Next Race will be session: {self.session_id}")
        logging.info(f"RMA Accumulated Score for Session {self.session_id_dropdown}")
        
    def calculate_score(self, races, participants, laps):
        logging.info("RMA Def calculate_score entered")
        processed_race_ids = set()  # Add this line at the start of the method
        race_scores = {}  # Dictionary to store the score for each participant in each race
        total_scores = {}  # Dictionary to accumulate total scores for each participant across all races
        race_scores = {}  # Dictionary to store the score for each participant in each race
        last_positions = {}  # To store the last position of each driver
        medal_counts = {'gold': {}, 'silver': {}, 'bronze': {}}  # To count gold, silver, and bronze medals
        # Load the score table from the config file
        config = configparser.ConfigParser()
        config.read('config.ini')
        # Extract scoring rules
        score_table = {int(k.split('_')[0]): int(v) for k, v in config['Score Table'].items() if k != 'best_lap'}
        best_lap_bonus = int(config['Score Table']['best_lap'])
        # Iterate over each race
        for race in races:
            race_id = race[0]  # Assuming race_id is the first element in the race tuple
            processed_race_ids.add(race_id)  # Add this inside the loop that iterates over each race
            race_scores[race_id] = {} # Initialize the race-specific data
            driver_total_times = {} # Dictionary to store the total time for each driver in the
            driver_flags = {} # Dictionary to store the flag for each driver
            best_lap_times = {} # Dictionary to store the best lap time for each driver
            driver_laps_completed = {} # Dictionary to store the number of laps completed by each driver
            driver_race_positions = {} # Dictionary to store the race position for each driver
            # Checking to see if there are any participants in this race
            race_participants = [p for p in participants if p[0] == race_id]
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
                float('inf') if driver_flags.get(x) != "No Flag" else driver_total_times[x]
            )
        )
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

    def format_score_view(self, total_scores, race_count, last_positions, medal_counts, races):
        logging.info("RMA Def format_score_view entered")
        sorted_scores = sorted(total_scores.items(), key=lambda x: x[1], reverse=True) # Sort the drivers by their total score, highest to lowest
        race_ids =  [race[0] for race in races]
        race_ids_str = f"({', '.join(map(str, race_ids))})"
        # HTML table header with images
        header = f'''
        <div style="text-align: Left; font-size: 20px; margin-bottom: 10px;">Number of Races {race_count}</div><div style="text-align: Left; font-size: 15px; margin-bottom: 15px;"> Races:{race_ids_str}</div>   <!-- Center the number of races -->
        '''
        table_header = f'''  
        <table style="text-align: left; background-image: url('table_background.png');width:100%; border-spacing: 0 5px;">
            <tr>
                <th style="padding-right: 10px;">Place</th>
                <th style="padding-left: 70px;padding-right: 79px;">Name</th>
                <th style="text-align: center;padding-left: 10px;padding-right: 10px;">Last Pos</th>
                <th style="text-align: center;padding-left: 13px;padding-right: 13px;">Points</th>
                <th style="text-align: center;padding-left: 12px;padding-right: 12px;">G</th>
                <th style="text-align: center;padding-left: 12px;padding-right: 12px;">S</th>
                <th style="text-align: center;padding-left: 12px;padding-right: 12px;">B</th>
            </tr>
        '''
        rows = '' # HTML rows for each driver
        for i, (mName, score) in enumerate(sorted_scores, start=1):
            # Example placeholder for gold, silver, bronze counts (you can adjust this logic)
            last_pos = last_positions.get(mName, 'N/A')
            gold = medal_counts['gold'].get(mName, 0)
            silver = medal_counts['silver'].get(mName, 0)
            bronze = medal_counts['bronze'].get(mName, 0)
            rows += f''' 
                <tr style="text-align: center;">
                <td style="background-image: url('place.png'); text-align: center; vertical-align: middle;">{i}</td>
                <td style="background-image: url('Name.png'); padding-left: 10px; ">{mName}</td>
                <td style="background-image: url('lastplace.png'); text-align: center;">{last_pos}</td>
                <td style="background-image: url('points.png'); text-align: center;">{score}</td>
                <td style="background-image: url('gold.png'); text-align: center;">{gold}</td>
                <td style="background-image: url('silver.png'); text-align: center; ">{silver}</td>
                <td style="background-image: url('bronse.png'); text-align: center;">{bronze}</td>
                </tr>
            '''
        footer = '</table>' # Close the table
        final_score_str = header +table_header + rows + footer # Combine everything into the final score string
        self.final_content.setText(final_score_str) # Update the UI with the formatted scores
        if not self.racestarted:
            self.live_status_label.setText("Score Calculated! for session: " + str(self.session_id))

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
                    if self.viewing_race_id == race_id:
                        self.results_content.setText("Race Deleted")
                        self.viewing_race_id = None
                        self.dropdown.removeItem(selected_index)
                        self.set_delete_mode(False) # Deactivates delete mode
                        #print("Right before initialize_dropdown")
                        self.initialize_dropdown()
                print(f"on_race_deleted:Race_id is None:{race_id}")
                logging.info(f"on_race_deleted:Race_id is None:{race_id}")
            # Send request to DatabaseThread
            self.set_delete_mode(True)  # Activates delete mode
            self.db_queue.put(('delete_race', (race_id, on_race_deleted)))

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

    def set_delete_db_mode(self, is_active):
        logging.info("RMA Def set_delete_db_mode entered")
        if is_active:
            self.delete_button.setText("Deleting DB...")
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
            self.delete_button.setEnabled(False)
        else:
            self.delete_all_button.setText("Delete All Data")
            self.delete_all_button.setStyleSheet("""
                 font-size: 14px;
                 background-color: #a32d2d;
                 color: white;
                 margin-bottom: 5px;                             
                 border: 2px solid black;  /* Change the border color */
                 border-radius: 5px;  /* Optional: rounded corners */
            """)        
            self.delete_all_button.setEnabled(True)   
            
    def start_new_session(self):
        logging.info(f"RMA Start New Session entered")
        self.display_score()
        logging.info("RMA Def start_new_session entered")
        self.session_id += 1
        self.final_heading.setText(f"Accumulated Score for Session {self.session_id_dropdown} Next Race will be session: {self.session_id}")
        logging.info(f"Self selected index: {self.selected_index}")
        self.session_id_updated.emit(self.session_id)
        
    def previous_session(self):
        logging.info("RMA Def go back session entered")
        self.session_id -= 1
        if self.session_id <1: self.session_id = 1
        self.final_heading.setText(f"Accumulated Score for Session {self.session_id_dropdown} Next Race will be session: {self.session_id}")
        print(f"Self selected index: {self.selected_index}")
        self.session_id_updated.emit(self.session_id)

    def closeEvent(self, event):
        print("Closing the application...")
        self.monitor_thread.stop()
        print("Monitor thread stopped.")
        self.db_thread.stop()
        print("Database thread stopped.")
        event.accept()
        
    def stop(self):
        logging.info("Stopping RaceMonitorApp...") # Log the stopping sequence initiation
        if hasattr(self, 'databaseThread') and self.databaseThread.isRunning(): # Stop the database thread if it exists and is running
            logging.info("Stopping DatabaseThread...")
            self.databaseThread.stop()
            self.databaseThread.wait()  # Wait for the thread to finish
        if hasattr(self, 'monitorThread') and self.monitorThread.isRunning(): # Stop the monitor thread if it exists and is running
            logging.info("Stopping MonitorThread...")
            self.monitorThread.stop()
            self.monitorThread.wait()  # Wait for the thread to finish
        self.close()  # Assuming this is a QMainWindow or similar
        logging.info("RaceMonitorApp stopped successfully.") # Log completion of stopping sequence

def main():
    global app
    app = QApplication(sys.argv)
    ex = RaceMonitorApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address