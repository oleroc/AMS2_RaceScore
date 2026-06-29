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
