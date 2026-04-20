"""Chatterbox TTS microservice - runs in its own venv to avoid numpy conflicts"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import logging

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

FLASK_PORT = int(os.getenv('CHATTERBOX_PORT', 5003))
DOCUMENTS_DIR = Path(os.getenv('DOCUMENTS_DIR', '../server/documents')).resolve()

chatterbox_model = None


def load_model():
    global chatterbox_model
    if chatterbox_model is not None:
        return True
    try:
        logger.info("Loading Chatterbox TTS model...")
        from chatterbox.tts import ChatterboxTTS
        import torch
        device = "cuda" if torch.cuda.is_available() else "cpu"
        chatterbox_model = ChatterboxTTS.from_pretrained(device=device)
        logger.info(f"Chatterbox model loaded on {device}")
        return True
    except Exception as e:
        logger.error(f"Failed to load Chatterbox model: {str(e)}")
        return False


@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': chatterbox_model is not None
    })


@app.route('/generate', methods=['POST'])
def generate():
    try:
        if not load_model():
            return jsonify({'error': 'Chatterbox model could not be loaded'}), 503

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400

        user_id = data.get('user_id')
        text = data.get('text')
        exaggeration = float(data.get('exaggeration', 0.5))
        cfg_weight = float(data.get('cfg_weight', 0.5))

        if not user_id or not text:
            return jsonify({'error': 'user_id and text are required'}), 400

        if str(user_id).startswith('user_') or str(user_id).startswith('set_'):
            user_dir = DOCUMENTS_DIR / 'voice_samples' / user_id
        else:
            user_dir = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}'

        if not user_dir.exists():
            return jsonify({'error': 'No voice samples found for this user'}), 404

        # Pick reference audio from metadata or scan directory
        speaker_wavs = []
        metadata_path = user_dir / 'metadata.json'
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
                    for sample in metadata.get('samples', []):
                        wav_path = user_dir / sample['filename']
                        if wav_path.exists():
                            speaker_wavs.append(str(wav_path))
            except Exception as e:
                logger.warning(f"Error reading metadata: {e}")

        if not speaker_wavs:
            speaker_wavs = [str(p) for p in user_dir.glob('*.wav')]

        if not speaker_wavs:
            return jsonify({'error': 'No valid voice sample files found'}), 404

        reference_wav = speaker_wavs[0]

        import torchaudio
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        text_hash = hashlib.md5(text.encode()).hexdigest()[:8]
        output_filename = f'chatterbox_{timestamp}_{text_hash}.wav'

        if str(user_id).startswith('user_') or str(user_id).startswith('set_'):
            output_dir = DOCUMENTS_DIR / 'voice_samples' / user_id / 'generated'
        else:
            output_dir = DOCUMENTS_DIR / 'voice_samples' / f'user_{user_id}' / 'generated'
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / output_filename

        logger.info(f"Generating for {user_id} with ref={reference_wav}")
        wav = chatterbox_model.generate(
            text,
            audio_prompt_path=reference_wav,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight
        )
        torchaudio.save(str(output_path), wav, chatterbox_model.sr)

        logger.info(f"Done: {output_path}")
        return jsonify({
            'status': 'success',
            'message': 'Speech generated successfully',
            'audio_filename': output_filename,
            'audio_path': str(output_path),
            'text': text,
            'reference_clips_used': 1,
            'config': {
                'exaggeration': exaggeration,
                'cfg_weight': cfg_weight
            }
        })

    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    logger.info("Starting Chatterbox service...")
    load_model()
    logger.info(f"Listening on port {FLASK_PORT}")
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=False)
