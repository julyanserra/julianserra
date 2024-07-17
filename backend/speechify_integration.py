import os
import requests
import base64

JO_VOICE="a954d930-3e08-470c-a303-3c1ff39e8ebd"
JUL_VOICE="0f60290d-4fe7-451b-b778-17daf1e4fe8d"        

class SpeechifyAPI:
    def __init__(self):
        self.api_key = os.environ.get("SPEECHIFY_API_KEY")
        self.api_url = "https://api.sws.speechify.com"  # Replace with actual Speechify API URL

       
        #get voices to define main voice
        # self.voices = self.get_voices()
        # print(self.voices)

    def convert_to_speech(self, text):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "voice_id": JUL_VOICE,    
            "audio_format": "mp3"
        }
        
        response = requests.post(f"{self.api_url}/v1/audio/speech", json=data, headers=headers)
        if response.status_code == 200:
            response_data = response.json()
            audio_data_base64 = response_data['audio_data']
            # Decode Base64 to bytes
            audio_data = base64.b64decode(audio_data_base64)
            return audio_data, "mp3"  # Return "mp3" as the format
        else:
            response.raise_for_status()

    #in case I wanted to upload audio to a server (NOT RIGHT)    
    def upload_audio(self, audio_data, format):
        # Upload audio to a public server or create a temporary file
        # This example uses a local file server for demonstration
        import tempfile
        import shutil

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{format}')
        with open(temp_file.name, 'wb') as file:
            file.write(audio_data)
        
        # Here you would need to handle the upload to a public server or a CDN
        # For example, use AWS S3, Google Cloud Storage, etc.
        # This is just an example assuming you have a local server to serve the file
        audio_url = f"/audio/{temp_file.name.split('/')[-1]}"
        return audio_url
    
    def get_voices(self):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        voices_url = "v1/audio/voices"
        response = requests.get(f"{self.api_url}/v1/voices", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    # Add more methods as needed for Speechify integration