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
        return response
    
    def fetch_page(self, page_id):
        response = self.supabase.table('page').select("*").eq('page_id', page_id).execute()
        return response.data
    
    def fetch_page_from_title(self, title):
        response = self.supabase.table('page').select("*").eq('title', title).execute()
        return response.data
    
        # QUOTES CRUD
    def fetch_quotes(self):
        response = self.supabase.table('quotes').select("*").execute()
        return response.data

    def fetch_quote(self, quote_id):
        response = self.supabase.table('quotes').select("*").eq('quote_id', quote_id).execute()
        return response.data

    def create_quote(self, quote, author):
        response = self.supabase.table('quotes').insert({"quote": quote, "author": author}).execute()
        return response

    def update_quote(self, quote_id, quote, author):
        response = self.supabase.table('quotes').update({"quote": quote, "author": author}).eq('quote_id', quote_id).execute()
        return response

    def delete_quote(self, quote_id):
        response = self.supabase.table('quotes').delete().eq('quote_id', quote_id).execute()
        return response

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
    
    def fetch_profile_links(self):
        # response = self.supabase.table('profile_links').select("*").execute()
        # return response.data
        return []
        

#     CRUD for table for ai voices from this table: CREATE TABLE ai_voices (
#   voice_id    BIGSERIAL PRIMARY KEY,
#   api_voice_id VARCHAR(200),
#   voice_name  VARCHAR(200),
#   voice_photo VARCHAR(200),
#   voice_prompt VARCHAR(200),
#   payment_id  VARCHAR(200),
#   payed       BOOLEAN DEFAULT FALSE,
#   created_at  TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
# );

    def fetch_ai_voices(self):
        response = self.supabase.table('ai_voices').select("*").execute()
        return response.data
    
    def create_ai_voice(self, api_voice_id, voice_name, voice_photo, voice_prompt):
        response = self.supabase.table('ai_voices').insert({"api_voice_id": api_voice_id, "voice_name": voice_name, "voice_photo": voice_photo, "voice_prompt": voice_prompt}).execute()
        return response
    
    def set_voice_payment(self, voice_id, payment_id):
        response = self.supabase.table('ai_voices').update({"payment_id": payment_id}).eq('voice_id', voice_id).execute()
        return response
    
    def set_voice_payed(self, voice_id):
        response = self.supabase.table('ai_voices').update({"payed": True}).eq('voice_id', voice_id).execute()
        return response
    
    def update_ai_voice(self, voice_id, api_voice_id, voice_name, voice_photo, voice_prompt):
        response = self.supabase.table('ai_voices').update({"api_voice_id": api_voice_id, "voice_name": voice_name, "voice_photo": voice_photo, "voice_prompt": voice_prompt}).eq('voice_id', voice_id).execute()
        return response
    
    def delete_ai_voice(self, voice_id):
        response = self.supabase.table('ai_voices').delete().eq('voice_id', voice_id).execute()
        return response
    
    def fetch_ai_voice(self, voice_id):
        response = self.supabase.table('ai_voices').select("*").eq('voice_id', voice_id).execute()
        return response.data
    
    def fetch_ai_voice_by_api_id(self, api_voice_id):
        response = self.supabase.table('ai_voices').select("*").eq('api_voice_id', api_voice_id).execute()
        return response.data
    
    def fetch_ai_voice_by_name(self, voice_name):
        response = self.supabase.table('ai_voices').select("*").eq('voice_name', voice_name).execute()
        return response.data
    
    