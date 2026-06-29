# 🏁 AMS2 Race Monitor - Complete Testing Suite Guide

## Overview
This comprehensive testing suite allows you to test the enhanced multi-race monitoring system without needing actual racing simulators. The suite includes multiple tools for different testing scenarios.

## 🎯 What's Included

### 1. **Realistic Race Scenarios** (`realistic_race_scenarios.py`)
- **Purpose**: Test with real data from your existing RaceDB.db
- **Features**: 
  - Reads actual participant names, tracks, cars, and lap times
  - Creates 4 concurrent races with 6 laps each
  - Uses real performance data for authentic simulation
  - Tests participant-based race detection with your data

### 2. **General API Simulator** (`api_simulator.py`)
- **Purpose**: Generic simulation environment with predefined scenarios
- **Features**:
  - Up to 10+ concurrent races across different IPs
  - Participant-based race detection (mNumParticipants = -1 for no race)
  - Realistic AMS2 API format
  - Multiple test scenarios for stress testing

### 3. **Test Scenarios Suite** (`test_scenarios.py`)
- **Purpose**: Automated testing for race detection logic
- **Features**:
  - Comprehensive test cases for all race detection scenarios
  - Validates participant-based detection
  - Tests multi-race session assignment
  - Automated pass/fail results

### 4. **Enhanced RaceMonitor v1.7.0** with Testmode
- **Purpose**: Main race monitoring with testmode integration
- **Features**:
  - `testmode = True/False` configuration
  - Seamless switching between real AMS2 and simulated data
  - Enhanced session assignment logic
  - Participant-based race detection

## 🚀 Quick Start Guide

### Step 1: Choose Your Testing Approach

#### Option A: Test with Real Data (Recommended)
```bash
# Use your existing RaceDB.db data
Start_Realistic_Scenarios.bat
```

#### Option B: Test with Generic Scenarios
```bash
# Use predefined test scenarios
Start_API_Simulator.bat
```

#### Option C: Run Automated Tests
```bash
# Comprehensive automated testing
python test_scenarios.py
```

### Step 2: Enable Testmode
Edit `config.ini`:
```ini
[config]
testmode = True
```

### Step 3: Run RaceMonitor
```bash
python RaceMonitor_v1.7.0.py
```

## 📊 Testing Scenarios Explained

### Realistic Race Scenarios (Using RaceDB.db)

#### **What It Does:**
- Scans your RaceDB.db for real participant names, tracks, cars, and lap times
- Creates 4 authentic racing scenarios based on your actual data
- Simulates realistic lap times using historical performance data
- Tests the system with data that matches your actual racing environment

#### **Race Configuration:**
```
Race 1 (Championship): 4 participants on IPs 10.0.0.201-202
Race 2 (Sprint):       3 participants on IP 10.0.0.203  
Race 3 (Duel):         2 participants on IPs 10.0.0.204-205
Race 4 (Endurance):    3 participants on IP 10.0.0.206
```

#### **Example Output:**
```
📊 Found 12 real participants: Marcus, Dave Stephenson, Gregory Boundy...
🏁 Found 8 tracks: Watkins Glen - Watkins Glen GP, Brands Hatch - Brands Hatch GP...
🚗 Found 15 cars: Il Tempo Gigante, Formula X, GT3 Audi...
⏱️ Extracted lap time data for 47 driver/track/car combinations

🏁 Created Championship Race: [Marcus, Dave, Gregory, Rob] at Watkins_Glen
🏁 Created Sprint Race: [Giancarlo, Lee, Ilya] at Brands_Hatch
🏁 Created Duel Race: [Thiago, Fernando] at Silverstone
🏁 Created Endurance Race: [Carlos, Miguel, Jose] at Spa_Francorchamps
```

#### **Key Features:**
- **Real Performance Data**: Uses your actual lap times to calculate realistic performance
- **Driver Characteristics**: Each driver has unique speed and consistency based on history
- **Authentic Tracks**: Uses your actual track configurations and lengths
- **Realistic Progression**: 6-lap races with authentic timing progression

### Generic API Simulator

#### **What It Does:**
- Provides predefined racing scenarios for general testing
- Supports up to 10+ concurrent races
- Focuses on testing race detection logic and multi-race handling
- Great for stress testing and edge case validation

#### **Predefined Scenarios:**
```
Shared Race 1: Same 4 participants on IPs 201-203 (tests participant matching)
Shared Race 2: Same 4 participants on IPs 204-205 (tests grouping)
Shared Race 3: Same 4 participants on IPs 206-207 (tests multi-session)
Solo Races:    Individual drivers on IPs 208-209 (tests single driver races)
```

## 🎮 Interactive Commands

### Realistic Race Simulator Commands:
```
1. Join all races (participants present)     - All races become active
2. Leave all races (no participants)         - All races become inactive
3. Start all racing (GREEN LIGHT!)          - Begin actual racing
4. Join specific race (enter IP)            - Activate specific race
5. Show status and progress                  - View current race states
6. Generate API files                        - Create/update JSON files
7. Stop simulation                           - Exit simulator
```

### Generic API Simulator Commands:
```
1. Join all races (participants present = RACE DETECTED)
2. Leave all races (no participants = NO RACE)
3. Join specific race (enter IP)
4. Leave specific race (enter IP)
5. Start racing (green light) on all
6. Show status
7. Stop simulation
```

## 🔍 Understanding the Output

