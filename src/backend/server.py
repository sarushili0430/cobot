# backend/server.py

from flask import Flask, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
from ai_agent import AI_Agent
import logging
import os

# Initialize Flask app and SocketIO
app = Flask(__name__, static_folder='../frontend', static_url_path='/')
app.config['SECRET_KEY'] = 'this_is_a_default_secret_key_for_local_testing'  # Default SECRET_KEY for local use
socketio = SocketIO(app, cors_allowed_origins="*")

# Configure Logging
logging.basicConfig(level=logging.INFO)

# Initialize AI Agent
ai_agent = AI_Agent()

# API Endpoint to handle chat commands
@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_prompt = data.get('prompt', '')
        if not user_prompt:
            return jsonify({'error': 'No prompt provided.'}), 400

        logging.info(f"Received prompt: {user_prompt}")

        # Process prompt to determine action
        action = ai_agent.process_external_prompt(user_prompt)

        logging.info(f"Determined action: {action}")

        # Emit action to Webots Controller via SocketIO
        socketio.emit('execute_action', {'action': action})

        return jsonify({'action': action})
    except Exception as e:
        logging.error(f"Error processing chat: {e}")
        return jsonify({'error': 'Internal server error.'}), 500

# Serve Frontend Files
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def static_proxy(path):
    return send_from_directory(app.static_folder, path)

# SocketIO Events (if needed)
@socketio.on('connect')
def handle_connect():
    logging.info('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    logging.info('Client disconnected')

if __name__ == '__main__':
    if not os.path.exists('../frontend'):
        print("Frontend directory not found.")
        exit(1)
    # Disable debug mode and auto-reloader
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False)
