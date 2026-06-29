#!/usr/bin/env python3
"""
Quick Test Race Creator
Creates simple API files with active participants for testing
"""

import json
import os

def create_api_file(ip, participants):
    """Create an API file with active participants"""
    api_data = {
        "buildinfo": {
            "mVersion": 14,
            "mBuildVersionNumber": 2913
        },
        "gameStates": {
            "mGameState": 1,
            "mSessionState": 0,
            "mSessionIsPrivate": 0,
            "mRaceState": 0
        },
        "participants": {
            "mViewedParticipantIndex": -1,
            "mNumParticipants": len(participants) if participants else -1,
            "mParticipantInfo": [
                {
                    "mName": name,
                    "mWorldPosition": [0, 0, 0],
                    "mCurrentLapDistance": 0,
                    "mRacePosition": i+1,
                    "mLapsCompleted": 0,
                    "mCurrentLap": 1,
                    "mCurrentSectorTime": 0,
                    "mCarName": "Il Tempo Gigante",
                    "mCarClassName": "Formula X"
                } for i, name in enumerate(participants)
            ] if participants else []
        },
        "vehicleInformation": {
            "mCarName": "Il Tempo Gigante",
            "mCarClassName": "Formula X"
        },
        "eventInformation": {
            "mLapsInEvent": 6,
            "mSessionDuration": 0,
            "mSessionAdditionalLaps": 1,
            "mTrackLocation": "Watkins_Glen",
            "mTrackVariation": "Watkins_Glen_GP",
            "mTrackLength": 5440.27,
            "mTranslatedTrackLocation": "Watkins Glen",
            "mTranslatedTrackVariation": "Watkins Glen GP"
        },
        "timings": {
            "mLapInvalidated": False,
            "mBestLapTime": -1,
            "mLastLapTime": -1,
            "mCurrentTime": 0.0,
            "mSplitTimeAhead": 0,
            "mSplitTimeBehind": -1,
            "mSplitTime": 0,
            "mEventTimeRemaining": -1,
            "mPersonalFastestLapTime": -1,
            "mWorldFastestLapTime": -1,
            "mCurrentSector1Time": 0,
            "mCurrentSector2Time": 0,
            "mCurrentSector3Time": 0,
            "mSessionFastestLapTime": -1,
            "mSessionFastestSector1Time": -1,
            "mSessionFastestSector2Time": -1,
            "mSessionFastestSector3Time": -1
        }
    }
    
    os.makedirs('api_files', exist_ok=True)
    filepath = f'api_files/{ip}.json'
    with open(filepath, 'w') as f:
        json.dump(api_data, f, indent=2)
    print(f"✅ Created {filepath} with {len(participants)} participants")

def main():
    print("🏁 Creating Test Race API Files")
    print("=" * 50)
    
    # Create 4 different races for testing
    races = {
        "10.0.0.201": ["Marcus", "Dave Stephenson", "Gregory Boundy", "Rob Thompson"],
        "10.0.0.202": ["Marcus", "Dave Stephenson", "Gregory Boundy", "Rob Thompson"],  # Same race as 201
        "10.0.0.203": ["Giancarlo Rampanelli", "Lee Chorley", "Ilya Malyuev"],
        "10.0.0.204": ["Thiago Izequiel", "Fernando Santos", "Carlos Rodriguez", "Miguel Fernandez"]
    }
    
    for ip, participants in races.items():
        create_api_file(ip, participants)
    
    print("\n🚦 Test races created!")
    print(f"📁 Files created in: {os.path.abspath('api_files')}")
    print("\n🎯 What was created:")
    print("- Race 1: 4 participants on IPs 10.0.0.201-202 (same race)")
    print("- Race 2: 3 participants on IP 10.0.0.203")
    print("- Race 3: 4 participants on IP 10.0.0.204")
    print("\n✅ RaceMonitor should now detect these active races!")

if __name__ == "__main__":
    main()
