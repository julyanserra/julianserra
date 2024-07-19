import os
from supabase import create_client, Client
import backend.helpers as helper  # Make sure this helper module exists and has the verify_password function

class SupabaseClient:
    def __init__(self):
        print(os.environ)
        # Get the Supabase URL and key from environment variables in .env.example
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    # PAGES CRUD
    def fetch_pages(self):
        response = self.supabase.table('page').select("*").execute()
        return response.data
    
    def create_page(self, title, icon, text):
        response = self.supabase.table('page').insert({"title": title, "icon": icon, "content": text}).execute()
        return response

    def update_page(self, page_id, title, icon, text):
        response = self.supabase.table('page').update({"title": title, "icon": icon, "content": text}).eq('page_id', page_id).execute()
        return response

    def delete_page(self, page_id):
        response = self.supabase.table('page').delete().eq('page_id', page_id).execute()
        return response.status_code == 200
    
    def fetch_page(self, page_id):
        response = self.supabase.table('page').select("*").eq('page_id', page_id).execute()
        return response.data
    
    def fetch_page_from_title(self, title):
        response = self.supabase.table('page').select("*").eq('title', title).execute()
        return response.data

    # PAGE CONTENT CRUD
    def fetch_page_content(self, page_id):
        response = self.supabase.table('page_content').select("*").eq('page_id', page_id).execute()
        return response.data
    
    def fetch_page_content_from_id(self, content_id):
        response = self.supabase.table('page_content').select("*").eq('content_id', content_id).execute()
        return response.data

    def create_page_content(self, page_id, content):
        response = self.supabase.table('page_content').insert({"page_id": page_id, "content": content}).execute()
        return response

    def update_page_content(self, content_id, page_id, content):
        response = self.supabase.table('page_content').update({"page_id": page_id, "content": content}).eq('content_id', content_id).execute()
        return response

    def delete_page_content(self, content_id):
        response = self.supabase.table('page_content').delete().eq('content_id', content_id).execute()
        return response.status_code == 200
    
        # QUOTES CRUD
    def fetch_quotes(self):
        response = self.supabase.table('quotes').select("*").execute()
        return response.data

    def create_quote(self, quote, author):
        response = self.supabase.table('quotes').insert({"quote": quote, "author": author}).execute()
        return response

    def update_quote(self, quote_id, quote, author):
        response = self.supabase.table('quotes').update({"quote": quote, "author": author}).eq('quote_id', quote_id).execute()
        return response

    def delete_quote(self, quote_id):
        response = self.supabase.table('quotes').delete().eq('quote_id', quote_id).execute()
        return response.status_code == 200

    # User authentication
    def login(self, email, password):
        result = self.supabase.table('users').select("*").eq('email', email).execute()
        if result.data:
            user = result.data[0]
            if helper.verify_password(user["password"], password):
                self.userId = user["user_id"]
                self.email = user["email"]
                return True
        return False

    def fetch_content_by_title(self, title):
        response = self.supabase.table('page_content').select("*").eq('Title', title).execute()
        return response.data