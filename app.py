import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response
from dotenv import load_dotenv
import os
from functools import lru_cache


import datetime
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.braintrust_integration import BraintrustAPI
import backend.models as models
import backend.stripe_integration as stripe
import backend.helpers as helpers
import backend.cloudflare_integration as cloudflare

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
#set up session

cloudflare_url = os.getenv('CLOUDFLARE_PUBLIC_URL')
supabase = SupabaseClient()
speechify = SpeechifyAPI()
brain = BraintrustAPI()
cloudflare = cloudflare.CloudflareR2Integration()

@app.route('/')
def index(path=None):
    #see all session variables
    session["visitor"] = helpers.get_visitor_info()
    location = helpers.get_most_specific_location(helpers.get_location(session["visitor"]))
    #return one text option if no location data
    biography = f"""Hey there over in {location}! Chat with me below (and hear my voice)!""" if location != 'Unknown' else "Hey there! Chat with me below (and hear my voice)!"
    return render('index.html', bio=biography, profile_photo='https://media.licdn.com/dms/image/D5603AQH-aetvtESQbA/profile-displayphoto-shrink_400_400/0/1679704251439?e=1726704000&v=beta&t=zzuSGt4H0vOitpAhvNaWl3dDYGJYP9k00C8sA7fYKhs')

#has parameter audio to determine whether or not to generate audio
@app.route('/chat', methods=['POST'])
def chat():
    audio = request.json.get('audio')
    message = request.json.get('message')
    voice_id = request.json.get('voice_id')
    prompt = request.json.get('prompt')
    response = brain.generate_response(session["visitor"], message, prompt)
    #generate audio if audio is true
    if(audio):
        audio_url = get_audio_url(response, voice_id)
    else:
        audio_url = None
    return jsonify({'data': response, 'audio_url': audio_url})


#ADMIN STARTS HERE

@app.route('/admin')
def admin():
    return render('admin/admin.html')

@app.route('/admin/quotes')
def quotes():
    response = models.get_quotes()
    return render('admin/quotes.html', quotes=response)

@app.route('/delete_page/<int:page_id>', methods=['POST','DELETE'])
def delete_page(page_id):
    models.delete_page(page_id)
    print(jsonify({'message': 'Page deleted successfully'}), 200)
    return redirect(url_for('pages'))


@app.route('/delete_quote/<int:quote_id>', methods=['POST','DELETE'])
def delete_quote(quote_id):
    models.delete_quote(quote_id)
    print(jsonify({'message': 'Quote deleted successfully'}), 200)
    return redirect(url_for('quotes'))

@app.route('/admin/pages', methods=['GET'])
def pages():
    response = models.get_pages()
    print(response)
    # Handle delete request
    return render('admin/pages.html', pages=response)

@app.route('/admin/voices')
def admin_voices():
    voices = models.get_voices()
    return render('voices.html', voices=voices)

@app.route('/about')
def about():
    timeline = helpers.get_timeline()

    return render('about.html', timeline=timeline)

@app.route('/admin/update_quote/<int:quote_id>', methods=['GET','POST'])
@app.route('/admin/update_quote', methods=['GET','POST'])
def update_quote(quote_id=None):
    if quote_id:
        quote = models.get_quote(quote_id)
    else:
        quote = None

    # Handle form submission
    if request.method == 'POST':
        print(request.form)
        data = {
            'text': request.form['text'],
            'author': request.form['author']
        }

        if quote_id:
            models.update_quote(quote_id, data)
        else:
            models.create_quote(data)
        return redirect(url_for('quotes'))
    return render('admin/update_quote.html', db_quote=quote)

