# AMS2 Race Monitor - Testmode & API Simulation Guide

## Overview
The testmode feature allows you to test the multi-race monitoring system without needing 20 actual AMS2 racing simulators. It uses simulated API data files to recreate realistic racing scenarios.

## Key Features
- **Participant-Based Race Detection**: Uses `mNumParticipants` for race detection (-1 = no race, >0 = race active)
- **Multi-Race Simulation**: Test up to 10+ concurrent races across different IPs
- **Enhanced Session Assignment**: Test automatic session assignment logic
- **Realistic Data**: Simulated lap times, positions, car telemetry, and race states

## Quick Start

### 1. Enable Testmode
Edit `config.ini`:
```ini
testmode = True
```

### 2. Start API Simulator
```bash
# Option 1: Use batch file
Start_API_Simulator.bat

# Option 2: Run directly
python api_simulator.py
```

### 3. Run Race Monitor
```bash
python RaceMonitor_v1.7.0.py
```

### 4. Test Scenarios
The simulator will show a menu to control race states:
- Join/leave races (participant presence = race detection)
- Start racing (green light)
- View status of all simulated races

## Understanding Participant-Based Detection

### Critical Concept
**Race detection is based on PARTICIPANT PRESENCE, not game states!**

- `mNumParticipants = -1` → No race active
- `mNumParticipants > 0` → Race active (participants present)
- Game states are for UI/status display only

### Example API Data
```json
{
  "participants": {
    "mNumParticipants": 4,  // ← RACE DETECTED (4 participants)
    "mParticipantInfo": [   // ← Participant array populated
      {"mName": "Marcus", "mRacePosition": 1},
      {"mName": "Dave", "mRacePosition": 2},
      // ... more participants
    ]
  },
  "gameStates": {
    "mGameState": 2,        // ← Game states for display only
    "mRaceState": 2,        // ← Not used for race detection
    "mSessionState": 5
  }
}
```

## Pre-defined Test Scenarios

### Shared Races (Participant Matching)
- **IPs 10.0.0.201-203**: Same 4 participants (Marcus, Dave, Gregory, Rob)
- **IPs 10.0.0.204-205**: Same 4 participants (Giancarlo, Lee, Ilya, Jose)
- **IPs 10.0.0.206-207**: Same 4 participants (Thiago, Fernando, Carlos, Miguel)

### Individual Races
- **IP 10.0.0.208**: Solo race (John Smith)
- **IP 10.0.0.209**: Solo race (Jane Doe)
- **IP 10.0.0.210-211**: Additional shared race (same as 201-203)

## Simulator Controls

### 1. Join All Races
All participants join → All races detected

### 2. Leave All Races  
All participants leave → No races detected

### 3. Join Specific Race
Enter IP → Participants join that specific race

### 4. Start Racing
Green light on all active races

### 5. Show Status
View current state of all simulated races

## Testing Procedures

### Test 1: No Races Detected
1. Start simulator (default: no participants)
2. All API files show `mNumParticipants: -1`
3. RaceMonitor shows no active races

### Test 2: Single Race Detection
1. Join race on specific IP (e.g., 10.0.0.201)
2. Only that IP shows `mNumParticipants: 4`
3. RaceMonitor detects one active race

### Test 3: Multiple Independent Races
1. Join races on different IPs with different participants
2. Each IP shows different participant signatures
3. RaceMonitor detects multiple separate races

### Test 4: Shared Race Detection
1. Join same race on multiple IPs (e.g., 201-203)
2. All show same participants
3. RaceMonitor groups them as one race session

### Test 5: Race State Transitions
1. Join race → Participants present
2. Start racing → Green light
3. Finish race → Results screen (participants still present)
4. Leave race → No participants

## Configuration Files

### config.ini Settings
```ini
[DEFAULT]
ip_address = 10.0.0.201
session_id = 1
testmode = True  # ← Enable/disable testmode

# Other settings...
track_variation = Watkins_Glen_GP
```

### API File Structure
Files created in `api_files/` directory:
- `10.0.0.201.json` - API data for IP 201
- `10.0.0.202.json` - API data for IP 202
- etc.

