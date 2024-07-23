import os
import boto3
from botocore.config import Config

class CloudflareR2Integration:
    def __init__(self):
        self.r2 = boto3.client('s3',
            endpoint_url = os.environ.get('CLOUDFLARE_ENDPOINT'),
            aws_access_key_id = os.environ.get('CLOUDFLARE_ACCESS_KEY_ID'),
            aws_secret_access_key = os.environ.get('CLOUDFLARE_SECRET_ACCESS_KEY'),
            config = Config(signature_version='s3v4'),
            region_name = 'auto'
        )
        self.bucket_name = os.environ.get('CLOUDFLARE_BUCKET_NAME')
        self.public_url = os.environ.get('CLOUDFLARE_PUBLIC_URL')

    def upload_file(self, file, filename):
        try:
            self.r2.upload_fileobj(
                file,
                self.bucket_name,
                filename,
                ExtraArgs={'ACL': 'public-read'}
            )
            return f"{self.public_url}/{filename}"
        except Exception as e:
            print(f"Error uploading to R2: {str(e)}")
            raise

    def handle_image_upload(self, request):
        if 'voice_photo' not in request.files:
            return None
        
        file = request.files['voice_photo']
        if file.filename == '':
            return None
        
        if file:
            filename = f"voice_photos/{file.filename}"
            try:
                r2_url = self.upload_file(file, filename)
                return r2_url
            except Exception as e:
                print(f"Error handling image upload: {str(e)}")
                raise

# Create a single instance to be imported and used in other files
cloudflare_r2 = CloudflareR2Integration()