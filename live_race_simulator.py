#!/usr/bin/env python3
"""
Live Race Simulator - Continuously updates API files to test RaceMonitor
"""

import json
import os
import time
import threading
from datetime import datetime

class LiveRaceSimulator:
    def __init__(self):
        self.running = False
        self.races = {
            "10.0.0.201": {
                "participants": ["Marcus", "Dave Stephenson", "Gregory Boundy", "Rob Thompson"],
                "race_time": 0,
                "active": True
            },
            "10.0.0.202": {
                "participants": ["Marcus", "Dave Stephenson", "Gregory Boundy", "Rob Thompson"],
                "race_time": 0,
                "active": True
            },
            "10.0.0.203": {
                "participants": ["Giancarlo Rampanelli", "Lee Chorley", "Ilya Malyuev"],
                "race_time": 0,
                "active": True
            },
            "10.0.0.204": {
                "participants": ["Thiago Izequiel", "Fernando Santos", "Carlos Rodriguez", "Miguel Fernandez"],
                "race_time": 0,
                "active": True
            }
        }
        
    def create_api_file(self, ip, race_data):
        """Create an API file with live race data"""
        participants = race_data["participants"] if race_data["active"] else []
        
        api_data = {
            "buildinfo": {
                "mVersion": 14,
                "mBuildVersionNumber": 2913
            },
            "gameStates": {
                "mGameState": 2,  # Racing
                "mSessionState": 5,  # Race
                "mSessionIsPrivate": 0,
                "mRaceState": 2 if race_data["active"] else 0
            },
            "participants": {
                "mViewedParticipantIndex": -1,
                "mNumParticipants": len(participants) if race_data["active"] else -1,
                "mParticipantInfo": [
                    {
                        "mName": name,
                        "mWorldPosition": [float(i*100), 0, float(i*50)],
                        "mCurrentLapDistance": min(5440.27, race_data["race_time"] * 50 + i * 100),
                        "mRacePosition": i+1,
                        "mLapsCompleted": int(race_data["race_time"] / 120),
                        "mCurrentLap": int(race_data["race_time"] / 120) + 1,
                        "mCurrentSectorTime": race_data["race_time"] % 40,
                        "mCarName": "Il Tempo Gigante",
                        "mCarClassName": "Formula X",
                        "mLastLapTime": 120.5 + i * 0.5,
                        "mFastestLapTime": 119.8 + i * 0.3
                    } for i, name in enumerate(participants)
                ] if race_data["active"] else []
            },
            "vehicleInformation": {
                "mCarName": "Il Tempo Gigante",
                "mCarClassName": "Formula X"
            },
            "eventInformation": {
                "mLapsInEvent": 6,
                "mSessionDuration": 600,
                "mSessionAdditionalLaps": 1,
                "mTrackLocation": "Watkins_Glen",
                "mTrackVariation": "Watkins_Glen_GP",
                "mTrackLength": 5440.27,
                "mTranslatedTrackLocation": "Watkins Glen",
                "mTranslatedTrackVariation": "Watkins Glen GP"
            },
            "timings": {
                "mLapInvalidated": False,
                "mBestLapTime": 119.8,
                "mLastLapTime": 120.5,
                "mCurrentTime": race_data["race_time"],
                "mSplitTimeAhead": 0,
                "mSplitTimeBehind": -1,
                "mSplitTime": 0,
                "mEventTimeRemaining": max(0, 600 - race_data["race_time"]),
                "mPersonalFastestLapTime": 119.8,
                "mWorldFastestLapTime": 118.2,
                "mCurrentSector1Time": race_data["race_time"] % 40,
                "mCurrentSector2Time": 0,
                "mCurrentSector3Time": 0,
                "mSessionFastestLapTime": 118.9,
                "mSessionFastestSector1Time": 35.2,
                "mSessionFastestSector2Time": 45.1,
                "mSessionFastestSector3Time": 38.5
            }
        }
        
        os.makedirs('api_files', exist_ok=True)
        filepath = f'api_files/{ip}.json'
        
        # Write atomically to prevent partial reads
        temp_filepath = f'{filepath}.tmp'
        with open(temp_filepath, 'w') as f:
            json.dump(api_data, f, indent=2)
        os.replace(temp_filepath, filepath)
    
    def update_races(self):
        """Update race data continuously"""
        while self.running:
            timestamp = datetime.now().strftime("%H:%M:%S")
            active_count = sum(1 for race in self.races.values() if race["active"])
            
            print(f"[{timestamp}] 🏁 Updating {active_count} active races...")
            
            for ip, race_data in self.races.items():
                if race_data["active"]:
                    race_data["race_time"] += 2  # Increment race time
                    self.create_api_file(ip, race_data)
                    
            print(f"[{timestamp}] ✅ API files updated - Active races: {active_count}")
            time.sleep(2)  # Update every 2 seconds
    
    def start(self):
        """Start the live simulation"""
        print("🏁 Starting Live Race Simulator")
        print("=" * 50)
        
        # Create initial active races
        for ip, race_data in self.races.items():
            self.create_api_file(ip, race_data)
        
        print(f"✅ Created {len(self.races)} active races")
        print("📁 Files created in: api_files/")
        
        # Start update thread
        self.running = True
        update_thread = threading.Thread(target=self.update_races, daemon=True)
        update_thread.start()
        
        print("\n🚦 Live simulation running! Race data updating every 2 seconds...")
        print("\nCommands:")
        print("1. Toggle race on/off (enter IP)")
        print("2. Show status")
        print("3. Stop simulation")
        
        # Interactive loop
        try:
            while self.running:
                choice = input("\nEnter command (1-3): ").strip()
                
                if choice == "1":
                    ip = input("Enter IP (10.0.0.201-204): ").strip()
                    if ip in self.races:
                        self.races[ip]["active"] = not self.races[ip]["active"]
                        status = "ACTIVE" if self.races[ip]["active"] else "INACTIVE"
                        print(f"🏁 Race {ip} is now {status}")
                        self.create_api_file(ip, self.races[ip])
                    else:
                        print("❌ Invalid IP")
                        
                elif choice == "2":
                    print("\n🏁 LIVE RACE STATUS")
                    print("=" * 30)
                    for ip, race_data in self.races.items():
                        status = "🟢 ACTIVE" if race_data["active"] else "🔴 INACTIVE"
                        participants = len(race_data["participants"])
                        race_time = race_data["race_time"]
                        print(f"{ip}: {status} | {participants} drivers | Time: {race_time}s")
                        
                elif choice == "3":
                    self.stop()
                    break
                    
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop the simulation"""
        print("\n🔴 Stopping Live Race Simulator...")
        self.running = False
        
        # Set all races to inactive
        for ip, race_data in self.races.items():
            race_data["active"] = False
            self.create_api_file(ip, race_data)
        
        print("✅ All races stopped")

if __name__ == "__main__":
    simulator = LiveRaceSimulator()
    simulator.start()
