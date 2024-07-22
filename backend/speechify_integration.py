import os
import requests
import base64
import json


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

    def create_voice(self, name, audio_file):
        print("Creating voice")
        
        try:
            # Reset the file pointer to the beginning of the file
            audio_file.seek(0)
            
            # Prepare the multipart form data
            files = {
                'sample': ('recording.mp3', audio_file, 'audio/mpeg')
            }
            
            data = {
                'name': name,
                'consent': json.dumps({
                    'fullName': "Julian Serra",
                    'email': "julian.serra.wright@gmail.com"
                })
            }
            
            headers = {
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = requests.post(
                f"{self.api_url}/v1/voices",
                files=files,
                data=data,
                headers=headers
            )
            
            print(f"Request URL: {response.request.url}")
            print(f"Request headers: {response.request.headers}")
            print(f"Request body size: {len(response.request.body)} bytes")
            
            if response.status_code != 200:
                print(f"Error response: Status code {response.status_code}")
                print(f"Response content: {response.text}")
                response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Error in create_voice: {str(e)}")
            if hasattr(e, 'response'):
                print(f"Response status code: {e.response.status_code}")
                print(f"Response content: {e.response.text}")
            raise
        
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