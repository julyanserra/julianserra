import hashlib
import user_agents
from flask import request

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