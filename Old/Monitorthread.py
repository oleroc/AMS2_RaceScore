class MonitorThread(QThread):
    data_updated = pyqtSignal(dict)
    race_finished = pyqtSignal(dict)
    race_id_updated = pyqtSignal(int)  # Signal to update the RaceID
    error_occurred = pyqtSignal(str)   # New signal for errors
    connection_restored = pyqtSignal(int)  # Signal with mGameState as parameter

    
   
    
    def __init__(self, tab_widget, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ip_address = self.read_ip_address()
        self.tab_widget = tab_widget  # Store the reference to tab_widget
        self.previous_race_state = None
        self.running = True
        self.first_time_run = True
        self.session = requests.Session()
        self.session_id = self.initialize_session_id()
        self.conn = sqlite3.connect('RaceDB.db')
        self.cursor = self.conn.cursor()
        self.session_id = self.initialize_session_id()
        
        # Adjusting race_count based on existing data in the database
        Previous_ipaddress = "127.0.0.1"
        # Get the latest RaceID and corresponding RaceIndex
        self.cursor.execute('SELECT RaceIndex FROM Races ORDER BY RaceID DESC LIMIT 1')
        last_race_index = self.cursor.fetchone()

        if last_race_index is None:
            self.race_count = 1  # Start with 1 if there are no races in the database
        else:
            # Extract the numeric part after "Race_" and convert to an integer, then increment by 1
            last_race_number = int(last_race_index[0].split('_')[1])
            self.race_count = last_race_number + 1
            #logging.info(f"selfracecount {self.race_count} racecount {last_race_number}")

        #self.conn.close()

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
        self.cursor.execute('''
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
                                break # Race is over, break the loop
                            
                            logging.info(f"Processing data for {len(participants)} participants.")
                            #print(f"Processing data for {len(participants)} participants. Current Race_ID {self.current_race_id}")
                            MonitorThread.write_race(race_index, data)
                            self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
                            race_id = self.cursor.fetchone()[0]
                            self.current_race_id = race_id  
                            self.race_id_updated.emit(self.current_race_id)  # Emit signal with the updated RaceID                         
                            self.connection_restored.emit(current_race_state) # Emit signal for successful connection restoration with mGameState
                            logging.info(f"RaceID for {race_index} is {race_id}.")
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
                                        self.insert_lap_data(self.cursor, race_id, participant_name, current_lap - 1, lap_time) #insert lap into Table

                                        last_lap_counts[participant_name] = current_lap

                            conn.commit()
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
    
    def initialize_session_id(self):
        self.cursor.execute('SELECT MAX(SessionID) FROM Races')
        result = self.cursor.fetchone()
        return result[0] + 1 if result[0] else 1
    
    def start_new_session(self):
        self.session_id += 1

    def write_race(self, race_index, data):
        # Insert race data into the Races table if not already present
        self.cursor.execute('''
        INSERT OR IGNORE INTO Races (RaceIndex, mTranslatedTrackVariation, mLapsInEvent, SessionID)
        VALUES (?, ?, ?, ?)
        ''', (race_index, data['eventInformation']['mTranslatedTrackVariation'], data['eventInformation']['mLapsInEvent'], self.session_id))
        
        # Log and print the action taken
        logging.info(f"Inserted race data for race {race_index} if not already present.")
        print(f"Inserted race data for race {race_index} if not already present.")


    def finalize_race(self, data):
        participants = data['participants']['mParticipantInfo']
        #for participant in participants:
            #logging.debug(f"Participant data: {json.dumps(participant, indent=2)}") 
        race_index = f"Race_{self.race_count}"
     
      
        # Get the RaceID for this race
        self.cursor.execute('SELECT RaceID FROM Races WHERE RaceIndex = ?', (race_index,))
        race_id = self.cursor.fetchone()[0]
        self.current_race_id = race_id

        for participant in participants[:data['participants']['mNumParticipants']]:
            participant_name = participant['mName']
            if participant['mFastestLapTimes'] == -123.0:
                participant['mFastestLapTimes'] = None
            if participant['mLastLapTimes'] == -123.0:
                participant['mLastLapTimes'] = None

            # Insert or update participant data
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
                    self.cursor.execute('''
                        INSERT INTO Laps (RaceID, mName, LapNumber, LapTime)
                        VALUES (?, ?, ?, ?)
                    ''', (race_id, participant_name, current_lap, lap_time))

        self.conn.commit()
        self.conn.close()
        logging.info(f"Finalized race data for {race_index}")
        print(f"Finalized race data for {race_index}")

    def stop(self):
        self.running = False
        self.session.close() 
        self.quit()
        self.wait()