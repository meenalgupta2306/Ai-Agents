"""Voice Service - Flask microservice for XTTS voice cloning and speech generation"""
import os
import json
import hashlib
import numpy as np
import noisereduce as nr
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from pydub import AudioSegment, effects
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration
FLASK_PORT = int(os.getenv('FLASK_PORT', 5002))
XTTS_MODEL_NAME = os.getenv('XTTS_MODEL_NAME', 'tts_models/multilingual/multi-dataset/xtts_v2')
DOCUMENTS_DIR = Path(os.getenv('DOCUMENTS_DIR', '../server/documents')).resolve()

# Global variable to hold the TTS model
tts_model = None


def load_tts_model():
    """Load XTTS model on startup"""
    global tts_model
    try:
        logger.info(f"Loading XTTS model: {XTTS_MODEL_NAME}")
        
        # Workaround for PyTorch 2.6 weights_only parameter
        import torch
        import warnings
        warnings.filterwarnings('ignore', category=FutureWarning)
        
        # Allow TTS classes in torch.load
        try:
            from TTS.tts.configs.xtts_config import XttsConfig
            torch.serialization.add_safe_globals([XttsConfig])
        except:
            pass  # Older PyTorch versions don't have this
        
        from TTS.api import TTS
        
        # Initialize TTS with XTTS model
        tts_model = TTS(model_name=XTTS_MODEL_NAME, progress_bar=True, gpu=False)
        logger.info("XTTS model loaded successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to load XTTS model: {str(e)}")
        return False


def preprocess_audio(input_path: Path, output_path: Path) -> bool:
    """
    Preprocess audio validation for optimal XTTS quality:
    1. Convert to Mono
    2. Resample to 22,050 Hz
    3. Normalize loudness
    4. Trim silence
    5. Light noise reduction
    """
    try:
        # Load audio with pydub
        audio = AudioSegment.from_file(str(input_path))
        
        # 1. Convert to Mono
        audio = audio.set_channels(1)
        
        # 2. Resample to 22,050 Hz
        audio = audio.set_frame_rate(22050)
        
        # 3. Normalize loudness
        audio = effects.normalize(audio)
        
        # 4. Trim silence (simple approach using pydub)
        # Split on silence and recombine
        # This is a basic implementation; robust silence trimming can be complex
        # For now, we'll keep it simple: normalize is usually enough for well-recorded audio
        # But let's strip start/end silence
        def strip_silence(sound, silence_thresh=-50.0, chunk_size=10):
            trim_ms = 0  # ms
            assert chunk_size > 0  # to avoid infinite loop
            while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_thresh and trim_ms < len(sound):
                trim_ms += chunk_size
            return sound[trim_ms:]

        audio = strip_silence(audio)  # Trim start
        # To trim end, reverse, trim start, reverse back
        audio = strip_silence(audio.reverse()).reverse()

        # 5. Noise Reduction (using noisereduce)
        # Convert pydub audio to numpy array
        samples = np.array(audio.get_array_of_samples())
        if audio.sample_width == 2:
            data_type = np.int16
        elif audio.sample_width == 4:
            data_type = np.int32
        else:
            data_type = np.float32
            
        samples = samples.astype(data_type)
        
        # Apply noise reduction
        # Stationary noise reduction is safer for speech
        reduced_noise = nr.reduce_noise(y=samples, sr=audio.frame_rate, stationary=True, prop_decrease=0.75)
        
        # Ensure we convert back to the correct type (noisereduce might return floats)
        reduced_noise = reduced_noise.astype(data_type)
        
        # Convert back to AudioSegment
        processed_audio = AudioSegment(
            reduced_noise.tobytes(), 
            frame_rate=audio.frame_rate,
            sample_width=audio.sample_width, 
            channels=1
        )
        
        # Export as WAV
        processed_audio.export(str(output_path), format='wav')
        return True
        
    except Exception as e:
        logger.error(f"Audio preprocessing failed: {str(e)}")
        # Fallback: simple conversion if advanced processing fails
        try:
            audio = AudioSegment.from_file(str(input_path))
            audio = audio.set_channels(1).set_frame_rate(22050)
            audio.export(str(output_path), format='wav')
            logger.info("Fallback: Performed basic conversion")
            return True
        except Exception as fallback_e:
            logger.error(f"Fallback conversion failed: {str(fallback_e)}")
            return False


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': tts_model is not None,
        'model_name': XTTS_MODEL_NAME
    })


