#!/usr/bin/env python3
"""
Quick test file generator for fixing IP assignments
"""

import json
import os

def create_test_files():
    """Generate test files for all 8 IPs with proper race groups"""
    
    # Create api_files directory if it doesn't exist
    os.makedirs("api_files", exist_ok=True)
    
    # Race scenarios with proper participants
    race_scenarios = {
        # Championship Race (Group A) - 4 participants
        "championship": {
            "participants": ["Tony", "Hans_Christian", "Sivert", "Torstein"],
            "track": "Watkins Glen - Watkins Glen GP",
            "car": "Chevrolet Corvette C8 Z06",
            "ips": ["192.168.3.201", "192.168.3.202"]
        },
        # Sprint Race (Group B) - 3 participants  
        "sprint": {
            "participants": ["Simon", "Kåre", "Per_Erik"],
            "track": "Mojave - Sidewinder", 
            "car": "Ford MkIV",
            "ips": ["192.168.3.203", "192.168.3.204"]
        },
        # Duel Race (Group C) - 2 participants
        "duel": {
            "participants": ["S-8", "Emerson Fittipaldi"],
            "track": "Interlagos - Interlagos GP",
            "car": "Porsche 911 GT3 R", 
            "ips": ["192.168.3.205", "192.168.3.206"]
        },
        # Endurance Race (Group D) - 3 participants
        "endurance": {
            "participants": ["Sandra", "Vegard", "Bjørn_H"],
            "track": "Watkins Glen - Watkins Glen GP",
            "car": "Superkart 250cc",
            "ips": ["192.168.3.207", "192.168.3.208"]
        }
    }
    
    # Different race states for each IP
    race_states = {
        "192.168.3.201": {"state": 2, "scenario": "race_start"},     # Championship - Active racing
        "192.168.3.202": {"state": 2, "scenario": "mid_race"},      # Championship - Mid-race 
        "192.168.3.203": {"state": 2, "scenario": "race_start"},    # Sprint - Active racing
        "192.168.3.204": {"state": 4, "scenario": "race_finish"},   # Sprint - Race finished
        "192.168.3.205": {"state": 4, "scenario": "participants_joined"}, # Duel - Participants waiting
        "192.168.3.206": {"state": 2, "scenario": "race_start"},    # Duel - Active racing
        "192.168.3.207": {"state": 2, "scenario": "mid_race"},      # Endurance - Mid-race
        "192.168.3.208": {"state": 4, "scenario": "race_finish"}    # Endurance - Race finished
    }
    
    for scenario_name, scenario in race_scenarios.items():
        for ip in scenario["ips"]:
            state_info = race_states[ip]
            participants = scenario["participants"]
            
            # Generate participant data
            participant_info = []
            for i, name in enumerate(participants):
                participant_info.append({
                    "mIsActive": True,
                    "mName": name,
                    "mRacePosition": i + 1,
                    "mLapsCompleted": 2 if state_info["scenario"] == "mid_race" else 0,
                    "mCurrentLap": 3 if state_info["scenario"] == "mid_race" else 1,
                    "mRaceStates": 2 if state_info["state"] == 2 else 1,
                    "mFastestLapTimes": 125.5 + i,
                    "mLastLapTimes": 126.2 + i,
                    "mCarNames": scenario["car"],
                    "mCarClassNames": "Realistic"
                })
            
            # Create API data
            api_data = {
                "buildinfo": {"mVersion": 14, "mBuildVersionNumber": 2913},
                "gameStates": {
                    "mGameState": state_info["state"],
                    "mSessionState": 5 if state_info["state"] > 1 else 0,
                    "mRaceState": 2 if state_info["state"] == 2 else (3 if state_info["state"] == 4 else 0)
                },
                "participants": {
                    "mViewedParticipantIndex": 0,
                    "mNumParticipants": len(participants),
                    "mParticipantInfo": participant_info
                },
                "vehicleInformation": {
                    "mCarName": scenario["car"],
                    "mCarClassName": "Realistic"
                },
                "eventInformation": {
                    "mLapsInEvent": 6,
                    "mTrackLocation": scenario["track"].split(" - ")[0].replace(" ", "_"),
                    "mTrackVariation": scenario["track"].split(" - ")[1].replace(" ", "_"),
                    "mTranslatedTrackLocation": scenario["track"].split(" - ")[0],
                    "mTranslatedTrackVariation": scenario["track"].split(" - ")[1],
                    "mTrackLength": 5000.0
                },
                "timestamp": 1733500000000
            }
            
            # Write file
            filename = os.path.join("api_files", f"{ip}.json")
            with open(filename, 'w') as f:
                json.dump(api_data, f, indent=2)
            
            print(f"✅ Created {ip} → {scenario_name} ({state_info['scenario']}) - {len(participants)} participants: {participants}")
    
    print(f"\n🎯 Generated 8 test files with proper race group assignments!")
    print("📋 Race Groups:")
    print("   Group A (Championship): 192.168.3.201-202 → Tony, Hans_Christian, Sivert, Torstein")
    print("   Group B (Sprint): 192.168.3.203-204 → Simon, Kåre, Per_Erik") 
    print("   Group C (Duel): 192.168.3.205-206 → S-8, Emerson Fittipaldi")
    print("   Group D (Endurance): 192.168.3.207-208 → Sandra, Vegard, Bjørn_H")

if __name__ == "__main__":
    create_test_files()