## Enhanced Session Assignment Testing

### Scenario 1: 1-3 Active Races
- **Expected**: Automatically assigned to session_id = 1
- **Test**: Join 1-3 different races, verify single session

### Scenario 2: 4+ Active Races  
- **Expected**: New sessions created as needed
- **Test**: Join 4+ races, verify multiple sessions

### Database Integration
- Sessions track active races
- Participants matched by signature
- Race data isolated by session_id

## Troubleshooting

### Common Issues

1. **Testmode not working**
   - Check `config.ini`: `testmode = True`
   - Verify `api_files/` directory exists
   - Check file permissions

2. **No races detected**
   - Ensure `mNumParticipants > 0` in API files
   - Check participant array is populated
   - Verify IP address matches filename

3. **API simulator crashes**
   - Check Python dependencies
   - Verify write permissions for `api_files/`
   - Review error messages

### Debug Steps
1. Check `debug.log` for testmode messages
2. Verify API files are being created/updated
3. Monitor console output for state changes
4. Use test scenarios to isolate issues

## Advanced Usage

### Custom Scenarios
Edit `api_simulator.py` to create custom scenarios:
```python
"custom_race": {
    "participants": ["Driver1", "Driver2"],
    "track": {
        "track_location": "Custom_Track",
        "track_length": 5000.0,
        "laps_in_event": 20
    }
}
```

### Multiple IP Testing
1. Change `ip_address` in config.ini
2. Restart RaceMonitor
3. Different IP loads different simulated race
4. Test IP switching behavior

### Stress Testing
1. Start all 10+ races simultaneously
2. Rapid join/leave cycles
3. Monitor memory usage and performance
4. Test edge cases and error handling

## Integration with Real AMS2

### Switching Between Modes
```ini
# Testing with simulation
testmode = True

# Racing with real AMS2
testmode = False
```

### Hybrid Testing
1. Test logic with simulated data
2. Validate with real AMS2 when available
3. Compare behavior between modes
4. Ensure consistent race detection

## API Data Format Reference

### Key Fields for Race Detection
```json
{
  "participants": {
    "mNumParticipants": -1,        // -1 = no race, >0 = race active
    "mViewedParticipantIndex": -1, // -1 = no participants
    "mParticipantInfo": []         // Empty = no race, populated = active race
  }
}
```

### Participant Signature Format
Used for matching races across multiple IPs:
```
"Marcus|Dave Stephenson|Gregory Boundy|Rob Thompson"
```

### Game States (Display Only)
```json
{
  "gameStates": {
    "mGameState": 1,    // 1=Lobby, 2=Racing, 4=Menu/Results
    "mSessionState": 0, // 0=Lobby, 1=Practice, 3=Qualify, 5=Race
    "mRaceState": 0     // 0=Lobby, 1=Wait, 2=Racing, 3=Results
  }
}
```

## Performance Considerations

### File I/O
- API files updated every 1 second
- JSON parsing optimized for speed
- Error handling prevents crashes

### Memory Usage
- Minimal memory footprint
- Data structures cleaned up properly
- No memory leaks in long-running tests

### CPU Usage
- Efficient simulation algorithms
- Background threading
- Minimal impact on RaceMonitor performance

## Support & Development

### File Structure
```
AMS2_RaceScore/
├── api_simulator.py          # Main simulation engine
├── test_scenarios.py         # Comprehensive test suite
├── Start_API_Simulator.bat   # Easy launcher
├── api_files/               # Generated API data files
│   ├── 10.0.0.201.json
│   ├── 10.0.0.202.json
│   └── ...
├── RaceMonitor_v1.7.0.py    # Main race monitor (testmode enabled)
└── config.ini               # Configuration (testmode setting)
```

### Development Notes
- Participant presence = race detection method
- Enhanced session assignment implemented in v1.7.0
- Backward compatible with existing functionality
- Extensive error handling and logging

This testmode system provides comprehensive testing capabilities for the multi-race monitoring system without requiring multiple physical racing setups.