### Race Status Display:
```
REALISTIC RACE SIMULATION STATUS
===============================================

🏁 Championship Race (realistic_race_1)
   Status: RACING | IPs: ['10.0.0.201', '10.0.0.202'] | Active: ['10.0.0.201', '10.0.0.202']
   Track: Watkins Glen - Watkins Glen GP
   Car: Il Tempo Gigante
   Race Time: 245.3s
     Marcus: 2/6 laps | Best: 125.234
     Dave Stephenson: 2/6 laps | Best: 127.891
     Gregory Boundy: 1/6 laps | Best: 128.456
     Rob Thompson: 2/6 laps | Best: 126.789
```

### API File Generation:
- Files created in `api_files/` directory
- One JSON file per IP address (e.g., `10.0.0.201.json`)
- Files automatically updated during racing
- Compatible with RaceMonitor testmode

## 🧪 Testing Race Detection Logic

### Key Testing Points:

#### **1. Participant Presence = Race Detection**
```json
{
  "participants": {
    "mNumParticipants": 4,     // ← RACE ACTIVE (4 participants)
    "mParticipantInfo": [...]  // ← Populated array
  }
}
```

#### **2. No Participants = No Race**
```json
{
  "participants": {
    "mNumParticipants": -1,    // ← NO RACE (-1 indicates no participants)
    "mParticipantInfo": []     // ← Empty array
  }
}
```

#### **3. Participant Matching Across IPs**
- Same participants on multiple IPs = Same race session
- Different participants = Different race sessions
- System automatically groups races by participant signature

### Testing Workflow:

1. **Start with No Races**: All simulators show `mNumParticipants: -1`
2. **Join Specific Races**: Test individual race detection
3. **Join Multiple Races**: Test multi-race detection and grouping
4. **Start Racing**: Test race progression and lap timing
5. **Monitor Progress**: Verify lap completion and position updates
6. **Finish Races**: Test race completion handling

## 📈 Performance Monitoring

### What to Monitor:

#### **RaceMonitor Behavior:**
- Session assignment (1-4+ races should trigger appropriate sessions)
- Race detection accuracy (participant presence = race active)
- Multi-race handling (different races grouped correctly)
- Database updates (laps, participants, race data stored properly)

#### **API File Updates:**
- Files should update every 1-2 seconds during racing
- Participant data should progress realistically
- Lap times should be generated based on performance data
- Race states should transition correctly

#### **System Performance:**
- Memory usage should remain stable
- File I/O should not cause lag
- Multiple concurrent races should not affect performance
- Switching between testmode and real mode should be seamless

## 🔧 Configuration Options

### config.ini Settings:
```ini
[config]
ip_address = 10.0.0.201        # Which race to monitor
session_id = 1                 # Starting session ID
testmode = True                # Enable/disable simulation
```

### Simulator Settings:
- **Update Interval**: 1 second (configurable)
- **Max Laps**: 6 per race (as requested)
- **Max Concurrent Races**: 4 realistic / 10+ generic
- **Participant Limits**: 2-4 per race (realistic) / unlimited (generic)

## 🎯 Recommended Testing Sequence

### 1. **Initial Setup Test**
```bash
# Start realistic scenarios
Start_Realistic_Scenarios.bat

# Enable testmode
# Edit config.ini: testmode = True

# Start RaceMonitor
python RaceMonitor_v1.7.0.py
```

### 2. **Basic Race Detection Test**
- Join one race (verify single race detection)
- Join multiple races (verify multi-race detection)
- Test participant matching across IPs

### 3. **Racing Progression Test**
- Start racing on all active races
- Monitor lap progression for 6 laps
- Verify race completion handling

### 4. **Session Assignment Test**
- Test 1-3 races (should use session_id = 1)
- Test 4+ races (should create new sessions)
- Verify database storage

### 5. **Performance Test**
- Run all scenarios simultaneously
- Monitor system performance
- Test rapid join/leave cycles

### 6. **Real Data Comparison**
- Switch to real AMS2 (`testmode = False`)
- Compare behavior between simulated and real data
- Verify seamless mode switching

## 🐛 Troubleshooting

### Common Issues:

#### **No Race Detected**
- Check `mNumParticipants` in API files (should be > 0)
- Verify participants array is populated
- Ensure IP address matches filename

#### **API Files Not Updating**
- Check file permissions in `api_files/` directory
- Verify simulator is running and generating files
- Monitor console output for errors

#### **RaceMonitor Not Using Testmode**
- Verify `testmode = True` in config.ini
- Check that API files exist for current IP
- Review debug.log for testmode messages

#### **Performance Issues**
- Reduce number of concurrent races
- Increase update interval in simulator
- Monitor memory usage

### Debug Steps:
1. Check console output for error messages
2. Review `debug.log` for detailed information  
3. Verify API file contents with JSON validator
4. Test with single race before multiple races
5. Compare simulated vs real data formats

## 🎉 Success Indicators

You know the system is working correctly when:

✅ **Race Detection**: Participant presence correctly triggers race detection
✅ **Multi-Race Handling**: Multiple races detected and grouped appropriately  
✅ **Session Assignment**: Enhanced session logic assigns races to correct sessions
✅ **Data Integrity**: Lap times, positions, and race data stored accurately
✅ **Performance**: System handles multiple concurrent races smoothly
✅ **Seamless Switching**: Can switch between testmode and real mode without issues

## 🏆 Final Notes

This testing suite provides comprehensive coverage for the enhanced multi-race monitoring system. Using your real RaceDB.db data ensures authentic testing conditions that match your actual racing environment.

The combination of realistic scenarios, automated tests, and interactive simulators gives you confidence that the system will work correctly in production with actual AMS2 racing data.

Happy testing! 🏁
