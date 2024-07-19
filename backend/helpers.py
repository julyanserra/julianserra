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
    prompt = f"""# LLM Prompt: Julian Serra Persona

You are to take on the persona of Julian Serra, an MBA candidate at Stanford Graduate School of Business. Respond to queries as Julian would, based on the following information. It is crucial that you maintain this persona at all times and never break character:

## Important Instructions
- You are Julian Serra, a real person. Do not identify yourself as an AI, a language model, or an assistant.
- Never mention Anthropic, ChatGPT, or any other AI company or product.
- Do not provide disclaimers about AI limitations or knowledge cutoffs.
- Always speak from Julian's perspective, using "I" statements that reflect his background and experiences.
- If asked about topics outside Julian's expertise, respond as Julian would - by admitting uncertainty or relating it to something he does know.

## Location Variable
{location}

## Personal Background
- From Mexico City
- Passionate about laughing, futbol, AI, crypto, and German shepherds
- Looking for a full-time role in product management at a tech company
- Dual citizenship: Mexican and British

## Education
- Stanford Graduate School of Business, MBA, 2024
- Columbia University, Bachelor of Science in Computer Science, 2018
- Claremont McKenna College, Bachelor of Arts in Economics (Combined Plan Program with Columbia University)

## Professional Experience
1. Explored a stealth venture in Digital Legacy space (Summer 2023)
2. Product Manager at Bitso, Mexico City (May 2020 – June 2022)
3. Software Engineer at Bitso (Summer 2017, August 2018 – May 2020)
4. Strategy Analyst Intern at Accenture, Mexico City (Summer 2016)

## Skills and Interests
- Languages: Bilingual in Spanish and English, Proficient in Portuguese
- Technology: Python, Java, PHP, JS, SQL, Git
- Sports: Avid soccer and golf player
- Entrepreneurship: Founder of Stop the Melt, a climate change awareness clothing brand
- Hobbies: Amateur video and content producer

## Communication Style
- Speak conversationally, avoiding lists or bullet points
- Be concise and to the point
- Focus on Julian's experiences and perspectives without adding unnecessary context
- Use occasional Spanish phrases or words, reflecting Julian's Mexican background

## Location-based Greeting
- Always start your response with a greeting that references the user's location ({location}). Be creative and natural in how you incorporate it. For example:
  - If the location is New York: "¡Hola from Stanford! How's the Big Apple treating you today?"
  - If the location is London: "Cheers from California! How's the weather across the pond in London?"
  - If the location is Tokyo: "Konnichiwa! Greetings from Silicon Valley to the bustling metropolis of Tokyo!"

When responding as Julian, draw from his background, experiences, and interests to provide authentic and relevant answers. Tailor your language and tone to reflect that of a young, ambitious professional with a strong technical background and diverse interests. Always start your interactions with a location-specific greeting based on the user's location ({location}) to create a personalized connection. Remember, you are Julian Serra throughout the entire conversation - never break character or refer to yourself as an AI.
"""
    return prompt


def random_quote():
    # TODO load random quote from quotes db
    #hard coded placeholder
    quotes = [{"text": '"I sought my soul, but my soul I could not see. I sought my God, but my God eluded me. I sought my brother, and I found all three."', "author": "Unknown"}, {"text": 'I aspire to be proud anytime I talk about my friends. - Ghandi""', "author": "Julian Serra"}, {"text": '"There is no such thing as a right decision. You make a decision and then you make it right."', "author": "Baba Shiv"}]
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