from re import L, T; from timeit import Timer; import atexit, sys, re, inspect, requests, sqlite3, queue, json, time, traceback, logging, os, asyncio, aiohttp, math, base64, configparser, tempfile
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QTabWidget, QSpacerItem, QMessageBox, QLineEdit, QCalendarWidget, QProgressBar
from PyQt5.QtGui import QPixmap, QIcon, QFontDatabase, QTransform, QPainter, QFont
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer, QObject, QEvent, QEventLoop, QDate, QPoint, QSize
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis, QBarSet, QBarSeries, QBarCategoryAxis
from datetime import datetime
from file_base64_strings import (bestlap_bg_img_base64, wheel_bg_img_base64, pedal_bg_img_base64, lap_bg_img_base64, pos_bg_img_base64,laptime_bg_img_base64, speedometer_bg_img_base64,tachometer_bg_img_base64,needle_bg_img_base64, Driver_Statistics_Background_img_base64, High_scores_Background_img_base64, Race_results_Background_img_base64, Race_scores_Background_img_base64, liverace_liveview_img_base64, liverace_status_img_base64, icon_base64, sui_generis_rg_font_base64, ds_digib_font_base64)
if os.path.exists('debug.log'): # Set up logging
    os.remove('debug.log')
logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 


class ConfigManager:
    def __init__(self, db_queue):
        self.config_file = 'config.ini'
        self.__version__ = "1.5.9"
        self.__author__ = "RockyTM"
        self.__email__ = "post@drs.no"
        self.__date__ = "2025-03-28"
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
                        if response:self.db_queue.put(('delete_db', ()))  # If OK was clicked, proceed
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
                else: logging.info("All required fields are already present in the config file.")
                    
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
        
    def rad_config_file(self):
        #config = configparser.ConfigParser()
        try:
            self.config.read(self.config_file) #Read the existing config file

            return self.config
        except (configparser.Error, IOError) as e:
            print(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
            logging.info(f"CM Line {inspect.currentframe().f_lineno} An error occurred while accessing the config file: {e}")
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
    write_cp_all_signal = pyqtSignal(object)
    load_sessionid_on_start_signal = pyqtSignal(object)
    write_cp_signal = pyqtSignal(object, object)
    load_highscores_on_start_signal = pyqtSignal(object)
    highscore_data_loaded_signal = pyqtSignal(object)
    drivers_signal = pyqtSignal(object)
    # latest_session_id_signal = pyqtSignal(object)

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
                logging.info(f"DB Line {inspect.currentframe().f_lineno} Operation: {operation} Args: {args}")
                print(f"DB Line {inspect.currentframe().f_lineno}  Queue Called: {operation} ")
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
                logging.error(f"DB Line {inspect.currentframe().f_lineno} Unknown operation: {operation}")
                print(f"DB Line {inspect.currentframe().f_lineno} Unknown operation: {operation}")

        except Exception as e:
            logging.error(f"DB Operation failed: {e}")
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

                read_cp_status = self.config_manager.read_cp_status()
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
                    logging.info("DB Line {inspect.currentframe().f_lineno} Callback None")
                    callback(None)  # No race found
        except Exception as e:
            logging.error(f"Database Line {inspect.currentframe().f_lineno} operation failed: {e}")
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
                self.highscore_data_loaded_signal.emit(None)
        except Exception as e:
            logging.error(f"DB Line {inspect.currentframe().f_lineno} operation failed: {e}")
            self.highscore_data_loaded_signal.emit(None)

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
                        print(f"DB Line {inspect.currentframe().f_lineno} Raceid to delete: {race_id}")
                        logging.info(f"DB Line {inspect.currentframe().f_lineno} No Rows or participants, DB Race id to delete: {race_id}")
                        self.cursor.execute('DELETE FROM Laps WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Participants WHERE RaceID = ?', (race_id,))
                        self.cursor.execute('DELETE FROM Races WHERE RaceID = ?', (race_id,))
                        self.conn.commit() 
                        print(f"DB Line {inspect.currentframe().f_lineno} No laps or participants, race deleted with race_id:{race_id}")
                        logging.info(f"DB Line {inspect.currentframe().f_lineno} No laps or participants, race deleted with race_id:{race_id}")
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
                    logging.info("DB Invoking callback with session_id")
                    callback(session_id, dato)
            else:
                if callback:
                    print(f"DB Line {inspect.currentframe().f_lineno} No Session ID. Invoking callback with session_id None")
                    logging.info("DB No Session ID. Invoking callback with session_id None")
                    callback(None, None)
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
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
                logging.info("DB Result is valid")
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
            print(f"Read CP Status: {read_cp_status}")
            if read_cp_status:
                logging.info("DB Emitted write_cp_signal")
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

    def stop(self):
        self.running = False
        self.db_queue.put(('stop', None))
        if hasattr(self, 'session') and self.session:
            self.session.close()  # Safely close the session
        self.quit()  # Stop the event loop if it's running
        self.wait()  # Wait until the thread has fully exited        
        
class ControlPanel(QObject):
    driver_sims_updated = pyqtSignal(dict)  # Signal to update driver sims
    def __init__(self, db_thread, config_manager, racemonitorapp):
        super().__init__()
        self.running = True
        self.config_manager= config_manager
        self.config = configparser.ConfigParser()
        self.config.read('config.ini')
        self.file_path = self.config['config']['path_to_cp_scores'] + 'score.txt'
        self.best_lap_file_path =  self.config['config']['path_to_cp_scores'] + 'bestlap.txt'
        self.driver_file_path =  self.config['config']['path_to_cp_scores'] + 'drivers.txt'
        self.db_thread = db_thread
        self.racemonitorapp = racemonitorapp
        
        #signalling
        self.db_thread.write_cp_signal.connect(self.process_signal) # Connect the signal to a slot that updates Session ID
        self.db_thread.write_cp_all_signal.connect(self.process_all_signal) # Connect the signal to a slot writes all scores to file
        self.racemonitorapp.get_request_for_sim_signal.connect(self.process_sim_signal) # Connect the signal to a slot that processes the sim data


    def process_sim_signal(self):
        driver_names = self.read_driver_names(self.driver_file_path)
        # Match position of driver name with sim
        driver_names_dict = {}
        for index, driver in enumerate(driver_names, start=1):
            # Create key-value pair: driver name -> Sim-[index]
            driver_names_dict[driver.strip()] = f"{index}"
        self.driver_sims_updated.emit(driver_names_dict)
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
    error_occurred = pyqtSignal(str)   # New signal for errors
    connection_restored = pyqtSignal()  # Signal to clear error message
    ip_address_updated = pyqtSignal(str) # Signal to update IP address
    race_message_updated = pyqtSignal(str) # Signal to update label text
    api_response_time_updated = pyqtSignal(float)  # Signal to update API response time
    session_type_updated = pyqtSignal(str)  # Signal to indicate time trial detection

    
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
        #self.ip_address = self.config_manager.read_ip_address()
        #self.ip_address_updated.emit(self.ip_address)
        asyncio.create_task(self.connection_monitor())
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
                    print(F"Waiting... Loop number {index}")
                # logging.info(f"Line {inspect.currentframe().f_lineno} Waiting... Loop number {index}")
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
                    # check if it is qualify or race or practice
                    if data['gameStates']['mSessionState'] == 3:
                        print(f"MT Line {inspect.currentframe().f_lineno} Qualifying Starting")
                        logging.info("Qualifying")
                        self.qualify = True
                        self.session_type_updated.emit("Qualifying")  # Emit signal to indicate qualifying session
                        await self.qualify_running(data) # Start the qualifying running loop
                        #self.race_message_updated.emit("Qualifying Finished...")
                        
                        self.qualify_finished.emit()
                        qualifying_finished = True
                        print(f"MT Line {inspect.currentframe().f_lineno} Qualifying Finished")
                    elif data['gameStates']['mSessionState'] == 1:
                        print(f"MT  Line {inspect.currentframe().f_lineno} Practice Starting")
                        logging.info("Practice")
                        self.practice = True
                        self.session_type_updated.emit("Practice") 
                        await self.practice_running(data) # Start the practice running loop
                        self.practice_finished.emit()
                        practice_finished = True
                        print(f"MT Line {inspect.currentframe().f_lineno} Practice Finished")
                    else:
                        print(f"MT Line {inspect.currentframe().f_lineno} Starting Race Loop")
                        if data['eventInformation']['mLapsInEvent'] == 0: # If mLapsInEvent is 0, it means its a time trial.
                            print(f"MT Line {inspect.currentframe().f_lineno} Time Trial Detected")
                            logging.info("Time Trial Detected")
                            self.time_trial = True
                            self.session_type_updated.emit("TimeTrail") # Emit signal to indicate time trial detection
                        else:
                            self.time_trial = False
                            self.session_type_updated.emit("Race") # Emit signal to indicate normal Race.
                        await self.race_running(data) # Start the race running loop
                        print(f"MT Line {inspect.currentframe().f_lineno} Race Loop Finished")
                        self.first_time_run = True
                        self.race_not_finished_message_shown = False
                
            except Exception as e:
                logging.error(f"MT Line {inspect.currentframe().f_lineno} An error occurred while monitoring race state: {e}")
                print(f"MT Line {inspect.currentframe().f_lineno} An error occurred while monitoring race state: {e}")
                await asyncio.sleep(5)   
                
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

    def set_session_id(self, new_session_id):
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Def set_session_id entered")
        print(f"MT Line {inspect.currentframe().f_lineno} Set session ID entered Self.session: {self.session_id} New session ID: {new_session_id}")
        if new_session_id is None:
            print(f"MT Line {inspect.currentframe().f_lineno} Should never happen: MT Session ID is None, setting to 1")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Should never happen: MT Session ID is None, setting to 1")
            self.session_id = 1
        else:            
            self.session_id = new_session_id
            #self.race_message_updated.emit(f"Waiting for a new race to start...Current Session: {self.session_id}")
            print(f"MT Line {inspect.currentframe().f_lineno} Monitorapp Session ID updated to {self.session_id}")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Monitorapp Session ID updated to {self.session_id}")
    
    async def cache_api_data(self):
        while self.start_cache_data:  # Loop until the cache is stopped
            await asyncio.sleep(self.fetch_api_delay)  # Sleep for a short duration to avoid busy-waiting
            self.cached_data = await self.get_api_data()  # Fetch the API data
        print(f"MT Line {inspect.currentframe().f_lineno} Cache API data stopped.")

    async def get_api_data(self):
        error_message_shown = False
        self.no_server_connection = True
        if not self.running: return
        if self.session is None: self.session = aiohttp.ClientSession()
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
                                print(f"MT Line {inspect.currentframe().f_lineno} Connection Restored")
                                logging.info(f"MT Line {inspect.currentframe().f_lineno} Connection Restored")
                                self.connection_restored.emit() # Emit signal for successful connection restoration to clear the error message
                                self.connecton_restored_message_shown = True
                            current_game_state = data['gameStates']['mGameState']
                            current_race_state = data['gameStates']['mRaceState']
                            current_session_state = data['gameStates']['mSessionState']
                            if current_race_state != self.previous_race_state:
                                print(f"MT Line {inspect.currentframe().f_lineno} Race state changed to {current_game_state}")  # Ensure console output remains
                                logging.info(f"MT Line {inspect.currentframe().f_lineno} Race state changed to {current_race_state}")
                                self.previous_race_state = current_race_state
                            if current_game_state != self.previous_game_state:
                                print(f"MT Line {inspect.currentframe().f_lineno} Game state changed to {current_game_state}")  # Ensure console output remains
                                logging.info(f"MT Line {inspect.currentframe().f_lineno} Game state changed to {current_game_state}")
                                self.previous_game_state = current_game_state
                            if current_session_state != self.previous_session_state:
                                print(f"MT Line {inspect.currentframe().f_lineno} Session State changed to {current_session_state}")  # Ensure console output remains
                                logging.info(f"MT Line {inspect.currentframe().f_lineno} Session state changed to {current_session_state}")
                                self.previous_session_state = current_session_state
                            if not self.running or self.session is None: return
                            return data # return if the response is valid
                            
                    except ValueError as ve:
                        if not error_message_shown:
                            logging.error(f"MT Line {inspect.currentframe().f_lineno} Error parsing JSON response: {ve}")
                            print(f"MT Line {inspect.currentframe().f_lineno} Error parsing JSON response: {ve}")
                            error_message_shown = True
                            self.connecton_restored_message_shown = False
                        await asyncio.sleep(2)  # Wait for 5 seconds before fetching the next data
                else:
                    if not error_message_shown:
                        logging.error(f"MT Line {inspect.currentframe().f_lineno} Unexpected status code {response.status} received from the API.")
                        print(f"MT Line {inspect.currentframe().f_lineno} Unexpected status code {response.status} received from the API.")
                        self.error_occurred.emit(f'Game Not Started: Unexpected status code {response.status}')
                        error_message_shown = True
                        self.connecton_restored_message_shown = False
                    await asyncio.sleep(5)  # Wait for 5 seconds before fetching the next data
        except asyncio.CancelledError:
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Operation cancelled due to application shutdown.")
            return None
        except Exception as e:
            self.error_occurred.emit(f'Connection Error: Check IP Address in Config.ini:')
            if not error_message_shown:
                logging.error(f"MT Line {inspect.currentframe().f_lineno} An error occurred while fetching API Data {e}")
                print(f"MT Line {inspect.currentframe().f_lineno} An error occurred while fetcing API Data: {e}")
                error_message_shown = True
                self.connecton_restored_message_shown = False
            await asyncio.sleep(5)
        finally:
            self.no_server_connection = True
            if self.ip_adress_changed:
                if self.session:
                    try:
                        await self.session.close()  # Safely close the session
                    except Exception as e:
                        logging.error(f"MT Line {inspect.currentframe().f_lineno} Error while closing session: {e}")
                    self.session = None  # Reset the session to None after closing it
                    self.ip_adress_changed = False
        
    async def connection_monitor(self):
        while self.running:
            try:
                self.ip_address = self.config_manager.read_ip_address()
                if self.previous_ipaddress != self.ip_address:
                    self.previous_ipaddress = self.ip_address
                    self.ip_address_updated.emit(self.ip_address)
                    self.ip_adress_changed = True
                    print(f"MT Line {inspect.currentframe().f_lineno} IP address changed to {self.ip_address}")
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} IP address changed to {self.ip_address}")

                # Optional: test connectivity or emit heartbeat

            except Exception as e:
                logging.error(f"MT Line {inspect.currentframe().f_lineno} Error in connection monitor: {e}")

            await asyncio.sleep(2)  # Adjust interval as needed

    async def qualify_running(self, data):
        print(f"MT Line {inspect.currentframe().f_lineno} Qualify Running!")
        logging.info("Qualify Running!")
        while data['gameStates']['mSessionState'] == 3:
            # print(f"Qualify Session State: {data['gameStates']['mSessionState']}")
            #self.race_message_updated.emit("Qualifying Running...")
            if not self.running: break
            data = await self.get_api_data()
            if data is not None: 
                self.data_updated.emit(data)
    
    async def practice_running(self, data):
        print(f"MT Line {inspect.currentframe().f_lineno} Practice Running!")
        logging.info("Practice Running!")
        while data['gameStates']['mSessionState'] == 1:
            # print(f"Practice Session State: {data['gameStates']['mSessionState']}")
            if not self.running: break
            data = await self.get_api_data()
            if data is not None:
                self.data_updated.emit(data)

    async def race_running(self, data):
        if not self.running: return
        race_in_session = True
        if data is not None:
            self.data_updated.emit(data)
        lap_times_dict = {} # Clear the lap times dictionary ready for next race.
        last_lap_counts = {} # Clear the last lap counts dictionary
        driver_total_times = {} # Clear the driver total times dictionary
        driver_flags ={} # Clear the driver flags dictionary
        QMetaObject.invokeMethod(self.tab_widget, "setCurrentIndex", Qt.QueuedConnection, Q_ARG(int, 0)) #Switch to Score View tab
        print(f"MT Line {inspect.currentframe().f_lineno} Race is STARTING!!!!!!.")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Race is STARTING!!!!!!.")
        print(f"MT Line {inspect.currentframe().f_lineno} Data to be written to database, Session id: {self.session_id}")
        logging.info(f"MT Line {inspect.currentframe().f_lineno} Data to be written to database: race index: {self.race_id} Sesson id: {self.session_id}")
        self.track_location = data['eventInformation']['mTranslatedTrackVariation']+ ' - ' + data['eventInformation']['mTranslatedTrackLocation']
        while self.session_id == 0: # Just to be sure the session ID is not 0, wait for it to be updated from RaceMonitorApp Thread via signalling.
            await asyncio.sleep(0.50)  # Wait for 0.5 seconds before checking again
            print(f"MT Line {inspect.currentframe().f_lineno} Waiting for session ID to be updated. Current session ID: {self.session_id}")
            logging.info(f"MT Line {inspect.currentframe().f_lineno} Waiting for session ID to be updated. Current session ID: {self.session_id}")
        if not self.time_trial: # If it is not a time trial, write race to DB    
            self.db_queue.put(('write_race', (data, self.session_id)))
            print(f"MT Line {inspect.currentframe().f_lineno} Session ID received: {self.session_id} Race written to database.")
        self.db_queue.put(('get_latest_race_id', (self.set_race_id,)))  # Only pass the necessary data, not the function
        print(f"MT Line {inspect.currentframe().f_lineno} self.race_id: {self.race_id}")
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
        while race_in_session:
            if not self.running: break
            previous_data = data
            #start_time = time.time()     #loop while race is running
            #self.start_cache_data = True
            #await asyncio.sleep(cache_delay)  # Tune for minimum delay between API calls
            try:
                #start_time = time.time() # Start the timer for measuring API response time
                data = await self.get_api_data()
                #data = self.cached_data if hasattr(self, 'cached_data') else await self.get_api_data()  # Fetch the API data
                #if data == previous_data:
                #    skippet += 1
                #    if skippet % 10 == 0:  # Print every 1000th time to avoid flooding the console
                #        print(f"MT Line {inspect.currentframe().f_lineno} Data is the same as previous data, Skipped {skippet} times.")
                #        logging.info(f"MT Line {inspect.currentframe().f_lineno} Data is the same as previous data, Skipped {skippet} times.")

                #    cache_delay += 0.0001  # Increase cache delay if data is the same as previous data
                #    if cache_delay > 0.020:  # Adjust the threshold as needed
                #        self.fetch_api_delay = cache_delay - 0.06 # Update the fetch API delay 
                    # print(f"MT Line {inspect.currentframe().f_lineno} Data is the same as previous data, skipping this loop. Cache delay increased to {cache_delay:.3f} seconds. fetch_api_delay set to {self.fetch_api_delay:.3f} seconds.")
                #    response_time_ms += 1
                      # Skip the rest of the loop if data is the same as previous data
                #else:
                #    not_skippet += 1
                #    if not_skippet % 10 == 0:  # Print every 1000th time to avoid flooding the console
                #        print(f"MT Line {inspect.currentframe().f_lineno} Data is different from previous data, Not Skipped {not_skippet} times.")
                #        logging.info(f"MT Line {inspect.currentframe().f_lineno} Data is different from previous data, Not Skipped {not_skippet} times.")

                #if self.race_loop_first_time: logging.info(f"MT Line {inspect.currentframe().f_lineno} RaceID is: {self.race_id}.")
                 # Store the previous data
                #if cache_delay > 0.0334:  # Adjust the threshold as needed
                #    cache_delay = 0.0167  # Reset the cache delay if it exceeds the threshold
                #    self.fetch_api_delay = 0.01  # Reset the fetch API delay to the initial value
                #else:
                #    cache_delay -= 0.01 
                #end_time = time.time()
                #elapsed_time.append(end_time - start_time)
                #response_time_ms = (end_time - start_time) * 1000  # Convert to milliseconds
                #self.api_response_time_updated.emit(response_time_ms)  # Emit response time

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
                        race_in_session = False
                    elif not data['eventInformation']['mLapsInEvent'] == 0: # If it is a time trial, continue loop until no participants are found.                           
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} All participants finished, Race is over,Sending Data one last time, breaking the loop")
                            print(f"MT Line {inspect.currentframe().f_lineno} All participants finished race, Race is over. Sending Data one last time.")
                            self.race_may_not_be_finished = True
                            race_in_session = False

                if not self.running: break
                if data is not None: 
                    self.data_updated.emit(data) #Send the data to Live view
                for participant in participants:
                    if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                    if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0   
                    if (participant.get('mCurrentLap', 0) > last_lap_counts.get(participant['mName'], 1)) and (participant.get('mLastLapTimes') != -123):
                        if participant['mName'] not in lap_times_dict: lap_times_dict[participant['mName']] = [] # Initialize the key with an empty list
                        if participant['mName'] not in driver_total_times: driver_total_times[participant['mName']] = 0  # Initialize the key with a value of 0                                    
                        driver_total_times[participant['mName']] += participant.get('mLastLapTimes', 0)
                        if not self.time_trial:  
                            self.db_queue.put(('insert_lap_data', (self.race_id, participant['mName'], participant.get('mCurrentLap', 0) - 1,participant.get('mLastLapTimes'), self.track_location, participant['mCarNames']))) #insert lap into Table
                            lap_times_dict[participant['mName']].append(participant.get('mLastLapTimes', None))
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Storing lap time for {participant['mName']}: Lap {participant.get('mCurrentLap', 0)}, Time {participant.get('mLastLapTimes', 0)},Last Lap:{participant.get('mLastLapTimes', None)} Driver Total Time: {driver_total_times[participant['mName']]} ")
                    else:
                        if (participant.get('mSpeeds',0) >10) and (data['gameStates']['mRaceState'] == 1) and (driver_flags.get(participant['mName'],None) != 'Falsestart'):
                            print(f"MT Line {inspect.currentframe().f_lineno} Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Adding Falsestart to Flags for {participant['mName']} Current lap:{participant.get('mCurrentLap', 0)}")
                            driver_flags[participant['mName']] = 'Falsestart'
                            if driver_flags is not None: self.flags_updated.emit(driver_flags)
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
                        if driver_flags is not None:
                            logging.info(f"MT Line {inspect.currentframe().f_lineno} Participant: {participant_name}, Flags: {driver_flags}")
                            if driver_flags.get(participant_name) != 'Falsestart': # Check if the participant has a 'Falsestart' flag
                                print(f"MT Line {inspect.currentframe().f_lineno} Adding DNF to Flags for {participant_name}")
                                logging.info(f"MT Line {inspect.currentframe().f_lineno} Adding DNF to Flags for {participant_name}")
                                driver_flags[participant_name] = 'DNF'
                                if driver_flags is not None: self.flags_updated.emit(driver_flags) 
                                await asyncio.sleep(0.5)
                if not self.time_trial:                                
                    self.db_queue.put(('finalize_race', (data, lap_times_dict,driver_flags, self.pit_stops_dict))) # Write final data to DB
                    print(f"MT Line {inspect.currentframe().f_lineno} Finalizing race")
                    logging.info(f"MT Line {inspect.currentframe().f_lineno} Finalizing race")
                if data is not None: self.data_updated.emit(data) #Send the data to Live view to update the flags
                race_valid = True
                self.race_finished.emit(race_valid, self.session_id)
                self.start_cache_data = False
                print(f"MT Line {inspect.currentframe().f_lineno} Race finished emitted")
                print(f"MT Line {inspect.currentframe().f_lineno} Race Finished for session ID: {self.session_id}")
                # self.db_queue.put(('load_score_data', (self.session_id,)))  # Only pass the necessary data, not the function
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

