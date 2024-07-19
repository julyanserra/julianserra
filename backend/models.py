# This file contains the models for the backend.
import backend.helpers as helpers
from flask import request, session
from backend.supabase_db import SupabaseClient
from dotenv import load_dotenv

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
    return pages[0]

def create_page(data):
    new_page = base.create_page(data['title'], data['icon'], data['content'])
    return new_page

def update_page(page_id, data):
    updated_page = base.update_page(page_id, data['title'], data['icon'], data['content'])
    return updated_page

def delete_page(page_id):
    success = base.delete_page(page_id)
    return success

# Page Content
def get_page_content(page_id):
    page_content = base.fetch_page_content(page_id)
    return page_content

def get_page_content_from_id(content_id):
    page_content = base.fetch_page_content_from_id(content_id)
    return page_content[0]

def get_page_from_title(title):
    page = base.fetch_page_from_title(title)[0]
    return page

def create_page_content(data):
    new_content = base.create_page_content(data['page_id'], data['content'])
    return new_content

def update_page_content(content_id, data):
    updated_content = base.update_page_content(content_id, data['page_id'], data['content'])
    return updated_content

def delete_page_content(content_id):
    success = base.delete_page_content(content_id)
    return success

# # Other functions you provided
# def get_content(page):
#     #get content for a specific page, returns a list of text objects
#     content = base.fetch_page_content(page)
#     return content

# Authentication
def login(email, password):
    success = base.login(email, password)
    return success

# Chat history
def get_chat_history(user_id):
    chat_history = base.fetch_chat_history(user_id)
    return chat_history