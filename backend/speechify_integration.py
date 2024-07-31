import os
import requests
import base64
import json
from flask import jsonify
import backend.models as models


JO_VOICE="a954d930-3e08-470c-a303-3c1ff39e8ebd"
JUL_VOICE="0f60290d-4fe7-451b-b778-17daf1e4fe8d"        

class SpeechifyAPI:
    def __init__(self):
        self.api_key = os.environ.get("SPEECHIFY_API_KEY")
        self.api_url = "https://api.sws.speechify.com"  # Replace with actual Speechify API URL

       
        #get voices to define main voice
        # self.voices = self.get_voices()
        # print(self.voices)

    def convert_to_speech(self, text, id=JUL_VOICE):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "input": text,
            "voice_id": id,    
            "audio_format": "mp3",
            "model": "simba-base"
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

    def delete_voice(self, id):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        delete_url = self.api_url+ "/v1/voices/"+id
        print(delete_url)
        response = requests.delete(delete_url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()

    def get_voices(self): 
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        response = requests.get(f"{self.api_url}/v1/voices", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()
    
    #delete specific voices or unused voices
    def delete_voices(self):
        voices = self.get_voices()
        db_voices = models.get_voices()
        for voice in voices:
            #check if voice['id'] is containted in db_voices object
            if (voice['type'] == 'personal' and not any(db_voice['api_voice_id'] == voice['id'] for db_voice in db_voices) and voice['id'] != JUL_VOICE):
                print(f"Deleting voice {voice['id']}")
                self.delete_voice(voice['id'])


    def create_voice(self, name, audio_file, test=False):

        if test:
            return {"id": "123455"}
       
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
        response = requests.get(f"{self.api_url}/v1/voices", headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            response.raise_for_status()


    def handle_voice_upload(self, request, voice_name):
        # Handle audio file
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            raise jsonify({'error': 'No selected audio file'})
                
        # call speechify
        try:
            speechify_response = self.create_voice(voice_name, audio_file)
        except requests.exceptions.RequestException as e:
            print(f"Speechify API error: {str(e)}")
            error_details = {
                'error': 'Speechify API error',
                'details': str(e),
                'status_code': e.response.status_code if hasattr(e, 'response') else None,
                'response_content': e.response.text if hasattr(e, 'response') else None
            }
            #throw exception to be caught outside of function
            raise jsonify(error_details)

        api_voice_id = speechify_response.get('id')
        if not api_voice_id:
            print("No voice ID returned from Speechify")
            raise jsonify({'error': 'No voice ID returned from Speechify'})
        
        return api_voice_id

    # Add more methods as needed for Speechify integration