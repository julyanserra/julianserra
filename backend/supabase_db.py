import os
from supabase import create_client, Client

class SupabaseClient:
    def __init__(self):
        print(os.environ)
        # Get the Supabase URL and key from environment variables in .env.example
         
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    #get chat history from chat table for specific user
    def fetch_chat_history(self, user_id):
        response = self.supabase.table('chat').select("*").eq('user_id', user_id).execute()
        return response.data
    
    #get quotes from quote table
    def fetch_quotes(self):
        response = self.supabase.table('quotes').select("*").execute()
        return response.data
    
    def fetch_curriculum(self):
        # Implement the logic to fetch curriculum data from Supabase
        response = self.supabase.table('curriculum').select("*").execute()
        return response.data

    # Add more methods as needed for database operations