@app.route('/upload-sample', methods=['POST'])
def upload_sample():
    """
    Upload and save user's voice sample
    Now supports multiple samples per user.
    """
    try:
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        if 'user_id' not in request.form:
            return jsonify({'error': 'No user_id provided'}), 400
        
        audio_file = request.files['audio_file']
        user_id = request.form['user_id']
        
        if audio_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Create user directory
        # Create user directory (handle prefix)
        if str(user_id).startswith('user_') or str(user_id).startswith('set_'):
             user_dir = DOCUMENTS_DIR / 'voice_samples' / user_id
        else:
             user_dir = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}'
        user_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f'sample_{timestamp}.wav'
        
        # Save uploaded file temporarily
        temp_path = user_dir / f'temp_{timestamp}'
        audio_file.save(str(temp_path))
        
        # Output path for processed file
        sample_path = user_dir / unique_filename
        
        # Preprocess and convert
        if not preprocess_audio(temp_path, sample_path):
            temp_path.unlink(missing_ok=True)
            return jsonify({'error': 'Failed to process audio file'}), 500
        
        # Remove temp file
        temp_path.unlink(missing_ok=True)
        
        # Get audio duration
        audio = AudioSegment.from_wav(str(sample_path))
        duration_seconds = len(audio) / 1000.0
        
        # Simple duration check (warn but allow slightly shorter/longer clips if needed)
        if duration_seconds < 3: 
            # Too short to be useful
            sample_path.unlink()
            return jsonify({'error': 'Audio too short (min 3 seconds)'}), 400
            
        # Update metadata list
        metadata_path = user_dir / 'metadata.json'
        metadata = {'samples': []}
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    data = json.load(f)
                    # Migrate old metadata format if needed
                    if 'samples' in data:
                        metadata = data
                    else:
                        # Convert old single format to list
                        if 'uploaded_at' in data:
                            metadata['samples'].append({
                                'filename': 'sample.wav', # Assuming old file was sample.wav
                                'uploaded_at': data.get('uploaded_at'),
                                'duration_seconds': data.get('duration_seconds', 0)
                            })
            except Exception as e:
                logger.warning(f"Could not load existing metadata: {e}")
        
        # Add new sample info
        new_sample_info = {
            'filename': unique_filename,
            'uploaded_at': datetime.now().isoformat(),
            'duration_seconds': duration_seconds,
            'file_size_bytes': sample_path.stat().st_size
        }
        metadata['samples'].append(new_sample_info)
        
        # Save updated metadata
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
            
        # Legacy sample.wav copy logic removed to avoid file duplication confusion.
        # Newer endpoints scan for all .wav files or use metadata.json.
        
        logger.info(f"Voice sample uploaded for user {user_id}: {unique_filename}")
        
        return jsonify({
            'status': 'success',
            'message': 'Voice sample uploaded and processed successfully',
            'sample_info': new_sample_info,
            'total_samples': len(metadata['samples'])
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/generate-speech', methods=['POST'])
def generate_speech():
    """
    Generate speech using XTTS and user's voice samples (multi-shot)
    Improvements: Explicit latent extraction for consistency + Tuning params
    """
    try:
        print("GENERATE SPEECH REQUEST RECEIVED")
        if tts_model is None:
            return jsonify({'error': 'TTS model not loaded'}), 503
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        text = data.get('text')
        
        # Tuning parameters (with defaults)
        temperature = float(data.get('temperature', 0.85)) # Lower = more stable
        speed = float(data.get('speed', 1.0))
        repetition_penalty = float(data.get('repetition_penalty', 2.0))
        
        if not user_id or not text:
            return jsonify({'error': 'user_id and text are required'}), 400
        
        # Check if user has voice samples
        if str(user_id).startswith('user_') or str(user_id).startswith('set_'):
            user_dir = DOCUMENTS_DIR / 'voice_samples' / user_id
        else:
            user_dir = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}'
        if not user_dir.exists():
             return jsonify({
                'error': 'No voice samples found for this user',
                'message': 'Please upload voice samples first'
            }), 404
            
        # Gather all valid .wav files from metadata or directory
        speaker_wavs = []
        
        # Try reading from metadata first to get order/validity
        metadata_path = user_dir / 'metadata.json'
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    if 'samples' in metadata:
                        for sample in metadata['samples']:
                            wav_path = user_dir / sample['filename']
                            if wav_path.exists():
                                speaker_wavs.append(str(wav_path))
            except Exception as e:
                logger.warning(f"Error reading metadata: {e}")
        
        # Fallback: scan directory if no metadata samples found
        if not speaker_wavs:
            speaker_wavs = [str(p) for p in user_dir.glob('*.wav')]
            
        if not speaker_wavs:
            return jsonify({
                'error': 'No valid voice sample files found',
                'message': 'Please upload a voice sample'
            }), 404
            
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_filename = f'{timestamp}_{text_hash}.wav'
        
        # Create output directory
        if str(user_id).startswith('user_') or str(user_id).startswith('set_'):
             output_dir = DOCUMENTS_DIR / 'voice_samples' / user_id / 'generated'
        else:
             output_dir = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}' / 'generated'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename
        
        # Generate speech using XTTS with multiple reference files
        # We pass the list of files to speaker_wav, and the library handles latent extraction internally
        # We also pass tuning parameters (temperature, speed, etc.)
        logger.info(f"Generating speech for user {user_id} (temp={temperature}, speed={speed})")
        
        tts_model.tts_to_file(
            text=text,
            speaker_wav=speaker_wavs, # Pass list of files
            language='en',
            file_path=str(output_path),
            temperature=temperature,
            length_penalty=1.0,
            repetition_penalty=repetition_penalty,
            top_k=50,
            top_p=0.8,
            speed=speed,
            enable_text_splitting=True
        )
        
        logger.info(f"Speech generated: {output_path}")
        
        return jsonify({
            'status': 'success',
            'message': 'Speech generated successfully',
            'audio_filename': output_filename,
            'audio_path': str(output_path),
            'text': text,
            'reference_clips_used': len(speaker_wavs),
            'config': {
                'temperature': temperature,
                'speed': speed
            }
        })
        
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Voice Service...")
    
    # Load TTS model on startup
    if load_tts_model():
        logger.info(f"Starting Flask server on port {FLASK_PORT}")
        app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
    else:
        logger.error("Failed to start service: Could not load TTS model")
        exit(1)
