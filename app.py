import base64
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, send_from_directory, send_file
from asgiref.sync import async_to_sync
from dotenv import load_dotenv
import os
from functools import lru_cache
from datetime import datetime
import xml.etree.ElementTree as ET
import re
import time
import io
import asyncio
from uuid import uuid4
import logging
from concurrent.futures import ThreadPoolExecutor
import redis
from urllib.parse import quote_plus
from backend.multion_integration import multion_api
import json
import datetime
from backend.supabase_db import SupabaseClient
from backend.speechify_integration import SpeechifyAPI
from backend.braintrust_integration import BraintrustAPI
import backend.models as models
import backend.stripe_integration as stripe
import backend.helpers as helpers
import backend.cloudflare_integration as cloudflare
import backend.claude_integration as claude
import traceback
import requests

from threading import Lock
from collections import defaultdict

load_dotenv()

app = Flask(__name__)
logging.basicConfig(level=logging.ERROR)
executor = ThreadPoolExecutor(max_workers=5)  # Adjust the number of workers as needed
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your_secret_key')
#set up session

#region redis
## set up redis
# URL encode the password
password = os.getenv('KV_REST_API_TOKEN')
encoded_password = quote_plus(password)

# Construct the Redis URL with the encoded password
redis_url = f"rediss://default:{encoded_password}@caring-perch-58102.upstash.io:6379"

print(f"Connecting to: {redis_url}")

try:
    # Create a connection pool
    pool = redis.ConnectionPool.from_url(
        redis_url,
        socket_timeout=5,
        socket_connect_timeout=5
    )
    
    # Create a Redis client using the connection pool
    r = redis.Redis(connection_pool=pool)
    
    # Test the connection
    pong = r.ping()
    print(f"Successfully connected to Redis. Ping response: {pong}")

except redis.exceptions.ConnectionError as e:
    print(f"Failed to connect to Redis: {e}")
except Exception as e:
    print(f"An error occurred: {e}")
#endregion

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
    biography = "Hey there! Chat with me below (and hear my voice)!"
    return render('index.html', bio=biography, profile_photo='https://media.licdn.com/dms/image/D5603AQH-aetvtESQbA/profile-displayphoto-shrink_400_400/0/1679704251439?e=1726704000&v=beta&t=zzuSGt4H0vOitpAhvNaWl3dDYGJYP9k00C8sA7fYKhs')

#has parameter audio to determine whether or not to generate audio
@app.route('/chat', methods=['POST'])
def chat():
    audio = request.json.get('audio')
    message = request.json.get('message')
    voice_id = request.json.get('voice_id')
    prompt = request.json.get('prompt')
    response = brain.generate_response(session["visitor"], message, voice_id, prompt )
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
    # Handle delete request
    return render('admin/pages.html', pages=response)

@app.route('/admin/voices')
def admin_voices():
    voices = models.get_voices()
    return render('voices.html', voices=voices)

@app.route('/about')
def about():
    timeline = helpers.get_timeline()
    print(timeline)
    return render('about.html', timeline=timeline)

@app.route('/about_me')
def about_me():
    return render('about_me.html')

@app.route('/favorite-content')
def favorite_content():
    content_items = [
        {
            'id': '1816825251218501832',
            'description': 'A heartwarming, kinda sad video that will touch your heart.',
            'category' : 'cry',
            'link' : 'https://twitter.com/ceciarmy/status/1816825251218501832'
        },
        {
            'id': 'C8cGsQDt4rQ',
            'description': 'A short documentary about a dog that speaks - watch all 8 reels.',
            'category' : 'laugh',
            'link' : 'https://instagram.com/p/C8cGsQDt4rQ'
        },
        {
            'id': 'vAoADCSpD-8',
            'description': 'Listen to this, its live.',
            'category' : 'smile',
            'link' : 'https://youtube.com/watch?v=vAoADCSpD-8'
        }
        # Add more items as needed
    ]

    top_movies = [
    "About Time",
    "Gladiator",
    "The Dark Knight",
    "Love Actually",
    "Crazy Stupid Love",
    "Casino Royale",
    "Definitely Maybe",
    "Wedding Crashers",
    "Interstellar",
    "Dune"]

    return render('favourite_posts.html', content_items=content_items, top_movies=top_movies)

