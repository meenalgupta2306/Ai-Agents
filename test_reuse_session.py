#!/usr/bin/env python3
"""
Test script to reuse existing session for frame capture debugging
Uses session_c9733e982180 which has valid scene/audio data
"""

import requests
import json
import time
import os

# Configuration
config_path = os.path.abspath('server/config.json')
url = 'http://192.1.150.45:4200/#/content-contributor/path/topic-content/48619830-598a-46e1-874f-e85bb4cd312a/e1fa5e65-66d7-4524-874c-95669015ac9f/bc318d6e-13e4-4370-b7a5-0bd7197030bf/en/question-bank'
EXISTING_SESSION_ID = 'session_c9733e982180'

print("🎬 Starting Frame Capture Debug Test (Reusing Session)")
print("=" * 70)
print(f"Session: {EXISTING_SESSION_ID}")
print(f"URL: {url[:80]}...")
print("=" * 70)

# Start generation with skip_generation=True
print("\n🚀 Starting frame capture only...")
response = requests.post(
    'http://localhost:3001/api/content-generation/generate',
    json={
        'session_id': EXISTING_SESSION_ID,
        'config_path': config_path,
        'voice_set_id': 'set_a6078dfe',
        'tts_model': 'coqui-xtts-v2',
        'url': url, # Omit URL to use existing page
        'use_existing_browser': True,
        'cdp_url': 'http://localhost:9222',
        'options': {
            'skip_generation': True
        }
    }
)

result = response.json()
print(f"✅ Started: {json.dumps(result, indent=2)}")

# Poll for progress
print(f"\n📊 Monitoring progress for session: {EXISTING_SESSION_ID}")
print("-" * 70)

completed = False
last_phase = ""
last_progress = 0

while not completed:
    time.sleep(1)
    
    try:
        progress_response = requests.get(
            f'http://localhost:3001/api/content-generation/progress/{EXISTING_SESSION_ID}'
        )
        
        progress_data = progress_response.json()
        updates = progress_data.get('updates', [])
        
        for update in updates:
            if update.get('type') == 'error':
                print(f"\n❌ ERROR: {update.get('message') or update.get('error')}")
                completed = True
                break
            elif update.get('type') == 'completed' and update.get('progress_percentage') == 100:
                print(f"\n✅ COMPLETE!")
                completed = True
                break
            else:
                phase = update.get('current_phase', '')
                progress = update.get('progress_percentage', 0)
                message = update.get('message', '')
                
                # Print update
                print(f"[{progress:3d}%] {phase:20s}: {message}")
                
    except Exception as e:
        print(f"Error polling: {e}")
        time.sleep(2)

print("\n✨ Done!")
