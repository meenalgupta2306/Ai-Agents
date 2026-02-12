#!/usr/bin/env python3
"""
Complete end-to-end test for content generation with video
"""

import requests
import json
import time
import os

# Configuration
config_path = os.path.abspath('server/config.json')
url = 'http://192.1.150.45:4200/#/content-contributor/path/topic-content/48619830-598a-46e1-874f-e85bb4cd312a/e1fa5e65-66d7-4524-874c-95669015ac9f/bc318d6e-13e4-4370-b7a5-0bd7197030bf/en/question-bank'

print("🎬 Starting COMPLETE Content Generation Pipeline")
print("=" * 70)
print(f"Config: {config_path}")
print(f"URL: {url[:80]}...")
print("=" * 70)

# Start generation
print("\n🚀 Starting content generation...")
response = requests.post(
    'http://localhost:3001/api/content-generation/generate',
    json={
        'config_path': config_path,
        'voice_set_id': 'set_a6078dfe',
        'tts_model': 'coqui-xtts-v2',
        'url': url,
        'use_existing_browser': True,
        'cdp_url': 'http://localhost:9222'
    }
)

result = response.json()
print(f"✅ Started: {json.dumps(result, indent=2)}")

session_id = result['session_id']

# Poll for progress
print(f"\n📊 Monitoring progress for session: {session_id}")
print("-" * 70)

completed = False
last_phase = ""
last_progress = 0

while not completed:
    time.sleep(3)
    
    progress_response = requests.get(
        f'http://localhost:3001/api/content-generation/progress/{session_id}'
    )
    
    progress_data = progress_response.json()
    updates = progress_data.get('updates', [])
    
    for update in updates:
        if update.get('type') == 'error':
            print(f"\n❌ ERROR: {update.get('error')}")
            completed = True
            break
        elif update.get('type') == 'complete':
            print(f"\n✅ COMPLETE!")
            completed = True
            break
        else:
            phase = update.get('current_phase', '')
            progress = update.get('progress_percentage', 0)
            message = update.get('message', '')
            
            # Only print if phase or progress changed
            if phase != last_phase or progress != last_progress:
                emoji = {
                    'scene_generation': '🎭',
                    'script_generation': '📝',
                    'audio_generation': '🎵',
                    'frame_capture': '📸',
                    'video_assembly': '🎬',
                    'completed': '✨'
                }.get(phase, '⚙️')
                
                print(f"{emoji} [{progress:3d}%] {phase:20s}: {message}")
                last_phase = phase
                last_progress = progress

# Get final result
print(f"\n📦 Fetching final result...")
result_response = requests.get(
    f'http://localhost:3001/api/content-generation/result/{session_id}'
)

final_result = result_response.json()

if final_result.get('status') == 'completed':
    print("\n" + "=" * 70)
    print("🎉 SUCCESS! Video Generation Complete!")
    print("=" * 70)
    
    if 'video_path' in final_result.get('artifacts', {}):
        video_path = final_result['artifacts']['video_path']
        print(f"\n🎥 Video: {video_path}")
        
        # Check if file exists and get size
        if os.path.exists(video_path):
            size_mb = os.path.getsize(video_path) / (1024 * 1024)
            print(f"   Size: {size_mb:.2f} MB")
        
    print(f"\n📁 Session Directory:")
    print(f"   documents/content_generation/{session_id}/")
    print(f"\n📊 Artifacts:")
    for key, value in final_result.get('artifacts', {}).items():
        print(f"   - {key}: {value}")
    
    print(f"\n⏱️  Duration: {final_result.get('duration', 0)} seconds")
    print(f"🎬 Scenes: {final_result.get('scenes_count', 0)}")
else:
    print(f"\n❌ Generation failed or incomplete")
    print(json.dumps(final_result, indent=2))

print("\n✨ Done!")
