"""Drag and Drop Test API Routes"""
from flask import Blueprint, jsonify, request
from features.dnd_test.service import DndTestService
import asyncio
from threading import Thread
import queue

dnd_test_blueprint = Blueprint('dnd_test', __name__, url_prefix='/api/dnd-test')

# Global queue for progress updates
progress_queue = queue.Queue()


def run_async_test(url: str, config_path: str = None, use_existing_browser: bool = True, cdp_url: str = None):
    """Run the async test in a separate thread"""
    async def run():
        service = DndTestService(config_path)
        
        # Set progress callback
        async def progress_callback(update):
            progress_queue.put(update)
        
        service.set_progress_callback(progress_callback)
        
        # Run the test
        result = await service.run_test(url, use_existing_browser, cdp_url)
        
        # Put final result in queue
        progress_queue.put({"type": "complete", "result": result})
    
    # Run in event loop
    asyncio.run(run())


@dnd_test_blueprint.route('/start', methods=['POST'])
def start_test():
    """Start the drag and drop automation test"""
    try:
        data = request.json or {}
        url = data.get('url', 'http://192.1.150.45:4200/#/content-contributor/path/topic-content/48619830-598a-46e1-874f-e85bb4cd312a/e1fa5e65-66d7-4524-874c-95669015ac9f/bc318d6e-13e4-4370-b7a5-0bd7197030bf/en/question-bank')
        config_path = data.get('config_path')
        use_existing_browser = data.get('use_existing_browser', True)
        cdp_url = data.get('cdp_url', 'http://localhost:9222')
        
        # Clear the queue
        while not progress_queue.empty():
            progress_queue.get()
        
        # Start test in background thread
        thread = Thread(target=run_async_test, args=(url, config_path, use_existing_browser, cdp_url))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "status": "started",
            "message": "Test started successfully"
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@dnd_test_blueprint.route('/progress', methods=['GET'])
def get_progress():
    """Get progress updates (SSE-like polling endpoint)"""
    updates = []
    
    # Get all available updates
    while not progress_queue.empty():
        try:
            update = progress_queue.get_nowait()
            updates.append(update)
        except queue.Empty:
            break
    
    return jsonify({
        "updates": updates
    })


@dnd_test_blueprint.route('/config', methods=['GET'])
def get_config():
    """Get the current config"""
    try:
        service = DndTestService()
        config = service.load_config()
        
        return jsonify({
            "status": "success",
            "config": config
        })
    
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