@app.route('/speedtest/download')
def download_test():
    file_size = 1024 * 1024  # 1 MB file
    random_data = os.urandom(file_size)
    return send_file(
        io.BytesIO(random_data),
        mimetype='application/octet-stream',
        as_attachment=True,
        download_name='speedtest.bin'
    )

@app.route('/speedtest/upload', methods=['POST'])
def upload_test():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected for uploading'}), 400

    start_time = time.time()
    file_size = 0
    for chunk in file:
        file_size += len(chunk)
    end_time = time.time()
    
    duration = end_time - start_time
    if duration == 0:
        return jsonify({'error': 'Test duration too short'}), 400
    
    speed_bps = (file_size * 8) / duration
    speed_mbps = speed_bps / (1024 * 1024)
    
    return jsonify({'speed': speed_mbps})

@app.route('/speed_test')
def speed_test():
    return render('speedtest.html')

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
def update_page(page_id):
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

        models.update_page(page_id, data)

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
    payed = False
    url = '/error'
    try:
        payment_status = models.check_voice_payment(voice_id)
        payed = payment_status['payed']
        url = payment_status['url']
    except Exception as e:
        print(f"Error checking voice payment: {str(e)}")    
    #check with stripe if payment has been made
    payment_made = admin_bypass or payed
    voice = models.get_voice(voice_id)
    if(voice is None):
        return render('create_voice.html')
    else:
        return render('custom_voice.html', voice=voice, admin_bypass=admin_bypass, payment_made=payment_made, payment_url = url)
    
##PROJECTS
# Custom voices
@app.route('/projects/voices')
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
            # to lower case
            voice_photo = cloudflare.handle_image_upload(request, voice_name.lower())
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
                return jsonify({'error': 'Database error', 'details': str(e)}), 500
        
            #create stripe checkout session
            try:
                session = stripe.create_checkout_voice_ai(voice_id)
                if session:
                    session_id = session.id
                    payment_url = session.url
                    models.update_voice_payment(voice_id, session_id)
                else:
                    raise Exception("Failed to create checkout session")

            except Exception as e:
                print(f"Error creating checkout session: {str(e)}")
                just_the_string = traceback.format_exc()
                return jsonify({'error': just_the_string, 'details': str(e)}), 500

        return jsonify({
            'message': 'Voice processed successfully',
            'api_voice_id': voice_id,
            'url': payment_url
        }), 201

    except Exception as e:
        print(f"Unexpected error in process_voice: {str(e)}")
        return jsonify({'error': 'Unexpected error', 'details': str(e)}), 500

@app.route('/projects/emails')
def email_signature(path=None):
    #get voice id from path
    return render('emails.html')
    
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

@app.route('/sports', methods=['GET'])
def sports():
    return render('sports.html')

@app.route('/admin/golf', methods=['GET', 'POST'])
def admin_golf():
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


@app.route('/sports/golf', methods=['GET'])
def golf():    
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

@app.route('/sports/cycling', methods=['GET', 'POST'])
def cycling():
    return render('cycling.html')

@app.route('/recipes')
def recipes():
    #TODO LOAD FROM DB
    recipes = [
        {"id": 1,
            "name": "Breakfast Cereal",
            "description": "Flawless combination for a quick breakfast.",
            "prep_time": "1 min",
            "cook_time": "1 min",
            "servings": "1"
        },
        {
            "id": 2,
            "name": "Butter Garlic Shrimp",
            "description": "A delicious and quick shrimp dish featuring a rich butter and garlic sauce.",
            "prep_time": "10 min",
            "cook_time": "10 min",
            "servings": "4"
        },
        {
            "id": 3,
            "name": "Caprese",
            "description": "Simple is better here...",
            "prep_time": "5 min",
            "cook_time": "1 min",
            "servings": "2"
        },
        {
            "id": 4,
            "name": "Pomodoro Pasta",
            "description": "Weeknight-friendly pasta dish with ahomemade pomodoro sauce.",
            "prep_time": "10 min",
            "cook_time": "20 min",
            "servings": "3/4"
        }
        # Add more recipes here
    ]
    return render('recipes.html', recipes=recipes)

