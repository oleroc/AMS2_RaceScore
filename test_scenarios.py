#!/usr/bin/env python3
"""
Test Scenarios for Participant-Based Race Detection
Comprehensive testing for multi-race monitoring with proper participant detection logic.
"""

import time
import json
import os
from api_simulator import APISimulationManager

class TestScenarios:
    """Test scenarios for participant-based race detection system"""
    
    def __init__(self):
        self.sim_manager = APISimulationManager()
        self.test_results = {}
    
    def run_all_tests(self):
        """Run all test scenarios"""
        print("=" * 60)
        print("PARTICIPANT-BASED RACE DETECTION TEST SUITE")
        print("=" * 60)
        print("KEY: Race detection uses mNumParticipants (-1 = no race, >0 = race active)")
        print("=" * 60)
        
        tests = [
            self.test_no_races_detected,
            self.test_single_race_detection,
            self.test_multiple_races_detection,
            self.test_shared_race_detection,
            self.test_race_state_transitions,
            self.test_participant_matching,
            self.test_mixed_scenarios
        ]
        
        for test in tests:
            try:
                print(f"\n{'='*50}")
                print(f"Running: {test.__name__}")
                print(f"{'='*50}")
                test()
                self.test_results[test.__name__] = "PASSED"
                print(f"✅ {test.__name__} PASSED")
            except Exception as e:
                print(f"❌ {test.__name__} FAILED: {e}")
                self.test_results[test.__name__] = f"FAILED: {e}"
        
        self.print_test_summary()
    
    def test_no_races_detected(self):
        """Test: No races should be detected when no participants present"""
        print("Testing: No participants = No races detected")
        
        # Setup environment with no participants
        self.sim_manager.setup_test_environment()
        self.sim_manager.start_simulation()
        
        # Wait for files to generate
        time.sleep(2)
        
        # Check all files show mNumParticipants = -1
        api_files = self.get_api_files()
        for filename, data in api_files.items():
            participants = data.get("participants", {})
            num_participants = participants.get("mNumParticipants", 0)
            
            if num_participants != -1:
                raise AssertionError(f"{filename}: Expected mNumParticipants=-1, got {num_participants}")
            
            # Should have empty participant array
            participant_info = participants.get("mParticipantInfo", [])
            if len(participant_info) != 0:
                raise AssertionError(f"{filename}: Expected empty mParticipantInfo, got {len(participant_info)} entries")
        
        print(f"✓ All {len(api_files)} files correctly show no participants (mNumParticipants=-1)")
        self.sim_manager.stop_simulation()
    
    def test_single_race_detection(self):
        """Test: Single race detection with participants"""
        print("Testing: Single race with participants")
        
        self.sim_manager.setup_test_environment()
        self.sim_manager.start_simulation()
        
        # Join single race
        test_ip = "10.0.0.201"
        self.sim_manager.join_race(test_ip)
        
        time.sleep(2)
        
        # Check race is detected on specific IP
        api_files = self.get_api_files()
        race_detected = False
        
        for filename, data in api_files.items():
            participants = data.get("participants", {})
            num_participants = participants.get("mNumParticipants", -1)
            
            if filename.replace('.json', '') == test_ip:
                # This IP should have participants
                if num_participants <= 0:
                    raise AssertionError(f"{filename}: Expected participants >0, got {num_participants}")
                
                participant_info = participants.get("mParticipantInfo", [])
                if len(participant_info) != num_participants:
                    raise AssertionError(f"{filename}: Participant count mismatch")
                
                race_detected = True
                print(f"✓ Race detected on {filename}: {num_participants} participants")
            else:
                # Other IPs should have no participants
                if num_participants != -1:
                    raise AssertionError(f"{filename}: Expected no participants, got {num_participants}")
        
        if not race_detected:
            raise AssertionError("Race not detected on target IP")
        
        self.sim_manager.stop_simulation()
    
    def test_multiple_races_detection(self):
        """Test: Multiple separate races detection"""
        print("Testing: Multiple independent races")
        
        self.sim_manager.setup_test_environment()
        self.sim_manager.start_simulation()
        
        # Join races on multiple IPs
        test_ips = ["10.0.0.201", "10.0.0.204", "10.0.0.206"]
        for ip in test_ips:
            self.sim_manager.join_race(ip)
        
        time.sleep(2)
        
        # Check races detected on correct IPs
        api_files = self.get_api_files()
        races_detected = 0
        
        for filename, data in api_files.items():
            participants = data.get("participants", {})
            num_participants = participants.get("mNumParticipants", -1)
            ip = filename.replace('.json', '')
            
            if ip in test_ips:
                if num_participants <= 0:
                    raise AssertionError(f"{filename}: Expected participants, got {num_participants}")
                races_detected += 1
                print(f"✓ Race detected on {filename}: {num_participants} participants")
            else:
                if num_participants != -1:
                    raise AssertionError(f"{filename}: Expected no participants, got {num_participants}")
        
        if races_detected != len(test_ips):
            raise AssertionError(f"Expected {len(test_ips)} races, detected {races_detected}")
        
        print(f"✓ All {races_detected} races correctly detected")
        self.sim_manager.stop_simulation()
    
    def test_shared_race_detection(self):
        """Test: Same race on multiple IPs (participant matching)"""
        print("Testing: Shared race across multiple IPs")
        
        self.sim_manager.setup_test_environment()
        self.sim_manager.start_simulation()
        
        # Join same race on multiple IPs (201-203 have same participants)
        shared_ips = ["10.0.0.201", "10.0.0.202", "10.0.0.203"]
        for ip in shared_ips:
            self.sim_manager.join_race(ip)
        
        time.sleep(2)
        
        # Check all shared IPs have same participants
        api_files = self.get_api_files()
        shared_participants = None
        
        for filename, data in api_files.items():
            ip = filename.replace('.json', '')
            if ip in shared_ips:
                participants = data.get("participants", {})
                num_participants = participants.get("mNumParticipants", -1)
                participant_info = participants.get("mParticipantInfo", [])
                
                if num_participants <= 0:
                    raise AssertionError(f"{filename}: Expected participants, got {num_participants}")
                
                # Extract participant names
                names = [p.get("mName", "") for p in participant_info]
                names.sort()  # Sort for comparison
                
                if shared_participants is None:
                    shared_participants = names
                    print(f"✓ Reference participants from {filename}: {names}")
                else:
                    if names != shared_participants:
                        raise AssertionError(f"{filename}: Participant mismatch. Expected {shared_participants}, got {names}")
                    print(f"✓ Matching participants on {filename}: {names}")
        
        print(f"✓ Shared race correctly detected across {len(shared_ips)} IPs")
        self.sim_manager.stop_simulation()
    
    def test_race_state_transitions(self):
        """Test: Race state transitions (join -> racing -> finish -> leave)"""
        print("Testing: Complete race state transitions")
        
        self.sim_manager.setup_test_environment()
        self.sim_manager.start_simulation()
        
        test_ip = "10.0.0.201"
        
        # Initial state: no participants
        time.sleep(1)
        data = self.get_api_file_data(f"{test_ip}.json")
        if data["participants"]["mNumParticipants"] != -1:
            raise AssertionError("Initial state should have no participants")
        print("✓ Initial state: No participants")
        
        # Join race
        self.sim_manager.join_race(test_ip)
        time.sleep(1)
        data = self.get_api_file_data(f"{test_ip}.json")
        if data["participants"]["mNumParticipants"] <= 0:
            raise AssertionError("After join: Should have participants")
        print("✓ Participants joined: Race detected")
        
        # Start racing
        self.sim_manager.start_racing(test_ip)
        time.sleep(1)
        data = self.get_api_file_data(f"{test_ip}.json")
        if data["gameStates"]["mRaceState"] != 2:
            raise AssertionError("Race should be in green light state")
        print("✓ Racing started: Green light")
        
        # Finish race
        self.sim_manager.finish_race(test_ip)
        time.sleep(1)
        data = self.get_api_file_data(f"{test_ip}.json")
        if data["gameStates"]["mRaceState"] != 3:
            raise AssertionError("Race should be in results state")
        # Participants should still be present
        if data["participants"]["mNumParticipants"] <= 0:
            raise AssertionError("Results state should still have participants")
        print("✓ Race finished: Results screen (participants still present)")
        
        # Leave race
        self.sim_manager.leave_race(test_ip)
        time.sleep(1)
        data = self.get_api_file_data(f"{test_ip}.json")
        if data["participants"]["mNumParticipants"] != -1:
            raise AssertionError("After leave: Should have no participants")
        print("✓ Participants left: Race ended")
        
        self.sim_manager.stop_simulation()
    
    def test_participant_matching(self):
        """Test: Participant signature matching logic"""
        print("Testing: Participant signature matching")
        
        self.sim_manager.setup_test_environment()
        self.sim_manager.start_simulation()
        
        # Join different races with different participants
        race_configs = [
            ("10.0.0.201", "shared_race_1"),  # Marcus, Dave, Gregory, Rob
            ("10.0.0.204", "shared_race_2"),  # Giancarlo, Lee, Ilya, Jose
            ("10.0.0.208", "solo_race_1"),    # John Smith
        ]
        
        for ip, scenario in race_configs:
            self.sim_manager.join_race(ip)
        
        time.sleep(2)
        
        # Verify each race has unique participant signatures
        signatures = {}
        api_files = self.get_api_files()
        
        for filename, data in api_files.items():
            ip = filename.replace('.json', '')
            participants = data.get("participants", {})
            num_participants = participants.get("mNumParticipants", -1)
            
            if num_participants > 0:
                participant_info = participants.get("mParticipantInfo", [])
                names = [p.get("mName", "") for p in participant_info]
                names.sort()
                signature = "|".join(names)
                
                if signature in signatures:
                    print(f"✓ Shared race detected: {ip} matches {signatures[signature]} with signature: {signature}")
                else:
                    signatures[signature] = ip
                    print(f"✓ Unique race detected: {ip} with signature: {signature}")
        
        expected_signatures = 3  # Should have 3 unique participant signatures
        if len(signatures) != expected_signatures:
            raise AssertionError(f"Expected {expected_signatures} unique signatures, got {len(signatures)}")
        
        print(f"✓ Participant signature matching working correctly")
        self.sim_manager.stop_simulation()
    
    def test_mixed_scenarios(self):
        """Test: Mixed scenarios with some races active, some not"""
        print("Testing: Mixed scenarios (some races active, some inactive)")
        
        self.sim_manager.setup_test_environment()
        self.sim_manager.start_simulation()
        
        # Join races on some IPs, leave others inactive
        active_ips = ["10.0.0.201", "10.0.0.204"]
        all_ips = [f"10.0.0.{i}" for i in range(201, 211)]
        
        for ip in active_ips:
            self.sim_manager.join_race(ip)
        
        time.sleep(2)
        
        # Verify correct active/inactive states
        api_files = self.get_api_files()
        active_count = 0
        inactive_count = 0
        
        for filename, data in api_files.items():
            ip = filename.replace('.json', '')
            participants = data.get("participants", {})
            num_participants = participants.get("mNumParticipants", -1)
            
            if ip in active_ips:
                if num_participants <= 0:
                    raise AssertionError(f"{filename}: Should be active but got {num_participants} participants")
                active_count += 1
                print(f"✓ Active race on {ip}: {num_participants} participants")
            else:
                if num_participants != -1:
                    raise AssertionError(f"{filename}: Should be inactive but got {num_participants} participants")
                inactive_count += 1
        
        expected_active = len(active_ips)
        expected_inactive = len(all_ips) - len(active_ips)
        
        if active_count != expected_active:
            raise AssertionError(f"Expected {expected_active} active races, got {active_count}")
        
        if inactive_count != expected_inactive:
            raise AssertionError(f"Expected {expected_inactive} inactive races, got {inactive_count}")
        
        print(f"✓ Mixed scenario correct: {active_count} active, {inactive_count} inactive")
        self.sim_manager.stop_simulation()
    
    def get_api_files(self):
        """Get all API files as parsed JSON"""
        api_files = {}
        api_dir = self.sim_manager.output_dir
        
        for filename in os.listdir(api_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(api_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        api_files[filename] = json.load(f)
                except Exception as e:
                    print(f"Error reading {filename}: {e}")
        
        return api_files
    
    def get_api_file_data(self, filename):
        """Get specific API file data"""
        filepath = os.path.join(self.sim_manager.output_dir, filename)
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def print_test_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("TEST RESULTS SUMMARY")
        print("=" * 60)
        
        passed = 0
        failed = 0
        
        for test_name, result in self.test_results.items():
            if result == "PASSED":
                print(f"✅ {test_name}")
                passed += 1
            else:
                print(f"❌ {test_name}: {result}")
                failed += 1
        
        print("=" * 60)
        print(f"Total Tests: {len(self.test_results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print("=" * 60)
        
        if failed == 0:
            print("🎉 ALL TESTS PASSED! Participant-based race detection working correctly!")
        else:
            print("⚠️  Some tests failed. Check the results above.")

def run_individual_test():
    """Run individual test scenarios"""
    test_runner = TestScenarios()
    
    tests = [
        ("No races detected", test_runner.test_no_races_detected),
        ("Single race detection", test_runner.test_single_race_detection),
        ("Multiple races detection", test_runner.test_multiple_races_detection),
        ("Shared race detection", test_runner.test_shared_race_detection),
        ("Race state transitions", test_runner.test_race_state_transitions),
        ("Participant matching", test_runner.test_participant_matching),
        ("Mixed scenarios", test_runner.test_mixed_scenarios),
    ]
    
    print("Available Tests:")
    for i, (name, _) in enumerate(tests, 1):
        print(f"{i}. {name}")
    print("8. Run all tests")
    
    try:
        choice = int(input("Enter test number (1-8): "))
        if choice == 8:
            test_runner.run_all_tests()
        elif 1 <= choice <= len(tests):
            test_name, test_func = tests[choice - 1]
            print(f"Running: {test_name}")
            test_func()
            print(f"✅ {test_name} completed!")
        else:
            print("Invalid choice!")
    except ValueError:
        print("Please enter a valid number!")
    except KeyboardInterrupt:
        print("\nTest interrupted!")

if __name__ == "__main__":
    print("AMS2 Participant-Based Race Detection Test Suite")
    print("=" * 50)
    run_individual_test()