@app.route('/admin/update_page/<int:page_id>', methods=['GET','POST'])
@app.route('/admin/update_page', methods=['GET', 'POST'])
def update_page(page_id=None):
    if page_id:
        page = models.get_page(page_id)
    else:
        page = None

    # Handle form submission
    if request.method == 'POST':
        data = {
            'title': request.form['title'],
            'icon': request.form['icon'],
            'content': request.form['content']
        }

        if page_id:
            models.update_page(page_id, data)
        else:
            models.create_page(data)
        return redirect(url_for('pages'))
    return render('admin/update_page.html', page=page)


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
    voice_id = path.split('/')[-1]
    #get voice id from path
    admin_bypass = False
    payment_status = models.check_voice_payment(voice_id)
    payed = payment_status['payed']
    url = payment_status['url']
    #check with stripe if payment has been made
    payment_made = admin_bypass or payed
    voice = models.get_voice(voice_id)
    if(voice is None):
        return render('create_voice.html')
    else:
        return render('custom_voice.html', voice=voice, admin_bypass=admin_bypass, payment_made=payment_made, payment_url = url)
    

# Custom voices
@app.route('/voices')
def voices(path=None):
    #get voice id from path
    voices = models.get_voices()
    return render('voices.html', voices=voices)

@app.route('/update_voice/<int:voice_id>')
def update_voice(voice_id):
    voice = models.get_voice(voice_id)
    return render('update_voice.html', voice=voice)

@app.route('/create_voice')
def create_voice():
    return render('create_voice.html')

# Process or update voice
@app.route('/process_voice/<int:voice_id>', methods=['POST'])
@app.route('/process_voice', methods=['POST'])
def process_voice(voice_id=None):
    try:
        # Extract form data
        voice_name = request.form.get('voice_name')
        voice_photo = request.form.get('voice_photo')
        voice_prompt = request.form.get('voice_prompt')

        # Handle image upload
        try:
            voice_photo = cloudflare.handle_image_upload(request)
        except Exception as e:
            print(e)
            return jsonify({'error': 'Image upload failed', 'details': str(e)}), 500
        # upload voice to speechify
        try:
            api_voice_id = speechify.handle_voice_upload(request, voice_name)
        except Exception as e:
            return e

        # save voice to db

        if voice_id:
            try:
                data = {'id': api_voice_id, 'name': voice_name, 'photo': voice_photo, 'prompt': voice_prompt}
                models.update_voice(voice_id, data)
            except Exception as e:
                print(f"Database error: {str(e)}")
                return jsonify({'error': 'Database error', 'details': str(e)}), 500
            return jsonify({'message': 'Voice updated successfully'}), 200
        else: 
            try:
                data = {'id': api_voice_id, 'name': voice_name, 'photo': voice_photo, 'prompt': voice_prompt}
                voice_id = models.create_voice(data)['voice_id']
            except Exception as e:
                print(f"Database error: {str(e)}")
                print(e.with_traceback())
                return jsonify({'error': 'Database error', 'details': str(e)}), 500
        
            #create stripe checkout session
            try:

                session = stripe.create_checkout_voice_ai(voice_id)
                session_id = session['id']
                payment_url = session['url']
                models.update_voice_payment(voice_id, session_id)

            except Exception as e:
                print(f"Error creating checkout session: {str(e)}")
                return jsonify({'error': 'Error creating checkout session', 'details': str(e)}), 500

        return jsonify({
            'message': 'Voice processed successfully',
            'api_voice_id': voice_id,
            'url': payment_url
        }), 201

    except Exception as e:
        print(f"Unexpected error in process_voice: {str(e)}")
        return jsonify({'error': 'Unexpected error', 'details': str(e)}), 500

# create generic route that loads whatever html is listed in route and a 404 if not found in directory
@app.route('/<path:path>')
def generic(path):
    try:
        return render(f'{path}.html')
    except:
        response = models.get_page_from_title(path)
        return render('generic.html', page=response)
    
#delete voices from speechify
@app.route('/delete_voice/<string:voice_id>')
def delete_voice(voice_id):
    if voice_id:
        api_voice_id = models.get_voice(voice_id).get('api_voice_id')
        models.delete_voice(voice_id)
        speechify.delete_voice(api_voice_id)
        print("Voices delete succesfully")
    return redirect(url_for('voices'))
    
#delete voices from speechify
@app.route('/delete_voices/<string:voice_id>')
def delete_voices(voice_id=None):
    if voice_id == "ALL":
        speechify.delete_voices()
    else:
        speechify.delete_voice(voice_id)
    return jsonify({'message': 'Voices deleted successfully'}), 200

