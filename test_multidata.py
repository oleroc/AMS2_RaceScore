#!/usr/bin/env python3
"""
RaceMonitor Testmode Fix
Force initial multi-race data fetching in testmode
"""

import asyncio
import aiohttp
import json
import os

async def fetch_testmode_data():
    """Fetch data from all test IPs to populate multi_data"""
    test_ips = [
        "10.0.0.201", "10.0.0.202", "10.0.0.203", "10.0.0.204",
        "10.0.0.205", "10.0.0.206", "10.0.0.207", "10.0.0.208"
    ]
    
    print("🔍 Fetching testmode data from all test IPs...")
    
    multi_data = {}
    
    for ip in test_ips:
        api_file = f"api_files/{ip}.json"
        if os.path.exists(api_file):
            try:
                with open(api_file, 'r') as f:
                    data = json.load(f)
                
                # Check if this IP has active participants
                participants = data.get('participants', {})
                num_participants = participants.get('mNumParticipants', -1)
                
                if num_participants > 0:
                    print(f"✅ {ip}: {num_participants} participants detected")
                    multi_data[ip] = data
                else:
                    print(f"❌ {ip}: No participants")
                    
            except Exception as e:
                print(f"❌ {ip}: Error reading file - {e}")
        else:
            print(f"❌ {ip}: No API file found")
    
    print(f"\n🎯 Total active races detected: {len(multi_data)}")
    return multi_data

async def main():
    data = await fetch_testmode_data()
    
    if data:
        print("\n✅ Testmode data ready!")
        print("🏁 Active races found on IPs:", list(data.keys()))
        
        # Show participant summary
        for ip, race_data in data.items():
            participants = race_data.get('participants', {}).get('mParticipantInfo', [])
            names = [p.get('mName', 'Unknown') for p in participants[:3]]
            print(f"   {ip}: {names}")
    else:
        print("\n❌ No active races detected in testmode")
        print("🔧 Make sure live_race_simulator.py is running and generating API files")

if __name__ == "__main__":
    asyncio.run(main())
