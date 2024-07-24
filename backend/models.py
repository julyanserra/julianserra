# This file contains the models for the backend.
import backend.helpers as helpers
from flask import request, session
from backend.supabase_db import SupabaseClient
import backend.stripe_integration as stripe
from dotenv import load_dotenv
import json
import os
import datetime

from backend.supabase_db import SupabaseClient
load_dotenv()

cloudflare_public = os.getenv('CLOUDFLARE_PUBLIC_ACCESS')
base = SupabaseClient()

# Quotes
def get_quotes():
    quotes = base.fetch_quotes()
    return quotes

def get_quote(quote_id):
    quotes = base.fetch_quote(quote_id)
    if len(quotes) > 0:
        return quotes[0]

def create_quote(data):
    new_quote = base.create_quote(data['text'], data['author'])
    return new_quote

def update_quote(quote_id, data):
    updated_quote = base.update_quote(quote_id, data['text'], data['author'])
    return updated_quote

def delete_quote(quote_id):
    success = base.delete_quote(quote_id)
    return success

# Pages
def get_pages():
    pages = base.fetch_pages()
    return pages

def get_page(page_id):
    pages = base.fetch_page(page_id)
    if len(pages) > 0:
        pages = transformContent(pages)
        return pages[0]
    
def get_page_from_title(title):
    pages = base.fetch_page_from_title(title)
    if len(pages) > 0:
        pages = transformContent(pages)
        return pages[0]

def create_page(data):
    content = processContent(data['content'])
    new_page = base.create_page(data['title'], data['icon'], content)
    return new_page

def update_page(page_id, data):
    content = processContent(data['content'])
    updated_page = base.update_page(page_id, data['title'], data['icon'], content)
    return updated_page

def delete_page(page_id):
    success = base.delete_page(page_id)
    return success
    
def processContent(content):
    # get the content and create an array separating with new lines
    #jsonify the array
    jscontent = json.dumps(content.split(';'))
    print(jscontent)
    return jscontent

def transformContent(pages, admin=False):
    for page in pages:
        try:
            # Parse the outer list
            outer_list = json.loads(page['content'])
            print(outer_list)
            # Get the first (and only) element, which should be a JSON string
            inner_json = outer_list[0]
            page['content'] = json.loads(inner_json)
        except (json.JSONDecodeError, IndexError):
        # If parsing fails, return an empty list
            print("Error parsing content")
    return pages

# def makeContentArray()
    
# Authentication
def login(email, password):
    success = base.login(email, password)
    return success

# Chat history
def get_chat_history(user_id):
    chat_history = base.fetch_chat_history(user_id)
    return chat_history

def get_profile_links():
    links = base.fetch_profile_links()
    if len(links) <= 0:
        links = helpers.get_default_links()
    return links


# ai voice section
def get_voice(voice_id):
    voice = base.fetch_ai_voice(voice_id)
    if len(voice) > 0:
        voice = helpers.handle_url_for_voice(cloudflare_public, voice)
        return voice[0]
    
def get_voice_from_api_id(api_voice_id):
    voice = base.fetch_ai_voice_by_api_id(api_voice_id)
    if len(voice) > 0:
        voice = helpers.handle_url_for_voice(cloudflare_public, voice)
        return voice[0]
    
def create_voice(data):
    voice = base.create_ai_voice(data['id'], data['name'], data['photo'], data['prompt'])
    return voice.data[0]

def get_voices():
    voices = base.fetch_ai_voices()
    voices = helpers.handle_url_for_voice(cloudflare_public, voices)
    return voices

def update_voice(voice_id, data):
    if(data['photo'] == None):
        voice = base.update_ai_voice_without_photo(voice_id, data['id'], data['name'], data['prompt'])
    else: 
        voice = base.update_ai_voice(voice_id, data['id'], data['name'], data['photo'], data['prompt'])
    return voice

def delete_voice(voice_id):
    voice = base.delete_ai_voice(voice_id)
    return voice

def update_voice_payment(voice_id, payment_id):
    voice = base.set_voice_payment(voice_id, payment_id)
    return voice

def update_voice_payed(voice_id):
    voice = base.set_voice_payed(voice_id)
    return voice

def check_voice_payment(voice_id):
    voice = base.fetch_ai_voice(voice_id)
    payment_status = {'payed': False, 'url': None}
    if len(voice) > 0:
        #we have a voice
        voice = voice[0]
        if voice['payed'] == True:
            payment_status['payed'] = True
            return payment_status
        else:
            #get payment id and check with stripe
            payment_id = voice['payment_id']
            if payment_id:
                payment_status = stripe.get_payment_status(payment_id)
                if payment_status['payed']:
                    update_voice_payed(voice_id)
                return payment_status
            

#golf section
def get_golf_courses():
    courses = base.fetch_courses()
    return courses

def get_golf_course(course_id):
    course = base.fetch_course(course_id)
    if len(course) > 0:
        return course[0]
    
def create_golf_course(data):
    course = base.create_course(data['name'], data['rating'], data['slope'])
    return course

def update_golf_course(course_id, data):
    course = base.update_course(course_id, data['name'], data['rating'], data['slope'])
    return course

def delete_golf_course(course_id):
    success = base.delete_course(course_id)
    return success

def get_golf_scores():
    scores = base.fetch_scores()
    return scores

def get_golf_score(score_id):
    score = base.fetch_score(score_id)
    if len(score) > 0:
        return score[0]

def create_golf_score(data):
    if isinstance(data['date'], datetime.datetime   ):
        data['date'] = data['date'].isoformat()
    score = base.create_score(data['date'], data['score'], data['course_id'], data['tee'], data['is_nine_hole'])
    return score

def update_golf_core(score_id, data):
    if isinstance(data['date'], datetime):
        data['date'] = data['date'].isoformat()
    score = base.update_score(score_id, data['date'], data['score'], data['course_id'], data['tee'])
    return score

def delete_golf_score(score_id):
    success = base.delete_score(score_id)
    return success

def get_golf_scores_by_course(course_id):
    scores = base.fetch_scores_by_course(course_id)
    return scores

def get_golf_scores_by_date(date):
    scores = base.fetch_scores_by_date(date)
    return scores

def get_last_20_golf_scores():
    scores = base.fetch_last_20_scores()
    return scores