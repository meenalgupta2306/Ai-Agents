#!/usr/bin/env python3
"""
Migration script to create metadata.json for existing voice sample directories
"""
import os
import json
from pathlib import Path
from datetime import datetime

def get_file_size(filepath):
    """Get file size in bytes"""
    return os.path.getsize(filepath)

def estimate_duration(filepath):
    """Estimate audio duration (rough estimate based on file size)"""
    # Rough estimate: ~176KB per second for 16-bit 22050Hz mono WAV
    file_size = get_file_size(filepath)
    return round(file_size / 176000, 2)

def migrate_voice_samples(documents_dir='documents'):
    """Create metadata.json for all existing voice sample directories"""
    voice_samples_dir = Path(documents_dir) / 'voice_samples'
    
    if not voice_samples_dir.exists():
        print(f"Voice samples directory not found: {voice_samples_dir}")
        return
    
    migrated_count = 0
    
    for set_dir in voice_samples_dir.iterdir():
        if not set_dir.is_dir():
            continue
            
        metadata_path = set_dir / 'metadata.json'
        
        # Check existing metadata
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    existing_data = json.load(f)
                
                # If set_id is present and valid, skip
                if 'set_id' in existing_data and existing_data['set_id']:
                    print(f"✓ Valid metadata exists for: {set_dir.name}")
                    continue
                else:
                    print(f"⚠ Invalid metadata (missing set_id) for: {set_dir.name}. Fixing...")
            except json.JSONDecodeError:
                print(f"⚠ Corrupt metadata for: {set_dir.name}. Regenerating...")

        # Find all WAV files in the directory
        wav_files = list(set_dir.glob('*.wav'))
        
        if not wav_files:
            # If no wav files but metadata exists and we are here, it means we might want to keep it?
            # But if it was invalid, we proceed to regenerate it but maybe we find no wavs now.
            # Let's check wavs independently.
            print(f"⚠ No WAV files found in: {set_dir.name}")
            continue
        
        # Determine set type based on directory name
        # Force profile type for user directories
        set_type = 'profile' if 'user_' in set_dir.name else 'demo'
        
        # Extract user_id
        if set_type == 'profile':
            user_id = set_dir.name.replace('user_', '')
        else:
            user_id = None
        
        # Create sample entries
        samples = []
        for wav_file in wav_files:
            sample = {
                'filename': wav_file.name,
                'uploaded_at': datetime.fromtimestamp(wav_file.stat().st_mtime).isoformat(),
                'duration_seconds': estimate_duration(wav_file),
                'file_size_bytes': get_file_size(wav_file)
            }
            samples.append(sample)
        
        # Create metadata - preserve existing samples if they have more info? 
        # For now, simplistic regeneration is safer given the state of that file.
        metadata = {
            'set_id': set_dir.name,
            'set_type': set_type,
            'user_id': user_id,
            'samples': samples,
            'created_at': datetime.fromtimestamp(set_dir.stat().st_mtime).isoformat(),
            'total_samples': len(samples)
        }
        
        # Write metadata file
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Created metadata for: {set_dir.name} ({len(samples)} samples)")
        migrated_count += 1
    
    print(f"\n🎉 Migration complete! Migrated {migrated_count} sample set(s)")

if __name__ == '__main__':
    migrate_voice_samples()
