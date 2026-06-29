    def update_live_view(self, data):
        cursor = self.cursor  # Use the class-level cursor for database queries
        background_color = "#333333"  # Default background color
        top_background_color = "#A7DB8D"  # Default top background color

        # Extract event information and participant details from the data
        event_info = data['eventInformation']
        participants = data['participants']['mParticipantInfo']
    
        # Sort participants by race position
        sorted_participants = sorted(participants[:data['participants']['mNumParticipants']], key=lambda p: p['mRacePosition'])
    
        # Update the heading with track variation and car names
        heading_text = f"{event_info['mTranslatedTrackVariation']} ({event_info['mLapsInEvent']}) - {participants[0]['mCarNames']}"
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
            #print(f"Processing: {participant_name} Time: {self.format_lap_time(best_lap_time)}")

            if current_lap < 3:
                # Format last lap and fastest lap times using the provided utility functions
                last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
                fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])
                # Create the participant text using the utility function
                participant_text = self.create_participant_text(participant, last_lap_str, fastest_lap_str, last_lap_str)
            else:
                # Query the database for recorded laps if the current lap is 3 or beyond
                cursor.execute('''
                    SELECT LapNumber, LapTime 
                    FROM Laps 
                    WHERE mName = ? AND RaceID = ? 
                    ORDER BY LapNumber ASC
                ''', (participant_name, self.current_race_id))
                recorded_laps = cursor.fetchall()

                # Filter and format the laps to display only those prior to the current lap
                last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
                laps_to_display = [lap for lap in recorded_laps if lap[0] < current_lap]
                lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in laps_to_display)

                # Format the fastest lap time
                fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])
                # Create the participant text with the lap times string
                participant_text = self.create_participant_text(participant, last_lap_str, fastest_lap_str, lap_times_str)



            label = self.participant_labels[i]
            if valid_lap_times: #sets background color based on best lap time
                if participant['mFastestLapTimes'] == best_lap_time:
                        print(f"Best time color assigned: {participant_name} Last Lap:{last_lap_str} Best Lap in race: {self.format_lap_time(best_lap_time)}")
                        label.setStyleSheet(f"font-size: 14px; background-color: {top_background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                else: 
                    label.setStyleSheet(f"font-size: 14px; background-color: {background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
            else: # Sets all labels to the default background color if no valid lap times are found
                label.setStyleSheet(f"font-size: 14px; background-color: {background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                print(f"No one has a valid lap time: {participant_name} Time:No valid lap")
                label.show()  # Make the label visible 
            label.setText(participant_text) # Update the existing label with the new participant text and styling  
            #self.live_view_layout.addWidget(label)  # Ensure the label is visible
                    