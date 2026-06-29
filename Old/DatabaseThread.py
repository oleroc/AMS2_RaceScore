class DatabaseThread(threading.Thread):

    def __init__(self, db_queue):
        super().__init__()
        self.conn = sqlite3.connect('RaceDB.db')
        self.cursor = self.conn.cursor()
        self.db_queue = db_queue
        self.running = True

    def run(self):
        self.conn = sqlite3.connect('RaceDB.db')
        self.cursor = self.conn.cursor()
        logging.info(f"Create DB Thread ID in operation: {threading.get_ident()}")
        print(f"Create DB Thread ID in operation: {threading.get_ident()}")
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
            callback(participant_name, recorded_laps, current_lap)

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
            if self.worker:
                self.worker.race_written.emit(True)
        except Exception as e:
            logging.error(f"Failed to write race data to the database: {e}")
            logging.error(traceback.format_exc())  # Log the full traceback for debugging
            if self.worker:
                self.worker.race_written.emit(False)  # Emit False if there's an error
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
