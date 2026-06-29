from re import L, T; from timeit import Timer; import atexit, sys, re, inspect, requests, sqlite3, queue, json, time, traceback, logging, os, asyncio, aiohttp, math, base64, configparser, tempfile
from PyQt5.QtWidgets import QApplication, QMainWindow, QDesktopWidget, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QTabWidget, QSpacerItem, QMessageBox, QLineEdit, QCalendarWidget, QProgressBar, QButtonGroup, QRadioButton, QGridLayout
from PyQt5.QtGui import QPixmap, QIcon, QFontDatabase, QTransform, QPainter, QFont, QGuiApplication
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer, QObject, QEvent, QEventLoop, QDate, QPoint, QSize, QByteArray, QBuffer
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QBarSet, QBarSeries, QBarCategoryAxis
from datetime import datetime
from ping3 import ping
import socket
from file_base64_strings import (wheels_bg_img_base64, remaining_bg_img_base64, delta_local_record_bg_img_base64, delta_world_record_bg_img_base64, bestlap_bg_img_base64, wheel_bg_img_base64, pedal_raw_bg_img_base64, pedal_bg_img_base64, lap_bg_img_base64, pos_bg_img_base64,laptime_bg_img_base64, speedometer_bg_img_base64,tachometer_bg_img_base64,needle_bg_img_base64, driver_statistics_background_img_base64, high_scores_background_img_base64, race_results_background_img_base64, race_scores_background_img_base64, liverace_liveview_img_base64, liverace_status_img_base64, rockytm_icon_base64, sui_generis_rg_font_base64, ds_digib_font_base64)
if os.path.exists('debug.log'): # Set up logging
    os.remove('debug.log')
logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 

