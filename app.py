import base64
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.claude_integration import ClaudeAPI
import backend.helpers as helpers

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')

supabase = SupabaseClient()
speechify = SpeechifyAPI()
claude = ClaudeAPI()

@app.route('/')
def index(path=None):
    print(helpers.get_visitor_info())
    biography = "Hi, I'm Julian Serra a tech enthusiast who just graduated from Stanford GSB. Chat with me below (and hear my voice)!"
    return render_template('index_copy.html', bio=biography, favourite_video='https://www.youtube.com/embed/1y_kfWUCFDQ')

# create generic route that loads whatever html is listed in route and a 404 if not found in directory
@app.route('/<path:path>')
def generic(path):
    try:
        print(path)
        return render_template(f'{path}.html')
    except:
        return render_template('404.html')

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
    

if __name__ == '__main__':
    app.run(debug=True)