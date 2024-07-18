import base64
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
import os
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.claude_integration import ClaudeAPI
from backend.braintrust_integration import BraintrustAPI
import backend.helpers as helpers

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')

supabase = SupabaseClient()
speechify = SpeechifyAPI()
claude = ClaudeAPI()
brain = BraintrustAPI()

#override render template to always include these variables

@app.route('/')
def index(path=None):
    print(helpers.get_visitor_info())
    biography = "Hi, I'm Julian a tech enthusiast who just graduated from Stanford GSB. Chat with me below (and hear my voice)!"
    return render('index.html', bio=biography, picture_link='https://www.youtube.com/embed/1y_kfWUCFDQ')

# create generic route that loads whatever html is listed in route and a 404 if not found in directory
@app.route('/<path:path>')
def generic(path):
    try:
        print(path)
        return render_template(f'{path}.html')
    except:
        return render_template('index.html')

#has parameter audio to determine whether or not to generate audio
@app.route('/chat', methods=['POST'])
def chat():
    audio = request.json.get('audio')
    message = request.json['message']
    response = brain.generate_response(message)
    #generate audio if audio is true
    audio_url = get_audio_url(response) if audio else None
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
    
def render(template, **kwargs):
    return render_template(template, **kwargs, instagram='https://www.instagram.com/julyanserra/', linkedin='https://www.linkedin.com/in/julianserra/', github='https://github.com/julyanserra', email='mailto:julian.serra.wright@gmail.com')


if __name__ == '__main__':
    app.run(debug=True)