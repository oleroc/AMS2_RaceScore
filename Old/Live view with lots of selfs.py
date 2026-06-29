    def update_live_view(self, data):
        #print(f"Update live view Thread ID in operation: {threading.get_ident()}")
        self.background_color = "#333333"  # Default background color
        self.top_background_color = "#A7DB8D"  # Default top background color

        # Extract event information and participant details from the data
        event_info = data['eventInformation']
        self.participants = data['participants']['mParticipantInfo']
    
        # Sort participants by race position
        sorted_participants = sorted(self.participants[:data['participants']['mNumParticipants']], key=lambda p: p['mRacePosition'])
        #print(f"Number of participants: {len(sorted_participants)}")
        # Update the heading with track variation and car names
        heading_text = f"{event_info['mTranslatedTrackVariation']} ({event_info['mLapsInEvent']}) - {self.participants[0]['mCarNames']}"
        self.live_heading.setText(heading_text)
        
        # Hide all labels when new race start in case of changed number of participants
        #for i in range(20):  # Assuming 20 participants max
            #self.participant_labels[i].hide()
            
        # Find the valid Lap Times
        valid_lap_times = [p['mFastestLapTimes'] for p in sorted_participants if p['mFastestLapTimes'] != -123]
        if valid_lap_times:
            self.previous_best_lap_time = self.best_lap_time
            self.best_lap_time = min(valid_lap_times)
            #best_lap_time = min(valid_lap_times)
            if self.previous_best_lap_time != self.best_lap_time:        
                print(f"New best Lap Time: {self.format_lap_time(self.best_lap_time)}")

        # Loop through each participant to update their corresponding label
       
        for i, self.participant in enumerate(sorted_participants):
            self.last_lap_str = self.format_lap_time(self.participant['mLastLapTimes'])
            self.fastest_lap_str = self.format_lap_time(self.participant['mFastestLapTimes']) 
            #current_race_place=i
            self.participant_name = self.participant['mName']
            current_lap = self.participant.get('mCurrentLap', 0)
            self.label = self.participant_labels[i]
            #print(f"current lap: {current_lap}")
            if current_lap < 3: # For the driver being processed.
                # Format last lap and fastest lap times using the provided utility functions

                # Create the participant text using the utility function
                participant_text = self.create_participant_text(self.participant, self.last_lap_str, self.fastest_lap_str, self.last_lap_str, self.last_lap_str)
                #participant_text = self.create_participant_text()
                if self.first_time_run: # Sets all labels to the default background color if no valid lap times are found and it is first run.                   
                    #label = self.participant_labels[i]
                    self.label.setStyleSheet(f"font-size: 14px; background-color: {self.background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                    self.label.show()  # Make the label visible
                    print(f"No one has a valid lap time: {self.participant_name} Time:No valid lap")
                    self.live_status_label.setText("Race Started!")  # Update the status label"
                self.label.setText(participant_text)  # Update the existing label with the new participant text and styling 
                self.label.show()  # Make the label visiblelabel.setText(participant_text)  # Update the existing label with the new participant text and styling    
              
            else:
                #print(f"Fetching Laps from DB: {participant_name}")
                self.db_queue.put(('fetch_recorded_laps', (self.participant_name, self.current_race_id, current_lap,)))
           
        self.first_time_run = False 
       
    def update_participant_label(self, participant_name, recorded_laps, current_lap,):
        #print(f"Update Label: {participant_name}")
        # This is where you handle the GUI update based on the fetched laps
        # The logic previously in on_laps_fetched now goes here

        # Find the participant and update their label
        #participant = next(p for p in self.participants if p['mName'] == participant_name)
        #i = self.participants.index(participant)  # Assuming participants is a list
        #i=current_race_place
        # Filter and format the laps to display only those prior to the current lap
        #last_lap_str = self.format_lap_time(participant['mLastLapTimes'])
        laps_to_display = [lap for lap in recorded_laps if lap[0] < current_lap]
        #total_time_seconds = sum(lap[1] for lap in laps_to_display)
        #total_time_str = self.format_lap_time(total_time_seconds)
        self.new.lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in laps_to_display)

        # Format the fastest lap time
        #fastest_lap_str = self.format_lap_time(participant['mFastestLapTimes'])

        # Create the participant text with the lap times string
        #participant_text = self.create_participant_text(participant, last_lap_str, fastest_lap_str, lap_times_str, total_time_str)
        participant_text = self.create_participant_text(self.participant, self.last_lap_str, self.fastest_lap_str, lap_times_str, self.total_time_str)
        
        # set default background color
        self.label.setStyleSheet(f"font-size: 14px; background-color: {self.background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
        # Now update the label with the participant text and styling
        if self.participant['mFastestLapTimes'] == self.best_lap_time: #sets the best lap time participant to a different color
            self.label.setStyleSheet(f"font-size: 14px; background-color: {self.top_background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
            if self.previous_best_lap_time != self.best_lap_time: 
                print(f"Best time color assigned: {self.participant_name} Last Lap:{self.last_lap_str} Best Lap in race: {self.format_lap_time(self.best_lap_time)}")
                self.live_status_label.setText(f"Best time: {self.participant_name} Best Lap in race: {self.format_lap_time(self.best_lap_time)}")
        
        self.label.setText(participant_text)  # Update the existing label with the new participant text and styling 
        self.label.show()  # Make the label visible
