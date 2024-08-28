import requests  # Import the requests library to make HTTP requests
import json  # Import the json library to handle JSON data
import os  # Import the os library for interacting with the operating system
import sys  # Import the sys library to handle command-line arguments
import time  # Import the time library for sleep functionality

def fetch_race_data(url):
    # Make a GET request to the given URL and fetch the race data
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()  # Return the JSON data if the request is successful
    else:
        print(f"Failed to fetch data from {url}, status code: {response.status_code}")
        return None

def read_driver_names(file_path):
    # Read the driver names from the specified file
    with open(file_path, 'r') as f:
        line = f.readline().strip()
        driver_names = line.split(';')
        driver_names = [name.split(' (')[0] for name in driver_names]  # Remove any part after "("
    return driver_names

def map_scores_to_drivers(driver_names, race_data):
    # Map the race positions to the driver names
    driver_scores = {name: 0 for name in driver_names}
    for participant in race_data['participants']['mParticipantInfo']:
        driver_name = participant['mName'].split(' (')[0]  # Remove any part after "("
        if driver_name in driver_scores:
            driver_scores[driver_name] = participant['mRacePosition']
    return driver_scores

def write_race_results(driver_scores, file_path):
    # Write the race results to the specified file
    line = ';'.join(str(driver_scores[name]) for name in driver_scores) + ';'
    
    # Ensure the directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Append the results to the file
    with open(file_path, 'a') as f:
        f.write(line + '\n')
    print("Race results written to file.")

def find_best_lap_driver(race_data):
    best_lap_time = float('inf')
    best_driver = None
    
    for participant in race_data['participants']['mParticipantInfo']:
        lap_time = participant['mFastestLapTimes']
        if lap_time > 0 and lap_time < best_lap_time:
            best_lap_time = lap_time
            best_driver = participant['mName'].split(' (')[0]  # Remove any part after "("
    
    return best_driver, best_lap_time

def write_best_lap_driver(best_driver, file_path):
    # Write the best lap driver to the specified file
    if best_driver:
        with open(file_path, 'a') as f:
            f.write(best_driver + '\n')
        print(f"Best lap driver {best_driver} written to file.")
    else:
        print("No valid best lap driver found.")

def main(api_host):
    # Define the API URL and file paths
    api_url = f'http://{api_host}:8180/crest2/v1/api'
    file_path = 'C:\\force\\gui\\score.txt'
    best_lap_file_path = 'C:\\force\\gui\\bestlap.txt'
    driver_file_path = 'C:\\force\\gui\\drivers.txt'
    end_flag_file = 'C:\\force\\gui\\end.txt'

    previous_game_state = None  # Initialize previous_game_state as None

    while True:
        # Check if the end flag file exists
        if os.path.exists(end_flag_file):
            print("End flag detected. Stopping the script.")
            os.remove(end_flag_file)  # Remove the end flag file
            break

        race_data = fetch_race_data(api_url)  # Fetch the race data from the API
        if race_data:
            current_game_state = race_data['gameStates']['mGameState']  # Get the current game state
            
            # Check for transition from 2 to 3 or 2 to 4
            if previous_game_state == 2 and (current_game_state == 3 or current_game_state == 4):
                driver_names = read_driver_names(driver_file_path)  # Read the driver names from the file
                driver_scores = map_scores_to_drivers(driver_names, race_data)  # Map scores to drivers
                write_race_results(driver_scores, file_path)  # Write the race results to the file

                best_driver, _ = find_best_lap_driver(race_data)  # Find the best lap driver
                write_best_lap_driver(best_driver, best_lap_file_path)  # Write the best lap driver to the file
            
            previous_game_state = current_game_state  # Update previous_game_state
        
        time.sleep(5)  # Wait for 5 seconds before checking again

if __name__ == "__main__":
    # Check the command-line arguments
    if len(sys.argv) != 2:
        print("Usage: python GetScore.py <IP ADDRESS> | end")
        sys.exit(1)
    
    arg = sys.argv[1]
    if arg.lower() == "end":
        # Create the end flag file
        open('C:\\force\\gui\\end.txt', 'w').close()
        print("End flag file created. The script will stop if it's running.")
    else:
        api_host = arg  # Get the API host from the command-line argument
        main(api_host)  # Run the main function with the provided API host
