#!/usr/bin/env python3
"""
Frame Capture Only Test
Use this to rerun frame capture for an existing session
"""

import requests
import json
import time
import os
import sys

def capture_frames(session_id: str):
    # Configuration
    config_path = os.path.abspath('server/config.json')
    url = 'http://192.1.150.45:4200/#/content-contributor/path/topic-content/48619830-598a-46e1-874f-e85bb4cd312a/e1fa5e65-66d7-4524-874c-95669015ac9f/bc318d6e-13e4-4370-b7a5-0bd7197030bf/en/question-bank'

    print(f"📸 Starting Frame Capture for session: {session_id}")
    print("=" * 70)

    # Start generation with skip_generation=True
    # This will use existing scene_structure.json and audio files
    response = requests.post(
        'http://localhost:3001/api/content-generation/generate',
        json={
            'session_id': session_id,
            'config_path': config_path,
            'voice_set_id': 'set_a6078dfe',
            'url': url,
            'use_existing_browser': True,
            'cdp_url': 'http://localhost:9222',
            'options': {
                'skip_generation': True
            }
        }
    )

    result = response.json()
    if 'error' in result:
        print(f"❌ Error starting: {result['error']}")
        return

    print(f"✅ Started! Monitoring progress...")
    print("-" * 70)

    completed = False
    last_phase = ""
    while not completed:
        time.sleep(2)
        try:
            progress_response = requests.get(
                f'http://localhost:3001/api/content-generation/progress/{session_id}'
            )
            progress_data = progress_response.json()
            updates = progress_data.get('updates', [])
            
            for update in updates:
                if update.get('type') == 'error':
                    print(f"\n❌ ERROR: {update.get('message') or update.get('error')}")
                    completed = True
                    break
                elif update.get('type') == 'completed':
                    print(f"\n✅ COMPLETE!")
                    completed = True
                    break
                else:
                    phase = update.get('current_phase', '')
                    progress = update.get('progress_percentage', 0)
                    message = update.get('message', '')
                    
                    if phase != last_phase:
                        print(f"[{progress:3d}%] {phase:20s}: {message}")
                        last_phase = phase
        except Exception as e:
            print(f"Polling error: {e}")
            break

    # Get final result
    print(f"\n📦 Fetching result...")
    res = requests.get(f'http://localhost:3001/api/content-generation/result/{session_id}')
    print(json.dumps(res.json(), indent=2))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_capture_frames.py <session_id>")
        sys.exit(1)
    capture_frames(sys.argv[1])