@app.route('/api/recipes/<int:recipe_id>')
def get_recipe(recipe_id):
    # In a real application, you would fetch this data from a database
    recipes = {
        2: {
            "name": "Butter Garlic Shrimp",
            "description": "A delicious and quick shrimp dish featuring a rich butter and garlic sauce, perfect for a weeknight dinner or special occasion.",
            "ingredients": [
                "1 pound large shrimp, peeled and deveined",
                "4 tablespoons unsalted butter",
                "4-6 cloves garlic, minced",
                "1/4 cup white wine or chicken broth",
                "2 tablespoons fresh lemon juice",
                "1/4 cup chopped fresh parsley",
                "Salt and black pepper to taste",
                "Red pepper flakes (optional)"
            ],
            "instructions": [
                "Pat shrimp dry and season with salt and pepper.",
                "Melt butter in a large skillet over medium heat. Add minced garlic and cook for 1 minute.",
                "Add shrimp to the skillet and cook for 2-3 minutes per side until pink and curled.",
                "Pour in white wine or chicken broth and lemon juice. Simmer for 2-3 minutes until sauce reduces slightly.",
                "Remove from heat and stir in chopped parsley. Add red pepper flakes if desired.",
                "Taste and adjust seasoning if needed.",
                "Serve immediately."
            ]
            },
        1: {
            "name": "Weetabix Breakfast with Nutella Toast",
            "description": "A simple and satisfying breakfast.",
            "ingredients": [
                "2 Weetabix biscuits",
                "200ml lactose-free milk",
                "1 tablespoon sugar",
                "1 ripe banana",
                "2 slices of bread",
                "2 tablespoons Nutella"
            ],
            "instructions": [
                "Place 2 Weetabix biscuits in a bowl.",
                "Pour 200ml of lactose-free milk over the Weetabix.",
                "Sprinkle 1 tablespoon of sugar over the cereal.",
                "Grab a banana and peel it.",
                "Toast 2 slices of bread until golden brown.",
                "Spread 1 tablespoon of Nutella on each slice of toast.",
                "Serve the Weetabix, Banana, and Nutella toast together."
            ]
        },
        3: {
            "name": "Authentic Caprese Salad",
            "description": "Classic caprese.",
            "ingredients": [
                "2 large ripe tomatoes, preferably heirloom or beefsteak",
                "200g fresh buffalo mozzarella (mozzarella di bufala)",
                "1 bunch fresh basil leaves",
                "2 tablespoons high-quality extra virgin olive oil",
                "1 tablespoon aged balsamic vinegar from Modena",
                "Flaky sea salt and freshly ground black pepper to taste"
            ],
            "instructions": [
                "Wash and slice the tomatoes into 1/4 inch thick rounds.",
                "Drain and slice the buffalo mozzarella into similar thickness as the tomatoes.",
                "On a serving plate, alternate slices of tomato and buffalo mozzarella, slightly overlapping them.",
                "Tuck whole fresh basil leaves between the tomato and mozzarella slices.",
                "Drizzle the extra virgin olive oil over the salad.",
                "Carefully drizzle the aged balsamic vinegar over the salad.",
                "Season with flaky sea salt and freshly ground black pepper to taste.",
                "Let the salad rest for 5 minutes at room temperature to allow flavors to meld.",
                "Serve immediately, enjoying the pure flavors of the high-quality ingredients."
            ]
        },
        4: {
            "name": "Two-Tomato Pomodoro Pasta",
            "description": "A delicious pasta dish featuring a homemade pomodoro sauce.",
            "ingredients": [
                "500g pasta (such as spaghetti or penne)",
                "800g ripe plum tomatoes",
                "250g cherry tomatoes",
                "6 cloves of garlic, minced",
                "1/2 cup extra virgin olive oil, plus extra for finishing",
                "1 tsp salt, plus more to taste",
                "1/4 cup fresh basil leaves, torn",
                "1/4 cup freshly grated Parmigiano-Reggiano cheese",
                "Freshly ground black pepper to taste"
            ],
            "instructions": [
                "Bring a large pot of salted water to boil for the pasta.",
                "Meanwhile, score an X on the bottom of each plum tomato. In a separate pot, bring water to a boil. Blanch plum tomatoes for 30 seconds, then remove with a slotted spoon to a bowl of ice water. Peel and roughly chop the tomatoes.",
                "In a large, deep skillet, heat 1/4 cup of olive oil over medium-high heat. Add the cherry tomatoes and sear quickly, shaking the pan, until they start to burst, about 2-3 minutes.",
                "Reduce heat to medium, add half the minced garlic and cook until fragrant, about 30 seconds.",
                "Add the chopped plum tomatoes and 1 tsp of salt. Simmer for about 20 minutes, stirring occasionally, until the sauce thickens.",
                "While the sauce is simmering, cook the pasta in the pot of boiling salted water until al dente. Reserve 1 cup of pasta water before draining.",
                "Once the sauce has thickened, stir in the remaining garlic and olive oil. Cook for another minute.",
                "Add the drained pasta to the skillet with the sauce. Toss to coat, adding reserved pasta water as needed to reach desired consistency.",
                "Remove from heat and stir in torn basil leaves.",
                "Serve immediately, topping each portion with grated Parmigiano-Reggiano, a drizzle of extra virgin olive oil, and freshly ground black pepper."
            ]
        }
        # Add more recipes here
    }
    return jsonify(recipes.get(recipe_id, {'error': 'Recipe not found'}))


