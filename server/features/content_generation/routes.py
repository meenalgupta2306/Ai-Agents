"""
Content Generation API Routes
"""

import os
import asyncio
import queue
from threading import Thread
from flask import Blueprint, request, jsonify
from .orchestrator import ContentGenerationOrchestrator

content_generation_blueprint = Blueprint('content_generation', __name__, url_prefix='/api/content-generation')

# Initialize orchestrator
documents_dir = os.getenv('DOCUMENTS_DIR', os.path.abspath(os.path.join(os.path.dirname(__file__), '../../documents')))
voice_service_url = os.getenv('VOICE_SERVICE_URL', 'http://localhost:8000')
orchestrator = ContentGenerationOrchestrator(documents_dir, voice_service_url)

# Progress tracking
progress_queues = {}


def run_async_generation(session_id: str, config_path: str, voice_set_id: str, tts_model: str, options: dict):
    """Run content generation in a separate thread"""
    async def run():
        # Set progress callback
        async def progress_callback(update):
            if session_id in progress_queues:
                progress_queues[session_id].put(update)
        
        orchestrator.set_progress_callback(session_id, progress_callback)
        
        # Run generation
        try:
            result = await orchestrator.generate_content(
                session_id,
                config_path,
                voice_set_id,
                tts_model,
                options
            )
            
            # Put final result in queue
            progress_queues[session_id].put({
                "type": "complete",
                "result": result.__dict__
            })
        except Exception as e:
            progress_queues[session_id].put({
                "type": "error",
                "error": str(e)
            })
    
    # Run in event loop
    asyncio.run(run())


@content_generation_blueprint.route('/generate', methods=['POST'])
def generate_content():
    """Start content generation"""
    try:
        data = request.json or {}
        
        config_path = data.get('config_path', 'server/config.json')
        voice_set_id = data.get('voice_set_id')
        tts_model = data.get('tts_model', 'coqui-xtts-v2')
        
        # Frame capture options
        url = data.get('url')
        use_existing_browser = data.get('use_existing_browser', True)
        cdp_url = data.get('cdp_url', 'http://localhost:9222')
        
        if not voice_set_id:
            return jsonify({
                "status": "error",
                "message": "voice_set_id is required"
            }), 400
        
        if not url and not use_existing_browser:
            return jsonify({
                "status": "error",
                "message": "url is required for new browser session"
            }), 400
        
        # Create options dict
        options = data.get('options', {})
        options.update({
            'url': url,
            'use_existing_browser': use_existing_browser,
            'cdp_url': cdp_url
        })
        
        # Use provided session_id or create new
        import uuid
        session_id = data.get('session_id')
        if not session_id:
            session_id = f"session_{uuid.uuid4().hex[:12]}"
        
        # Create progress queue
        progress_queues[session_id] = queue.Queue()
        
        # Start generation in background thread
        thread = Thread(
            target=run_async_generation,
            args=(session_id, config_path, voice_set_id, tts_model, options)
        )
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "started",
            "session_id": session_id,
            "message": "Content generation started"
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@content_generation_blueprint.route('/progress/<session_id>', methods=['GET'])
def get_progress(session_id: str):
    """Get progress updates for a session"""
    try:
        if session_id not in progress_queues:
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
        
        updates = []
        q = progress_queues[session_id]
        
        # Get all available updates
        while not q.empty():
            try:
                update = q.get_nowait()
                updates.append(update)
            except queue.Empty:
                break
        
        return jsonify({
            "status": "success",
            "updates": updates
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@content_generation_blueprint.route('/result/<session_id>', methods=['GET'])
def get_result(session_id: str):
    """Get final result for a session"""
    try:
        # Check if session exists
        session_dir = os.path.join(documents_dir, 'content_generation', session_id)
        
        if not os.path.exists(session_dir):
            return jsonify({
                "status": "error",
                "message": "Session not found"
            }), 404
        
        # Load artifacts
        import json
        
        scene_structure_path = os.path.join(session_dir, 'scene_structure.json')
        scripts_path = os.path.join(session_dir, 'scripts.json')
        
        result = {
            "status": "completed",
            "session_id": session_id,
            "artifacts": {}
        }
        
        if os.path.exists(scene_structure_path):
            with open(scene_structure_path, 'r') as f:
                result['scene_structure'] = json.load(f)
        
        if os.path.exists(scripts_path):
            with open(scripts_path, 'r') as f:
                result['scripts'] = json.load(f)
        
        # List audio files
        audio_dir = os.path.join(session_dir, 'audio')
        if os.path.exists(audio_dir):
            audio_files = [f for f in os.listdir(audio_dir) if f.endswith('.mp3')]
            result['audio_files'] = audio_files
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
