#!/usr/bin/env python3
"""
Test script for content generation
"""

import requests
import json
import time
import os

# Get absolute path to config
config_path = os.path.abspath('server/config.json')

# Start generation
print("🚀 Starting content generation...")
response = requests.post(
    'http://localhost:3001/api/content-generation/generate',
    json={
        'config_path': config_path,
        'voice_set_id': 'set_a6078dfe',
        'tts_model': 'coqui-xtts-v2'
    }
)

result = response.json()
print(f"✅ Started: {json.dumps(result, indent=2)}")

session_id = result['session_id']

# Poll for progress
print(f"\n📊 Monitoring progress for session: {session_id}")
print("-" * 60)

completed = False
while not completed:
    time.sleep(2)
    
    progress_response = requests.get(
        f'http://localhost:3001/api/content-generation/progress/{session_id}'
    )
    
    progress_data = progress_response.json()
    updates = progress_data.get('updates', [])
    
    for update in updates:
        if update.get('type') == 'error':
            print(f"❌ ERROR: {update.get('error')}")
            completed = True
            break
        elif update.get('type') == 'complete':
            print(f"✅ COMPLETE!")
            completed = True
            break
        else:
            phase = update.get('current_phase', '')
            progress = update.get('progress_percentage', 0)
            message = update.get('message', '')
            print(f"[{progress}%] {phase}: {message}")

# Get final result
print(f"\n📦 Fetching final result...")
result_response = requests.get(
    f'http://localhost:3001/api/content-generation/result/{session_id}'
)

final_result = result_response.json()
print(json.dumps(final_result, indent=2))

print(f"\n✨ Done! Check documents/content_generation/{session_id}/")
