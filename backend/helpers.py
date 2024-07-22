import hashlib
import user_agents
import backend.helpers as helpers
from flask import request, session
import requests
import random
import hashlib, binascii, os

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
def processContext(visitor):
    location = helpers.get_most_specific_location(get_location(visitor))
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


def random_quote():
    # TODO load random quote from quotes db
    #hard coded placeholder
    quotes = [{"text": '"I sought my soul, but my soul I could not see. I sought my God, but my God eluded me. I sought my brother, and I found all three."', "author": "Unknown"}, {"text": '"I aspire to be proud anytime I talk about my friends. - Ghandi"', "author": "Julian Serra"}, {"text": '"There is no such thing as a right decision. You make a decision and then you make it right."', "author": "Baba Shiv"}]
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
    return links    