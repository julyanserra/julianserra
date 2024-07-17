import os
from supabase import create_client, Client

class SupabaseClient:
    def __init__(self):
        print(os.environ)
        # Get the Supabase URL and key from environment variables in .env.example
         
        url: str = os.environ.get("SUPABASE_URL")
        key: str = os.environ.get("SUPABASE_KEY")
        self.supabase: Client = create_client(url, key)

    def fetch_curriculum(self):
        # Implement the logic to fetch curriculum data from Supabase
        response = self.supabase.table('curriculum').select("*").execute()
        return response.data

    # Add more methods as needed for database operations