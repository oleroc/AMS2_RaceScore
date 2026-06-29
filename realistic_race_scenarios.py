#!/usr/bin/env python3
"""
Realistic Race Scenario Generator
Reads data from existing RaceDB.db to create authentic racing scenarios for testing.
Generates up to 4 concurrent races with 6 laps each using real participant data.
"""

import sqlite3
import json
import random
import time
import os
from datetime import datetime
from typing import Dict, List, Any, Tuple

class RaceDBDataExtractor:
    """Extract real race data from existing RaceDB.db for realistic testing"""
    
    def __init__(self, db_path: str = "RaceDB.db"):
        self.db_path = db_path
        self.conn = None
        self.real_participants = []
        self.real_tracks = []
        self.real_cars = []
        self.real_lap_times = {}
        self.driver_performance = {}
        
    def connect_db(self):
        """Connect to the RaceDB database"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            print(f"✅ Connected to {self.db_path}")
            return True
        except sqlite3.Error as e:
            print(f"❌ Error connecting to database: {e}")
            return False
    
    def extract_all_data(self):
        """Extract all relevant data from RaceDB for realistic scenarios"""
        if not self.connect_db():
            return False
        try:
            cursor = self.conn.cursor()
            # Extract participant names
            cursor.execute("SELECT DISTINCT mName FROM Participants WHERE mName NOT LIKE '%(AI)%' ORDER BY mName")
            participants = cursor.fetchall()
            self.real_participants = [p[0] for p in participants if p[0].strip()]
            print(f"📊 Found {len(self.real_participants)} real participants: {self.real_participants[:5]}...")
            # Extract track information
            cursor.execute("SELECT DISTINCT mTranslatedTrackVariation FROM Races ORDER BY mTranslatedTrackVariation")
            tracks = cursor.fetchall()
            self.real_tracks = [t[0] for t in tracks if t[0]]
            print(f"🏁 Found {len(self.real_tracks)} tracks: {self.real_tracks}")
            # Extract car names
            cursor.execute("SELECT DISTINCT mCarNames FROM Participants ORDER BY mCarNames")
            cars = cursor.fetchall()
            self.real_cars = [c[0] for c in cars if c[0]]
            print(f"🚗 Found {len(self.real_cars)} cars: {self.real_cars}")
            # Extract lap times and performance data
            cursor.execute("""
                SELECT p.mName, p.mCarNames, r.mTranslatedTrackVariation, 
                       l.LapTime, p.mFastestLapTimes, p.mLastLapTimes
                FROM Participants p
                JOIN Races r ON p.RaceID = r.RaceID
                LEFT JOIN Laps l ON p.RaceID = l.RaceID AND p.mName = l.mName
                WHERE p.mName NOT LIKE '%(AI)%' AND l.LapTime IS NOT NULL
                ORDER BY p.mName, r.mTranslatedTrackVariation
            """)
            lap_data = cursor.fetchall()
            for name, car, track, lap_time, fastest, last in lap_data:
                key = f"{name}|{track}|{car}"
                if key not in self.real_lap_times:
                    self.real_lap_times[key] = []
                if lap_time and lap_time > 0:
                    self.real_lap_times[key].append(lap_time)
                # Store driver performance characteristics
                if name not in self.driver_performance:
                    self.driver_performance[name] = {
                        'fastest_times': [],
                        'average_performance': 1.0,
                        'consistency': 0.1
                    }
                if fastest and fastest > 0:
                    self.driver_performance[name]['fastest_times'].append(fastest)
            print(f"⏱️ Extracted lap time data for {len(self.real_lap_times)} driver/track/car combinations")
            # Calculate driver performance characteristics
            self._calculate_driver_stats()
            return True
        except sqlite3.Error as e:
            print(f"❌ Error extracting data: {e}")
            return False
        finally:
            if self.conn:
                self.conn.close()
    
    def _calculate_driver_stats(self):
        """Calculate realistic performance characteristics for each driver"""
        for driver, perf in self.driver_performance.items():
            if perf['fastest_times']:
                # Calculate average performance relative to fastest time
                fastest_times = perf['fastest_times']
                avg_fastest = sum(fastest_times) / len(fastest_times)
                
                # Performance factor (1.0 = baseline, <1.0 = faster, >1.0 = slower)
                perf['average_performance'] = random.uniform(0.98, 1.05)
                
                # Consistency (lower = more consistent, higher = more variable)
                perf['consistency'] = random.uniform(0.02, 0.08)
                
                print(f"👤 {driver}: Avg={perf['average_performance']:.3f}, Consistency={perf['consistency']:.3f}")

class RealisticRaceScenarioGenerator:
    """Generate realistic race scenarios using real RaceDB data"""
    
    def __init__(self, data_extractor: RaceDBDataExtractor):
        self.data_extractor = data_extractor
        self.scenarios = {}
        self.output_dir = "api_files"
        os.makedirs(self.output_dir, exist_ok=True)
        
    def create_realistic_scenarios(self) -> Dict[str, Dict]:
        """Create 4 realistic race scenarios with real data"""
        if not self.data_extractor.real_participants:
            print("❌ No real participant data available - using fallback data")
            return self._create_fallback_scenarios()
        
        # Create 4 different race scenarios
        scenarios = {}
        
        # Ensure we have enough participants for 4 races
        available_participants = self.data_extractor.real_participants.copy()
        if len(available_participants) < 8:
            # Duplicate some drivers if not enough unique ones
            available_participants.extend(available_participants[:8-len(available_participants)])
        
        # Shuffle to get different combinations
        random.shuffle(available_participants)
        
        # Create 4 races with 2-4 participants each
        race_configs = [
            {"participants": 4, "name": "Championship Race"},
            {"participants": 3, "name": "Sprint Race"},
            {"participants": 2, "name": "Duel Race"},
            {"participants": 3, "name": "Endurance Race"}
        ]
        
        participant_index = 0
        
        for i, config in enumerate(race_configs, 1):
            # Select participants for this race
            race_participants = []
            for _ in range(config["participants"]):
                if participant_index < len(available_participants):
                    race_participants.append(available_participants[participant_index])
                    participant_index += 1
                else:
                    # Wrap around if we run out
                    race_participants.append(available_participants[participant_index % len(available_participants)])
                    participant_index += 1
            
            # Select track and car
            track_info = self._select_track_and_car()
            
            scenario_key = f"realistic_race_{i}"
            scenarios[scenario_key] = {
                "name": config["name"],
                "participants": race_participants,
                "track": track_info,
                "performance_data": self._get_performance_data_for_participants(race_participants, track_info)
            }
            
            print(f"🏁 Created {config['name']}: {race_participants} at {track_info['track_location']}")
        
        return scenarios
    
    def _select_track_and_car(self) -> Dict[str, Any]:
        """Select a random track and car combination from real data"""
        if self.data_extractor.real_tracks:
            track_name = random.choice(self.data_extractor.real_tracks)
            # Parse track name to get location and variation
            if " - " in track_name:
                location, variation = track_name.split(" - ", 1)
            else:
                location = track_name
                variation = track_name
        else:
            location = "Watkins Glen"
            variation = "Watkins Glen GP"
            track_name = f"{location} - {variation}"
        
        car = random.choice(self.data_extractor.real_cars) if self.data_extractor.real_cars else "Formula X"
        
        return {
            "track_location": location.replace(" ", "_"),
            "track_variation": variation.replace(" ", "_"),
            "translated_location": location,
            "translated_variation": variation,
            "track_length": random.uniform(3000, 6000),  # Realistic track lengths
            "laps_in_event": 6,  # Fixed at 6 laps as requested
            "car_name": car
        }
    
    def _get_performance_data_for_participants(self, participants: List[str], track_info: Dict[str, Any]) -> Dict[str, Dict]:
        """Get realistic performance data for participants based on historical data"""
        performance_data = {}
        
        for participant in participants:
            # Look for historical lap times for this driver/track/car combination
            key = f"{participant}|{track_info['translated_location']} - {track_info['translated_variation']}|{track_info['car_name']}"
            
            if key in self.data_extractor.real_lap_times:
                # Use real lap times as baseline
                historical_times = self.data_extractor.real_lap_times[key]
                base_time = sum(historical_times) / len(historical_times)
            else:
                # Generate realistic base time (2-3 minutes for most tracks)
                base_time = random.uniform(120, 180)
            
            # Get driver performance characteristics
            driver_perf = self.data_extractor.driver_performance.get(participant, {
                'average_performance': 1.0,
                'consistency': 0.05
            })
            
            performance_data[participant] = {
                "base_lap_time": base_time,
                "performance_factor": driver_perf['average_performance'],
                "consistency": driver_perf['consistency'],
                "historical_times": self.data_extractor.real_lap_times.get(key, [])
            }
            
        return performance_data
    
    def _create_fallback_scenarios(self) -> Dict[str, Dict]:
        """Create fallback scenarios with diverse names for different race groups"""
        print("⚠️ Using enhanced fallback scenarios with diverse names")
        
        # Diverse driver names for different race groups
        race_group_a_drivers = ["Lewis Hamilton", "Max Verstappen", "Charles Leclerc", "Lando Norris"]
        race_group_b_drivers = ["Sebastian Vettel", "Fernando Alonso", "Daniel Ricciardo", "George Russell"]  
        race_group_c_drivers = ["Carlos Sainz", "Sergio Perez", "Valtteri Bottas", "Alexander Albon"]
        race_group_d_drivers = ["Pierre Gasly", "Esteban Ocon", "Yuki Tsunoda", "Lance Stroll"]
        
        return {
            "realistic_race_1": {  # Race Group A
                "name": "Formula Grand Prix - Group A",
                "participants": race_group_a_drivers,
                "track": {
                    "track_location": "Watkins_Glen",
                    "track_variation": "Watkins_Glen_GP",
                    "translated_location": "Watkins Glen",
                    "translated_variation": "Watkins Glen GP",
                    "track_length": 5440.27,
                    "laps_in_event": 6,
                    "car_name": "Formula X"
                },
                "performance_data": {
                    race_group_a_drivers[0]: {"base_lap_time": 118.5, "performance_factor": 0.96, "consistency": 0.02},
                    race_group_a_drivers[1]: {"base_lap_time": 119.2, "performance_factor": 0.97, "consistency": 0.025},
                    race_group_a_drivers[2]: {"base_lap_time": 120.1, "performance_factor": 0.98, "consistency": 0.03},
                    race_group_a_drivers[3]: {"base_lap_time": 121.0, "performance_factor": 0.99, "consistency": 0.035}
                }
            },
            "realistic_race_2": {  # Race Group B
                "name": "Touring Car Championship - Group B",
                "participants": race_group_b_drivers,
                "track": {
                    "track_location": "Brands_Hatch",
                    "track_variation": "Brands_Hatch_GP",
                    "translated_location": "Brands Hatch",
                    "translated_variation": "Brands Hatch GP",
                    "track_length": 3908.0,
                    "laps_in_event": 6,
                    "car_name": "Touring Car"
                },
                "performance_data": {
                    race_group_b_drivers[0]: {"base_lap_time": 88.2, "performance_factor": 0.97, "consistency": 0.025},
                    race_group_b_drivers[1]: {"base_lap_time": 89.1, "performance_factor": 0.98, "consistency": 0.03},
                    race_group_b_drivers[2]: {"base_lap_time": 89.8, "performance_factor": 0.99, "consistency": 0.035},
                    race_group_b_drivers[3]: {"base_lap_time": 90.5, "performance_factor": 1.00, "consistency": 0.04}
                }
            },
            "realistic_race_3": {  # Race Group C
                "name": "GT3 Endurance - Group C",
                "participants": race_group_c_drivers,
                "track": {
                    "track_location": "Silverstone",
                    "track_variation": "Silverstone_GP",
                    "translated_location": "Silverstone",
                    "translated_variation": "Silverstone GP",
                    "track_length": 5891.0,
                    "laps_in_event": 6,
                    "car_name": "GT3"
                },
                "performance_data": {
                    race_group_c_drivers[0]: {"base_lap_time": 132.8, "performance_factor": 0.98, "consistency": 0.03},
                    race_group_c_drivers[1]: {"base_lap_time": 133.5, "performance_factor": 0.99, "consistency": 0.035},
                    race_group_c_drivers[2]: {"base_lap_time": 134.2, "performance_factor": 1.00, "consistency": 0.04},
                    race_group_c_drivers[3]: {"base_lap_time": 135.0, "performance_factor": 1.01, "consistency": 0.045}
                }
            },
            "realistic_race_4": {  # Race Group D  
                "name": "Sports Car Series - Group D",
                "participants": race_group_d_drivers,
                "track": {
                    "track_location": "Spa_Francorchamps",
                    "track_variation": "Spa_Francorchamps_GP",
                    "translated_location": "Spa-Francorchamps",
                    "translated_variation": "Spa-Francorchamps GP",
                    "track_length": 7004.0,
                    "laps_in_event": 6,
                    "car_name": "Sports Car"
                },
                "performance_data": {
                    race_group_d_drivers[0]: {"base_lap_time": 148.3, "performance_factor": 0.99, "consistency": 0.035},
                    race_group_d_drivers[1]: {"base_lap_time": 149.1, "performance_factor": 1.00, "consistency": 0.04},
                    race_group_d_drivers[2]: {"base_lap_time": 149.8, "performance_factor": 1.01, "consistency": 0.045},
                    race_group_d_drivers[3]: {"base_lap_time": 150.5, "performance_factor": 1.02, "consistency": 0.05}
                }
            }
        }

class RealisticRaceSimulator:
    def generate_all_test_files(self):
        """Generate ALL possible test files for comprehensive testing - creates main IP files with different racing states"""
        print("\n🔄 Generating ALL test files for comprehensive testing...")
        # Create api_files directory if it doesn't exist
        os.makedirs("api_files", exist_ok=True)
        files_generated = 0
        # Define races: each with its own drivers and IPs
        races = [
            {
                "name": "RaceA",
                "drivers": ["driver1", "driver2", "driver5"],
                "ips": ["192.168.3.201", "192.168.3.202", "192.168.3.205"]
            },
            {
                "name": "RaceB",
                "drivers": ["driver10", "driver12"],
                "ips": ["192.168.3.210", "192.168.3.212"]
            }
        ]
        # Map each IP to its race's drivers and set viewed index to main driver (first in list)
        ip_participant_mapping = {}
        ip_scenario_mapping = {}
        ip_viewed_index_mapping = {}
        for race in races:
            main_driver = race["drivers"][0] if race["drivers"] else None
            for ip in race["ips"]:
                ip_participant_mapping[ip] = race["drivers"]
                ip_scenario_mapping[ip] = "race_start"
                # Set viewed index to index of main_driver in drivers list
                if main_driver and main_driver in race["drivers"]:
                    ip_viewed_index_mapping[ip] = race["drivers"].index(main_driver)
                else:
                    ip_viewed_index_mapping[ip] = 0
        print("🎯 Assigning race scenarios to IPs:")
        for ip, drivers in ip_participant_mapping.items():
            print(f"  {ip}: {drivers}")
        # Store all original states - need to track by IP to avoid conflicts
        original_states = {}
        ip_temp_states = {}
        for ip in self.simulators:
            sim = self.simulators[ip]
            scenario_key = sim["scenario_key"]
            original_states[ip] = {"participants_active": sim["participants_active"]}
            if scenario_key not in ip_temp_states:
                ip_temp_states[scenario_key] = self.race_progress[scenario_key].copy()
        # Generate each file independently to avoid race_progress conflicts
        for ip, target_scenario in ip_scenario_mapping.items():
            if ip not in self.simulators:
                print(f"⚠️  IP {ip} not in simulators, skipping")
                continue
            sim = self.simulators[ip]
            scenario_key = sim["scenario_key"]
            # Use our new mapping for participants
            participant_names = ip_participant_mapping[ip]
            sim["scenario_data"]["participants"] = participant_names
            # Set IP to have participants for testing
            sim["participants_active"] = True
            # All IPs get the same race state: race_start with their race's drivers
            race_progress = {
                "race_active": True,
                "race_finished": False,
                "laps_completed": {name: 0 for name in participant_names},
                "current_lap_times": {name: [random.uniform(125, 140)] for name in participant_names},
                "race_time": random.uniform(10, 60)
            }
            # Temporarily update race progress for this specific IP generation
            self.race_progress[scenario_key] = race_progress
            # Generate API data for this scenario
            api_data = self.generate_realistic_api_data(ip)
            # Fix: Set mViewedParticipantIndex to unique value for each IP in the race
            viewed_index = ip_viewed_index_mapping.get(ip, 0)
            if "participants" in api_data and isinstance(api_data["participants"], dict):
                api_data["participants"]["mViewedParticipantIndex"] = viewed_index
            # Debug: Check what we're about to write
            print(f"🔍 Debug {ip}: GameState={api_data['gameStates']['mGameState']}, NumParticipants={api_data['participants']['mNumParticipants']}, ParticipantsActive={sim['participants_active']}, ViewedIndex={viewed_index}")
            # Create ONLY the main IP file (no suffix) so RaceMonitor can read it
            filename = os.path.join("api_files", f"{ip}.json")
            try:
                with open(filename, 'w') as f:
                    json.dump(api_data, f, indent=2)
                files_generated += 1
                print(f"✅ {ip} → {target_scenario} (main file updated)")
                # Immediately verify what was written to file (debug)
                with open(filename, 'r') as f:
                    written_data = json.load(f)
                print(f"🔍 Verify {ip}: Written GameState={written_data['gameStates']['mGameState']}, NumParticipants={written_data['participants']['mNumParticipants']}, ViewedIndex={written_data['participants']['mViewedParticipantIndex']}")
            except Exception as e:
                print(f"❌ Error writing {filename}: {e}")
        # Restore ALL original states after generating all files
        for ip, states in original_states.items():
            if ip in self.simulators:
                self.simulators[ip]["participants_active"] = states["participants_active"]
        # Restore original race progress states
        for scenario_key, original_progress in ip_temp_states.items():
            self.race_progress[scenario_key] = original_progress
        print(f"\n✅ Generated {files_generated} main IP files with different racing scenarios")
        print("🎯 RaceMonitor can now see multiple active races with different states!")
        self._print_files_summary()
        # Set flag to prevent auto-generation from overwriting our test files
        self.test_files_generated = True
    """Simulate realistic races with real data and 6 lap limit"""
    
    def __init__(self, scenario_data: Dict[str, Any]):
        self.scenario_data = scenario_data
        self.ip_assignments = {
            "realistic_race_1": ["192.168.3.201", "192.168.3.202"],  # Championship Race on 2 IPs
            "realistic_race_2": ["192.168.3.205", "192.168.3.210"],  # Sprint Race on 2 IPs
            "realistic_race_3": ["192.168.3.212", "192.168.3.206"],  # Duel Race on 2 IPs  
            "realistic_race_4": ["192.168.3.207", "192.168.3.208"]   # Endurance Race on 2 IPs
        }
        self.simulators = {}
        self.race_progress = {}
        self.running = False
        self.test_files_generated = False  # Flag to track test file generation
        
    def setup_realistic_races(self):
        """Setup all realistic race scenarios"""
        print("\n🏁 Setting up Realistic Race Test Environment")
        print("=" * 60)
        
        for scenario_key, scenario_data in self.scenario_data.items():
            if scenario_key in self.ip_assignments:
                ips = self.ip_assignments[scenario_key]
                
                print(f"\n📋 {scenario_data['name']} ({scenario_key})")
                print(f"   Participants: {scenario_data['participants']}")
                print(f"   Track: {scenario_data['track']['translated_location']} - {scenario_data['track']['translated_variation']}")
                print(f"   Car: {scenario_data['track']['car_name']}")
                print(f"   IPs: {ips}")
                
                # Initialize race progress
                self.race_progress[scenario_key] = {
                    "laps_completed": {p: 0 for p in scenario_data['participants']},
                    "current_lap_times": {p: [] for p in scenario_data['participants']},
                    "race_time": 0.0,
                    "race_active": False,
                    "race_finished": False
                }
                
                # Create simulator for each IP
                for ip in ips:
                    self.simulators[ip] = {
                        "scenario_key": scenario_key,
                        "scenario_data": scenario_data,
                        "participants_active": False
                    }
        
        print(f"\n✅ Setup complete! Created {len(self.simulators)} simulators across {len(self.scenario_data)} races")
        return True
    
    def generate_realistic_api_data(self, ip: str, viewed_index: int = 0) -> Dict[str, Any]:
        """Generate realistic API data for specific IP based on real RaceDB data"""
        if ip not in self.simulators:
            return self._generate_empty_api_data()

        sim = self.simulators[ip]
        scenario_key = sim["scenario_key"]
        scenario_data = sim["scenario_data"]
        race_progress = self.race_progress[scenario_key]

        # Base API structure
        api_data = {
            "buildinfo": {"mVersion": 14, "mBuildVersionNumber": 2913},
            "gameStates": self._get_game_states(sim["participants_active"], race_progress),
            "participants": self._generate_realistic_participants(sim, scenario_data, race_progress, viewed_index),
            "unfilteredInput": self._get_input_data(sim["participants_active"]),
            "vehicleInformation": {"mCarName": scenario_data['track']['car_name'], "mCarClassName": "Realistic"},
            "eventInformation": self._get_event_info(scenario_data['track']),
            "timings": self._get_timing_data(sim["participants_active"], race_progress),
            "flags": {"mHighestFlagColour": 0, "mHighestFlagReason": 0, "mYellowFlagState": 0},
            "pitInfo": {"mPitMode": 0, "mPitSchedule": 0, "mEnforcedPitStopLap": 0},
            "carState": self._get_car_state(sim["participants_active"], race_progress),
            "motionAndDeviceRelated": self._get_motion_data(sim["participants_active"]),
            "wheelsAndTyres": self._get_wheel_data(sim["participants_active"]),
            "carDamage": {"mCrashState": 0, "mAeroDamage": 0, "mEngineDamage": random.uniform(0, 0.01) if sim["participants_active"] else 0},
            "weather": self._get_weather_data(),
            "timestamp": int(time.time() * 1000)
        }

        return api_data
    
    def _generate_realistic_participants(self, sim: Dict, scenario_data: Dict, race_progress: Dict, viewed_index: int = 0) -> Dict[str, Any]:
        """Generate realistic participant data"""
        if not sim["participants_active"]:
            return {"mViewedParticipantIndex": -1, "mNumParticipants": -1, "mParticipantInfo": []}

        participants = []
        participant_names = scenario_data['participants']
        performance_data = scenario_data['performance_data']
        track_length = scenario_data['track']['track_length']

        for i, name in enumerate(participant_names):
            perf = performance_data.get(name, {"base_lap_time": 130.0, "performance_factor": 1.0, "consistency": 0.05})
            laps_completed = race_progress["laps_completed"][name]

            # Generate realistic lap distance based on progress
            if race_progress["race_active"] and laps_completed < 6:  # Max 6 laps
                lap_distance = random.uniform(0, track_length)
            elif laps_completed >= 6:  # Race finished
                lap_distance = track_length
            else:
                lap_distance = random.uniform(0, 100)  # Pre-race positioning

            # Calculate race position based on total distance
            total_distance = (laps_completed * track_length) + lap_distance

            # Generate realistic lap times
            if laps_completed > 0:
                base_time = perf["base_lap_time"]
                variation = random.uniform(-perf["consistency"], perf["consistency"]) * base_time
                last_lap_time = (base_time * perf["performance_factor"]) + variation
                best_lap_time = min(race_progress["current_lap_times"][name]) if race_progress["current_lap_times"][name] else last_lap_time
            else:
                last_lap_time = -1
                best_lap_time = -1

            participant = {
                "mIsActive": True,
                "mName": name,
                "mWorldPosition": [random.uniform(-400, 400), random.uniform(10, 50), random.uniform(-700, 700)],
                "mCurrentLapDistance": lap_distance,
                "mRacePosition": i + 1,  # Will be updated based on total distance
                "mLapsCompleted": laps_completed,
                "mCurrentLap": laps_completed + 1 if laps_completed < 6 else 6,
                "mCurrentSector": random.randint(1, 3),
                "mRaceStates": 2 if race_progress["race_active"] else 1,
                "mPitModes": 0,
                "mFastestLapTimes": best_lap_time,
                "mLastLapTimes": last_lap_time,
                "mFastestSector1Times": random.uniform(25, 35) if best_lap_time > 0 else -1,
                "mFastestSector2Times": random.uniform(35, 45) if best_lap_time > 0 else -1,
                "mFastestSector3Times": random.uniform(30, 40) if best_lap_time > 0 else -1,
                "mCurrentSector1Times": random.uniform(25, 35),
                "mCurrentSector2Times": random.uniform(35, 45),
                "mCurrentSector3Times": -1,
                "mLapsInvalidated": 0,
                "mOrientations": [random.uniform(-0.1, 0.1), random.uniform(-3.14, 3.14), random.uniform(-0.1, 0.1)],
                "mSpeeds": random.uniform(45, 85) if race_progress["race_active"] else random.uniform(0, 20),
                "mCarNames": scenario_data['track']['car_name'],
                "mCarClassNames": "Realistic",
                "mPitSchedules": 0,
                "mHighestFlagColours": 0,
                "mHighestFlagReasons": 0,
                "mNationalities": 0,
                "_total_distance": total_distance  # For position calculation
            }
            participants.append(participant)

        # Sort by total distance (descending) to get correct race positions
        participants.sort(key=lambda p: p["_total_distance"], reverse=True)
        for i, participant in enumerate(participants):
            participant["mRacePosition"] = i + 1
            del participant["_total_distance"]  # Remove helper field

        return {
            "mViewedParticipantIndex": viewed_index,
            "mNumParticipants": len(participants),
            "mParticipantInfo": participants
        }
    
    def _get_game_states(self, participants_active: bool, race_progress: Dict) -> Dict[str, int]:
        """Get realistic game states"""
        if not participants_active:
            return {"mGameState": 1, "mSessionState": 0, "mRaceState": 0}
        elif race_progress.get("race_finished", False):
            return {"mGameState": 4, "mSessionState": 5, "mRaceState": 3}
        elif race_progress.get("race_active", False):
            return {"mGameState": 2, "mSessionState": 5, "mRaceState": 2}
        else:
            return {"mGameState": 4, "mSessionState": 5, "mRaceState": 1}
    
    def _get_event_info(self, track_data: Dict) -> Dict[str, Any]:
        """Get event information"""
        return {
            "mLapsInEvent": track_data["laps_in_event"],
            "mSessionDuration": 0,
            "mSessionAdditionalLaps": 1,
            "mTrackLocation": track_data["track_location"],
            "mTrackVariation": track_data["track_variation"],
            "mTrackLength": track_data["track_length"],
            "mTranslatedTrackLocation": track_data["translated_location"],
            "mTranslatedTrackVariation": track_data["translated_variation"]
        }
    
    def _get_timing_data(self, participants_active: bool, race_progress: Dict) -> Dict[str, Any]:
        """Get timing data"""
        if not participants_active:
            return {
                "mLapInvalidated": False, "mBestLapTime": -1, "mLastLapTime": -1,
                "mCurrentTime": 0, "mSplitTimeAhead": 0, "mSplitTimeBehind": -1,
                "mSplitTime": 0, "mEventTimeRemaining": -1, "mPersonalFastestLapTime": -1,
                "mWorldFastestLapTime": -1, "mCurrentSector1Time": 0, "mCurrentSector2Time": 0,
                "mCurrentSector3Time": -1, "mFastestSector1Time": -1, "mFastestSector2Time": -1,
                "mFastestSector3Time": -1, "mPersonalFastestSector1Time": -1,
                "mPersonalFastestSector2Time": -1, "mPersonalFastestSector3Time": -1,
                "mWorldFastestSector1Time": -1, "mWorldFastestSector2Time": -1, "mWorldFastestSector3Time": -1
            }
        
        return {
            "mLapInvalidated": False,
            "mBestLapTime": -1,
            "mLastLapTime": -1,
            "mCurrentTime": race_progress["race_time"],
            "mSplitTimeAhead": random.uniform(0, 30),
            "mSplitTimeBehind": -1,
            "mSplitTime": random.uniform(20, 40),
            "mEventTimeRemaining": -1,
            "mPersonalFastestLapTime": -1,
            "mWorldFastestLapTime": -1,
            "mCurrentSector1Time": random.uniform(25, 35),
            "mCurrentSector2Time": random.uniform(35, 45),
            "mCurrentSector3Time": -1,
            "mFastestSector1Time": -1,
            "mFastestSector2Time": -1,
            "mFastestSector3Time": -1,
            "mPersonalFastestSector1Time": -1,
            "mPersonalFastestSector2Time": -1,
            "mPersonalFastestSector3Time": -1,
            "mWorldFastestSector1Time": -1,
            "mWorldFastestSector2Time": -1,
            "mWorldFastestSector3Time": -1
        }
    
    def _generate_empty_api_data(self) -> Dict[str, Any]:
        """Generate empty API data for invalid IP"""
        return {
            "buildinfo": {"mVersion": 14, "mBuildVersionNumber": 2913},
            "gameStates": {"mGameState": 1, "mSessionState": 0, "mRaceState": 0},
            "participants": {"mViewedParticipantIndex": -1, "mNumParticipants": -1, "mParticipantInfo": []},
            "timestamp": int(time.time() * 1000)
        }
    
    def _get_input_data(self, active: bool) -> Dict[str, float]:
        """Get input data"""
        if not active:
            return {"mUnfilteredThrottle": 0, "mUnfilteredBrake": 0, "mUnfilteredSteering": 0, "mUnfilteredClutch": 0, "mJoyPad0": 0, "mDPad": 0}
        return {"mUnfilteredThrottle": random.uniform(0.3, 1.0), "mUnfilteredBrake": random.uniform(0, 0.3), "mUnfilteredSteering": random.uniform(-0.2, 0.2), "mUnfilteredClutch": 0, "mJoyPad0": 0, "mDPad": 0}
    
    def _get_car_state(self, active: bool, race_progress: Dict) -> Dict[str, Any]:
        """Get car state data"""
        if not active:
            return {"mCarFlags": 2, "mOilTempCelsius": 20, "mWaterTempCelsius": 20, "mSpeed": 0, "mRpm": 0, "mThrottle": 0, "mBrake": 0, "mGear": 0}
        
        return {
            "mCarFlags": 2, "mOilTempCelsius": random.uniform(110, 125), "mWaterTempCelsius": random.uniform(105, 120),
            "mWaterPressureKPa": random.uniform(50, 65), "mFuelPressureKPa": 58.5, "mFuelLevel": random.uniform(0.3, 1.0),
            "mFuelCapacity": 77, "mSpeed": random.uniform(45, 85) if race_progress["race_active"] else random.uniform(0, 20),
            "mRpm": random.uniform(3000, 8000) if race_progress["race_active"] else random.uniform(1000, 2000),
            "mMaxRPM": 8500, "mBrake": random.uniform(0, 0.3), "mThrottle": random.uniform(0.3, 1.0) if race_progress["race_active"] else 0,
            "mClutch": 0, "mSteering": random.uniform(-0.2, 0.2), "mGear": random.randint(1, 6) if race_progress["race_active"] else 1,
            "mNumGears": 6, "mOdometerKM": random.uniform(200, 500)
        }
    
    def _get_motion_data(self, active: bool) -> Dict[str, List[float]]:
        """Get motion data"""
        if not active:
            return {"mOrientation": [0, 0, 0], "mLocalVelocity": [0, 0, 0], "mWorldVelocity": [0, 0, 0], "mAngularVelocity": [0, 0, 0], "mLocalAcceleration": [0, 0, 0], "mWorldAcceleration": [0, 0, 0], "mExtentsCentre": [0, 1.20686, 0.119275]}
        
        return {
            "mOrientation": [random.uniform(-0.1, 0.1), random.uniform(-3.14, 3.14), random.uniform(-0.1, 0.1)],
            "mLocalVelocity": [random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)],
            "mWorldVelocity": [0, 0, 0], "mAngularVelocity": [random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01), random.uniform(-0.01, 0.01)],
            "mLocalAcceleration": [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)],
            "mWorldAcceleration": [random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1), random.uniform(-0.1, 0.1)],
            "mExtentsCentre": [0, 1.20686, 0.119275]
        }
    
    def _get_wheel_data(self, active: bool) -> Dict[str, Any]:
        """Get wheel and tyre data"""
        if not active:
            return {"mTyreFlags": [0, 0, 0, 0], "mTyreTemp": [20, 20, 20, 20], "mTyreGrip": [0, 0, 0, 0], "mTyreCompound": ["", "", "", ""]}
        
        return {
            "mTyreFlags": [7, 7, 7, 7], "mTerrain": [0, 0, 0, 0], "mTyreTemp": [random.uniform(80, 110) for _ in range(4)],
            "mTyreGrip": [random.uniform(0.95, 1.0) for _ in range(4)], "mTyreCompound": ["Soft", "Soft", "Soft", "Soft"],
            "mBrakeTempCelsius": [random.uniform(200, 400) for _ in range(4)]
        }
    
    def _get_weather_data(self) -> Dict[str, float]:
        """Get weather data"""
        return {
            "mAmbientTemperature": random.uniform(20, 30), "mTrackTemperature": random.uniform(25, 40),
            "mRainDensity": 0, "mWindSpeed": random.uniform(0, 5), "mWindDirectionX": random.uniform(-1, 1),
            "mWindDirectionY": random.uniform(-1, 1), "mCloudBrightness": 2, "mSnowDensity": 0
        }
    
    def update_race_progress(self, delta_time: float):
        """Update race progress for all active races"""
        for scenario_key, progress in self.race_progress.items():
            if not progress["race_active"]:
                continue
                
            progress["race_time"] += delta_time
            scenario_data = None
            
            # Find scenario data
            for sim in self.simulators.values():
                if sim["scenario_key"] == scenario_key:
                    scenario_data = sim["scenario_data"]
                    break
            
            if not scenario_data:
                continue
            
            # Update each participant's progress
            for participant in scenario_data["participants"]:
                if progress["laps_completed"][participant] >= 6:  # Max 6 laps
                    continue
                
                perf = scenario_data["performance_data"].get(participant, {"base_lap_time": 130.0})
                expected_lap_time = perf["base_lap_time"]
                
                # Check if participant should complete a lap
                time_since_last_lap = progress["race_time"] - (progress["laps_completed"][participant] * expected_lap_time)
                
                if time_since_last_lap >= expected_lap_time:
                    # Complete a lap
                    progress["laps_completed"][participant] += 1
                    
                    # Generate realistic lap time
                    variation = random.uniform(-0.05, 0.05) * expected_lap_time
                    lap_time = expected_lap_time + variation
                    progress["current_lap_times"][participant].append(lap_time)
                    
                    print(f"🏁 {participant} completed lap {progress['laps_completed'][participant]} in {lap_time:.3f}s ({scenario_key})")
                    
                    # Check if race is finished (all participants completed 6 laps)
                    if all(laps >= 6 for laps in progress["laps_completed"].values()):
                        progress["race_finished"] = True
                        progress["race_active"] = False
                        print(f"🏆 {scenario_key} FINISHED!")
    
    def join_race(self, ip: str):
        """Participants join race on specific IP"""
        if ip in self.simulators:
            self.simulators[ip]["participants_active"] = True
            scenario_key = self.simulators[ip]["scenario_key"]
            scenario_data = self.simulators[ip]["scenario_data"]
            print(f"🏁 Participants joined {scenario_data['name']} on {ip}")
    
    def leave_race(self, ip: str):
        """Participants leave race on specific IP"""
        if ip in self.simulators:
            self.simulators[ip]["participants_active"] = False
            scenario_key = self.simulators[ip]["scenario_key"]
            scenario_data = self.simulators[ip]["scenario_data"]
            print(f"🏃 Participants left {scenario_data['name']} on {ip}")
    
    def start_racing(self, scenario_key: str):
        """Start racing for specific scenario"""
        if scenario_key in self.race_progress:
            self.race_progress[scenario_key]["race_active"] = True
            self.race_progress[scenario_key]["race_time"] = 0.0
            print(f"🚦 GREEN LIGHT! Racing started for {scenario_key}")
    
    def start_all_racing(self):
        """Start racing for all active scenarios"""
        for scenario_key in self.race_progress:
            # Check if any IP for this scenario has active participants
            scenario_active = any(
                sim["participants_active"] for sim in self.simulators.values() 
                if sim["scenario_key"] == scenario_key
            )
            if scenario_active:
                self.start_racing(scenario_key)
    
    def generate_api_files(self):
        """Generate API files for all simulators (unless test files are active)"""
        if self.test_files_generated:
            print("🛡️ Skipping auto-generation - test files are active")
            return
            
        for ip in self.simulators:
            api_data = self.generate_realistic_api_data(ip)
            filename = os.path.join("api_files", f"{ip}.json")
            
            try:
                with open(filename, 'w') as f:
                    json.dump(api_data, f, indent=2)
            except Exception as e:
                print(f"❌ Error writing API file for {ip}: {e}")
    
    def generate_all_test_files(self):
        """Generate ALL possible test files for comprehensive testing - creates main IP files with different racing states"""
        print("\n🔄 Generating ALL test files for comprehensive testing...")
        
        # Create api_files directory if it doesn't exist
        os.makedirs("api_files", exist_ok=True)
        
        files_generated = 0
        

        # Define races: each with its own drivers and IPs
        races = [
            {
                "name": "RaceA",
                "drivers": ["driver1", "driver2", "driver5"],
                "ips": ["192.168.3.201", "192.168.3.202", "192.168.3.205"]
            },
            {
                "name": "RaceB",
                "drivers": ["driver10", "driver12"],
                "ips": ["192.168.3.210", "192.168.3.212"]
            }
        ]

        # Map each IP to its race's drivers and its index in the IP list
        ip_participant_mapping = {}
        ip_scenario_mapping = {}
        ip_viewed_index_mapping = {}
        for race in races:
            for idx, ip in enumerate(race["ips"]):
                ip_participant_mapping[ip] = race["drivers"]
                ip_scenario_mapping[ip] = "race_start"
                ip_viewed_index_mapping[ip] = idx  # Each IP gets a unique viewed participant index
        print("🎯 Assigning race scenarios to IPs:")
        for ip, drivers in ip_participant_mapping.items():
            print(f"  {ip}: {drivers}")


        # Store all original states - need to track by IP to avoid conflicts
        original_states = {}
        ip_temp_states = {}
        for ip in self.simulators:
            sim = self.simulators[ip]
            scenario_key = sim["scenario_key"]
            original_states[ip] = {"participants_active": sim["participants_active"]}
            if scenario_key not in ip_temp_states:
                ip_temp_states[scenario_key] = self.race_progress[scenario_key].copy()

        # Generate each file independently to avoid race_progress conflicts
        for ip, target_scenario in ip_scenario_mapping.items():
            if ip not in self.simulators:
                print(f"⚠️  IP {ip} not in simulators, skipping")
                continue
            sim = self.simulators[ip]
            scenario_key = sim["scenario_key"]
            # Use our new mapping for participants
            participant_names = ip_participant_mapping[ip]
            sim["scenario_data"]["participants"] = participant_names
            # Set IP to have participants for testing
            sim["participants_active"] = True

            # All IPs get the same race state: race_start with their race's drivers
            race_progress = {
                "race_active": True,
                "race_finished": False,
                "laps_completed": {name: 0 for name in participant_names},
                "current_lap_times": {name: [random.uniform(125, 140)] for name in participant_names},
                "race_time": random.uniform(10, 60)
            }

            # Temporarily update race progress for this specific IP generation
            self.race_progress[scenario_key] = race_progress

            # Get viewed_index for this IP (main driver index)
            viewed_index = ip_viewed_index_mapping.get(ip, 0)

            # Generate API data for this scenario, passing viewed_index
            api_data = self.generate_realistic_api_data(ip, viewed_index)

            # Debug: Check what we're about to write
            print(f"🔍 Debug {ip}: GameState={api_data['gameStates']['mGameState']}, NumParticipants={api_data['participants']['mNumParticipants']}, ParticipantsActive={sim['participants_active']}, ViewedIndex={viewed_index}")

            # Create ONLY the main IP file (no suffix) so RaceMonitor can read it
            filename = os.path.join("api_files", f"{ip}.json")

            try:
                with open(filename, 'w') as f:
                    json.dump(api_data, f, indent=2)
                files_generated += 1
                print(f"✅ {ip} → {target_scenario} (main file updated)")

                # Immediately verify what was written to file (debug)
                with open(filename, 'r') as f:
                    written_data = json.load(f)
                print(f"🔍 Verify {ip}: Written GameState={written_data['gameStates']['mGameState']}, NumParticipants={written_data['participants']['mNumParticipants']}, ViewedIndex={written_data['participants']['mViewedParticipantIndex']}")

            except Exception as e:
                print(f"❌ Error writing {filename}: {e}")
        
        # Restore ALL original states after generating all files
        for ip, states in original_states.items():
            if ip in self.simulators:
                self.simulators[ip]["participants_active"] = states["participants_active"]
        
        # Restore original race progress states
        for scenario_key, original_progress in ip_temp_states.items():
            self.race_progress[scenario_key] = original_progress
        
        print(f"\n✅ Generated {files_generated} main IP files with different racing scenarios")
        print("🎯 RaceMonitor can now see multiple active races with different states!")
        self._print_files_summary()
        
        # Set flag to prevent auto-generation from overwriting our test files
        self.test_files_generated = True

    def _print_files_summary(self):
        """Print summary of generated files"""
        try:
            files = os.listdir("api_files")
            json_files = [f for f in files if f.endswith('.json')]
            print("📁 Files available in api_files/ directory:")
            for f in sorted(json_files):
                print(f"   📄 {f}")
        except Exception as e:
            print(f"❌ Error listing files: {e}")
    
    def print_status(self):
        """Print current status of all races"""
        print("\n" + "=" * 70)
        print("REALISTIC RACE SIMULATION STATUS")
        print("=" * 70)
        
        for scenario_key, progress in self.race_progress.items():
            # Find scenario data and IPs
            scenario_data = None
            ips = []
            active_ips = []
            
            for ip, sim in self.simulators.items():
                if sim["scenario_key"] == scenario_key:
                    scenario_data = sim["scenario_data"]
                    ips.append(ip)
                    if sim["participants_active"]:
                        active_ips.append(ip)
            
            if not scenario_data:
                continue
            
            status = "FINISHED" if progress["race_finished"] else "RACING" if progress["race_active"] else "WAITING"
            
            print(f"\n🏁 {scenario_data['name']} ({scenario_key})")
            print(f"   Status: {status} | IPs: {ips} | Active: {active_ips}")
            print(f"   Track: {scenario_data['track']['translated_location']} - {scenario_data['track']['translated_variation']}")
            print(f"   Car: {scenario_data['track']['car_name']}")
            print(f"   Race Time: {progress['race_time']:.1f}s")
            
            # Show participant progress
            for participant in scenario_data['participants']:
                laps = progress["laps_completed"][participant]
                lap_times = progress["current_lap_times"][participant]
                best_time = min(lap_times) if lap_times else "N/A"
                print(f"     {participant}: {laps}/6 laps | Best: {best_time}")
        
        print("=" * 70)

def main():
    """Main function to run the realistic race scenario generator"""
    print("🏁 AMS2 Realistic Race Scenario Generator")
    print("=" * 60)
    print("Reading real data from RaceDB.db for authentic racing scenarios")
    print("Maximum 4 concurrent races, 6 laps each")
    print("=" * 60)
    
    # Step 1: Extract real data from RaceDB
    data_extractor = RaceDBDataExtractor()
    if not data_extractor.extract_all_data():
        print("❌ Failed to extract data from RaceDB.db")
        return
    
    # Step 2: Create realistic scenarios
    scenario_generator = RealisticRaceScenarioGenerator(data_extractor)
    scenarios = scenario_generator.create_realistic_scenarios()
    
    # Step 3: Setup race simulator
    race_simulator = RealisticRaceSimulator(scenarios)
    if not race_simulator.setup_realistic_races():
        print("❌ Failed to setup race scenarios")
        return
    
    # Step 4: Start simulation loop
    print("\n🚦 Starting realistic race simulation...")
    race_simulator.running = True
    
    try:
        while True:
            print("\n🏁 Realistic Race Simulation Commands:")
            print("1. Join all races (participants present)")
            print("2. Leave all races (no participants)")  
            print("3. Start all racing (GREEN LIGHT!)")
            print("4. Join specific race (enter IP)")
            print("5. Show status and progress")
            print("6. Generate ALL test files (comprehensive)")
            print("7. Stop simulation")
            
            choice = input("Enter choice (1-7): ").strip()
            
            if choice == "1":
                for ip in race_simulator.simulators:
                    race_simulator.join_race(ip)
                print("✅ All participants joined races!")
                
            elif choice == "2":
                for ip in race_simulator.simulators:
                    race_simulator.leave_race(ip)
                print("✅ All participants left races!")
                
            elif choice == "3":
                race_simulator.start_all_racing()
                if not race_simulator.test_files_generated:  # Only auto-generate if we haven't created test files
                    race_simulator.generate_api_files()  # Immediately update main IP files with active race data
                print("🚦 GREEN LIGHT on all active races!")
                
            elif choice == "4":
                print("Available IPs:", list(race_simulator.simulators.keys()))
                ip = input("Enter IP: ").strip()
                race_simulator.join_race(ip)
                
            elif choice == "5":
                race_simulator.print_status()
                
            elif choice == "6":
                race_simulator.generate_all_test_files()
                print("✅ ALL test files generated!")
                
            elif choice == "7":
                race_simulator.running = False
                print("👋 Simulation stopped!")
                break
                
            else:
                print("❌ Invalid choice!")
            
            # Auto-generation only runs during live racing mode, not for other menu interactions
            # Update race progress if races are active (but not if we just generated test files)
            if choice == "3" and any(progress["race_active"] for progress in race_simulator.race_progress.values()) and not race_simulator.test_files_generated:
                race_simulator.update_race_progress(1.0)  # 1 second progress
                race_simulator.generate_api_files()  # Auto-generate files during racing
                
    except KeyboardInterrupt:
        print("\n👋 Simulation interrupted!")
        race_simulator.running = False

if __name__ == "__main__":
    main()
