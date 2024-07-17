import base64
from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
from dotenv import load_dotenv
import os
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.claude_integration import ClaudeAPI

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
socketio = SocketIO(app)

supabase = SupabaseClient()
speechify = SpeechifyAPI()
claude = ClaudeAPI()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/chat')
def chat():
    return render_template('chat.html')

@app.route('/curriculum', methods=['GET'])
def get_curriculum():
    curriculum = supabase.fetch_curriculum()
    return jsonify(curriculum)

@socketio.on('message')
def handle_message(message):
    response = claude.generate_response(message)
    try:
        audio_data, audio_format = speechify.convert_to_speech(response)
        if audio_data and audio_format:
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            audio_url = f"data:audio/{audio_format};base64,{audio_base64}"
            print("Audio generated successfully")
        else:
            audio_url = None
            print("No audio data received from Speechify")
    except Exception as e:
        print(f"Error generating audio from Speechify: {str(e)}")
        audio_url = None
    emit('response', {'data': response, 'audio_url': audio_url})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json['text']
    audio_url = speechify.convert_to_speech(text)
    return jsonify({"audio_url": audio_url})

if __name__ == '__main__':
    socketio.run(app, debug=True)