#start random routes

@app.route('/golf', methods=['GET', 'POST'])
def golf():
    if request.method == 'POST':
        date = datetime.datetime.strptime(request.form['date'], '%Y-%m-%d')
        score = int(request.form['score'])
        course_id = request.form['course_id']
        tee = request.form['tee']
        is_nine = request.form.get('is_nine_hole', False)
        
        score_data = {
            'date': date,
            'score': score,
            'course_id': course_id,
            'tee': tee,
            'is_nine_hole': is_nine
        }
        models.create_golf_score(score_data)
        
        # Invalidate the cache for get_last_20_golf_scores
        get_last_20_golf_scores.cache_clear()
        
        return jsonify({"message": "Score added successfully"}), 200
    
    scores = get_last_20_golf_scores()
    handicap, used_score_ids = calculate_handicap(scores)
    courses = get_golf_courses()

    # Mark the scores used in handicap calculation
    for score in scores:
        score['used_in_handicap'] = score['id'] in used_score_ids
    
    return render('golf.html', courses=courses, scores=scores, handicap=handicap)

@app.route('/add_course', methods=['POST'])
def add_course():
    name = request.form['name']
    rating = float(request.form['rating'])
    slope = float(request.form['slope'])
    
    new_course = {
        "name": name,
        "rating": rating,
        "slope": slope
    }
    
    response = models.create_golf_course(new_course)
    
    # Invalidate the cache for get_golf_courses
    get_golf_courses.cache_clear()
    
    if response.data:
        return jsonify({"message": "Course added successfully", "course": response.data[0]}), 200
    else:
        return jsonify({"error": "Failed to add course"}), 400

@lru_cache(maxsize=1)
def get_last_20_golf_scores():
    return models.get_last_20_golf_scores()

@lru_cache(maxsize=1)
def get_golf_courses():
    return models.get_golf_courses()

@lru_cache(maxsize=128)
def get_golf_course(course_id):
    return models.get_golf_course(course_id)

def calculate_handicap(scores):
    if len(scores) < 5:
        return None, []
    
    # Calculate differentials
    differentials = []
    for score in scores:
        course = get_golf_course(score['course_id'])
        if score['is_nine_hole']:
            differential = (score['score'] * 2 - course['rating']) * 113 / course['slope']
        else:
            differential = (score['score'] - course['rating']) * 113 / course['slope']
        differentials.append((differential, score['id']))
    
    # Sort differentials and take the best ones based on the number of scores
    differentials.sort(key=lambda x: x[0])
    num_scores = len(differentials)
    if num_scores <= 6:
        handicap_differentials = differentials[:1]
    elif num_scores <= 8:
        handicap_differentials = differentials[:2]
    elif num_scores <= 10:
        handicap_differentials = differentials[:3]
    elif num_scores <= 12:
        handicap_differentials = differentials[:4]
    elif num_scores <= 14:
        handicap_differentials = differentials[:5]
    elif num_scores <= 16:
        handicap_differentials = differentials[:6]
    elif num_scores <= 18:
        handicap_differentials = differentials[:7]
    else:
        handicap_differentials = differentials[:8]
    
    # Calculate the handicap index
    handicap_index = sum(diff for diff, _ in handicap_differentials) / len(handicap_differentials) * 0.96
    used_score_ids = [score_id for _, score_id in handicap_differentials]
    
    return round(handicap_index, 1), used_score_ids
    
# HELPERS -TODO MOVE TO HELPERS

def get_audio_url(text, id=None):
    if id:
        id = models.get_voice(id).get('api_voice_id')
        audio_data, audio_format = speechify.convert_to_speech(text, id)
    else:
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
    random_quote = helpers.random_quote(models.get_quotes())
    pages = models.get_pages()
    links = models.get_profile_links()
    year = helpers.get_current_year()
    return render_template(template, sidebar_items = pages, quote=random_quote, links=links, year=year, **kwargs)

if __name__ == '__main__':
    app.run(debug=True)