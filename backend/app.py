from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
from supabase_db import SupabaseClient
from speechify_integration import SpeechifyAPI
from claude_integration import Claude

load_dotenv()  # Load environment variables from .env file

app = Flask(__name__)

# Initialize clients
supabase = SupabaseClient()
speechify = SpeechifyAPI()
claude = Claude()

@app.route('/')
def home():
    return "Welcome to the Virtual Curriculum API"

@app.route('/curriculum', methods=['GET'])
def get_curriculum():
    # Fetch curriculum data from Supabase
    curriculum = supabase.fetch_curriculum()
    return jsonify(curriculum)

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json['message']
    # Use Claude API to generate a response
    response = claude.generate_response(user_message)
    return jsonify({"response": response})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json['text']
    # Use Speechify API to convert text to speech
    audio_url = speechify.convert_to_speech(text)
    return jsonify({"audio_url": audio_url})

if __name__ == '__main__':
    app.run(debug=True)