class ConfigManager:
    _instance = None  # Singleton instance for global access
    def __init__(self, task_queue):
        self.config_file = 'config.ini'
        self.__version__ = "1.6.0"
        self.__author__ = "RockyTM"
        self.__email__ = "post@drs.no"
        self.__date__ = "2025-03-28"
        self.__description__ = "Script for getting Race Data from AMS2"
        self.config = configparser.ConfigParser()
        self.task_queue = task_queue
        if ConfigManager._instance is None:
            ConfigManager._instance = self
    @classmethod
    def get_config_value(cls, key, section='DEFAULT', default=None):
        if cls._instance is None:
            config = configparser.ConfigParser()
            config.read('config.ini')
            return config.get(section, key, fallback=default)
        return cls._instance.config.get(section, key, fallback=default)

    def update_config_file(self, gui_window):
        # Define the required sections and fields
        required_fields = {
            'config': {
                'ip_address': '127.0.0.1',
                'width': '1150',
                'height': '1150',
                'monitor': '1', # Default monitor to 1
                'titlebar': 'True',
                'cp_integration': 'False',
                'version': self.__version__,
                'author': self.__author__,
                'email': self.__email__,
                'path_to_cp_scores': 'C:\\force\\gui\\',
                'extra_data': 'False' # For future use, if needed
            },
            'simsettings': {
                'sim-1': '127.0.0.1',
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
                print(f"CM Line {inspect.currentframe().f_lineno} Config file created with all default settings at {self.config_file}.")
                logging.info(f"CM Line {inspect.currentframe().f_lineno} Config file created with all default settings at {self.config_file}.")
            else:
                self.config.read(self.config_file) # Read the existing config file
                existing_version = self.config['config'].get('version')
                current_version_parts = self.__version__.split(".")
                existing_version_parts = existing_version.split(".")
                if existing_version != self.__version__ and existing_version != None: # Check if the existing version matches the current version
                    if current_version_parts[1] != existing_version_parts[1]:
                        response = gui_window.show_version_update_message(existing_version, self.__version__)  # Call the method in the GUI class to show the message
                        if response:self.task_queue.put(('delete_db', ()))  # If OK was clicked, proceed
                        else:
                            print(f"CM Line {inspect.currentframe().f_lineno} User canceled the version update. Exiting program.")
                            sys.exit()  # Quit the program
                    self.config['config']['version'] = self.__version__  # Update the version information
                    changes_made = True
                    print(f"CM Line {inspect.currentframe().f_lineno} Version updated from {existing_version} to {self.__version__}.")
                    logging.info(f"CM Line {inspect.currentframe().f_lineno} Version updated from {existing_version} to {self.__version__}.")
                        
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
                    print(f"CM Line {inspect.currentframe().f_lineno} Config file at {self.config_file} updated with missing fields.")
                    logging.info(f"CM Line {inspect.currentframe().f_lineno} Config file at {self.config_file} updated with missing fields.")
                    self.config.read(self.config_file) # Read the updated config file
                else: logging.info(f"CM Line {inspect.currentframe().f_lineno} All required fields are already present in the config file.")
                    
        except (configparser.Error, IOError) as e:
            print(f"CM Line {inspect.currentframe().f_lineno} An error occurred while ensuring required fields in the config file: {e}")
            logging.info(f"CM Line {inspect.currentframe().f_lineno} An error occurred while ensuring required fields in the config file: {e}")
            return None

    def add_comments(self): # Now, add comments manually after specific fields
        with open(self.config_file, 'r+') as configfile:
            lines = configfile.readlines()
            configfile.seek(0)
            for line in lines: 
                configfile.write(line)
                if line.strip().startswith('ip_address'):
                    configfile.write("; The IP address of currently monitored sim\n")
                elif line.strip().startswith('width'):
                    configfile.write("; Minimum height is 1150\n")
                elif line.strip().startswith('cp_integration'):
                    configfile.write("; Should be False, unless you have an external app that needs to read from files instead of DB (True/False)\n")
                elif line.strip().startswith('simsettings'):
                    configfile.write("; The name and IP address of all sims to monitored.\n")
            configfile.truncate()

    def read_cp_status(self):
        #config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file) #Read the existing config file
            return self.config.get('config', 'cp_integration', fallback='False').strip().lower() == 'true' # Return the data from the config and convert to boolean
        except (configparser.Error, IOError) as e:
            print(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
            logging.info(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
            return None   
        
    def read_ip_address(self):
        #config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file) #Read the existing config file
            return self.config['config']['ip_address'] # Return the IP address from the config
        except (configparser.Error, IOError) as e:
            print(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
            logging.info(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
            return None
        
    def read_config_file(self):
        #config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file) #Read the existing config file

            return self.config
        except (configparser.Error, IOError) as e:
            print(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
            logging.info(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
            return None

    def update_ip_address(self, new_ip):
        config = configparser.ConfigParser()
        config.read('config.ini')
        config.set('config', 'ip_address', new_ip)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)

    def cp_enabled(self, value):
        if value == "check":
            return self.read_cp_status()
        elif value == True:
            self.config.set('config', 'cp_integration', 'True')
        elif value == False:
            self.config.set('config', 'cp_integration', 'False')
        with open(self.config_file, 'w') as configfile:
            self.config.write(configfile)

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
    write_cp_all_signal = pyqtSignal(object)
    load_sessionid_on_start_signal = pyqtSignal(object)
    write_cp_signal = pyqtSignal(object, object)
    load_highscores_on_start_signal = pyqtSignal(object)
    highscore_data_loaded_signal = pyqtSignal(object)
    send_recordlaps_signal = pyqtSignal(object)
    drivers_signal = pyqtSignal(object)

    def __init__(self, task_queue, config_manager):
        super().__init__()
        self.task_queue = task_queue
        self.running = True
        self.config_manager = config_manager
        self.db_name = 'RaceDB.db'
        self.conn = None
        self.ip_name_flag = {}  # Store ip_name_flag for human driver detection

    def run(self):
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        #self.cursor.execute('PRAGMA foreign_keys = ON')  # Enable foreign key constraints
        self.create_database()
        #self.migrate_laps_table()
        while self.running:
            try:
                operation, args = self.task_queue.get()
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Operation: {operation} Args: {args}")
                print(f"DB Line {inspect.currentframe().f_lineno}  Queue Called: {operation} ")
                if operation == 'stop':
                    self.running = False
                    self.conn.close()  # Close the connection after the race ends
                    self.conn = None
                    break
                else: self.process_queue(operation, *args)
            except Exception as e: logging.error(f"DB Line {inspect.currentframe().f_lineno} Unpack failed: Operation: {operation} Message: {e}")
            finally: 
                self.task_queue.task_done()

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
            elif operation == 'get_record_laps': self.get_record_laps(*args)
            elif operation == 'get_recent_session_participants': self.get_recent_session_participants(*args)
            elif operation == 'check_session_has_races': self.check_session_has_races(*args)
            elif operation == 'update_ip_name_flag': self.update_ip_name_flag(*args)
            else: 
                logging.error(f"DB Line {inspect.currentframe().f_lineno} Unknown operation: {operation}")
                print(f"DB Line {inspect.currentframe().f_lineno} Unknown operation: {operation}")

        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Operation failed: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} Operation failed: {e}")
                
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
                FOREIGN KEY (RaceID, mName) REFERENCES Participants(RaceID, mName) ON DELETE CASCADE,
                FOREIGN KEY (RaceID) REFERENCES Races(RaceID) ON DELETE CASCADE
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
            print(f"DB Line {inspect.currentframe().f_lineno} Database file {self.db_name} deleted.")
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Database file {self.db_name} deleted.")
        else:
            print(f"DB Line {inspect.currentframe().f_lineno}  file {self.db_name} does not exist.")
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Database file {self.db_name} does not exist.")

        # Recreate the database (reopen connection and reinitialize)
            # Reopen the database connection
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()    
        self.create_database()
        self.conn.commit()

    def load_score_data(self,session_id):
        try:
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Executing race query for get score data ...")
            self.cursor.execute('''
                SELECT *
                FROM Races
                WHERE SessionID = ?
           
           ''', (session_id,))
            
            race_table = self.cursor.fetchall()
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Race table with  session id: {session_id} fetched.")
            race_ids = [race[0] for race in race_table]  # This will give you a list of all race IDs
            logging.info(f"DB Line {inspect.currentframe().f_lineno} List of all Race_ids: {race_ids}")
            if not race_ids: # Check if race_ids is empty
                print(f"DB Line {inspect.currentframe().f_lineno} Race_ids fetched: {race_ids}")  # Debugging output
                logging.info(f"DB Line {inspect.currentframe().f_lineno} check if race id's are empty Race_ids fetched: {race_ids}")
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No Race id's, emitting None")
                self.score_data_signal.emit(None, None, None)
                return
            query = '''
                SELECT *
                FROM laps
                WHERE RaceID IN ({})
            '''.format(','.join('?' * len(race_ids)))
            self.cursor.execute(query, race_ids)
            laps = self.cursor.fetchall()
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Laps fetched with Race Ids: {race_ids}")
            if not laps:
                print(f"DB Line {inspect.currentframe().f_lineno} No scores found, emitting None.")
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No scores found, emitting None.")
                self.score_data_signal.emit(None, None, None)
                return
            query = '''
                SELECT *
                FROM participants
                WHERE RaceID IN ({})
            '''.format(','.join('?' * len(race_ids)))
            self.cursor.execute(query, race_ids)
            participants = self.cursor.fetchall()
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Participants for the given race_ID: {race_ids} fetched.")
            if not participants:
                print(f"DB Line {inspect.currentframe().f_lineno} No participants found, emitting None.")
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No best laps list found, emitting None.")
                self.score_data_signal.emit(None, None, None)
                return
            if laps and race_table and participants:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Emitting score data signal")
                self.score_data_signal.emit(race_table, participants,laps,)

                read_cp_status = ConfigManager.get_config_value('cp_integration', 'config', 'False').strip().lower() == 'true'
                print(f"DB Line {inspect.currentframe().f_lineno} Read CP Status: {read_cp_status}")
                if read_cp_status:
                    self.write_cp_all_signal.emit(participants)

            else:
               logging.info(f"DB Line {inspect.currentframe().f_lineno} No laps, race_tables or participants found, emitting None")
               self.score_data_signal.emit(None, None, None)
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Database operation failed: {e}")
            self.score_data_signal.emit(None, None, None)

    def delete_race(self, race_id, callback):
        try:
            print(f"DB Line {inspect.currentframe().f_lineno} Raceid to delete: {race_id}")
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Race_iD Race_ID: {race_id}")
            self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
            self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
            self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
            self.conn.commit()
            if callback:
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} Callback {race_id}")
                    callback(race_id)  # Pass the deleted race_id back to the main thread
            else:
                if callback:
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} Callback None")
                    callback(None)  # No race found
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Database operation failed: {e}")
            if callback:
                callback(None)

    def delete_driver(self, driver_name, callback):
        try:
            self.cursor.execute('DELETE FROM Drivers WHERE Name = ?', (driver_name,))
            self.conn.commit()
            if callback:
                callback(driver_name)  # Pass the deleted driver name back to the main thread
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Database operation failed: {e}")
            if callback:
                callback(None)

    def load_driver_statistics_on_start(self):
        logging.info(f"DB Line {inspect.currentframe().f_lineno} Load driver statistics on start")
        print(f"DB Line {inspect.currentframe().f_lineno} DB Load driver statistics on start")
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
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Database operation failed: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} Load Driver Statistics failed: {e}")
            self.drivers_signal.emit(None)
    
    def get_record_laps(self, track):
        try:
            self.cursor.execute('''
                SELECT Name, Lapnumber, BestLap, MTrackvariation, mCarName
                FROM HighScore
                WHERE mTrackvariation = ?
                ORDER BY BestLap ASC
            ''', (track,))
            track_scores = self.cursor.fetchall()
            # Dictionary to store best lap times
            best_laps = {}

 
            # Process each record
            for record in track_scores:
                driver_name, _, best_lap, _, car_name = record  # Unpack tuple
                best_lap = float(best_lap)  # Ensure lap time is float
                
                # Update if car not seen or new lap time is better
                if car_name not in best_laps or best_lap < best_laps[car_name]['worldrecord']:
                    best_laps[car_name] = {
                        'worldrecord': best_lap,
                        'recorddriver': driver_name
                    }
            if best_laps:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} High Scores found, emitting signal")
                self.send_recordlaps_signal.emit(best_laps)
            else:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No High Scores found, emitting None")
                self.send_recordlaps_signal.emit(None)
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Database operation failed: {e}")
            self.send_recordlaps_signal.emit(None)

    def load_highscores(self, car, track):
        print(f"DB Line {inspect.currentframe().f_lineno} Load High Scores: Track: {track} Car: {car}")
        try:
            self.cursor.execute('''
                SELECT Name, lapnumber, BestLap, mTrackvariation, MCarName
                FROM HighScore
                WHERE mTrackvariation = ? AND MCarName = ?
                ORDER BY BestLap ASC
            ''', (track, car))
            high_scores = self.cursor.fetchall()
            print(f"DB Line {inspect.currentframe().f_lineno} High Scores fetched. ")
            logging.info(f"DB Line {inspect.currentframe().f_lineno} High Scores fetched: ")
            if high_scores:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} High Scores found, emitting signal")
                self.highscore_data_loaded_signal.emit(high_scores)
            else:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No High Scores found, emitting None")
                self.highscore_data_loaded_signal.emit(None)  # Emit None if no high scores found
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} operation failed: {e}")
            self.highscore_data_loaded_signal.emit(None)  # Emit None if an error occurs

    def load_highscores_on_start(self):
        try:
            self.cursor.execute('''
                SELECT Name, lapnumber, BestLap, mTrackvariation, MCarName
                FROM HighScore
                ORDER BY mTrackvariation ASC
            ''')
            high_scores = self.cursor.fetchall()
            logging.info(f"DB Line {inspect.currentframe().f_lineno} High Scores fetched: ")
            if high_scores:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} High Scores found, emitting signal")
                self.load_highscores_on_start_signal.emit(high_scores)
            else:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No High Scores found, emitting None")
                self.load_highscores_on_start_signal.emit(None)
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} operation failed: {e}")
            self.load_highscores_on_start_signal.emit(None)

    def load_race_data_on_start(self, callback=None):
        print(f"DB Line {inspect.currentframe().f_lineno} Load race data on start def entered")
        race_deleted = False
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
                        race_deleted = True
                        print(f"DB Line {inspect.currentframe().f_lineno} Raceid to delete: {race_id}")
                        logging.info(f"DB Line {inspect.currentframe().f_lineno} No Rows or participants, DB Race id to delete: {race_id}")
                        self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
                        self.conn.commit() 
                        print(f"DB Line {inspect.currentframe().f_lineno} No laps or participants, race deleted with race_id:{race_id}")
                        logging.info(f"DB Line {inspect.currentframe().f_lineno} No laps or participants, race deleted with race_id:{race_id}")
                if race_deleted:
                    self.cursor.execute('''
                        SELECT RaceID, mTranslatedTrackVariation, mLapsInEvent, RaceDate
                        FROM Races
                        ORDER BY RaceID ASC
                    ''')
                    races = self.cursor.fetchall()                        
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Load race data on start all Races: ")
                self.cursor.execute('''
                    SELECT RaceID, mCarNames
                    FROM Participants
                    ORDER BY RaceID ASC
                ''')
                participants = self.cursor.fetchall()
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Paticipants carNames and RaceID fetched.")
                if participants:
                    self.load_race_on_start_signal.emit(races,participants) # Emit the signal with the results in the main thread
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} Load race on start signal emitted")
                else:
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} No participants found, emitting None")
                    print(f"DB Line {inspect.currentframe().f_lineno} No participants found, emitting None")
                    self.load_race_on_start_signal.emit(None, None)
            else:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No races found, emitting None")
                print(f"DB Line {inspect.currentframe().f_lineno} No races found, emitting None")
                self.load_race_on_start_signal.emit(None, None)
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Database operation failed: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} Load Race on start failed:  {e}")
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
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Load session id on start fetched from Races")
            sessionids = [sessionid[0] for sessionid in sessionids]
            if sessionids:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Session ID valid, emitting signal")
                self.load_sessionid_on_start_signal.emit(sessionids) # Emit the signal with the results in the main thread
            else:
                print(f"DB Session ID not fetched: {sessionids}")
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Session ID not fetched: {sessionids}, emitting empty list")
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
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Load selected race: {race}")
            if race:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Race valid, fetching participants and laps with raceID: {race[0]}")
                self.cursor.execute('''
                    SELECT mName, mRacePosition, mFastestLapTimes, mLastLapTimes, mCarNames, flags, PitStops
                    FROM Participants
                    WHERE RaceID = ?
                    ORDER BY mRacePosition ASC
                ''', (race[0],))
                participants = self.cursor.fetchall()
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Load selected race participants fetched with raceID:{race[0]}")
                
                self.cursor.execute('''
                    SELECT LapID, RaceID, mName, LapNumber, LapTime
                    FROM Laps
                    WHERE RaceID = ?
                ''', (race[0],))
                laps = self.cursor.fetchall()
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Load selected race laps for race: {race[0]} fetched")
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Load selected race signal emitted") # Call the callback with the fetched data
                self.race_data_loaded_signal.emit(race, participants, laps)
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} operation failed: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} Load Selected Races failed: {e}")
            if callback: callback(None)
            
    def get_latest_session_id(self, callback=None):
        try:
            self.cursor.execute('SELECT MAX(SessionID) FROM Races')
            result = self.cursor.fetchone()
            session_id = result[0]
            self.cursor.execute('select MAX(RaceDate) from Races')
            result = self.cursor.fetchone()
            dato = result[0]
            logging.info(f"DB Line {inspect.currentframe().f_lineno} DB  Date result: {dato}")
            logging.info(f"DB Line {inspect.currentframe().f_lineno} DB Session ID result: {session_id}")
            if session_id:
                if callback:
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} Invoking callback with session_id")
                    callback(session_id, dato)
            else:
                if callback:
                    print(f"DB Line {inspect.currentframe().f_lineno} No Session ID. Invoking callback with session_id None")
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} No Session ID. Invoking callback with session_id None")
                    callback(None, None)
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Database operation failed: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} Database operation get_latest_session_id failed: {e}")
            if callback:
                callback(None, None)
                print(f"DB Line {inspect.currentframe().f_lineno}  no session stored, sending none: {e}")
                logging.info(f"DB Line {inspect.currentframe().f_lineno} no session stored, sending none: {e}")
                
    def get_latest_race_id(self, callback =None):
        try:
            self.cursor.execute('SELECT RaceID FROM Races ORDER BY RaceID DESC LIMIT 1')
            result = self.cursor.fetchone()
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Last RaceID in races, Result: {result}")
            if result:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Result is valid")
                last_race_id = result[0]  # Extract the RaceID from the tuple
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Result valid, calling back last_race_id:{last_race_id}")
                if callback and callable(callback): callback(last_race_id)
                else: 
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} No Callback, returning Rac_id: {last_race_id}")
                    return last_race_id  # Return the race ID if no valid callback is provided

            else:
                return None  # Return None if no race ID was found
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} operation failed: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} operation failed: {e}")
            if callback and callable(callback):callback(None) 

    def write_race(self, data, session_id):
        try:
            track_info = f"{data['eventInformation']['mTranslatedTrackLocation']} - {data['eventInformation']['mTranslatedTrackVariation']}" # Concatenate mTranslatedTrackLocation and mTranslatedTrackVariation
            logging.info(f"DB Line {inspect.currentframe().f_lineno} track_info to write:{track_info}")
            print(f"DB Line {inspect.currentframe().f_lineno} track_info to write:{track_info}")
            self.cursor.execute('''
                INSERT OR IGNORE INTO Races (mTranslatedTrackVariation, mLapsInEvent, SessionID)
                VALUES (?, ?, ?)
            ''', (track_info, data['eventInformation']['mLapsInEvent'], session_id,))
            # write drivers
            for participant in data['participants']['mParticipantInfo']:
                if participant['mName'].endswith("(AI)"):
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} Skipping AI driver: {participant['mName']}")
                    print(f"DB Line {inspect.currentframe().f_lineno} Skipping AI driver: {participant['mName']}")
                    continue
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
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Race Written to DB")
            print(f"DB Line {inspect.currentframe().f_lineno} Race Written to DB")
            self.conn.commit()
        except Exception as e:
            print(f"DB Line {inspect.currentframe().f_lineno} Failed to write race data to the database: Program Crash! {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            self.conn.close()  # Ensure the connection is closed
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")
            
    def insert_lap_data(self, race_id, name, current_lap, lap_time, track, car):
        print(f"DB Line {inspect.currentframe().f_lineno}  Insert Lap DATA entered")
        try:
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Def insert lap data entered, data to be written:Race_id:{race_id}, p_name:{name}, lap:{current_lap}, lap time:{lap_time}")
            
            # Check if driver is AI using multiple methods:
            # 1. Traditional method: name ends with "(AI)" (works for multiplayer)
            if name.endswith("(AI)"):
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Lap not written (AI) - detected by (AI) suffix")
                print(f"DB Line {inspect.currentframe().f_lineno} Lap not written (AI) - detected by (AI) suffix")
                return
            
            # 2. New method: check if driver is NOT in ip_name_flag human drivers (works for single player)
            if self.ip_name_flag:
                human_drivers = [driver_name for ip, (driver_name, in_race) in self.ip_name_flag.items() if in_race == 1]
                if name not in human_drivers:
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} Lap not written (AI) - {name} not in human drivers: {human_drivers}")
                    print(f"DB Line {inspect.currentframe().f_lineno} Lap not written (AI) - {name} not in human drivers: {human_drivers}")
                    return
                else:
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} Lap will be written for human driver: {name}")
                    print(f"DB Line {inspect.currentframe().f_lineno} Lap will be written for human driver: {name}")
            else:
                # Fallback: if ip_name_flag is not available, use traditional method only
                logging.warning(f"DB Line {inspect.currentframe().f_lineno} ip_name_flag not available, using traditional AI detection only")
                print(f"DB Line {inspect.currentframe().f_lineno} ip_name_flag not available, using traditional AI detection only")
            
            self.cursor.execute('''
                INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
                VALUES (?, ?, ?, ?)
            ''', (race_id, name, current_lap, lap_time))
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Lap data written")

            # Step 1: Get the driver by name
            self.cursor.execute('''
                SELECT Name
                FROM Drivers
                WHERE Name = ?
            ''', (name,))
            result = self.cursor.fetchone()

            logging.info(f"DB Line {inspect.currentframe().f_lineno} Driver name fetched: {result}")
            self.cursor.execute('''
                SELECT Phone FROM Drivers WHERE Name = ?
                ''', (name,))
            phone = self.cursor.fetchone()
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Phone number fetched: {phone}")
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
                        logging.info(f"DB Line {inspect.currentframe().f_lineno} HighScore updated with a new best lap time")
                else:
                    # Step 4: Insert a new high score if no record exists for this track and car
                    self.cursor.execute('''
                        INSERT INTO HighScore (phone, Name, lapnumber, BestLap, mTrackvariation, MCarName)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (phone, driver_name, current_lap, lap_time, track, car))
                    logging.info(f"DB Line {inspect.currentframe().f_lineno} New HighScore inserted")
                
                # Commit the changes
                self.conn.commit()

        except Exception as e:
            print(f"DB Line {inspect.currentframe().f_lineno} Failed to write Lap data to the database: Program Crash! {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            self.conn.close()  # Ensure the connection is closed
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")
            
    def finalize_race(self, data, lap_times_dict, flags_dict, pit_stops_dict):
        try:
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Def finalize entered")
            participants = data['participants']['mParticipantInfo']
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Finalizing DB, Lap times dict:{lap_times_dict} flags: {flags_dict}")    
            race_id = self.get_latest_race_id() # Get the RaceID for the last
            print(f"DB Line {inspect.currentframe().f_lineno} Finalizing Race with Race ID: {race_id}")
            self.cursor.execute('SELECT COUNT(*) FROM Laps WHERE RaceID = ?', (race_id,)) # Check if there are any laps recorded for the last RaceID
            rows_in_race = self.cursor.fetchone()[0]  # This will give the count of laps
            if rows_in_race == 0:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} No rows, returning")
                print(f"DB Line {inspect.currentframe().f_lineno} No Rows in DB, returning")
                return
            driver_total_times_dict = {}
            for driver, lap_times in lap_times_dict.items():
                driver_total_times_dict[driver] = sum(lap_times)
            ranked_drivers = self.calculate_score(participants, flags_dict, driver_total_times_dict)
            print(f"DB Line {inspect.currentframe().f_lineno} Ranked Drivers: {ranked_drivers}")
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
            '''
            read_cp_status = self.config_manager.read_cp_status()
            print(f"DB Line {inspect.currentframe().f_lineno} Read CP Status: {read_cp_status}")
            if read_cp_status:
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Emitted write_cp_signal")
                self.write_cp_signal.emit(ranked_drivers, lap_times_dict)
            '''
        except Exception as e:
            print(f"DB Line {inspect.currentframe().f_lineno} Failed to Finalize race data to the database: {e}")
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
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Ranked drivers: {ranked_drivers}")
            return ranked_drivers

    def get_recent_session_participants(self, callback=None):
        """Get participants from the most recent race to compare with current race participants"""
        try:
            conn = sqlite3.connect('RaceDB.db')
            cursor = conn.cursor()
            
            # Get the most recent race and its participants
            cursor.execute('''
                SELECT SessionID, 
                    GROUP_CONCAT(DISTINCT mName) as participants
                FROM Races r
                JOIN Participants p ON r.RaceID = p.RaceID
                WHERE r.RaceID = (SELECT MAX(RaceID) FROM Races)
                GROUP BY SessionID
                ORDER BY r.RaceDate DESC
                LIMIT 1
            ''')
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                session_id, participants_str = result
                participants = participants_str.split(',') if participants_str else []
                print(f"DB Line {inspect.currentframe().f_lineno} Recent session {session_id} participants: {participants}")
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Recent session {session_id} participants: {participants}")
                if callback:
                    callback((session_id, participants))
                return session_id, participants
            else:
                print(f"DB Line {inspect.currentframe().f_lineno} No recent participants found")
                if callback:
                    callback((None, []))
                return None, []
                
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Error getting recent participants: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} Error getting recent participants: {e}")
            if callback:
                callback((None, []))
            return None, []

    def check_session_has_races(self, session_id, callback=None):
        """Check if a session has any races"""
        try:
            conn = sqlite3.connect('RaceDB.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM Races WHERE SessionID = ?', (session_id,))
            count = cursor.fetchone()[0]
            conn.close()
            
            has_races = count > 0
            print(f"DB Line {inspect.currentframe().f_lineno} Session {session_id} has {count} races: {has_races}")
            logging.info(f"DB Line {inspect.currentframe().f_lineno} Session {session_id} has {count} races: {has_races}")
            
            if callback:
                callback(has_races)
            return has_races
                
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} Error checking session races: {e}")
            print(f"DB Line {inspect.currentframe().f_lineno} Error checking session races: {e}")
            if callback:
                callback(False)
            return False

    def update_ip_name_flag(self, ip_name_flag):
        """Update the stored ip_name_flag for human driver detection"""
        self.ip_name_flag = ip_name_flag
        human_drivers = [name for ip, (name, in_race) in ip_name_flag.items() if in_race == 1]
        print(f"DB Line {inspect.currentframe().f_lineno} Updated ip_name_flag: {len(human_drivers)} human drivers detected: {human_drivers}")
        logging.info(f"DB Line {inspect.currentframe().f_lineno} ip_name_flag updated with {len(human_drivers)} human drivers: {human_drivers}")

    def stop(self):
        self.running = False
        self.task_queue.put(('stop', None))
        if hasattr(self, 'session') and self.session:
            self.session.close()  # Safely close the session
        self.quit()  # Stop the event loop if it's running
        self.wait()  # Wait until the thread has fully exited        
        
class ControlPanel(QObject):
    #driver_sims_updated = pyqtSignal(dict)  # Signal to update driver sims

    def __init__(self, db_thread, config_manager, gui_main_app, race_app=None):
        super().__init__()
        self.running = True
        self.config_manager = config_manager
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.file_path = self.config['config']['path_to_cp_scores'] + 'score.txt'
        self.best_lap_file_path = self.config['config']['path_to_cp_scores'] + 'bestlap.txt'
        self.driver_file_path = self.config['config']['path_to_cp_scores'] + 'drivers.txt'
        self.db_thread = db_thread
        self.gui_main_app = gui_main_app
        self.race_app = race_app

        # Signalling
        self.db_thread.write_cp_signal.connect(self.process_signal)
        self.db_thread.write_cp_all_signal.connect(self.process_all_signal)
        
    def connect_signals(self, race_app):
        self.race_app = race_app
        #self.race_app.get_request_for_sim_signal.connect(self.process_sim_signal)

    '''    
    def process_sim_signal(self):
        print(f"CP Line {inspect.currentframe().f_lineno} Process Sim Signal entered")
        driver_names = self.read_driver_names(self.driver_file_path)
        # Match position of driver name with sim
        driver_names_dict = {}
        for index, driver in enumerate(driver_names, start=1):
            # Create key-value pair: driver name -> Sim-[index]
            driver_names_dict[driver.strip()] = f"{index}"
        self.driver_sims_updated.emit(driver_names_dict)
        '''
    
    def process_all_signal(self, participants):
        print(f"CP Line {inspect.currentframe().f_lineno} Process all Signals entered")
        """
        Process all participants, grouped by race_id, write their scores to the score file,
        and write the best lap driver for each race to the bestlap.txt file.
        """
        # Read the driver names from the drivers.txt file
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            if os.path.exists(self.best_lap_file_path):
                os.remove(self.best_lap_file_path)
        except PermissionError as e:
            logging.error(f"CP Line {inspect.currentframe().f_lineno} Failed to delete file {self.best_lap_file_path}: {e}")
            print(f"CP Line {inspect.currentframe().f_lineno} Failed to delete file {self.best_lap_file_path}: {e}")

        driver_names = self.read_driver_names(self.driver_file_path)

        # Group participants by race_id using a dictionary
        race_groups = {}
        for participant in participants:
            race_id = participant[0]  # race_id is at index 0
            if race_id not in race_groups:
                race_groups[race_id] = []
            race_groups[race_id].append(participant)
        # Print the number of groups found
        print(f"CP Line {inspect.currentframe().f_lineno} Number of groups (unique race_ids) found: {len(race_groups)}")

        # Iterate over each race_id and its participants
        for race_id, race_participants in race_groups.items():
            # Initialize a list to store the scores for this race
            race_scores = []

            # Find the participant with the best lap time
            best_lap_participant = min(
                race_participants,
                key=lambda p: p[4] if p[4] is not None and p[4] > 0 else float('inf'),
                default=None
            )

            # Extract the best lap driver name
            if best_lap_participant:
                best_lap_driver = best_lap_participant[1]
            else:
                best_lap_driver = None

            # Iterate over each driver in the drivers.txt file
            for driver in driver_names:
                # Find the driver in the participants list
                driver_found = False
                for participant in race_participants:
                    if participant[1] == driver:  # Driver's name is at index 1
                        print(f"CP Line {inspect.currentframe().f_lineno} Driver found: {driver} Race Score: {participant[9]}")
                        # If the driver is found, append their mRacePosition (index 3) to the scores
                        race_scores.append(participant[9])
                        driver_found = True
                        break

                # If the driver is not found, append 0 to the scores
                if not driver_found:
                    # print(f"CP Line {inspect.currentframe().f_lineno} Driver not found: {driver}")
                    race_scores.append(0)

            # Write the race results to the score file
            self.write_race_results({name: score for name, score in zip(driver_names, race_scores)}, self.file_path)

            # Write the best lap driver to the bestlap.txt file
            if best_lap_driver:
                self.write_best_lap_driver(best_lap_driver, self.best_lap_file_path)

        logging.info(f"CP Line {inspect.currentframe().f_lineno} process_all_signal completed")
        print(f"CP Line {inspect.currentframe().f_lineno} process_all_signal completed")

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
        logging.info(f"CP Line {inspect.currentframe().f_lineno} process signal completed")
        print(f"CP Line {inspect.currentframe().f_lineno} process signal completed")
            
    def read_driver_names(self, file_path):
        with open(file_path, 'r') as f:
            line = f.readline().strip()
            driver_names = line.split(';')
            driver_names = [name.split(' (')[0].strip() for name in driver_names if name.strip()]  # Remove empty entries
            print(f"CP Line {inspect.currentframe().f_lineno} Driver names read from file: {driver_names}")
            logging.info(f"CP Line {inspect.currentframe().f_lineno} Driver names read from file: {driver_names}")
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
        print(f"CP Line {inspect.currentframe().f_lineno} Race results written to file.")
        logging.info(f"CP Line {inspect.currentframe().f_lineno} Race results written to file.")

    def write_best_lap_driver(self,best_driver, file_path):
        if best_driver: # Write the best lap driver to the specified file
            with open(file_path, 'a') as f:
                f.write(best_driver + '\n')
            print(f"CP Line {inspect.currentframe().f_lineno} Best lap driver written to file.")
            logging.info(f"CP Line {inspect.currentframe().f_lineno} Best lap driver written to file.")
    def stop(self):
        self.running = False
        self.session.close()
        self.quit()
        self.wait()        
        
class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal(object, object)
    qualify_finished = pyqtSignal()
    practice_finished = pyqtSignal()
    flags_updated = pyqtSignal(dict)
    initialize = pyqtSignal()
    change_tab_signal = pyqtSignal(int)  # Signal to change the tab in the GUI
    api_signal_status_updated = pyqtSignal(bool, str)  # Signal to update API status
    ip_address_updated = pyqtSignal(str) # Signal to update IP address
    race_message_updated = pyqtSignal(str) # Signal to update label text
    session_type_updated = pyqtSignal(str)  # Signal to indicate time trial detection
    active_computers_signal = pyqtSignal(dict)  # Signal to update active computers
    multi_data_signal = pyqtSignal(dict)  # Signal to update multi data
    auto_session_assigned_signal = pyqtSignal(int)  # Signal for automatic session assignment
    session_id_updated = pyqtSignal(int)  # Signal to update session ID
    
    def __init__(self, gui_main_app, tab_widget, task_queue, config_manager, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_manager = config_manager
        self.ip_address = self.config_manager.read_ip_address()
        self.gui_main_app = gui_main_app
        self.task_queue = task_queue
        self.tab_widget = tab_widget

        # Variabler
        self.previous_game_state = None
        self.previous_race_state = None
        self.previous_session_state = None
        self.running = True
        self.first_time_run = True
        self.race_id = 0
        self.race_may_not_be_finished = False
        self.session_id = 0
        self.session = None
        self.pit_stops_dict = {}
        self.previous_ipaddress = None
        self.connecton_restored_message_shown = False

        self.init_signals()

    
    def connect_race_app(self, race_app):
        self.race_app = race_app
        self.race_app.pit_stops_updated.connect(self.update_pit_stops)    
    
    def init_signals(self):
        # Remove old GA connection - MT now owns session management
        # self.gui_main_app.session_id_updated.connect(self.set_session_id)
        self.gui_main_app.delete_flag.connect(self.delete_flag)
        # Connect to button signals for session control
        if hasattr(self.gui_main_app, 'update_session_id_from_button'):
            self.gui_main_app.update_session_id_from_button.connect(self.set_session_id_from_button)

    def run(self):
        # Start the asyncio event loop in this thread
        self.task_queue.put(('get_latest_session_id', (self.set_session_id,)))
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_main_loop())  # Run your async method
        loop.close()
        
    async def run_main_loop(self):
        race_not_finished_message_shown = False
        index = 0
        #self.ip_address = self.config_manager.read_ip_address()
        #self.ip_address_updated.emit(self.ip_address)
        asyncio.create_task(self.connection_monitor())
        #asyncio.create_task(self.auto_scan_active_computers())
        while self.running:
            try:
                if self.first_time_run and not self.race_may_not_be_finished: self.initialize.emit() #Load selected race after start.
                if not self.running: break
                if self.session is None: self.session = aiohttp.ClientSession()
                data = await self.get_api_data()
                await asyncio.sleep(2)
                if not self.running: break
                # if self.session is not None: await self.session.close()
                # self.session = None
                if index % 50 == 0:
                    print(f"MT Line {inspect.currentframe().f_lineno} Waiting... Loop number {index}")
                # logging.info(f"MT Line {inspect.currentframe().f_lineno} Waiting... Loop number {index}")
                index += 1
                if data is None:
                    self.first_time_run = False
                    continue
                participants = data.get('participants', {}).get('mParticipantInfo', []) # Fetch participants data
                if not participants and self.first_time_run and not self.race_may_not_be_finished:
                    self.first_time_run = False
                    race_not_finished_message_shown = False
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} No participants found, Still waiting for race start.")
                    print(f"MT Line {inspect.currentframe().f_lineno} Waiting for race start.....")
                    index = 0
                    continue  # Restart loop if participants list is empty
                else:
                    if self.race_may_not_be_finished and participants:
                        if not race_not_finished_message_shown:
                            print(f"MT Line {inspect.currentframe().f_lineno} Race not finished yet....")
                            race_not_finished_message_shown = True
                        continue
                    if self.race_may_not_be_finished:
                        print(f"MT Line {inspect.currentframe().f_lineno} Race Finished!")
                        self.race_may_not_be_finished = False
                        continue

                if participants:
                    self.race_loop_first_time = True
                    self.first_time_run = False
                    self.race_in_session = True
                    self.change_tab_signal.emit(0)  # Switch to the first tab
                    await self.get_participants_ips(participants)
                    # Send ip_name_flag to database thread for human driver detection
                    self.task_queue.put(('update_ip_name_flag', (self.ip_name_flag,)))
                    asyncio.create_task(self.periodic_fetch_enriched_data())
                    # check if it is qualify or race or practice
                    if data['gameStates']['mSessionState'] == 3:
                        print(f"MT Line {inspect.currentframe().f_lineno} Qualifying Starting")
                        logging.info(f"MT Line {inspect.currentframe().f_lineno} Qualifying")
                        self.qualify = True
                        self.session_type_updated.emit("Qualifying")  # Emit signal to indicate qualifying session
                        await self.qualify_running(data) # Start the qualifying running loop
                        #self.race_message_updated.emit("Qualifying Finished...")
                        self.race_in_session = False
                        self.qualify_finished.emit()
                        qualifying_finished = True
                        print(f"MT Line {inspect.currentframe().f_lineno} Qualifying Finished")
                    elif data['gameStates']['mSessionState'] == 1:
                        print(f"MT  Line {inspect.currentframe().f_lineno} Practice Starting")
                        logging.info(f"MT Line {inspect.currentframe().f_lineno} Practice")
                        self.practice = True
                        self.session_type_updated.emit("Practice") 
                        await self.practice_running(data) # Start the practice running loop
                        self.race_in_session = False
                        self.practice_finished.emit()
                        practice_finished = True
                        print(f"MT Line {inspect.currentframe().f_lineno} Practice Finished")
                    else:
                        print(f"MT Line {inspect.currentframe().f_lineno} Starting Race Loop")
                        if data['eventInformation']['mLapsInEvent'] == 0: # If mLapsInEvent is 0, it means its a time trial.
                            print(f"MT Line {inspect.currentframe().f_lineno} Time Trial Detected")
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Time Trial Detected")
                            self.time_trial = True
                            self.session_type_updated.emit("TimeTrail") # Emit signal to indicate time trial detection
                        else:
                            self.time_trial = False
                            self.session_type_updated.emit("Race") # Emit signal to indicate normal Race.
                            print(f"MT Line {inspect.currentframe().f_lineno} Should now see me after race is finished!")
                        await self.race_running(data) # Start the race running loop
                        print(f"MT Line {inspect.currentframe().f_lineno} Race Loop Finished")
                        self.first_time_run = True
                        self.race_not_finished_message_shown = False
                        # Reset session logic: for single-driver races or new day check
                        if self.session_id == 1:
                            print(f"MT Line {inspect.currentframe().f_lineno} Post-race session reset: checking DB for session increment")
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Post-race session reset: session was 1, checking for increment")
                            self.task_queue.put(('get_latest_session_id', (self.set_session_id,)))
                
            except Exception as e:
                logging.error(f"MT Line {inspect.currentframe().f_lineno} An error occurred while monitoring race state: {e}")
                print(f"MT Line {inspect.currentframe().f_lineno} An error occurred while monitoring race state: {e}")
                await asyncio.sleep(5)   

    async def get_participants_ips(self, participants):
        """
        Queries all configured sim IPs and builds a mapping of IP -> [name, in_race].
        A name is flagged as in_race only if it exists in the provided participants list.
        All configured IPs are included, with fallback names like S-1, S-2 for unavailable ones.
        """
        ip_name_flag = {}  # Format: {"192.168.3.201": ["Fred", 1], "192.168.3.202": ["S-2", 0], ...}
        sim_ips = [ConfigManager.get_config_value(f"sim-{i}", "simsettings", "").strip()
                for i in range(1, 21)
                if ConfigManager.get_config_value(f"sim-{i}", "simsettings", "").strip()]

        participant_names = {p['mName'] for p in participants if p.get('mName')}

        async def fetch_data(ip):
            url = f"http://{ip}:8180/crest2/v1/api"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=1) as response:
                        if response.status == 200:
                            return ip, await response.json()
            except Exception as e:
                print(f"MT Line {inspect.currentframe().f_lineno} Error fetching from {ip}: {e}")
            return ip, None

        tasks = [fetch_data(ip) for ip in sim_ips]
        results = await asyncio.gather(*tasks)

        for sim_index, (ip, data) in enumerate(results):
            name = f"S-{sim_index+1}"
            in_race = 0

            if data is not None:
                participants_data = data.get('participants', {})
                viewed_index = participants_data.get('mViewedParticipantIndex', -1)
                infos = participants_data.get('mParticipantInfo', [])
                if 0 <= viewed_index < len(infos):
                    fetched_name = infos[viewed_index].get('mName')
                    if fetched_name:
                        name = fetched_name
                        if fetched_name in participant_names:
                            in_race = 1

            ip_name_flag[ip] = [name, in_race]

        self.active_computers_signal.emit(ip_name_flag)
        self.ip_name_flag = ip_name_flag  # Store the mapping for later use

    async def periodic_fetch_enriched_data(self):
        """
        Periodically fetch enriched race data while race is ongoing.
        """
        while self.race_in_session: 
            try:
                if hasattr(self, "ip_name_flag"):
                    await self.fetch_race_data_all_ips(self.ip_name_flag)
            except Exception as e:
                print(f"MT Line {inspect.currentframe().f_lineno} Error in periodic_fetch_enriched_data: {e}")
            await asyncio.sleep(2)          

    async def fetch_race_data_all_ips(self, ip_name_flag):
        """
        Fetches raw race data from all IPs marked as in_race in ip_name_flag.
        Emits a dictionary of format:
        {
            "192.168.3.201": <raw data dict from API>,
            ...
        }
        After 3 failed attempts, sets in_race = 0 for that IP.
        """
        failed_attempts = getattr(self, "_fetch_failures", {})

        async def fetch(ip):
            url = f"http://{ip}:8180/crest2/v1/api"
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=0.5) as response:
                        if response.status == 200:
                            if ip in failed_attempts:
                                del failed_attempts[ip]
                            return ip, await response.json()
            except Exception as e:
                print(f"MT Line {inspect.currentframe().f_lineno} Error fetching detailed race data from {ip}: {e}")

            failed_attempts[ip] = failed_attempts.get(ip, 0) + 1
            if failed_attempts[ip] >= 3:
                print(f"MT Line {inspect.currentframe().f_lineno} Marking {ip} as not in race after 3 failed attempts")
                if ip in self.ip_name_flag:
                    self.ip_name_flag[ip][1] = 0  # Set in_race = 0
            return ip, None

        tasks = [fetch(ip) for ip, (name, in_race) in ip_name_flag.items() if in_race]
        results = await asyncio.gather(*tasks)

        self._fetch_failures = failed_attempts  # Persist between calls

        dataset = {ip: data for ip, data in results if data is not None}
        #print(f"MT Line {inspect.currentframe().f_lineno} Fetched data from {len(dataset)} IPs")
        self.multi_data_signal.emit(dataset)

    def delete_flag(self, driver_name):
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Def delete_flag entered")
        print(f"MT Line {inspect.currentframe().f_lineno} Delete flag for driver: {driver_name}")
        if self.race_in_session:
            if driver_name in self.driver_flags:
                del self.driver_flags[driver_name]
                self.flags_updated.emit(self.driver_flags)  # Emit the updated flags dictionary
        else:
            print(f"MT Line {inspect.currentframe().f_lineno} Race not running, cannot delete flag for driver: {driver_name}")

    def set_race_id(self, latest_race_id):
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Def set_race_id entered")
        global app
        print(f"MT Line {inspect.currentframe().f_lineno} Fetch race ID after write Race. Race_id: {latest_race_id}")
        if latest_race_id is None:
            print(f"MT Line {inspect.currentframe().f_lineno} Race_id is None, program crash!")
            if app is not None:
                app.quit()  # Properly quit the application if an error occurs  
                raise ValueError("An error occurred")
        else:
            self.race_id = latest_race_id
            print(f"MT Line {inspect.currentframe().f_lineno} Monitorthread Race ID received from DB Race id: {self.race_id}")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Race ID received from DB Race id: {self.race_id}")

    def update_pit_stops(self, pit_stops_dict):
        self.pit_stops_dict = pit_stops_dict
        print(f"MT Line {inspect.currentframe().f_lineno} Pit stops updated: {self.pit_stops_dict}")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Pit stops updated: {self.pit_stops_dict}")

    def set_session_id_from_button(self, button):
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Def set_session_id entered")
        print(f"MT Line {inspect.currentframe().f_lineno} Set session ID from button entered Self.session_ID: {self.session_id} Button: {button}")
        if button is None:
            print(f"MT Line {inspect.currentframe().f_lineno} Should never happen: MT Session ID is None, setting to 1")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Should never happen: MT Session ID is None, setting to 1")
            self.task_queue.put(('get_latest_session_id', (self.set_session_id,)))
        else:
            if button == "increase":
                self.session_id += 1
            elif button == "decrease":
                self.session_id -= 1
            self.session_id_updated.emit(self.session_id)
            print(f"MT Line {inspect.currentframe().f_lineno} Monitorapp Session ID updated to {self.session_id}")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Monitorapp Session ID updated to {self.session_id}")

    def set_session_id(self, new_session_id, dato):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def set_session_id entered. new.session_id: {new_session_id}, dato: {dato}")
        print(f"GA Line {inspect.currentframe().f_lineno} Def set_session_id entered. new.session_id: {new_session_id}, dato: {dato}")
        
        if new_session_id is None:
            print(f"GA Line {inspect.currentframe().f_lineno} Session ID not found in the database, setting to 2")
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Session ID not found in the database, setting to 2")
            self.session_id = 2

        else:
            print(f"GA Line {inspect.currentframe().f_lineno} Session ID fetched: ({new_session_id})")
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Session ID fetched: ({new_session_id})")
            dato = datetime.strptime(dato, "%Y-%m-%d").date()
            if dato != datetime.now().date():
                logging.info(f"GA Line {inspect.currentframe().f_lineno} Date from DB: {dato}")
                print(f"GA Line {inspect.currentframe().f_lineno} Date from DB: {dato}")
                self.session_id = new_session_id + 1  # Increment session ID for new day
                logging.info(f"GA Line {inspect.currentframe().f_lineno} GA Session ID is not for today, setting to +1. Session ID: {self.session_id}")
                print(f"GA Line {inspect.currentframe().f_lineno} GA Session ID is not for today, setting to +1. Session ID: {self.session_id}")
                
                print(f"GA Line {inspect.currentframe().f_lineno} Session ID is not for today, setting to +1: self.sesssion_id: {self.session_id} ")
                # self.task_queue.put(('load_score_data',(self.session_id-1,))) # Get the score data for the current session ID
            else:
                self.session_id = new_session_id
                print(f"GA Line {inspect.currentframe().f_lineno} Session ID is for today, setting to {self.session_id} from DB.")
            self.session_id_updated.emit(self.session_id)
      
            # self.task_queue.put(('load_score_data',(new_session_id,))) # Get the score data for the last race current session ID
        
        self.session_id_updated.emit(self.session_id)               

    def calculate_session_id_for_participants(self, current_participants, ip_name_flag, previous_participants=None, session_has_races=False):
        """
        Automatically determine session ID based on number of human drivers:
        - Single human driver races always use session ID = 1
        - Multi-human driver races use current MT session ID (respects manual overrides and new day logic)
        - If >50% drivers different from previous race AND session has races → increment session ID
        Uses ip_name_flag to identify human drivers (including S-1, S-2, etc.)
        """
        try:
            # Extract human driver names from ip_name_flag (those currently in race)
            human_drivers = [name for ip, (name, in_race) in ip_name_flag.items() if in_race == 1]
            human_count = len(human_drivers)
            
            print(f"MT Line {inspect.currentframe().f_lineno} Human drivers detected: {human_drivers} (count: {human_count})")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Human drivers in race (including S-1, S-2, etc.): {human_drivers}")
            
            # Fallback: if ip_name_flag is empty or no drivers detected, fall back to old method
            if human_count == 0:
                print(f"MT Line {inspect.currentframe().f_lineno} No human drivers detected from ip_name_flag, falling back to participant list")
                logging.warning(f"MT Line {inspect.currentframe().f_lineno} ip_name_flag empty or no drivers detected, using fallback method")
                fallback_names = [p.get('mName', '') for p in current_participants if p.get('mName') and not p.get('mName', '').endswith('(AI)')]
                human_count = len(fallback_names)
                print(f"MT Line {inspect.currentframe().f_lineno} Fallback detected {human_count} human drivers: {fallback_names}")
            
            # Rule 1: Single human driver races always use session ID = 1
            if human_count == 1:
                calculated_session_id = 1
                print(f"MT Line {inspect.currentframe().f_lineno} Single human driver race - using session ID = 1")
                logging.info(f"MT Line {inspect.currentframe().f_lineno} Single human driver race ({human_drivers[0] if human_drivers else 'fallback'}) - using session ID = 1")
            
            # Rule 2: Multi-human driver races use current MT session ID
            elif human_count > 1:
                # Use MonitorThread's current session (respects manual increments and new day logic)
                calculated_session_id = self.session_id
                print(f"MT Line {inspect.currentframe().f_lineno} Multi-human driver race ({human_count} drivers) - using current MT session ID = {calculated_session_id}")
                logging.info(f"MT Line {inspect.currentframe().f_lineno} Multi-human driver race with {human_count} drivers - using current session ID = {calculated_session_id}")
                
                # Ensure minimum session ID of 2 for multi-driver races if somehow MT has session 1
                if calculated_session_id < 2:
                    calculated_session_id = 2
                    print(f"MT Line {inspect.currentframe().f_lineno} Adjusting multi-driver session from {self.session_id} to minimum = 2")
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} Multi-driver race adjusted to minimum session ID = 2")
                
                # Rule 4: Driver change detection (only if session has races and we have previous participants)
                if previous_participants and session_has_races:
                    if self.compare_driver_lists(human_drivers, previous_participants):
                        calculated_session_id += 1
                        print(f"MT Line {inspect.currentframe().f_lineno} Driver change >50% detected - incrementing session ID from {calculated_session_id-1} to {calculated_session_id}")
                        logging.info(f"MT Line {inspect.currentframe().f_lineno} Driver change >50% detected - session incremented from {calculated_session_id-1} to {calculated_session_id}")
            
            # Rule 3: No human drivers detected - fallback to session ID = 1
            else:
                calculated_session_id = 1
                print(f"MT Line {inspect.currentframe().f_lineno} No human drivers detected - fallback to session ID = 1")
                logging.warning(f"MT Line {inspect.currentframe().f_lineno} No human drivers detected - using fallback session ID = 1")
            
            # Emit signal and update MT session
            self.auto_session_assigned_signal.emit(calculated_session_id)
            self.session_id_updated.emit(calculated_session_id)
            return calculated_session_id
                
        except Exception as e:
            logging.error(f"MT Line {inspect.currentframe().f_lineno} Error calculating session ID: {e}")
            print(f"MT Line {inspect.currentframe().f_lineno} Error calculating session ID: {e}")
            # Fallback to current MT session or 1
            fallback_session = self.session_id if self.session_id > 0 else 1
            print(f"MT Line {inspect.currentframe().f_lineno} Using fallback session ID: {fallback_session}")
            self.auto_session_assigned_signal.emit(fallback_session)
            self.session_id_updated.emit(fallback_session)
            return fallback_session

    def compare_driver_lists(self, current_drivers, previous_drivers):
        """
        Compare two driver lists and return True if >50% different names.
        Handles name normalization (remove AI tags, trim whitespace).
        """
        try:
            # Normalize current drivers (remove AI tags, strip whitespace, convert to lowercase)
            normalized_current = set()
            for name in current_drivers:
                clean_name = name.split(' (')[0].strip().lower() if name else ""
                if clean_name:
                    normalized_current.add(clean_name)
            
            # Normalize previous drivers  
            normalized_previous = set()
            for name in previous_drivers:
                clean_name = name.split(' (')[0].strip().lower() if name else ""
                if clean_name:
                    normalized_previous.add(clean_name)
            
            # If either list is empty, consider it a significant change
            if not normalized_current or not normalized_previous:
                print(f"MT Line {inspect.currentframe().f_lineno} Empty driver list detected - considering as change")
                logging.info(f"MT Line {inspect.currentframe().f_lineno} Empty driver list detected (current: {len(normalized_current)}, previous: {len(normalized_previous)})")
                return False
            
            # Calculate overlap and difference percentage
            intersection = normalized_current.intersection(normalized_previous)
            total_unique = len(normalized_current.union(normalized_previous))
            overlap_percentage = len(intersection) / max(len(normalized_current), len(normalized_previous)) * 100
            difference_percentage = 100 - overlap_percentage
            
            is_significant_change = difference_percentage > 50
            
            print(f"MT Line {inspect.currentframe().f_lineno} Driver comparison - Current: {sorted(normalized_current)}, Previous: {sorted(normalized_previous)}")
            print(f"MT Line {inspect.currentframe().f_lineno} Overlap: {overlap_percentage:.1f}%, Difference: {difference_percentage:.1f}%, Significant change: {is_significant_change}")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Driver comparison - Overlap: {overlap_percentage:.1f}%, Difference: {difference_percentage:.1f}%, Change >50%: {is_significant_change}")
            
            return is_significant_change
            
        except Exception as e:
            logging.error(f"MT Line {inspect.currentframe().f_lineno} Error comparing driver lists: {e}")
            print(f"MT Line {inspect.currentframe().f_lineno} Error comparing driver lists: {e}")
            return False
    
    async def cache_api_data(self):
        while self.start_cache_data:  # Loop until the cache is stopped
            await asyncio.sleep(self.fetch_api_delay)  # Sleep for a short duration to avoid busy-waiting
            self.cached_data = await self.get_api_data()  # Fetch the API data
        print(f"MT Line {inspect.currentframe().f_lineno} Cache API data stopped.")

    async def get_api_data(self):
        def _handle_restore():
            if not self.connecton_restored_message_shown:
                logging.info(f"MT Line {inspect.currentframe().f_lineno}MT: Connection Restored")
                print(f"MT Line {inspect.currentframe().f_lineno}MT: Connection Restored")
                self.api_signal_status_updated.emit(False, "")
                self.connecton_restored_message_shown = True

        async def _handle_error(msg, sleep=5, exception=None):
            if not self.connecton_restored_message_shown:
                print(f"MT Line {inspect.currentframe().f_lineno}MT: {msg}")
                logging.error(f"MT Line {inspect.currentframe().f_lineno}MT: {msg}" + (f" - {exception}" if exception else ""))
                self.api_signal_status_updated.emit(True, msg)
                self.connecton_restored_message_shown = False
            await asyncio.sleep(sleep)

        def _update_state(label, current):
            attr = f"previous_{label.lower()}_state"
            prev = getattr(self, attr)
            if current != prev:
                print(f"MT Line {inspect.currentframe().f_lineno}MT: {label} state changed to {current}")
                logging.info(f"MT Line {inspect.currentframe().f_lineno}MT: {label} state changed to {current}")
                setattr(self, attr, current)

        if not self.running:
            return
        self.no_server_connection = True
        self.session = self.session or aiohttp.ClientSession()
        error_message_shown = False
        try:
            async with self.session.get(f"http://{self.ip_address}:8180/crest2/v1/api", timeout=3) as r:
                if r.status != 200:
                    if not error_message_shown:
                        error_message_shown = True
                        self.connecton_restored_message_shown = False
                    return await _handle_error(f"Game Not Started: Unexpected status code {r.status}", sleep=5)

                data = await r.json()
                if data is None:
                    raise ValueError("MT Received None as data. Possible issue with API response.")

                _handle_restore()
                self.no_server_connection = False

                for k in ["Game", "Race", "Session"]:
                    _update_state(k, data["gameStates"][f"m{k}State"])

                return data if self.running else None

        except asyncio.CancelledError:
            logging.info(f"MT Line {inspect.currentframe().f_lineno}MT: Operation cancelled")

        except ValueError as ve:
            if not error_message_shown:
                error_message_shown = True
                self.connecton_restored_message_shown = False
            return await _handle_error(f"Error parsing JSON: {ve}", sleep=2)

        except Exception as e:
            if not error_message_shown:
                error_message_shown = True
                self.connecton_restored_message_shown = False
            return await _handle_error("Connection Error: Check IP Address in Config.ini:", sleep=5, exception=e)

        finally:
            self.no_server_connection = True
            if self.ip_adress_changed and self.session:
                try: await self.session.close()
                except Exception as e: logging.error(f"Error closing session: {e}")
                self.session = None
                self.ip_adress_changed = False
 
    async def connection_monitor(self):
        last_scan_time = time.monotonic() - 360000  # Initialize last scan time to 60 minutes ago
        print(f"MT Line {inspect.currentframe().f_lineno} Connection Monitor started with Last Scan Time: {last_scan_time}")
        
        while self.running:
            try:
                self.ip_address = self.config_manager.read_ip_address()
                if self.previous_ipaddress != self.ip_address:
                    self.previous_ipaddress = self.ip_address
                    self.ip_address_updated.emit(self.ip_address)
                    self.ip_adress_changed = True
                    print(f"MT Line {inspect.currentframe().f_lineno} IP address changed to {self.ip_address}")
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} IP address changed to {self.ip_address}")

            except Exception as e:
                logging.error(f"MT Line {inspect.currentframe().f_lineno} Error in connection monitor: {e}")

            await asyncio.sleep(2)

    async def qualify_running(self, data):
        print(f"MT Line {inspect.currentframe().f_lineno} Qualify Running!")
        logging.info(f"MT Line {inspect.currentframe().f_lineno}Qualify Running!")
        while data['gameStates']['mSessionState'] == 3:
            # print(f"Qualify Session State: {data['gameStates']['mSessionState']}")
            #self.race_message_updated.emit("Qualifying Running...")
            if not self.running: break
            data = await self.get_api_data()
            if data is not None: 
                self.data_updated.emit(data)
                #self.data_updated_newclass.emit(data)
    
    async def practice_running(self, data):
        print(f"MT Line {inspect.currentframe().f_lineno} Practice Running!")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Practice Running!")
        while data['gameStates']['mSessionState'] == 1:
            # print(f"Practice Session State: {data['gameStates']['mSessionState']}")
            if not self.running: break
            data = await self.get_api_data()
            if data is not None:
                self.data_updated.emit(data)
                #self.data_updated_newclass.emit(data)

    async def race_running(self, data):
        if not self.running: return
        self.race_in_session = True
        #if data is not None:
            # Commented out to allow automatic session assignment to complete first
        #    self.data_updated.emit(data)
            #self.data_updated_newclass.emit(data)
        #    pass
        lap_times_dict = {} # Clear the lap times dictionary ready for next race.
        last_lap_counts = {} # Clear the last lap counts dictionary
        driver_total_times = {} # Clear the driver total times dictionary
        self.driver_flags ={} # Clear the driver flags dictionary
        #QMetaObject.invokeMethod(self.tab_widget, "setCurrentIndex", Qt.QueuedConnection, Q_ARG(int, 0)) #Switch to Score View tab
        print(f"MT Line {inspect.currentframe().f_lineno} Race is STARTING!!!!!!.")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Race is STARTING!!!!!!.")
        
        # AUTOMATIC SESSION ASSIGNMENT - New Feature!
        participants = data.get('participants', {}).get('mParticipantInfo', [])
        print(f"MT Line {inspect.currentframe().f_lineno} Calculating automatic session ID for participants: {[p.get('mName', 'Unknown') for p in participants]}")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Starting automatic session assignment for {len(participants)} participants")
        
        # Get current ip_name_flag for human driver detection
        await self.get_participants_ips(participants)
        
        # Send ip_name_flag to database thread for human driver detection
        self.task_queue.put(('update_ip_name_flag', (self.ip_name_flag,)))
        
        # NEW: Fetch previous race participants for driver change detection
        print(f"MT Line {inspect.currentframe().f_lineno} Fetching recent session participants for driver change detection")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Fetching recent session participants for driver change detection")
        
        # Create storage for async database results
        self.recent_participants_result = None
        self.session_has_races_result = None
        
        def store_recent_participants(result):
            self.recent_participants_result = result
            
        def store_session_has_races(result):
            self.session_has_races_result = result
        
        # Fetch previous participants and check if current session has races
        self.task_queue.put(('get_recent_session_participants', (store_recent_participants,)))
        self.task_queue.put(('check_session_has_races', (self.session_id, store_session_has_races)))
        
        # Wait for database results (with timeout)
        wait_timeout = 0
        while (self.recent_participants_result is None or self.session_has_races_result is None) and wait_timeout < 100:
            await asyncio.sleep(0.05)  # 50ms intervals
            wait_timeout += 1
        
        # Extract previous participants and session status
        previous_participants = []
        session_has_races = False
        
        if self.recent_participants_result:
            _, previous_participants = self.recent_participants_result
            print(f"MT Line {inspect.currentframe().f_lineno} Previous race participants: {previous_participants}")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Previous race participants fetched: {len(previous_participants)} drivers")
        
        if self.session_has_races_result is not None:
            session_has_races = self.session_has_races_result
            print(f"MT Line {inspect.currentframe().f_lineno} Current session {self.session_id} has races: {session_has_races}")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Session {self.session_id} has existing races: {session_has_races}")
        
        # Calculate session ID directly in MonitorThread with enhanced logic
        calculated_session_id = self.calculate_session_id_for_participants(
            participants, 
            self.ip_name_flag, 
            previous_participants, 
            session_has_races
        )
        
        # Update session ID with automatic assignment (including driver change detection)
        self.session_id = calculated_session_id
        print(f"MT Line {inspect.currentframe().f_lineno} Session ID automatically assigned: {self.session_id}")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Using auto-assigned session ID: {self.session_id}")
        
        # Notify GUI of automatic session assignment
        self.auto_session_assigned_signal.emit(self.session_id)

        print(f"MT Line {inspect.currentframe().f_lineno} Data to be written to database, Session id: {self.session_id} ")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Data to be written to database: Sesson id: {self.session_id}")
        self.track_location = data['eventInformation']['mTranslatedTrackVariation']+ ' - ' + data['eventInformation']['mTranslatedTrackLocation']
        if not self.time_trial: # If it is not a time trial, write race to DB    
            self.task_queue.put(('write_race', (data, self.session_id)))
            print(f"MT Line {inspect.currentframe().f_lineno} Session ID received: {self.session_id} Race written to database.")
        else:
            print(f"MT Line {inspect.currentframe().f_lineno} Session ID received: {self.session_id} Time Trial No DB write.")
        self.task_queue.put(('get_latest_race_id', (self.set_race_id,)))  # Only pass the necessary data, not the function
        print(f"MT Line {inspect.currentframe().f_lineno} self.race_id: {self.race_id}")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Current Race ID: {self.race_id}")
        while self.race_id == 0:
            await asyncio.sleep(0.5)
            print(f"MT Line {inspect.currentframe().f_lineno} Waiting for race ID to be updated. Current Race ID: {self.race_id}")
        print(f"MT Line {inspect.currentframe().f_lineno} Race ID received: {self.race_id}, entering live view loop.")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Race written to database., asked for race ID: {self.race_id}, entering live view loop.")
        #elapsed_time = []
        round_counter = 0
        response_time_ms = 0
        skippet = 0  # Initialize a counter for skipped iterations
        not_skippet = 0  # Initialize a counter for non-skipped iterations
        self.fetch_api_delay = 0.03  # Set the initial delay for fetching API data
        cache_delay = 0.06  # Set the delay for caching API data. optimal value: 0.0167
        self.start_cache_data = True
        previous_data = data
        #asyncio.create_task(self.cache_api_data()) # Start caching API data in the background
        #await asyncio.sleep(1)  # Initial delay to allow the cache to start        
        while self.race_in_session:
            if not self.running: break
            previous_data = data
            #start_time = time.time()     #loop while race is running
            #self.start_cache_data = True
            #await asyncio.sleep(cache_delay)  # Tune for minimum delay between API calls
            try:
                #start_time = time.time() # Start the timer for measuring API response time
                data = await self.get_api_data()


                if data == None:
                    print(f"MT Line {inspect.currentframe().f_lineno} Data is None, skipping")
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} Data is None, skipping")
                    continue
                participants = data.get('participants', {}).get('mParticipantInfo', [])  # Proceed with processing the valid data 
                if not participants or all(participant.get('mCurrentLap', 0) > data['eventInformation']['mLapsInEvent'] for participant in participants):  # Check if all participants have completed every lap or if there is data.
                    if not participants:                                                       
                        data = previous_data # Revert to the previous data if no participants are found
                        logging.info(f"MT Line {inspect.currentframe().f_lineno} No participants found , Race is over. Break loop")
                        print(f"MT Line {inspect.currentframe().f_lineno} No participants found, Race is over.")
                        self.race_in_session = False
                    elif not data['eventInformation']['mLapsInEvent'] == 0: # If it is a time trial, continue loop until no participants are found.                           
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} All participants finished, Race is over,Sending Data one last time, breaking the loop")
                            print(f"MT Line {inspect.currentframe().f_lineno} All participants finished race, Race is over. Sending Data one last time.")
                            self.race_may_not_be_finished = True
                            self.race_in_session = False

                if not self.running: break
                if data is not None: 
                    self.data_updated.emit(data) #Send the data to Live view
                    #self.data_updated_newclass.emit(data)
                for participant in participants:
                    if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                    if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0   
                    if (participant.get('mCurrentLap', 0) > last_lap_counts.get(participant['mName'], 1)) and (participant.get('mLastLapTimes') != -123):
                        if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                        if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0                                    
                        driver_total_times[participant['mName']] += participant.get('mLastLapTimes', 0)
                        if not self.time_trial:  
                            self.task_queue.put(('insert_lap_data', (self.race_id, participant['mName'], participant.get('mCurrentLap', 0) - 1,participant.get('mLastLapTimes'), self.track_location, participant['mCarNames']))) #insert lap into Table
                            lap_times_dict[participant['mName']].append(participant.get('mLastLapTimes', None))
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Storing lap time for {participant['mName']}: Lap {participant.get('mCurrentLap', 0)}, Time {participant.get('mLastLapTimes', 0)},Last Lap:{participant.get('mLastLapTimes', None)} Driver Total Time: {driver_total_times[participant['mName']]} ")
                    else:
                        if (participant.get('mSpeeds',0) >10) and (data['gameStates']['mRaceState'] == 1) and (self.driver_flags.get(participant['mName'],None) != 'Falsestart'):
                            print(f"MT Line {inspect.currentframe().f_lineno} Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            self.driver_flags[participant['mName']] = 'Falsestart'
                            if self.driver_flags is not None: self.flags_updated.emit(self.driver_flags)
                    last_lap_counts[participant['mName']] = participant.get('mCurrentLap', 0)
                self.race_loop_first_time = False
            except Exception as e:
                logging.error(f"MT Line {inspect.currentframe().f_lineno} An error occurred while processing participant data: {e}")
                print(f"MT Line {inspect.currentframe().f_lineno} An error occurred while processing participant data: {e}")
                raise
            #end_time = time.time()
            #elapsed_time.append(end_time - start_time)
            #response_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds
            #self.api_response_time_updated.emit(response_time_ms)  # Emit response time
            #self.api_response_time_updated.emit(cache_delay)  # Emit response time
            round_counter += 1
        # Race loop has ended    
        #average_time = sum(elapsed_time) / len(elapsed_time)
        #max_time = max(elapsed_time)
        #min_time = min(elapsed_time)
        #print(f"MT Line {inspect.currentframe().f_lineno} Api Fetch time, average execution time: {average_time:.6f} seconds, maximum execution time: {max_time:.6f} seconds, minimum execution time: {min_time:.6f} seconds")
        if self.session is not None: await self.session.close()
        self.session = None
        print(f"MT Line {inspect.currentframe().f_lineno} Race Ended Finalizing Race for: Race_{self.race_id} with Driver Total times: {driver_total_times}")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Race Ended Finalizing Race for: Race_{self.race_id} with Driver Total times: {driver_total_times}")
        if data is not None: participants = data.get('participants', {}).get('mParticipantInfo', [])
        if not driver_total_times:
            print(f"MT Line {inspect.currentframe().f_lineno} No reason to write race, no one finished, no driver_total_times.")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} No reason to write race, no one finished, no driver_total_times.")
            self.race_may_not_be_finished = True
            race_valid = False
            self.race_finished.emit(race_valid, self.session_id) # no reason to write the race, no one finished
        else:
            try:                
                for participant in participants:
                    participant_name = participant['mName']
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} Participant: {participant['mName']}, Race Position: {participant.get('mRacePosition', 0)}")
                    participant_name = participant['mName']
                    if data is None or not self.running: return
                    if participant['mCurrentLap'] <= data['eventInformation']['mLapsInEvent']: # Driver has fewer laps less than he should, either False start Or DNF
                        print(f"MT Line {inspect.currentframe().f_lineno} Participant: {participant_name}, Current Lap: {participant['mCurrentLap']}, Laps in Event: {data['eventInformation']['mLapsInEvent']}")
                        if self.driver_flags is not None:
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Participant: {participant_name}, Flags: {self.driver_flags}")
                            if self.driver_flags.get(participant_name) != 'Falsestart': # Check if the participant has a 'Falsestart' flag
                                print(f"MT Line {inspect.currentframe().f_lineno} Adding DNF to Flags for {participant_name}")
                                logging.info(f"MT Line {inspect.currentframe().f_lineno} Adding DNF to Flags for {participant_name}")
                                self.driver_flags[participant_name] = 'DNF'
                                if self.driver_flags is not None: self.flags_updated.emit(self.driver_flags)
                                await asyncio.sleep(0.5)
                            print(f"MT Line {inspect.currentframe().f_lineno} Participant: {participant_name}, Flags: {self.driver_flags.get('participant_name',0)}")
                print(f"MT Line {inspect.currentframe().f_lineno} All flags: {self.driver_flags}")                
                if not self.time_trial:                                
                    self.task_queue.put(('finalize_race', (data, lap_times_dict,self.driver_flags, self.pit_stops_dict))) # Write final data to DB
                    print(f"MT Line {inspect.currentframe().f_lineno} Finalizing race")
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} Finalizing race")
                if data is not None: self.data_updated.emit(data) #Send the data to Live view to update the flags
                race_valid = True
                self.race_finished.emit(race_valid, self.session_id)
                self.start_cache_data = False
                print(f"MT Line {inspect.currentframe().f_lineno} Race finished emitted")
                print(f"MT Line {inspect.currentframe().f_lineno} Race Finished for session ID: {self.session_id}")
                # self.task_queue.put(('load_score_data', (self.session_id,)))  # Only pass the necessary data, not the function
            except Exception as e:
                logging.error(f"MT Line {inspect.currentframe().f_lineno} An error occurred while finalizing race: {e}")
                print(f"MT Line {inspect.currentframe().f_lineno} An error occurred while finalizing race: {e}")
                await asyncio.sleep(5)
                
    async def stop(self):
        if self.session:
            await self.session.close()  # Close the session when stopping
            self.session = None
        self.running = False
        print(f"MT Line {inspect.currentframe().f_lineno} Starting pending all tasks")
        pending = asyncio.all_tasks(loop=asyncio.get_event_loop())
        for task in pending: task.cancel()
        print(f"MT Line {inspect.currentframe().f_lineno} all tasks cancelled")
        self.quit()
        self.wait()

class GuiMainApp(QMainWindow):
    #session_id_updated = pyqtSignal(int)
    tab_changed = pyqtSignal(int)
    delete_flag = pyqtSignal(str)  # Signal to delete a flag for a driver
    update_session_id_from_button = pyqtSignal(str)  # Signal to update session ID from buttons
    #active_computers_signal = pyqtSignal(list)  # Signal to update the list of active computers
    _instance = None

    @classmethod
    def get_instance(cls):
        return cls._instance or cls()

    def __init__(self):
        if GuiMainApp._instance is not None:
            raise RuntimeError("GuiMainApp er allerede opprettet! Bruk get_instance().")
        super().__init__()
        GuiMainApp._instance = self
        self.available_ips = [ConfigManager.get_config_value(f'sim-{i}', 'simsettings', '').strip() for i in range(1, 21) if ConfigManager.get_config_value(f'sim-{i}', 'simsettings', '')]
        self.initUI()
        self.init_threads_and_managers()
        self.init_components()
        self.connect_signals()
        self.init_state_variables()
        self.on_tab_changed(1)  # Set the initial tab to previous races
        self.check_enable_disable_cp_button()

        print(f"GA Line {inspect.currentframe().f_lineno} Get latest session ID from DB.")
        #self.task_queue.put(('get_latest_session_id', (self.set_session_id,)))
        #self.race_app.get_request_for_sim_signal.emit()

    def init_threads_and_managers(self):
        self.task_queue = queue.Queue()
        self.config_manager = ConfigManager(self.task_queue)
        self.update_config_file = self.config_manager.update_config_file(self)
        self.db_thread = DatabaseThread(self.task_queue, self.config_manager)
        self.monitor_thread = MonitorThread(self, self.tab_widget, self.task_queue, self.config_manager)

    def init_components(self):
        self.control_panel = ControlPanel(self.db_thread, self.config_manager, self)
        self.race_app = RaceApp(
            self.monitor_thread, self.task_queue, self.config_manager,
            self.db_thread, self.control_panel, self, self.tab_widget, self
        )
        #self.race_app.get_request_for_sim_signal.connect(self.control_panel.process_sim_signal)
        #self.active_computers_signal.connect(self.race_app.handle_active_computers_update)  # Connect the signal to the slot that handles active computers
        self.monitor_thread.connect_race_app(self.race_app)
        self.monitor_thread.start()
        self.db_thread.start()

    def connect_signals(self):

        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.qualify_finished.connect(self.qualify_finished)
        self.monitor_thread.practice_finished.connect(self.practice_finished)
        self.monitor_thread.initialize.connect(self.initialize_dropdown)
        self.db_thread.load_race_on_start_signal.connect(self.handle_race_data_on_start)
        self.db_thread.load_sessionid_on_start_signal.connect(self.handle_sessionid_data)
        self.db_thread.load_highscores_on_start_signal.connect(self.handle_high_scores_data_on_start)
        self.db_thread.race_data_loaded_signal.connect(self.on_race_loaded)
        self.db_thread.highscore_data_loaded_signal.connect(self.on_highscore_loaded)
        self.db_thread.drivers_signal.connect(self.handle_driver_statistics_on_start)
        self.db_thread.score_data_signal.connect(self.calculate_score)
        self.monitor_thread.auto_session_assigned_signal.connect(self.handle_automatic_session_assignment)  # Automatic session assignment from MonitorThread
        self.monitor_thread.ip_address_updated.connect(self.update_ip_address)
        self.monitor_thread.race_message_updated.connect(self.update_race_message)
        self.monitor_thread.api_signal_status_updated.connect(self.update_api_status)
        self.monitor_thread.session_type_updated.connect(self.handle_session_type)
        self.monitor_thread.active_computers_signal.connect(self.handle_radio_button_update)
        self.monitor_thread.session_id_updated.connect(self.update_session_id)
        #self.monitor_thread.radio_button_update.connect(self.handle_radio_button_update)
        self.race_app.gui_realtime_update.connect(self.needle_pedal_wheel_animation)  # Connect the signal to the slot that handles real-time GUI updates
        self.race_app.participant_update.connect(self.handle_participant_update)
        self.race_app.gui_update.connect(self.apply_gui_updates)
        self.race_app.hide_buttons.connect(self.set_hide_button_flag)
        #self.control_panel.driver_sims_updated.connect(self.update_driver_names)  # Connect the signal to the slot that updates the driver names
        self.race_app.radio_button_update.connect(self.handle_radio_button_update)  # IP of computers in the race passed
        self.monitor_thread.change_tab_signal.connect(self.on_tab_changed)

    def init_state_variables(self):
        self.response_time_log = {}
        self.last_flush = time.time()
        self.session_id_dropdown = None
        self.hidebuttons = False
        self.time_trial = False
        self.active_computers = []
        self.do_not_reset_index = False
        self.selected_race_id = 0
        self.all_driver_dropdown_items = []
        self.speedo_max = 320
        self.speedo_sweep = (0, 225)
        self.tacho_max = 14000
        self.tacho_sweep = (0, 245)

    def initUI(self):
        self.labels = {}
        self.session_id = None
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        # Convert images to base64 strings once during initialization
        self.window_icon = QIcon(self.base64_to_qicon(rockytm_icon_base64))
        self.live_image = self.base64_to_pixmap(liverace_liveview_img_base64)  # Background for Live view
        self.result_background_image = self.base64_to_pixmap(race_results_background_img_base64)  # Background for Results view
        self.final_background_image = self.base64_to_pixmap(race_scores_background_img_base64)  # Background for Final view
        self.status_image = self.base64_to_pixmap(liverace_status_img_base64)
        self.highscore_background_image = self.base64_to_pixmap(high_scores_background_img_base64)
        self.driver_statistics_background_image = self.base64_to_pixmap(driver_statistics_background_img_base64)
        self.speedometer_image = self.base64_to_pixmap(speedometer_bg_img_base64)  # Speedometer image
        self.tachometer_image = self.base64_to_pixmap(tachometer_bg_img_base64)  # Tachometer image
        self.needle_image = self.base64_to_pixmap(needle_bg_img_base64)  # Needle image 
        self.lap_image = self.base64_to_pixmap(lap_bg_img_base64)  # Lap image
        self.bestlaptime_image = self.base64_to_pixmap(bestlap_bg_img_base64)  # Best lap image
        self.wheel_image = self.base64_to_pixmap(wheel_bg_img_base64)  # Wheel image
        self.wheels_image = self.base64_to_pixmap(wheels_bg_img_base64)  # Wheels image
        self.pedals_image = self.base64_to_pixmap(pedal_bg_img_base64)  # Pedals image
        self.pedals_raw_image = self.base64_to_pixmap(pedal_raw_bg_img_base64)  # Pedals raw image
        self.pos_image = self.base64_to_pixmap(pos_bg_img_base64)  # Position image
        self.laptime_image = self.base64_to_pixmap(laptime_bg_img_base64)  # Laptime image
        self.delta_local_record_image = self.base64_to_pixmap(delta_local_record_bg_img_base64)  # Delta local record image
        self.remaining_image = self.base64_to_pixmap(remaining_bg_img_base64)  # Remaining image
        self.delta_world_record_image = self.base64_to_pixmap(delta_world_record_bg_img_base64)  # Delta world record image
        self.window_icon = self.base64_to_qicon(rockytm_icon_base64)
        self.setWindowIcon(self.window_icon)
        self.font_family = self.base64_to_font(sui_generis_rg_font_base64)
        self.font_family_digits = self.base64_to_font(ds_digib_font_base64)


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
        height = int(self.config['config']['height']) if int(self.config['config']['height']) > 1150 else 1150
        self.setGeometry(0, 0, int(self.config['config']['width']), height)
        self.setFixedSize(int(self.config['config']['width']), height) # Set fixed size to prevent autoresizing
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Fully transparent
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
        background-position: center;
        background-repeat: no-repeat;
        """)
        # Hent monitor-index fra config, eller bruk 0 som fallback
        monitor_index = int(self.config.get('config', 'monitor', fallback='0'))
        # For moderne systemer med flere skjermer
        screens = QGuiApplication.screens()
        if 0 <= monitor_index < len(screens):
            screen_geometry = screens[monitor_index].geometry()
            x = screen_geometry.x()
            y = screen_geometry.y()
            self.move(x, y)
        else:
            print(f"Monitor index {monitor_index} not found, defaulting to primary screen.")
            self.move(0, 0)        

        self.tab_widget = QTabWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.addWidget(self.tab_widget)
        self.main_layout.setContentsMargins(15, 0, 15, 0)  # Remove margins to use full space
        self.main_layout.setSpacing(0)  # Remove spacing between widgets

        # Apply the translucent style to the tab panes.
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

        # Create widgets for each tab
        self.live_view_widget = QWidget()
        self.results_view_widget = QWidget()
        self.final_view_widget = QWidget()
        self.highscore_view_widget = QWidget()
        self.driver_statistics_widget = QWidget()
        self.driver_info_tab = QWidget()
        self.bottom_bar = QWidget()
        self.top_layout = QHBoxLayout()
        self.info_layout = QVBoxLayout()
        self.progress_layout = QHBoxLayout()
        #self.button_column_layout = QVBoxLayout()
        self.button_column_layout = QGridLayout()
        self.bottom_layout = QHBoxLayout(self.bottom_bar)
        # 
        
        # Set up layouts for each tab
        self.driver_view_layout = QGridLayout(self.driver_info_tab)
        self.live_view_layout = QVBoxLayout(self.live_view_widget)
        self.results_view_layout = QVBoxLayout(self.results_view_widget)
        self.final_view_layout = QVBoxLayout(self.final_view_widget)
        self.highscore_view_layout = QVBoxLayout(self.highscore_view_widget)
        self.driver_statistics_layout = QVBoxLayout(self.driver_statistics_widget)
        self.bottom_layout.addLayout(self.button_column_layout)
        #self.driver_info_tab.setLayout(QVBoxLayout())
        #self.bottom_widget = QWidget(self.driver_info_tab)
        #self.bottom_widget.hide()  # Hide until tab is active
        
        #self.live_view_widget.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

        # Add live view and results view to the tab widget and give the tabs a name
        self.tab_widget.addTab(self.live_view_widget, "Live Race Data")
        self.tab_widget.addTab(self.results_view_widget, "Previous Races")
        self.tab_widget.addTab(self.final_view_widget, "Accumulated Score")
        self.tab_widget.addTab(self.highscore_view_widget, "High Scores")
        self.tab_widget.addTab(self.driver_statistics_widget, "Driver Statistics")
        self.tab_widget.addTab(self.driver_info_tab, "Driver Info")

        # Add your existing widgets and layout configurations to the appropriate tab layouts
        self.setup_live_view() # Initialize the live view
        self.setup_final_view() # Initialize the final view
        self.setup_result_view() # Initialize the result view
        self.setup_highscore_view() # Initialize the highscore view
        self.setup_driver_statistics_view() # Initialize the driver statistics view
        self.setup_driver_info_view() # Initialize the driver info view
        #self.tab_widget.setCurrentIndex(1) #Set the Status view as the default tab

        # Connect tab change to background update
        self.tab_widget.currentChanged.connect(self.on_tab_changed)

        # Create a QLabel to display the background image
        self.background_label = QLabel(self.central_widget)
        self.background_label.setPixmap(self.status_image)
        self.background_label.setGeometry(0, 0, int(self.config['config']['width']), height)
        #self.result_background_label.setGeometry(0,0,int(self.width()), int(self.height()))
        self.background_label.setScaledContents(True)  # Adjusts the image size to the window
        self.background_label.lower()  # Ensure the background stays behind other widgets
        #self.main_layout.setAlignment(Qt.AlignTop)


        # Dropdowns and Calendar
        self.track_dropdown = QComboBox(self)
        self.labels['track_dropdown'] = self.track_dropdown
        self.track_dropdown.setStyleSheet("""
             font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;
            border-radius: 5px;
            padding: 2px 5px;
        """)
        self.track_dropdown.setFixedSize(600, 30)
        self.track_dropdown.currentIndexChanged.connect(self.update_dropdowns)
        self.button_column_layout.addWidget(self.track_dropdown)

        self.car_dropdown = QComboBox(self)
        self.labels['car_dropdown'] = self.car_dropdown
        self.car_dropdown.setStyleSheet(self.track_dropdown.styleSheet())
        self.car_dropdown.setFixedSize(600, 30)
        self.button_column_layout.addWidget(self.car_dropdown)

        self.driver_dropdown = QComboBox(self)
        self.labels['driver_dropdown'] = self.driver_dropdown
        self.driver_dropdown.setEditable(True)
        line_edit = self.driver_dropdown.lineEdit()
        line_edit.textEdited.connect(self.filter_dropdown)
        line_edit.installEventFilter(self)
        line_edit.setFocusPolicy(Qt.StrongFocus)
        self.driver_dropdown.setFocusPolicy(Qt.StrongFocus)
        self.driver_dropdown.setStyleSheet(self.track_dropdown.styleSheet())
        self.driver_dropdown.setFixedSize(600, 30)
        self.driver_dropdown.activated.connect(self.load_selected_driver)
        self.button_column_layout.addWidget(self.driver_dropdown)

        self.dropdown_races = QComboBox(self)
        self.labels['dropdown_races'] = self.dropdown_races
        self.dropdown_races.setStyleSheet(self.track_dropdown.styleSheet())
        self.dropdown_races.setFixedSize(600, 30)
        self.dropdown_races.activated.connect(self.load_selected_race)
        self.button_column_layout.addWidget(self.dropdown_races)

        self.calendar_widget = QCalendarWidget(self)
        self.labels['calendar_widget'] = self.calendar_widget
        self.calendar_widget.setStyleSheet("""
            font-size: 10px;
            color: black;
            background-color: white;
            border: 1px solid black;
            border-radius: 5px;
            padding: 2px 5px;
        """)
        self.calendar_widget.setGeometry(700, height-175, 300, 150)
        self.calendar_widget.setGridVisible(True)
        self.calendar_widget.setSelectedDate(QDate.currentDate())
        self.calendar_widget.clicked.connect(self.load_race_for_date)

        self.dropdown_sessionid = QComboBox(self)
        self.labels['dropdown_sessionid'] = self.dropdown_sessionid
        self.dropdown_sessionid.setEditable(True)
        self.dropdown_sessionid.setStyleSheet(self.track_dropdown.styleSheet())
        self.dropdown_sessionid.setFixedSize(300, 30)
        self.dropdown_sessionid.activated.connect(self.display_score)
        self.button_column_layout.addWidget(self.dropdown_sessionid)



        # Add Button Style 
        self.button_style = """
            QPushButton {
                font-size: 14px;
                background-color: #a32d2d;
                color: white;
                margin-bottom: 5px;
                border: 2px solid black;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #b33b3b;
            }
            QPushButton:focus {
                outline: none;
                border: 2px solid #ff0000;
            }
            QPushButton:pressed {
                background-color: #801919;
                border: 2px solid #5d1a1a;
            }
        """

        # Utility function to create and add buttons


        # Buttons in button_column_layout
        self.add_control_button("Find Computers", self.scan_active_computers, 'find_computers_button', self.button_column_layout)
        self.add_control_button("Filter Drivers", lambda: self.handle_radio_button_update(None), 'filter_drivers_button', self.button_column_layout)
        self.add_control_button("Disable CP", self.enable_disable_cp, 'Enable_CP', self.button_column_layout)
        self.add_control_button("Remove Flag", self.remove_falseflag, 'Remove_FF', self.button_column_layout)

        # Buttons in main_layout
        self.add_control_button("Load High Scores", self.load_selected_highscore, 'load_high_scores_button', self.button_column_layout)
        self.add_control_button("Delete Driver", self.delete_selected_driver, 'delete_driver_button', self.button_column_layout)
        self.add_control_button("Delete Selected Race", self.delete_selected_race, 'delete_button', self.button_column_layout)
        self.add_control_button("Delete All Races", self.delete_all_races, 'delete_all_races_button', self.button_column_layout)
        self.add_control_button("Next Session", self.start_new_session, 'new_session_button', self.button_column_layout)
        self.add_control_button("Previous Session", self.previous_session, 'previous_session_button', self.button_column_layout)

        # Status label
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
        self.main_layout.addWidget(self.status_label)


        #self.button_column_layout.addStretch()
        # 1. Opprett containeren for radio-knappene
        self.radio_container = QWidget(self.driver_info_tab)
        self.labels['radio_buttons'] = self.radio_container
        self.radio_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        #self.radio_container.setGeometry(315, 800, 800, 100)  # Posisjon nederst til høyre
        self.bottom_layout.addStretch()
        self.main_layout.addWidget(self.radio_container, alignment=Qt.AlignBottom | Qt.AlignRight)   

        # 2. Sett stilen (bakgrunn etc)
        self.radio_container.setStyleSheet("""
            background-color: rgba(0, 0, 0, 120);
            border-radius: 10px;
        """)

        # 3. Legg til layout inni containeren (f.eks. grid)
        self.radio_layout = QGridLayout(self.radio_container)
        self.radio_layout.setContentsMargins(5, 5, 5, 5)
        # 4. Legg til radioknappene
        self.sim_radio_group = QButtonGroup(self.radio_container)

        for i, ip in enumerate(self.available_ips):
            btn = QRadioButton(str(i + 1))
            btn.setToolTip(ip)
            btn.setStyleSheet(f"""
                    QRadioButton::indicator {{
                    width: 0px;
                    height: 0px;
                    image: none;
                }}
                QRadioButton:enabled {{
                    color: red;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QRadioButton:checked {{
                    color: lime;

             }}
                QRadioButton:disabled {{
                    color: grey;
                    font-size: 6px;
                }}
            """)

            btn.setFixedSize(180, 25)  # Sett en fast størrelse for knappene
            self.sim_radio_group.addButton(btn, i)
            self.radio_layout.addWidget(btn, i // 5, i % 5)

        # 5. Koble klikksignal
        self.sim_radio_group.buttonClicked.connect(
            lambda button: self.set_monitored_ip(self.sim_radio_group.id(button))
        )
        self.bottom_layout.addWidget(self.radio_container)


        # 2. Legg til tab-widget og bottom_bar i main_layout
        self.main_layout.addWidget(self.bottom_bar)  # Legges under tab-widgeten


        # Sett default valgt IP
        default_ip = ConfigManager.get_config_value('ip_address', 'config', '127.0.0.1').strip()
        default_index = self.available_ips.index(default_ip) if default_ip in self.available_ips else 0
        self.sim_radio_group.button(default_index).setChecked(True)


        
        self.tab_widget_mapping = {  # Widget visibility mapping for each tab
            0: [],  # Widgets for Live View
            1: ['dropdown_races', 'delete_button', 'delete_all_races_button', 'calendar_widget'  ],  # Widgets for Results View
            2: ['Enable_CP','new_session_button', 'dropdown_sessionid', 'previous_session_button' ],  # Widgets for Score View
            3: ['car_dropdown', 'track_dropdown', 'load_high_scores_button'],  # Widgets for High Scores
            4: ['driver_dropdown', 'delete_driver_button'],  # Widgets for Driver Statistics
            5: ['find_computers_button', 'filter_drivers_button', 'Enable_CP', 'Remove_FF', 'radio_buttons']  # Widgets for Driver Info
        }

    def add_control_button(self, label, callback, key, layout):
        button = QPushButton(label, self)
        button.setStyleSheet(self.button_style)
        button.setFixedSize(150, 30)
        button.clicked.connect(callback)
        setattr(self, key, button)  # Also set as instance attribute
        self.labels[key] = button
        layout.addWidget(button)

    def remove_falseflag(self):
        """Remove false flag from the driver."""
        current_value = self.driver_txt.text()
        print(f"GA Line {inspect.currentframe().f_lineno} Current driver text: {current_value}")
        if current_value:
            driver_name = current_value.strip()
            print(f"GA Line {inspect.currentframe().f_lineno} Removing false flag for driver: {driver_name}")
            self.delete_flag.emit(driver_name)

    def needle_pedal_wheel_animation(self, data):
        def rotate_needle(value, max_value, label, needle_pixmap, start_angle=-135, end_angle=135):
            value = max(0, min(value, max_value))
            sweep = end_angle - start_angle
            angle = (value / max_value) * sweep + start_angle
            size = needle_pixmap.size()
            canvas = QPixmap(size)
            canvas.fill(Qt.transparent)
            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            center = needle_pixmap.rect().center()
            painter.translate(center)
            painter.rotate(angle)
            painter.translate(-center)
            painter.drawPixmap(0, 0, needle_pixmap)
            painter.end()
            label.setPixmap(canvas)
            #print(f"Drawing needle. angle={angle:.2f}, label={label}, pixmap size={needle_pixmap.size()}")

        def rotate_steering_wheel(value):
            angle = value * 360
            pixmap = self.wheel_image
            rotated_pixmap = QPixmap(pixmap.size())
            rotated_pixmap.fill(Qt.transparent)
            painter = QPainter(rotated_pixmap)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            center = pixmap.rect().center()
            painter.translate(center)
            painter.rotate(angle)
            painter.translate(-center)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            self.wheel_label.setPixmap(rotated_pixmap)

        steering = data.get("steering")
        speed = data.get("speed")
        rpm = data.get("rpm")
        throttle = data.get("throttle")
        brake = data.get("brake")
        clutch = data.get("clutch")
        throttle_raw = data.get("throttle_raw")
        brake_raw = data.get("brake_raw")
        clutch_raw = data.get("clutch_raw")

        if steering is not None:
            rotate_steering_wheel(steering)
        if speed is not None:
            rotate_needle(speed, self.speedo_max, self.speed_needle_label, self.scaled_needle_image, *self.speedo_sweep)
        if rpm is not None:
            rotate_needle(rpm, self.tacho_max, self.tacho_needle_label, self.scaled_needle_image, *self.tacho_sweep)
        
        # Update pedal bars immediately for smooth animation
        if throttle is not None:
            self.throttle_bar.setValue(throttle)
        if brake is not None:
            self.brake_bar.setValue(brake)
        if clutch is not None:
            self.clutch_bar.setValue(clutch)
        if throttle_raw is not None:
            self.throttle_raw_bar.setValue(throttle_raw)
        if brake_raw is not None:
            self.brake_raw_bar.setValue(brake_raw)
        if clutch_raw is not None:
            self.clutch_raw_bar.setValue(clutch_raw)    
    
    def handle_participant_update(self, index, html):
        if 0 <= index < len(self.participant_labels):
            self.participant_labels[index].setText(html)

    def apply_gui_updates(self, updates):
        for method, args in updates:
            method(*args)
            #print("Applying GUI update:", method.__name__, args)

    def set_hide_button_flag(self):
        self.hidebuttons = True
    
    def handle_gui_driver_updates(self, gui_data):
        """Handle GUI updates for driver statistics."""
        for setter, args in gui_data:
            setter(*args)

            # Add more cases as needed
    
    def check_enable_disable_cp_button(self):
        """Check if the Control Panel writing button should be enabled or disabled."""
        if self.config_manager.cp_enabled("check"):
            self.Enable_CP.setText("Disable CP")
            print(f"GA Line {inspect.currentframe().f_lineno} Control Panel writing is enabled.")
        else:
            self.Enable_CP.setText("Enable CP")
            print(f"GA Line {inspect.currentframe().f_lineno} Control Panel writing is disabled.")

    def enable_disable_cp(self):
        """Enable or disable the Control Panel writing of score data."""
        if self.config_manager.cp_enabled("check"):
            self.config_manager.cp_enabled(False)
            self.Enable_CP.setText("Enable CP")
            print(f"GA Line {inspect.currentframe().f_lineno} Control Panel writing disabled.")
        else:
            self.config_manager.cp_enabled (True)
            self.Enable_CP.setText("Disable CP")
            print(f"GA Line {inspect.currentframe().f_lineno} Control Panel writing enabled.")
     
    def scan_active_computers(self):
        # run on race start, and on program start.
        #self.active_computers.clear()
        active_computers = []
        self.race_app.get_request_for_sim_signal.emit()
        for i, ip in enumerate(self.available_ips):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.05)  # 50ms timeout
            try:
                result = sock.connect_ex((ip, 8180))
                if result == 0:
                    active_computers.append(ip)
                    self.sim_radio_group.button(i).setEnabled(True)
                    print(f"GA Line {inspect.currentframe().f_lineno} Computer {i+1} is active: {ip}")
                else:
                    self.sim_radio_group.button(i).setEnabled(False)
            finally:
                sock.close()
    
    def handle_radio_button_update(self, data):
        """
        Handle radio button updates based on either:
        - List of active IPs → legacy behavior (only enable/disable buttons).
        - Dict of {ip: (name, in_race)} → set label + enable/disable.
        """
        if data is None:
            print(f"GA Line {inspect.currentframe().f_lineno} No data provided, using stored value.")
            data = getattr(self, 'active_computers', None)
            if data is None:
                print(f"GA Line {inspect.currentframe().f_lineno} Still no data, skipping.")
                return
        else:
            self.active_computers = data

        for i, ip in enumerate(self.available_ips):
            button = self.sim_radio_group.button(i)
            if not button:
                continue

            if isinstance(data, dict):  # New style: {ip: (name, in_race)}
                name, in_race = data.get(ip, (f"S-{i+1}", 0))
                button.setText(f"{name} [{i+1}]")
                button.setEnabled(bool(in_race))
                print(f"GA Line {inspect.currentframe().f_lineno} Button {i+1}: {name}, {'ENABLED' if in_race else 'DISABLED'}")
            elif isinstance(data, list):  # Old style: list of IPs
                button.setEnabled(ip in data)
                print(f"GA Line {inspect.currentframe().f_lineno} Computer {i+1} is {'active' if ip in data else 'inactive'}: {ip}")

    def handle_radio_button_update_old(self, active_computers):
        if active_computers is None:
            print(f"GA Line {inspect.currentframe().f_lineno} No active computers provided, using stored value.")
            active_computers = getattr(self, 'active_computers', None)
            if active_computers is None:
                print(f"GA Line {inspect.currentframe().f_lineno} Still no active computers, skipping.")
                return
        else:
            self.active_computers = active_computers
        for i, ip in enumerate(self.available_ips):
            button = self.sim_radio_group.button(i)
            if button:  # Safety check
                button.setEnabled(ip in active_computers)
                if ip in active_computers:
                    print(f"GA Line {inspect.currentframe().f_lineno} Computer {i+1} is active: {ip}")

    def update_driver_names_to_be_deleted(self, driver_sims):
        """Update button labels in sim_radio_group with driver names and sim numbers."""

        if not driver_sims:
            print(f"GA Line {inspect.currentframe().f_lineno} No driver sims provided, skipping update.")
            return

        self.driver_sims = driver_sims
        print(f"GA Line {inspect.currentframe().f_lineno} Driver sims updated: {self.driver_sims}")

        for sim_index_str in driver_sims.values():
            sim_index = int(sim_index_str) - 1  # Adjust from 1-based to 0-based index
            driver_name = [name for name, idx in driver_sims.items() if idx == sim_index_str][0]
            button = self.sim_radio_group.button(sim_index)
            if button:
                button.setText(f"{driver_name} [{sim_index_str}]")
                print(f"GA Line {inspect.currentframe().f_lineno} Set button {sim_index + 1} to: {driver_name} [{sim_index_str}]")
            else:
                print(f"⚠️ Fant ingen knapp med ID {sim_index_str} for navn {driver_name}")

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
        """Load a QFont directly from base64 data in memory without writing to disk."""
        font_data = base64.b64decode(base64_str)
        byte_array = QByteArray(font_data)
        buffer = QBuffer(byte_array)

        if not buffer.open(QBuffer.ReadOnly):
            print(f"GA Line {inspect.currentframe().f_lineno} Failed to open buffer for font data.")
            return None

        font_id = QFontDatabase.addApplicationFontFromData(buffer.data())

        if font_id == -1:
            print(f"GA Line {inspect.currentframe().f_lineno} Failed to load font from memory!")
            logging.error("Failed to load font from base64 memory.")
            return None

        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
        print(f"GA Line {inspect.currentframe().f_lineno} Font loaded successfully from memory: {font_family}")
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

    def load_race_for_date(self, date):
        print(f"GA Line {inspect.currentframe().f_lineno} load race for date def entered with parameter: {date}")
        # Convert the selected date to a string in the format "YYYY-MM-DD"
        number_of_date_matches = 0
        selected_date_str = date.toString("yyyy-MM-dd")
        print(f"GA Line {inspect.currentframe().f_lineno} Selected date string: {selected_date_str}")
        # Convert the selected date to the desired format
        selected_date_converted = f"{date.day()}. {date.toString('MMMM').lower()} {date.year()}"
        print(f"GA Line {inspect.currentframe().f_lineno} Converted date: {selected_date_converted}")
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Searching for race on date: {selected_date_str}")
        print(f"GA Line {inspect.currentframe().f_lineno} Searching for race on date: {selected_date_str}")

        # Iterate through all items in the dropdown
        selected_index = -1  # Initialize to -1 to indicate no match found
        for index in range(self.dropdown_races.count()):
            item_text = self.dropdown_races.itemText(index)
            # Extract the date from the item text (assuming the date is after " - ")
            match = re.search(r"- (\d{4}-\d{2}-\d{2}) -", item_text)
            if match and match.group(1) == selected_date_str:
                selected_index = index  # Update the selected_index to the current match
                number_of_date_matches +=1
        # No need to break; the loop will continue to find the last match

        # If a matching race is found, process it
        if selected_index > 0:
            race_text = self.dropdown_races.itemText(selected_index)
            match = re.search(r"Race_(\d+)", race_text)
            if match:
                self.dato_selected_race_id = int(match.group(1))  # The number after "Race_"
                self.task_queue.put(('load_selected_race', (self.dato_selected_race_id,)))  # Queue the operation to DatabaseThread
                self.results_message_label.setText(f"Found {number_of_date_matches} Races on {selected_date_converted}, starting with {self.dato_selected_race_id}")
                self.dropdown_races.setCurrentIndex(selected_index)  # Set the selected index in the dropdown
                self.do_not_reset_index = True  # Prevent resetting the index in the dropdown
                number_of_date_matches = 0  # Reset the counter for the next search
                logging.info(f"GA Line {inspect.currentframe().f_lineno} GA Load selected race Signal Sent for Race ID: {self.dato_selected_race_id}")
                print(f"GA Line {inspect.currentframe().f_lineno} Selected Race ID: {self.dato_selected_race_id}")

        else:
            self.results_message_label.setText(f"No Race found for the selected date: {selected_date_str}")
            logging.info(f"GA Line {inspect.currentframe().f_lineno} No race found for the selected date: {selected_date_str}")
            print(f"GA Line {inspect.currentframe().f_lineno} No race found for the selected date: {selected_date_str}")

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
            print(f"GA Line {inspect.currentframe().f_lineno} Edit line focused, calling clear_driver_dropdown...")
            self.clear_driver_dropdown()  # Call your method
            return True  # Indicate that the event was handled
        # Pass other events to the default handler
        return super().eventFilter(obj, event)

    def delete_db(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Delete DB def entered")
        #print(f"GA Line {inspect.currentframe().f_lineno} Delete DB def entered
        self.task_queue.put(('delete_db', ()))
        self.set_delete_db_mode(True)
        QTimer.singleShot(5000, lambda: self.set_delete_db_mode(False))

    def delete_all_races(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Delete all races def entered")
        #print(f"GA Line {inspect.currentframe().f_lineno} Delete DB def entered
        self.task_queue.put(('delete_all_races', ()))
        self.set_delete_all_races_mode(True)
        QTimer.singleShot(1000, self.after_timer_race_deleted)
        QTimer.singleShot(5000, lambda: self.set_delete_all_races_mode(False))

    def set_delete_all_races_mode(self, is_active):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def set_delete_all_races_mode entered")
        if is_active:
            self.delete_all_races_button.setText("Deleting all races...")
            print(f"GA Line {inspect.currentframe().f_lineno} Deleting all Races...")
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
            print(f"GA Line {inspect.currentframe().f_lineno} Deleting all Races Completed...")
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
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def set_delete_db_mode entered")
        if is_active:
            self.delete_all_button.setText("Deleting DB...")
            print(f"GA Line {inspect.currentframe().f_lineno} Deleting DB...")
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
            print(f"GA Line {inspect.currentframe().f_lineno} Deleting DB Completed...")
            self.delete_all_button.setStyleSheet("""
                 font-size: 14px;
                 background-color: #a32d2d;
                 color: white;
                 margin-bottom: 5px;                             
                 border: 2px solid black;  /* Change the border color */
                 border-radius: 5px;  /* Optional: rounded corners */
            """) 
            
            self.delete_all_button.setEnabled(True)  
        
    def initialize_dropdown(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Initialize Dropdown def entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Initialize Dropdown def entered")
        self.task_queue.put(('load_race_data_on_start', ()))
        self.task_queue.put(('load_sessionid_on_start', ()))
        self.task_queue.put(('load_highscores_on_start', ()))
        self.task_queue.put(('load_driver_statistics_on_start', ()))
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Initialize Dropdown completed")
        print(f"GA Line {inspect.currentframe().f_lineno} Initialize Dropdown completed")
      
    def update_ip_address(self, ip_address):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Update IP Address def entered")
        #print(f"GA Line {inspect.currentframe().f_lineno} Update IP Address def entered")
        #self.ip_address = ip_address
        try:
            ip_last_segment = ip_address.split('.')[-1]
            if len(ip_last_segment) > 1:
                if int(ip_last_segment[-2:]) < 10 :
                    self.tab_widget.setTabText(0, f"Live Race Data: Sim-{ip_last_segment[-1]}")
                else:
                    self.tab_widget.setTabText(0, f"Live Race Data: Sim-{ip_last_segment[-2:]}")
            else:
                self.tab_widget.setTabText(0, f"Live Race Data: Sim-{ip_last_segment}")
        except Exception as e:
            logging.error(f"GA Line {inspect.currentframe().f_lineno} Error updating IP address: {e}")
            print(f"GA Line {inspect.currentframe().f_lineno} Error updating IP address: {e}")
            self.tab_widget.setTabText(0, f"Live Race Data: Sim-Error")
        # QTimer.singleShot(5000, lambda: self.status_label.clear())

    def update_session_id(self, session_id):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Update Session ID def entered with parameter: {session_id}")
        print(f"GA Line {inspect.currentframe().f_lineno} Update Session ID def entered with parameter: {session_id}")
        if session_id is not None:
            self.session_id = session_id
        self.live_heading.setText(f"Waiting for Race Start. Current Session: {self.session_id}")  # Update the status label
    
    def handle_session_type(self,session_type):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def handle session_type detected entered with parameter: {session_type}")
        print(f"GA Line {inspect.currentframe().f_lineno} Def handle session_type detected entered with parameter: {session_type}")
        self.live_heading.setText(f"{session_type} detected.")  # Update the status label
        self.session_type = session_type  # Store the session type for later use
    
    def handle_race_data_on_start(self, races, participants):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def handle race data on start entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def handle_race_data_on_start entered")
        self.dropdown_races.clear()  # Clear the dropdown first
        self.dropdown_races.addItem("Choose a race to view..")  # Add a default item
        if races:
            for race in reversed(races):  # Iterate over races in reverse order
                race_id, track_variation, laps_in_event, race_date = race
                # Find participants for the current race
                race_participants = [p for p in participants if p[0] == race_id]
                # Format participant car names and ensure uniqueness
                cars = ', '.join(sorted(set([p[1] for p in race_participants]))) if race_participants else "No participants"
                # Combine race and participant information into the dropdown item
                item_text = f"Race_{race_id} - {race_date} - {track_variation} Laps:{laps_in_event} - {cars}"
                self.dropdown_races.blockSignals(True)
                self.dropdown_races.addItem(item_text)
            self.dropdown_races.setCurrentIndex(0)
            self.dropdown_races.blockSignals(False)
            print(f"GA Line {inspect.currentframe().f_lineno} Number of races loaded: {len(races)}")
            if not len(races) >1: self.load_selected_race()
            else: self.results_heading.setText("\n Select a Race to View previous races") 
        else:  
            self.results_name.setText("No Races in DB")
            self.final_heading.setText("\n All races Deleted")     

    def handle_high_scores_data_on_start(self, high_scores):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def handle high scores data entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def handle high scores data entered")
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
            print(f"GA Line {inspect.currentframe().f_lineno} Number of high scores loaded: {len(high_scores)}")
            #print(f"High Scores Dictionary: {self.highscores_dict}")
        else:
            self.highscore_name.setText("No High Scores in DB")
        self.car_dropdown.blockSignals(False)
        self.track_dropdown.blockSignals(False)
        self.update_dropdowns()

    def load_selected_highscore(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} load_selected_highscore def entered")
        print(f"GA Line {inspect.currentframe().f_lineno} load_selected_highscore def entered")
        selected_car = self.car_dropdown.currentText()
        selected_track = self.track_dropdown.currentText()
        print(f"GA Line {inspect.currentframe().f_lineno} Selected Car: {selected_car} Selected Track: {selected_track}")
        if self.car_dropdown.currentIndex() >= 0 and self.track_dropdown.currentIndex() >= 0:
            self.task_queue.put(('load_highscores', (selected_car, selected_track)))
            print(f"GA Line {inspect.currentframe().f_lineno} Load score for {selected_car} on {selected_track}")
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Load score for {selected_car} on {selected_track}")
        else:
            print(f"GA Line {inspect.currentframe().f_lineno} Car or Track not selected:{selected_car} {selected_track}")
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Car or Track not selected:{selected_car} {selected_track}")

    def update_dropdowns(self):
            logging.info(f"GA Line {inspect.currentframe().f_lineno} update dropdowns def entered")
            print(f"GA Line {inspect.currentframe().f_lineno} update dropdowns def entered")
            self.car_dropdown.blockSignals(True)
            self.track_dropdown.blockSignals(True)
            sender = self.sender()
            
            # Clear the dropdowns before repopulating
            if sender == self.car_dropdown:
                self.track_dropdown.clear()
                selected_car = self.car_dropdown.currentText()

                # Populate the track dropdown based on the selected car
                for track, cars in self.highscores_dict.items():
                    if selected_car in cars:
                        self.track_dropdown.addItem(track)            
            else: # Populate the cars dropdown on track selection, as well as on initialization
            #if sender == self.track_dropdown:
                self.car_dropdown.clear()
                selected_track = self.track_dropdown.currentText()

                # Populate the car dropdown based on the selected track
                if selected_track in self.highscores_dict:
                    cars_for_track = self.highscores_dict[selected_track]
                    for car in cars_for_track:
                        self.car_dropdown.addItem(car)


            self.car_dropdown.blockSignals(False)
            self.track_dropdown.blockSignals(False)

    def clear_driver_dropdown(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} clear driver dropdown def entered")
        print(f"GA Line {inspect.currentframe().f_lineno} clear driver dropdown def entered")
        self.driver_dropdown.blockSignals(True)
        self.driver_dropdown.setItemText(0, "")
        self.driver_dropdown.setCurrentIndex(0)
        self.driver_dropdown.blockSignals(False)

    def handle_driver_statistics_on_start(self, driverdata):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def handle driver statistics on start entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def handle driver statistics on start entered")
        self.driver_dropdown.clear()  # Clear the dropdown first
        self.driver_dropdown.addItem("Select a driver or type a driver name...")
        self.driver_dropdown.blockSignals(True)
        self.driverdata = driverdata  # Store the driver data in a class variable
        if driverdata:
            for driver in driverdata:
                driver_name, lapnumber, bestlap, track, car = driver
                if driver_name not in [self.driver_dropdown.itemText(i) for i in range(self.driver_dropdown.count())]: self.driver_dropdown.addItem(driver_name)
            self.driver_dropdown.setCurrentIndex(0)
            print(f"GA Line {inspect.currentframe().f_lineno} Number of Highscores loaded: {len(driverdata)}")
            if len(driverdata) == 2: self.load_selected_driver()
            else: self.driver_statistics_heading.setText("\n Select a Driver to View Driver Statistics")
            self.all_driver_dropdown_items = [self.driver_dropdown.itemText(i) for i in range(1, self.driver_dropdown.count())]
        else:
            self.driver_statistics_heading.setText("\n No Driver Statistics in DB")
        self.driver_dropdown.blockSignals(False)

    def load_selected_driver(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} on driver statistics loaded def entered")
        print(f"GA Line {inspect.currentframe().f_lineno} on driver statistics loaded def entered")
        selected_driver = self.driver_dropdown.currentText()
        if self.driver_dropdown.currentIndex() > 0:
            print(f"GA Line {inspect.currentframe().f_lineno} Load driver statistics for {selected_driver} with index {self.driver_dropdown.currentIndex()}")
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Load driver statistics for {selected_driver}")
            driver = selected_driver
            heading = (f"<br><span style='color:{self.color_labels}'>Driver:</span> <span style='color:{self.color_values}'>{driver}</span><br>")
            loaded_lap = ''
            loaded_bestlap = ''
            loaded_track = ''
            loaded_car = ''
            if any(driver == record[0] for record in self.driverdata):
                print(f"GA Line {inspect.currentframe().f_lineno} Driver found: {driver}")
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
            print(f"GA Line {inspect.currentframe().f_lineno} Driver not selected:{selected_driver}")
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Driver not selected:{selected_driver}")
            return
        
    def load_selected_race(self): # Function to be called when the data is loaded
        print(f"GA Line {inspect.currentframe().f_lineno} Load Selected race def entered")
        logging.info(f"GA Line Load Selected race def entered")
        selected_index = self.dropdown_races.currentIndex()
        self.results_message_label.setText(f"") # Clear the message label
        if selected_index > 0:
            race_text = self.dropdown_races.itemText(selected_index)
            match = re.search(r"Race_(\d+)", race_text)
            self.selected_race_id = int(match.group(1))  # The number after "Race_"
            self.task_queue.put(('load_selected_race', (self.selected_race_id,) )) # Queue the operation to DatabaseThread
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Load selected race Signal Sent")
        else:
            print(f"GA Line {inspect.currentframe().f_lineno} Race not selected:{selected_index}")   
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Race not selected:{selected_index}")
        
    def on_race_loaded(self, race, participants, laps):
        logging.info(f"GA Line on race loaded def entered")
        race_id, track_variation, laps_in_event, session_id = race # Function to be called when the data is loaded
        #print(f"Signal received")
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Load selected race Signal received")
        loaded_names = ''
        loaded_places = ''
        loaded_flags = ''
        loaded_pitstops = ''
        loaded_totals = ''
        loaded_bestlap = ''
        loaded_points = ''
        #best_lap_time = {}

        if race_id:
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Load Selected Race, RaceID: {race_id}")
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

            if not participants:
                logging.info(f"GA Line {inspect.currentframe().f_lineno} No participants found for the selected race.")
                print(f"GA Line {inspect.currentframe().f_lineno} No participants found for the selected race.")
                self.results_heading.setText(heading)
                self.results_name.setText('No Participants')
                self.results_places.setText(loaded_places) 
                self.results_flags.setText(loaded_flags)
                self.results_pitstops.setText(loaded_pitstops)
                self.results_bestlap.setText(loaded_bestlap)
                self.results_total.setText(loaded_totals) 
                self.results_points.setText(loaded_points) 
                return  # Exit if no participants are found
            score_table = {int(k.split('_')[0]): int(v) for k, v in self.config['Score Table'].items() if k != 'best_lap'}
            best_lap_points = int(self.config['Score Table'].get('best_lap', 0)) 
            best_lap_participant = min(participants, key=lambda p: p[2] if p[2] not in (None, 0) else float('inf'))
            print(f"GA Line {inspect.currentframe().f_lineno} Best Lap Participant: {best_lap_participant[0]} with time: {best_lap_participant[2]}")

            place = 1
            for participant in participants:
                name, race_position, best_lap, last_lap, car, flags, pits = participant
                participant_laps = [lap for lap in laps if lap[2] == name]
                total_time_seconds = sum(lap[4] for lap in participant_laps)
                total_time_str = self.format_lap_time(total_time_seconds)
                best_lap_str = self.format_lap_time(best_lap)
                   
                if name in displayed_participants:
                    continue  # Skip duplicate participant names
                
                # Add participant info to the result string
                displayed_participants.add(name)
                #spaces = (f"<br> {'&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;' if int(race_position) > 9 else '&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;'}")
                flags = flags or ''
                pits = '' if pits == 0 else pits
                loaded_places += (f"<span style='color:{self.color_labels};'>{race_position}</span><br>")
                loaded_names += f"<span style='color:{self.color_labels};'>{name}{' <span style=\"color:blue; font-size:14px;\">(Best Lap + ' + str(best_lap_points) + ' points)</span>' if name == best_lap_participant[0] else ''}</span><br>"
                loaded_flags += (f"<span style='color:{self.color_dnf if flags == 'DNF' else self.color_falsestart};'> {flags} </span><br>")          
                loaded_pitstops += (f"<span style='color:{self.color_pitstop};'> {pits} </span><br>")
                loaded_totals += (f"<span style='color:{self.color_values};'> {total_time_str} </span><br>")
                loaded_bestlap += f"<span style='color:{'blue' if name == best_lap_participant[0] else self.color_values};'> {best_lap_str} </span><br>"
                bonus = best_lap_points if name == best_lap_participant[0] else 0
                loaded_points += str(score_table.get(place, 0) + bonus) + "<br>"
                place += 1 
                
           
            self.results_heading.setText(heading)  # Update the UI with the loaded results            
            self.results_places.setText(loaded_places) 
            self.results_name.setText(loaded_names)
            self.results_flags.setText(loaded_flags)
            self.results_pitstops.setText(loaded_pitstops)
            self.results_bestlap.setText(loaded_bestlap)
            self.results_total.setText(loaded_totals) 
            self.results_points.setText(loaded_points)
        if self.do_not_reset_index == False:    
            self.dropdown_races.setCurrentIndex(0)  # Might not work with delete selected race.
        self.do_not_reset_index = False # Reset the flag after processing

    def on_highscore_loaded(self, high_scores):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def on highscore loaded entered")
        #print(f"GA Line {inspect.currentframe().f_lineno} Def on highscore loaded entered", {'high_scores': high_scores})
        print(f"GA Line {inspect.currentframe().f_lineno} self.track_dropdown: {self.track_dropdown.currentText()} self.car_dropdown: {self.car_dropdown.currentText()}" )
        heading = (f"<span style='color:{self.color_labels}'>Track: </span><span style='color:{self.color_values}'>{self.track_dropdown.currentText()} </span><br><span style='color:{self.color_labels}'>Car: </span><span style='color:{self.color_values}'> {self.car_dropdown.currentText()}</span><br>" ) # Update the heading with track variation and car names
        if self.tab_widget.currentWidget() != self.highscore_view_widget:
            if high_scores != None:
                heading = (f"<span style='color:{self.color_labels}'>Track: </span><span style='color:{self.color_values}'>{high_scores[0][3]} </span><br><span style='color:{self.color_labels}'>Car: </span><span style='color:{self.color_values}'> {high_scores[0][4]}</span><br>" ) # Update the heading with track variation and car names
    
        print(f"GA Line {inspect.currentframe().f_lineno} High Scores variable self.highscores is set! ")
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
            print(f"GA Line {inspect.currentframe().f_lineno} Best Lap: {best_lap}")
            loaded_names += (f"<br><span style='color:{self.color_labels};'>Best Lap: </span><span style='color:{self.color_values};'> {best_lap} </span><br>")
            self.highscore_heading.setText(heading)
            self.highscore_places.setText(loaded_place)    
            self.highscore_name.setText(loaded_names)
            self.highscore_laptime.setText(loaded_lap)
        else:
            self.highscore_name.setText("No High Scores in DB")
            self.highscore_laptime.setText("No High Scores in DB")
        self.task_queue.put(('load_highscores_on_start',())) #Send the request to the DatabaseThread to load highscore data on start

    def handle_sessionid_data(self, sessionids):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def handle sessionid data entered")
        self.dropdown_sessionid.clear()  # Add this line to clear the dropdown
        self.sessionids = sessionids
        if sessionids:
            self.dropdown_sessionid.addItem("Use DropDown or Type ID:")  # Add explanatory text
            self.dropdown_sessionid.setCurrentIndex(0)  # Set it as the default selected item
            for session_id in reversed(sessionids):  # Iterate over sessionids in reverse order
                if len(sessionids) > 1:
                    self.dropdown_sessionid.blockSignals(True)
                self.dropdown_sessionid.addItem(f"Session ID - {session_id}")
                if len(sessionids) > 1:
                    self.dropdown_sessionid.blockSignals(False)
                
    def handle_automatic_session_assignment(self, session_id):
        """Handle automatic session assignment notification from database"""
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Automatic session assignment: {session_id}")
        print(f"GA Line {inspect.currentframe().f_lineno} Automatic session assignment: Session ID {session_id}")
        
        # Update the GUI to reflect the automatic assignment
        self.session_id = session_id
        self.world_record_label.setText(f"🤖 Auto-assigned Session {session_id} - Race Starting...")
        print(f"GA Line {inspect.currentframe().f_lineno} world_record_label updated with auto-assigned session {session_id} and label text: {self.world_record_label.text()}")
        # Show notification message
        participants_count = self.get_current_participant_count()
        if session_id == 1:
            status_msg = f"Single driver race → Session 1"
        elif participants_count > 1:
            status_msg = f"{participants_count} drivers → Session {session_id}"
        else:
            status_msg = f"Session {session_id} assigned"
        
        print(f"GA Line {inspect.currentframe().f_lineno} AUTO SESSION: {status_msg}")
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Automatic session assignment complete: {status_msg}")
        
    def get_current_participant_count(self):
        """Helper method to get current participant count for status messages"""
        try:
            # Try to get participant count from race_app if available
            if hasattr(self, 'race_app') and hasattr(self.race_app, 'current_participants'):
                return len(self.race_app.current_participants)
            return 0
        except:
            return 0
        
    def on_tab_changed(self, index):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
        #print(f"GA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
        if index == 0: self.update_background('live') # Handle other tab-specific logic, like background updates
        else:
            self.update_background('status')
        for widget_list in self.tab_widget_mapping.values(): # Hide all widgets first
            for widget_name in widget_list:
                if widget_name in self.labels:  # Check if the widget exists in the labels dictionary
                     self.labels[widget_name].hide()
        for widget_name in self.tab_widget_mapping.get(index, []): # Show only the widgets associated with the active tab
            if widget_name in self.labels:
                if self.hidebuttons != True:
                    self.labels[widget_name].show()
                else:
                    if (widget_name != 'new_session_button') and (widget_name != 'previous_session_button'):
                        self.labels[widget_name].show()
                
        if index == 0: self.update_background('live') # Handle other tab-specific logic, like background updates
        else:
            self.update_background('status')
        if index == 4:
            if self.all_driver_dropdown_items: # Check if the driver dropdown items have been loaded 
                for item in self.all_driver_dropdown_items:
                    self.driver_dropdown.addItem(item)
                self.driver_dropdown.setItemText(0, "Select a driver or type a driver name...")
                self.driver_dropdown.setCurrentIndex(0)
        self.tab_widget.setCurrentIndex(index)  # Set the current index of the tab widget
        print(f"GA Line {inspect.currentframe().f_lineno} Sending signal Tab: {index}")
        self.tab_changed.emit(index)  # Emit the signal with the new index
        #self.tab_widget.currentChanged.connect(lambda: self.tab_changed.emit(self.tab_widget.currentIndex()))
    
    def toggle_sim_radio_buttons(self, visible: bool):
        """Viser eller skjuler alle radio-knappene i sim_radio_group."""
        if hasattr(self, 'sim_radio_group'):
            for button in self.sim_radio_group.buttons():
                button.setVisible(visible)

    def update_background(self, view):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def update_background entered")
        if view == 'status': self.background_label.setPixmap(self.status_image)
        elif view == 'live': self.background_label.setPixmap(self.live_image)
    
    def update_api_status(self, status: bool, message: str = ""):
        if status:  # Error occurred
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Error message triggered")
            print(f"GA Line {inspect.currentframe().f_lineno} Error message triggered")

            if hasattr(self, 'error_label') and self.error_label.text() == message:
                return

            if hasattr(self, 'error_label'):
                self.error_label.deleteLater()

            self.error_label = QLabel(message, self)
            self.error_label.setAlignment(Qt.AlignCenter)
            self.error_label.setFixedSize(1060, 35)
            self.error_label.setStyleSheet("font-size: 18px; color: red; background-color: yellow; padding: 10px;")

            self.timer = QTimer(self)
            self.timer.timeout.connect(self.toggle_error_visibility)
            self.timer.start(500)
        else:  # Error cleared
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Error cleared")
            print(f"GA Line {inspect.currentframe().f_lineno} Error cleared")
            if hasattr(self, 'error_label'):
                self.error_label.deleteLater()
                del self.error_label
            if hasattr(self, 'timer') and self.timer.isActive():
                self.timer.stop()

    def handle_connection_restored(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def handle_connection_restored entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def handle_connection_restored entered")
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()

    def show_error_message(self, message): # Check if the error label already exists with the same message
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def show_error_message entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def show_error_message entered")
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
        #logging.info(f"GA Line Def toggle_error_visibility entered")
        #print(f"GA Line {inspect.currentframe().f_lineno} Def toggle_error_visibility entered")
        if hasattr(self, 'error_label') and self.error_label is not None:
            if self.error_label.isVisible(): self.error_label.setVisible(False)
            else: self.error_label.setVisible(True)
 
    def update_race_message(self, message):
        print(f"GA Line {inspect.currentframe().f_lineno} Race Message: {message}")
        #logging.info(f"GA Line {inspect.currentframe().f_lineno} RaceMessage: {message}")
        self.live_status_label.setText(f"{message}")  # Update the status label  

    def setup_result_view_setup(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_result_view entered")
        labels = [
            ("results_places",  "#",     60, 165, 100, 900, 22, False, False),
            ("results_name",    "Name",  100,165,1000,900, 22, False, False),
            ("results_flags",   "Flags", 490,165,150, 900, 22, False, False),
            ("results_pitstops","Pits",  620,165,15,  900, 22, False, True),
            ("results_bestlap", "Lap",   720,165,150, 900, 22, False, False),
            ("results_total",   "Total", 845,165,150, 900, 22, False, False),
            ("results_points",  "#",     965,165,15,  900, 22, False, True),
        ]
        self.setup_view(
            widget=self.results_view_widget,
            layout=self.results_view_layout,
            background_image=self.result_background_image,
            heading_text="\n Select a race to view previous races",
            heading_attr_name="results_heading",
            labels_info=labels
        )

    def setup_final_view_setup(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_final_view entered")
        labels = [
            ("final_places",  "#",      60, 165, 100, 900, 22, False, False),
            ("final_name",    "Name",   100,165,1000,900, 22, False, False),
            ("final_lastpos", "LastPos",490,165,150, 900, 22, False, False),
            ("final_points",  "#",      620,165,15,  900, 22, False, True),
            ("final_gold",    "Gold",   720,165,15,  900, 22, False, True),
            ("final_silver",  "Silver", 820,165,15,  900, 22, False, True),
            ("final_bronze",  "Bronze", 920,165,15,  900, 22, False, True),
        ]
        self.setup_view(
            widget=self.final_view_widget,
            layout=self.final_view_layout,
            background_image=self.final_background_image,
            heading_text="Select a session to view scores",
            heading_attr_name="final_heading",
            labels_info=labels
        )

    def setup_highscore_view_setup(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_highscore_view entered")
        labels = [
            ("highscore_places",  "#",       60, 165, 100, 900, 22, False, False),
            ("highscore_name",    "Name",   100,165,1000,900, 22, False, False),
            ("highscore_laptime", "Laptime",490,165,150, 900, 22, False, False),
        ]
        self.setup_view(
            widget=self.highscore_view_widget,
            layout=self.highscore_view_layout,
            background_image=self.highscore_background_image,
            heading_text="\n Select a track and car to view high Scores",
            heading_attr_name="highscore_heading",
            labels_info=labels
        )

    def setup_result_view(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_result_view entered")

        def create_label(text, x, y, w, h, center=False):
            label = QLabel(text, self.results_view_widget)
            label.setStyleSheet(f"font-family:{self.font_family};font-size: 22px;")
            label.setMinimumSize(w, h)
            alignment = Qt.AlignHCenter | Qt.AlignTop if center else Qt.AlignLeft | Qt.AlignTop
            label.setAlignment(alignment)
            label.move(x, y)
            return label

        # Bakgrunnsbilde
        self.result_background_label = QLabel(self.results_view_widget)
        self.result_background_label.setPixmap(QPixmap(self.result_background_image))
        self.result_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.results_view_layout.addWidget(self.result_background_label)
        self.results_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Heading
        self.results_heading = QLabel("\n Select a race to view previous races", self.results_view_widget)
        self.results_heading.setStyleSheet(f"font-family:{self.font_family};font-size: 22px;")
        self.results_heading.setMinimumSize(650, 200)
        self.results_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.results_heading.move(30, 15)

        # Liste over labels: (navn, tekst, x-posisjon, bredde, sentrert?)
        labels_info = [
            ("results_places",   "#",     60,  100, False),
            ("results_name",     "Name",  100, 1000, False),
            ("results_flags",    "Flags", 490, 150, False),
            ("results_pitstops", "Pits",  620, 15,  True),
            ("results_bestlap",  "Lap",   720, 150, False),
            ("results_total",    "Total", 845, 150, False),
            ("results_points",   "#",     965, 15,  True),
        ]

        for attr, text, x, w, center in labels_info:
            setattr(self, attr, create_label(text, x, 165, w, 900, center))

        # Statuslabel
        self.results_message_label = QLabel("", self.results_view_widget)
        self.results_message_label.setStyleSheet("font-size: 14px;font-weight:bold; color: red;")
        self.results_view_layout.addWidget(self.results_message_label)
        self.results_view_layout.addStretch(1)

    def setup_final_view(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_final_view entered")

        def create_label(text, x, y, w, h, center=False):
            label = QLabel(text, self.final_view_widget)
            label.setStyleSheet(f"font-family:{self.font_family};font-size: 22px;")
            label.setMinimumSize(w, h)
            alignment = Qt.AlignHCenter | Qt.AlignTop if center else Qt.AlignLeft | Qt.AlignTop
            label.setAlignment(alignment)
            label.move(x, y)
            return label

        # Bakgrunnsbilde
        self.final_background_label = QLabel(self.final_view_widget)
        self.final_background_label.setPixmap(QPixmap(self.final_background_image))
        self.final_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.final_view_layout.addWidget(self.final_background_label)
        self.final_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Heading
        self.final_heading = QLabel("Select a session to view scores", self.final_view_widget)
        self.final_heading.setStyleSheet(f"font-family:{self.font_family};font-size: 22px;")
        self.final_heading.setMinimumSize(650, 200)
        self.final_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.final_heading.move(30, 15)

        # Innholdslister: (attributtnavn, tekst, x-pos, bredde, sentrert?)
        labels_info = [
            ("final_places", "#",        60,  100,  False),
            ("final_name",   "Name",    100, 1000,  False),
            ("final_lastpos","LastPos", 490, 150,  False),
            ("final_points", "#",       620,   15,  True),
            ("final_gold",   "Gold",    720,   15,  True),
            ("final_silver", "Silver",  820,   15,  True),
            ("final_bronze", "Bronze",  920,   15,  True),
        ]

        for attr, text, x, w, center in labels_info:
            setattr(self, attr, create_label(text, x, 165, w, 900, center))

        # Statuslabel
        self.final_message_label = QLabel("", self.final_view_widget)
        self.final_message_label.setStyleSheet("font-size: 14px;font-weight:bold; color: red;")
        self.final_view_layout.addWidget(self.final_message_label)
        self.final_view_layout.addStretch(1)
  
    def setup_highscore_view(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_higscore_view entered")

        def create_label(text, x, y, w, h, center=False):
            label = QLabel(text, self.highscore_view_widget)
            label.setStyleSheet(f"font-family:{self.font_family};font-size: 22px;")
            label.setMinimumSize(w, h)
            alignment = Qt.AlignHCenter | Qt.AlignTop if center else Qt.AlignLeft | Qt.AlignTop
            label.setAlignment(alignment)
            label.move(x, y)
            return label

        # Bakgrunnsbilde
        self.highscore_background_label = QLabel(self.highscore_view_widget)
        self.highscore_background_label.setPixmap(QPixmap(self.highscore_background_image))
        self.highscore_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.highscore_view_layout.addWidget(self.highscore_background_label)
        self.highscore_view_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Heading
        self.highscore_heading = QLabel("\n Select a track and car to view high Scores", self.highscore_view_widget)
        self.highscore_heading.setStyleSheet(f"font-family:{self.font_family};font-size: 22px;")
        self.highscore_heading.setMinimumSize(650, 200)
        self.highscore_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.highscore_heading.move(30, 15)

        # Innholdsliste: (navn, tekst, x-posisjon, bredde, sentrert?)
        labels_info = [
            ("highscore_places",  "#",       60,  100,  False),
            ("highscore_name",    "Name",   100, 1000,  False),
            ("highscore_laptime", "Laptime", 490, 150,  False),
        ]

        for attr, text, x, w, center in labels_info:
            setattr(self, attr, create_label(text, x, 165, w, 900, center))
  
    def setup_driver_statistics_view(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_driver_statistics_view entered")

        def create_label(text, x, y, w, h):
            label = QLabel(text, self.driver_statistics_widget)
            label.setStyleSheet(f"font-family:{self.font_family};font-size: 14px;")
            label.setMinimumSize(w, h)
            label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
            label.move(x, y)
            return label

        # Bakgrunnsbilde
        self.driver_statistics_background_label = QLabel(self.driver_statistics_widget)
        self.driver_statistics_background_label.setPixmap(QPixmap(self.driver_statistics_background_image))
        self.driver_statistics_background_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.driver_statistics_layout.addWidget(self.driver_statistics_background_label)
        self.driver_statistics_layout.addSpacerItem(QSpacerItem(0, 0, QSizePolicy.Minimum, QSizePolicy.Expanding))

        # Heading
        self.driver_statistics_heading = QLabel("Select a driver to view statistics", self.driver_statistics_widget)
        self.driver_statistics_heading.setStyleSheet(f"font-family:{self.font_family};font-size: 22px;")
        self.driver_statistics_heading.setMinimumSize(650, 200)
        self.driver_statistics_heading.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.driver_statistics_heading.move(30, 15)

        # Labels (navn, tekst, x-pos, bredde)
        labels_info = [
            ("driver_statistics_track",   "Track",   45,   1000),
            ("driver_statistics_car",     "Car",     520,  1000),
            ("driver_statistics_laptime", "Laptime", 900,  150),
            ("driver_statistics_lap",     "Lap",     1015, 150),
        ]

        for attr, text, x, w in labels_info:
            setattr(self, attr, create_label(text, x, 165, w, 900))
   
    def setup_live_view(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_live_view entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def setup_live_view entered {self.session_id}")

        self.live_view_layout.setSpacing(5)
        self.live_view_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins to use full space

        def create_label(text, w=300, h=60, bold=False):
            label = QLabel(text, self.live_view_widget)
            style = f"font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);"
            if bold:
                style += "; font-weight: bold;"
            label.setStyleSheet(style)
            label.setMinimumSize(w, h)
            return label

        # Container for world record label (20px height, right-aligned)
        worldrecord_container = QWidget(self.live_view_widget)
        worldrecord_container.setFixedHeight(20)
        worldrecord_layout = QHBoxLayout(worldrecord_container)
        worldrecord_layout.setContentsMargins(0, 0, 0, 0)
        worldrecord_layout.setAlignment(Qt.AlignRight)

        self.world_record_label = create_label("Records", w=450, h=20, bold=True)
        worldrecord_layout.addWidget(self.world_record_label)

        self.live_view_layout.addWidget(worldrecord_container)

        # Container for status and best labels (20px height, left-aligned)
        status_container = QWidget(self.live_view_widget)
        status_container.setFixedHeight(20)
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setAlignment(Qt.AlignLeft)

        self.live_status_label = create_label("Race Messages...", w=325, h=20)
        status_layout.addWidget(self.live_status_label)

        self.live_best_label = create_label("Top Speed and Time:", w=600, h=20)
        status_layout.addWidget(self.live_best_label)

        self.live_view_layout.addWidget(status_container)

        # Container for heading
        heading_container = QWidget(self.live_view_widget)
        heading_container.setFixedHeight(65)
        heading_layout = QHBoxLayout(heading_container)
        heading_layout.setContentsMargins(0, 0, 0, 0)
        heading_layout.setAlignment(Qt.AlignLeft)

        self.live_heading = create_label(f"Waiting for a new race to start...Current Session: {self.session_id}", w=1000, h=60, bold=True)
        self.live_heading.setStyleSheet("font-size: 18px; font-weight: bold; color: black;")  # Restore original styling
        heading_layout.addWidget(self.live_heading)

        self.live_view_layout.addWidget(heading_container)

        # Flashing timer
        self.flash_timer = QTimer(self)
        self.flash_timer.timeout.connect(lambda: self.world_record_label.setVisible(not self.world_record_label.isVisible()))

        # Container for participant labels (uses remaining space)
        participant_container = QWidget(self.live_view_widget)
        participant_layout = QVBoxLayout(participant_container)
        participant_layout.setContentsMargins(0, 0, 0, 0)
        #participant_layout.setAlignment(Qt.AlignTop)

        self.participant_labels = {}
        for i in range(20):
            label = QLabel("", participant_container)
            label.hide()  # Hidden initially, shown later
            participant_layout.addWidget(label)
            self.participant_labels[i] = label

        participant_container.setLayout(participant_layout)
        self.live_view_layout.addWidget(participant_container)
        self.live_view_widget.setLayout(self.live_view_layout)
        #self.live_view_widget.setMinimumSize(1000, 500)  # Minimum height for all containers

        # Debug: Check initial positions
        #print(f"Worldrecord container y: {worldrecord_container.y()}, height: {worldrecord_container.height()}")
        #print(f"Status container y: {status_container.y()}, height: {status_container.height()}")
        #print(f"Heading container y: {heading_container.y()}, height: {heading_container.height()}")
        #if self.participant_labels:
        #    print(f"First participant label y: {self.participant_labels[0].y()}")
        #self.participant_labels[0].show()
        #print(f"First participant label y after show: {self.participant_labels[0].y()}")
        #print(f"Participant container y: {participant_container.y()}, height: {participant_container.height()}")
    
    def setup_driver_info_view(self):  # Setup your driver info view widgets here
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def setup_driver_info_view entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def setup_driver_info_view entered")
        font_name = self.font_family
        scaled_speedo = self.speedometer_image.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        scaled_tacho = self.tachometer_image.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.speedometer_label = QLabel(self.driver_info_tab)
        self.speedometer_label.setPixmap(scaled_speedo)
        self.speedometer_label.setFixedSize(scaled_speedo.size())
        self.speedometer_label.setStyleSheet("background: transparent;")
        self.speedometer_label.setAttribute(Qt.WA_TranslucentBackground)
        self.speedometer_label.move(25, 25)

        self.tachometer_label = QLabel(self.driver_info_tab)
        self.tachometer_label.setPixmap(scaled_tacho)
        self.tachometer_label.setFixedSize(scaled_tacho.size())
        self.tachometer_label.setStyleSheet("background: transparent;")
        self.tachometer_label.setAttribute(Qt.WA_TranslucentBackground)
        self.tachometer_label.move(210, 25)

        self.scaled_needle_image = self.needle_image.scaled(183, 183, Qt.KeepAspectRatio, Qt.SmoothTransformation)

        self.speed_needle_label = QLabel(self.speedometer_label)
        self.speed_needle_label.setPixmap(self.scaled_needle_image)
        self.speed_needle_label.setAttribute(Qt.WA_TranslucentBackground)
        self.speed_needle_label.setStyleSheet("background: transparent;")
        self.speed_needle_label.setFixedSize(self.scaled_needle_image.size())

        self.tacho_needle_label = QLabel(self.tachometer_label)
        self.tacho_needle_label.setPixmap(self.scaled_needle_image)
        self.tacho_needle_label.setAttribute(Qt.WA_TranslucentBackground)
        self.tacho_needle_label.setStyleSheet("background: transparent;")
        self.tacho_needle_label.setFixedSize(self.scaled_needle_image.size())

        speedo_center = QPoint(self.speedometer_label.width() // 2, self.speedometer_label.height() // 2)
        needle_center = self.scaled_needle_image.rect().center()
        self.speed_needle_label.move(speedo_center.x() - needle_center.x(), speedo_center.y() - needle_center.y())
        self.speed_needle_label.raise_()

        tacho_center = QPoint(self.tachometer_label.width() // 2, self.tachometer_label.height() // 2)
        self.tacho_needle_label.move(tacho_center.x() - needle_center.x(), tacho_center.y() - needle_center.y())
        self.tacho_needle_label.raise_()

        self.speed_display = QLabel(self.speedometer_label)
        self.speed_display.setFont(QFont(self.font_family_digits, 25))
        self.speed_display.setStyleSheet("color: red; background-color: black;")
        self.speed_display.setAttribute(Qt.WA_TranslucentBackground)
        self.speed_display.setAlignment(Qt.AlignCenter)
        self.speed_display.setFixedSize(50, 30)
        self.speed_display.move(int(self.speedometer_label.width() * 0.55), int(self.speedometer_label.height() * 0.67))

        self.gear_display = QLabel(self.tachometer_label)
        self.gear_display.setFont(QFont(self.font_family_digits, 32))
        self.gear_display.setStyleSheet("color: red; background-color: black;")
        self.gear_display.setAttribute(Qt.WA_TranslucentBackground)
        self.gear_display.setAlignment(Qt.AlignCenter)
        self.gear_display.setFixedSize(50, 30)
        self.gear_display.move(int(self.tachometer_label.width() * 0.55), int(self.tachometer_label.height() * 0.67))

        pedal_x = self.tachometer_label.x() + self.tachometer_label.width() + 30
        base_y = self.tachometer_label.y()

        # Øverst i metoden eller klassen
        drvtxt_x = 25
        drvtxt_y = 620
        drvtxt_spacing = 40
        heading_font = f"font-family:{font_name};font-size: 22px;"
        value_font = f"font-family:{font_name};font-size: 22px; color: red;"

        # Liste over (labeltekst, labelnavn, tekstnavn, Minimum_size(Heading width), value_x (Heading width), mintxt_x (text width))
        driver_info_fields = [
            ("Car:", "car_heading_text", "car_txt", 53, 400),
            ("Driver:", "driver_heading_text", "driver_txt", 82, 300),
            ("Crash:", "collison_heading_text", "collison_txt", 82, 300),
            ("World Record:", "worldrecord_heading_text", "worldrecord_txt", 180, 300),
            ("Local Record:", "localrecord_heading_text", "localrecord_txt", 180, 400),
            ("Flags:", "flags_heading_text", "flags_txt", 82, 200),
            ("Track:", "track_heading_text", "track_txt", 80, 600),
        ]

        for i, (label_text, heading_attr, value_attr, min_x, mintxt_x) in enumerate(driver_info_fields):
            y_pos = drvtxt_y + i * drvtxt_spacing
            value_x = drvtxt_x + min_x

            heading_label = QLabel(label_text, self.driver_info_tab)
            heading_label.setStyleSheet(heading_font)
            heading_label.setMinimumSize(min_x, 50)
            heading_label.move(drvtxt_x, y_pos)
            setattr(self, heading_attr, heading_label)

            value_label = QLabel(label_text[:-1], self.driver_info_tab)  # f.eks. "Car" fra "Car:"
            value_label.setStyleSheet(value_font)
            value_label.setMinimumSize(mintxt_x, 50)
            value_label.move(value_x, y_pos)
            setattr(self, value_attr, value_label)


        self.pedals_bg = QLabel(self.driver_info_tab)
        self.pedals_bg.setPixmap(self.pedals_image)
        self.pedals_bg.setScaledContents(True)
        self.pedals_bg.setFixedSize(100, 110)
        self.pedals_bg.move(pedal_x - 10, base_y)
        self.pedals_bg.lower()

        self.clutch_bar = QProgressBar(self.pedals_bg)
        self.brake_bar = QProgressBar(self.pedals_bg)
        self.throttle_bar = QProgressBar(self.pedals_bg)

        for bar, color, offset in zip([self.clutch_bar, self.brake_bar, self.throttle_bar], ['blue', 'red', 'green'], [0, 30, 60]):
            bar.setOrientation(Qt.Vertical)
            bar.setRange(0, 100)
            bar.setGeometry(offset + 10, 8, 20, 70)  # Leave 10px padding at top
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background: transparent;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            bar.setTextVisible(False)
            bar.raise_()


        self.pedals_raw_bg = QLabel(self.driver_info_tab)
        self.pedals_raw_bg.setPixmap(self.pedals_raw_image)
        self.pedals_raw_bg.setScaledContents(True)
        self.pedals_raw_bg.setFixedSize(100, 110)
        self.pedals_raw_bg.move(pedal_x - 10, self.pedals_bg.height()+30)
        self.pedals_bg.lower()
        self.clutch_raw_bar = QProgressBar(self.pedals_raw_bg)
        self.brake_raw_bar = QProgressBar(self.pedals_raw_bg)
        self.throttle_raw_bar = QProgressBar(self.pedals_raw_bg)

        for bar_raw, color, offset in zip([self.clutch_raw_bar, self.brake_raw_bar, self.throttle_raw_bar], ['blue', 'red', 'green'], [0, 30, 60]):
            bar_raw.setOrientation(Qt.Vertical)
            bar_raw.setRange(0, 100)
            bar_raw.setGeometry(offset + 10, 8, 20, 70)  # Leave 10px padding at top
            bar_raw.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background: transparent;
                }}
                QProgressBar::chunk {{
                    background-color: {color};
                }}
            """)
            bar_raw.setTextVisible(False)
            bar_raw.raise_()
        #Create Player race position labels and text          
        
        # Define layout origin variables
        bg_spacing = 10
        font_size = 42
        font_color = "red"
        font_family = self.font_family_digits

        # Posisjoneringshjelpere
        lap_x = pedal_x + self.pedals_bg.width() + 60
        lap_y = 75

        # Elementspesifikasjon (bilde, tekst, font, alignment, justeringer)
        driver_info_bgs = [
            ("pos", self.pos_image, "0", font_size + 20, Qt.AlignCenter, self.pedals_raw_bg.x() - int((self.pos_image.width() - self.pedals_raw_bg.width())/2), self.pedals_raw_bg.y() + self.pedals_raw_bg.height() + bg_spacing),
            ("lap", self.lap_image, "0/0", font_size, Qt.AlignCenter, lap_x, lap_y),
            ("laptime", self.laptime_image, "0:00.00", font_size, Qt.AlignLeft, lap_x, lap_y + self.lap_image.height() + bg_spacing),
            ("bestlaptime", self.bestlaptime_image, "0:00.00", font_size, Qt.AlignCenter, lap_x, lap_y + 2 * self.laptime_image.height() + 2 * bg_spacing),
            ("deltaworldrecord", self.delta_world_record_image, "0:00.00", font_size, Qt.AlignCenter, lap_x, lap_y + 3 * self.lap_image.height() + 3 * bg_spacing),
            ("deltalocalrecord", self.delta_local_record_image, "0:00.00", font_size, Qt.AlignCenter, lap_x, lap_y + 4 * self.lap_image.height()  + 4 * bg_spacing),
            ("remaining", self.remaining_image, "0:00.00", font_size, Qt.AlignLeft, lap_x, lap_y + 5 * self.lap_image.height() + 5 * bg_spacing),
        ]

        for name, pixmap, text, fsize, align, pos_x, pos_y in driver_info_bgs:
            bg_label = QLabel(self.driver_info_tab)
            bg_label.setPixmap(pixmap)
            bg_label.setFixedSize(pixmap.size())
            bg_label.move(pos_x, pos_y)
            setattr(self, f"{name}_bg", bg_label)

            txt_label = QLabel(text, bg_label)
            txt_label.setFont(QFont(font_family, fsize))
            txt_label.setStyleSheet(f"color: {font_color}; background: transparent;")
            txt_label.setAlignment(align)
            # Adjust Y position: lap=-15, pos=-15 (up), remaining=20 (lower), laptime=20 (lower), others=-5
            y_offset = -15 if name == "lap" else (-15 if name == "pos" else (20 if name in ["remaining", "laptime"] else -5))
            txt_label.setGeometry(25 if align == Qt.AlignLeft else 0, y_offset, pixmap.width(), pixmap.height())
            txt_label.raise_()
            setattr(self, f"{name}_text", txt_label)

        # Create the wheels image with tire temperatures
        wheels_x = self.pedals_raw_bg.x() - int((self.pos_image.width() - self.pedals_raw_bg.width())/2) - int((self.wheels_image.width()-self.pos_image.width()) /2)
        wheels_y = self.pedals_raw_bg.y() + self.pedals_raw_bg.height() + self.pos_image.height() + 2* bg_spacing

        self.wheels_label = QLabel(self.driver_info_tab)
        self.wheels_label.setPixmap(self.wheels_image)
        self.wheels_label.setFixedSize(self.wheels_image.size())
        self.wheels_label.move(wheels_x, wheels_y)

        # Create tire temperature labels for each wheel (Left front, Right front, Left back, Right back)
        temp_font_size = 14
        temp_color = "yellow"
        temp_font = QFont(font_family, temp_font_size)
        
        # Positions for tire temp labels (adjust these based on your wheels image layout)
        #1 - Tire name (for attribute naming)
        #2 - X position (horizontal position from left edge of the wheels_label)
        #3 - Y position (vertical position from top edge of the wheels_label)
        
        tire_positions = [
            ("left_front", 5, 5),    # Left front tire
            ("right_front", 125, 5),  # Right front tire  
            ("left_back", 5, 175),    # Left back tire
            ("right_back", 125, 175)   # Right back tire
        ]
        
        for tire_name, x_pos, y_pos in tire_positions:
            temp_label = QLabel("0.0°", self.wheels_label)
            temp_label.setFont(temp_font)
            temp_label.setStyleSheet(f"color: {temp_color}; background: rgba(0, 0, 0, 150); border-radius: 3px; padding: 2px;")
            temp_label.setAlignment(Qt.AlignCenter)
            temp_label.setFixedSize(45, 20)
            temp_label.move(x_pos, y_pos)
            temp_label.raise_()
            setattr(self, f"{tire_name}_temp_label", temp_label)

        # Create tire overlay labels for visual temperature representation
        #1 - X position (horizontal position from left edge of the wheels_label)
        #2 - Y position (vertical position from top edge of the wheels_label)
        #3 - Width of the overlay in pixels
        #4 - Height of the overlay in pixels
        tire_overlay_positions = [
            ("left_front_overlay", 10, 10, 50, 87),    # Left front tire overlay
            ("right_front_overlay", 110, 10, 50, 87),  # Right front tire overlay
            ("left_back_overlay", 10, 108, 50, 87),    # Left back tire overlay
            ("right_back_overlay", 110, 108, 50, 87)   # Right back tire overlay
        ]
        
        for overlay_name, x_pos, y_pos, width, height in tire_overlay_positions:
            overlay_label = QLabel("", self.wheels_label)
            overlay_label.setStyleSheet("background: rgba(0, 0, 0, 0); border-radius: 8px;")  # Start invisible
            overlay_label.setFixedSize(width, height)
            overlay_label.move(x_pos, y_pos)
            overlay_label.lower()  # Place behind temperature labels
            setattr(self, f"{overlay_name}", overlay_label)

        # Create the wheel image and label
        self.wheel_label = QLabel(self.driver_info_tab)
        self.wheel_label.setPixmap(self.wheel_image)
        self.wheel_label.setFixedSize(self.wheel_image.size())
        self.wheel_label.move(pedal_x + 420, base_y + 50)

    def get_tire_color(self, temp):
        """Calculate tire color based on temperature:
        0-20°C: Pure blue (very cold tires)
        20-85°C: Blue to cyan to green transition
        85-95°C: Invisible (optimal range)
        95-135°C: Yellow to red (hot tires)"""
        
        # Cold tires: 0-85°C (blue to cyan to green)
        if temp <= 85:
            # Clamp temperature to 0-85°C range
            temp = max(0, min(temp, 85))
            
            # Keep pure blue from 0-20°C, then transition to green from 20-85°C
            if temp <= 20:
                # Pure blue for very cold tires (0-20°C)
                return "rgb(0, 0, 255)"
            else:
                # Transition from blue to cyan to green (20-85°C)
                # Normalize temperature to 0-1 range (20°C = 0, 85°C = 1)
                normalized_temp = (temp - 20) / (85 - 20)
                
                # Interpolate from blue (0,0,255) through cyan to bright green (104,187,57)
                # This creates: blue -> cyan -> green transition
                red = int(104 * normalized_temp)  # 0 to 104
                green = int(255 * normalized_temp * 0.7 + 187 * normalized_temp * 0.3)  # Creates cyan transition
                blue = int(255 * (1 - normalized_temp) + 57 * normalized_temp)  # 255 to 57
                
                return f"rgb({red}, {green}, {blue})"
        
        # Invisible range: 85-95°C
        elif temp < 95:
            return "rgba(0, 0, 0, 0)"  # Completely transparent
        
        # Hot tires: 95-135°C (yellow to red)
        else:
            # Clamp temperature to 95-135°C range
            temp = max(95, min(temp, 135))
            # Normalize temperature to 0-1 range (95°C = 0, 135°C = 1)
            normalized_temp = (temp - 95) / (135 - 95)
            
            # Interpolate between yellow (255,255,0) and bright red (255,0,0)
            red = 255
            green = int(255 * (1 - normalized_temp))  # 255 to 0
            blue = 0
            
            return f"rgb({red}, {green}, {blue})"

    def update_tire_temperatures(self, tire_temps):
        """Update tire temperature labels with values and colors"""
        tire_names = ["left_front", "right_front", "left_back", "right_back"]
        
        for i, tire_name in enumerate(tire_names):
            temp = tire_temps[i] if i < len(tire_temps) else 0.0
            color = self.get_tire_color(temp)
            
            # Update temperature label
            temp_label = getattr(self, f"{tire_name}_temp_label", None)
            if temp_label:
                temp_label.setText(f"{temp:.1f}°")
                
                # Set text color based on temperature range
                if 85 <= temp < 95:
                    # Optimal range: use white text for good visibility
                    text_color = "Yellow"  # Use yellow for optimal range
                elif temp < 85:
                    # Cold tires: use same color as overlay for consistency
                    text_color = "Yellow"
                else:
                    # Hot tires: use same color as overlay for consistency
                    text_color = color
                
                temp_label.setStyleSheet(f"color: {text_color}; background: rgba(0, 0, 0, 150); border-radius: 3px; padding: 2px;")
            
            # Update overlay color
            overlay_label = getattr(self, f"{tire_name}_overlay", None)
            if overlay_label:
                # Check if temperature is in invisible range (85-95°C)
                if 85 <= temp < 95:
                    overlay_label.setStyleSheet("background: rgba(0, 0, 0, 0); border-radius: 8px;")  # Invisible
                else:
                    # Visible overlay with color for both cold (0-85°C) and hot (95°C+) tires
                    # Convert rgb color to rgba with transparency
                    if color.startswith("rgb("):
                        # Extract RGB values and convert to RGBA with 60% opacity (153 out of 255)
                        rgb_values = color[4:-1]  # Remove 'rgb(' and ')'
                        rgba_color = f"rgba({rgb_values}, 165)"
                        overlay_label.setStyleSheet(f"background: {rgba_color}; border-radius: 8px;")
                    else:
                        # Fallback for rgba colors (shouldn't happen in this case)
                        overlay_label.setStyleSheet(f"background: {color}; border-radius: 8px;")  # Visible with color
     
    def set_monitored_ip(self, ip_index):
        if 0 <= ip_index < len(self.available_ips):
            self.current_ip = self.available_ips[ip_index]
            print(f"GA Line {inspect.currentframe().f_lineno} set_monitored_ip: {self.current_ip}")
            self.config_manager.update_ip_address(self.current_ip) #Will be updated later with a signal from the main window
            #self.reconnect_to_ip()
   
    def display_final_results(self, race_valid, session_id): # Display the score data in the final view
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def display_final_results entered")
        self.live_status_label.setText("Waiting for a new race to start...")  # Update the status label"
        self.hidebuttons =False
        self.final_message_label.setText("") # Clear any existing error message if the connection is successful
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop() 
        if race_valid:
            print(f"GA Line {inspect.currentframe().f_lineno} Race finished for session ID: {session_id}")
            # self.initialize_dropdown()
            self.task_queue.put(('load_score_data',(session_id,))) # Get data I need to calculate score (New Session ID button must not be pushed before this))
            self.world_record_label.setText(f"Race with session ID {session_id} is finished.")

    def qualify_finished(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def qualify_finished entered")
        self.live_status_label.setText("Qualifying Finished! Waiting for Race to start...")  # Update the status label"
        self.hidebuttons = False
    
    def practice_finished(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def practice_finished entered")
        self.live_status_label.setText("Practice Finished! Waiting for Qualifying to start...")  # Update the status label"
        self.hidebuttons = False

    def display_score(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Display Score Result def entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Display score Result def entered")
        self.selected_index = self.dropdown_sessionid.currentIndex()
        sessionid_text = self.dropdown_sessionid.itemText(self.selected_index)
        self.session_id_dropdown = int(re.search(r'\d+', self.dropdown_sessionid.itemText(self.selected_index)).group()) if re.search(r'\d+', self.dropdown_sessionid.itemText(self.selected_index)) else 0
        print(f"GA Line {inspect.currentframe().f_lineno} Selected Index: {self.selected_index} Selected session text: {sessionid_text} Extracted session_ID: {self.session_id_dropdown}")
        self.final_message_label.setText("") # Clear any existing error message if the connection is successful
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()
        if 0 < self.session_id_dropdown and hasattr(self, 'sessionids') and self.session_id_dropdown in self.sessionids: # Check if the session ID is valid and exists in available sessions
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Get score Data. Session ID: {self.session_id_dropdown}")
            print(f"GA Line {inspect.currentframe().f_lineno} Get score Data. Session ID: {self.session_id_dropdown}")
            self.task_queue.put(('load_score_data',(self.session_id_dropdown,))) #Get data I need to calculate score (New Session ID button must not be pushed before this))
        else:
            self.final_message_label.setText(f"No valid session ID selected")
            self.session_id_dropdown = None         
            logging.info(f"GA Line {inspect.currentframe().f_lineno} No valid session ID selected")
            print(f"GA Line {inspect.currentframe().f_lineno} No valid session ID selected.")
        if "Session ID -" not in sessionid_text: # Check if the session ID contains a '-'
            print(f"GA Line {inspect.currentframe().f_lineno} Manually typed ID. Index will be removed from the dropdown list")
            if self.dropdown_sessionid.currentIndex() != 0:
                self.dropdown_sessionid.removeItem(self.selected_index) # Remove the manually typed ID from the dropdown
        self.dropdown_sessionid.setCurrentIndex(0)
        # logging.info(f"GA Line {inspect.currentframe().f_lineno} Accumulated Score for Session {self.session_id_dropdown}")
    
    def format_lap_time(self, lap_time): # Helper function to format lap time from seconds to 'MM:SS.ss' format.
        if lap_time is None or lap_time == -123.0: return "N/A"
        minutes = int(lap_time // 60)
        seconds = lap_time % 60
        return f"{minutes}:{seconds:05.2f}"        
    
    def calculate_score(self, races, participants, laps):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def calculate_score entered")
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
                    print(f"GA Line {inspect.currentframe().f_lineno} No participants found for race {race_id}. Skipping score calculation for this race.")
                    logging.info(f"GA Line {inspect.currentframe().f_lineno} No participants found for race {race_id}. Skipping score calculation for this race.")
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
            logging.info(f"GA Line {inspect.currentframe().f_lineno} Ranked drivers: {self.ranked_drivers}")
        else:
            print(f"GA Line {inspect.currentframe().f_lineno} No races in database, displaying next session info")                
            #self.session_id_updated.emit(self.session_id)
            #self.final_heading.setText(f"<span style='color:{self.color_labels}'>Next Race will be session: </span><span style='color:{self.color_values}'>{self.session_id}</span>")
            heading = (
            f"<span style='color:{self.color_labels}'>Session:</span>"
            f"<span style='color:{self.color_values}'> {self.session_id}</span> "
            f"<span style='color:{self.color_labels}'>Next Race will be session: </span>"
            f"<span style='color:{self.color_values}'> {self.session_id}</span><br>"  
            f"<span style='color:{self.color_labels}'> </span> "     
            f"<span style='color:{self.color_values}'>Select from Dropdown to view a session</span> <br>"
            f"<span style='color:{self.color_labels}; font-size: 16px;'>Races: </span>"
            f"<span style='color:{self.color_values}; font-size: 16px;'> (No races in this session yet!) </span>")
            
            self.final_heading.setText(heading)
            self.final_places.setText('') 
            self.final_name.setText('')  
            self.final_lastpos.setText('')  
            self.final_points.setText('')
            self.final_gold.setText('')
            self.final_silver.setText('')
            self.final_bronze.setText('')

    def format_score_view(self, total_scores, race_count, last_positions, medal_counts, races):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def format_score_view entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Def format_score_view entered")
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
        print(f"GA Line {inspect.currentframe().f_lineno} Self session id dropdown: {self.session_id_dropdown}")
        print(f"GA Line {inspect.currentframe().f_lineno} Self session id: {self.session_id}")
        heading = (
            f"<span style='color:{self.color_labels}'>Session:</span>"
            f"<span style='color:{self.color_values}'> "
            f"{self.session_id_dropdown if self.session_id_dropdown is not None else self.session_id}</span> "
            f"<span style='color:{self.color_labels}'>Next Race will be session: </span>"
            f"<span style='color:{self.color_values}'> {self.session_id}</span><br>"  
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
            #print(f"GA Line {inspect.currentframe().f_lineno} Participant: {mName} - Score: {score} - Last Position: {last_pos} - Gold: {gold} - Silver: {silver} - Bronze: {bronze}")

            loaded_places += (f"<span style='color:{self.color_labels};'>{i}</span><br>")
            loaded_names += (f"<span style='color:{self.color_labels};'>{mName}</span><br>")
            loaded_lastpos += (f"<span style='color:{self.color_lastpos};'> {last_pos} </span><br>")
            loaded_points += (f"<span style='color:{self.color_scores};'> {score} </span><br>")                      
            loaded_gold += (f"<span style='color:{self.color_gold};'> {gold} </span><br>")
            loaded_silver += (f"<span style='color:{self.color_silver};'> {silver} </span><br>")
            loaded_bronze += (f"<span style='color:{self.color_bronze};'> {bronze} </span><br>")

        if not self.hidebuttons: self.live_status_label.setText("Score Calculated! for session: " + str(self.session_id))
        self.final_heading.setText(heading)  # Update the UI with the loaded results        
        self.final_places.setText(loaded_places)
        self.final_name.setText(loaded_names)
        self.final_lastpos.setText(loaded_lastpos)
        self.final_points.setText(loaded_points)
        self.final_gold.setText(loaded_gold) 
        self.final_silver.setText(loaded_silver)
        self.final_bronze.setText(loaded_bronze)
        self.session_id_dropdown = None 

    def delete_selected_race(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Delete selected race def entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Delete selected race def entered")
        # selected_index = self.dropdown_races.currentIndex()
        if self.selected_race_id > 0:

            def on_race_deleted(race_id):
                print(f"GA Line {inspect.currentframe().f_lineno} Should only see this once")
                logging.info(f"GA Line {inspect.currentframe().f_lineno} Should only see this once")
                if race_id is not None:
                    self.initialize_dropdown()
                else:
                    print(f"GA Line {inspect.currentframe().f_lineno} on_race_deleted:Race_id is None:{race_id}")
                    logging.info(f"GA Line {inspect.currentframe().f_lineno} on_race_deleted:Race_id is None:{race_id}")
 
            self.set_delete_mode(True)  # Activates delete mode
            self.task_queue.put(('delete_race', (self.selected_race_id, on_race_deleted))) #Send request to DatabaseThread
            QTimer.singleShot(1000,lambda: self.set_delete_mode(False))
            QTimer.singleShot(1000, self.after_timer_race_deleted)
        else:
            print(f"GA Line {inspect.currentframe().f_lineno} NO valid race selected.")

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
        logging.info(f"GA Line {inspect.currentframe().f_lineno} GA Delete selected driver def entered")
        selected_index = self.driver_dropdown.currentIndex()
        if selected_index > 0:
            driver_text = self.driver_dropdown.itemText(selected_index)

            def on_driver_deleted(driver_text):
                print(f"GA Line {inspect.currentframe().f_lineno} Should only see this once")
                logging.info(f"GA Line Should only see this once")
                if driver_text is not None:
                    self.initialize_dropdown()
                else:
                    print(f"GA Line {inspect.currentframe().f_lineno} on_driver_deleted:Driver_text is None:{driver_text}")
                    logging.info(f"GA Line {inspect.currentframe().f_lineno} on_driver_deleted:Driver_text is None:{driver_text}")

            self.task_queue.put(('delete_driver', (driver_text, on_driver_deleted))) #Send request to DatabaseThread
            QTimer.singleShot(1000, self.after_timer_driver_deleted)

    def after_timer_driver_deleted(self):
        new_text= "\n" "Driver Deleted"
        self.driver_statistics_heading.setText(new_text)
        self.driver_statistics_track.setText('') 
        self.driver_statistics_car.setText('')
        self.driver_statistics_laptime.setText('')
        self.driver_statistics_lap.setText('')

    def set_delete_mode(self, is_active):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def set_delete_mode entered")
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
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def start_new_session entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Start new session entered")
        self.update_session_id_from_button.emit('increase')  # Emit the signal to update the session ID from the buttons
        
    def previous_session(self):
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Def previous_session entered")
        print(f"GA Line {inspect.currentframe().f_lineno} Previous session entered")
        self.update_session_id_from_button.emit('decrease')

    def closeEvent(self, event):
        self.stop()
        event.accept()
        
    def stop(self):
        print(f"GA Line {inspect.currentframe().f_lineno} Closing the application...")
        app.quit() # Quit the application immediately.
        if hasattr(self, 'db_thread') and self.db_thread.isRunning(): # Stop the database thread if it exists and is running
            logging.info("Stopping DatabaseThread...")
            self.db_thread.stop()
            self.db_thread.wait()  # Wait for the thread to finish
            print(f"GA Line {inspect.currentframe().f_lineno} Database thread stopped.")
        logging.info("Stopping MonitorThread...")
        print(f"GA Line {inspect.currentframe().f_lineno} Stopping MonitorThread...")
        if hasattr(self, 'monitor_thread'):
            try:
                self.monitor_thread.data_updated.disconnect()
                self.monitor_thread.race_finished.disconnect()
            except TypeError:
                pass  # Signals might already be disconnected or not connected
        if hasattr(self, 'monitor_thread') and self.monitor_thread.isRunning(): # Stop the monitor thread if it exists and is running
                self.monitor_thread.running = False
                print(f"GA Line {inspect.currentframe().f_lineno} Running self monitor thread stop")
                self.monitor_thread.wait()  # Wait for the thread to finish
                print(f"GA Line {inspect.currentframe().f_lineno} Monitor thread stopped.")
                pass  # Signals might already be disconnected or not connected
        logging.info(f"GA Line {inspect.currentframe().f_lineno} Application stopped successfully.") # Log completion of stopping sequence

class RaceApp(QThread):
    gui_realtime_update = pyqtSignal(object)
    session_id_updated = pyqtSignal(int)
    participant_update = pyqtSignal(int, str)
    gui_update = pyqtSignal(list)
    hide_buttons = pyqtSignal()
    get_request_for_sim_signal = pyqtSignal()
    radio_button_update = pyqtSignal(list)  # Signal to update radio button text
    pit_stops_updated = pyqtSignal(dict)

    def __init__(self, monitor_thread, task_queue, config_manager, db_thread, control_panel, parent=None, tab_widget=None, gui_main_app=None):
        super().__init__(parent)
        self.task_queue = task_queue
        self.monitor_thread = monitor_thread
        self.config_manager = config_manager
        self.db_thread = db_thread
        self.control_panel = control_panel
        self.tab_widget = tab_widget
        self.gui_main_app = gui_main_app or GuiMainApp.get_instance()

        logging.info(f"RA Line {inspect.currentframe().f_lineno} RaceApp __init__ called")
        print(f"RA Line {inspect.currentframe().f_lineno} RaceApp __init__ called")
        self.connect_signals()
        self.init_state_variables()

    def connect_signals(self):
        self.monitor_thread.flags_updated.connect(self.update_flags)
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.data_updated.connect(self.update_driver_view)
        self.db_thread.send_recordlaps_signal.connect(self.on_record_laps_loaded)
        self.db_thread.load_sessionid_on_start_signal.connect(self.handle_sessionid_data)
        #self.gui_main_app.session_id_updated.connect(self.handle_latest_session_id)
        self.monitor_thread.session_type_updated.connect(self.handle_session_type)
        self.monitor_thread.ip_address_updated.connect(self.update_ip_address)
        self.gui_main_app.tab_changed.connect(self.tab_changed)
        #self.control_panel.driver_sims_updated.connect(self.update_driver_names)
        self.monitor_thread.qualify_finished.connect(self.session_finished)
        self.monitor_thread.practice_finished.connect(self.session_finished)
        self.monitor_thread.race_finished.connect(self.session_finished)
        self.monitor_thread.active_computers_signal.connect(self.update_driver_names)
        self.monitor_thread.multi_data_signal.connect(self.handle_multi_data)
        self.monitor_thread.session_id_updated.connect(self.update_session_id)

    def init_state_variables(self):
        self.running = True
        self.speedo_max = 320
        self.speedo_sweep = (0, 225)
        self.tacho_max = 14000
        self.tacho_sweep = (0, 245)
        self.active_tab = 0
        self.live_first_time_run = True
        self.gui = GuiMainApp.get_instance()
        self.live_first_time_run_done = False
        self.on_first_live_run_started = False
        self.new_local_record = False
        self.worldrecordsupdated = False 

    def handle_multi_data(self, data):
        #logging.info(f"RA Line {inspect.currentframe().f_lineno} Def handle_multi_data entered")
        #print(f"RA Line {inspect.currentframe().f_lineno} Def handle_multi_data entered")
        self.multi_data = data
        if not self.worldrecordsupdated and not self.live_first_time_run:  # Only update if not already done
            print(f"GA Line {inspect.currentframe().f_lineno} self.ip_name_flag: {self.ip_name_flag}")
            for ip, (driver_name, in_race) in self.ip_name_flag.items():
                if in_race == 1 and ip in self.multi_data:
                    lap_time = self.multi_data[ip]['timings']['mWorldFastestLapTime']

                    #if lap_time > 0:  # Skip invalid lap times (e.g., -1)
                    car_name = self.multi_data[ip]['vehicleInformation']['mCarName']
                    self.driverworldrecord[car_name] = {
                        'worldrecord': float(lap_time),
                        'recorddriver': 'internet'
                }
            print(f"RA Line {inspect.currentframe().f_lineno} Def handle_multi_data: Driver World Records updated: {self.driverworldrecord}")
            self.worldrecordsupdated = True  # Set the flag to indicate that world records have been updated
    
    def session_finished(self, notinuse, notinuse2):
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Def session_finished entered")
        print(f"RA Line {inspect.currentframe().f_lineno} Def session_finished entered")
        self.live_first_time_run = True  # Reset the flag to ensure the live view is updated with the new session data
        self.live_first_time_run_done = False  # Reset the flag to indicate that the first live view run is done
        self.on_first_live_run_started = False

    def update_ip_address(self, ip_address):
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Def update_ip_address entered with IP: {ip_address}")
        print(f"RA Line {inspect.currentframe().f_lineno} Def update_ip_address entered with IP: {ip_address}")
        # delayed to ensure the data is coming from the right sim before updating variables.
        QTimer.singleShot(500, lambda: setattr(self, 'driver_view_first_update', True))  # Reset the flag to ensure the driver view is updated with the new IP address  
    
    def handle_sessionid_data(self, sessionids):
        logging.info(f"RA Line {inspect.currentframe().f_lineno} RaceApp Def handle sessionid data entered")
        self.sessionids = sessionids

    def update_driver_names(self, ip_name_flag):
        self.ip_name_flag = ip_name_flag
        print(f"RA Line {inspect.currentframe().f_lineno} Def update_driver_names entered with ip_name_flag: {ip_name_flag}")
        """
        Converts ip_name_flag into driver_names_dict used for button labeling.
        Only includes entries where in_race == 1.
        Format: {'192.168.3.201': ['S-1', 1], '192.168.3.202': ['S-2', 0]}
        """
        driver_names_dict = {}
        for sim_index, (ip, (name, in_race)) in enumerate(ip_name_flag.items(), start=1):
            if in_race == 1:
                driver_names_dict[name] = str(sim_index)
        self.driver_sims =  driver_names_dict
   
    def tab_changed(self, tab_index):
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Def tab_changed entered. Tab index: {tab_index}")
        print(f"RA Line {inspect.currentframe().f_lineno} tab_changed entered. Tab index: {tab_index}")
        self.active_tab = tab_index

    def on_record_laps_loaded(self, record_laps):
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Def RaceApp on_record_laps_loaded entered")
        print(f"RA Line {inspect.currentframe().f_lineno} Def RaceAPP on_record_laps_loaded entered")
        #print(f"RA Line {inspect.currentframe().f_lineno} Best Scores: {record_laps}")
        self.localrecordlaps = record_laps  # Store the best laps for each driver
        if  self.localrecordlaps != None:
            if self.classrace:
                self.localtrackrecord = 0
                self.recorddriver = "Multi"  # Get the driver with the best lap time
            else:
                if self.selected_car in self.localrecordlaps:
                    self.recorddriver =  self.localrecordlaps[self.selected_car]['recorddriver']  # Get the driver with the best lap time
                    self.localtrackrecord =  self.localrecordlaps[self.selected_car]['worldrecord']
                else:
                    self.recorddriver = ""
                    self.localtrackrecord = 0
            print(f"RA Line {inspect.currentframe().f_lineno} Track Record: {self.localtrackrecord} by {self.recorddriver}")
        else:
            print(f"RA Line {inspect.currentframe().f_lineno} No High Scores found in DB")            
            self.localtrackrecord = 0
            self.recorddriver = ""
            self.localrecordlaps = {}

        self.update_heading("skip", self.trackworldrecord, self.localtrackrecord)
        self.waiting_for_highscores = False  # Reset the waiting flag
        
    def update_session_id(self, session_id):
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Def Raceapp latest_session_id entered")
        print(f"RA Line {inspect.currentframe().f_lineno} Def Raceapp latest_session_id entered with session_id: {session_id}")
        if session_id is not None:
            self.session_id = session_id
        else:
            self.session_id = 1
        print(f"RA Line {inspect.currentframe().f_lineno} Latest Session ID: {self.session_id}")
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Latest Session ID: {self.session_id}")

    def handle_session_type(self,session_type):
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Def handle session_type detected entered with parameter: {session_type}")
        print(f"RA Line {inspect.currentframe().f_lineno} Def handle session_type detected entered with parameter: {session_type}")
        self.session_type = session_type  # Store the session type for later use

    def on_first_live_view_run(self, data):
        # Tab changed via signal from monitor thread, so no need to call it here.
        # self.gui.on_tab_changed(0)  # Ensure the live view tab is active when the live view is updated
        logging.info(f"RA Line {inspect.currentframe().f_lineno} Def on_first_live_view_run entered")
        self.event_info = data['eventInformation'] # Extract event information and participant details from the data
        participants = data['participants']['mParticipantInfo']
        sessionstate = data['gameStates']['mSessionState']
        self.selected_track = f"{self.event_info['mTranslatedTrackVariation']} - {self.event_info['mTranslatedTrackLocation']}"
        self.total_laps = self.event_info['mLapsInEvent']  # Get the total laps from event information
        self.classrace = self.identical_cars(data)
        print (f"{'RA Line '} {inspect.currentframe().f_lineno} {'classrace starting' if self.classrace else 'Single Race Starting'}")
        #if len(self.sessionids) < 1: self.final_heading.setText("Score - Waiting for a new race to finish...")
        if len(self.sessionids) < 1:
            updates = [(self.gui.final_heading.setText, ("Score - Waiting for a new race to finish...",))]
            self.gui_update.emit(updates)
        self.migration = 1 # Migration flag to indicate if the new class system is being used
        self.driver_view_first_update = True
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
        #self.driver_sims = {}
        self.leader_participant = {}
        #self.localrecordlaps = {}  # Reset track record tracking for each update
        self.driverworldrecord = {}  # Reset driver track record tracking for each update
        self.trackworldrecord = data['timings']['mWorldFastestLapTime']  # Get the world record time for the track
        self.deltaworldrecord = 0
        self.deltalocalrecord = 0

        self.selected_track = f"{self.event_info['mTranslatedTrackVariation']} - {self.event_info['mTranslatedTrackLocation']}"
        self.selected_car = data['vehicleInformation']['mCarName'] # Get the viewed participant's car name
        
        # Bestem status-tekst basert på sessionstate
        if sessionstate == 3:
            status_text = "Qualifying in progress ..."
        elif sessionstate == 1:
            status_text = "Practice in progress ..."
        else:
            status_text = "Waiting for Green Light..."

        # Pakk oppdateringer i liste
        updates = [
            (self.gui.live_status_label.setText, (status_text,)),
            (self.gui.live_best_label.setText, ("Top Speed and Time",)),
            #(self.gui.world_record_label.setText, ("",)),
            (self.gui.new_session_button.hide, ()),
            (self.gui.previous_session_button.hide, ())
        ]

        # Send til GUI
        print(f"RA Line {inspect.currentframe().f_lineno} New Session button visible?", self.gui.new_session_button.isVisible())
        print(f"RA Line {inspect.currentframe().f_lineno} UpdateLiveView button ID:", id(self.gui.new_session_button))
        self.gui_update.emit(updates)
        self.hide_buttons.emit()
        #self.hidebuttons = True
        self.pit_stop = {}
        self.pit_stops = ""
        self.background_color = "#333333"  # Default background color
        self.top_background_color = "#a80baa"  # Default top background color
        self.race_started = False
        #print(f"RA Line {inspect.currentframe().f_lineno} on first live view run. Emitting self.session ID {self.session_id}")
        #self.session_id_updated.emit(self.session_id)
        self.task_queue.put(('get_record_laps', (self.selected_track,)))
        self.task_queue.put(('load_highscores', (self.selected_car,self.selected_track)))  # Load Highs scores for current car and track into High Score Tab.
        self.waiting_for_highscores = True  # Set the flag to indicate we are waiting for high scores
        updates = [
            (self.gui.participant_labels[i].hide, ())
            for i in range(20)
        ]
        if self.migration == 1: #Disable for now, until migration to new class system is done
            self.gui_update.emit(updates)

        #for i in range(20): self.participant_labels[i].hide()  # Hide labels initially  # Assuming 20 participants max
        # Find out which sim the particpant is using and write the it after the name
        # Check participants in file drivers.txt, and match participant['mName'] with the name in the file.
        # This will help to identify which sim the participant is using.
        # Sim is the names position in the file.
        #if self.config_manager.read_cp_status():
        #    self.get_request_for_sim_signal.emit()  # Emit the signal to get the driver sim data
        self.sector_times = {}
        self.last_sector = {}
        self.driver_finished = {}
        self.leader_name = None
        self.leader_total_time = 0.0
        self.leader_current_lap = 0
        self.leader_progress = 0.0
        #heading_text = f"{self.session_type} - {self.event_info['mTranslatedTrackLocation']} - {self.event_info['mTranslatedTrackVariation']} ({'Qualify' if sessionstate == 3 else 'Practice' if sessionstate == 1 else self.event_info['mLapsInEvent']}) - {participants[0]['mCarNames']} - {len(participants)} Drivers - Session ID: {self.session_id} - World rec:{trackworldrecord} " # Create the heading text
        if self.classrace:
            car = "class or multi class race"
        else:
            car = self.selected_car  # Use the selected car name for the heading

        # --- bygg heading-teksten ---------------------------------
        session_map   = {3: "Qualify", 1: "Practice"}
        session_label = session_map.get(sessionstate,
        f"{self.event_info['mLapsInEvent']} Laps")

        self.heading_session = (f"Session Type: {self.session_type} - ")
        self.heading_track = (
            f"Track: {self.selected_track} - "
            f"({session_label})<br>"
        )
        self.heading_car = ( f"Car: {car} ")
        self.heading_drivers = (
            f"- {len(participants)} Drivers<br>")
        self.heading_sessionid = (
            f"Session ID: {self.session_id} - ")
        self.heading_wrecord = (
            f"World record: {(self.format_lap_time(self.trackworldrecord) if self.trackworldrecord != -1 else 'MOD Car/Track')} - ")
        self.heading_lrecord =("")
        heading_text = (f"{self.heading_session} {self.heading_track}{self.heading_car} {self.heading_drivers} {self.heading_sessionid} {self.heading_wrecord} {self.heading_lrecord}")


        # --- pakk i updates og emit én gang -----------------------
        updates = [
            (self.gui.live_heading.setText, (heading_text,))
        ]
        print(f"RA Line {inspect.currentframe().f_lineno} Updates for live view: {heading_text}")
        self.gui_update.emit(updates)
        #self.gui.scan_active_computers()
        #asyncio.create_task(self.get_participants_ips()) # Get the participants IPs and update the driver view 
        print("New Session button visible?", self.gui.new_session_button.isVisible())
        print(f"Current tab: {self.tab_widget.tabText(self.tab_widget.currentIndex())}")
        print(f"RA Line {inspect.currentframe().f_lineno} Self.active_tab: {self.active_tab}")
        self.live_first_time_run_done = True  # Set the flag to indicate the first live view run is done

    def update_live_view(self, data):
        
        if not self.live_first_time_run_done and not self.on_first_live_run_started:
            print(f"RA Line {inspect.currentframe().f_lineno} On first live view run not done, calling on_first_live_view_run.")
            print(f"RA Line {inspect.currentframe().f_lineno} Def update_live_view entered with Session_ID: {self.session_id}")
            self.on_first_live_view_run(data)
            self.on_first_live_run_started = True  # Set the flag to indicate the first live run has started
            return
        if self.waiting_for_highscores:
            print(f"RA Line {inspect.currentframe().f_lineno} Waiting for high scores to be loaded, skipping live view update.")
            return
        if not self.live_first_time_run_done:
            print(f"RA Line {inspect.currentframe().f_lineno} Waiting for on first live view run to complete.")
            return
        
        if not getattr(self, 'multi_data', None):

            if (getattr(self, 'multi_data_message', False) == False ):
                print(f"RA Line {inspect.currentframe().f_lineno} No multi_data available, setting it to Data.")
                self.multi_data_message = True

        # Reset the message flag if multi_data is now available
        participants = data['participants'].get('mParticipantInfo', None)
        if not participants:
            return
        sorted_participants = sorted(
            participants[:data['participants']['mNumParticipants']],
            key=lambda p: (float('inf') if self.driver_flags.get(p['mName']) == 'Falsestart' else p['mRacePosition'])
        )
        #print(f"RA Line {inspect.currentframe().f_lineno} Def update_live_view entered with {sorted_participants} participants")
        sessionstate = data['gameStates']['mSessionState']
        leader = sorted_participants[0]
        self.leader_name = leader['mName']
        self.leader_current_lap = leader['mCurrentLap']
        self.leader_progress = leader.get('mCurrentLapDistance', 0.0)

        if not hasattr(self, 'previous_best_lap_time') or self.live_first_time_run:
            self.previous_best_lap_time = self.best_lap_time - 1
        for i, participant in enumerate(sorted_participants):
            name = participant['mName']
            carname = participant['mCarNames']
            self.current_lap[name] = participant['mCurrentLap']
            if participant['mLastLapTimes'] != -123 and name in self.previous_current_lap and not self.driver_finished.get(name, False):
                if self.current_lap[name] != self.previous_current_lap.get(name):
                    self.gui_update.emit([(self.gui.live_status_label.setText, (f"{name} is now on lap {self.current_lap[name]}",))])
                    self.lap_time[name] = participant['mLastLapTimes']
                    self.lap_list.setdefault(name, []).append(self.format_lap_time(self.lap_time[name]))
                    self.previous_current_lap[name] = self.current_lap[name]
                    
                    # -------------- Check for new record laps ----------------
                    if carname in self.localrecordlaps:
                        print(f"RA Line {inspect.currentframe().f_lineno} Driver laptime: {self.lap_time[name]} , WorldTrack Record: {self.trackworldrecord}, Local Record: {self.localrecordlaps[carname]['worldrecord']}")
                        if self.lap_time[name] < self.localrecordlaps[carname]['worldrecord']:
                            new_laptime = self.format_lap_time(self.lap_time[name])
                            self.gui_update.emit([(self.gui.world_record_label.setText, (f"New Local Record: {name} - {new_laptime}",))])
                            self.localrecordlaps[carname] = {'worldrecord': self.lap_time[name], 'recorddriver': name}
                            self.new_local_record = True                          
                            self.update_heading(carname, self.trackworldrecord, self.lap_time[name])
                            self.gui_update.emit([(self.gui.flash_timer.start, (500,))])
                    else:
                        print(f"RA Line {inspect.currentframe().f_lineno} Driver track record not found for car: {carname}, First entry!")
                        new_laptime = self.format_lap_time(self.lap_time[name])
                        self.gui_update.emit([(self.gui.world_record_label.setText,(f"Brand New Local Record: {name} - {new_laptime}",))])
                        self.localrecordlaps[carname] = {'worldrecord': self.lap_time[name], 'recorddriver': name}
                        self.new_local_record = True
                        self.update_heading(carname, self.trackworldrecord, self.lap_time[name])
                        self.gui_update.emit([(self.gui.flash_timer.start, (500,))])
                    if carname in self.driverworldrecord:
                        # print(f"RA Line {inspect.currentframe().f_lineno} Driver track record: {self.driverworldrecord}")
                        if self.lap_time[name] < self.driverworldrecord[carname]['worldrecord']:
                            new_laptime = self.format_lap_time(self.lap_time[name])
                            self.gui_update.emit([(self.gui.world_record_label.setText, (f"New World Record: {name} - {new_laptime}",))])
                            print(f"RA Line {inspect.currentframe().f_lineno} Driver laptime: {self.lap_time[name]} , World Track Record: {self.driverworldrecord[carname]['worldrecord']}")
                            self.driverworldrecord[carname] = {'worldrecord': self.lap_time[name]}
                            self.trackworldrecord = self.lap_time[name]
                            self.update_heading(carname, self.trackworldrecord, self.lap_time[name])
                            self.gui_update.emit([(self.gui.flash_timer.start, (500,))])
 
                    if self.current_lap[name] > self.total_laps:
                        self.driver_finished[name] = True

            else:
                self.previous_current_lap[name] = 1        

            if self.driver_finished.get(name, False):
                self.total_time_seconds[name] = sum(float(t.split(':')[0]) * 60 + float(t.split(':')[1]) for t in self.lap_list.get(name, []))
                continue  # Skip further processing for this driver
            else:
                datadriver = self.get_full_api_data_by_driver_name(name)
                current_lap_time = datadriver.get('timings', {}).get('mCurrentTime') if datadriver else 0
                self.total_time_seconds[name] = current_lap_time + sum(float(t.split(':')[0]) * 60 + float(t.split(':')[1]) for t in self.lap_list.get(name, []))
                if participant['mRacePosition'] == 1:
                    self.leader_name = name
                    self.leader_current_lap = self.current_lap[name]
                    self.leader_total_time = self.total_time_seconds[name]
                    self.leader_participant = participant
                    self.leader_progress = participant.get('mCurrentLapDistance', 0.0)
        updates = [] 
        if self.best_lap_time < self.previous_best_lap_time or self.live_first_time_run:
            for j in range(min(20, len(sorted_participants))):
                p = sorted_participants[j]
                bg_color = (self.top_background_color
                            if p['mFastestLapTimes'] <= self.best_lap_time and p['mCurrentLap'] > 1
                            else self.background_color)
                updates.append((self.gui.participant_labels[j].setStyleSheet,
                                (f"font-size:14px; background-color:{bg_color}; "
                                f"padding:5px; margin-bottom:2px; border-radius:5px;",)))
            self.previous_best_lap_time = self.best_lap_time

        # --------------- Skip if Live Tab is Hidden ----------
        if self.active_tab != 0 and not self.live_first_time_run:
            self.gui_update.emit(updates)          # Send updates to GUI
            return                                 # Skip further GUI-data in this round

        # ---------------- participants -------------------------
        for i, participant in enumerate(sorted_participants):
            name = participant['mName']
            total_time_str = self.format_lap_time(self.total_time_seconds.get(name, 0) if self.total_time_seconds.get(name, 0) != -1 else 0)
            last_lap_str   = self.format_lap_time(participant['mLastLapTimes'])
            lap_times_str  = ", ".join(self.lap_list.get(name, ["No Valid Lap!"]))
            gap_str, gap_distance_str = self.get_gap_to_leader(participant)
            gap_to_ahead_str, gap_to_ahead_distance_str = self.get_gap_to_ahead(
                participant, sorted_participants
            )

            html = self.create_participant_text(
                participant,
                self.driver_flags.get(name, ""),
                last_lap_str,
                lap_times_str,
                sessionstate,
                total_time_str,
                gap_str,
                gap_distance_str,
                gap_to_ahead_str,
                gap_to_ahead_distance_str
            )

            self.participant_update.emit(i, html)

        # ---------------- status-text ----------------------
        race_state = data['gameStates']['mRaceState']
        if race_state == 2 and not self.race_started:
            updates.append((self.gui.live_status_label.setText, ("Green Light! GO GO GO",)))
            self.race_started = True
        elif race_state in (3, 6):
            updates.append((self.gui.live_status_label.setText, ("Race Ending....",)))

        # --------------- First Time Run -------------
        if self.live_first_time_run:
            for i in range(len(sorted_participants)):
                lbl = self.gui.participant_labels.get(i)
                if lbl:
                    updates.append((lbl.show, ()))

        # --------------- Send batch updates ------------
        if updates:
            self.gui_update.emit(updates)

        self.live_first_time_run = False
    
    def get_full_api_data_by_driver_name(self, name):
        """
        Return the enriched API dataset for the given driver's name.
        """
        #print(f"RA Line {inspect.currentframe().f_lineno} Def get_full_api_data_by_driver_name entered with name: {name}")
        #print (f"RA Line {inspect.currentframe().f_lineno} Self.ip_name_flag: {self.ip_name_flag}")
        #print (f"RA Line {inspect.currentframe().f_lineno} Self.multi_data: {self.multi_data}")
        if not hasattr(self, "multi_data") or not hasattr(self, "ip_name_flag"):
            return None
        for ip, (driver_name, in_race) in self.ip_name_flag.items():
            if driver_name == name:
                return self.multi_data.get(ip)
        return None   
    
    def update_driver_view(self, data):
        if (self.active_tab != 5 and self.driver_view_first_update == False) or not data or 'participants' not in data or 'mParticipantInfo' not in data['participants']:
            return

        if self.driver_view_first_update:
            updates = [(self.gui.track_txt.setText, (self.selected_track,))]
            carname = data['vehicleInformation']['mCarName']
            self.previous_carname = carname
            if not self.waiting_for_highscores:
                #self.update_heading(carname, self.trackworldrecord, self.localtrackrecord)
                self.driver_view_first_update = False
                return
            else:
                return  # Skip the rest of the update if this is the first run
            
      
        # Precompute values
        participants = data['participants']
        carnode = data['carState']
        timingsnode = data['timings']
        index = min(participants.get('mViewedParticipantIndex', 0), participants.get('mNumParticipants', 0) - 1)
        drvnode = participants['mParticipantInfo'][index]
        inputnode = data['unfilteredInput']
        speed = int(carnode['mSpeed'] * 3.6)
        crashindex = carnode['mLastOpponentCollisionIndex']
        if crashindex > participants['mNumParticipants'] - 1:
            crashindex = -1
        crashname = participants['mParticipantInfo'][crashindex]['mName'] if crashindex != -1 else "None"
        rpm = carnode['mRpm']
        #mMaxRPM = carnode['mMaxRPM']
        bestlap = timingsnode['mBestLapTime']
        current_lap = drvnode['mCurrentLap']
        race_pos = drvnode['mRacePosition']
        drivername = drvnode['mName']
        carname = data['vehicleInformation']['mCarName']
        
        # ---------------- Check for car change ----------------
        if carname != self.previous_carname or self.new_local_record:  # Must be a classrace.
            self.trackworldrecord = data['timings']['mWorldFastestLapTime']
            self.task_queue.put(('load_highscores', (carname,self.selected_track)))  # Load Highs scores for current car and track into High Score Tab.
            if carname not in self.localrecordlaps:
                self.previous_carname = carname
                return  # Skip if the car is not in the local record laps
            else:
                self.localtrackrecord = self.localrecordlaps[carname]['worldrecord']
                self.recorddriver = self.localrecordlaps[carname]['recorddriver']
                self.update_heading(carname, self.trackworldrecord, self.localtrackrecord)
            self.new_local_record = False 

        self.deltalocalrecord = bestlap - self.localtrackrecord if bestlap != -1 and self.localtrackrecord != 0 else 0
        self.deltaworldrecord = bestlap - self.trackworldrecord if bestlap != -1 and self.trackworldrecord != -1 else 0
                
        self.previous_carname = carname
        laptime = self.format_lap_time(timingsnode['mCurrentTime'] if timingsnode['mCurrentTime'] != -1 else 0)
        remaining = timingsnode['mEventTimeRemaining']
        gear = carnode['mGear']
        throttle = int(carnode.get('mThrottle', 0) * 100)
        brake = int(carnode.get('mBrake', 0) * 100)
        clutch = int(carnode.get('mClutch', 0) * 100)

        throttle_raw = int(inputnode.get('mUnfilteredThrottle', 0) * 100)
        brake_raw = int(inputnode.get('mUnfilteredBrake', 0) * 100)
        clutch_raw = int(inputnode.get('mUnfilteredClutch', 0) * 100)
        
        # Extract tire temperature data and update the display
        tire_temps = [0.0, 0.0, 0.0, 0.0]  # Default values
        if 'wheelsAndTyres' in data and 'mTyreTemp' in data['wheelsAndTyres']:
            tire_temps = data['wheelsAndTyres']['mTyreTemp']

        # self.gui.update_tire_temperatures(tire_temps)
        
        #print("Sending to GUI – speed:", data.get("speed"), "rpm:", data.get("rpm"))
        self.gui_realtime_update.emit({
            "steering": data['unfilteredInput']['mUnfilteredSteering'],
            "speed": speed,
            "rpm": rpm,
            "throttle": throttle,
            "brake": brake,
            "clutch": clutch,
            "throttle_raw": throttle_raw,
            "brake_raw": brake_raw,
            "clutch_raw": clutch_raw
            })  # Emit the data to the GUI for live updates

        # Batch UI updates
        formatted_trackworldrecord = self.format_lap_time(self.trackworldrecord) if self.trackworldrecord != -1 else "Mod Car/Track"
        formatted_worldrecorddb = f"{self.format_lap_time(self.localtrackrecord)} - {self.recorddriver}" if self.localtrackrecord != 0 else "No Record"
        formatted_deltaworldrecord = self.format_lap_time(self.deltaworldrecord)
        formatted_deltalocalrecord = self.format_lap_time(self.deltalocalrecord)
        formatted_remaining = self.format_lap_time(remaining) if remaining != -1 else "No Time"
        formatted_bestlap = self.format_lap_time(bestlap if bestlap != -1 else 0)

        flag_value = self.driver_flags.get(drivername, None)
        #print(f"RA Line {inspect.currentframe().f_lineno} flag: {flag_value}")
        
        if  not self.waiting_for_highscores:
            #print (f"RA Line {inspect.currentframe().f_lineno} self.local_record_updated: {self.local_record_updated}, self.waiting_for_highscoresr: {self.waiting_for_highscores}, worldrecord: {self.worldrecord}, worldrecorddb: {self.worldrecorddb}, deltaworldrecord: {deltaworldrecord}, deltalocalrecord: {deltalocalrecord}")
            #gui = RaceMonitorApp.get_instance()
            updates = [
                (self.gui.update_tire_temperatures, (tire_temps,)),  # Update tire temperatures
                (self.gui.flags_txt.setText, (flag_value if flag_value else "No Flag",)),  # Update driver flags
                (self.gui.driver_txt.setText, (drivername,)),
                (self.gui.worldrecord_txt.setText, (formatted_trackworldrecord,)),
                (self.gui.localrecord_txt.setText, (formatted_worldrecorddb,)),
                (self.gui.deltaworldrecord_text.setText, (formatted_deltaworldrecord,)),
                (self.gui.deltalocalrecord_text.setText, (formatted_deltalocalrecord,)),
                (self.gui.remaining_text.setText, (formatted_remaining,)),
                (self.gui.laptime_text.setText, (laptime,)),
                (self.gui.car_txt.setText, (carname,)),
                (self.gui.collison_txt.setText, (str(crashname),)),
                (self.gui.speed_display.setText, (str(speed),)),
                (self.gui.gear_display.setText, ('N' if gear == 0 else str(gear),)),
                (self.gui.pos_text.setText, (str(race_pos),)),
                (self.gui.lap_text.setText, (f"{current_lap}/{self.total_laps}" if self.total_laps > 0 else f"{current_lap}",)),
                (self.gui.bestlaptime_text.setText, (formatted_bestlap,))
            ]
            self.gui_update.emit(updates)

            #for setter, args in updates:
            #    setter(*args)

    def identical_cars(self, data):
        if not data or 'participants' not in data or 'mParticipantInfo' not in data['participants']:
            return False

        participants = data['participants']['mParticipantInfo']
        if not participants:
            return False

        # Filter out SafetyCars and PaceCars
        car_names = [p['mCarNames'] for p in participants if 'Safety' not in p['mCarNames'] and 'PaceCar' not in p['mCarNames']]


        # If there are no non-SafetyCar entries, we can't compare — return False

        if not car_names:
            return False

        # If all non-SafetyCar cars are the same, return False
        first_car = car_names[0]
        if all(car == first_car for car in car_names):
            return False

        # Otherwise, cars are not identical => return True
        return True

    def update_flags(self, flags):
        logging.info(f"RA Line Flags updated def entered")
        #print(f"RA Line {inspect.currentframe().f_lineno} Flags updated def entered")
        self.driver_flags=flags # Update the flags label with the message    
    
    def update_heading(self, new_car: str,
                    worldrecord: float | int,
                    localrecord: float | int) -> None:
        """
        Oppdater «live heading»-teksten.

        new_car      - bilnavn eller "skip"
        worldrecord  - world-rekordtid i sekunder, eller 0  ->  «Mod Car/Track»
        localrecord  - lokal rekordtid  i sekunder, eller 0 ->  «First Race»
        """

        # --- formater tallverdier ---------------------------------------------------
        local_str  = "First Race"        if localrecord  == 0 else self.format_lap_time(localrecord)
        world_str  = "Mod Car/Track"     if worldrecord == -1 else self.format_lap_time(worldrecord)

        # hent eksisterende bil hvis vi skal «skippe» oppdatering av bilnavn
        if new_car != "skip" and not self.classrace:
            new_car = new_car.strip()
            self.heading_car = f"Car: {new_car} "
        # --- bygg ny heading --------------------------------------------------------
        self.heading_lrecord = (
                f" - Local Record: {local_str} " )
        self.heading_wrecord = (
                f"World Record: {world_str} " )
        if self.classrace:
            self.current_car = ' - ' + new_car
        else:
            self.current_car = ''    
        heading_text = (f"{self.heading_session} {self.heading_track}{self.heading_car} {self.heading_drivers} {self.heading_sessionid} {self.heading_wrecord} {self.heading_lrecord}{self.current_car}")

        # --- send til GUI i ett, trådsikkert kall -----------------------------------
        self.gui_update.emit([(self.gui.live_heading.setText, (heading_text,))])

    def get_gap_to_leader(self, participant):
        if hasattr(self, 'leader_name') and participant['mName'] == self.leader_name:
            return "Leader", "0.0m"

        gap_sec, gap_dist = self._gap_details(participant)
        gap_str = f"+{gap_sec:.0f}"
        gap_distance_str = f"{gap_dist/1000:.1f} km" if gap_dist >= 1000 else f"{gap_dist:.0f}m"
        return gap_str, gap_distance_str

    def _gap_details(self, participant):
        if not hasattr(self, 'leader_name') or not hasattr(self, 'leader_current_lap') or not hasattr(self, 'leader_progress'):
            return 0,0
        lap = participant['mCurrentLap']
        progress = participant.get('mCurrentLapDistance', 0.0)
        track_length = self.event_info.get('mTrackLength', 0)

        abs_progress = lap * track_length + progress
        leader_progress = self.leader_current_lap * track_length + self.leader_progress
        gap_dist = leader_progress - abs_progress

        # If leader hasn't completed a full lap, fallback to real-time estimation
        #print(f"Debug: self.leader_current_lap={self.leader_current_lap}, progress={progress}, gap_dist={gap_dist}")
        if self.leader_current_lap < 2:
            # Use leader's current speed instead of participant's
            speed = self.leader_participant.get('mSpeeds', 0.0)
            speed = max(speed, 1e-3)  # Prevent divide-by-zero
            gap_time = gap_dist / speed
            #leader_speed = speed
        else:
            # After lap 1, use average leader speed
            leader_speed = self.get_average_speed(self.leader_name)
            leader_speed = max(leader_speed, 1e-3)
            gap_time = gap_dist / leader_speed


        return gap_time, gap_dist

    def get_gap_to_ahead(self, participant, sorted_participants):
        if not sorted_participants or participant['mRacePosition'] <= 1:
            return "N/A", "0.0m"

        for other in sorted_participants:
            if other['mRacePosition'] == participant['mRacePosition'] - 1:
                gap_self_sec, dist_self_m = self._gap_details(participant)
                gap_ahead_sec, dist_ahead_m = self._gap_details(other)

                gap_sec = max(0.0, gap_self_sec - gap_ahead_sec)
                gap_dist = max(0.0, dist_self_m - dist_ahead_m)

                gap_str = f"+{gap_sec:.0f}"
                dist_to_ahead_str = f"{gap_dist/1000:.1f} km" if gap_dist >= 1000 else f"{gap_dist:.0f}m"

                return gap_str, dist_to_ahead_str

        return "N/A", "0.0m"
                
    def get_average_speed(self, name):
        track_length = self.event_info.get('mTrackLength', 0)
        lap_times = self.lap_list.get(name, [])
        if not lap_times or track_length <= 0:
            return 0.0

        total_distance = track_length * len(lap_times)
        total_time = 0.0

        for lap_str in lap_times:
            try:
                minutes, seconds = map(float, lap_str.split(":"))
                total_time += minutes * 60 + seconds
            except Exception:
                continue

        if total_time <= 0:
            return 0.0

        return total_distance / total_time  # m/s
    
    def format_lap_time(self, lap_time): # Helper function to format lap time from seconds to 'MM:SS.ss' format.
        if lap_time is None or lap_time == -123.0: return "N/A"
        minutes = int(lap_time // 60)
        seconds = lap_time % 60
        return f"{minutes}:{seconds:05.2f}"
    
    def create_participant_text(self, participant, flag, last_lap_str, lap_times_str, sessionstate,
                            total_time_str="", gap_str="", gap_distance_str="", gap_to_ahead_str="", gap_to_ahead_distance_str="" ):
                            
        #print(f"RA Line {inspect.currentframe().f_lineno} Def create_participant_text entered with participant: {participant['mName']}")
        name = participant['mName']
        car = participant['mCarNames']
        if self.top_speed.get(name, -1000) < math.floor(participant['mSpeeds']):
            self.top_speed[name] = math.floor(participant['mSpeeds'])
        sim = self.driver_sims.get(name, "")
        #print(f"RA Line {inspect.currentframe().f_lineno} Def create_participant_text entered with name: {name}, sim: {sim}")
        fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])

        # Update top speed and best lap data if relevant
        self.update_best_lap_and_speed(participant, sessionstate)

        # Handle pit stop and get count
        pit_count = self.handle_pit_stop(participant)
        pit_stop_str = (
            f"<span style='color:#00fff0'>Pits: </span><span style='color:#FFD700'>{pit_count}</span>"
            if pit_count > 0 else ""
        )
        pit_status = f"<span style='color:#00FF00;font-weight:bold'>(PIT)</span>" if participant['mPitModes'] != 0 else ""

        # Get race status, flag, lap history formatting
        race_status = self.get_race_status(participant, sessionstate)
        flag_text = self.get_flag_text(flag)
        lap_times_str = self.format_lap_times_list(lap_times_str)

        # Leading spacing adjustment
        spaces = (f"<br>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;{'&nbsp;&nbsp;' if participant['mRacePosition'] > 9 else ''}"
                f"<span style='color:#00FF00;'>")

        # Construct output
        output = (
            f"<span style='font-weight:bold; color:#FFFFFF;'>{participant['mRacePosition']}</span>: "
            f"<span style='color:#FFFFFF;font-weight:bold'>{name} {race_status} {flag_text} {pit_status} {pit_stop_str}</span> "
        )

        if sim:
            output += f"<span style='color:#00fff0;'>Sim: <span style='color:#FFD700;'>{sim}</span> - "

        output += (
            f"<span style='color:#00fff0;'>Speed: <span style='color:#FFD700;'>{participant['mSpeeds'] * 3.6:.0f} Km/t</span> "
            f"Top Speed: <span style='color:#FFD700;'>{self.top_speed[name] * 3.6:.0f}</span> "
            f"Lap: <span style='color:#FFD700;'>{participant['mCurrentLap']}</span> "
            f"Last Lap: <span style='color:#FFD700;'>{last_lap_str}</span> "
            f"Best: <span style='color:#FFD700;'>{fastest_lap_str}</span> "
            f"Total: <span style='color:#FFD700;'>[{total_time_str}]</span> "
            f"Gap: <span style='color:#FFD700;'>{gap_str}</span>"
        )

        if name != self.leader_name:
            output += (
                f" Dist: <span style='color:#FFD700;'>{gap_distance_str}</span> "
                f"Ahead: <span style='color:#FFD700;'>{gap_to_ahead_str}</span> "
                f"Dist: <span style='color:#FFD700;'>{gap_to_ahead_distance_str}</span>"
            )

        output += (
            f"{spaces}<span style='color:#00fff0;'>Laptimes: <span style='color:#00FF00;'>[{lap_times_str}]</span>"
        )
        if self.classrace:
            output += (
                f"{spaces}<span style='color:#00fff0;'>Car: <span style='color:#e73c3c;font-weight:bold'>{car}</span></span>"
            )
        return output

    def get_flag_text(self, flag):
        return f"<span style='color:#e73c3c;font-weight:bold'>({flag})</span>" if flag else ''

    def get_race_status(self, participant, sessionstate):
        if participant['mCurrentLap'] - 1 == self.event_info['mLapsInEvent'] and sessionstate not in (1, 3) and self.session_type == "Race":
            return "<span style='color:#FF0000;font-weight:bold'>(Finished!)</span>"
        return ""

    def update_best_lap_and_speed(self, participant, sessionstate):
        name = participant['mName']
        updated = False
        updates = []

        if math.floor(participant['mSpeeds']) > self.best_top_speed:
            self.best_top_speed = math.floor(participant['mSpeeds'])
            self.top_speed_driver = name
            updated = True

        if (
            participant['mFastestLapTimes'] < self.best_lap_time
            and participant['mCurrentLap'] > 1
            and participant['mFastestLapTimes'] != -123
        ):
            self.best_lap_time = participant['mFastestLapTimes']
            self.best_lap_driver = name
            status_text = (
                f"{name} just got a new best lap time"
                + (
                    " (Qualify)" if sessionstate == 3
                    else " (Practice)" if sessionstate == 1
                    else ""
                )
                + f": {self.format_lap_time(self.best_lap_time)}"
            )
            updates.append((self.gui.live_status_label.setText, (status_text,)))
            updated = True

        if updated:
            best_label_text = (
                f"Top Speed: {self.top_speed_driver} {self.best_top_speed * 3.6:.0f} Km/t "
                + (
                    f"Best Lap: {self.best_lap_driver} {self.format_lap_time(self.best_lap_time)}"
                    if self.best_lap_time != 999
                    else "Best Lap: "
                )
            )
            updates.append((self.gui.live_best_label.setText, (best_label_text,)))

        if updates:
            self.gui_update.emit(updates)

    def handle_pit_stop(self, participant):
        updates = []
        name = participant['mName']
        if name not in self.pit_stop:
            self.pit_stop[name] = {}

        if participant['mPitModes'] == 2 and participant['mCurrentLap'] not in self.pit_stop[name]:
            self.pit_stop[name][participant['mCurrentLap']] = 1
            self.pit_stops_updated.emit(self.pit_stop)
            status_text = (f"{name} entered PIT")
            updates.append((self.gui.live_status_label.setText, (status_text,)))

            logging.info(f"Pit Stop added for {name} at lap {participant['mCurrentLap']}")
        if updates:
            self.gui_update.emit(updates)
        return sum(self.pit_stop[name].values())

    def format_lap_times_list(self, lap_times_str):
        laps = lap_times_str.split(", ")
        return ", ".join(laps[-16:]) if len(laps) > 17 else lap_times_str
 
    def run(self):
        
        while self.running:
            if not self.task_queue.empty():
                task, args = self.task_queue.get()
                if hasattr(self, task):
                    getattr(self, task)(*args)

    def stop(self):
        self.running = False

def main():
    global app
    app = QApplication(sys.argv)
    ex = GuiMainApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address
