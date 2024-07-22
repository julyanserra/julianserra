import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import os

import requests
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.braintrust_integration import BraintrustAPI
import backend.models as models
import backend.stripe_integration as stripe
import backend.helpers as helpers

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
#set up session


supabase = SupabaseClient()
speechify = SpeechifyAPI()
brain = BraintrustAPI()


@app.route('/')
def index(path=None):
    #see all session variables
    session["visitor"] = helpers.get_visitor_info()
    location = helpers.get_most_specific_location(helpers.get_location(session["visitor"]))
    #return one text option if no location data
    biography = f"""Hey there over in {location}! Chat with me below (and hear my voice)!""" if location != 'Unknown' else "Hey there! Chat with me below (and hear my voice)!"
    return render('index.html', bio=biography, profile_photo='https://media.licdn.com/dms/image/D5603AQH-aetvtESQbA/profile-displayphoto-shrink_400_400/0/1679704251439?e=1726704000&v=beta&t=zzuSGt4H0vOitpAhvNaWl3dDYGJYP9k00C8sA7fYKhs', picture_link='https://open.spotify.com/track/71glNHT4FultOqlau4zrFf?si=3ed90ad714c54a67', hover_photo='https://i.ibb.co/0QcbGsY/Screenshot-2024-07-18-at-5-19-02-PM.png')

# create generic route that loads whatever html is listed in route and a 404 if not found in directory
@app.route('/<path:path>')
def generic(path):
    try:
        return render(f'{path}.html')
    except:
        response = models.get_page_from_title(path)
        return render('generic.html', page=response)

#has parameter audio to determine whether or not to generate audio
@app.route('/chat', methods=['POST'])
def chat():
    audio = request.json.get('audio')
    message = request.json['message']
    response = brain.generate_response(session["visitor"], message)
    #generate audio if audio is true
    audio_url = get_audio_url(response) if audio else None
    return jsonify({'data': response, 'audio_url': audio_url})

@app.route('/text-to-speech', methods=['POST'])
def text_to_speech():
    text = request.json['text']
    audio_url = get_audio_url(text)
    return jsonify({"audio_url": audio_url})

#ADMIN STARTS HERE

@app.route('/admin')
def admin():
    return render_template('admin/admin.html')

# Pages CRUD
@app.route('/admin/pages')
def list_pages():
    response = models.get_pages()
    return render_template('admin/pages/list.html', pages=response)

@app.route('/admin/pages/create', methods=['GET', 'POST'])
def create_page():
    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'icon': request.form['icon'],
            'content': request.form['content']
        }
        models.create_page(data)
        return redirect(url_for('list_pages'))
    return render_template('admin/pages/create.html')

@app.route('/admin/pages/<int:page_id>/edit', methods=['GET', 'POST'])
def edit_page(page_id):
    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'icon': request.form['icon'],
            'content': request.form['content']
        }
        models.update_page(page_id, data)
        return redirect(url_for('list_pages'))
    
    page_response = models.get_page(page_id)
    return render_template('admin/pages/edit.html', page=page_response)

@app.route('/admin/pages/<int:page_id>/delete', methods=['POST'])
def delete_page(page_id):
    models.delete_page(page_id)
    return redirect(url_for('list_pages'))

# Quotes CRUD
@app.route('/admin/quotes')
def list_quotes():
    response = supabase.table('quotes').select('*').execute()
    quotes = response.data
    return render_template('admin/quotes/list.html', quotes=quotes)

@app.route('/admin/quotes/create', methods=['GET', 'POST'])
def create_quote():
    if request.method == 'POST':
        data = {
            'quote': request.form['quote'],
            'author': request.form['author']
        }
        supabase.table('quotes').insert(data).execute()
        return redirect(url_for('list_quotes'))
    return render_template('admin/quotes/create.html')

@app.route('/admin/quotes/<int:quote_id>/edit', methods=['GET', 'POST'])
def edit_quote(quote_id):
    if request.method == 'POST':
        data = {
            'quote': request.form['quote'],
            'author': request.form['author']
        }
        supabase.table('quotes').update(data).eq('quote_id', quote_id).execute()
        return redirect(url_for('list_quotes'))
    
    response = supabase.table('quotes').select('*').eq('quote_id', quote_id).execute()
    quote = response.data[0]
    return render_template('admin/quotes/edit.html', quote=quote)

@app.route('/admin/quotes/<int:quote_id>/delete', methods=['POST'])
def delete_quote(quote_id):
    supabase.table('quotes').delete().eq('quote_id', quote_id).execute()
    return redirect(url_for('list_quotes'))


# Webhook listener
@app.route('/stripe_webhook', methods=['POST'])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get('STRIPE-SIGNATURE')
    result  = stripe.process_webhook(payload, sig_header)
    return result

# Custom voice page with voice id in url
@app.route('/custom_voice/<path:path>')
def custom_voice(path=None):
    #get voice id from path
    voice_id = path.split('/')[-1]
    voice = models.get_voice(voice_id)
    if(voice is None):
        return render('create_voice.html')
    else:
        return render('custom_voice.html', voice=voice)
    

#VOICE HANDLING STARTS HERE    
UPLOAD_FOLDER = 'temp_audio'
ALLOWED_EXTENSIONS = {'wav', 'mp3'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    
@app.route('/process_voice', methods=['POST'])
def process_voice():
    try:
        # Extract form data
        voice_name = request.form.get('voice_name')
        voice_photo = request.form.get('voice_photo')
        voice_prompt = request.form.get('voice_prompt')

        print(f"Received data: name={voice_name}, photo={voice_photo}, prompt={voice_prompt}")

        # Handle audio file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': 'No selected audio file'}), 400
        
        print(f"Received audio file: {audio_file.filename}")
        
        # call speechify
        try:
            speechify_response = speechify.create_voice(voice_name, audio_file)
        except requests.exceptions.RequestException as e:
            print(f"Speechify API error: {str(e)}")
            error_details = {
                'error': 'Speechify API error',
                'details': str(e),
                'status_code': e.response.status_code if hasattr(e, 'response') else None,
                'response_content': e.response.text if hasattr(e, 'response') else None
            }
            return jsonify(error_details), 500

        api_voice_id = speechify_response.get('id')
        if not api_voice_id:
            print("No voice ID returned from Speechify")
            return jsonify({'error': 'No voice ID returned from Speechify'}), 500

        # save voice to db
        try:
            data = {'id': api_voice_id, 'name': voice_name, 'photo': voice_photo, 'prompt': voice_prompt}
            models.create_voice(data)
        except Exception as e:
            print(f"Database error: {str(e)}")
            print(e.with_traceback())
            return jsonify({'error': 'Database error', 'details': str(e)}), 500

        return jsonify({
            'message': 'Voice processed successfully',
            'api_voice_id': api_voice_id
        }), 201

    except Exception as e:
        print(f"Unexpected error in process_voice: {str(e)}")
        return jsonify({'error': 'Unexpected error', 'details': str(e)}), 500
    
# HELPERS -TODO MOVE TO HELPERS

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
    random_quote = helpers.random_quote()
    pages = models.get_pages()
    links = models.get_profile_links()
    year = helpers.get_current_year()
    return render_template(template, sidebar_items = pages, quote=random_quote, links=links, year=year, **kwargs)

if __name__ == '__main__':
    app.run(debug=True)