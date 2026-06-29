import sys
import requests
import sqlite3
import json
import time
import logging
import os
import configparser
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget, QPushButton, QComboBox, QHBoxLayout, QTabWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QThread, pyqtSignal, Qt, QTimer
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
            RaceDate TEXT DEFAULT (date('now'))
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

    conn.commit()
    conn.close()

class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal(dict)
    race_id_updated = pyqtSignal(int)  # Signal to update the RaceID
    error_occurred = pyqtSignal(str)   # New signal for errors
    connection_restored = pyqtSignal(int)  # Signal with mGameState as parameter
    
    def __init__(self):
        super().__init__()
        self.ip_address = self.read_ip_address()
        self.previous_race_state = None
        self.running = True
        self.session = requests.Session()
        # Adjusting race_count based on existing data in the database
        conn = sqlite3.connect('RaceDB.db')
        cursor = conn.cursor()
        Previous_ipaddress = "127.0.0.1"

        # Get the latest RaceID and corresponding RaceIndex
        cursor.execute('SELECT RaceIndex FROM Races ORDER BY RaceID DESC LIMIT 1')
        last_race_index = cursor.fetchone()

        if last_race_index is None:
            self.race_count = 1  # Start with 1 if there are no races in the database
        else:
            # Extract the numeric part after "Race_" and convert to an integer, then increment by 1
            last_race_number = int(last_race_index[0].split('_')[1])
            self.race_count = last_race_number + 1
            #logging.info(f"selfracecount {self.race_count} racecount {last_race_number}")

        conn.close()

        self.current_race_id = None
        self.viewing_race_id = None  # New variable for viewing historical data
        self.lap_times_dict = {}  # Dictionary to track lap times for each participant
        
        
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

        return config['config']['ip_address']     
        
    def insert_lap_data(self, cursor, race_id, participant_name, current_lap, lap_time):
        cursor.execute('''
            INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
            VALUES (?, ?, ?, ?)
        ''', (race_id, participant_name, current_lap, lap_time))
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

                if current_race_state in [2, 3]:
                    race_index = f"Race_{self.race_count}"
                    logging.info(f"Race {self.race_count} has started, beginning data collection.")

                    conn = sqlite3.connect('RaceDB.db')
                    cursor = conn.cursor()
                    logging.info(f"Connected to the database, processing race {race_index}.")

                    last_lap_counts = {}

                    while current_race_state in [2, 3] and self.running:
                        try:
                            Previous_ipaddress=self.ip_address
                            logging.info("Attempting to get data from the API.")
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
                                    continue  # Skip this loop iteration and try again
                               

                            # Proceed with processing the valid data                             
                            
                            participants = data['participants']['mParticipantInfo']
                            
                            logging.info(f"Processing data for {len(participants)} participants.")
                            print(f"Processing data for {len(participants)} participants. Current Race_ID {self.current_race_id}")


                            cursor.execute('''
                                INSERT OR IGNORE INTO Races (RaceIndex, mTranslatedTrackVariation, mLapsInEvent)
                                VALUES (?, ?, ?)
                            ''', (race_index, data['eventInformation']['mTranslatedTrackVariation'], data['eventInformation']['mLapsInEvent']))
                            logging.info(f"Inserted race data for race {race_index} if not already present.")
                            print(f"Inserted race data for race {race_index} if not already present.")

                            cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
                            race_id = cursor.fetchone()[0]
                            self.current_race_id = race_id  
                            self.race_id_updated.emit(self.current_race_id)  # Emit signal with the updated RaceID                         
                            self.connection_restored.emit(current_race_state) # Emit signal for successful connection restoration with mGameState
                            logging.info(f"RaceID for {race_index} is {race_id}.")
                            print(f"RaceID for {race_index} is {race_id}.")

                            for participant in participants:
                                participant_name = participant['mName']
                                current_lap = participant.get('mCurrentLap', 0)
                                logging.info(f"Participant {participant_name} is on lap {current_lap}.")
                                print(f"Participant {participant_name} is on lap {current_lap}.")
                                if participant_name not in self.lap_times_dict:
                                    self.lap_times_dict[participant_name] = []

                                latest_lap_time = participant.get('mLastLapTimes', None)
                                logging.info(f"Latest lap time for {participant_name}: {latest_lap_time}")
                                print(f"Latest lap time for {participant_name}: {latest_lap_time}")

                                # Dump all participant data to the log for debugging
                                #logging.info(f"Complete participant data: {json.dumps(participant, indent=2)}")
                                #tmp code
                                '''
                                if current_lap > last_lap_counts.get(participant_name, 1):
                                    if current_lap - 1 <= len(lap_times):
                                        self.lap_times_dict[participant_name].append(latest_lap_time)
                                '''
                                #Temp code
                                

                                if latest_lap_time is not None and len(self.lap_times_dict[participant_name]) < current_lap - 1:
                                    self.lap_times_dict[participant_name].append(latest_lap_time)
                                    logging.info(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                    print(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                    logging.info(f"Lap times list for {participant_name}: {lap_times}")
                                    print(f"Lap times list for {participant_name}: {lap_times}")
                                lap_times = self.lap_times_dict[participant_name]
                                
                                
                                '''
                                if current_lap > last_lap_counts.get(participant_name, 1):
                                    if current_lap - 1 <= len(lap_times):
                                        lap_time = lap_times[current_lap - 2]
                                        logging.info(f"Updated lap_times for {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                '''
                                #tmp code
                                #if current_lap > last_lap_counts.get(participant_name, 1):
                                    #if current_lap - 1 <= len(lap_times):
                                       #logging.info(f"Updated lap_times for {lap_times}  {participant_name} at lap {current_lap}: {self.lap_times_dict[participant_name]}")
                                #tmp code
                                '''
                                if 1 <= current_lap - 1 < len(lap_times):
                                    lap_time = lap_times[current_lap - 2]
                                    logging.debug(f"I should see this {current_lap} ")
                                    self.insert_lap_data(cursor, race_id, participant_name, current_lap - 1, lap_time) #insert lap into Table
                                else:
                                    logging.info(f"why Am I seeing this? {current_lap}")
                                '''
                                if current_lap > last_lap_counts.get(participant_name, 1):
                                    if current_lap - 1 <= len(lap_times):
                                        lap_time = lap_times[current_lap - 2]
                                        logging.info(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time}")
                                        print(f"Storing lap time for {participant_name}: Lap {current_lap}, Time {lap_time}")
                                        self.insert_lap_data(cursor, race_id, participant_name, current_lap - 1, lap_time) #insert lap into Table

                                        last_lap_counts[participant_name] = current_lap

                            conn.commit()
                            logging.debug(f"Committed lap data to the database for race {race_index}.")
                            print(f"Committed lap data to the database for race {race_index}.")
                            self.data_updated.emit(data)
                            print(f"Data Sent to live view {race_index}.")
                            time.sleep(5)

                            current_race_state = data['gameStates']['mGameState']
                            print (f"Last line of the loop: Current_Race_State: {current_race_state} self.running: {self.running}")
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
                    self.finalize_race(data)
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

    

    def finalize_race(self, data):
        participants = data['participants']['mParticipantInfo']
        #for participant in participants:
            #logging.debug(f"Participant data: {json.dumps(participant, indent=2)}") 
        race_index = f"Race_{self.race_count}"
        conn = sqlite3.connect('RaceDB.db')
        cursor = conn.cursor()
        
      
        # Get the RaceID for this race
        cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
        race_id = cursor.fetchone()[0]
        self.current_race_id = race_id

        for participant in participants[:data['participants']['mNumParticipants']]:
            participant_name = participant['mName']
            if participant['mFastestLapTimes'] == -123.0:
                participant['mFastestLapTimes'] = None
            if participant['mLastLapTimes'] == -123.0:
                participant['mLastLapTimes'] = None

            # Insert or update participant data
            cursor.execute('''
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

            # Insert lap times into the Laps table based on mCurrentLap
            current_lap = participant.get('mCurrentLap', 0)

            # If mCurrentLap is valid, proceed with inserting the data
            if current_lap > 1:  # Ensure only valid laps are processed
                lap_times = self.lap_times_dict.get(participant_name, [])
                #logging.info(f"current_lap: {current_lap}, lap_times length: {len(lap_times)}")
                if 1 <= current_lap <= len(lap_times):  # Ensure valid indexing
                    lap_time = lap_times[current_lap - 1]
                else:
                    lap_time = None

                if lap_time is not None:
                    cursor.execute('''
                        INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
                        VALUES (?, ?, ?, ?)
                    ''', (race_id, participant_name, current_lap, lap_time))

        conn.commit()
        conn.close()
        logging.info(f"Finalized race data for {race_index}")
        print(f"Finalized race data for {race_index}")

    def stop(self):
        self.running = False
        self.session.close() 
        self.quit()
        self.wait()


class RaceMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Live Race Data")
        self.setGeometry(100, 100, 900, 720)
        # Set fixed size to prevent autoresizing
        self.setFixedSize(900, 720)
        # Set the background color of the window
        self.setStyleSheet("background-color: #a32d2d;")
        self.current_view = 'results'  # Default view is results view
        


        self.labels = {}
        self.current_race_id = None

        self.conn = sqlite3.connect('RaceDB.db')  # Create a database connection
        self.cursor = self.conn.cursor()          # Create a cursor

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.central_widget.setStyleSheet("""
        background-position: center;
        background-repeat: no-repeat;
        """)
        
       
        # Load the background image
        #self.background_image = QPixmap("LiveRace.jpg")
        self.status_background_image = QPixmap("Liverace_Status.jpg")  # Background for Status view
        self.live_background_image = QPixmap("LiveRace_LiveView.jpg")  # Background for Live view

        # Create a QLabel to display the background image
        self.background_label = QLabel(self.central_widget)
        self.background_label.setPixmap(self.status_background_image)
        self.background_label.setGeometry(0, 0, 900, 720)
        self.background_label.setScaledContents(True)  # Adjusts the image size to the window
        self.background_label.lower()  # Ensure the background stays behind other widgets
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignTop)

        self.labels['heading'] = QLabel("", self)
        self.labels['heading'].setStyleSheet("font-size: 16px;")
        self.layout.addWidget(self.labels['heading'])

        self.labels['results'] = QLabel("", self)
        self.labels['results'].setStyleSheet("font-size: 14px;")
        self.layout.addWidget(self.labels['results'])

        self.dropdown = QComboBox(self)
        #self.dropdown.setStyleSheet("font-size: 14px;")
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
        self.layout.addWidget(self.dropdown)
        
        # Add the Delete button
        self.delete_button = QPushButton("Delete Selected Race", self)
        #self.delete_button.setStyleSheet("font-size: 14px;")
        self.delete_button.setStyleSheet("""
            font-size: 14px;
            background-color: #a32d2d;
            color: white;
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

        self.monitor_thread = MonitorThread()
        self.monitor_thread.data_updated.connect(self.update_live_view)
        self.monitor_thread.race_finished.connect(self.display_final_results)
        self.monitor_thread.race_id_updated.connect(self.update_race_id)  # Connect the signal
        self.monitor_thread.error_occurred.connect(self.show_error_message)  # Connect the error signal
        self.monitor_thread.connection_restored.connect(self.handle_connection_restored)  # Connection restored
        self.monitor_thread.start()
        #self.latest_data = None  # Initialize latest_data to store the most recent API data
        self.labels['heading'].setStyleSheet("font-size: 16px; background-color: rgba(0, 0, 0, 0); color: black;")
        self.labels['results'].setStyleSheet("font-size: 14px; background-color: rgba(0, 0, 0, 0); color: black;")
        self.status_label.setStyleSheet("font-size: 14px; color: red; background-color: rgba(0, 0, 0, 0);")
 
    
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

        if mGameState in [2, 3]:
            
            if self.current_view != 'live':
                self.current_view = 'live'
                self.update_background('live')  # Update background to live view
                logging.warning(f"Live View should be active, mGamestate is {mGameState}")
                print(f"Live View should be active, mGamestate is {mGameState}") 
            else:
                logging.warning(f"View is {self.current_view}, mGamestate is {mGameState}")
                print(f"View is {self.current_view}, mGamestate is {mGameState}")
        else:
            # Only update if not already in results view
            if self.current_view != 'results':
                self.current_view = 'results'
                self.update_background('status')  # Update background to status view
                logging.warning(f"Result view should be active, mGamestate is {mGameState}")
                print(f"Result view should be active, mGamestate is {mGameState}")
                self.load_selected_race() # Re-loads the currently selected race to update the UI
                #else:
                #logging.warning(f"View is {self.current_view}, mGamestate is {mGameState}")
                #print(f"View is {self.current_view}, mGamestate is {mGameState}")
        
    def update_status_message(self, message):
        # Update the status label with the message
        self.status_label.setText(message)

        # Optionally, you can make the message blink as well
        #self.blink_status_message()

    def blink_status_message(self):
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_status_visibility)
        self.timer.start(500)  # Blink every 500 ms

    def toggle_status_visibility(self):
        if self.status_label.isVisible():
            self.status_label.setVisible(False)
        else:
            self.status_label.setVisible(True)
            
    def load_race_data_on_start(self):
        conn = sqlite3.connect('RaceDB.db')
        cursor = conn.cursor()

        cursor.execute('''
            SELECT RaceID, RaceIndex, mTranslatedTrackVariation, mLapsInEvent, RaceDate
            FROM Races
            ORDER BY RaceID ASC
        ''')
        races = cursor.fetchall()

        if races:
            for race_id, race_index, track_variation, laps_in_event, race_date in races:
                self.dropdown.addItem(f"{race_date} - {track_variation} - {race_index}")

            # Load the latest race results by default
            self.dropdown.setCurrentIndex(self.dropdown.count() - 1)
            self.load_selected_race()
        else:
            # If no races are found, display a fallback message
            self.labels['heading'].setText("No race data available")
            self.labels['results'].setText("Waiting for a new race to start...")

        conn.close()

    def update_live_view(self, data):
            logging.info(f"Updating live view Live view DEF:")
            # Clear any existing error message if the connection is successful
            if hasattr(self, 'error_label'):
                self.error_label.deleteLater()
                del self.error_label
            cursor = self.cursor  # Use the class-level cursor
            # Set a default background color before the conditional statement
            background_color = "#333333"  # Default background color
            self.current_view = 'live'  # Switch to live view
            if cursor:
                logging.info("Cursor is valid")
            else:
                logging.error("Cursor is invalid!")
            
            # Ensure that only live view is shown during a race
            self.labels['results'].hide()
            self.dropdown.hide()  # Hide the dropdown
            self.delete_button.hide()  # Hide the delete button
            # Hide background image in live view
            #if hasattr(self, 'background_label'):
            #    self.background_label.hide()
            # Set up the layout for the live view
            #self.layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)  # Align to Top Center            
                
            event_info = data['eventInformation']
            participants = data['participants']['mParticipantInfo']

            sorted_participants = sorted(participants[:data['participants']['mNumParticipants']], key=lambda p: p['mRacePosition'])

            heading_text = f"<span style='font-weight:bold; color:#FFFFFF;'>{event_info['mTranslatedTrackVariation']} ({event_info['mLapsInEvent']}) - {participants[0]['mCarNames']}"
            self.labels['heading'].setText(heading_text)

            # Clear previous participant labels
            for key in list(self.labels.keys()):
                if key.startswith('participant_'):
                    self.labels[key].deleteLater()
                    del self.labels[key]
            
            for i, participant in enumerate(sorted_participants):
                participant_name = participant['mName']
                current_lap = participant.get('mCurrentLap', 0)

                if current_lap < 3:
                    # Start accessing the database for laps 2 and beyond, show data from API
                    last_lap = None if participant['mLastLapTimes'] == -123.0 else participant['mLastLapTimes']
                    fastest_lap = None if participant['mFastestLapTimes'] == -123.0 else participant['mFastestLapTimes']
                    last_lap_str = f"{last_lap:.2f}" if last_lap is not None else "No Valid Lap!"
                    fastest_lap_str = f"{fastest_lap:.2f}" if fastest_lap is not None else "No Valid Lap!"

                    # Create participant text with custom styling
                    participant_text = f"<span style='font-weight:bold; color:#FFFFFF;'>{participant['mRacePosition']}</span>: " \
                                       f"<span style='color:#FFFFFF;'>{participant_name}</span> - " \
                                       f"<span style='color:#FFFFA0;'>Last Lap: <span style='color:#00FF00;'>{last_lap_str}</span> - " \
                                       f"<span style='color:#FFFFA0;'>Best Lap: <span style='color:#FFD700;'>{fastest_lap_str}</span> - " \
                                       f"<span style='color:#FFFFA0;'>Laptimes: <span style='color:#FFFFFF;'>[{last_lap_str}]</span>"
                else:
                    # For lap 3 and beyond, combine database laps with the latest API lap time
                    cursor.execute('''
                        SELECT LapNumber, LapTime 
                        FROM Laps 
                        WHERE mName = ? AND RaceID = ? 
                        ORDER BY LapNumber ASC
                    ''', (participant_name, self.current_race_id))
                    recorded_laps = cursor.fetchall()
                    
                    # Only include laps prior to the most recent completed lap (i.e., up to current_lap - 1)
                    laps_to_display = [lap for lap in recorded_laps if lap[0] < current_lap]
                    lap_times_str = ", ".join(f"{lap[1]:.2f}" for lap in laps_to_display)

                    fastest_lap = participant['mFastestLapTimes']
                    fastest_lap_str = f"{fastest_lap:.2f}" if fastest_lap is not None else "No valid lap!"
                    
                    # Create participant text with custom styling
                    participant_text = f"<span style='font-weight:bold; color:#FFFFFF;'>{participant['mRacePosition']}</span>: " \
                                       f"<span style='color:#FFFFFF;'>{participant_name}</span> - " \
                                       f"<span style='color:#FFFFA0;'>Best Lap: <span style='color:#FFD700;'>{fastest_lap_str}</span> - " \
                                       f"<span style='color:#FFFFA0;'>Laptimes: <span style='color:#FFFFFF;'>[{lap_times_str}]</span>"


                    # Set a default background color before the conditional statement
                    #background_color = "#333333"  # Default background color
                    # Highlight the participant with the best lap
                    
                    valid_lap_times = [p['mFastestLapTimes'] for p in sorted_participants if p['mFastestLapTimes'] != -123]

                    if valid_lap_times:
                        best_lap_time = min(valid_lap_times)
                        if participant['mFastestLapTimes'] == best_lap_time:
                            background_color = "#A7DB8D"  # Green background for the best lap
                        else:
                            background_color = "#333333"  # Default background color
                    else:
                        background_color = "#333333"  # Default background color if no valid lap times

                label = QLabel(participant_text, self)
                label.setStyleSheet(f"font-size: 14px; background-color: {background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                label.setTextFormat(Qt.RichText)  # Enable rich text formatting
                self.layout.addWidget(label)
                self.labels[f'participant_{i}'] = label

            self.labels['heading'].show()
            self.show_participant_labels()


    def show_error_message(self, message):
        if hasattr(self, 'error_label') and self.error_label.text() == message:
            return  # Do not create a new label if the message is the same

        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()  # Remove the existing error label

        self.error_label = QLabel(message, self)
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.setStyleSheet("font-size: 20px; color: red; background-color: yellow; padding: 10px;")
        self.layout.addWidget(self.error_label)
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

 
    def display_final_results(self, data):
        logging.info(f"Display Final Result")
        self.current_view = 'status'
        self.update_background('status')
        # Clear any existing error message if the connection is successful
        if hasattr(self, 'error_label'):
            self.error_label.deleteLater()
            del self.error_label
        
        if hasattr(self, 'timer') and self.timer.isActive():
            self.timer.stop()
    
    
        # Ensure that only the final results are shown
        self.hide_participant_labels()
        self.current_view = 'results'  # Switch to results view

        participants = data['participants']['mParticipantInfo']
        final_results = "Final Standings:\n"

        sorted_participants = sorted(participants[:data['participants']['mNumParticipants']], key=lambda p: p['mRacePosition'])

        conn = sqlite3.connect('RaceDB.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT RaceID, RaceIndex, mTranslatedTrackVariation, mLapsInEvent, RaceDate
            FROM Races
            ORDER BY RaceID DESC
            LIMIT 1
        ''')
        race = cursor.fetchone()
        self.current_race_id, race_index, track_variation, laps_in_event, race_date = race

        if self.dropdown.findText(f"{race_date} - {track_variation} - {race_index}") == -1:
            self.dropdown.addItem(f"{race_date} - {track_variation} - {race_index}")
            self.dropdown.setCurrentIndex(self.dropdown.count() - 1)

        for participant in sorted_participants:
            name = participant['mName']
            race_position = participant['mRacePosition']
            fastest_lap = participant['mFastestLapTimes']
            fastest_lap_str = f"{fastest_lap:.2f}" if fastest_lap is not None else "No valid lap!"
            
            cursor.execute('''
                SELECT LapNumber, LapTime
                FROM Laps
                WHERE RaceID = ? AND mName = ?
                ORDER BY LapNumber ASC
            ''', (self.current_race_id, name))
            
            lap_times = cursor.fetchall()
            #lap_times_str = ", ".join(f"{lap[1]:.2f}" for lap in lap_times if lap[1] is not None)
            #lap_times_str = ", ".join(f"{lap[1]:.2f}" if lap[1] is not None else "No valid lap!" for lap in lap_times)
            #logging.info(f"Final standings entry: {name} with race position {race_position}, fastest lap {fastest_lap}, and lap times {lap_times_str}")
            # Ensure the list is not empty and the index is valid
            valid_lap_times = [time for time in lap_times if time[1] != -123]
            if valid_lap_times:
                lap_times_str = ", ".join(f"{lap[1]:.2f}" for lap in valid_lap_times)
            else:
                lap_times_str = "No valid lap!"

            final_results += (f"{race_position}: {name} - Fastest Lap: {fastest_lap_str} - Lap Times: [{lap_times_str}]\n")

        self.labels['heading'].setText(f"{track_variation} ({laps_in_event}) - Final Standings")
        self.labels['results'].setText(final_results)
        self.labels['results'].show()
        self.dropdown.show()  # Show the dropdown
        self.delete_button.show()  # Show the delete button
        # Show background image when switching back from live view
        #if hasattr(self, 'background_label'):
        #   self.background_label.show()

        conn.close()

    def load_selected_race(self):
        self.update_background('status')
        logging.info(f"Load Selected Race, Race_State: {self.current_view}")
        print(f"Load Selected Race, Race_State: {self.current_view}")
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
                    SELECT mName, mRacePosition, mFastestLapTimes, mLastLapTimes
                    FROM Participants
                    WHERE RaceID = ?
                    ORDER BY mRacePosition ASC
                ''', ( self.viewing_race_id,))
                participants = cursor.fetchall()

                final_results = "Final Standings:\n"
                displayed_participants = set()

                for participant in participants:
                    name, race_position, fastest_lap, last_lap = participant
                    fastest_lap_str = f"{fastest_lap:.2f}" if fastest_lap is not None else "No valid lap!"                   
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
                        lap_times_str = ", ".join(f"{lap[1]:.2f}" for lap in valid_lap_times)
                    else:
                        lap_times_str = "No valid lap!"
                   

                    final_results += (f"{race_position}: {name} - Fastest Lap: {fastest_lap_str} - Lap Times: [{lap_times_str}]\n")
                    
                    displayed_participants.add(name)

                self.labels['heading'].setText(f"{track_variation} ({laps_in_event}) - Final Standings")
                self.labels['results'].setText(final_results)

            conn.close()

    def delete_selected_race(self):
        selected_index = self.dropdown.currentIndex()
        if selected_index >= 0:
            race_text = self.dropdown.itemText(selected_index)
            race_index = race_text.split(" - ")[-1]

            conn = sqlite3.connect('RaceDB.db')
            cursor = conn.cursor()

            # Get the RaceID for the selected race
            cursor.execute('''
                SELECT RaceID FROM Races WHERE RaceIndex = ?
            ''', (race_index,))
            race = cursor.fetchone()

            if race:
                race_id = race[0]

                # Delete from Laps
                cursor.execute('''
                    DELETE FROM Laps WHERE RaceID = ?
                ''', (race_id,))

                # Delete from Participants
                cursor.execute('''
                    DELETE FROM Participants WHERE RaceID = ?
                ''', (race_id,))

                # Delete from Races
                cursor.execute('''
                    DELETE FROM Races WHERE RaceID = ?
                ''', (race_id,))

                conn.commit()

                # Remove the race from the dropdown
                self.dropdown.removeItem(selected_index)

                # Clear the displayed race results if the deleted race was the current one
                if  self.viewing_race_id == race_id:
                    self.labels['heading'].setText("Race Deleted")
                    self.labels['results'].setText("")
                    self.viewing_race_id = None

            conn.close()
            
    def update_race_id(self, race_id):
        self.current_race_id = race_id
        print(f"Updated Race_ID from RUN current_race_id to {self.current_race_id}")
        logging.info(f"Updated Race_ID from RUN current_race_id to {self.current_race_id}")


    def show_participant_labels(self):
        for key in self.labels:
            if key.startswith('participant_'):
                self.labels[key].show()

    def hide_participant_labels(self):
        for key in self.labels:
            if key.startswith('participant_'):
                self.labels[key].hide()

    def closeEvent(self, event):
        self.cursor.close()  # Close the cursor
        self.conn.close()    # Close the connection
        self.monitor_thread.stop()
        event.accept()


def main():
    create_database()
    app = QApplication(sys.argv)
    ex = RaceMonitorApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
        main() # No need to pass an IP address