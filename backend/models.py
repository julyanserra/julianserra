# This file contains the models for the backend.
import backend.helpers as helpers
from flask import request, session
from backend.supabase_db import SupabaseClient
from dotenv import load_dotenv
import json

from backend.supabase_db import SupabaseClient
load_dotenv()

base = SupabaseClient()

# Quotes
def get_quotes():
    quotes = base.fetch_quotes()
    return quotes

def create_quote(quote, author):
    new_quote = base.create_quote(quote, author)
    return new_quote

def update_quote(quote_id, quote, author):
    updated_quote = base.update_quote(quote_id, quote, author)
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

def transformContent(pages):
    for page in pages:
        page['content'] = json.loads(page['content'])
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
    return voice

def create_voice(data):
    voice = base.create_ai_voice(data['id'], data['name'], data['photo'], data['prompt'])
    return voice