def should_include_in_sitemap(rule):
    """Determine if a rule should be included in the sitemap."""
    # Exclude static files, admin routes, and routes with parameters
    exclude_patterns = [
        r'^/static/',
        r'^/admin/',
        r'^/api/',
    ]
    
    if any(re.match(pattern, rule.rule) for pattern in exclude_patterns):
        return False
    
    # Exclude routes with parameters (except optional ones)
    if any(arg for arg in rule.arguments if not rule.defaults or arg not in rule.defaults):
        return False
    
    return True

def get_priority_and_changefreq(rule):
    """Determine priority and change frequency for a given rule."""
    if rule.rule == '/' or 'about' in rule.rule:
        return "1.0", "daily"
    elif any(keyword in rule.rule for keyword in ['projects', 'sports', 'voices']):
        return "0.8", "weekly"
    elif 'custom_voice' in rule.endpoint:
        return "0.7", "weekly"
    else:
        return "0.6", "monthly"

def generate_sitemap():
    """Generate a fully dynamic sitemap."""
    root = ET.Element("urlset")
    root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")

    # Discover all routes in the Flask app
    for rule in app.url_map.iter_rules():
        if should_include_in_sitemap(rule):
            url = ET.SubElement(root, "url")
            loc = ET.SubElement(url, "loc")
            
            # Generate the full URL
            loc.text = url_for(rule.endpoint, _external=True, **rule.defaults if rule.defaults else {})
            
            lastmod = ET.SubElement(url, "lastmod")
            lastmod.text = datetime.datetime.now().strftime("%Y-%m-%d")
            
            priority, changefreq = get_priority_and_changefreq(rule)
            
            cf = ET.SubElement(url, "changefreq")
            cf.text = changefreq
            
            pri = ET.SubElement(url, "priority")
            pri.text = priority

    return ET.tostring(root, encoding="unicode")

@app.route('/sitemap.xml')
def sitemap():
    sitemap_xml = generate_sitemap()
    return Response(sitemap_xml, mimetype='application/xml')

@app.route('/robots.txt')
def robots_txt():
    return send_from_directory(app.static_folder, 'robots.txt')

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

@app.route('/price-tracker')
def price_tracker():
    trading_pairs = ["btc_usd", "eth_usd", "usd_mxn"]  # Add more pairs as needed
    currency_data = helpers.get_bitso_data(trading_pairs)
    
    # Add custom names and symbols for each currency
    currency_info = {
        "btc_usd": {"name": "Bitcoin", "base" : "USD"},
        "eth_usd": {"name": "Ethereum", "base" : "USD"},
        "usd_mxn": {"name": "US Dollar", "base" : "MXN"},
    }
    
    for pair in currency_data:
        currency_data[pair]["name"] = currency_info[pair]["name"]
        currency_data[pair]["base"] = currency_info[pair]["base"]
    
    return render('crypto.html', currencies=currency_data)

