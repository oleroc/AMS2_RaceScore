#!/usr/bin/env python3
"""
AMS2 API Simulation Environment - Participant-Based Race Detection
Creates realistic racing data files for testing multi-race monitoring system.
Uses participant presence for race detection, correct game states for realism.
"""

import json
import time
import random
import os
import threading
import math
from datetime import datetime
from typing import Dict, List, Any

class RaceSimulator:
    """Simulates a single race with participants-based state management"""
    
    def __init__(self, ip: str, participants: List[str], track_info: Dict[str, Any]):
        self.ip = ip
        self.participants = participants
        self.track_info = track_info
        self.participants_active = False  # Key: participants present = race active
        self.session_duration = 0
        self.race_time = 0.0
        self.lap_length = track_info.get("track_length", 5440.27)
        
        # Game states (for realism, not race detection)
        self.game_state = 1  # Start in lobby
        self.session_state = 0  # Start in lobby
        self.race_state = 0  # Start in lobby
        
        # Initialize participant data
        self.participant_data = []
        for i, name in enumerate(participants):
            self.participant_data.append({
                "name": name,
                "position": i + 1,
                "laps_completed": 0,
                "current_lap": 1,
                "current_sector": 1,
                "lap_distance": random.uniform(0, 100),
                "best_lap_time": -1,
                "last_lap_time": -1,
                "sector_times": [-1, -1, -1],
                "car_name": "Il Tempo Gigante",
                "car_class": "Flaaklypa",
                "speed": 0.0,
                "fuel_level": random.uniform(0.8, 1.0),
                "race_position": i + 1
            })
    
    def set_participants_active(self, active: bool):
        """Set whether participants are present (race detection key)"""
        self.participants_active = active
        if active:
            print(f"Participants joined race on {self.ip} - RACE DETECTED")
            # Set realistic game states for active race
            self.game_state = 4  # Menu/Waiting for go
            self.session_state = 5  # Game in progress  
            self.race_state = 1  # Waiting for green light
        else:
            print(f"Participants left race on {self.ip} - RACE ENDED")
            # Set game states for lobby/no race
            self.game_state = 1  # Lobby
            self.session_state = 0  # Lobby
            self.race_state = 0  # Lobby
    
    def start_racing(self):
        """Start the actual racing (green light)"""
        if self.participants_active:
            self.race_time = 0.0
            # Update game states to racing
            self.game_state = 2  # Race running
            self.session_state = 5  # Game in progress
            self.race_state = 2  # Green light
            print(f"Green light! Racing started on {self.ip}")
    
    def finish_race(self):
        """Finish the race (results screen, but participants still present)"""
        if self.participants_active:
            # Update to results screen
            self.game_state = 4  # Menu/final resultscreen
            self.session_state = 5  # Game in progress
            self.race_state = 3  # Won race and Resultscreen
            print(f"Race finished on {self.ip} - showing results")
    
    def update_race(self, delta_time: float):
        """Update race simulation by delta_time seconds"""
        if not self.participants_active:
            return
            
        # Only update race progress if participants are present
        self.race_time += delta_time
        
        # Update each participant (only if race is active)
        for participant in self.participant_data:
            # Simulate driving progress
            if self.race_state == 2:  # Only move if green light
                base_speed = random.uniform(45, 70)  # km/h
                participant["speed"] = base_speed + random.uniform(-5, 5)
                
                # Update lap distance
                distance_increment = (participant["speed"] / 3.6) * delta_time  # m/s
                participant["lap_distance"] += distance_increment
                
                # Check if completed a lap
                if participant["lap_distance"] >= self.lap_length:
                    participant["lap_distance"] -= self.lap_length
                    participant["laps_completed"] += 1
                    participant["current_lap"] += 1
                    
                    # Generate lap time
                    base_lap_time = 120 + random.uniform(-10, 15)  # 110-135 seconds
                    participant["last_lap_time"] = base_lap_time
                    
                    if participant["best_lap_time"] == -1 or base_lap_time < participant["best_lap_time"]:
                        participant["best_lap_time"] = base_lap_time
                    
                    print(f"{self.ip}: {participant['name']} completed lap {participant['laps_completed']} in {base_lap_time:.3f}s")
            else:
                # Not racing - minimal speed
                participant["speed"] = random.uniform(0, 10)
            
            # Update sector based on distance
            sector_1_end = self.lap_length * 0.33
            sector_2_end = self.lap_length * 0.66
            
            if participant["lap_distance"] < sector_1_end:
                participant["current_sector"] = 1
            elif participant["lap_distance"] < sector_2_end:
                participant["current_sector"] = 2
            else:
                participant["current_sector"] = 3
            
            # Update fuel consumption (only during racing)
            if self.race_state == 2:
                participant["fuel_level"] -= random.uniform(0.0001, 0.0005)
                participant["fuel_level"] = max(0, participant["fuel_level"])
        
        # Update race positions based on laps completed and lap distance
        if self.race_state == 2:  # Only during racing
            self.participant_data.sort(key=lambda p: (p["laps_completed"], p["lap_distance"]), reverse=True)
            for i, participant in enumerate(self.participant_data):
                participant["race_position"] = i + 1
    
    def generate_api_data(self) -> Dict[str, Any]:
        """Generate AMS2 API format data"""
        
        # Build participants array - ONLY if participants are active
        participants_array = []
        if self.participants_active:
            for i, p in enumerate(self.participant_data):
                participant = {
                    "mIsActive": True,
                    "mName": p["name"],
                    "mWorldPosition": [
                        random.uniform(-400, 400),
                        random.uniform(10, 50),
                        random.uniform(-700, 700)
                    ],
                    "mCurrentLapDistance": p["lap_distance"],
                    "mRacePosition": p["race_position"],
                    "mLapsCompleted": p["laps_completed"],
                    "mCurrentLap": p["current_lap"],
                    "mCurrentSector": p["current_sector"],
                    "mRaceStates": self.race_state,
                    "mPitModes": 0,
                    "mFastestLapTimes": p["best_lap_time"],
                    "mLastLapTimes": p["last_lap_time"],
                    "mFastestSector1Times": -1,
                    "mFastestSector2Times": -1,
                    "mFastestSector3Times": -1,
                    "mCurrentSector1Times": random.uniform(30, 50),
                    "mCurrentSector2Times": random.uniform(45, 60),
                    "mCurrentSector3Times": -1,
                    "mLapsInvalidated": 0,
                    "mOrientations": [
                        random.uniform(-0.1, 0.1),
                        random.uniform(-3.14, 3.14),
                        random.uniform(-0.1, 0.1)
                    ],
                    "mSpeeds": p["speed"],
                    "mCarNames": p["car_name"],
                    "mCarClassNames": p["car_class"],
                    "mPitSchedules": 0,
                    "mHighestFlagColours": 0,
                    "mHighestFlagReasons": 0,
                    "mNationalities": 0
                }
                participants_array.append(participant)
        
        # Main API structure
        api_data = {
            "buildinfo": {
                "mVersion": 14,
                "mBuildVersionNumber": 2913
            },
            "gameStates": {
                "mGameState": self.game_state,
                "mSessionState": self.session_state,
                "mSessionIsPrivate": 0,
                "mRaceState": self.race_state
            },
            "participants": {
                "mViewedParticipantIndex": 0 if self.participants_active else -1,
                "mNumParticipants": len(participants_array) if self.participants_active else -1,  # -1 if no participants = no race
                "mParticipantInfo": participants_array
            },
            "unfilteredInput": {
                "mUnfilteredThrottle": 0,
                "mUnfilteredBrake": 0,
                "mUnfilteredSteering": random.uniform(-0.1, 0.1),
                "mUnfilteredClutch": 0,
                "mJoyPad0": 0,
                "mDPad": 0
            },
            "vehicleInformation": {
                "mCarName": "Il Tempo Gigante",
                "mCarClassName": "Flaaklypa"
            },
            "eventInformation": {
                "mLapsInEvent": self.track_info.get("laps_in_event", 101),
                "mSessionDuration": self.session_duration,
                "mSessionAdditionalLaps": 1,
                "mTrackLocation": self.track_info.get("track_location", "Watkins_Glen"),
                "mTrackVariation": self.track_info.get("track_variation", "Watkins_Glen_GP"),
                "mTrackLength": self.track_info.get("track_length", 5440.27),
                "mTranslatedTrackLocation": self.track_info.get("translated_location", "Watkins Glen"),
                "mTranslatedTrackVariation": self.track_info.get("translated_variation", "Watkins Glen GP")
            },
            "timings": {
                "mLapInvalidated": False,
                "mBestLapTime": -1,
                "mLastLapTime": -1,
                "mCurrentTime": self.race_time,
                "mSplitTimeAhead": random.uniform(0, 60) if self.participants_active else 0,
                "mSplitTimeBehind": -1,
                "mSplitTime": random.uniform(30, 50) if self.participants_active else 0,
                "mEventTimeRemaining": -1,
                "mPersonalFastestLapTime": -1,
                "mWorldFastestLapTime": -1,
                "mCurrentSector1Time": random.uniform(30, 50) if self.participants_active else 0,
                "mCurrentSector2Time": random.uniform(45, 60) if self.participants_active else 0,
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
            },
            "flags": {
                "mHighestFlagColour": 0,
                "mHighestFlagReason": 0,
                "mYellowFlagState": 0
            },
            "pitInfo": {
                "mPitMode": 0,
                "mPitSchedule": 0,
                "mEnforcedPitStopLap": 0
            },
            "carState": {
                "mCarFlags": 2,
                "mOilTempCelsius": random.uniform(110, 125) if self.participants_active else 20,
                "mWaterTempCelsius": random.uniform(105, 120) if self.participants_active else 20,
                "mWaterPressureKPa": random.uniform(50, 65) if self.participants_active else 0,
                "mFuelPressureKPa": 58.5 if self.participants_active else 0,
                "mFuelLevel": self.participant_data[0]["fuel_level"] if self.participants_active and self.participant_data else 0,
                "mFuelCapacity": 77,
                "mSpeed": self.participant_data[0]["speed"] if self.participants_active and self.participant_data else 0,
                "mRpm": random.uniform(1500, 8000) if self.participants_active else 0,
                "mMaxRPM": 8500,
                "mBrake": random.uniform(0, 0.1) if self.participants_active else 0,
                "mThrottle": random.uniform(0.3, 1.0) if self.race_state == 2 else 0,
                "mClutch": random.choice([0, 1]) if self.participants_active else 1,
                "mSteering": random.uniform(-0.1, 0.1) if self.participants_active else 0,
                "mGear": random.randint(1, 6) if self.race_state == 2 else 0,
                "mNumGears": 6,
                "mOdometerKM": random.uniform(200, 300) if self.participants_active else 0,
                "mAntiLockActive": False,
                "mLastOpponentCollisionIndex": -1,
                "mLastOpponentCollisionMagnitude": 0,
                "mBoostActive": False,
                "mBoostAmount": 0,
                "mEngineSpeed": random.uniform(180, 200) if self.participants_active else 0,
                "mEngineTorque": random.uniform(1e-10, 1e-8) if self.participants_active else 0,
                "mWings": [0, 0],
                "mHandBrake": 0,
                "mBrakeBias": 0.37,
                "mTurboBoostPressure": random.uniform(13000, 15000) if self.participants_active else 0,
                "mDrsState": 0,
                "mAntiLockSetting": 8,
                "mTractionControlSetting": 8,
                "mErsDeploymentMode": 0,
                "mErsAutoModeEnabled": 0,
                "mClutchTemp": random.uniform(350, 400) if self.participants_active else 20,
                "mClutchWear": 0,
                "mClutchOverheated": 0,
                "mClutchSlipping": 0,
                "mLaunchStage": -1
            },
            "motionAndDeviceRelated": {
                "mOrientation": [
                    random.uniform(-0.1, 0.1) if self.participants_active else 0,
                    random.uniform(-3.14, 3.14) if self.participants_active else 0,
                    random.uniform(-0.1, 0.1) if self.participants_active else 0
                ],
                "mLocalVelocity": [
                    random.uniform(-0.001, 0.001) if self.participants_active else 0,
                    random.uniform(-0.001, 0.001) if self.participants_active else 0,
                    random.uniform(-0.001, 0.001) if self.participants_active else 0
                ],
                "mWorldVelocity": [0, 0, 0],
                "mAngularVelocity": [
                    random.uniform(-0.001, 0.001) if self.participants_active else 0,
                    random.uniform(-0.001, 0.001) if self.participants_active else 0,
                    random.uniform(-0.001, 0.001) if self.participants_active else 0
                ],
                "mLocalAcceleration": [
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0
                ],
                "mWorldAcceleration": [
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0
                ],
                "mExtentsCentre": [0, 1.20686, 0.119275]
            },
            "wheelsAndTyres": {
                "mTyreFlags": [7, 7, 7, 7] if self.participants_active else [0, 0, 0, 0],
                "mTerrain": [0, 0, 0, 0],
                "mTyreY": [
                    random.uniform(0.03, 0.04) if self.participants_active else 0,
                    random.uniform(0.03, 0.04) if self.participants_active else 0,
                    random.uniform(0.03, 0.04) if self.participants_active else 0,
                    random.uniform(0.03, 0.04) if self.participants_active else 0
                ],
                "mTyreRPS": [
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0
                ],
                "mTyreSlipSpeed": [
                    random.uniform(0, 0.005) if self.participants_active else 0,
                    random.uniform(0, 0.005) if self.participants_active else 0,
                    random.uniform(0, 0.005) if self.participants_active else 0,
                    random.uniform(0, 0.005) if self.participants_active else 0
                ],
                "mTyreTemp": [
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20
                ],
                "mTyreTempLeft": [
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20
                ],
                "mTyreTempCenter": [
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20
                ],
                "mTyreTempRight": [
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20,
                    random.uniform(30, 40) if self.participants_active else 20
                ],
                "mTyreGrip": [
                    random.uniform(0.99, 1.0) if self.participants_active else 0,
                    random.uniform(0.99, 1.0) if self.participants_active else 0,
                    random.uniform(0.99, 1.0) if self.participants_active else 0,
                    random.uniform(0.99, 1.0) if self.participants_active else 0
                ],
                "mTyreHeightAboveGround": [
                    random.uniform(-0.02, 0) if self.participants_active else 0,
                    random.uniform(-0.02, 0) if self.participants_active else 0,
                    random.uniform(-0.02, 0) if self.participants_active else 0,
                    random.uniform(-0.02, 0) if self.participants_active else 0
                ],
                "mTyreLateralStiffness": [0, 0, 0, 0],
                "mTyreWear": [
                    random.uniform(0, 0.00001) if self.participants_active else 0,
                    random.uniform(0, 0.00001) if self.participants_active else 0,
                    random.uniform(0, 0.00001) if self.participants_active else 0,
                    random.uniform(0, 0.00001) if self.participants_active else 0
                ],
                "mBrakeDamage": [0, 0, 0, 0],
                "mSuspensionDamage": [0, 0, 0, 0],
                "mBrakeTempCelsius": [
                    random.uniform(40, 70) if self.participants_active else 20,
                    random.uniform(40, 70) if self.participants_active else 20,
                    random.uniform(40, 70) if self.participants_active else 20,
                    random.uniform(40, 70) if self.participants_active else 20
                ],
                "mTyreTreadTemp": [
                    random.uniform(300, 320) if self.participants_active else 200,
                    random.uniform(300, 320) if self.participants_active else 200,
                    random.uniform(300, 320) if self.participants_active else 200,
                    random.uniform(300, 320) if self.participants_active else 200
                ],
                "mTyreLayerTemp": [
                    random.uniform(300, 320) if self.participants_active else 200,
                    random.uniform(300, 320) if self.participants_active else 200,
                    random.uniform(300, 320) if self.participants_active else 200,
                    random.uniform(300, 320) if self.participants_active else 200
                ],
                "mTyreCarcassTemp": [
                    random.uniform(310, 330) if self.participants_active else 200,
                    random.uniform(310, 330) if self.participants_active else 200,
                    random.uniform(310, 330) if self.participants_active else 200,
                    random.uniform(310, 330) if self.participants_active else 200
                ],
                "mTyreRimTemp": [
                    random.uniform(320, 340) if self.participants_active else 200,
                    random.uniform(320, 340) if self.participants_active else 200,
                    random.uniform(320, 340) if self.participants_active else 200,
                    random.uniform(320, 340) if self.participants_active else 200
                ],
                "mTyreInternalAirTemp": [
                    random.uniform(315, 335) if self.participants_active else 200,
                    random.uniform(315, 335) if self.participants_active else 200,
                    random.uniform(315, 335) if self.participants_active else 200,
                    random.uniform(315, 335) if self.participants_active else 200
                ],
                "mWheelLocalPositionY": [
                    random.uniform(-0.15, -0.1) if self.participants_active else 0,
                    random.uniform(-0.15, -0.1) if self.participants_active else 0,
                    random.uniform(-0.1, -0.04) if self.participants_active else 0,
                    random.uniform(-0.1, -0.04) if self.participants_active else 0
                ],
                "mSuspensionTravel": [
                    random.uniform(0.08, 0.1) if self.participants_active else 0,
                    random.uniform(0.08, 0.1) if self.participants_active else 0,
                    random.uniform(0.08, 0.1) if self.participants_active else 0,
                    random.uniform(0.08, 0.1) if self.participants_active else 0
                ],
                "mSuspensionVelocity": [
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0,
                    random.uniform(-0.01, 0.01) if self.participants_active else 0
                ],
                "mRideHeight": [
                    random.uniform(14, 17) if self.participants_active else 0,
                    random.uniform(14, 17) if self.participants_active else 0,
                    random.uniform(14, 17) if self.participants_active else 0,
                    random.uniform(14, 17) if self.participants_active else 0
                ],
                "mAirPressure": [
                    random.uniform(160, 180) if self.participants_active else 0,
                    random.uniform(160, 180) if self.participants_active else 0,
                    random.uniform(160, 180) if self.participants_active else 0,
                    random.uniform(160, 180) if self.participants_active else 0
                ],
                "mTyreCompound": ["Slick", "Slick", "Slick", "Slick"] if self.participants_active else ["", "", "", ""]
            },
            "carDamage": {
                "mCrashState": 0,
                "mAeroDamage": 0,
                "mEngineDamage": random.uniform(0, 0.01) if self.participants_active else 0
            },
            "weather": {
                "mAmbientTemperature": random.uniform(20, 30),
                "mTrackTemperature": random.uniform(25, 40),
                "mRainDensity": 0,
                "mWindSpeed": random.uniform(0, 5),
                "mWindDirectionX": random.uniform(-1, 1),
                "mWindDirectionY": random.uniform(-1, 1),
                "mCloudBrightness": 2,
                "mSnowDensity": 0
            },
            "timestamp": int(time.time() * 1000)
        }
        
        return api_data

