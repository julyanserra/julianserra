import hashlib
import user_agents
import backend.helpers as helpers
from flask import request, session
import requests
import random
import hashlib, binascii, os
from datetime import datetime

def get_visitor_info():
    # Create a unique fingerprint based on available information
    fingerprint_data = [
        request.remote_addr,
        request.headers.get('User-Agent', ''),
        request.headers.get('Accept-Language', ''),
        request.headers.get('Accept-Encoding', ''),
    ]
    fingerprint = hashlib.md5(''.join(fingerprint_data).encode()).hexdigest()
    
    user_agent = request.headers.get('User-Agent')
    ua = user_agents.parse(user_agent)
    
    visitor_info = {
        'fingerprint': fingerprint,
        'ip_address': request.remote_addr,
        'browser': ua.browser.family,
        'browser_version': ua.browser.version_string,
        'os': ua.os.family,
        'os_version': ua.os.version_string,
        'device': ua.device.family,
        'is_mobile': ua.is_mobile,
        'is_tablet': ua.is_tablet,
        'is_pc': ua.is_pc,
        'referrer': request.referrer,
        'language': request.headers.get('Accept-Language'),
    }

    return visitor_info

def handle_url_for_voice(public_url, voices):
    for voice in voices:
        current_url = voice['voice_photo']
        #separate url before /voice_photos
        if(current_url and current_url.find('cloudflare') > -1):
            path = current_url.split('/julianserra') 
            #get the public url
            # check if path has 2 parts
            if len(path) > 1:
                path = path[1]
                voice['voice_photo'] = public_url + path
    return voices

def get_location(visitor_info):
    #get location from ip address
    
    ip_address = visitor_info['ip_address']
    # check if session has location data
    if "location_data" in session:
        return session["location_data"]
    else:
        #use ipstack api to get location data
        response = requests.get(f'https://ipapi.co/{ip_address}/json/').json()
        location_data = {
            "ip": ip_address,
            "city": response.get("city"),
            "region": response.get("region"),
            "country": response.get("country_name")
        }
        session["location_data"] = location_data
    return location_data

def get_most_specific_location(location_data):
    #get the most specific location from the location data
    specific = location_data['city'] or location_data['region'] or location_data['country'] or 'Unknown'
    return specific

# TODO GET SOME GOOD PROMPTS
def processContext(visitor, prompt=None):
    location = helpers.get_most_specific_location(get_location(visitor))
    if(prompt):
        initial_prompt = prompt
        # add be very brief to prompt
        initial_prompt = initial_prompt + " Respond as briefly as you can"
    else: 
        initial_prompt = helpers.get_julian_serra_prompt(location)
    return initial_prompt

def get_julian_serra_prompt(location):
    prompt = f"""You are Julian Serra, Stanford MBA grad from Mexico City. Respond very briefly as Julian in 1-3 short sentences max. Key points:

Stanford MBA, Columbia CS grad
Ex-Product Manager at Bitso
Seeking tech PM role
Loves soccer, AI, crypto
Bilingual, tech-savvy
Climate change activist

Start with a quick greeting mentioning {location}. Use Julian's background to answer. If unsure, say so. Occasionally use Spanish. Be concise and casual.
"""
    return prompt


def random_quote(quotes):
    return quotes[random.randint(0, len(quotes) - 1)]

# Password management
def hash_password(password):
    """Hash a password for storing."""
    salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
    pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'),
                                salt, 100000)
    pwdhash = binascii.hexlify(pwdhash)
    return (salt + pwdhash).decode('ascii')

def verify_password(stored_password, provided_password):
    """Verify a stored password against one provided by user"""
    salt = stored_password[:64]
    stored_password = stored_password[64:]
    pwdhash = hashlib.pbkdf2_hmac('sha512',
                                  provided_password.encode('utf-8'),
                                  salt.encode('ascii'),
                                  100000)
    pwdhash = binascii.hexlify(pwdhash).decode('ascii')
    return pwdhash == stored_password

def get_default_links():
    links = {}
    links["instagram"] = "https://www.instagram.com/julyanserra/"
    links["linkedin"] = "https://www.linkedin.com/in/julianserra/"
    links["github"] = "https://github.com/julyanserra"
    links["email"] = "mailto:julian.serra.wright@gmail.com"
    links["stripe"] = "https://buy.stripe.com/28o162atU2HJ7DOfYY"
    links["song"] = "https://open.spotify.com/track/71glNHT4FultOqlau4zrFf?si=3ed90ad714c54a67"
    return links    

def get_current_year():
    # get current year
    return datetime.now().year

def get_timeline():
    timeline = [
    {
        "logo": "https://www.shutterstock.com/image-vector/mexico-panorama-city-flat-line-260nw-1190202997.jpg",
        "description": "Born in Mexico City",
        "link": "https://en.wikipedia.org/wiki/Mexico_City",
        'date': '1994',
        # 'title': 'Born'
    },{
        "logo": "data:image/png;base64,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",
        "description": "BA in Economics",
        "link": "https://cmc.edu",
        'date': '2014 - 2018',

    },
    {
        "logo": "data:image/png;base64,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",
        "description": "BS in Computer Science",
        "link": "https://columbia.edu",
        'date': '2014 - 2018',

    },
    {
        "logo": "https://i.pinimg.com/originals/35/2b/03/352b03550b831ae511712e566e35afad.png",
        "description": "Software Engineer and Product Manager",
        "link": "https://bitso.com",
        'date': '2017 - 2022'

    },
    {
        "logo": "data:image/png;base64,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",
        "description": "MBA",
        "link": "https://www.gsb.stanford.edu/",
        'date': '2022 - 2024',

    },
    # {
    #     "logo": "https://media.licdn.com/dms/image/C4E0BAQFaPIDW2TjcCQ/company-logo_200_200/0/1632326992808/to_be_determined_hq_logo?e=2147483647&v=beta&t=IR6i6pGZwKR5PV_5HnfkaU9_Ql67TsEWyWvGTbi-lQg",
    #     "description": "Where to next?"
    # }
    # Add more items as needed
]
    
    return timeline