async def generate_page_async(task_id, prompt, page_title, icon, route):
    print("GENERATING PAGE")
    try:
        # Generate HTML content using Claude
        logging.debug(f"Generating HTML content for task {task_id}")
        html_content = await claude.generate_html(prompt)
        logging.debug(f"HTML content generated for task {task_id}")

        # Create page in the database
        logging.debug(f"Attempting to create page in database for task {task_id}")
        page_data = {'title': page_title, 'icon': icon, 'content': html_content, 'route': route, 'prompt': prompt}
        models.create_page(page_data)
        
        logging.debug(f"Page created in database for task {task_id}")

        # Update task status in Redis
        r.hmset(f'task:{task_id}', {
            'status': 'completed',
            'type': 'generate_page'
        })
        logging.debug(f"Task {task_id} completed successfully")
    except Exception as e:
        logging.error(f"Error in generate_page_async for task {task_id}: {str(e)}")
        r.hmset(f'task:{task_id}', {
            'status': 'failed',
            'type': 'generate_page'
        })

def generate_page_sync(task_id, prompt, page_title, icon, route):
    try:
        asyncio.run(generate_page_async(task_id, prompt, page_title, icon, route))
    except Exception as e:
        r.hmset(f'task:{task_id}', {
            'status': 'failed',
            'type': 'generate_page'
        })

@app.route('/projects/generate_page', methods=['GET', 'POST'])
def generate_page():
    if request.method == 'POST':
        prompt = request.form['prompt']
        page_title = request.form['page_title']
        icon = request.form['page_icon']
        route = "pages/"+request.form['page_route']
        
        # Create a new task
        task_id = str(uuid4())
        r.hmset(f'task:{task_id}', {
            'status': 'pending',
            'type': 'generate_page'
        })
        
        # Start asynchronous task in a separate thread
        executor.submit(generate_page_sync, task_id, prompt, page_title, icon, route)
        print("SENDING RESPONSE TO FRONT END")
        
        return jsonify({
        'message': 'Page generation initiated. The page will be ready in a few minutes.',
        'task_id': task_id
        }), 202
    
    generated_pages = models.get_pages()
    return render('generate_page.html', generated_pages=generated_pages)

@app.route('/check_page_status/<task_id>')
def check_page_status(task_id):
    task_data = r.hgetall(f'task:{task_id}')
    if not task_data:
        logging.warning(f"Task {task_id} not found")
        return jsonify({'status': 'not_found'}), 404
    
    # Decode bytes to strings
    task_data = {k.decode('utf-8'): v.decode('utf-8') for k, v in task_data.items()}
    
    status = task_data.get('status', 'unknown')
    task_type = task_data.get('type', 'unknown')
    
    if status == 'completed':
        logging.info(f"Task {task_id} completed successfully")
        return jsonify({'status': status, 'type': task_type})
    elif status == 'failed':
        logging.error(f"Task {task_id} failed")
        return jsonify({'status': status, 'type': task_type})
    else:
        logging.debug(f"Task {task_id} still pending")
        return jsonify({'status': status, 'type': task_type})

@app.route('/get_generated_pages')
def get_generated_pages():
    generated_pages = models.get_pages()
    return jsonify(generated_pages)

@app.route('/delete_generated_page/<page_id>', methods=['POST'])
def delete_generated_page(page_id):
    models.delete_page(page_id)
    return redirect(url_for('generate_page'))

@app.route('/update_generated_page/<page_id>', methods=['POST'])
def update_generated_page(page_id):
    new_prompt = request.form['new_prompt']
    
    # Generate new HTML content using Claude
    new_html_content = async_to_sync(claude.generate_html)(new_prompt)
    old_page = models.get_page(page_id)
    old_page['content'] = new_html_content
    models.update_page(page_id, old_page)
    
    return redirect(url_for('generate_page'))

@app.route('/tools')
def tools():
    return render('tools.html')

@app.route('/tools/news')
def news():
    categories = models.get_categories()  # Fetch categories from the database
    return render('news.html', categories=categories)

@app.route('/api/news')
def get_news():
    categories = models.get_categories()
    news_articles = {}
    # for category in categories:
        # commenting because multion api sucks and is expensive AF
        # news_articles[category['name']] = multion_api.get_latest_headline(category)
    return jsonify(news_articles)

