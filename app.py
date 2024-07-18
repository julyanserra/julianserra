import base64
from flask import Flask, render_template, request, jsonify
import hashlib
import user_agents
from dotenv import load_dotenv
import os
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.claude_integration import ClaudeAPI

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')

supabase = SupabaseClient()
speechify = SpeechifyAPI()
claude = ClaudeAPI()

@app.route('/')
def index(path=None):
    print(get_visitor_info())
    biography = "Hey I'm Claude, your virtual assistant. How can I help you today?"
    return render_template('index_copy.html', bio=biography, favourite_video='https://www.youtube.com/embed/1y_kfWUCFDQ')

# create generic route that loads whatever html is listed in route and a 404 if not found in directory
@app.route('/<path:path>')
def generic(path):
    try:
        print(path)
        return render_template(f'{path}.html')
    except:
        return render_template('404.html')

# IN CASE I WANT TO WELCOME THEM WITHOUT ACTION
# @socketio.on('connect')
# def welcome():
#     welcome = "Welcome to the Virtual Curriculum API"
#     audio_url = get_audio_url(welcome)
#     emit('response', {'data': welcome, 'audio_url': audio_url})

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json['message']
    response = claude.generate_response(message)
    audio_url = get_audio_url(response)
    return jsonify({'data': response, 'audio_url': audio_url})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json['text']
    audio_url = get_audio_url(text)
    return jsonify({"audio_url": audio_url})

def get_audio_url(text):
    audio_data, audio_format = speechify.convert_to_speech(text)
    try:
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
    return audio_url
    


def get_visitor_info():
    # Create a unique fingerprint based on available information
    fingerprint_data = [
        request.remote_addr,
        request.headers.get('User-Agent', ''),
        request.headers.get('Accept-Language', ''),
        request.headers.get('Accept-Encoding', ''),
    ]
    fingerprint = hashlib.md5(''.join(fingerprint_data).encode()).hexdigest()
    
    user_agent = request.headers.get('User-Agent')
    ua = user_agents.parse(user_agent)
    
    visitor_info = {
        'fingerprint': fingerprint,
        'ip_address': request.remote_addr,
        'browser': ua.browser.family,
        'browser_version': ua.browser.version_string,
        'os': ua.os.family,
        'os_version': ua.os.version_string,
        'device': ua.device.family,
        'is_mobile': ua.is_mobile,
        'is_tablet': ua.is_tablet,
        'is_pc': ua.is_pc,
        'referrer': request.referrer,
        'language': request.headers.get('Accept-Language'),
    }
    
    return visitor_info

if __name__ == '__main__':
    app.run(debug=True)