import sys
from timeit import Timer
import requests
import sqlite3
import queue
import threading
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



# Set up logging
if os.path.exists('debug.log'):
    os.remove('debug.log')

logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
#class SignalEmitter(QObject):
#   race_data_loaded_signal = pyqtSignal(int, str, int, list)
#  laps_fetched_signal = pyqtSignal(str, list, int)
class ConfigManager:
    def __init__(self):
        self.config_file = 'config.ini'
        self.__version__ = "1.3.0"
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
            else:
                # Read the existing config file
                config.read(self.config_file)

                # Update the version information
                config['config']['version'] = self.__version__

                with open(self.config_file, 'w') as configfile:
                    config.write(configfile)

                print(f"Config file at {self.config_file} updated with version {self.__version__}.")
        
        except (configparser.Error, IOError) as e:
            print(f"An error occurred while accessing the config file: {e}")
            return None        
    
        
    def read_ip_address(self):
        config = configparser.ConfigParser()

        try:
            #Read the existing config file
            config.read(self.config_file)
            # Return the IP address from the config
            return config['config']['ip_address']
        
        except (configparser.Error, IOError) as e:
            print(f"An error occurred while accessing the config file: {e}")
            return None

    def get_metadata(self):
        return {
            'version': self.__version__,
            'author': self.__author__,
            'email': self.__email__,
            'date': self.__date__,
            'description': self.__description__,
        }
    
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
            SessionID INTEGER
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
            flags TEXT,       
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
            Name TEXT UNIQUE,
            RaceDate TEXT DEFAULT (date('now'))
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
#class DatabaseThread(threading.Thread):
class DatabaseThread(QThread):
    race_data_loaded_signal = pyqtSignal(object, object, object)
    laps_fetched_signal = pyqtSignal(str, list, int)
    load_race_on_start_signal = pyqtSignal(list, list)
    score_data_signal = pyqtSignal(object, object, object)
    load_sessionid_on_start_signal = pyqtSignal(object)
    def __init__(self, db_queue):
        super().__init__()
        #QObject.__init__(self)  # Initialize QObject
        #threading.Thread.__init__(self)  # Initialize threading.Thread
        #self.conn = sqlite3.connect('RaceDB.db')
        #self.cursor = self.conn.cursor()
        #self.signals = SignalEmitter()  # Initialize SignalEmitter instance
        #self.signals.moveToThread(self)  # Move signals to the same thread
        #self.session_id_queue = queue.Queue()
        self.db_queue = db_queue
        self.running = True

    def run(self):
        self.conn = sqlite3.connect('RaceDB.db')
        self.cursor = self.conn.cursor()
        #logging.info(f"Create DB Thread ID in operation: {threading.get_ident()}")
        #print(f"Create DB Thread ID in operation: {threading.get_ident()}")
        while self.running:
            try:
                operation, args = self.db_queue.get()
                #print(f"Operation: {operation} Args: {args}")
                #print(f"Operation: {operation} ")
                if operation == 'stop':
                    break
                if operation == 'write_race':
                    print("DB write Race")
                    self.write_race(*args)
                elif operation == 'insert_lap_data':
                    self.insert_lap_data(*args)
                    #print("DB insert Lap Data")
                elif operation == 'finalize_race':
                    print("DB Finalize Race")
                    self.finalize_race(*args)
                elif operation == 'delete_race':
                    print("DB Delete Race")
                    self.delete_race(*args)
                elif operation == 'get_race_id':
                    print ("DB Get Race ID")
                    self.get_race_id(*args)
                elif operation == 'get_latest_race_id':
                    print ("DB Get latest Race ID")
                    self.get_latest_race_id(*args)                    
                elif operation == 'get_session_id':
                    print ("DB Get Session_id")
                    #session_id = self.initialize_session_id(*args)
                    #self.session_id_queue.put(session_id)
                    self.get_session_id(*args)
                    
                    print ("Initialize Session_id succeeded")
                elif operation == 'get_race_index':
                    print("DB Get Race Index")
                    self.get_race_index(*args)
                    print ("DB Get Race Index succeeded")
                elif operation == 'load_selected_race':
                    print ("DB Load Selected Race")
                    self.load_selected_race(*args)
                elif operation == 'load_race_data_on_start':
                    print ("DB Load race data on start")
                    self.load_race_data_on_start(*args)
                elif operation =='load_sessionid_on_start':
                    print ("DB Load Session ID on start")
                    self.load_sessionid_on_start(*args)
                elif operation == 'fetch_recorded_laps':
                    #print("Fetch Recorded laps")
                    self.fetch_recorded_laps(*args)
                elif operation == 'get_race_id_and_delete':
                    print ("DB Get Race ID and Delete")
                    self.get_race_id_and_delete(*args)
                elif operation == 'get_score_data':
                    print("DB Get Score Data")
                    self.get_score_data(*args)
                elif operation == ('get_number_of_rows'):
                    print("DB Get Number of Rows")
                    self.get_number_of_rows(*args)
          
                # Add more operations as needed
            #except Exception as e:
                #logging.error(f"Unpack failed:Operation: {operation} Message: {e}")
                #print(f"Unpack failed:Operation: {operation} Message: {e}")
            finally:
                self.db_queue.task_done()
        # Close the connection when the thread stops
        self.conn.close()

    def get_number_of_rows(self,race_id, callback=None):
        try:
            self.cursor.execute('SELECT COUNT(*) FROM laps WHERE RaceID = ?',(race_id,))
            rows = self.cursor.fetchone()[0]
            if callback:
                callback(rows)  # Pass the deleted race_id back to the main thread
            else:
                if callback:
                    callback(None)  # No race found

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback:
                callback(None)               
    
    def get_score_data(self,session_id):
        print(f"get_score_data called with session_id: {session_id}")
        try:
            print("Executing race query for get score data ...")
            self.cursor.execute('''
                SELECT *
                FROM Races
                WHERE SessionID = ?
           
           ''', (session_id,))
            
            race_table = self.cursor.fetchall()
            #print(f"Race table: {race_table}")
            race_ids = [race[0] for race in race_table]  # This will give you a list of all race IDs
            # Check if race_ids is empty
            if not race_ids:
                print(f"Race_ids fetched: {race_ids}")  # Debugging output
                self.score_data_signal.emit(None)
                return
            query = '''
                SELECT *
                FROM laps
                WHERE RaceID IN ({})
            '''.format(','.join('?' * len(race_ids)))
            self.cursor.execute(query, race_ids)
            #self.cursor.execute(query, tuple(race_ids))
            laps = self.cursor.fetchall()
            #print(f"Scores fetched: {scores}")  # Debugging output
            if not laps:
                print("No scores found, emitting None.")
                self.score_data_signal.emit(None)
                return
            query = '''
                SELECT *
                FROM participants
                WHERE RaceID IN ({})
            '''.format(','.join('?' * len(race_ids)))
            self.cursor.execute(query, race_ids)
            #self.cursor.execute(query, tuple(race_ids))  # Passing race_ids as a tuple
            participants = self.cursor.fetchall()
            #print(f"Best Laps fetched: {best_laps_list}")  # Debugging output
            if not participants:
                print("No best laps list found, emitting None.")
                self.score_data_signal.emit(None, None, None)
                return
            if laps and race_table and participants:
               print("Emitting score data signal")
               self.score_data_signal.emit(race_table, participants,laps,)
            else:
               self.score_data_signal.emit(None, None, None)
               
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            self.score_data_signal.emit(None, None, None)


    def get_race_id_and_delete(self, race_index, callback):
        try:
            self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
            race = self.cursor.fetchone()
            print(f"Raceid to delete: {race}")
            if race:
                race_id = race[0]
                self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
                self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
                self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
                self.conn.commit()

                if callback:
                    callback(race_id)  # Pass the deleted race_id back to the main thread
            else:
                if callback:
                    callback(None)  # No race found

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback:
                callback(None)
                


    def fetch_recorded_laps(self, participant_name, race_id, current_lap):
        #print("Goint into try")
        #try:
            #self.cursor.execute('SELECT 1')
            #print("Cursor is valid and connected.")
       # except Exception as e:
            #print(f"Cursor test query failed: {e}")
 
        try:
            # Time the database query
            #start_time = time.time()
           # if self.cursor is None:
                #print("Cursor is None. It was not properly initialized.")
            # Perform the database operation to fetch recorded laps
            #print(f"Fetching recorded laps for {participant_name} Race_id: {race_id} Current Lap: {current_lap} [Thread ID: {threading.get_ident()}")
            self.cursor.execute('SELECT LapNumber, LapTime FROM Laps WHERE RaceID = ? AND mName = ?',(race_id, participant_name))
            #print(f"Race ID: {race_id}, Name: {participant_name}")
            #print(f"Query executed in {time.time() - start_time} seconds")
            recorded_laps = self.cursor.fetchall()
            #print(f"Data gotten: {recorded_laps}")
            # Emit the signal with the fetched data
            #print("Emitting recoreded laps signal")
            self.laps_fetched_signal.emit(participant_name, recorded_laps, current_lap)

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            self.laps_fetched_signal.emit(None)  # Pass empty data on error

    def load_race_data_on_start(self,callback=None):
        try:
            self.cursor.execute('''
                SELECT RaceID, RaceIndex, mTranslatedTrackVariation, mLapsInEvent, RaceDate
                FROM Races
                ORDER BY RaceID ASC
            ''')
            races = self.cursor.fetchall()
            
            self.cursor.execute('''
                SELECT RaceID, mCarNames
                FROM Participants
                ORDER BY RaceID ASC
            ''')
            participants = self.cursor.fetchall()

            # Emit the signal with the results in the main thread
            self.load_race_on_start_signal.emit(races,participants)

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Load Race on start failed: {e}")
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
            sessionids = [sessionid[0] for sessionid in sessionids]
            if sessionids:
                #print(f"Session ID fetched: {sessionids}")
                self.load_sessionid_on_start_signal.emit(sessionids)
            # Emit the signal with the results in the main thread
            else:
                print(f"Session ID not fetched: {sessionids}")
                self.load_sessionid_on_start_signal.emit([])
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Load session id  on start failed: {e}")
            self.load_sessionid_on_start_signal.emit([])
                
    def load_selected_race(self, race_index, callback = None):
        #print(f"Race Index:{race_index}")
        try:
            self.cursor.execute('''
                SELECT RaceID, mTranslatedTrackVariation, mLapsInEvent, sessionID
                FROM Races
                WHERE RaceIndex = ?
            ''', (race_index,))
            race = self.cursor.fetchone()
            

            if race:
                
                self.cursor.execute('''
                    SELECT mName, mRacePosition, mFastestLapTimes, mLastLapTimes, mCarNames, flags
                    FROM Participants
                    WHERE RaceID = ?
                    ORDER BY mRacePosition ASC
                ''', (race[0],))
                participants = self.cursor.fetchall()
                
                self.cursor.execute('''
                    SELECT LapID, RaceID, mName, LapNumber, LapTime
                    FROM Laps
                    WHERE RaceID = ?
                ''', (race[0],))
                laps = self.cursor.fetchall()
                                                
                # Call the callback with the fetched data
                #print(f"Sending the signal back!") 
                self.race_data_loaded_signal.emit(race, participants, laps)

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Load Selected Races failed: {e}")
            if callback: callback(None)
            

            
    def get_race_index(self, callback=None):
        try:
            #print("Trying to get race_index and race_id from DB")
        
            # Fetch the last RaceIndex and its corresponding RaceID from the Races table
            self.cursor.execute('SELECT RaceIndex, RaceID FROM Races ORDER BY RaceID DESC LIMIT 1')
            result = self.cursor.fetchone()
        
            if result:
                last_race_index, last_race_id = result
                #print(f"Fetched RaceIndex: {last_race_index}, RaceID: {last_race_id}")
            
                # Extract the numerical part of the RaceIndex (e.g., '54' from 'Race_54')
                last_race_number = int(last_race_index.split('_')[1])
            
                # Check if there are any laps recorded for the last RaceID
                self.cursor.execute('SELECT COUNT(*) FROM Laps WHERE RaceID = ?', (last_race_id,))
                rows_in_race = self.cursor.fetchone()[0]  # This will give the count of laps
                
                # check if there are any participants in the race
                self.cursor.execute('SELECT COUNT(*) FROM Participants WHERE RaceID = ?', (last_race_id,))
                rows_in_participants = self.cursor.fetchone()[0]  # This will give the count of participants

               #delete race if there are not laps or participants
                if rows_in_race == 0 or rows_in_participants == 0:
                    print(f"Raceid to delete: {last_race_id}")
                    if last_race_id:
                        race_id = last_race_id
                        self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
                        self.conn.commit() 
                        print("No laps or participants, race deleted")



                # If a callback is provided and it's callable, process the result
                if callback and callable(callback):
                    if rows_in_race > 0 and rows_in_participants >0:
                        callback(last_race_number)  # Pass the numerical part if laps exist
                    else:
                        callback(last_race_number - 1)  # Pass the previous number if no laps or participants exist
            else:
                print("No race records found in the database.")
                if callback and callable(callback):
                    callback(None)  # No races found, pass None
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback and callable(callback):
                callback(None)  # In case of error, pass None

    def get_session_id(self, callback=None):
        #print("Entered get_session_id")
        try:
            #print("Trying to get Max session ID from DB")
            self.cursor.execute('SELECT MAX(SessionID) FROM Races')
            result = self.cursor.fetchone()
            session_id = result[0]
            #print(f"Session ID result: {session_id}")
            if session_id:
                if callback:
                    #print("Invoking callback with session_id")
                    callback(session_id)
            else:
                if callback:
                    print("No Session ID. Invoking callback with session_id None")
                    callback(None)        
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Database operation failed: {e}")
            
            if callback:
                callback(None)
                print(f"DB no session stored, sending default 1: {e}")
                
    def get_race_id(self, race_index, callback = None):
        try:
            self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
            race_id = self.cursor.fetchone()[0]
            if race_id:
                if callback:
                    callback(race_id)  # Pass the deleted race_id back to the main thread
            else:
                if callback:
                    callback(None)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback:
                callback(None)

    def get_latest_race_id(self, callback =None):
        try:
            #print("Trying to get race_index from DB")
            self.cursor.execute('SELECT RaceID FROM Races ORDER BY RaceID DESC LIMIT 1')
            result = self.cursor.fetchone()
            if result:
                last_race_id = result[0]  # Extract the RaceID from the tuple
                #print(f"Race ID fetched: {last_race_id}")
                if callback and callable(callback): callback(last_race_id)
                else:
                    callback(None)
                    print("Callback is not callable or is None")
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Database operation failed: {e}")
            if callback and callable(callback):callback(None)
                
    def write_race(self, race_index, data, session_id):
        try:
            # Replace the incorrect SQL statement with the correct one
            # Concatenate mTranslatedTrackLocation and mTranslatedTrackVariation
            track_info = f"{data['eventInformation']['mTranslatedTrackLocation']} - {data['eventInformation']['mTranslatedTrackVariation']}"
            self.cursor.execute('''
                INSERT OR IGNORE INTO Races (RaceIndex, mTranslatedTrackVariation, mLapsInEvent, SessionID)
                VALUES (?, ?, ?, ?)
            ''', (race_index, track_info, data['eventInformation']['mLapsInEvent'], session_id))         

            self.conn.commit()
        except Exception as e:
            print(f"Failed to write race data to the database: {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            
    def insert_lap_data(self, race_id, participant_name, current_lap, lap_time):
        self.cursor.execute('''
            INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
            VALUES (?, ?, ?, ?)
        ''', (race_id, participant_name, current_lap, lap_time))
        self.conn.commit()

    def finalize_race(self, data, race_index, lap_times_dict, flags_dict):
        participants = data['participants']['mParticipantInfo']
        print(f"Finalizing DB DataRace index: {race_index} Lap times dict:{lap_times_dict} flags: {flags_dict}")        
        self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
        race_id = self.cursor.fetchone()[0]
        
        # Check if there are any laps recorded for the last RaceID
        self.cursor.execute('SELECT COUNT(*) FROM Laps WHERE RaceID = ?', (race_id,))
        rows_in_race = self.cursor.fetchone()[0]  # This will give the count of laps
        if rows_in_race == 0:
            return
        for participant in participants:
            participant_name = participant['mName']
            if participant['mFastestLapTimes'] == -123.0:
                participant['mFastestLapTimes'] = None
            if participant['mLastLapTimes'] == -123.0:
                participant['mLastLapTimes'] = None
            # Retrieve the flag data for this participant from the dictionary
            flags_data = flags_dict.get(participant_name, None)
            # Insert or update participant data in the database
            self.cursor.execute('''
                INSERT OR REPLACE INTO Participants (
                    RaceID, mName, mCarNames, mRacePosition, mFastestLapTimes, mLastLapTimes, flags
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                race_id,
                participant_name,
                participant['mCarNames'],
                participant['mRacePosition'],
                participant['mFastestLapTimes'],
                participant['mLastLapTimes'],
                flags_data
            ))

            current_lap = participant.get('mCurrentLap', 0)

            if current_lap > 1:
                lap_times = lap_times_dict.get(participant_name, [])
                if 1 <= current_lap <= len(lap_times):
                    lap_time = lap_times[current_lap - 1]
                else:
                    lap_time = None

                if lap_time is not None:
                    self.cursor.execute('''
                        INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
                        VALUES (?, ?, ?, ?)
                    ''', (race_id, participant_name, current_lap, lap_time))

        self.conn.commit()

    def delete_race(self, race_id):
        self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
        self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
        self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
        self.conn.commit()

    def stop(self):
        self.running = False
        self.db_queue.put(('stop', None))
        self.quit()  # Stop the event loop if it's running
        self.wait()  # Wait until the thread has fully exited        
        #self.join()  # Wait for the thread to finish before returning
        
class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal()
    flags_updated = pyqtSignal(dict)
    initialize = pyqtSignal()
    #race_id_updated = pyqtSignal(int)  # Signal to update the RaceID
    
    error_occurred = pyqtSignal(str)   # New signal for errors
    connection_restored = pyqtSignal()  # Signal to clear error message
    #race_index_updated = pyqtSignal(int)  # Signal to update race_count
    
    def __init__(self, race_monitor_app, tab_widget ,db_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = ConfigManager()
        self. update_config_file = self.config_manager.update_config_file()
        self.ip_address = self.config_manager.read_ip_address()   #threading.Thread.__init__(self)   
        self.race_monitor_app = race_monitor_app
        self.db_queue = db_queue
        self.update_config_file = self.config_manager.update_config_file()
        #self.session_id_queue = queue.Queue()
        #self.db_queue.put(('initialize_session_id', ()))
        
        #self.ip_address = self.read_ip_address()
        self.tab_widget = tab_widget  # Store the reference to tab_widget
        self.previous_race_state = None
        self.current_race_id = None
        self.viewing_race_id = None
        self.running = True
        self.first_time_run = True
        self.session = requests.Session()
        self.lap_times_dict = {}
        self.driver_flags = {}
        #Signalling
        self.race_monitor_app.session_id_updated.connect(self.set_session_id) # Connect the signal to a slot that updates Session ID
       
        # Adjusting race_count based on existing data in the database
        Previous_ipaddress = "127.0.0.1"
        # Get the latest RaceID and corresponding RaceIndex
        logging.info(f"Thread ID in operation: {threading.get_ident()}")
        #print(f"Monitor init Thread ID in operation: {threading.get_ident()}")
        self.db_queue.put(('get_race_index', (self.set_race_index,)))
        self.db_queue.put(('get_session_id', (self.set_session_id,)))
        
        #self.session_id = 1
        #self.race_index = 1
          # New variable for viewing historical data
          # Dictionary to track lap times for each participant

       
         #def handle_race_index(self, new_race_index):
         #self.race_count_updated.emit(new_race_index)
       
    def set_race_index(self, new_race_count):
        if new_race_count is None:
            print("Race index is None, setting to 0")
            self.race_index = 0
        else:
            self.race_index = new_race_count
        #print(f"Monitorapp Race index updated to {self.race_index}")    
    
    def set_session_id(self, new_session_id):
        if new_session_id is None:
            print("Session ID is None, setting to 1")
            self.session_id = 1
        else:            
            self.session_id = new_session_id
            print(f"Monitorapp Session ID updated to {self.session_id}") 

    def receive_number_of_rows(self,rows):
        self.number_of_rows = rows            
        
    
        

        #logging.info(f"Lap {current_lap} for {participant_name} recorded with time {lap_time}")
    def run(self):
        while self.running:
            try:
                
                Previous_ipaddress=self.ip_address
                #logging.info("Attempting to get data from the API.")
                self.ip_address = self.config_manager.read_ip_address()  # Read IP address before each API call
                
                with self.session.get(f'http://{self.ip_address}:8180/crest2/v1/api') as response:
                    data = response.json()

                    #Ensure the response content is valid JSON
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if data is None:
                                raise ValueError("Received None as data. Possible issue with API response.")
                        except ValueError as ve:
                            logging.error(f"Error parsing JSON response: {ve}")
                            print(f"Error parsing JSON response: {ve}")
                            continue  # Skip this loop iteration and try again
                    else:
                        logging.error(f"Unexpected status code {response.status_code} received from the API.")
                        print(f"Unexpected status code {response.status_code} received from the API.")
                        continue  # Skip this loop iteration and try again
                # Fetch participants data
                participants = data.get('participants', {}).get('mParticipantInfo', [])
                if not participants and self.first_time_run:
                    self.first_time_run = False
                    logging.info("No participants found, Still waiting for race start.")
                    print("Waiting for race start.....")
                    time.sleep(5) # Wait for some time before retrying
                    self.initialize.emit() #Load selected race after start.  
                    continue  # Restart loop if participants list is empty
                
                # Proceed with processing the valid data                
                data = response.json()
                # Store the latest data         
                #logging.info(f"Full API response: {json.dumps(data, indent=2)}")
                if Previous_ipaddress != self.ip_address:
                    print(f"Ipadress changed, new ipadress {self.ip_address}")
                

                #logging.info(f"Current Race_State: {current_race_state}")              
               
                self.connection_restored.emit() # Emit signal for successful connection restoration to clear error message
                
                #logging.info(f"Race_state emitted!")
                current_race_state = data['gameStates']['mGameState']
                if current_race_state != self.previous_race_state:
                    print(f"Game state changed to {current_race_state}")  # Ensure console output remains
                    #logging.info(f"Race state changed to {current_race_state}")
                    self.previous_race_state = current_race_state
                #print(f"Sleeping.....")
                time.sleep(5)  # Wait for 5 seconds before fetching the next data)
                

                if participants:
                    self.race_index += 1 #Increment Race Index to next Race number
                    self.lap_times_dict = {} # Clear the lap times dictionary ready for next race.
                    self.last_lap_counts = {} # Clear the last lap counts dictionary
                    driver_total_times = {} # Clear the driver total times dictionary
                    self.driver_flags ={} # Clear the driver flags dictionary
                    #print("Race index +1 laptimes and last lap counts dictionarys reset")
                    race_index = f"Race_{self.race_index}" #Make the Race DB entry String Race_1, Race_2 etc.
                    logging.info(f"Race {self.race_index} has started, beginning data collection.")
                    logging.info(f"Connected to the database, processing race {race_index}.")
                    last_lap_counts = {}
                    QMetaObject.invokeMethod(self.tab_widget, "setCurrentIndex", Qt.QueuedConnection, Q_ARG(int, 0)) #Switch to Score View tab
                    print("Race is STARTING!!!!!!.")
                    #print(f"Data to be written to database: race index: {race_index} Sesson id: {self.session_id}")
                    try:
                      self.db_queue.put(('write_race', (race_index, data, self.session_id)))
                    except Exception as e:
                        logging.error(f"Sesson ID not gotten, trying again {e}")
                        print(f"Sesson ID not gotten, trying again: {e}")                    
                        raise
                    #print("Race written to database.")
                         
                    def handle_race_id (race_id):
                        global app
                        print (f"Fetch race ID after write Race. Race_id: {race_id}")
                        if race_id is None:
                            print("Race_id is None, program crash!")
                            raise ValueError("An error occurred")
                            if app is not None:
                                app.quit()  # Properly quit the application if an error occurs        
                        else:
                            self.current_race_id = race_id
                            #print(f"Monitorthread Race ID received from DB Race id: {self.current_race_id}")
                    #    print(f"Race_id Signal sendt to GUI: {self.current_race_id}")
                    self.db_queue.put(('get_race_id', (race_index,handle_race_id)))  # Only pass the necessary data, not the function

                    while self.running: #loop while race is running
                        try:
                            #self.race_id_updated.emit(self.current_race_id)  # Emit signal with the updated RaceID   
                            Previous_ipaddress=self.ip_address
                            previous_data = data
                            logging.info("Attempting to get data from the API.")
                            #print("Attempting to get data from the API.")
                            self.ip_address = self.config_manager.read_ip_address()  # Read IP address before each API call
                            with self.session.get(f'http://{self.ip_address}:8180/crest2/v1/api') as response:
                                data = response.json()
                                # Ensure the response content is valid JSON
                               
                                if response.status_code == 200:
                                    try:
                                        data = response.json()
                                        if data is None:
                                            print("Data error")
                                            raise ValueError("Received None as data. Possible issue with API response.")
                                    except ValueError as ve:
                                        logging.error(f"Error parsing JSON response: {ve}")
                                        print(f"Error parsing JSON response: {ve}")
                                        continue  # Skip this loop iteration and try again
                                else:
                                    logging.error(f"Unexpected status code {response.status_code} received from the API.")
                                    print(f"Unexpected status code {response.status_code} received from the API.")
                                    data = previous_data  # Revert to the previous data if no participants are found
                                    continue  # Skip this loop iteration and try again

                            # Proceed with processing the valid data                             
                                
                            participants = data.get('participants', {}).get('mParticipantInfo', [])
                            if not participants:
                                data = previous_data  # Revert to the previous data if no participants are found
                                logging.info("No participants found, Race is over")
                                print("No participants found, Race is over.")
                                self.first_time_run = True
                                break # Race is over, break the loop
                            
                            logging.info(f"Processing data for {len(participants)} participants.")
                            #print(f"Processing data for {len(participants)} participants. Current Race_ID {self.current_race_id}")
                      
                            self.connection_restored.emit() # Emit signal for successful connection restoration to clear the error message
                            logging.info(f"RaceID for {race_index} is {self.current_race_id}.")
                            #print(f"RaceID for {race_index} is {race_id}.")

                            for participant in participants:
                                participant_name = participant['mName']
                                current_lap = participant.get('mCurrentLap', 0)
                                logging.info(f"Participant {participant_name} is on lap {current_lap}.")
                                #print(f"Participant {participant_name} is on lap {current_lap}.")
                                if participant_name not in self.lap_times_dict:
                                    self.lap_times_dict[participant_name] = []
                                latest_lap_time = participant.get('mLastLapTimes', None)
                                #print(f"Latest Lap Time: {latest_lap_time}")
                                lap_times = self.lap_times_dict[participant_name]
                                #lap_number =  len(self.lap_times_dict[participant_name])
                                #previous_lap = current_lap - 1
                                #print(f"number of laps: {lap_number} Current lap:{previous_lap}")
                                if latest_lap_time is not None and len(self.lap_times_dict[participant_name]) < current_lap - 1:
                                    self.lap_times_dict[participant_name].append(latest_lap_time)
                                    #print(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                    logging.info(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                    #print(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                    logging.info(f"Lap times list for {participant_name}: {lap_times}")
                                    #print(f"Lap times list for {participant_name}: {lap_times}")

                                #print(f"number of laps: {lap_number} Current lap:{previous_lap}")
                                if current_lap > last_lap_counts.get(participant_name, 1):
                                    if current_lap - 1 <= len(lap_times):
                                        lap_time = lap_times[current_lap - 2]
                                        if participant_name not in driver_total_times:
                                            driver_total_times[participant_name] = 0  # Initialize the key with a value of 0
                                        if lap_time is not None:    
                                            driver_total_times[participant_name] += lap_time
                                        logging.info(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time}")
                                        # mLapInvalidated = data.get('timings', {}).get('mLapInvalidated', 'Unknown')
                                        # print(f"Participant: {participant_name}, mLapInvalidated: {mLapInvalidated}")
                                        #print(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time}")
                                        #print(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time},{participant.get('mLastLapTimes', None)} ")
                                        logging.info(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time},{participant.get('mLastLapTimes', None)} ")                                        

                                        #self.db_queue.put(('get_number_of_rows',(self.current_race_id, self.receive_number_of_rows)))
                                        if current_lap == 2 and latest_lap_time == -123:
                                            #print(f"Number of rows: {self.number_of_rows}")
                                            #if self.number_of_rows >= participant.get('mRacePosition', None):
                                            print(f"Adding Falsestart to Flags for {participant_name} Current lap:{current_lap}")
                                            self.driver_flags[participant_name] = 'Falsestart'
                                            self.flags_updated.emit(self.driver_flags)

                                        self.db_queue.put(('insert_lap_data', (self.current_race_id, participant_name, current_lap - 1, lap_time))) #insert lap into Table
                                        last_lap_counts[participant_name] = current_lap

                            #time.sleep(5)     
                            current_race_state = data['gameStates']['mGameState']       
                            self.data_updated.emit(data) #Send the data to Live view
                            if current_race_state != self.previous_race_state:
                                print(f"Game state changed to {current_race_state}")  # Ensure console output remains
                                logging.info(f"Race state changed to {current_race_state}")
                                self.previous_race_state = current_race_state                            
                            #print(f"Data Sent to live view {race_index}.")
                            time.sleep(2)

                            current_race_state = data['gameStates']['mGameState']
                            #print (f"Last line of the loop: Current_Race_State: {current_race_state} self.running: {self.running}")
                            logging.info(f"Last line of the loop: Current_Race_State: {current_race_state} self.running: {self.running}")
                        except Exception as e:
                            logging.error(f"An error occurred while processing participant data: {e}")
                            print(f"An error occurred while processing participant data: {e}")
                            raise
                        except requests.exceptions.ConnectionError:
                            logging.error(f"Connection error: Unable to reach the server at {self.ip_address}. Retrying in 2 seconds.")
                            print(f"Connection error: Unable to reach the server at {self.ip_address}. Retrying in 2 seconds.")
                            self.error_occurred.emit('Connection Error: Unable to reach server')
                            time.sleep(2)
                            
                        except requests.exceptions.Timeout:
                            logging.error(f"Timeout error: The server at {self.ip_address} did not respond. Retrying in 2 seconds.")
                            print(f"Timeout error: The server at {self.ip_address} did not respond. Retrying in 2 seconds.")
                            self.error_occurred.emit('Timeout Error: Server did not respond')
                            time.sleep(2)
                            
                        except requests.exceptions.RequestException as e:
                            logging.error(f"Request error: An error occurred - {str(e)}. Retrying in 2 seconds.")
                            print(f"Request error: An error occurred - {str(e)}. Retrying in 2 seconds.")
                            self.error_occurred.emit(f'Request Error: {str(e)}')
                            time.sleep(2)                            
                    logging.info(f"Race {self.race_index} has ended. Current_Race_State: {current_race_state} self.running: {self.running}")
                    print(f"Race Ended Finalizing Race for Race_index: {race_index}, Current_Race_State: {current_race_state} self.running: {self.running}")
                    participants = data.get('participants', {}).get('mParticipantInfo', [])
                    total_laps = data['eventInformation']['mLapsInEvent']
                    total_time_participant = {}
                    print(f"Driver Total times: {driver_total_times}")
                    if not driver_total_times:
                        print("No reason to write race, no one finished.")
                        break   # no reason to write the race, no one finished
                    best_participant = min(driver_total_times, key=driver_total_times.get)
                    if not best_participant:
                        print("No reason to write race, no one finished.")
                        break   # no reason to write the race, no one finished
                        
                    print(f"Best Participant: {best_participant}")
                    winner_data = next((p for p in participants if p['mRacePosition'] == 1), None)
                    winner = winner_data.get('mName', 'Unknown')
                    print(f"Winner: {winner}")
                    for participant in participants:
                        #total_time_participant = driver_total_times.get(participant['participant'], 0)
                        
                        if participant.get('mRacePosition') == 1:
                            winner = participant['mName']
                            print(f"Winner: {winner}")
                        total_time_participant[participant['mName']] = driver_total_times.get(participant['mName'], 100000)
                        print(f"Participant: {participant['mName']}, Race Position: {participant.get('mRacePosition', 0)}, Total Laps: {total_laps} Tolal Time: {total_time_participant[participant['mName']]}")
                        participant_name = participant['mName']
                        current_lap = participant.get('mCurrentLap', 0)
                        print(f"Participant: {participant_name}, Current Lap: {current_lap}, Total Laps: {total_laps}")
                        print(f"Best Participant: {best_participant}, Winner: {winner}")
                        if participant['mName'] == winner and current_lap < total_laps:
                            print(f"Driver is {participant_name} same as {winner} and did not finish. That means False start!")
                            print(f"Adding Falsestart to Flags for {participant_name}")
                            self.driver_flags[participant_name] = 'Falsestart'
                                #self.driver_flags[participant_name].append('Falsestart')
                        if current_lap <= total_laps: # Driver has fewer laps less than he should, either False start Or DNF
                            # Check if the participant has a 'Falsestart' flag
                            print(f"Participant: {participant_name}, Flags: {self.driver_flags}")
                            #if participant_name in self.driver_flags:
                            if self.driver_flags.get(participant_name) != 'Falsestart':
                                print(f"Adding DNF to Flags for {participant_name}")
                                self.driver_flags[participant_name] = 'DNF'  # Initialize an empty list for the driver's flags
                        #Participant Loop is over
                    self.flags_updated.emit(self.driver_flags)
                    print(f"Sending Data for the last time")
                    self.data_updated.emit(data) #Send the data to Live view to update the flags
 
                    self.db_queue.put(('finalize_race', (data, race_index, self.lap_times_dict,self.driver_flags)))
                    time.sleep (3)
                    self.race_finished.emit()
                    time.sleep(10)
                    self.db_queue.put(('get_race_index', (self.set_race_index,)))
                        
            except requests.exceptions.ConnectionError:
                logging.error(f"Connection error: Unable to reach the server at {self.ip_address}. Retrying in 2 seconds.")
                print(f"Connection error: Unable to reach the server at {self.ip_address}. Retrying in 2 seconds.")
                self.error_occurred.emit('Connection Error: Unable to reach server')
                time.sleep(2)
                
            except requests.exceptions.Timeout:
                logging.error(f"Timeout error: The server at {self.ip_address} did not respond. Retrying in 2 seconds.")
                print(f"Timeout error: The server at {self.ip_address} did not respond. Retrying in 2 seconds.")
                self.error_occurred.emit('Timeout Error: Server did not respond')
                time.sleep(2)
                
            except requests.exceptions.RequestException as e:
                logging.error(f"Request error: An error occurred - {str(e)}. Retrying in 2 seconds.")
                print(f"Request error: An error occurred - {str(e)}. Retrying in 2 seconds.")
                self.error_occurred.emit(f'Request Error: {str(e)}')
                time.sleep(2)

            except Exception as e:
                logging.error(f"An error occurred while monitoring race state: {e}")
                print(f"An error occurred while monitoring race state: {e}")
                time.sleep(5)
    
    def stop(self):
        self.running = False
        self.session.close()
        #self.DatabaseThread.stop()
        self.quit()
        self.wait()

#class Worker(QObject):
    #switch_tab_signal = pyqtSignal(int)  # Define a signal to switch tabs
    #race_written = pyqtSignal(bool)  # Signal to indicate whether the race was written successfully
        #switch_tab_signal = pyqtSignal(int)  # Define a signal to switch tabs
    #race_data_loaded = pyqtSignal(list)  # Signal that will carry the race data
    #laps_fetched_signal = pyqtSignal(str, list, int)  # Signal for fetched laps
    #self.signals.laps_fetched_signal.emit(participant_name, recorded_laps, current_lap)
    #race_data_loaded_signal = pyqtSignal(int, str, int, list)  # Signal to emit loaded race data
    #self.signals.race_data_loaded_signal.emit(race_id, track_variation, laps_in_event, participants)
    session_id_updated = pyqtSignal(int)  # Signal to update the SessionID    

class RaceMonitorApp(QMainWindow):
    session_id_updated = pyqtSignal(int)  # Signal to update the SessionID
    def __init__(self):
        super().__init__()
         # Define all image paths using resource_path
        liverace_liveview_img_path = resource_path('LiveRace_LiveView.jpg')
        liverace_status_img_path = resource_path('LiveRace_Status')
        # Set the window icon
        icon_path = resource_path('RockyTM.ico')
        self.setWindowIcon(QIcon(icon_path))
        # Initialize QPixmap objects for each image
        self.live_background_image = QPixmap(liverace_liveview_img_path)  # Background for Live view
        self.live_status_image = QPixmap(liverace_status_img_path)
        self.db_queue = queue.Queue()
        self.db_thread = DatabaseThread(self.db_queue)
        self.db_thread.start()
        self.setWindowTitle("Live Race Data")
        self.setGeometry(100, 100, 1400, 900)
        
        self.setFixedSize(1400, 900) # Set fixed size to prevent autoresizing
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Fully transparent
        self.labels = {}
        self.current_race_id = None
        self.session_id = None
        self.live_first_time_run =True
        self.driver_flags = {}
        self.session_id_dropdown = None
         #self.runs = 0
 
        #Get DB values
        self.db_queue.put(('get_session_id', (self.set_session_id,)))
        
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
        background-position: center;
        background-repeat: no-repeat;
        """)
        # Create a QTabWidget to hold different views
        self.tab_widget = QTabWidget(self.central_widget)
        self.monitor_thread = MonitorThread(self, self.tab_widget, self.db_queue)
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.flags_updated.connect(self.update_flags)
        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.initialize.connect(self.initialize_dropdown)
        #self.monitor_thread.race_id_updated.connect(self.update_race_id)  # Connect the signal
        self.monitor_thread.error_occurred.connect(self.show_error_message)  # Connect the error signal
        self.monitor_thread.connection_restored.connect(self.handle_connection_restored)  # Connection restored
        self.db_thread.load_race_on_start_signal.connect(self.handle_race_data) # Get data to populate select races dropdown
        self.db_thread.load_sessionid_on_start_signal.connect(self.handle_sessionid_data) # Get data to populate session ID dropdown
        #self.db_thread.laps_fetched_signal.connect(self.update_participant_label) # Connect the signal to the slot that updates the UI
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
        # Tabs addition end
        # Connect tab change to background update
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        # Load the background image
        #self.background_image = QPixmap("LiveRace.jpg")
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
        self.layout.addSpacing(35) 
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
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
        """)        
        self.delete_button.setFixedSize(150, 30)
        self.delete_button.clicked.connect(self.delete_selected_race)
        self.layout.addWidget(self.delete_button) 

        # Add the New Session button
        self.new_session_button = QPushButton("Start New Session", self)
        self.labels['new_session_button'] = self.new_session_button
        self.new_session_button.setStyleSheet("""
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
            margin-bottom: 5px;                             
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
        """)
        self.new_session_button.setFixedSize(150, 30)
        self.new_session_button.clicked.connect(self.start_new_session)
        self.layout.addWidget(self.new_session_button) 

        # Status label for connection issues
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
        self.layout.addWidget(self.status_label)  # Add the status label below the delete button
        self.tab_widget_mapping = {  # Widget visibility mapping for each tab
            0: [],  # Widgets for Live View
            1: ['dropdown', 'delete_button' ],  # Widgets for Results View
            2: ['new_session_button', 'dropdown_sessionid' ],  # Widgets for Score View
        }        



        self.status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);") # Call the function to load race data
        #Set the Status view as the default tab
        self.tab_widget.setCurrentIndex(2)
        self.tab_widget.setCurrentIndex(1)
        
    def update_flags(self, flags):
        self.driver_flags=flags # Update the flags label with the message
        
    def initialize_dropdown(self):
         #self.load_sessionid_on_start()   
         #self.load_race_data_on_start()
         self.db_queue.put(('load_race_data_on_start',())) #Send the request to the DatabaseThread to load race data on start
         self.db_queue.put(('load_sessionid_on_start',())) 
    #def load_race_data_on_start(self):

     
    #def load_sessionid_on_start(self):

         


        
    def set_session_id(self, new_session_id):
        if new_session_id is None:
            print(f"Session ID not found in the database, setting to 1")
            self.session_id = 1
        else:
            print("Loading Dropdown boxes")
            self.session_id = new_session_id
            #self.load_race_data_on_start()
               
        #print(f"RaceMonitorApp Session ID updated to {self.session_id}")  
        
    def handle_race_data(self, races, participants):
        self.dropdown.clear()  # Clear the dropdown first
        if races:
            for race in races:
                race_id, race_index, track_variation, laps_in_event, race_date = race
                # Find participants for the current race
                race_participants = [p for p in participants if p[0] == race_id]
                # Format participant car names and ensure uniqueness
                cars = ', '.join(sorted(set([p[1] for p in race_participants]))) if race_participants else "No participants"
                # Combine race and participant information into the dropdown item
                item_text = f"{race_date} - {track_variation} - {race_index} -  {cars}"
                self.dropdown.blockSignals(True)
                self.dropdown.addItem(item_text)
                self.dropdown.setCurrentIndex(self.dropdown.count() - 1)  # Load the latest race results by default
                self.dropdown.blockSignals(False)
        self.load_selected_race()
           
    def handle_sessionid_data(self, sessionids):
        self.dropdown_sessionid.clear()  # Add this line to clear the dropdown
        #print(f"Session ID data received: {sessionids}")
        if sessionids:
            for session_id in sessionids:
                self.dropdown_sessionid.blockSignals(True)
                self.dropdown_sessionid.addItem(f"Session ID - {session_id}")
                self.dropdown_sessionid.blockSignals(False)
            # Load the latest race results by default


        

    def on_tab_changed(self, index):
        # Hide all widgets first
        for widget_list in self.tab_widget_mapping.values():
            for widget_name in widget_list:
                if widget_name in self.labels:  # Check if the widget exists in the labels dictionary
                    self.labels[widget_name].hide()
        
        for widget_name in self.tab_widget_mapping.get(index, []): # Show only the widgets associated with the active tab
            if widget_name in self.labels:
                self.labels[widget_name].show()
        if index == 0: self.update_background('live') # Handle other tab-specific logic, like background updates
        elif index == 1: self.update_background('status')

    def update_background(self, view):
        if view == 'status': self.background_label.setPixmap(self.status_background_image)
        elif view == 'live': self.background_label.setPixmap(self.live_background_image)

    def clear_error_message(self):
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()

    def handle_connection_restored(self):
        self.clear_error_message() # Clear the error message immediately upon restoring the connection
        
    def update_status_message(self, message):
        self.status_label.setText(message) # Update the status label with the message

    def blink_status_message(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_status_visibility)
        self.timer.start(500)  # Blink every 500 ms

    def toggle_status_visibility(self):
        if self.status_label.isVisible(): self.status_label.setVisible(False)
        else: self.status_label.setVisible(True)
   
    def show_error_message(self, message):
        # Check if the error label already exists with the same message
        if hasattr(self, 'error_label') and self.error_label.text() == message: return  # Do not create a new label if the message is the same
        if hasattr(self, 'error_label'): self.error_label.deleteLater()  # Remove the existing error label
           
        # Create the error label with the new message
        self.error_label = QLabel(message, self)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setFixedSize(1060, 35)
        self.error_label.setStyleSheet("font-size: 18px; color: red; background-color: yellow; padding: 10px;")
        self.blink_error_message()

    def blink_error_message(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_error_visibility)
        self.timer.start(500)  # Blink every 500 ms

    def toggle_error_visibility(self):
        if hasattr(self, 'error_label') and self.error_label is not None:
            if self.error_label.isVisible(): self.error_label.setVisible(False)
            else: self.error_label.setVisible(True)

    def setup_live_view(self):
        # Setup your live view widgets here
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

    def setup_result_view(self):
        # Content label for displaying loaded results
        self.results_content = QLabel("No race data available", self.results_view_widget)
        self.results_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        self.results_view_layout.addWidget(self.results_content)
        self.results_view_layout.addStretch(1)
        
    def setup_final_view(self):
        # Content label for displaying Final results
        self.final_content = QLabel("No race data available", self.final_view_widget)
        self.final_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        self.final_view_layout.addWidget(self.final_content)
        self.final_view_layout.addStretch(1)
        
        
    def set_race_id(self, new_latest_id):
        self.current_race_id = new_latest_id
        #print(f"Racemonitorapp Race ID set to {self.current_race_id}")
        
    def on_first_live_view_run(self):
        #print("Should only run once!")
        self.db_queue.put(('get_latest_race_id', (self.set_race_id,)))
        #self.load_race_data_on_start() # Knapp oppdatert med nytt race
        self.final_content.setText("Score - Waiting for a new race to start...")
        self.current_lap = {}
        self.previous_current_lap = {}
        self.current_bestlap_name = None
        self.previous_best_lap_time = None
        self.best_lap_time = None
        self.lap_time ={}
        self.lap_list = {}
        self.total_time_seconds = {}
        self.driver_flags = {}
        #self.load_sessionid_on_start() # Knapp oppdatert med siste session.
        
    def update_live_view(self, data):
        if self.live_first_time_run: self.on_first_live_view_run()
        #print(f"Iterations: {self.runs}")
        background_color = "#333333"  # Default background color
        top_background_color = "#A7DB8D"  # Default top background color
        # Extract event information and participant details from the data
        event_info = data['eventInformation']
        participants = data['participants']['mParticipantInfo']
        sorted_participants = sorted(participants[:data['participants']['mNumParticipants']], key=lambda p: p['mRacePosition']) # Sort participants by race position
        #print(f"Number of participants: {len(sorted_participants)}")
        # Set Heading text
        heading_text = f"{event_info['mTranslatedTrackVariation']} ({event_info['mLapsInEvent']}) - {participants[0]['mCarNames']} - Session ID: {self.session_id}" # Update the heading with track variation and car names
        self.live_heading.setText(heading_text)
        # Find the best valid lap time
        valid_lap_times = [p['mFastestLapTimes'] for p in sorted_participants if p['mFastestLapTimes'] != -123] # Find the valid Lap Times
        if valid_lap_times:
            self.previous_best_lap_time = self.best_lap_time
            self.best_lap_time = min(valid_lap_times)
            if self.previous_best_lap_time != self.best_lap_time: print(f"New best Lap Time: {self.format_lap_time(self.best_lap_time)}")

        for i, participant in enumerate(sorted_participants): # Loop through each participant to update their corresponding label
            # Get and store lap times in a dictionary
            #print(f"Participant: {participant['mName']} Lap: {participant['mCurrentLap']} Last Lap: {participant['mLastLapTimes']} Fastest Lap: {participant['mFastestLapTimes']}")
            self.current_lap[participant['mName']] = participant['mCurrentLap']
            
            if participant['mLastLapTimes'] != -123 and participant['mName'] in self.previous_current_lap:
                if self.current_lap[participant['mName']] != self.previous_current_lap.get(participant['mName'], None):
                    #print(f"Current Lap changed: {self.current_lap[participant['mName']]}")
                    #if participant['mName'] not in self.lap_time:
                    self.lap_time[participant['mName']] = participant['mLastLapTimes']
                    #print(f"LapTime:{self.lap_time[participant['mName']]}")
                    if participant['mName'] not in self.lap_list:
                        self.lap_list[participant['mName']] = [self.format_lap_time(self.lap_time[participant['mName']])]
                        #print(f"self lap time for participant: {participant['mName']} {self.lap_time[participant['mName']]} on lap: {self.previous_current_lap[participant['mName']]}")
                        self.total_time_seconds[participant['mName']] = self.lap_time[participant['mName']]
                        #print(f"Total Time for participant first lap:{participant['mName']} {self.total_time_seconds}")
                    else:
                        self.lap_list[participant['mName']].append(self.format_lap_time(self.lap_time[participant['mName']]))
                        #print(f"self lap time for participant: {participant['mName']} {self.lap_time[participant['mName']]} on lap: {self.previous_current_lap[participant['mName']]}")
                        #print(f"Appending laptimes to lap list: {self.lap_list[participant['mName']]}")
                        self.total_time_seconds[participant['mName']] += self.lap_time[participant['mName']]
                        #print(f"Total Time for participant second lap+:{participant['mName']} {self.total_time_seconds}")
                    #print(f"Setting new current lap for participant: {participant['mName']} Previous Lap: {self.previous_current_lap[participant['mName']]}")
                    self.previous_current_lap[participant['mName']] = self.current_lap[participant['mName']]
                    
                    #print(f"Total Time for participant:{participant['mName']} {self.total_time_seconds}")
                    #self.current_lap_str[participant.append(self.format_lap_time(participant('mCurrentLap')))
            else:
                self.previous_current_lap[participant['mName']] = 1
               
            participant_name = participant['mName']
            if participant['mName'] in self.lap_list: lap_times_str = ", ".join(self.lap_list[participant['mName']])
            else: lap_times_str = "No Valid Lap!"
            last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
            fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])
            if participant['mName'] in self.total_time_seconds: total_time_str = self.format_lap_time(self.total_time_seconds[participant['mName']])
            else: total_time_str = "No Valid Lap!"
            # Check if the participant has a flag in self.driver_flags
            flag = self.driver_flags.get(participant_name, None)
            if not flag: # If the participant has no flag, set it to an empty string
                flag = ""
            
            label = self.participant_labels[i]
            # set default background color
            label.setStyleSheet(f"font-size: 14px; background-color: {background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
            #print(f"current lap: {current_lap}")
            #if self.current_lap < 3: # For the driver being processed.
            # Create the participant text using the utility function
            #total_time_seconds = sum(lap[1] for lap in self.current_lap_list[participant['mName']])
            
            
            participant_text = self.create_participant_text(participant,flag, last_lap_str, fastest_lap_str, lap_times_str, total_time_str)
            #participant_text = self.create_participant_text(participant,flag, last_lap_str, fastest_lap_str, last_lap_str, self.current_lap_list[participant['mName']])
            #participant_text = self.create_participant_text()
            if self.live_first_time_run: # Sets all labels to the default background color if no valid lap times are found and it is first run.                   
                label.show()  # Make the label visible
                #print(f"No one has a valid lap time: {participant_name} Time:No valid lap")
                self.live_status_label.setText("Race Started!")  # Update the status label"
            #else:
                #print(f"Fetching Laps from DB: {participant_name}")
                #self.db_queue.put(('fetch_recorded_laps', (participant_name, self.current_race_id, self.current_lap,)))
                
                #lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in self.laps_to_display)    
                #total_time_seconds = sum(lap[1] for lap in self.laps_to_display)

                #print(f"Fetching Laps from DB: {participant_name}, Laps: {lap_times_str} Run:{self.runs}")
                # Now update the label with the participant text and styling
            if participant['mFastestLapTimes'] == self.best_lap_time: #sets the best lap time participant to a different color
                label.setStyleSheet(f"font-size: 14px; background-color: {top_background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                if self.previous_best_lap_time != self.best_lap_time: 
                    #print(f"Best time color assigned: {participant_name} Last Lap:{last_lap_str} Best Lap in race: {self.format_lap_time(self.best_lap_time)}")
                    self.live_status_label.setText(f"Best time: {participant_name} Best Lap in race: {self.format_lap_time(self.best_lap_time)}")
        
            label.setText(participant_text)  # Update the existing label with the new participant text and styling
            label.show()  # Make the label visible
        self.live_first_time_run = False
       
        #def update_participant_label(self, participant_name, recorded_laps, current_lap,):
        #self.laps_to_display = [lap for lap in recorded_laps if lap[0] < current_lap]
        #lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in self.laps_to_display)
        # print(f"Laps received from DB: {participant_name}, Recorded laps: {recorded_laps} Laps: {lap_times_str} run: {self.runs}")

    def format_lap_time(self, lap_time):
        #Helper function to format lap time from seconds to 'MM:SS.ss' format.
        if lap_time is None or lap_time == -123.0:
            return "No Valid Lap!"
        minutes = int(lap_time // 60)
        seconds = lap_time % 60
        return f"{minutes}:{seconds:05.2f}"
    
    def create_participant_text(self, participant,flag, last_lap_str, fastest_lap_str, lap_times_str, total_time_str=""):
        #Helper function to create participant text with custom styling.self.initialize_dropdown
        flag_text = f" <span style='color:#FF0000;font-weight:bold'>( {flag} )</span>" if flag else ""
        return (
        f"<span style='font-weight:bold; color:#FFFFFF;'>{participant['mRacePosition']}</span>: "
        f"<span style='color:#FFFFFF;font-weight:bold'>{participant['mName']}{flag_text}</span> - "
        f"<span style='color:#FFFFA0;'>Last Lap: <span style='color:#00FF00;'>{last_lap_str}</span> - "
        f"<span style='color:#FFFFA0;'>Best Lap: <span style='color:#FFD700;'>{fastest_lap_str}</span> - "
        f"<span style='color:#FFFFA0;'>Laptimes: <span style='color:#FFFFFF;'>[{lap_times_str}]</span> - "
        f"<span style='color:#FFFFA0;'>Total Time: <span style='color:#FFFFFF;'>[{total_time_str}]</span>"
        )
    
    def display_final_results(self):
        # Display the score data in the final view
        self.live_first_time_run =True
        self.initialize_dropdown()
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop() 
        #self.db_queue.put(('get_score_data', (self.session_id,))) #show score from current session ID
        self.tab_widget.setCurrentIndex(2) #Switch to Final View tab
        
        #self.load_sessionid_on_start()
        #self.load_race_data_on_start()
        #self.initialize_dropdown()
    
    def display_score(self):
        logging.info(f"Display Score Result")
        print(f"Display score Result")
        selected_index = self.dropdown_sessionid.currentIndex()
        if selected_index >= 0:
            sessionid_text = self.dropdown_sessionid.itemText(selected_index)
            print(f"Selected Session: {sessionid_text}")
            self.session_id_dropdown = sessionid_text.split(" - ")[-1]       
        # Clear any existing error message if the connection is successful
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        
        if hasattr(self, 'timer') and self.timer.isActive():
          self.timer.stop()
        if self.session_id_dropdown != None:
            print(f"Get score Data. Session ID: {self.session_id_dropdown}")
            self.db_queue.put(('get_score_data', self.session_id_dropdown,)) #Get data I need to calculate score (New Session ID button must not be pushed before this))
           
 
    def calculate_score(self, races, participants, laps):
        if not laps:
            return
        # Initialize dictionaries for storing aggregated data across all races
        # Keep track of unique races
        processed_race_ids = set()  # Add this line at the start of the method
        race_scores = {}  # Dictionary to store the score for each participant in each race
        total_scores = {}  # Dictionary to accumulate total scores for each participant across all races
        # Initialize dictionaries for storing aggregated data across all races
        race_scores = {}  # Dictionary to store the score for each participant in each race
        total_scores = {}  # Dictionary to accumulate total scores for each participant across all races
        last_positions = {}  # To store the last position of each driver
        medal_counts = {'gold': {}, 'silver': {}, 'bronze': {}}  # To count gold, silver, and bronze medals

        # Load the score table from the config file
        config = configparser.ConfigParser()
        config.read('config.ini')

        # Extract scoring rules
        score_table = {int(k.split('_')[0]): int(v) for k, v in config['Score Table'].items() if k != 'best_lap'}
        best_lap_bonus = int(config['Score Table']['best_lap'])

        # Iterate over each race
        #print(f"races: {races}")
        for race in races:
            #print(f"Starting New Race Loop: {race}")
            
            race_id = race[0]  # Assuming race_id is the first element in the race tuple
            processed_race_ids.add(race_id)  # Add this inside the loop that iterates over each race

            # Initialize the race-specific data
            race_scores[race_id] = {}

            # Calculate the total race time for each driver based on the laps
            driver_total_times = {}
            driver_flags = {}
            best_lap_times = {}
            
            #print(f"Laps: {laps}")
            for lap in laps:
                lap_race_id = lap[1]
                #print(f"Lap Race ID:{lap_race_id} and Race ID:{race_id}")
                if lap_race_id != race_id:
                    #print(f"Lap not from the current")
                    continue  # Only consider laps from the current race
                

                mName = lap[2]
                lap_time = lap[4]

                # Sum up the lap times for each driver in the current race
                if mName not in driver_total_times:
                    driver_total_times[mName] = 0
                driver_total_times[mName] += lap_time
                #print(f"best lap times {best_lap_times}")
             # Checking to see if there are any participants in this race
            race_participants = [p for p in participants if p[0] == race_id]
            if not race_participants:
                print(f"No participants found for race {race_id}. Skipping score calculation for this race.")
                continue               
            # Retrieve flags and best lap times from the participants table for the current race
            for participant in participants:
                participant_race_id = participant[0]
                #print(f"Participant Race ID: {participant_race_id} Race ID:{race_id}")
                if participant_race_id != race_id:
                    #print(f"Participant Race ID: {participant_race_id} Race ID:{race_id}")
                    #print(f"Participant not in Race")
                    continue  # Only consider participants from the current race
                    
                mName = participant[1]
                flag = participant[6]  # Flags column in the participants table
                #print(f"Name: {mName} Flag: {flag}")
                if flag == 'DNF' and mName not in driver_total_times:
                    driver_total_times[mName] = 0  # Assign a total time of 0
                    driver_flags[mName] = 'DNF'  # Ensure the DNF flag is assigned
                # Store the specific flag values
                if flag == 'Falsestart':
                    driver_flags[mName] = 'Falsestart'
                elif flag == 'DNF':
                    driver_flags[mName] = 'DNF'
                else:
                    driver_flags[mName] = 'No Flag'
                best_lap = participant[4]  # Best lap time in the participants table
                #print(f"Best Lap: {best_lap}")

                # Store the flag  for each driver
                driver_flags[mName] = flag if flag else "No Flag"
                best_lap_times[mName] = best_lap if best_lap else float('inf')
                #print(f"Best Lap Times: {best_lap_times}")
            
            # Rank drivers based on flags and total race time for the current race
            #ranked_drivers = sorted(driver_total_times.items(), key=lambda x: (driver_flags.get(x[0], "No Flag"), x[1]))
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
            ranked_drivers = sorted(driver_total_times.items(), key=lambda x: (flag_priority(driver_flags.get(x[0], "No Flag")),x[1]))  # Sort primarily by flag priority
            #print(f"Ranking: {ranked_drivers}")
            #for driver, total_time in driver_total_times.items():
               # print(f"Driver: {driver}, Flag: {driver_flags.get(driver)}, Time: {total_time}, "
                #      f"Sort Key: ({flag_priority(driver_flags.get(driver, 'No Flag'))}, "
               #       f"{total_time if driver_flags.get(driver) == 'No Flag' else float('inf')})")

            # Output the sorted results
            for driver, time in ranked_drivers:
                flag = driver_flags.get(driver, 'No Flag')
                sort_key = (
                    flag_priority(flag), 
                    time if flag_priority(flag) == 0 else float('inf')
                )
                #print(f"Driver: {driver}, Flag: {flag}, Time: {time}, Sort Key: {sort_key}")

            # Assign scores for the current race
            place = 1
            for mName, _ in ranked_drivers:
                race_scores[race_id][mName] = score_table.get(place, 0)  # Assign points based on position
                
                last_positions[mName] = place # Track the last position for each driver
                if place == 1: # Track gold, silver, and bronze medals
                    medal_counts['gold'][mName] = medal_counts['gold'].get(mName, 0) + 1
                elif place == 2:
                    medal_counts['silver'][mName] = medal_counts['silver'].get(mName, 0) + 1
                elif place == 3:
                    medal_counts['bronze'][mName] = medal_counts['bronze'].get(mName, 0) + 1
                    
                # Add best lap bonus if applicable
                place += 1
                # Adjust the final display to ensure the correct driver is recognized as the winner
               
            # Determine the driver with the best lap time in the race
            #print(f"Best lap times: {best_lap_times}")    
            if best_lap_times:  # Ensure there are lap times to compare
                best_lap_driver = min(best_lap_times.items(), key=lambda x: x[1])[0]
                #print(f"Best lap driver: {best_lap_driver} Time: {best_lap_times[best_lap_driver]} for Race ID:{race_id} ")
                # Award the best lap bonus to that driver
                #print(f"Race ID:{race_id}")
                #print(f"Race Scores:{race_scores}")
                #print(f"{race_scores[race_id][best_lap_driver]}")
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

        # Update the UI with the calculated scores
        
        self.format_score_view(total_scores, len(processed_race_ids), last_positions, medal_counts)        

    def format_score_view(self, total_scores, race_count, last_positions, medal_counts):
        # Sort the drivers by their total score, highest to lowest
        sorted_scores = sorted(total_scores.items(), key=lambda x: x[1], reverse=True)

        # HTML table header with images
        header = f'''
        <div style="text-align: Left; font-size: 20px; margin-bottom: 10px;">Number of Races {race_count}</div>  <!-- Center the number of races -->
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
        
        # HTML rows for each driver
        rows = ''
        
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
        # Close the table
        footer = '</table>'

        # Combine everything into the final score string
        final_score_str = header +table_header + rows + footer

        # Update the UI with the formatted scores
        self.final_content.setText(final_score_str)
     
    def load_selected_race(self): # Function to be called when the data is loaded
        #print("Load Selected race def entered")
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            race_index = race_text.split(" - ")[-2]
            print(f"Selected race: {race_index} from {race_text}")
            self.viewing_race_id = None  # Reset viewing_race_id before loading
            self.db_queue.put(('load_selected_race', (race_index,) )) # Queue the operation to DatabaseThread
            #print(f"Signal Sent")
            
    def on_race_loaded(self, race, participants, laps):
        
        race_id, track_variation, laps_in_event, Session_id = race # Function to be called when the data is loaded
        #print(f"Signal received")
        if race_id:
            self.viewing_race_id = race_id  # Set the viewing_race_id with the loaded race_id
            logging.info(f"Load Selected Race, RaceID: {self.viewing_race_id}")
            print(f"Load Selected Race, RaceID: {self.viewing_race_id}")
                
            displayed_participants = set()
            car_name = participants[0][4] if participants and participants[0][4] else "Unknown Car"
            loaded_results = (f"<span style='font-weight:bold;'>Race No: {race_id} "
                                f"Track: {track_variation} Laps: {laps_in_event} "
                                f"Car: {car_name}:</span><br>")

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
            self.display_score()

    def delete_selected_race(self):
        logging.info(f"Thread ID in operation: {threading.get_ident()}")
        #print(f"Delete Race Thread ID in operation: {threading.get_ident()}")
        
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            race_index = race_text.split(" - ")[-1]
            
            def on_race_deleted(race_id):
                print("Should only see this once")
                if race_id is not None:
                    if self.viewing_race_id == race_id:
                        self.results_content.setText("Race Deleted")
                        self.viewing_race_id = None
                        self.dropdown.blockSignals(True)
                        self.dropdown.removeItem(selected_index)
                        self.set_delete_mode(False) # Deactivates delete mode
                        self.dropdown.blockSignals(False)
                            
            


            # Send request to DatabaseThread
            self.set_delete_mode(True)  # Activates delete mode
            self.db_queue.put(('get_race_id_and_delete', (race_index, on_race_deleted)))
            
    
    def set_delete_mode(self, is_active):
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
        self.session_id += 1
        self.session_id_updated.emit(self.session_id)
        


    def closeEvent(self, event):
        self.monitor_thread.stop()
        self.db_thread.stop()
        event.accept()


def main():
    global app
    create_database()
    app = QApplication(sys.argv)
    ex = RaceMonitorApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address