class APISimulationManager:
    """Manages multiple race simulations focused on participant-based detection"""
    
    def __init__(self, output_dir: str = "api_files"):
        self.output_dir = output_dir
        self.simulators = {}
        self.running = False
        self.update_interval = 1.0  # seconds
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Pre-defined racing scenarios
        self.scenarios = self.create_scenarios()
    
    def create_scenarios(self) -> Dict[str, Dict]:
        """Create different racing scenarios for testing participant-based detection"""
        return {
            # Same race across multiple IPs (participant matching test)
            "shared_race_1": {
                "participants": ["Marcus", "Dave Stephenson", "Gregory Boundy", "Rob Thompson"],
                "track": {
                    "track_location": "Watkins_Glen",
                    "track_variation": "Watkins_Glen_GP", 
                    "translated_location": "Watkins Glen",
                    "translated_variation": "Watkins Glen GP",
                    "track_length": 5440.27,
                    "laps_in_event": 25
                }
            },
            "shared_race_2": {
                "participants": ["Giancarlo Rampanelli", "Lee Chorley", "Ilya Malyuev", "Jose Lopez"],
                "track": {
                    "track_location": "Brands_Hatch",
                    "track_variation": "Brands_Hatch_GP",
                    "translated_location": "Brands Hatch", 
                    "translated_variation": "Brands Hatch GP",
                    "track_length": 3916.0,
                    "laps_in_event": 30
                }
            },
            "shared_race_3": {
                "participants": ["Thiago Izequiel", "Fernando Santos", "Carlos Rodriguez", "Miguel Fernandez"],
                "track": {
                    "track_location": "Silverstone",
                    "track_variation": "Silverstone_GP",
                    "translated_location": "Silverstone",
                    "translated_variation": "Silverstone GP", 
                    "track_length": 5891.0,
                    "laps_in_event": 20
                }
            },
            # Single driver races
            "solo_race_1": {
                "participants": ["John Smith"],
                "track": {
                    "track_location": "Spa_Francorchamps",
                    "track_variation": "Spa_Francorchamps_GP",
                    "translated_location": "Spa-Francorchamps",
                    "translated_variation": "Spa-Francorchamps GP",
                    "track_length": 7004.0,
                    "laps_in_event": 15
                }
            },
            "solo_race_2": {
                "participants": ["Jane Doe"],
                "track": {
                    "track_location": "Monza",
                    "track_variation": "Monza_GP",
                    "translated_location": "Monza",
                    "translated_variation": "Monza GP",
                    "track_length": 5793.0,
                    "laps_in_event": 18
                }
            }
        }
    
    def setup_scenario(self, scenario_name: str, start_ip: int = 201, count: int = 1):
        """Setup a specific scenario across multiple IPs"""
        if scenario_name not in self.scenarios:
            print(f"Unknown scenario: {scenario_name}")
            return
            
        scenario = self.scenarios[scenario_name]
        
        for i in range(count):
            ip = f"192.168.3.{start_ip + i}"
            simulator = RaceSimulator(ip, scenario["participants"], scenario["track"])
            self.simulators[ip] = simulator
            print(f"Setup {scenario_name} on {ip} with participants: {scenario['participants']}")
    
    def setup_test_environment(self):
        """Setup comprehensive test environment for participant-based detection"""
        print("Setting up Participant-Based API simulation test environment...")
        
        # Scenario 1: Same race on 3 IPs (test participant matching)
        self.setup_scenario("shared_race_1", start_ip=201, count=3)
        
        # Scenario 2: Different race on 2 IPs  
        self.setup_scenario("shared_race_2", start_ip=204, count=2)
        
        # Scenario 3: Another different race on 2 IPs
        self.setup_scenario("shared_race_3", start_ip=206, count=2)
        
        # Scenario 4: Single driver races
        self.setup_scenario("solo_race_1", start_ip=208, count=1)
        self.setup_scenario("solo_race_2", start_ip=209, count=1)
        
        # Additional mixed scenarios for stress testing
        self.setup_scenario("shared_race_1", start_ip=210, count=2)  # Same race as 201-203
        
        print(f"Setup complete! Created {len(self.simulators)} race simulators")
        print("Available IPs:", sorted(self.simulators.keys()))
        print("NOTE: Use join_race() and leave_race() to control participant presence!")
    
    def join_race(self, ip: str):
        """Participants join race on specific IP (RACE DETECTED)"""
        if ip in self.simulators:
            self.simulators[ip].set_participants_active(True)
    
    def leave_race(self, ip: str):
        """Participants leave race on specific IP (RACE ENDED)"""
        if ip in self.simulators:
            self.simulators[ip].set_participants_active(False)
    
    def start_racing(self, ip: str):
        """Start actual racing (green light) on specific IP"""
        if ip in self.simulators:
            self.simulators[ip].start_racing()
    
    def finish_race(self, ip: str):
        """Finish race (results screen) on specific IP"""
        if ip in self.simulators:
            self.simulators[ip].finish_race()
    
    def join_all_races(self):
        """Participants join all races"""
        for ip in self.simulators:
            self.join_race(ip)
    
    def leave_all_races(self):
        """Participants leave all races"""
        for ip in self.simulators:
            self.leave_race(ip)
    
    def start_all_racing(self):
        """Start racing (green light) on all IPs"""
        for ip in self.simulators:
            self.start_racing(ip)
    
    def start_simulation(self):
        """Start the simulation update loop"""
        self.running = True
        print("Starting participant-based API simulation...")
        
        def update_loop():
            last_time = time.time()
            while self.running:
                current_time = time.time()
                delta_time = current_time - last_time
                last_time = current_time
                
                # Update all simulators
                for simulator in self.simulators.values():
                    simulator.update_race(delta_time)
                
                # Generate API files
                self.generate_api_files()
                
                time.sleep(self.update_interval)
        
        self.update_thread = threading.Thread(target=update_loop, daemon=True)
        self.update_thread.start()
        print("Simulation started!")
    
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False
        print("Simulation stopped!")
    
    def generate_api_files(self):
        """Generate API JSON files for all simulators"""
        for ip, simulator in self.simulators.items():
            api_data = simulator.generate_api_data()
            filename = os.path.join(self.output_dir, f"{ip}.json")
            
            try:
                with open(filename, 'w') as f:
                    json.dump(api_data, f, indent=2)
            except Exception as e:
                print(f"Error writing API file for {ip}: {e}")
    
    def get_simulator_status(self):
        """Get status of all simulators"""
        status = {}
        for ip, sim in self.simulators.items():
            status[ip] = {
                "participants_active": sim.participants_active,
                "game_state": sim.game_state,
                "race_state": sim.race_state,
                "participants": len(sim.participants),
                "race_time": sim.race_time,
                "participant_names": [p["name"] for p in sim.participant_data]
            }
        return status
    
    def print_status(self):
        """Print current status of all simulators"""
        print("\n=== Participant-Based API Simulation Status ===")
        status = self.get_simulator_status()
        for ip, info in status.items():
            active_str = "RACE ACTIVE" if info['participants_active'] else "NO RACE"
            game_states = f"G:{info['game_state']},R:{info['race_state']}"
            print(f"{ip}: {active_str} | {game_states} | {info['participants']} drivers | {info['race_time']:.1f}s | {info['participant_names']}")
        print("=" * 50)