@app.route('/api/add_category', methods=['POST'])
def add_category():
    category = request.json.get('category')
    if category:
        models.add_category(category)
        return jsonify({"success": True, "message": "Category added successfully"}), 200
    return jsonify({"success": False, "message": "Invalid category"}), 400

@app.route('/api/remove_category/<category_id>', methods=['POST'])
def remove_category(category_id):
    if category_id:
        models.remove_category(category_id)
        return jsonify({"success": True, "message": "Category removed successfully"}), 200
    return jsonify({"success": False, "message": "Invalid category"}), 400

@app.route('/receipt_analyzer', methods=['GET'])
def receipt_analyzer():
    return render('receipt_analyzer.html')

@app.route('/analyze_receipt', methods=['POST'])
def analyze_receipt():
    if 'photo' not in request.files:
        return jsonify({'error': 'No photo provided'}), 400
    
    photo = request.files['photo']
    if photo.filename == '':
        return jsonify({'error': 'No photo selected'}), 400
    
    # Get the custom structure
    structure = request.form.get('structure')
    if not structure:
        return jsonify({'error': 'No output structure provided'}), 400
    
    try:
        structure = json.loads(structure)
    except json.JSONDecodeError:
        return jsonify({'error': 'Invalid JSON structure'}), 400
    
    # Read the image file
    image_data = photo.read()
    
    # Encode the image to base64
    base64_image = base64.b64encode(image_data).decode('utf-8')
    
    # Prepare the request to GPT-4 Vision API
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}"
    }
    
    prompt = f"""
    Analyze this receipt image and provide a structured output according to the following JSON schema:
    {json.dumps(structure, indent=2)}
    
    Please ensure that your response strictly adheres to this structure and can be parsed as valid JSON.
    Do not include any markdown formatting or code block syntax in your response.
    Ensure that all JSON objects and arrays are properly closed.
    """
    
    payload = {
        "model": "gpt-4o-2024-08-06",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000  # Increased from 500 to 1000
    }
    
    # Make the request to GPT-4 Vision API
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    print(response.json())
    if response.status_code == 200:
        result = response.json()
        print(result)
        # Extract the structured output from the GPT-4 Vision response
        structured_output = result['choices'][0]['message']['content']
        
        # Remove markdown code block if present
        structured_output = re.sub(r'```json\n?|\n?```', '', structured_output).strip()

        print(structured_output)
        
        try:
            # Attempt to parse the output as JSON
            parsed_output = json.loads(structured_output)
            return jsonify(parsed_output)
        except json.JSONDecodeError as e:
            # If JSON is incomplete, attempt to fix it
            try:
                fixed_output = self.fix_incomplete_json(structured_output)
                return jsonify(json.loads(fixed_output))
            except:
                return jsonify({
                    'error': 'Failed to parse GPT-4 output as JSON',
                    'raw_output': structured_output,
                    'json_error': str(e)
                }), 500
    else:
        return jsonify({'error': 'Failed to analyze the receipt'}), 500

def fix_incomplete_json(self, json_string):
    # Count opening and closing braces and brackets
    open_braces = json_string.count('{')
    close_braces = json_string.count('}')
    open_brackets = json_string.count('[')
    close_brackets = json_string.count(']')
    
    # Add missing closing braces and brackets
    json_string += '}' * (open_braces - close_braces)
    json_string += ']' * (open_brackets - close_brackets)
    
    return json_string

# create generic route that loads whatever html is listed in route and a 404 if not found in directory
@app.route('/<path:path>')
def generic(path):
    print("Generic path found: ")
    try:
        return render(f'{path}.html')
    except:
        response = models.get_page_from_route(path)
        return render('generic.html', page=response)

def render(template, **kwargs):
    # avoid rendering things form db on index page to load fast.
    random_quote = helpers.random_quote(models.get_quotes())
    pages = models.get_pages()
    links = models.get_profile_links()
    year = helpers.get_current_year()
    return render_template(template, sidebar_items = pages, quote=random_quote, links=links, year=year, **kwargs)


if __name__ == '__main__':
    app.run(debug=True)