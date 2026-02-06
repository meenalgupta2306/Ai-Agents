"""Voice Cloning Feature - API Routes"""
from flask import Blueprint, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename
import os

from .service import VoiceCloningService


# Initialize blueprint
voice_cloning_bp = Blueprint('voice_cloning', __name__, url_prefix='/api/voice-cloning')

# Initialize service (will be configured in app.py)
voice_cloning_service = None


def init_voice_cloning_service(documents_dir: str, voice_service_url: str):
    """Initialize the voice cloning service"""
    global voice_cloning_service
    voice_cloning_service = VoiceCloningService(documents_dir, voice_service_url)


@voice_cloning_bp.route('/sample-sets', methods=['GET'])
def list_sample_sets():
    """List all available sample sets"""
    try:
        user_id = request.args.get('user_id')
        sets = voice_cloning_service.list_sample_sets(user_id)
        
        return jsonify({
            'status': 'success',
            'sample_sets': [
                {
                    'set_id': s.set_id,
                    'set_type': s.set_type,
                    'user_id': s.user_id,
                    'total_samples': s.total_samples,
                    'created_at': s.created_at,
                    'samples': [
                        {
                            'filename': sample.filename,
                            'duration_seconds': sample.duration_seconds,
                            'uploaded_at': sample.uploaded_at
                        }
                        for sample in s.samples
                    ]
                }
                for s in sets
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@voice_cloning_bp.route('/sample-sets', methods=['POST'])
def create_sample_set():
    """Create a new sample set"""
    try:
        data = request.get_json()
        set_type = data.get('set_type', 'demo')
        user_id = data.get('user_id')
        
        set_id = voice_cloning_service.create_sample_set(set_type, user_id)
        
        return jsonify({
            'status': 'success',
            'set_id': set_id,
            'message': 'Sample set created successfully'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@voice_cloning_bp.route('/sample-sets/<set_id>', methods=['GET'])
def get_sample_set(set_id):
    """Get sample set details"""
    try:
        sample_set = voice_cloning_service.get_sample_set(set_id)
        
        if not sample_set:
            return jsonify({'error': 'Sample set not found'}), 404
            
        return jsonify({
            'status': 'success',
            'sample_set': {
                'set_id': sample_set.set_id,
                'set_type': sample_set.set_type,
                'user_id': sample_set.user_id,
                'total_samples': sample_set.total_samples,
                'created_at': sample_set.created_at,
                'samples': [
                    {
                        'filename': s.filename,
                        'duration_seconds': s.duration_seconds,
                        'uploaded_at': s.uploaded_at,
                        'file_size_bytes': s.file_size_bytes
                    }
                    for s in sample_set.samples
                ]
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@voice_cloning_bp.route('/sample-sets/<set_id>/upload', methods=['POST'])
def upload_sample(set_id):
    """Upload a voice sample to a set"""
    try:
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
            
        audio_file = request.files['audio_file']
        
        if audio_file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
            
        success, message, sample_info = voice_cloning_service.upload_sample_to_set(
            set_id, audio_file
        )
        
        if success:
            response = {
                'status': 'success',
                'message': message
            }
            if sample_info:
                response['sample_info'] = {
                    'filename': sample_info.filename,
                    'duration_seconds': sample_info.duration_seconds,
                    'uploaded_at': sample_info.uploaded_at,
                    'file_size_bytes': sample_info.file_size_bytes
                }
            return jsonify(response)
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@voice_cloning_bp.route('/generate', methods=['POST'])
def generate_speech():
    """Generate speech using a sample set"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        set_id = data.get('set_id')
        text = data.get('text')
        
        if not set_id or not text:
            return jsonify({'error': 'set_id and text are required'}), 400
            
        temperature = float(data.get('temperature', 0.85))
        speed = float(data.get('speed', 1.0))
        repetition_penalty = float(data.get('repetition_penalty', 2.0))
        model = data.get('model')  # Optional, service will handle default if None
        
        success, message, record = voice_cloning_service.generate_speech(
            set_id, text, temperature, speed, repetition_penalty, source='web', model=model
        )
        
        if success:
            return jsonify({
                'status': 'success',
                'message': message,
                'generation': {
                    'audio_filename': record.audio_filename,
                    'text': record.text,
                    'set_id': record.set_id,
                    'generated_at': record.generated_at,
                    'reference_clips_used': record.reference_clips_used,
                    'config': record.config
                }
            })
        else:
            return jsonify({'error': message}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@voice_cloning_bp.route('/sample-sets/<set_id>/history', methods=['GET'])
def get_generation_history(set_id):
    """Get generation history for a sample set"""
    try:
        history = voice_cloning_service.get_generation_history(set_id)
        
        return jsonify({
            'status': 'success',
            'history': [
                {
                    'audio_filename': r.audio_filename,
                    'text': r.text,
                    'set_id': r.set_id,
                    'generated_at': r.generated_at,
                    'reference_clips_used': r.reference_clips_used,
                    'generated_at': r.generated_at,
                    'reference_clips_used': r.reference_clips_used,
                    'config': r.config,
                    'model': r.model
                }
                for r in history
            ]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@voice_cloning_bp.route('/audio/<set_id>/<filename>', methods=['GET'])
def get_generated_audio(set_id, filename):
    """Serve generated audio file"""
    try:
        # Construct path: voice_samples/{set_id}/generated/{filename}
        directory = voice_cloning_service.voice_samples_dir / set_id / 'generated'
        
        return send_from_directory(
            directory,
            filename,
            mimetype='audio/wav'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404

@voice_cloning_bp.route('/sample/<set_id>/<filename>', methods=['GET'])
def get_sample_audio(set_id, filename):
    """Serve original voice sample file"""
    try:
        # Check explicit set folder (for demo sets or profile)
        # Note: profile usually is user_{user_id}, but set_id handles both formats 
        # because list_sample_sets logic uses set_id derived from directory name
        
        # Check standard location
        directory = voice_cloning_service.voice_samples_dir / set_id
        
        if not directory.exists():
            return jsonify({'error': 'Set not found'}), 404
            
        return send_from_directory(
            directory,
            filename,
            mimetype='audio/wav'
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404
