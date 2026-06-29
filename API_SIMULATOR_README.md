# AMS2 API Simulation Environment

## Overview
This simulation environment creates realistic AMS2 API data files for testing the multi-race monitoring system **without needing 20 actual racing simulators**. It focuses on **participant-based race detection** methodology.

## Key Principle
**Race detection uses PARTICIPANT PRESENCE, not game states!**
- `mNumParticipants > 0` = Race is active
- `mNumParticipants = -1` = No race (outside of race)
- Game states are for UI/status display only

## Files

### `api_simulator.py`
Main simulation engine that creates realistic AMS2 API JSON files.

**Key Classes:**
- `RaceSimulator`: Simulates a single race instance
- `APISimulationManager`: Manages multiple race simulations

**Key Methods:**
- `join_race(ip)`: Participants join race (RACE DETECTED)
- `leave_race(ip)`: Participants leave race (RACE ENDED)
- `start_racing(ip)`: Green light starts
- `finish_race(ip)`: Results screen

### `test_scenarios.py`
Comprehensive test scenarios for participant-based race detection.

**Test Scenarios:**
1. **Participant Matching**: Same participants across multiple IPs
2. **Different Races**: Different participants = different races
3. **Race Lifecycle**: Join → Race → Leave sequence
4. **Stress Testing**: Multiple simultaneous races
5. **Game States vs Participants**: Verification of detection method

## Quick Start

### Basic Usage
```python
from api_simulator import APISimulationManager

# Create simulator
sim = APISimulationManager()

# Setup test environment (multiple races across 10+ IPs)
sim.setup_test_environment()

# Start generating API files
sim.start_simulation()

# Join participants to races (triggers race detection)
sim.join_all_races()

# Start racing (green light)
sim.start_all_racing()

# Check status
sim.print_status()
```

### Manual Control
```python
# Join specific race
sim.join_race("10.0.0.201")  # Race detected on this IP

# Leave specific race  
sim.leave_race("10.0.0.201")  # Race ends on this IP

# Start racing on specific IP
sim.start_racing("10.0.0.201")
```

### Run Test Suite
```bash
python test_scenarios.py
```

## Race Scenarios

### Default Test Environment
- **IPs 10.0.0.201-203**: Same race (Marcus, Dave, Gregory, Rob) - *Session assignment test*
- **IPs 10.0.0.204-205**: Different races - *Multi-race detection test*
- **IPs 10.0.0.206-207**: Another different race - *Additional session test*
- **IPs 10.0.0.208-209**: Solo races - *Single driver test*
- **IPs 10.0.0.210-211**: Additional same race - *Cross-IP participant matching*

### API File Generation
Files are generated in `api_files/` directory:
- `10.0.0.201.json`, `10.0.0.202.json`, etc.
- Updated every 1 second while simulation runs
- Realistic AMS2 telemetry data structure

## Game State Values (For Reference Only)

**Game States (mGameState):**
- `1`: Lobby/Frontend
- `2`: Race in progress
- `4`: Menu/Waiting for go/Results

**Race States (mRaceState):**
- `0`: Lobby
- `1`: Waiting for green light
- `2`: Green light (racing)
- `3`: Results screen

**Session States (mSessionState):**
- `0`: Lobby
- `5`: Game in progress

## Important Notes

### Race Detection Logic
```python
# CORRECT: Use participant presence
race_active = api_data["participants"]["mNumParticipants"] > 0

# WRONG: Don't use game states for race detection
# race_active = api_data["gameStates"]["mGameState"] == 2  # NO!
```

### Session Assignment Logic
```python
# Group races by participant signature
participant_names = sorted([p["mName"] for p in participants])
session_signature = tuple(participant_names)

# Same signature = same race across multiple IPs
# Different signature = different race
```

### Realistic Features
- Accurate telemetry values (speed, lap times, fuel, temperatures)
- Proper track lengths and lap counts
- Realistic participant progression
- Correct game state transitions (for authenticity)
- Dynamic fuel consumption and lap completion

## Testing Multi-Race Monitoring

### Enhanced Session Assignment
1. Start simulation with multiple races
2. Join participants on various IPs
3. Verify session assignment groups IPs correctly by participant signature
4. Test handling of 1-4+ active sessions

### Race State Detection
1. Verify no race detected when mNumParticipants = 0
2. Verify race detected when mNumParticipants > 0
3. Test race lifecycle: join → racing → results → leave
4. Confirm game states don't affect race detection

### Performance Testing
1. Run with 10-15 simultaneous simulated races
2. Verify accurate session assignment under load
3. Test rapid participant joining/leaving
4. Monitor file I/O performance

## Console Commands

When running `api_simulator.py` directly:
1. **Join all races**: All participants join (races detected)
2. **Leave all races**: All participants leave (no races)
3. **Join specific race**: Enter IP address
4. **Leave specific race**: Enter IP address
5. **Start racing**: Green light on all races
6. **Show status**: Display current state
7. **Stop simulation**: Exit

## Integration with RaceMonitor

The generated API files can be used by RaceMonitor_v1.7.0.py for testing:
1. Point RaceMonitor to read from `api_files/` directory
2. Configure IP scanning to include simulated IPs (10.0.0.201-211)
3. Test enhanced session assignment with realistic multi-race scenarios
4. Verify participant-based race detection works correctly

This simulation environment allows comprehensive testing of the multi-race monitoring system without requiring multiple physical racing setups.
