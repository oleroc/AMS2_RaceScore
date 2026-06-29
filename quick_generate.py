#!/usr/bin/env python3
"""
Quick script to automatically join all races in the API simulator
"""
import subprocess
import time
import os

print("Starting API simulator and joining all races...")

# Start simulator and send command
try:
    # Send command 1 to join all races
    p = subprocess.Popen(['python', 'api_simulator.py'], 
                        stdin=subprocess.PIPE, 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.PIPE,
                        text=True)
    
    # Wait a bit for setup
    time.sleep(2)
    
    # Send command 1 (join all races)
    output, errors = p.communicate(input="1\n7\n")
    
    print("Simulator output:")
    print(output)
    
    if errors:
        print("Errors:")
        print(errors)
        
    print("JSON files should now be generated with 192.168.3.x IPs")
    
except Exception as e:
    print(f"Error: {e}")
