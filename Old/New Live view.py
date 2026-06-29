    def update_live_view(self, data):
        #print(f"Update live view Thread ID in operation: {threading.get_ident()}")
        self.laps_gotten = False
        background_color = "#333333"  # Default background color
        top_background_color = "#A7DB8D"  # Default top background color

        # Extract event information and participant details from the data
        event_info = data['eventInformation']
        participants = data['participants']['mParticipantInfo']
    
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
            previous_best_lap_time = best_lap_time
            best_lap_time = min(valid_lap_times)
            #best_lap_time = min(valid_lap_times)
            if previous_best_lap_time != best_lap_time:        
                print(f"New best Lap Time: {self.format_lap_time(best_lap_time)}")

        # Loop through each participant to update their corresponding label
       
        for i, participant in enumerate(sorted_participants):
            last_lap_str = format_lap_time(participant['mLastLapTimes'])
            fastest_lap_str = format_lap_time(participant['mFastestLapTimes']) 
            #current_race_place=i
            participant_name = participant['mName']
            current_lap = participant.get('mCurrentLap', 0)
            label = self.participant_labels[i]
            #print(f"current lap: {current_lap}")
            if current_lap < 3: # For the driver being processed.
                # Format last lap and fastest lap times using the provided utility functions

                # Create the participant text using the utility function
                participant_text = self.create_participant_text(participant, last_lap_str, fastest_lap_str, last_lap_str, last_lap_str)
                #participant_text = self.create_participant_text()
                if self.first_time_run: # Sets all labels to the default background color if no valid lap times are found and it is first run.                   
                    #label = self.participant_labels[i]
                    label.setStyleSheet(f"font-size: 14px; background-color: {background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                    label.show()  # Make the label visible
                    print(f"No one has a valid lap time: {participant_name} Time:No valid lap")
                    self.live_status_label.setText("Race Started!")  # Update the status label"
                label.setText(participant_text)  # Update the existing label with the new participant text and styling 
                label.show()  # Make the label visiblelabel.setText(participant_text)  # Update the existing label with the new participant text and styling    
              
            else:
                #print(f"Fetching Laps from DB: {participant_name}")
                self.db_queue.put(('fetch_recorded_laps', (participant_name, self.current_race_id, current_lap,)))
                while self.laps_gotten == False:
                    time.sleep(0.1)
                total_time_seconds = sum(lap[1] for lap in laps_to_display)
                total_time_str = self.format_lap_time(total_time_seconds)
                lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in laps_to_display)
                participant_text = self.create_participant_text(participant, last_lap_str, fastest_lap_str, self.new_lap_times_str, total_time_str)
        
                # set default background color
                label.setStyleSheet(f"font-size: 14px; background-color: {background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                # Now update the label with the participant text and styling
                if participant['mFastestLapTimes'] == best_lap_time: #sets the best lap time participant to a different color
                    self.label.setStyleSheet(f"font-size: 14px; background-color: {top_background_color}; padding: 5px; margin-bottom: 2px; border-radius: 5px;")
                    if previous_best_lap_time != best_lap_time: 
                        print(f"Best time color assigned: {self.participant_name} Last Lap:{self.last_lap_str} Best Lap in race: {self.format_lap_time(best_lap_time)}")
                        self.live_status_label.setText(f"Best time: {participant_name} Best Lap in race: {self.format_lap_time(best_lap_time)}")
        
                label.setText(participant_text)  # Update the existing label with the new participant text and styling 
                label.show()  # Make the label visible
           
        self.first_time_run = False 
       
    def update_participant_label(self, participant_name, recorded_laps, current_lap,):
        laps_to_display = [lap for lap in recorded_laps if lap[0] < current_lap]
        self.new_lap_times_str = ", ".join(f"{int(lap[1] // 60)}:{lap[1] % 60:05.2f}" for lap in laps_to_display)
        self.laps_gotten = True

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