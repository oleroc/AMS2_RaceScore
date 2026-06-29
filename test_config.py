#!/usr/bin/env python3
"""
Test testmode configuration reading
"""

import configparser
import os
import json

def test_config():
    print("🔍 Testing Configuration Reading")
    print("=" * 40)
    
    # Test config.ini reading
    config_path = "config.ini"
    if os.path.exists(config_path):
        print(f"✅ Found config.ini at: {os.path.abspath(config_path)}")
        
        config = configparser.ConfigParser()
        config.read(config_path, encoding='utf-8')
        
        # Test testmode reading
        testmode_value = config.get('config', 'testmode', fallback='NOT_FOUND')
        testmode_bool = testmode_value.strip().lower() == 'true'
        
        print(f"📋 Raw testmode value: '{testmode_value}'")
        print(f"📋 Testmode boolean: {testmode_bool}")
        
        # Test IP address
        ip_address = config.get('config', 'ip_address', fallback='NOT_FOUND')
        print(f"📋 IP address: {ip_address}")
        
    else:
        print("❌ config.ini not found")
        return
    
    # Test API file reading
    api_file = f"api_files/{ip_address}.json"
    print(f"\n🔍 Testing API File Reading")
    print("=" * 40)
    
    if os.path.exists(api_file):
        print(f"✅ Found API file: {os.path.abspath(api_file)}")
        
        try:
            with open(api_file, 'r') as f:
                data = json.load(f)
            
            participants = data.get('participants', {})
            num_participants = participants.get('mNumParticipants', -1)
            participant_info = participants.get('mParticipantInfo', [])
            
            print(f"📋 mNumParticipants: {num_participants}")
            print(f"📋 Participant count in array: {len(participant_info)}")
            
            if num_participants > 0:
                print("✅ Race should be detected!")
                for i, p in enumerate(participant_info[:3]):  # Show first 3
                    print(f"   👤 {i+1}: {p.get('mName', 'Unknown')}")
            else:
                print("❌ No race detected (mNumParticipants <= 0)")
                
        except Exception as e:
            print(f"❌ Error reading API file: {e}")
    else:
        print(f"❌ API file not found: {api_file}")

def test_simulation_function():
    """Test the actual testmode function logic"""
    print(f"\n🔍 Testing Simulation Function")
    print("=" * 40)
    
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8')
    
    # Simulate the read_testmode_status function
    testmode_enabled = config.get('config', 'testmode', fallback='False').strip().lower() == 'true'
    print(f"📋 Testmode enabled: {testmode_enabled}")
    
    if testmode_enabled:
        ip_address = config.get('config', 'ip_address', fallback='10.0.0.201')
        api_file = f"api_files/{ip_address}.json"
        
        print(f"📋 Looking for API file: {api_file}")
        
        if os.path.exists(api_file):
            try:
                with open(api_file, 'r') as f:
                    data = json.load(f)
                
                print("✅ API file loaded successfully")
                print(f"📋 Keys in data: {list(data.keys())}")
                
                # Test race detection logic
                participants = data.get('participants', {})
                num_participants = participants.get('mNumParticipants', -1)
                
                if num_participants > 0:
                    print(f"✅ RACE DETECTED! {num_participants} participants")
                    return True
                else:
                    print(f"❌ NO RACE: mNumParticipants = {num_participants}")
                    return False
                    
            except Exception as e:
                print(f"❌ Error loading API file: {e}")
                return False
        else:
            print(f"❌ API file not found: {api_file}")
            return False
    else:
        print("❌ Testmode not enabled")
        return False

if __name__ == "__main__":
    test_config()
    race_detected = test_simulation_function()
    
    print(f"\n🎯 FINAL RESULT")
    print("=" * 20)
    if race_detected:
        print("✅ System should detect races in testmode!")
    else:
        print("❌ System will NOT detect races - check configuration")
