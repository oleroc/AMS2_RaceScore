from re import L, T; from timeit import Timer; import sys, re, inspect, requests, sqlite3, queue, json, time, traceback, logging, os, asyncio, aiohttp, math, base64, configparser, tempfile
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QSizePolicy, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QTabWidget, QSpacerItem, QMessageBox, QLineEdit, QCalendarWidget
from PyQt5.QtGui import QPixmap, QIcon, QFontDatabase, QTransform
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer, QObject, QEvent, QEventLoop, QDate
from datetime import datetime
from file_base64_strings import (Driver_Statistics_Background_img_base64, High_scores_Background_img_base64, Race_results_Background_img_base64, Race_scores_Background_img_base64, liverace_liveview_img_base64, liverace_status_img_base64, icon_base64, sui_generis_rg_font_base64, lap_bg_base64, pos_bg_base64, laptime_bg_base64, speedometer_bg_base64, tachometer_bg_base64, needle_bg_base64)
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
            logging.info("DB Lap data written")

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
        if best_driver: # Write ...(truncated 98220 characters)...lts_flags.setAlignment(Qt.AlignLeft | Qt.AlignTop)
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
        

        self.driver_statistics_laptime = QLabel("L