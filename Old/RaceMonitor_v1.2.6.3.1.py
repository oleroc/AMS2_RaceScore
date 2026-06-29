from re import S
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
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, QMetaObject, Qt, Q_ARG, QTimer, QObject
from datetime import datetime

# Set up logging
if os.path.exists('debug.log'):
    os.remove('debug.log')

logging.basicConfig(filename='debug.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
class DatabaseThread(threading.Thread):

    def __init__(self, db_queue):
        super().__init__()
        #QObject.__init__(self)  # Initialize QObject
        #threading.Thread.__init__(self)  # Initialize threading.Thread
        #self.conn = sqlite3.connect('RaceDB.db')
        #self.cursor = self.conn.cursor()
        self.session_id_queue = queue.Queue()
        self.db_queue = db_queue
        self.running = True

    def run(self):
        self.conn = sqlite3.connect('RaceDB.db')
        self.cursor = self.conn.cursor()
        logging.info(f"Create DB Thread ID in operation: {threading.get_ident()}")
        #print(f"Create DB Thread ID in operation: {threading.get_ident()}")
        while self.running:
            try:
                operation, args = self.db_queue.get()
                if operation == 'stop':
                    break
                if operation == 'write_race':
                    self.write_race(*args)
                elif operation == 'insert_lap_data':
                    self.insert_lap_data(*args)
                elif operation == 'finalize_race':
                    self.finalize_race(*args)
                elif operation == 'delete_race':
                    self.delete_race(*args)
                elif operation == 'get_race_id':
                    self.get_race_id(*args)
                elif operation == 'initialize_session_id':
                    session_id = self.initialize_session_id(*args)
                    self.session_id_queue.put(session_id)
                elif operation == 'update_race_index':
                    self.update_race_index(*args)
                elif operation == 'load_selected_race':
                    self.load_selected_race(*args)
                elif operation == 'load_race_data_on_start':
                    self.load_race_data_on_start(*args)
                elif operation == 'fetch_recorded_laps':
                    self.fetch_recorded_laps(*args)
                elif operation == 'get_race_id_and_delete':
                    self.get_race_id_and_delete(*args)                    
          
                # Add more operations as needed
            except Exception as e:
                logging.error(f"Database operation failed: {e}")
                print(f"Database operation failed: {e}")
            finally:
                self.db_queue.task_done()
        # Close the connection when the thread stops
        self.conn.close()
 
    def get_race_id_and_delete(self, race_index, callback):
        try:
            self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
            race = self.cursor.fetchone()
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
                


    def fetch_recorded_laps(self, participant_name, race_id, current_lap, callback=None):
        try:
            # Perform the database operation to fetch recorded laps
            self.cursor.execute('SELECT LapNumber, LapTime FROM Laps WHERE RaceID = ? AND ParticipantName = ?',
                                (race_id, participant_name))
            recorded_laps = self.cursor.fetchall()

            # Emit the signal with the fetched data
            self.signals.laps_fetched_signal.emit(participant_name, recorded_laps, current_lap)

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback:
                callback(participant_name, [], current_lap)  # Pass empty data on error

    def load_race_data_on_start(self, callback=None):
        try:
            self.cursor.execute('''
                SELECT RaceID, RaceIndex, mTranslatedTrackVariation, mLapsInEvent, RaceDate
                FROM Races
                ORDER BY RaceID ASC
            ''')
            races = self.cursor.fetchall()

            # Emit the signal with the results in the main thread
            if callback:
                callback.emit(races)

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            if callback:
                callback.emit([])  # Emit an empty list in case of error
            
    def load_selected_race(self, race_index, callback):
        try:
            self.cursor.execute('''
                SELECT RaceID, mTranslatedTrackVariation, mLapsInEvent
                FROM Races
                WHERE RaceIndex = ?
            ''', (race_index,))
            race = self.cursor.fetchone()
            
            if race:
                race_id, track_variation, laps_in_event = race
                self.cursor.execute('''
                    SELECT mName, mRacePosition, mFastestLapTimes, mLastLapTimes, mCarNames
                    FROM Participants
                    WHERE RaceID = ?
                    ORDER BY mRacePosition ASC
                ''', (race_id,))
                participants = self.cursor.fetchall()
                
                # Call the callback with the fetched data
                if callback:
                    callback(race_id, track_variation, laps_in_event, participants)

        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            print(f"Load Selected Races failed: {e}")
            if callback:
                callback(None)

    def update_race_index(self, callback=None):
        try:
            self.cursor.execute('SELECT RaceIndex FROM Races ORDER BY RaceID DESC LIMIT 1')
            last_race_index = self.cursor.fetchone()

            # Process the result and call the callback with the new race count
            if callback:
                if last_race_index:
                    last_race_number = int(last_race_index[0].split('_')[1])
                    callback(last_race_number + 1)
                else:
                    callback(1)  # Start with 1 if there are no races
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            callback(1)  # Emit 1 as a fallback if there's an error
                
    def initialize_session_id(self):
        self.cursor.execute('SELECT MAX(SessionID) FROM Races')
        result = self.cursor.fetchone()
        return result[0] + 1 if result[0] else 1
    
    def get_race_id(self, race_index, callback = None):
        try:
            self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
            race_id = self.cursor.fetchone()[0]
            if callback:
              callback(race_id)  # Pass the deleted race_id back to the main thread
            #if self.worker:
                #self.worker.race_id_fetched.emit(race_id)  # Emit the signal through the worker
        except Exception as e:
            logging.error(f"Database operation failed: {e}")
            #if self.worker:
             #   self.worker.race_id_fetched.emit(None)

    def write_race(self, race_index, data, session_id):
        try:
            # Replace the incorrect SQL statement with the correct one
            self.cursor.execute('''
                INSERT OR IGNORE INTO Races (RaceIndex, mTranslatedTrackVariation, mLapsInEvent, SessionID)
                VALUES (?, ?, ?, ?)
            ''', (race_index, data['eventInformation']['mTranslatedTrackVariation'], data['eventInformation']['mLapsInEvent'], session_id))         

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

    def finalize_race(self, data, race_index, race_count, lap_times_dict):
        participants = data['participants']['mParticipantInfo']
        self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
        race_id = self.cursor.fetchone()[0]

        for participant in participants:
            participant_name = participant['mName']
            if participant['mFastestLapTimes'] == -123.0:
                participant['mFastestLapTimes'] = None
            if participant['mLastLapTimes'] == -123.0:
                participant['mLastLapTimes'] = None

            self.cursor.execute('''
                INSERT OR REPLACE INTO Participants (
                    RaceID, mName, mCarNames, mRacePosition, mFastestLapTimes, mLastLapTimes
                )
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                race_id,
                participant_name,
                participant['mCarNames'],
                participant['mRacePosition'],
                participant['mFastestLapTimes'],
                participant['mLastLapTimes']
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
        self.join()  # Wait for the thread to finish before returning
        
class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal(dict)
    race_id_updated = pyqtSignal(int)  # Signal to update the RaceID
    error_occurred = pyqtSignal(str)   # New signal for errors
    connection_restored = pyqtSignal(int)  # Signal with mGameState as parameter
    race_count_updated = pyqtSignal(int)  # Signal to update race_count
    
    def __init__(self, tab_widget ,db_queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_queue = db_queue
        self.session_id_queue = queue.Queue()
        self.db_queue.put(('initialize_session_id', ()))
        self.ip_address = self.read_ip_address()
        self.tab_widget = tab_widget  # Store the reference to tab_widget
        self.previous_race_state = None
        self.running = True
        self.first_time_run = True
        self.session = requests.Session()       
        self.race_count_updated.connect(self.set_race_count) # Connect the signal to a slot that updates race_count


        
        # Adjusting race_count based on existing data in the database
        Previous_ipaddress = "127.0.0.1"
        # Get the latest RaceID and corresponding RaceIndex
        logging.info(f"Thread ID in operation: {threading.get_ident()}")
        #print(f"Monitor init Thread ID in operation: {threading.get_ident()}")
        self.db_queue.put(('update_race_index', (self.handle_race_index,)))
        
        self.current_race_id = None
        self.viewing_race_id = None  # New variable for viewing historical data
        self.lap_times_dict = {}  # Dictionary to track lap times for each participant

       
    def handle_race_index(self, new_race_count):
        self.race_count_updated.emit(new_race_count)
       
    def set_race_count(self, new_race_count):
        self.race_count = new_race_count
        print(f"Race count updated to {self.race_count}")    
        
    def read_ip_address(self):
        config_file = 'config.ini'
        config = configparser.ConfigParser()

        # Check if the config file exists
        if not os.path.exists(config_file):
            # Create a new config file with default settings
            config['config'] = {
                'ip_address': '127.0.0.1'
            }

            with open(config_file, 'w') as configfile:
                config.write(configfile)

            print(f"Config file created with default settings at {config_file}.")
        else:
            # Read the existing config file
            config.read(config_file)
            #print(f"Config file read.")
        return config['config']['ip_address']     
        

        #logging.info(f"Lap {current_lap} for {participant_name} recorded with time {lap_time}")
    def run(self):
        while self.running:
            try:
                Previous_ipaddress=self.ip_address
                #logging.info("Attempting to get data from the API.")
                self.ip_address = self.read_ip_address()  # Read IP address before each API call
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
                    print("No participants found, waiting for race start.")
                    time.sleep(10) # Wait for some time before retrying
                    continue  # Restart loop if participants list is empty
                
                # Proceed with processing the valid data                
                data = response.json()
                # Store the latest data         
                #logging.info(f"Full API response: {json.dumps(data, indent=2)}")
                if Previous_ipaddress != self.ip_address:
                    print(f"Ipadress changed, new ipadress {self.ip_address}")
                current_race_state = data['gameStates']['mGameState']

                #logging.info(f"Current Race_State: {current_race_state}")              
                # Emit signal for successful connection restoration with mGameState
                self.connection_restored.emit(current_race_state)
                #logging.info(f"Race_state emitted!")
                if current_race_state != self.previous_race_state:
                    print(f"Race state changed to {current_race_state}")  # Ensure console output remains
                    #logging.info(f"Race state changed to {current_race_state}")
                    self.previous_race_state = current_race_state

                if participants:
                    race_index = f"Race_{self.race_count}"
                    logging.info(f"Race {self.race_count} has started, beginning data collection.")
                    logging.info(f"Connected to the database, processing race {race_index}.")
                    last_lap_counts = {}
                    QMetaObject.invokeMethod(self.tab_widget, "setCurrentIndex", Qt.QueuedConnection, Q_ARG(int, 0)) #Switch to Score View tab
                    print("Race is STARTING!!!!!!.")
                    self.first_time_run = True
                    while self.running:
                        try:
                            Previous_ipaddress=self.ip_address
                            previous_data = data
                            logging.info("Attempting to get data from the API.")
                            #print("Attempting to get data from the API.")
                            self.ip_address = self.read_ip_address()  # Read IP address before each API call
                            with self.session.get(f'http://{self.ip_address}:8180/crest2/v1/api') as response:
                                data = response.json()
                                # Ensure the response content is valid JSON
                               
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
                                    data = previous_data  # Revert to the previous data if no participants are found
                                    continue  # Skip this loop iteration and try again
                               

                            # Proceed with processing the valid data                             
                            # participants = data['participants']['mParticipantInfo']
                                
                            participants = data.get('participants', {}).get('mParticipantInfo', [])
                            if not participants:
                                data = previous_data  # Revert to the previous data if no participants are found
                                logging.info("No participants found, Race is over")
                                print("No participants found, Race is over.")
                                self.first_time_run = True
                                break # Race is over, break the loop
                            
                            logging.info(f"Processing data for {len(participants)} participants.")
                            #print(f"Processing data for {len(participants)} participants. Current Race_ID {self.current_race_id}")
                            session_id = 1
                            if self.first_time_run:
                                self.db_queue.put(('write_race', (race_index, data, session_id)))
                                print("Race written to database.")
                                self.first_time_run = False
                            #print(f"After race written Thread ID in operation: {threading.get_ident()}")
                            def handle_race_id (race_id):
                                self.current_race_id = race_id
                                #print(f"Race id: {self.current_race_id}")
                            self.db_queue.put(('get_race_id', (race_index,handle_race_id)))  # Only pass the necessary data, not the function
                           
                            #self.current_race_id = race_id  
                            self.race_id_updated.emit(self.current_race_id)  # Emit signal with the updated RaceID                         
                            self.connection_restored.emit(current_race_state) # Emit signal for successful connection restoration with mGameState
                            #logging.info(f"RaceID for {race_index} is {race_id}.")
                            #print(f"RaceID for {race_index} is {race_id}.")

                            for participant in participants:
                                participant_name = participant['mName']
                                current_lap = participant.get('mCurrentLap', 0)
                                #logging.info(f"Participant {participant_name} is on lap {current_lap}.")
                                #print(f"Participant {participant_name} is on lap {current_lap}.")
                                if participant_name not in self.lap_times_dict:
                                    self.lap_times_dict[participant_name] = []

                                latest_lap_time = participant.get('mLastLapTimes', None)
                                lap_times = self.lap_times_dict[participant_name]
                                if latest_lap_time is not None and len(self.lap_times_dict[participant_name]) < current_lap - 1:
                                    self.lap_times_dict[participant_name].append(latest_lap_time)
                                    logging.info(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                    #print(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                    logging.info(f"Lap times list for {participant_name}: {lap_times}")
                                    #print(f"Lap times list for {participant_name}: {lap_times}")


                                if current_lap > last_lap_counts.get(participant_name, 1):
                                    if current_lap - 1 <= len(lap_times):
                                        lap_time = lap_times[current_lap - 2]
                                        logging.info(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time}")
                                        #print(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time}")
                                        #print(f"Current lap Thread ID in operation: {threading.get_ident()}")
                                        print(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time},{participant.get('mLastLapTimes', None)} ")
                                        logging.info(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time},{participant.get('mLastLapTimes', None)} ")                                        
                                        self.db_queue.put(('insert_lap_data', ( self.current_race_id, participant_name, current_lap - 1, lap_time))) #insert lap into Table

                                        last_lap_counts[participant_name] = current_lap

                            #logging.debug(f"Committed lap data to the database for race {race_index}.")
                            #print(f"Committed lap data to the database for race {race_index}.")
                            self.data_updated.emit(data)
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
                    logging.info(f"Race {self.race_count} has ended. Current_Race_State: {current_race_state} self.running: {self.running}")
                    print(f"Race Ended, Current_Race_State: {current_race_state} self.running: {self.running}")
                    self.db_queue.put(('finalize_race', (data, race_index, self.race_count, self.lap_times_dict)))
                    self.race_finished.emit(data)
                    self.race_count += 1
                    time.sleep(10)
                        
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
    

    
    def start_new_session(self):
        self.session_id += 1
    
    def stop(self):
        self.running = False
        self.session.close()
        #self.DatabaseThread.stop()
        self.quit()
        self.wait()

class Worker(QObject):
    switch_tab_signal = pyqtSignal(int)  # Define a signal to switch tabs
    #race_written = pyqtSignal(bool)  # Signal to indicate whether the race was written successfully

class RaceMonitorApp(QMainWindow):
    race_data_loaded = pyqtSignal(list)  # Signal that will carry the race data
    laps_fetched_signal = pyqtSignal(str, list, int)  # Signal for fetched laps
    def __init__(self):
        super().__init__()
        self.db_queue = queue.Queue()
        self.db_thread = DatabaseThread(self.db_queue)
        self.db_thread.start()
        

        self.setWindowTitle("Live Race Data")
        self.setGeometry(100, 100, 1130, 800)
        # Set fixed size to prevent autoresizing
        self.setFixedSize(1080, 800)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 0);")  # Fully transparent
        self.labels = {}
        self.current_race_id = None
        self.current_bestlap_name = None
        self.previous_best_lap_time = None
        self.best_lap_time = None
        self.first_time_run = True
        
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("background-color: transparent;")
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
        background-position: center;
        background-repeat: no-repeat;
        """)
        
        # Tabs addition start
        # Create a QTabWidget to hold different views
        self.tab_widget = QTabWidget(self.central_widget)

        self.tab_widget_mapping = {
            0: [],  # Widgets for Live View
            1: ['dropdown', 'delete_button'],  # Widgets for Results View
            2: [ ],  # Widgets for Score View
        }
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

        #Set the Status view as the default tab
        self.tab_widget.setCurrentIndex(1)
        # Tabs addition end
        # Connect tab change to background update
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        # Load the background image
        #self.background_image = QPixmap("LiveRace.jpg")
        self.status_background_image = QPixmap("Liverace_Status.jpg")  # Background for Status view
        self.live_background_image = QPixmap("LiveRace_LiveView.jpg")  # Background for Live view

        # Create a QLabel to display the background image
        self.background_label = QLabel(self.central_widget)
        self.background_label.setPixmap(self.status_background_image)
        self.background_label.setGeometry(0, 0, 1130, 800)
        self.background_label.setScaledContents(True)  # Adjusts the image size to the window
        self.background_label.lower()  # Ensure the background stays behind other widgets
        self.layout.setAlignment(Qt.AlignTop)
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
        self.dropdown.setFixedSize(400, 30)
        self.dropdown.currentIndexChanged.connect(self.load_selected_race)
        self.layout.addWidget(self.dropdown, alignment=Qt.AlignTop)
        
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
        
        # Status label for connection issues
        self.status_label = QLabel("", self)
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: red;")
        self.layout.addWidget(self.status_label)  # Add the status label below the delete button
        
        self.load_race_data_on_start() # Load any existing race data

        self.monitor_thread = MonitorThread(self.tab_widget, self.db_queue)
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.race_id_updated.connect(self.update_race_id)  # Connect the signal
        self.monitor_thread.error_occurred.connect(self.show_error_message)  # Connect the error signal
        self.monitor_thread.connection_restored.connect(self.handle_connection_restored)  # Connection restored
        self.monitor_thread.start()
        self.worker = Worker()
        self.db_thread.worker = self.worker
        self.worker.switch_tab_signal.connect(self.tab_widget.setCurrentIndex)
        #self.worker.race_written.connect(self.on_race_written)
        self.race_data_loaded.connect(self.handle_race_data) # Connect the signal to the slot that updates the UI            
        self.laps_fetched_signal.connect(self.update_participant_label) # Connect the signal to the slot that updates the UI

        # Call the function to load race data
        self.load_race_data_on_start()
        self.status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")

    #def on_race_written(self, success):
    #    if success:
    #        print("Race data successfully written to the database.")
    #    else:
    #        print("Failed to write race data to the database." )    
   
        
    def on_tab_changed(self, index):
        # Hide all widgets first
        for widget_list in self.tab_widget_mapping.values():
            for widget_name in widget_list:
                if widget_name in self.labels:  # Check if the widget exists in the labels dictionary
                    self.labels[widget_name].hide()

        # Show only the widgets associated with the active tab
        for widget_name in self.tab_widget_mapping.get(index, []):
            if widget_name in self.labels:
                self.labels[widget_name].show()
        # Handle other tab-specific logic, like background updates
        if index == 0:
            self.update_background('live')
        elif index == 1:
            self.update_background('status')

    def update_background(self, view):
        if view == 'status':
            self.background_label.setPixmap(self.status_background_image)
        elif view == 'live':
            self.background_label.setPixmap(self.live_background_image)

  
    def clear_error_message(self):
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()

        
    def handle_connection_restored(self, mGameState):
        # Clear the error message immediately upon restoring the connection
        self.clear_error_message()
        
    def update_status_message(self, message):
        # Update the status label with the message
        self.status_label.setText(message)

    def blink_status_message(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_status_visibility)
        self.timer.start(500)  # Blink every 500 ms

    def toggle_status_visibility(self):
        if self.status_label.isVisible():
            self.status_label.setVisible(False)
        else:
            self.status_label.setVisible(True)
 
    def show_error_message(self, message):
        # Check if the error label already exists with the same message
        if hasattr(self, 'error_label') and self.error_label.text() == message:
            return  # Do not create a new label if the message is the same

        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()  # Remove the existing error label
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
            if self.error_label.isVisible():
                self.error_label.setVisible(False)
            else:
                self.error_label.setVisible(True)
     
    def load_race_data_on_start(self):
        # Send the request to the DatabaseThread to load race data on start
        #print(f"load race on start Thread ID in operation: {threading.get_ident()}")
        self.db_queue.put(('load_race_data_on_start', (self.race_data_loaded,)))       
    def handle_race_data(self, races):
        #print(f"Load Race Data Thread ID in handle_race_data: {threading.get_ident()}")
        if races:
            for race_id, race_index, track_variation, laps_in_event, race_date in races:
                self.dropdown.addItem(f"{race_date} - {track_variation} - {race_index}")
            # Load the latest race results by default
            self.dropdown.setCurrentIndex(self.dropdown.count() - 1)
            self.load_selected_race()

        # Send the request to the DatabaseThread to load race data on start
        #self.db_queue.put(('load_race_data_on_start', (handle_race_data,)))
        
    def setup_live_view(self):
        # Setup your live view widgets here
        self.live_heading = QLabel("Waiting for a new race to start...", self.live_view_widget)
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
        #'''
        self.participant_labels = {}
        for i in range(20):  # Assuming 20 participants max
            self.participant_labels[i] = QLabel("", self.live_view_widget)
            self.participant_labels[i].setStyleSheet("font-size: 14px; color: white;")
            self.live_view_layout.addWidget(self.participant_labels[i])
            self.participant_labels[i].setStyleSheet("font-size: 14px; color: white; border: 1px solid blue; background-color: #333333;")  
            self.participant_labels[i].hide()  # Hide labels initially
        # '''
        # You can add other live view specific components here as per the original design.


    def setup_result_view(self):
        # Setup your results view widgets here
        # Content label for displaying loaded results
        self.results_content = QLabel("No race data available", self.results_view_widget)
        self.results_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        self.results_view_layout.addWidget(self.results_content)
        self.results_view_layout.addStretch(1)
        
    def setup_final_view(self):
        # Setup your final view widgets here
        
        # Content label for displaying Final results
        self.final_content = QLabel("No race data available", self.final_view_widget)
        self.final_content.setStyleSheet("font-size: 14px;font-weight:bold; color: black;")
        self.final_view_layout.addWidget(self.final_content)
        self.final_view_layout.addStretch(1)
        
    def update_live_view(self, data):
        #print(f"Update live view Thread ID in operation: {threading.get_ident()}")
        background_color = "#333333"  # Default background color
        top_background_color = "#A7DB8D"  # Default top background color

        # Extract event information and participant details from the data
        event_info = data['eventInformation']
        self.participants = data['participants']['mParticipantInfo']
    
        # Sort participants by race position
        sorted_participants = sorted(self.participants[:data['participants']['mNumParticipants']], key=lambda p: p['mRacePosition'])
    
        # Update the heading with track variation and car names
        heading_text = f"{event_info['mTranslatedTrackVariation']} ({event_info['mLapsInEvent']}) - {self.participants[0]['mCarNames']}"
        self.live_heading.setText(heading_text)
        
        # Hide all labels when new race start in case of changed number of participants
        for i in range(20):  # Assuming 20 participants max
            self.participant_labels[i].hide()
            
        # Find the valid Lap Times
        valid_lap_times = [p['mFastestLapTimes'] for p in sorted_participants if p['mFastestLapTimes'] != -123]
        if valid_lap_times:
            self.previous_best_lap_time = self.best_lap_time
            self.best_lap_time = min(valid_lap_times)
            best_lap_time = min(valid_lap_times)
            if self.previous_best_lap_time != self.best_lap_time:        
                print(f"New best Lap Time: {self.format_lap_time(self.best_lap_time)}")

        # Loop through each participant to update their corresponding label
        for i, participant in enumerate(sorted_participants):
            participant_name = participant['mName']
            current_lap = participant.get('mCurrentLap', 0)
            
            if current_lap < 3:
                # Format last lap and fastest lap times using the provided utility functions
                last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
                fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])
                # Create the participant text using the utility function
                participant_text = self.create_participant_text(participant, last_lap_str, fastest_lap_str, last_lap_str, last_lap_str)
            else:
                
                def on_laps_fetched(participant_name, recorded_laps, current_lap):
                    self.laps_fetched_signal.emit(participant_name, recorded_laps, current_lap)
                
                # New Code
                #print(f"Fetch recorded laps Thread ID in operation: {threading.get_ident()}")    
                self.db_queue.put(('fetch_recorded_laps', (participant_name, self.current_race_id, current_lap, on_laps_fetched)))

        self.first_time_run = False
        
    def update_participant_label(self, participant_name, recorded_laps, current_lap):
        # This is where you handle the GUI update based on the fetched laps
        # The logic previously in on_laps_fetched now goes here

        # Find the participant and update their label
        participant = next(p for p in self.participants if p['mName'] == participant_name)
        i = self.participants.index(participant)  # Assuming participants is a list

        # Filter and format the laps to display only those prior to the current lap
        last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
        laps_to_display = [lap for lap in recorded_laps if lap[0] < current_lap]
        total_time_seconds = sum(lap[1] for lap in laps_to_display)
        total_time_str = self.format_lap_time(total_time_seconds)
        lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in laps_to_display)

        # Format the fastest lap time
        fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])

        # Create the participant text with the lap times string
        participant_text = self.create_participant_text(participant, last_lap_str, fastest_lap_str, lap_times_str, total_time_str)

        # Now update the label with the participant text and styling
        label = self.participant_labels[i]
        label.setText(participant_text)  # Update the existing label with the new participant text and styling 
        label.show()  # Make the label visible
      
    def format_lap_time(self, lap_time):
       #Helper function to format lap time from seconds to 'MM:SS.ss' format.
        if lap_time is None or lap_time == -123.0:
            return "No Valid Lap!"
        minutes = int(lap_time // 60)
        seconds = lap_time % 60
        return f"{minutes}:{seconds:05.2f}"
    
    def create_participant_text(self, participant, last_lap_str, fastest_lap_str, lap_times_str, total_time_str=""):
        #Helper function to create participant text with custom styling.
        return (
        f"<span style='font-weight:bold; color:#FFFFFF;'>{participant['mRacePosition']}</span>: "
        f"<span style='color:#FFFFFF;'>{participant['mName']}</span> - "
        f"<span style='color:#FFFFA0;'>Last Lap: <span style='color:#00FF00;'>{last_lap_str}</span> - "
        f"<span style='color:#FFFFA0;'>Best Lap: <span style='color:#FFD700;'>{fastest_lap_str}</span> - "
        f"<span style='color:#FFFFA0;'>Laptimes: <span style='color:#FFFFFF;'>[{lap_times_str}]</span> - "
        f"<span style='color:#FFFFA0;'>Total Time: <span style='color:#FFFFFF;'>[{total_time_str}]</span>"
        )
    def display_final_results(self, data):
        logging.info(f"Display Final Result")
        print(f"Display Final Result")
        #self.current_view = 'final'
        #self.update_background('status')
        self.tab_widget.setCurrentIndex(2) #Switch to Final View tab
        self.current_bestlap_name = None #Reset the best lap participant name
        self.first_time_run = True
        self.previous_best_lap_time = None
        self.best_lap_time = None
        # Clear any existing error message if the connection is successful
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
    
    
        # Ensure that only the final results are shown
        #self.hide_participant_labels()
        # Set live view heading to wait for next race
        self.live_heading.setText("Score - Waiting for a new race to start...")



    def load_selected_race(self):
        #self.update_background('status')
        #logging.info(f"Load Selected Race, Race_State: {self.current_view}")
        #print(f"Load Selected Race, Race_State: {self.current_view}")
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            race_index = race_text.split(" - ")[-1]
            self.viewing_race_id = None  # Reset viewing_race_id before loading

            conn = sqlite3.connect('RaceDB.db')
            cursor = conn.cursor()

            cursor.execute('''
                SELECT RaceID, mTranslatedTrackVariation, mLapsInEvent
                FROM Races
                WHERE RaceIndex = ?
            ''', (race_index,))
            race = cursor.fetchone()
            if race:
                race_id, track_variation, laps_in_event = race
                self.viewing_race_id = race_id
                logging.info(f"Load Selected Race, RaceID: { self.viewing_race_id}")
                print(f"Load Selected Race, RaceID: { self.viewing_race_id}")
                cursor.execute('''
                    SELECT mName, mRacePosition, mFastestLapTimes, mLastLapTimes, mCarNames
                    FROM Participants
                    WHERE RaceID = ?
                    ORDER BY mRacePosition ASC
                ''', ( self.viewing_race_id,))
                participants = cursor.fetchall()

                
                displayed_participants = set()
                car_name = participants[0][4] if participants and participants[0][4] else "Unknown Car"
                loaded_results = (f"<span style='font-weight:bold; '> Race No: {race_id} Track: {track_variation} Laps: {laps_in_event} Car: {car_name}:</span><br>")

                for participant in participants:
                    name, race_position, fastest_lap, last_lap, car = participant
                    if fastest_lap is not None:
                        minutes = int(fastest_lap // 60)
                        seconds = fastest_lap % 60
                        fastest_lap_str = f"{minutes}:{seconds:05.2f}"
                    else:
                        fastest_lap_str = "No Valid Lap!"                     
                    if name in displayed_participants:
                        continue

                    cursor.execute('''
                        SELECT LapNumber, LapTime
                        FROM Laps
                        WHERE RaceID = ? AND mName = ?
                        ORDER BY LapNumber ASC
                    ''', ( self.viewing_race_id, name))
                    
                    
                    lap_times = cursor.fetchall()
                    
                    # Filter out any lap times with -123 placeholder
                    valid_lap_times = [time for time in lap_times if time[1] != -123]

                    # Ensure the list is not empty and the index is valid
                    if valid_lap_times:
                        lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in valid_lap_times)
                    else:
                        lap_times_str = "No valid lap!"
                   
                    
                    loaded_results += (f"<span style='font-weight:normal;'>{race_position}: {name} - Fastest Lap: {fastest_lap_str} - Lap Times: [{lap_times_str}]</span><br>")
                    
                    displayed_participants.add(name)

                self.results_content.setTextFormat(Qt.RichText)     
                self.results_content.setText(loaded_results)

            conn.close()

    def delete_selected_race(self):
        logging.info(f"Thread ID in operation: {threading.get_ident()}")
        #print(f"Delete Race Thread ID in operation: {threading.get_ident()}")
        
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            race_index = race_text.split(" - ")[-1]

            def on_race_deleted(race_id):
                if race_id is not None:
                    self.dropdown.removeItem(selected_index)
                    if self.viewing_race_id == race_id:
                        self.labels['results_heading'].setText("Race Deleted")
                        self.labels['results_content'].setText("")
                        self.viewing_race_id = None

            # Send request to DatabaseThread
            self.db_queue.put(('get_race_id_and_delete', (race_index, on_race_deleted)))
           
    def update_race_id(self, race_id):
        self.current_race_id = race_id
        #print(f"Updated Race_ID from RUN current_race_id to {self.current_race_id}")
        logging.info(f"Updated Race_ID from RUN current_race_id to {self.current_race_id}")

    '''
    def show_participant_labels(self):
        for key in self.labels:
            if key.startswith('participant_'):
                self.labels[key].show()

    def hide_participant_labels(self):
        for key in self.labels:
            if key.startswith('participant_'):
                self.labels[key].hide()
    '''
    def closeEvent(self, event):
        self.monitor_thread.stop()
        self.db_thread.stop()
        event.accept()


def main():
    create_database()
    app = QApplication(sys.argv)
    ex = RaceMonitorApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address