def main():
    """Main function for testing the participant-based API simulator"""
    print("AMS2 Participant-Based API Simulation Environment")
    print("=" * 50)
    print("KEY: Race detection based on PARTICIPANT PRESENCE, not game states!")
    print("=" * 50)
    
    # Create simulation manager
    sim_manager = APISimulationManager()
    
    # Setup test environment
    sim_manager.setup_test_environment()
    
    # Start simulation
    sim_manager.start_simulation()
    
    try:
        while True:
            print("\nParticipant-Based API Simulator Commands:")
            print("1. Join all races (participants present = RACE DETECTED)")
            print("2. Leave all races (no participants = NO RACE)")
            print("3. Join specific race (enter IP)")
            print("4. Leave specific race (enter IP)") 
            print("5. Start racing (green light) on all")
            print("6. Show status")
            print("7. Stop simulation")
            
            choice = input("Enter choice (1-7): ").strip()
            
            if choice == "1":
                sim_manager.join_all_races()
                print("All participants joined races - RACES DETECTED!")
                
            elif choice == "2":
                sim_manager.leave_all_races()
                print("All participants left races - NO RACES!")
                
            elif choice == "3":
                ip = input("Enter IP (e.g., 192.168.3.201): ").strip()
                sim_manager.join_race(ip)
                print(f"Participants joined race on {ip} - RACE DETECTED!")
                
            elif choice == "4":
                ip = input("Enter IP (e.g., 192.168.3.201): ").strip()
                sim_manager.leave_race(ip)
                print(f"Participants left race on {ip} - RACE ENDED!")
                
            elif choice == "5":
                sim_manager.start_all_racing()
                print("Green light on all races!")
                
            elif choice == "6":
                sim_manager.print_status()
                
            elif choice == "7":
                sim_manager.stop_simulation()
                break
                
            else:
                print("Invalid choice!")
                
    except KeyboardInterrupt:
        print("\nShutting down simulation...")
        sim_manager.stop_simulation()

if __name__ == "__main__":
    main()
