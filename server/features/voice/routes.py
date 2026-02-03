"""Voice feature routes"""
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import logging

from .service import VoiceService

logger = logging.getLogger(__name__)

voice_blueprint = Blueprint('voice', __name__, url_prefix='/api/voice')
voice_service = VoiceService()


@voice_blueprint.route('/health', methods=['GET'])
def health_check():
    """Check if voice service is healthy"""
    is_healthy = voice_service.check_service_health()
    return jsonify({
        "status": "healthy" if is_healthy else "unhealthy",
        "voice_service_enabled": voice_service.enabled,
        "voice_service_url": voice_service.voice_service_url
    })


@voice_blueprint.route('/upload-sample', methods=['POST'])
def upload_voice_sample():
    """
    Upload user's voice sample for cloning
    
    Expected form data:
    - user_id: User ID
    - audio_file: Audio file (12-15 seconds)
    """
    try:
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        if 'user_id' not in request.form:
            return jsonify({'error': 'No user_id provided'}), 400
        
        user_id = request.form['user_id']
        audio_file = request.files['audio_file']
        
        if audio_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        result = voice_service.upload_voice_sample(user_id, audio_file)
        
        if result.get('status') == 'error':
            return jsonify(result), 400
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@voice_blueprint.route('/check-sample', methods=['GET'])
def check_voice_sample():
    """
    Check if user has uploaded a voice sample
    
    Query params:
    - user_id: User ID
    """
    user_id = request.args.get('user_id')
    if not user_id:
        return jsonify({'error': 'user_id is required'}), 400
    
    has_sample, metadata = voice_service.has_voice_sample(user_id)
    
    return jsonify({
        'has_sample': has_sample,
        'message': 'Voice sample found' if has_sample else 'No voice sample found',
        'metadata': metadata
    })


@voice_blueprint.route('/generate', methods=['POST'])
def generate_speech():
    """
    Generate speech in user's cloned voice
    
    Expected JSON body:
    - user_id: User ID
    - text: Text to convert to speech
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        user_id = data.get('user_id')
        text = data.get('text')
        
        if not user_id or not text:
            return jsonify({'error': 'user_id and text are required'}), 400
        
        if len(text) > 5000:
            return jsonify({'error': 'Text too long (max 5000 characters)'}), 400
        
        # Extract optional tuning parameters
        kwargs = {}
        for param in ['temperature', 'speed', 'repetition_penalty']:
            if param in data:
                kwargs[param] = data[param]
        
        result = voice_service.generate_speech(user_id, text, **kwargs)
        
        if result.get('status') == 'error':
            status_code = 404 if result.get('requires_sample') else 500
            return jsonify(result), status_code
        
        # Build audio URL
        audio_url = None
        if result.get('audio_filename'):
            audio_url = f"/api/voice/audio/{user_id}/{result['audio_filename']}"
        
        return jsonify({
            'status': result.get('status', 'success'),
            'message': result.get('message', 'Speech generated successfully'),
            'audio_filename': result.get('audio_filename'),
            'audio_url': audio_url,
            'text': result.get('text')
        }), 200
    
    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        return jsonify({'error': str(e)}), 500


@voice_blueprint.route('/audio/<user_id>/<filename>', methods=['GET'])
def get_audio_file(user_id, filename):
    """
    Serve generated audio file
    """
    audio_path = voice_service.get_audio_file_path(user_id, filename)
    
    if not audio_path:
        return jsonify({'error': 'Audio file not found'}), 404
    
    return send_file(
        str(audio_path),
        mimetype='audio/wav',
        as_attachment=False,
        download_name=filename
    )
