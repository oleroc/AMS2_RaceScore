    def calculate_score(self, races, participants, laps):
        logging.info("RMA Def calculate_score entered")
        if not laps:
            return
        # Initialize dictionaries for storing aggregated data across all races
        # Keep track of unique races
        processed_race_ids = set()  # Add this line at the start of the method
        race_scores = {}  # Dictionary to store the score for each participant in each race
        total_scores = {}  # Dictionary to accumulate total scores for each participant across all races
        # Initialize dictionaries for storing aggregated data across all races
        race_scores = {}  # Dictionary to store the score for each participant in each race
        total_scores = {}  # Dictionary to accumulate total scores for each participant across all races
        last_positions = {}  # To store the last position of each driver
        medal_counts = {'gold': {}, 'silver': {}, 'bronze': {}}  # To count gold, silver, and bronze medals

        # Load the score table from the config file
        config = configparser.ConfigParser()
        config.read('config.ini')

        # Extract scoring rules
        score_table = {int(k.split('_')[0]): int(v) for k, v in config['Score Table'].items() if k != 'best_lap'}
        best_lap_bonus = int(config['Score Table']['best_lap'])

        # Iterate over each race
        #print(f"races: {races}")
        for race in races:
            #print(f"Starting New Race Loop: {race}")
            
            race_id = race[0]  # Assuming race_id is the first element in the race tuple
            processed_race_ids.add(race_id)  # Add this inside the loop that iterates over each race

            # Initialize the race-specific data
            race_scores[race_id] = {}

            # Calculate the total race time for each driver based on the laps
            driver_total_times = {}
            driver_flags = {}
            best_lap_times = {}
            driver_laps_completed = {}
            driver_race_positions = {}
            
            #print(f"Laps: {laps}")
            for lap in laps:
                lap_race_id = lap[1]
                #print(f"Lap Race ID:{lap_race_id} and Race ID:{race_id}")
                if lap_race_id != race_id:
                    #print(f"Lap not from the current")
                    continue  # Only consider laps from the current race
                

                mName = lap[2]
                lap_time = lap[4]

                # Sum up the lap times for each driver in the current race
                if mName not in driver_total_times:
                    driver_total_times[mName] = 0
                driver_total_times[mName] += lap_time
                #print(f"best lap times {best_lap_times}")
               
             # Checking to see if there are any participants in this race
            race_participants = [p for p in participants if p[0] == race_id]
            if not race_participants:
                print(f"No participants found for race {race_id}. Skipping score calculation for this race.")
                logging.info(f"RMA No participants found for race {race_id}. Skipping score calculation for this race.")
                continue               
            # Retrieve flags and best lap times from the participants table for the current race
            for participant in participants:
                participant_race_id = participant[0]
                #print(f"Participant Race ID: {participant_race_id} Race ID:{race_id}")
                logging.info(f"RMA Participant Race ID: {participant_race_id} Race ID:{race_id}")
                if participant_race_id != race_id:
                    #print(f"Participant Race ID: {participant_race_id} Race ID:{race_id}")
                    logging.info(f"RMA Participant Race ID: {participant_race_id} Race ID:{race_id}")
                    #print(f"Participant not in Race")
                    continue  # Only consider participants from the current race
                    
                mName = participant[1]
                flag = participant[7]  # Flags column in the participants table
                #print(f"Name: {mName} Flag: {flag}")
                logging.info(f"RMA Name: {mName} Flag: {flag}")
                if flag == 'DNF' and mName not in driver_total_times:
                    driver_total_times[mName] = 0  # Assign a total time of 0
                    driver_flags[mName] = 'DNF'  # Ensure the DNF flag is assigned
                # Store the specific flag values
                if flag == 'Falsestart':
                    driver_flags[mName] = 'Falsestart'
                elif flag == 'DNF':
                    driver_flags[mName] = 'DNF'
                else:
                    driver_flags[mName] = 'No Flag'
                best_lap = participant[4]  # Best lap time in the participants table
                #print(f"Best Lap: {best_lap}")
                logging.info(f"RMA Best Lap: {best_lap}")

                # Store the flag  for each driver
                driver_flags[mName] = flag if flag else "No Flag"
                best_lap_times[mName] = best_lap if best_lap else float('inf') 
                driver_laps_completed[mName] = participant[6]
                driver_race_positions[mName] = participant[3]
                print(f"Driver Laps Completed:{participant}: {driver_laps_completed}")
                #print(f"Best Lap Times: {best_lap_times}")
                logging.info(f"RMA Best Lap Times: {best_lap_times}")
            
            # Rank drivers based on flags and total race time for the current race
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
            # New Sorting Mechanism
            ranked_drivers = sorted(
            driver_total_times.keys(),
            key=lambda x: (
                flag_priority(driver_flags.get(x, "No Flag")),
                -driver_laps_completed.get(x, 0) if driver_flags.get(x) == "DNF" else 0,
                driver_race_positions.get(x, float('inf')) if driver_flags.get(x) == "DNF" else 0,
                float('inf') if driver_flags.get(x) != "No Flag" else driver_total_times[x]
            )
        )


            #Old Ranking 2
            '''
            ranked_drivers = sorted(
                driver_total_times.keys(),
                key=lambda x: (
                    flag_priority(driver_flags.get(x, "No Flag")),
                    -driver_laps_completed.get(x, 0) if driver_flags.get(x) == "DNF" else 0,
                    float('inf') if driver_flags.get(x) != "No Flag" else driver_total_times[x]
                )
            )
            '''
            #Old Ranking
            '''
            ranked_drivers = sorted(driver_total_times.items(), key=lambda x: (flag_priority(driver_flags.get(x[0], "No Flag")),x[1]))  # Sort primarily by flag priority
            
  
            # Output the sorted results
            for driver, time in ranked_drivers:
                flag = driver_flags.get(driver, 'No Flag')
                sort_key = (
                    flag_priority(flag), 
                    time if flag_priority(flag) == 0 else float('inf')
                )
            '''


                
            # print(f"Driver: {driver}, Flag: {flag}, Time: {time}, Sort Key: {sort_key}")
            # print(f"Driver: {driver}, Flag: {driver_flags.get(driver)}, Time: {total_time}, "
            #logging.info(f"RMA Driver: {driver}, Flag: {flag}, Time: {time}, Sort Key: {sort_key}")
            #logging.info(f"RMA Ranking: {ranked_drivers} Driver: {driver}, Flag: {driver_flags.get(driver)}, Time: {driver_total_times}, ")
            print(f"Ranking: {ranked_drivers}")
            # Assign scores for the current race
            place = 1
            for mName in ranked_drivers:
                race_scores[race_id][mName] = score_table.get(place, 0)  # Assign points based on position
                
                last_positions[mName] = place # Track the last position for each driver
                if place == 1: # Track gold, silver, and bronze medals
                    medal_counts['gold'][mName] = medal_counts['gold'].get(mName, 0) + 1
                elif place == 2:
                    medal_counts['silver'][mName] = medal_counts['silver'].get(mName, 0) + 1
                elif place == 3:
                    medal_counts['bronze'][mName] = medal_counts['bronze'].get(mName, 0) + 1
                    
                # Add best lap bonus if applicable
                place += 1
                # Adjust the final display to ensure the correct driver is recognized as the winner
               
            # Determine the driver with the best lap time in the race
            #print(f"Best lap times: {best_lap_times}")   
            if best_lap_times:  # Ensure there are lap times to compare
                best_lap_driver = min(best_lap_times.items(), key=lambda x: x[1])[0]
                #print(f"Best lap driver: {best_lap_driver} Time: {best_lap_times[best_lap_driver]} for Race ID:{race_id} ")
                logging.info(f"RMA Best lap driver: {best_lap_driver} Time: {best_lap_times[best_lap_driver]} for Race ID:{race_id} ")
                # Award the best lap bonus to that driver
                #print(f"Race ID:{race_id}")
                logging.info(f"RMA Race ID:{race_id}")
                #print(f"Race Scores:{race_scores}")
                logging.info(f"RMA Race Scores:{race_scores}")
                #print(f"{race_scores[race_id][best_lap_driver]}")
                logging.info(f"RMA {race_scores[race_id][best_lap_driver]}")
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

        # Update the UI with the calculated scores
        
        self.format_score_view(total_scores, len(processed_race_ids), last_positions, medal_counts)      