class RaceMonitorApp(QMainWindow):
    session_id_updated = pyqtSignal(int)  # Signal to update the SessionID
    pit_stops_updated = pyqtSignal(dict)  # Signal to update the pit stops
    get_request_for_sim_signal = pyqtSignal()  # Signal to update driver sims
    #delete_db = pyqtSignal()  # Signal to delete the database
    def __init__(self):
        super().__init__()
        self.db_queue = queue.Queue()
        self.config_manager = ConfigManager(self.db_queue)
        self.update_config_file = self.config_manager.update_config_file(self)
        self.db_thread = DatabaseThread(self.db_queue, self.config_manager)
        # self.temp_dir = tempfile.gettempdir()
        self.response_time_log = {}
        self.last_flush = time.time()
        #atexit.register(self.write_logs_on_exit)
        
        self.temp_dir = "tmp/"
        self.initUI() # Initialize the GUI
        self.monitor_thread = MonitorThread(self, self.tab_widget, self.db_queue, self.config_manager)
        self.control_panel = ControlPanel(self.db_thread, self.config_manager, self)  # Pass the db_thread and config_manager to ControlPanel
        self.monitor_thread.start()
        self.db_thread.start()
 
        #Variable initialization
        self.live_first_time_run =True
        self.driver_view_first_update = True  # Set to True to trigger first update in driver view
        self.session_id_dropdown = None
        self.latest_session_id = None  # Initialize latest_session_id to None
        self.racestarted = False
        self.time_trial = False
      
        self.do_not_reset_index = False
        self.selected_race_id = 0
        self.all_driver_dropdown_items = []
        self.speedo_max = 320
        self.speedo_sweep = (0, 225)
        self.tacho_max = 14000
        self.tacho_sweep = (0, 245)
        
        # Signal connections
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.data_updated.connect(self.update_driver_view)  # Connect the signal to the slot that updates driver data
        self.monitor_thread.flags_updated.connect(self.update_flags)
        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.qualify_finished.connect(self.qualify_finished)
        self.monitor_thread.practice_finished.connect(self.practice_finished)
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
        self.control_panel.driver_sims_updated.connect(self.update_driver_names)  # Connect the signal to the slot that updates the driver names
        self.monitor_thread.race_message_updated.connect(self.update_race_message)  # Connect the signal to the slot that updates the race message
        self.monitor_thread.api_response_time_updated.connect(self.update_api_response_graph)
        self.monitor_thread.session_type_updated.connect(self.handle_session_type)  # Connect the signal to the slot that handles time trial detection
        
        #Set the Status view as the default tab
        self.tab_widget.setCurrentIndex(2)
        self.tab_widget.setCurrentIndex(1)
        
        # self.monitor_thread.results_view_message.connect(self.update_results_view_message)  # Connect the signal to the slot that updates the results view message
        # Call the function to load race data 
        print(f"RMA Line {inspect.currentframe().f_lineno} Get latest session ID from DB.")
        self.db_queue.put(('get_latest_session_id', (self.set_session_id,)))

    def update_driver_names(self, driver_sims):
        """Populat the driver_sims variable."""
        if not driver_sims:
            print(f"RMA Line {inspect.currentframe().f_lineno} No driver sims provided, skipping update.")
            return
        self.driver_sims = driver_sims
        print(f"RMA Line {inspect.currentframe().f_lineno} Driver sims updated: {self.driver_sims}")

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

    def base64_to_font(self, base64_str, filename):
        """Convert a base64 string to a QFont object."""
        font_data = base64.b64decode(base64_str)
        font_path = os.path.join(self.temp_dir, filename)

        with open(font_path, "wb") as font_file:
            font_file.write(font_data)

        font_id = QFontDatabase.addApplicationFont(font_path)

        if font_id == -1:
            print(f"RMA Line {inspect.currentframe().f_lineno} Failed to load font!")
        else:
            print(f"RMA Line {inspect.currentframe().f_lineno} Font loaded successfully with ID: {font_id}")

        return QFontDatabase.applicationFontFamilies(font_id)[0]

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
        self.speedometer_image = self.base64_to_pixmap(speedometer_bg_img_base64)  # Speedometer image
        self.tachometer_image = self.base64_to_pixmap(tachometer_bg_img_base64)  # Tachometer image
        self.needle_image = self.base64_to_pixmap(needle_bg_img_base64)  # Needle image 
        self.lap_image = self.base64_to_pixmap(lap_bg_img_base64)  # Lap image
        self.bestlaptime_image = self.base64_to_pixmap(bestlap_bg_img_base64)  # Best lap image
        self.wheel_image = self.base64_to_pixmap(wheel_bg_img_base64)  # Wheel image
        self.pedals_image = self.base64_to_pixmap(pedal_bg_img_base64)  # Pedals image
        self.pos_image = self.base64_to_pixmap(pos_bg_img_base64)  # Position image
        self.laptime_image = self.base64_to_pixmap(laptime_bg_img_base64)  # Laptime image
        self.window_icon = self.base64_to_qicon(icon_base64)
        self.setWindowIcon(self.window_icon)
        self.font_family = self.base64_to_font(sui_generis_rg_font_base64, "generis_font.ttf")
        self.font_family_digits = self.base64_to_font(ds_digib_font_base64, "ds_digib_font.ttf")


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
        self.driver_info_tab = QWidget()
        self.top_layout = QHBoxLayout()
        self.info_layout = QVBoxLayout()
        self.progress_layout = QHBoxLayout()

        # Set up layouts for each tab
        self.driver_view_layout = QVBoxLayout(self.driver_info_tab)
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
        self.tab_widget.addTab(self.driver_info_tab, "Driver Info")

        # Add your existing widgets and layout configurations to the appropriate tab layouts
        self.setup_live_view() # Initialize the live view
        self.setup_final_view() # Initialize the final view
        self.setup_result_view() # Initialize the result view
        self.setup_highscore_view() # Initialize the highscore view
        self.setup_driver_statistics_view() # Initialize the driver statistics view
        self.setup_driver_info_view() # Initialize the driver info view
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
        self.dropdown_races = QComboBox(self)
        self.labels['dropdown_races'] = self.dropdown_races
        self.dropdown_races.setStyleSheet("""
            font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)        
        self.dropdown_races.setFixedSize(600, 30)
        #self.dropdown.currentIndexChanged.connect(self.load_selected_race)
        self.dropdown_races.activated.connect(self.load_selected_race)
        self.layout.addWidget(self.dropdown_races, alignment=Qt.AlignTop)

        # Add a calendar widget
        self.calendar_widget = QCalendarWidget(self)
        self.labels['calendar_widget'] = self.calendar_widget
        self.calendar_widget.setStyleSheet("""
            font-size: 10px;
            color: black;
            background-color: white;
            border: 1px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)
        self.calendar_widget.setGeometry(700, 975, 300, 150)  # Set the geometry of the calendar widget
        self.calendar_widget.setGridVisible(True)
        self.calendar_widget.setSelectedDate(QDate.currentDate())  # Set the current date as selected
        self.calendar_widget.clicked.connect(self.load_race_for_date)

        #Add Dropdown for selecting Sessions
        self.dropdown_sessionid = QComboBox(self)
        self.labels['dropdown_sessionid'] = self.dropdown_sessionid
        self.dropdown_sessionid.setEditable(True)
        self.dropdown_sessionid.setStyleSheet("""
            font-size: 14px;
            color: black;
            background-color: white;
            border: 2px solid black;  /* Change the border color */
            border-radius: 5px;  /* Optional: rounded corners */
            padding: 2px 5px;  /* Optional: padding inside the dropdown */
        """)        
        self.dropdown_sessionid.setFixedSize(300, 30)
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
        self.new_session_button = QPushButton("Next Session", self)
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
            1: ['dropdown_races', 'delete_button', 'delete_all_races_button', 'calendar_widget'  ],  # Widgets for Results View
            2: ['new_session_button', 'dropdown_sessionid', 'previous_session_button' ],  # Widgets for Score View
            3: ['car_dropdown', 'track_dropdown', 'load_high_scores_button'],  # Widgets for High Scores
            4: ['driver_dropdown', 'delete_driver_button']  # Widgets for Driver Statistics
        }

    def load_race_for_date(self, date):
        print(f"RMA Line {inspect.currentframe().f_lineno} load race for date def entered with parameter: {date}")
        # Convert the selected date to a string in the format "YYYY-MM-DD"
        number_of_date_matches = 0
        selected_date_str = date.toString("yyyy-MM-dd")
        print(f"RMA Line {inspect.currentframe().f_lineno} Selected date string: {selected_date_str}")
        # Convert the selected date to the desired format
        selected_date_converted = f"{date.day()}. {date.toString('MMMM').lower()} {date.year()}"
        print(f"RMA Line {inspect.currentframe().f_lineno} Converted date: {selected_date_converted}")
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Searching for race on date: {selected_date_str}")
        print(f"RMA Line {inspect.currentframe().f_lineno} Searching for race on date: {selected_date_str}")

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
                self.db_queue.put(('load_selected_race', (self.dato_selected_race_id,)))  # Queue the operation to DatabaseThread
                self.results_message_label.setText(f"Found {number_of_date_matches} Races on {selected_date_converted}, starting with {self.dato_selected_race_id}")
                self.dropdown_races.setCurrentIndex(selected_index)  # Set the selected index in the dropdown
                self.do_not_reset_index = True  # Prevent resetting the index in the dropdown
                number_of_date_matches = 0  # Reset the counter for the next search
                logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Load selected race Signal Sent for Race ID: {self.dato_selected_race_id}")
                print(f"RMA Line {inspect.currentframe().f_lineno} Selected Race ID: {self.dato_selected_race_id}")

        else:
            self.results_message_label.setText(f"No Race found for the selected date: {selected_date_str}")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} No race found for the selected date: {selected_date_str}")
            print(f"RMA Line {inspect.currentframe().f_lineno} No race found for the selected date: {selected_date_str}")

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
            print(f"RMA Line {inspect.currentframe().f_lineno} Edit line focused, calling clear_driver_dropdown...")
            self.clear_driver_dropdown()  # Call your method
            return True  # Indicate that the event was handled
        # Pass other events to the default handler
        return super().eventFilter(obj, event)

    def delete_db(self):
        logging.info("RMA Delete DB def entered")
        #print(f"RMA Line {inspect.currentframe().f_lineno} Delete DB def entered
        self.db_queue.put(('delete_db', ()))
        self.set_delete_db_mode(True)
        QTimer.singleShot(5000, lambda: self.set_delete_db_mode(False))

    def delete_all_races(self):
        logging.info("RMA Delete all reaces def entered")
        #print(f"RMA Line {inspect.currentframe().f_lineno} Delete DB def entered
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
        #print(f"RMA Line {inspect.currentframe().f_lineno} Flags updated def entered")
        self.driver_flags=flags # Update the flags label with the message
        
    def initialize_dropdown(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Initialize Dropdown def entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Initialize Dropdown def entered")
        self.db_queue.put(('load_race_data_on_start', ()))
        self.db_queue.put(('load_sessionid_on_start', ()))
        self.db_queue.put(('load_highscores_on_start', ()))
        self.db_queue.put(('load_driver_statistics_on_start', ()))
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Initialize Dropdown completed")
        print(f"RMA Line {inspect.currentframe().f_lineno} Initialize Dropdown completed")
      
    def update_ip_address(self, ip_address):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Update IP Address def entered")
        #print(f"RMA Line {inspect.currentframe().f_lineno} Update IP Address def entered")
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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def set_session_id entered. new.session_id: {new_session_id}, dato: {dato}")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def set_session_id entered. new.session_id: {new_session_id}, dato: {dato}")
        
        if new_session_id is None:
            print(f"RMA Line {inspect.currentframe().f_lineno} Session ID not found in the database, setting to 1")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Session ID not found in the database, setting to 1")
            self.session_id = 1
            self.session_id_updated.emit(self.session_id)
            self.latest_session_id = 0
        else:
            print(f"RMA Line {inspect.currentframe().f_lineno} Session ID fetched: ({new_session_id})")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Session ID fetched: ({new_session_id})")
            dato = datetime.strptime(dato, "%Y-%m-%d").date()
            if dato != datetime.now().date():
                logging.info(f"RMA Line {inspect.currentframe().f_lineno} Date from DB: {dato}")
                print(datetime.now().date())
                logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Session ID is not for today, setting to +1. Session ID: {self.session_id}")
                self.session_id = new_session_id + 1
                print(f"RMA Line {inspect.currentframe().f_lineno} Session ID is not for today, setting to +1: self.sesssion_id: {self.session_id} ")
                # self.db_queue.put(('load_score_data',(self.session_id-1,))) # Get the score data for the current session ID
            else:
                self.session_id = new_session_id
                print(f"RMA Line {inspect.currentframe().f_lineno} Session ID is for today, setting to {self.session_id}.")
            self.session_id_updated.emit(self.session_id)
            self.latest_session_id = new_session_id
        print(f"RMA Line {inspect.currentframe().f_lineno} set_session:id: Latest DB Session ID set to new_session_id or 0 if empty DB: {self.latest_session_id}")
            # self.db_queue.put(('load_score_data',(new_session_id,))) # Get the score data for the last race current session ID
        self.live_heading.setText(f"Waiting for Race Start. Current Session: {self.session_id}")  # Update the status label        
    
    def handle_session_type(self,session_type):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def handle session_type detected entered with parameter: {session_type}")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def handle session_type detected entered with parameter: {session_type}")
        self.live_heading.setText(f"{session_type} detected.")  # Update the status label
        self.session_type = session_type  # Store the session type for later use
    
    def handle_race_data_on_start(self, races, participants):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def handle race data on start entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def handle_race_data_on_start entered")
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
            print(f"RMA Line {inspect.currentframe().f_lineno} Number of races loaded: {len(races)}")
            if not len(races) >1: self.load_selected_race()
            else: self.results_heading.setText("\n Select a Race to View previous races") 
        else:  
            self.results_name.setText("No Races in DB")
            self.final_heading.setText("\n All races Deleted")     

    def handle_high_scores_data_on_start(self, high_scores):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def handle high scores data entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def handle high scores data entered")
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
            print(f"RMA Line {inspect.currentframe().f_lineno} Number of high scores loaded: {len(high_scores)}")
            #print(f"High Scores Dictionary: {self.highscores_dict}")
        else:
            self.highscore_name.setText("No High Scores in DB")
        self.car_dropdown.blockSignals(False)
        self.track_dropdown.blockSignals(False)
        self.update_dropdowns()

    def load_selected_highscore(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} load_selected_highscore def entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} load_selected_highscore def entered")
        selected_car = self.car_dropdown.currentText()
        selected_track = self.track_dropdown.currentText()
        print(f"RMA Line {inspect.currentframe().f_lineno} Selected Car: {selected_car} Selected Track: {selected_track}")
        if self.car_dropdown.currentIndex() >= 0 and self.track_dropdown.currentIndex() >= 0:
            self.db_queue.put(('load_highscores', (selected_car, selected_track)))
            print(f"RMA Line {inspect.currentframe().f_lineno} Load score for {selected_car} on {selected_track}")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Load score for {selected_car} on {selected_track}")
        else:
            print(f"RMA Line {inspect.currentframe().f_lineno} Car or Track not selected:{selected_car} {selected_track}")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Car or Track not selected:{selected_car} {selected_track}")

    def update_dropdowns(self):
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} update dropdowns def entered")
            print(f"RMA Line {inspect.currentframe().f_lineno} update dropdowns def entered")
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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} clear driver dropdown def entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} clear driver dropdown def entered")
        self.driver_dropdown.blockSignals(True)
        self.driver_dropdown.setItemText(0, "")
        self.driver_dropdown.setCurrentIndex(0)
        self.driver_dropdown.blockSignals(False)

    def handle_driver_statistics_on_start(self, driverdata):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def handle driver statistics on start entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def handle driver statistics on start entered")
        self.driver_dropdown.clear()  # Clear the dropdown first
        self.driver_dropdown.addItem("Select a driver or type a driver name...")
        self.driver_dropdown.blockSignals(True)
        self.driverdata = driverdata  # Store the driver data in a class variable
        if driverdata:
            for driver in driverdata:
                driver_name, lapnumber, bestlap, track, car = driver
                if driver_name not in [self.driver_dropdown.itemText(i) for i in range(self.driver_dropdown.count())]: self.driver_dropdown.addItem(driver_name)
            self.driver_dropdown.setCurrentIndex(0)
            print(f"RMA Line {inspect.currentframe().f_lineno} Number of Highscores loaded: {len(driverdata)}")
            if len(driverdata) == 2: self.load_selected_driver()
            else: self.driver_statistics_heading.setText("\n Select a Driver to View Driver Statistics")
            self.all_driver_dropdown_items = [self.driver_dropdown.itemText(i) for i in range(1, self.driver_dropdown.count())]
        else:
            self.driver_statistics_heading.setText("\n No Driver Statistics in DB")
        self.driver_dropdown.blockSignals(False)

    def load_selected_driver(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} on driver statistics loaded def entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} on driver statistics loaded def entered")
        selected_driver = self.driver_dropdown.currentText()
        if self.driver_dropdown.currentIndex() > 0:
            print(f"RMA Line {inspect.currentframe().f_lineno} Load driver statistics for {selected_driver} with index {self.driver_dropdown.currentIndex()}")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Load driver statistics for {selected_driver}")
            driver = selected_driver
            heading = (f"<br><span style='color:{self.color_labels}'>Driver:</span> <span style='color:{self.color_values}'>{driver}</span><br>")
            loaded_lap = ''
            loaded_bestlap = ''
            loaded_track = ''
            loaded_car = ''
            if any(driver == record[0] for record in self.driverdata):
                print(f"RMA Line {inspect.currentframe().f_lineno} Driver found: {driver}")
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
            print(f"RMA Line {inspect.currentframe().f_lineno} Driver not selected:{selected_driver}")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Driver not selected:{selected_driver}")
            return
        
    def load_selected_race(self): # Function to be called when the data is loaded
        print(f"RMA Line {inspect.currentframe().f_lineno} Load Selected race def entered")
        logging.info("RMA Load Selected race def entered")
        selected_index = self.dropdown_races.currentIndex()
        self.results_message_label.setText(f"") # Clear the message label
        if selected_index > 0:
            race_text = self.dropdown_races.itemText(selected_index)
            match = re.search(r"Race_(\d+)", race_text)
            self.selected_race_id = int(match.group(1))  # The number after "Race_"
            self.db_queue.put(('load_selected_race', (self.selected_race_id,) )) # Queue the operation to DatabaseThread
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Load selected race Signal Sent")
        else:
            print(f"RMA Line {inspect.currentframe().f_lineno} Race not selected:{selected_index}")   
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Race not selected:{selected_index}")
        
    def on_race_loaded(self, race, participants, laps):
        logging.info("RMA on race loaded def entered")
        race_id, track_variation, laps_in_event, session_id = race # Function to be called when the data is loaded
        #print(f"Signal received")
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Load selected race Signal received")
        loaded_names = ''
        loaded_places = ''
        loaded_flags = ''
        loaded_pitstops = ''
        loaded_totals = ''
        loaded_bestlap = ''
        loaded_points = ''
        #best_lap_time = {}

        if race_id:
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Load Selected Race, RaceID: {race_id}")
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
            best_lap_points = int(self.config['Score Table'].get('best_lap', 0)) 
            best_lap_participant = min(participants, key=lambda p: p[2] if p[2] not in (None, 0) else float('inf'))
            print(f"RMA Line {inspect.currentframe().f_lineno} Best Lap Participant: {best_lap_participant[0]} with time: {best_lap_participant[2]}")

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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def on highscore loaded entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def on highscore loaded entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} self.track_dropdown: {self.track_dropdown.currentText()} self.car_dropdown: {self.car_dropdown.currentText()}" )
        heading = (f"<span style='color:{self.color_labels}'>Track: </span><span style='color:{self.color_values}'>{self.track_dropdown.currentText()} </span><br><span style='color:{self.color_labels}'>Car: </span><span style='color:{self.color_values}'> {self.car_dropdown.currentText()}</span><br>" ) # Update the heading with track variation and car names
        if self.tab_widget.currentWidget() != self.highscore_view_widget:
            if high_scores != None:
                heading = (f"<span style='color:{self.color_labels}'>Track: </span><span style='color:{self.color_values}'>{high_scores[0][3]} </span><br><span style='color:{self.color_labels}'>Car: </span><span style='color:{self.color_values}'> {high_scores[0][4]}</span><br>" ) # Update the heading with track variation and car names
                self.trackrecorddb = min(high_scores, key=lambda x: x[2])[2]
                self.recorddriver, _, self.trackrecorddb, _, _ = min(high_scores, key=lambda x: x[2])
            else:
                self.trackrecorddb = 0
                self.recorddriver = ""
            self.live_heading.setText(f" {self.live_heading.text()} - Track Record: {self.format_lap_time(self.trackrecorddb) if self.trackrecorddb != 0 else 'Unavailable'}")
            self.driver_view_first_update = True  # Set to True to trigger first update in driver view
            
        print(f"RMA Line {inspect.currentframe().f_lineno} High Scores variable self.highscores is set! ")
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
            print(f"RMA Line {inspect.currentframe().f_lineno} Best Lap: {best_lap}")
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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def handle sessionid data entered")
        self.dropdown_sessionid.clear()  # Add this line to clear the dropdown
        self.sessionids = sessionids
        if sessionids:
            self.dropdown_sessionid.addItem("Use DropDown or Type ID:")  # Add explanatory text
            self.dropdown_sessionid.setCurrentIndex(0)  # Set it as the default selected item
        if self.latest_session_id > 0:   
            for session_id in reversed(sessionids):  # Iterate over sessionids in reverse order
                if len(sessionids) > 1:
                    self.dropdown_sessionid.blockSignals(True)
                self.dropdown_sessionid.addItem(f"Session ID - {session_id}")
                if len(sessionids) > 1:
                    self.dropdown_sessionid.blockSignals(False)
                
    def on_tab_changed(self, index):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
        #print(f"RMA Line {inspect.currentframe().f_lineno} Def on_tab_changed entered")
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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def update_background entered")
        if view == 'status': self.background_label.setPixmap(self.live_status_image)
        elif view == 'live': self.background_label.setPixmap(self.live_background_image)

    def handle_connection_restored(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def handle_connection_restored entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def handle_connection_restored entered")
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()

    def show_error_message(self, message): # Check if the error label already exists with the same message
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def show_error_message entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def show_error_message entered")
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
        #print(f"RMA Line {inspect.currentframe().f_lineno} Def toggle_error_visibility entered")
        if hasattr(self, 'error_label') and self.error_label is not None:
            if self.error_label.isVisible(): self.error_label.setVisible(False)
            else: self.error_label.setVisible(True)
 
    def update_race_message(self, message):
        print(f"RMA Line {inspect.currentframe().f_lineno} Race Message: {message}")
        #logging.info(f"Line {inspect.currentframe().f_lineno} RMA RaceMessage: {message}")
        self.live_status_label.setText(f"{message}")  # Update the status label  

    def setup_live_view(self): # Setup your live view widgets here
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_live_view entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def setup_live_view entered {self.session_id}")
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

    def setup_driver_info_view(self): # Setup your driver info view widgets here
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_driver_info_view entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def setup_driver_info_view entered")
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

        self.car_heading_text = QLabel("Car:", self.driver_info_tab)
        self.car_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.car_heading_text.setMinimumSize(100, 50)
        self.car_heading_text.move(25, 300)
        self.track_heading_text = QLabel("Track:", self.driver_info_tab)
        self.track_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.track_heading_text.setMinimumSize(100, 50)
        self.track_heading_text.move(25, 350)
        self.driver_heading_text = QLabel("Driver:", self.driver_info_tab)
        self.driver_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.driver_heading_text.setMinimumSize(100, 50)
        self.driver_heading_text.move(25, 400)
        self.collison_heading_text = QLabel("Crash:", self.driver_info_tab)
        self.collison_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.collison_heading_text.setMinimumSize(100, 50)
        self.collison_heading_text.move(25, 450)
        self.worldrecord_heading_text = QLabel("World Record:", self.driver_info_tab)
        self.worldrecord_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.worldrecord_heading_text.setMinimumSize(200, 50)
        self.worldrecord_heading_text.move(25, 500)
        self.localrecord_heading_text = QLabel("Local Record:", self.driver_info_tab)
        self.localrecord_heading_text.setStyleSheet(f"font-family:{font_name};font-size: 22px;")
        self.localrecord_heading_text.setMinimumSize(200, 50)
        self.localrecord_heading_text.move(25, 550)

        self.car_txt = QLabel("Car", self.driver_info_tab)
        self.car_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.car_txt.setMinimumSize(500, 50)
        self.car_txt.move(90, 300)
        self.track_txt = QLabel("Track", self.driver_info_tab)
        self.track_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.track_txt.setMinimumSize(500, 50)
        self.track_txt.move(110, 350)
        self.driver_txt = QLabel("Driver", self.driver_info_tab)
        self.driver_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.driver_txt.setMinimumSize(300, 50)
        self.driver_txt.move(115, 400)
        self.collison_txt = QLabel("Crash", self.driver_info_tab)
        self.collison_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.collison_txt.setMinimumSize(300, 50)
        self.collison_txt.move(115, 450)
        self.worldrecord_txt = QLabel("World Record", self.driver_info_tab)
        self.worldrecord_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.worldrecord_txt.setMinimumSize(300, 50)
        self.worldrecord_txt.move(200, 500)
        self.localrecord_txt = QLabel("Local Record", self.driver_info_tab)
        self.localrecord_txt.setStyleSheet(f"font-family:{font_name};font-size: 22px; color: red;")
        self.localrecord_txt.setMinimumSize(300, 50)
        self.localrecord_txt.move(200, 550)

        self.pedals_background = QLabel(self.driver_info_tab)
        self.pedals_background.setPixmap(self.pedals_image)
        self.pedals_background.setScaledContents(True)
        self.pedals_background.setFixedSize(100, 110)
        self.pedals_background.move(pedal_x - 10, base_y)
        self.pedals_background.lower()

        self.clutch_bar = QProgressBar(self.pedals_background)
        self.brake_bar = QProgressBar(self.pedals_background)
        self.throttle_bar = QProgressBar(self.pedals_background)

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

        self.lap_label = QLabel(self.driver_info_tab)
        self.lap_label.setPixmap(self.lap_image)
        self.lap_label.setFixedSize(self.lap_image.size())
        self.lap_label.move(pedal_x + self.pedals_background.width() + 30, 25)

        self.lap_text = QLabel("0/0", self.lap_label)
        self.lap_text.setFont(QFont(self.font_family_digits, 42))
        self.lap_text.setStyleSheet("color: red; background: transparent;")
        self.lap_text.setAlignment(Qt.AlignCenter)
        self.lap_text.setGeometry(0, -15, self.lap_label.width(), self.lap_label.height())
        self.lap_text.raise_()

        self.laptime_label = QLabel(self.driver_info_tab)
        self.laptime_label.setPixmap(self.laptime_image)
        self.laptime_label.setFixedSize(self.laptime_image.size())
        self.laptime_label.move(self.lap_label.x(), self.lap_label.y() + self.lap_label.height() + 10)

        self.laptime_text = QLabel("0:00.00", self.laptime_label)
        self.laptime_text.setFont(QFont(self.font_family_digits, 42))
        self.laptime_text.setStyleSheet("color: red; background: transparent;")
        self.laptime_text.setAlignment(Qt.AlignLeft)
        self.laptime_text.setGeometry(35, 20, self.laptime_label.width(), self.laptime_label.height())
        self.laptime_text.raise_()

        self.bestlaptime_label = QLabel(self.driver_info_tab)
        self.bestlaptime_label.setPixmap(self.bestlaptime_image)
        self.bestlaptime_label.setFixedSize(self.bestlaptime_image.size())
        self.bestlaptime_label.move(self.laptime_label.x(), self.laptime_label.y() + self.laptime_label.height() + 10)

        self.bestlaptime_text = QLabel("0:00.00", self.bestlaptime_label)
        self.bestlaptime_text.setFont(QFont(self.font_family_digits, 42))
        self.bestlaptime_text.setStyleSheet("color: red; background: transparent;")
        self.bestlaptime_text.setAlignment(Qt.AlignCenter)
        self.bestlaptime_text.setGeometry(0, -5, self.bestlaptime_label.width(), self.bestlaptime_label.height())
        self.bestlaptime_text.raise_()

        self.pos_label = QLabel(self.driver_info_tab)
        self.pos_label.setPixmap(self.pos_image)
        self.pos_label.setFixedSize(self.pos_image.size())
        self.pos_label.move(self.bestlaptime_label.x() + 50, self.bestlaptime_label.y() + self.bestlaptime_label.height() + 10)

        self.pos_text = QLabel("0", self.pos_label)
        self.pos_text.setFont(QFont(self.font_family_digits, 62))
        self.pos_text.setStyleSheet("color: red; background: transparent;")
        self.pos_text.setAlignment(Qt.AlignCenter)
        self.pos_text.setGeometry(0, -15, self.pos_label.width(), self.pos_label.height())
        self.pos_text.raise_()

        self.wheel_label = QLabel(self.driver_info_tab)
        self.wheel_label.setPixmap(self.wheel_image)
        self.wheel_label.setFixedSize(self.wheel_image.size())
        self.wheel_label.move(pedal_x + 420, base_y)
        '''
        # Create the line series for API response times
        self.api_response_series = QLineSeries()
        self.api_response_series.setName("API Cache misses")

        # Create the chart and add the series
        self.api_chart = QChart()
        self.api_chart.addSeries(self.api_response_series)
        self.api_chart.setTitle("Gui Delay over Last 5 minutes")
        self.api_chart.setAnimationOptions(QChart.NoAnimation)

        # Create axes
        self.axis_x = QValueAxis()
        self.axis_x.setTitleText("Time (minutes ago)")
        self.axis_x.setRange(-5, 0)  # Show last 300 seconds
        self.axis_x.setLabelFormat("%d")
        self.axis_x.setTickCount(5)  # Major ticks every 10 seconds (-60, -50, ..., 0)
        self.api_chart.addAxis(self.axis_x, Qt.AlignBottom)
        self.api_response_series.attachAxis(self.axis_x)

        self.axis_y = QValueAxis()
        self.axis_y.setTitleText("GUI update Delay (seconds)")
        #self.axis_y.setRange(0, 500)  # Default range 0-500ms (adjust dynamically if needed)
        self.axis_y.setRange(0.0167, 0.0334)  # Default range 0-500ms (adjust dynamically if needed)
        self.axis_y.setLabelFormat("%.4f")
        self.axis_y.setTickCount(5)  # Major ticks every 100ms (0, 100, ..., 500)
        self.api_chart.addAxis(self.axis_y, Qt.AlignLeft)
        self.api_response_series.attachAxis(self.axis_y)

        # Create chart view and add to layout
        self.api_chart_view = QChartView(self.api_chart, self.driver_info_tab)
        self.api_chart_view.setRenderHint(QPainter.Antialiasing)
        self.api_chart_view.setFixedSize(1050, 300)
        self.api_chart_view.setMinimumHeight(200)  # Adjust height as needed
        self.api_chart_view.setStyleSheet("background: transparent;")  # Make the background transparent
        self.api_chart_view.setAttribute(Qt.WA_TranslucentBackground)
        self.api_chart_view.setContentsMargins(0, 0, 0, 0)  # Remove margins for better fit
        self.api_chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.api_chart_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable horizontal scrolling
        self.api_chart_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)  # Disable vertical scrolling
        self.api_chart_view.setStyleSheet("border: none;")  # Remove border for a cleaner look
        self.api_chart_view.move(25, 500)  # Position the chart below the speedometer and tachometer 

        # Add the chart view to the Driver Info tab layout
        # Assuming self.driver_info_layout is a QVBoxLayout or similar
        #self.driver_view_layout.addWidget(self.api_chart_view)

        # Initialize data storage for the graph
        self.api_response_data = []  # List of (time, response_time) tuples
        self.start_time = time.time()  # Reference time for X-axis
        '''

    def setup_result_view(self): # Content label for displaying loaded results
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_result_view entered")
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
        
        #Status Label
        self.results_message_label = QLabel(f"", self.results_view_widget)
        self.results_message_label.setStyleSheet("font-size: 14px;font-weight:bold; color: red;")
        self.results_view_layout.addWidget(self.results_message_label)
        self.results_view_layout.addStretch(1)

    def setup_final_view(self): # Content label for displaying Final results
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_final_view entered")
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

        self.final_message_label = QLabel("", self.final_view_widget)
        self.final_message_label.setStyleSheet("font-size: 14px;font-weight:bold; color: red;")
        self.final_view_layout.addWidget(self.final_message_label)
        self.final_view_layout.addStretch(1)

    def setup_highscore_view(self): # Content label for displaying Final results
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_higscore_view entered")
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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def setup_higscore_view entered")
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
    
    def update_api_response_graph(self, response_time_ms):
        #timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S,%f')[:-3]
        #self.response_time_log[timestamp] = response_time_ms
        current_time = time.time()
        # Periodically flush logs
        #self.flush_logs_periodically()
        #logging.info(f"Def update_api_response_graph entered with response_time_ms: {response_time_ms}")
        relative_time = current_time - self.start_time  # Time since start in seconds

        # Append new data point (relative_time, response_time_ms)
        self.api_response_data.append((relative_time, response_time_ms))

        # Remove data points older than 300 seconds
        cutoff_time = relative_time - 300
        self.api_response_data = [(t, rt) for t, rt in self.api_response_data if t >= cutoff_time]

        # Update the series
        self.api_response_series.clear()
        for t, rt in self.api_response_data:
            # X-axis is negative seconds ago (e.g., -60 to 0)
            x_value = -(relative_time - t) / 60
            self.api_response_series.append(x_value, rt)

        # Dynamically adjust Y-axis range if needed
        if self.api_response_data:
            max_response_time = max(rt for t, rt in self.api_response_data)
            if max_response_time > self.axis_y.max():
                # Round up to nearest 100ms
                new_max = ((int(max_response_time) // 100) + 1) * 100
                self.axis_y.setRange(0, max(new_max, 500))  # Ensure minimum range of 0-500ms
            elif max_response_time < self.axis_y.max() * 0.5 and self.axis_y.max() > 500:
                # Scale down if data is much smaller, but not below 500ms
                new_max = max(((int(max_response_time) // 100) + 1) * 100, 500)
                self.axis_y.setRange(0, new_max)

    def flush_logs_periodically(self):
        if time.time() - self.last_flush >= 60:  # Flush every 1 minutes
            self.write_logs_to_file(append=True)
            self.response_time_log.clear()
            self.last_flush = time.time()

    def write_logs_to_file(self, append=False):
        mode = 'a' if append else 'w'
        with open('response_time_log.txt', mode) as f:
            for timestamp, response_time in sorted(self.response_time_log.items()):
                f.write(f"{timestamp} - INFO - API response time: {response_time}ms\n")

    def write_logs_on_exit(self):
        self.write_logs_to_file(append=True)
    def update_driver_view(self, data):
        if self.tab_widget.currentWidget() != self.driver_info_tab or not data or 'participants' not in data or 'mParticipantInfo' not in data['participants']:
            return  # Early exit for inactive tab or invalid data
        if self.driver_view_first_update:
            eventnode = data['eventInformation']
            self.total_laps = eventnode['mLapsInEvent']
            trackworldrecord = data['timings']['mWorldFastestLapTime']
            trackname = f"{eventnode['mTranslatedTrackLocation']} - {eventnode['mTranslatedTrackVariation']}"
            self.worldrecord_txt.setText(self.format_lap_time(trackworldrecord) if trackworldrecord != -1 else "Mod Car/Track")
            self.localrecord_txt.setText(f"{self.format_lap_time(self.trackrecorddb)} - {self.recorddriver}" if self.trackrecorddb != 0 else "No Record")
            self.track_txt.setText(trackname)
            self.driver_view_first_update = False

        participants = data['participants']
        carnode = data['carState']
        timingsnode = data['timings']
        index = min(participants.get('mViewedParticipantIndex', 0), participants.get('mNumParticipants', 0) - 1)
        drvnode = participants['mParticipantInfo'][index]

        # Precompute values
        speed = int(carnode['mSpeed'] * 3.6)
        crashindex = carnode['mLastOpponentCollisionIndex']
        rpm = carnode['mRpm']
        mMaxRPM = carnode['mMaxRPM']
        bestlap = timingsnode['mBestLapTime']
        current_lap = drvnode['mCurrentLap']
        race_pos = drvnode['mRacePosition']
        drivername = drvnode['mName']
        carname = drvnode['mCarNames']
        laptime = self.format_lap_time(timingsnode['mCurrentTime'] if timingsnode['mCurrentTime'] != -1 else 0)
        gear = carnode['mGear']
        throttle = int(carnode.get('mThrottle', 0) * 100)
        brake = int(carnode.get('mBrake', 0) * 100)
        clutch = int(carnode.get('mClutch', 0) * 100)

        # Batch UI updates
        updates = [
            (self.driver_txt.setText, (drivername,)),
            (self.laptime_text.setText, (laptime,)),
            (self.car_txt.setText, (carname,)),
            (self.collison_txt.setText, (str(crashindex),)),
            (self.speed_display.setText, (str(speed),)),
            (self.gear_display.setText, ('N' if gear == 0 else str(gear),)),
            (self.pos_text.setText, (str(race_pos),)),
            (self.throttle_bar.setValue, (throttle,)),
            (self.brake_bar.setValue, (brake,)),
            (self.clutch_bar.setValue, (clutch,)),
            (self.lap_text.setText, (f"{current_lap}/{self.total_laps}" if self.total_laps > 0 else f"{current_lap}",)),
            (self.bestlaptime_text.setText, (self.format_lap_time(bestlap if bestlap != -1 else 0),))
        ]
        for setter, args in updates:
            setter(*args)

        # Optimize needle rotations with precomputed painter
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

        def rotate_steering_wheel(value):
            angle = value * 360  # Assuming value is in range [-1, 1]
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

        rotate_steering_wheel(data['unfilteredInput']['mUnfilteredSteering'])
        rotate_needle(speed, self.speedo_max, self.speed_needle_label, self.scaled_needle_image, *self.speedo_sweep)
        rotate_needle(rpm, self.tacho_max, self.tacho_needle_label, self.scaled_needle_image, *self.tacho_sweep)

    def update_driver_view_omr(self, data):
        if self.tab_widget.currentWidget() != self.driver_info_tab:
            return  # Skip updating driver view if not visible
        if not data or 'participants' not in data or 'mParticipantInfo' not in data['participants']:
            return
        if self.driver_view_first_update:
            #Event information
            self.driver_view_first_update = False  # Set to False after the first update
            eventnode = data['eventInformation'] # Get the root tag for event information
            self.total_laps = eventnode['mLapsInEvent']
            trackworldrecord = data['timings']['mWorldFastestLapTime']  # Track record time
            trackname = f"{eventnode['mTranslatedTrackLocation']} - {eventnode['mTranslatedTrackVariation']}"
            self.worldrecord_txt.setText(self.format_lap_time(trackworldrecord) if trackworldrecord != -1 else "Mod Car/Track")
            self.localrecord_txt.setText(self.format_lap_time(self.trackrecorddb))              
            self.track_txt.setText(trackname)
        # Get the relevant nodes from the data
        #playernode = data['participants'] # Get the root tag for participant info
        #index = data['participants'].get('mViewedParticipantIndex', -1)
        playernode = data['participants']['mParticipantInfo']  # Get the root tag for participant info
        carnode = data['carState']  # Get the root tag for car state
        timingsnode = data['timings'] # Get the root tag for timings
        drvnode = playernode[data['participants'].get('mViewedParticipantIndex', -1)] # Get the viewed driver top node

        #Car information
        speed= int(carnode['mSpeed'] * 3.6)  # Convert speed from m/s to km/h
        crashindex = carnode['mLastOpponentCollisionIndex']  # Collision player index, -1 if no collision
        rpm = carnode['mRpm']  # Engine RPM
        mMaxRPM = carnode['mMaxRPM']  # Maximum RPM of the car
        #Timings information
        bestlap = timingsnode['mBestLapTime']

        # Driver information
        current_lap = drvnode['mCurrentLap']
        Race_positing = drvnode['mRacePosition']
        drivername = drvnode['mName']
        carname = drvnode['mCarNames']
        self.driver_txt.setText(drivername)
        self.laptime_text.setText(self.format_lap_time(timingsnode['mCurrentTime'] if timingsnode['mCurrentTime'] != -1 else 0))
        self.car_txt.setText(carname)
        #self.collison_txt.setText(playernode[crashindex]['mName'] if crashindex != -1 else "No Crash")
        self.collison_txt.setText(str(crashindex))

        gear = data['carState']['mGear']  # 0 = neutral

        self.speed_display.setText(str(speed))
        self.gear_display.setText('N' if gear == 0 else str(gear))
        self.pos_text.setText(str(Race_positing))

        throttle = int(carnode.get('mThrottle', 0) * 100)
        brake    = int(carnode.get('mBrake', 0) * 100)
        clutch   = int(carnode.get('mClutch', 0) * 100)

        self.throttle_bar.setValue(throttle)
        self.brake_bar.setValue(brake)
        self.clutch_bar.setValue(clutch)
        self.lap_text.setText(f"{current_lap}/{self.total_laps}" if self.total_laps > 0 else f"{current_lap}")
        self.bestlaptime_text.setText(self.format_lap_time(bestlap if bestlap != -1 else 0))
 
        def rotate_needle(value, max_value, label, needle_pixmap, start_angle=-135, end_angle=135):
            """
            Rotates the needle image from start_angle to end_angle based on value/max_value.

            :param value: The current value to map.
            :param max_value: The maximum scale value of the gauge.
            :param label: The QLabel showing the needle.
            :param needle_pixmap: The original (or scaled) QPixmap of the needle.
            :param start_angle: The angle (in degrees) where the needle starts (default -135).
            :param end_angle: The angle (in degrees) where the needle ends (default 135).
            """
            # Clamp value to avoid out-of-range rotation
            value = max(0, min(value, max_value))
            sweep = end_angle - start_angle
            angle = (value / max_value) * sweep + start_angle

            size = needle_pixmap.size()
            canvas = QPixmap(size)
            canvas.fill(Qt.transparent)

            painter = QPainter(canvas)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)

            center = needle_pixmap.rect().center()
            painter.translate(center.x(), center.y())
            painter.rotate(angle)
            painter.translate(-center.x(), -center.y())
            painter.drawPixmap(0, 0, needle_pixmap)
            painter.end()

            label.setPixmap(canvas)
            # print(f"RMA Line {inspect.currentframe().f_lineno} Needle rotated to {angle} degrees for value {value}/{max_value}")
        def rotate_steering_wheel(value):
            """
            Rotates the steering wheel QLabel based on mUnfilteredSteering input.
            :param value: Float in range [-1.0, 1.0] from the API
            """
            #max_angle = 270  # Full rotation range, adjust as needed
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

        rotate_steering_wheel(data['unfilteredInput']['mUnfilteredSteering'])  # Use carState for steering input
        
        # Speedo: 270° sweep from -135° to +135°
        rotate_needle(speed, self.speedo_max, self.speed_needle_label,
              self.scaled_needle_image, *self.speedo_sweep)
        # Tacho: 300° sweep from -150° to +150°
        rotate_needle(rpm, self.tacho_max, self.tacho_needle_label,
              self.scaled_needle_image, *self.tacho_sweep)
       
    def on_first_live_view_run(self, data):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def on_first_live_view_run entered")
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
        self.driver_sim = {}
        selected_track = f"{self.event_info['mTranslatedTrackVariation']} - {self.event_info['mTranslatedTrackLocation']}"
        selected_car = participants[0]['mCarNames']
        heading_text = f"{self.session_type} - {self.event_info['mTranslatedTrackLocation']} - {self.event_info['mTranslatedTrackVariation']} ({'Qualify' if sessionstate == 3 else 'Practice' if sessionstate == 1 else self.event_info['mLapsInEvent']}) - {participants[0]['mCarNames']} - {len(participants)} Drivers - Session ID: {self.session_id}" # Create the heading text
        self.live_heading.setText(heading_text)
        if sessionstate == 3: self.live_status_label.setText("Qualifying in progress ...")
        elif sessionstate == 1: self.live_status_label.setText("Practice in progress ...")
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
        self.driver_sim = {}
        print(f"RMA Line {inspect.currentframe().f_lineno} on first live view run. Emitting self.session ID {self.session_id}")
        self.session_id_updated.emit(self.session_id)
        self.db_queue.put(('load_highscores', (selected_car, selected_track)))

        for i in range(20): self.participant_labels[i].hide()  # Hide labels initially  # Assuming 20 participants max
        # Find out which sim the particpant is using and write the it after the name
        # Check participants in file drivers.txt, and match participant['mName'] with the name in the file.
        # This will help to identify which sim the participant is using.
        # Sim is the names position in the file.
        self.get_request_for_sim_signal.emit()  # Emit the signal to get the driver sim data
        self.sector_times = {}
        self.last_sector = {}
        self.driver_finished = {}
        self.leader_name = None
        self.leader_total_time = 0.0
        self.leader_current_lap = 0
        self.leader_progress = 0.0
        
    def update_live_view(self, data):
        if self.live_first_time_run:
            self.on_first_live_view_run(data)

        participants = data['participants'].get('mParticipantInfo', None)
        if not participants:
            return

        sorted_participants = sorted(
            participants[:data['participants']['mNumParticipants']],
            key=lambda p: (float('inf') if self.driver_flags.get(p['mName']) == 'Falsestart' else p['mRacePosition'])
        )
        #print(f"RMA Line {inspect.currentframe().f_lineno} Def update_live_view entered with {sorted_participants} participants")
        sessionstate = data['gameStates']['mSessionState']
        leader = sorted_participants[0]
        self.leader_name = leader['mName']
        self.leader_current_lap = leader['mCurrentLap']
        self.leader_progress = leader.get('mCurrentLapDistance', 0.0)

        if not hasattr(self, 'previous_best_lap_time') or self.live_first_time_run:
            self.previous_best_lap_time = self.best_lap_time - 1
        for i, participant in enumerate(sorted_participants):
            name = participant['mName']
            if participant['mLastLapTimes'] != -123 and name in self.previous_current_lap:
                if self.current_lap[name] != self.previous_current_lap.get(name):
                    self.live_status_label.setText(f"{name} is now on lap {self.current_lap[name]}")
                    self.lap_time[name] = participant['mLastLapTimes']
                    self.lap_list.setdefault(name, []).append(self.format_lap_time(self.lap_time[name]))
                    self.previous_current_lap[name] = self.current_lap[name]
            else:
                self.previous_current_lap[name] = 1        

            if self.driver_finished.get(name, False):
                #print(f"RMA Line {inspect.currentframe().f_lineno} Driver {name} is finished or not in participant, skipping update. self.driver_finished: {self.driver_finished.get(name, False)}")
                continue
            sector_index = participant['mCurrentSector']
            self.current_lap[name] = participant['mCurrentLap']
            s1 = participant['mCurrentSector1Times']
            s2 = participant['mCurrentSector2Times']
            s3 = participant['mCurrentSector3Times']
            if not self.driver_finished.get(name, False):
                if s1 == -1 and s3 != -1: #Race is over 
                    total_time_driver = sum(float(t.split(':')[0]) * 60 + float(t.split(':')[1]) for t in self.lap_list.get(name, []))
                    self.total_time_seconds[name] = total_time_driver
                    self.driver_finished[name] = True   # Skip timing from now on.
                    continue  # Skip further processing for this driver
                else:
                    current_lap_time = 0.0
                    if self.current_lap[name] == 1 and s1 == -1:
                        current_lap_time = 0.0  # No valid sector times yet
                    else:
                        if sector_index == 0:
                            current_lap_time = s1
                        elif sector_index == 1:
                            current_lap_time = s1 + s2
                        elif sector_index == 2:
                            current_lap_time = s1 + s2 + s3
                total_time_driver = current_lap_time + sum(float(t.split(':')[0]) * 60 + float(t.split(':')[1]) for t in self.lap_list.get(name, []))
                #print(f"lap list: {self.lap_list}")
                #print(f"RMA Line {inspect.currentframe().f_lineno} Driver {name} current lap: {self.current_lap[name]}, sector index: {sector_index}, s1: {s1}, s2: {s2}, s3: {s3}, total_time_driver: {total_time_driver}")
                self.total_time_seconds[name] = total_time_driver
                if participant['mRacePosition'] == 1:
                    self.leader_name = name
                    self.leader_current_lap = self.current_lap[name]
                    self.leader_total_time = total_time_driver
                    self.leader_participant = participant
                    self.leader_progress = participant.get('mCurrentLapDistance', 0.0)



        if self.best_lap_time < self.previous_best_lap_time or self.live_first_time_run:
            for j in range(min(20, len(sorted_participants))):
                label = self.participant_labels[j]
                p = sorted_participants[j]
                bg_color = self.top_background_color if p['mFastestLapTimes'] <= self.best_lap_time and p['mCurrentLap'] > 1 else self.background_color
                label.setStyleSheet(f"font-size: 14px; background-color: {bg_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
            self.previous_best_lap_time = self.best_lap_time            
        if self.tab_widget.currentWidget() != self.live_view_widget and not self.live_first_time_run:
            #print(f"RMA Line {inspect.currentframe().f_lineno} Live View tab not active, skipping GUI updates{self.tab_widget.currentWidget()}===:=== {self.live_view_widget}. self.first_time_run: {self.live_first_time_run}")
            return  # Skip GUI updates if Live View tab is not active
        else:
            for i, participant in enumerate(sorted_participants):
                name = participant['mName']
                label = self.participant_labels[i] if i < 20 else None
                if label:
                    total_time_str = self.format_lap_time(self.total_time_seconds.get(name, 0))
                    last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
                    lap_times_str = ", ".join(self.lap_list.get(name, ["No Valid Lap!"]))

                    gap_str, gap_distance_str = self.get_gap_to_leader(participant)
                    gap_to_ahead_str, gap_to_ahead_distance_str = self.get_gap_to_ahead(participant, sorted_participants)

                    participant_text = self.create_participant_text(
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
                    label.setText(participant_text)
                    if self.live_first_time_run:
                        label.show()
                    label.setText(participant_text)

        #leader = participants[0]
        race_state = data['gameStates']['mRaceState']
        if race_state == 2 and not self.race_started:
            self.live_status_label.setText("Green Light! GO GO GO")
            self.race_started = True
        elif race_state == 3 or race_state == 6:
            self.live_status_label.setText("Race Ending....")
        self.live_first_time_run = False
        
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

        # Debug info (optional)
        #print(f"DEBUG [{participant['mName']}]: lap={lap}, progress={progress:.2f}, "
        #f"gap_dist={gap_dist:.2f}, speed={speed if self.leader_current_lap < 1 else leader_speed:.2f}, "
        #f"gap_time={gap_time:.2f}"
        #f" Participant Speed: {participant['mSpeeds']:.2f} m/s, Leader Speed: {leader_speed:.2f} m/s"
        #f" self.leader_current_lap={self.leader_current_lap}, ")
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
                            
        #print(f"RMA Line {inspect.currentframe().f_lineno} Def create_participant_text entered with participant: {participant['mName']}")
        name = participant['mName']
        if self.top_speed.get(name, -1000) < math.floor(participant['mSpeeds']):
            self.top_speed[name] = math.floor(participant['mSpeeds'])

        sim = self.driver_sims.get(name, "")
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

        if math.floor(participant['mSpeeds']) > self.best_top_speed:
            self.best_top_speed = math.floor(participant['mSpeeds'])
            self.top_speed_driver = name
            updated = True

        if participant['mFastestLapTimes'] < self.best_lap_time and participant['mCurrentLap'] > 1 and participant['mFastestLapTimes'] != -123:
            self.best_lap_time = participant['mFastestLapTimes']
            self.best_lap_driver = name
            self.live_status_label.setText(
                f"{name} just got a new best lap time{' (Qualify)' if sessionstate == 3 else ' (Practice)' if sessionstate == 1 else ''}: {self.format_lap_time(self.best_lap_time)}"
            )
            updated = True

        if updated:
            self.live_best_label.setText(
                f"Top Speed: {self.top_speed_driver} {self.best_top_speed * 3.6:.0f} Km/t "
                f" Best Lap: {self.best_lap_driver} {self.format_lap_time(self.best_lap_time)}"
            )

    def handle_pit_stop(self, participant):
        name = participant['mName']
        if name not in self.pit_stop:
            self.pit_stop[name] = {}

        if participant['mPitModes'] == 2 and participant['mCurrentLap'] not in self.pit_stop[name]:
            self.pit_stop[name][participant['mCurrentLap']] = 1
            self.pit_stops_updated.emit(self.pit_stop)
            self.live_status_label.setText(f"{name} entered PIT")
            logging.info(f"Pit Stop added for {name} at lap {participant['mCurrentLap']}")

        return sum(self.pit_stop[name].values())

    def format_lap_times_list(self, lap_times_str):
        laps = lap_times_str.split(", ")
        return ", ".join(laps[-16:]) if len(laps) > 17 else lap_times_str

    def display_final_results(self, race_valid, session_id): # Display the score data in the final view
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def display_final_results entered")
        self.live_status_label.setText("Waiting for a new race to start...")  # Update the status label"
        self.racestarted =False
        self.final_message_label.setText("") # Clear any existing error message if the connection is successful
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop() 
        self.live_first_time_run =True
        if race_valid:
            if session_id > self.latest_session_id:
                print(f"RMA Line {inspect.currentframe().f_lineno} Display Final Result. Self.latest_session_id: {self.latest_session_id} wil be updated to: {session_id}")
                self.latest_session_id = session_id
                # self.initialize_dropdown()
            self.db_queue.put(('load_score_data',(session_id,))) # Get data I need to calculate score (New Session ID button must not be pushed before this))
    
    def qualify_finished(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def qualify_finished entered")
        self.live_status_label.setText("Qualifying Finished! Waiting for Race to start...")  # Update the status label"
        self.racestarted = False
        self.live_first_time_run = True
    
    def practice_finished(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def practice_finished entered")
        self.live_status_label.setText("Practice Finished! Waiting for Qualifying to start...")  # Update the status label"
        self.racestarted = False
        self.live_first_time_run = True

    def display_score(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Display Score Result def entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Display score Result def entered")
        self.selected_index = self.dropdown_sessionid.currentIndex()
        sessionid_text = self.dropdown_sessionid.itemText(self.selected_index)
        self.session_id_dropdown = int(re.search(r'\d+', self.dropdown_sessionid.itemText(self.selected_index)).group()) if re.search(r'\d+', self.dropdown_sessionid.itemText(self.selected_index)) else 0
        print(f"RMA Line {inspect.currentframe().f_lineno} Selected Index: {self.selected_index} RMA Selected session text: {sessionid_text} Extracted session_ID: {self.session_id_dropdown}")
        self.final_message_label.setText("") # Clear any existing error message if the connection is successful
        if hasattr(self, 'timer') and self.timer.isActive(): self.timer.stop()
        if 0 < self.session_id_dropdown <= self.latest_session_id: # Check if the session ID is valid and greater than the latest session ID
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Get score Data. Session ID: {self.session_id_dropdown}")
            print(f"RMA Line {inspect.currentframe().f_lineno} Get score Data. Session ID: {self.session_id_dropdown}")
            self.db_queue.put(('load_score_data',(self.session_id_dropdown,))) #Get data I need to calculate score (New Session ID button must not be pushed before this))
        else:
            self.final_message_label.setText(f"No valid session ID selected")
            self.session_id_dropdown = None         
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA No valid session ID selected")
            print(f"RMA Line {inspect.currentframe().f_lineno} No valid session ID selected.")
        if "Session ID -" not in sessionid_text: # Check if the session ID contains a '-'
            print(f"RMA Line {inspect.currentframe().f_lineno} Manually typed ID. Index will be removed from the dropdown list")
            if self.dropdown_sessionid.currentIndex() != 0:
                self.dropdown_sessionid.removeItem(self.selected_index) # Remove the manually typed ID from the dropdown
        self.dropdown_sessionid.setCurrentIndex(0)
        # logging.info(f"Line {inspect.currentframe().f_lineno} RMA Accumulated Score for Session {self.session_id_dropdown}")
        
    def calculate_score(self, races, participants, laps):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def calculate_score entered")
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
                    print(f"RMA Line {inspect.currentframe().f_lineno} No participants found for race {race_id}. Skipping score calculation for this race.")
                    logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA No participants found for race {race_id}. Skipping score calculation for this race.")
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
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Ranked drivers: {self.ranked_drivers}")
        else:
            # elif self.session_id == 1:
            print(f"RMA Line {inspect.currentframe().f_lineno} Races is empty, but self.latest_session_id is not None: {self.latest_session_id}")
            self.session_id = 1
            print(f"RMA Line {inspect.currentframe().f_lineno} Caclulate Score. Races is empty: Races: {races}. Session ID set to 1. Emitting self.session ID: {self.session_id}")
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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def format_score_view entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Def format_score_view entered")
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
        print(f"RMA Line {inspect.currentframe().f_lineno} Self session id dropdown: {self.session_id_dropdown}")
        print(f"RMA Line {inspect.currentframe().f_lineno} Self session id: {self.session_id}")
        print(f"RMA Line {inspect.currentframe().f_lineno} Latest session ID: {self.latest_session_id}")
        heading = (
            f"<span style='color:{self.color_labels}'>Session:</span>"
            f"<span style='color:{self.color_values}'> "
            f"{self.session_id_dropdown if self.session_id_dropdown is not None else (self.latest_session_id if self.session_id - 1 == self.latest_session_id else self.session_id)}</span> "
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
            #print(f"RMA Line {inspect.currentframe().f_lineno} Participant: {mName} - Score: {score} - Last Position: {last_pos} - Gold: {gold} - Silver: {silver} - Bronze: {bronze}")

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
        self.session_id_dropdown = None 

    def delete_selected_race(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Delete selected race def entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Delete selected race def entered")
        # selected_index = self.dropdown_races.currentIndex()
        if self.selected_race_id > 0:

            def on_race_deleted(race_id):
                print(f"RMA Line {inspect.currentframe().f_lineno} Should only see this once")
                logging.info(f"RMA Line {inspect.currentframe().f_lineno} Should only see this once")
                if race_id is not None:
                    self.initialize_dropdown()
                else:
                    print(f"RMA Line {inspect.currentframe().f_lineno} on_race_deleted:Race_id is None:{race_id}")
                    logging.info(f"RMA Line {inspect.currentframe().f_lineno} on_race_deleted:Race_id is None:{race_id}")
 
            self.set_delete_mode(True)  # Activates delete mode
            self.db_queue.put(('delete_race', (self.selected_race_id, on_race_deleted))) #Send request to DatabaseThread
            QTimer.singleShot(1000,lambda: self.set_delete_mode(False))
            QTimer.singleShot(1000, self.after_timer_race_deleted)
        else:
            print(f"RMA Line {inspect.currentframe().f_lineno} NO valid race selected.")

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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Delete selected driver def entered")
        selected_index = self.driver_dropdown.currentIndex()
        if selected_index > 0:
            driver_text = self.driver_dropdown.itemText(selected_index)

            def on_driver_deleted(driver_text):
                print(f"RMA Line {inspect.currentframe().f_lineno} Should only see this once")
                logging.info("RMA Should only see this once")
                if driver_text is not None:
                    self.initialize_dropdown()
                else:
                    print(f"RMA Line {inspect.currentframe().f_lineno} on_driver_deleted:Driver_text is None:{driver_text}")
                    logging.info(f"RMA Line {inspect.currentframe().f_lineno} on_driver_deleted:Driver_text is None:{driver_text}")

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
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def set_delete_mode entered")
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

    def handle_latest_session_id(self, session_id, dato):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def handle_latest_session_id entered")
        if session_id is not None:
            self.latest_session_id = session_id
        else:
            self.latest_session_id = 1
        print(f"RMA Line {inspect.currentframe().f_lineno} Latest Session ID: {self.latest_session_id}")
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Latest Session ID: {self.latest_session_id}")

    def start_new_session(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RMA Start New Session entered")
        # self.display_score()
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def start_new_session entered")

        # Create an event loop to wait for the callback
        loop = QEventLoop()

            # Define a wrapper for the callback to stop the event loop
        def handle_latest_session_id_wrapper(session_id, dato):
            self.handle_latest_session_id(session_id, dato)
            loop.quit()  # Quit the event loop once the callback is executed

        # Enqueue the operation with the wrapped callback
        print(f"RMA Line {inspect.currentframe().f_lineno} Get latest session ID from DB. Line 3074 {inspect.currentframe().f_lineno}")
        self.db_queue.put(('get_latest_session_id', (handle_latest_session_id_wrapper,)))

        # Start the event loop and wait for the callback to complete
        loop.exec_()

        self.session_id += 1
        if self.session_id - self.latest_session_id > 1:
            self.session_id = self.latest_session_id + 1
            print(f"RMA Line {inspect.currentframe().f_lineno} Max session is {self.session_id} rest of def will not be executed")  # Rest will not be executed.
        else:
            print(f"RMA Line {inspect.currentframe().f_lineno} Sending session: {self.session_id} to load_score_data")
            logging.info(f"RMA Line {inspect.currentframe().f_lineno} Sending session: {self.session_id} to load_score_data")
            self.db_queue.put(('load_score_data', (self.session_id if self.latest_session_id == self.session_id else self.session_id - 1,)))  # Get the score data for the current session ID

        # These lines are common and executed regardless of the condition
        print(f"RMA Line {inspect.currentframe().f_lineno} Start New session.  Emitting self.session ID {self.session_id}")
        self.session_id_updated.emit(self.session_id)
        self.live_heading.setText(f"Waiting for Race Start. Current Session: {self.session_id}")  # Update the status label 
        
    def previous_session(self):
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} Def go back session entered")
        print(f"RMA Line {inspect.currentframe().f_lineno} Self selected index: {self.session_id}")
        print(f"RMA Line {inspect.currentframe().f_lineno} Session_id_dropdown: {self.session_id_dropdown}")
        self.session_id -= 1
        if self.session_id <1: self.session_id = 1
        self.selected_index = self.session_id
        self.db_queue.put(('load_score_data',(self.session_id,))) # Get the score data for the current session ID
        self.live_heading.setText(f"Waiting for Race Start. Current Session: {self.session_id}")  # Update the status label  
        #self.final_heading.setText(f"Accumulated Score for Session {self.session_id_dropdown} Next Race will be session: {self.session_id}")

        print(f"RMA Line {inspect.currentframe().f_lineno} previous_session. Emitting Self.session ID: {self.session_id}")
        self.session_id_updated.emit(self.session_id)

    def closeEvent(self, event):
        self.stop()
        event.accept()
        
    def stop(self):
        print(f"RMA Line {inspect.currentframe().f_lineno} Closing the application...")
        app.quit() # Quit the application immediately.
        if hasattr(self, 'db_thread') and self.db_thread.isRunning(): # Stop the database thread if it exists and is running
            logging.info("Stopping DatabaseThread...")
            self.db_thread.stop()
            self.db_thread.wait()  # Wait for the thread to finish
            print(f"RMA Line {inspect.currentframe().f_lineno} Database thread stopped.")
        logging.info("Stopping MonitorThread...")
        print(f"RMA Line {inspect.currentframe().f_lineno} Stopping MonitorThread...")
        if hasattr(self, 'monitor_thread'):
            try:
                self.monitor_thread.data_updated.disconnect()
                self.monitor_thread.race_finished.disconnect()
            except TypeError:
                pass  # Signals might already be disconnected or not connected
        if hasattr(self, 'monitor_thread') and self.monitor_thread.isRunning(): # Stop the monitor thread if it exists and is running
                self.monitor_thread.running = False
                print(f"RMA Line {inspect.currentframe().f_lineno} Running self monitor thread stop")
                self.monitor_thread.wait()  # Wait for the thread to finish
                print(f"RMA Line {inspect.currentframe().f_lineno} Monitor thread stopped.")
                pass  # Signals might already be disconnected or not connected
        logging.info(f"RMA Line {inspect.currentframe().f_lineno} RaceMonitorApp stopped successfully.") # Log completion of stopping sequence

def main():
    global app
    app = QApplication(sys.argv)
    ex = RaceMonitorApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address