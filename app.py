import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from dotenv import load_dotenv
import os
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.braintrust_integration import BraintrustAPI
import backend.models as models
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
    return render('index.html', bio=biography, picture_link='https://open.spotify.com/track/71glNHT4FultOqlau4zrFf?si=3ed90ad714c54a67')

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
    return render_template(template, **kwargs, sidebar_items = pages, quote=random_quote, links=links)

if __name__ == '__main__':
    app.run(debug=True)