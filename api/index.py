from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import time
import re

app = Flask(__name__)
CORS(app)

# Real Instagram checking function
def check_instagram_username(username):
    """
    ACTUALLY checks if Instagram username is available
    Returns: True if available, False if taken
    """
    
    # Method 1: Check Instagram profile page
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Try to access the profile page
        url = f"https://www.instagram.com/{username}/"
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        # Check response
        if response.status_code == 404:
            # Page not found = username available
            return True
        elif response.status_code == 200:
            # Page exists - check if it's a valid profile
            if 'The link you followed may be broken' in response.text:
                return True
            elif 'Sorry, this page' in response.text:
                return True
            elif 'Page Not Found' in response.text:
                return True
            else:
                # Profile exists = username taken
                return False
        else:
            # Try alternative method
            return check_instagram_api(username)
            
    except Exception as e:
        # If first method fails, try API method
        return check_instagram_api(username)

def check_instagram_api(username):
    """Alternative method using Instagram's API"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'XMLHttpRequest',
            'Origin': 'https://www.instagram.com',
            'Connection': 'keep-alive',
        }
        
        # Try signup API
        url = "https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/"
        data = f'username={username}'
        
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        if response.status_code == 200:
            response_text = response.text.lower()
            
            if 'username_is_taken' in response_text:
                return False
            elif 'available' in response_text:
                return True
            elif 'taken' in response_text:
                return False
            else:
                # If unclear, check via JSON response
                try:
                    data = response.json()
                    if 'errors' in data and 'username' in data['errors']:
                        return False
                    return True
                except:
                    # Default to checking profile
                    return check_profile_fallback(username)
        else:
            return check_profile_fallback(username)
            
    except Exception as e:
        return check_profile_fallback(username)

def check_profile_fallback(username):
    """Final fallback - check if profile exists"""
    try:
        url = f"https://www.instagram.com/{username}/"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            # Check if it's an actual profile or error page
            if 'Profile' in response.text and 'posts' in response.text:
                return False  # Real profile exists = taken
            else:
                return True  # Error page = available
        elif response.status_code == 404:
            return True  # Not found = available
        else:
            # If we can't determine, assume taken to be safe
            return False
    except:
        # If all methods fail, return False (taken) to avoid false positives
        return False

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'EREN REAL Instagram Checker',
        'endpoints': {
            '/check/username': 'GET - Real-time Instagram check',
            '/generate': 'POST - Generate aesthetic usernames',
            '/send-telegram': 'POST - Send to Telegram',
            '/bulk-check': 'POST - Check multiple usernames'
        },
        'note': 'All checks are 100% real-time Instagram verification'
    })

@app.route('/check/<username>')
def check_username(username):
    """Real-time Instagram username check"""
    
    # Validate username
    if not username or len(username) < 3:
        return jsonify({
            'available': False,
            'username': username,
            'error': 'Invalid username'
        })
    
    # Check if username contains only allowed characters
    if not re.match("^[a-zA-Z0-9_]+$", username):
        return jsonify({
            'available': False,
            'username': username,
            'error': 'Username contains invalid characters'
        })
    
    # Perform real check
    is_available = check_instagram_username(username)
    
    return jsonify({
        'available': is_available,
        'username': username,
        'timestamp': time.time()
    })

@app.route('/bulk-check', methods=['POST'])
def bulk_check():
    """Check multiple usernames at once"""
    data = request.json
    usernames = data.get('usernames', [])
    
    if not usernames or len(usernames) > 20:
        return jsonify({
            'error': 'Maximum 20 usernames per request'
        })
    
    results = []
    for username in usernames:
        is_available = check_instagram_username(username)
        results.append({
            'username': username,
            'available': is_available
        })
        time.sleep(0.5)  # Small delay to avoid rate limiting
    
    return jsonify({
        'results': results,
        'count': len(results)
    })

@app.route('/generate', methods=['POST'])
def generate_usernames():
    """Generate aesthetic usernames that are LIKELY available"""
    data = request.json
    style = data.get('style', 4)  # 1:3,2:4,3:5,4:mix
    count = data.get('count', 10)
    
    if count > 50:
        count = 50
    
    # Character sets for generation
    rare_letters = 'xzqjwvy'
    common_letters = 'abcdefghiklmnoprstu'
    vowels = 'aeiou'
    numbers = '0123456789'
    
    def generate_one(style_num):
        if style_num == 1:  # 3 letters
            patterns = [
                lambda: random.choice(rare_letters) + random.choice(vowels) + random.choice(rare_letters),
                lambda: random.choice(rare_letters) + random.choice(rare_letters) + random.choice(vowels),
                lambda: random.choice(common_letters) + random.choice(rare_letters) + random.choice(numbers),
                lambda: random.choice(rare_letters) + random.choice(numbers) + random.choice(rare_letters),
            ]
            username = random.choice(patterns)()
            return username[:3].lower()
            
        elif style_num == 2:  # 4 letters
            patterns = [
                lambda: random.choice(rare_letters) + random.choice(vowels) + random.choice(rare_letters) + random.choice(vowels),
                lambda: random.choice(common_letters) + random.choice(rare_letters) + random.choice(vowels) + random.choice(rare_letters),
                lambda: random.choice(rare_letters) + random.choice(rare_letters) + random.choice(vowels) + random.choice(numbers),
            ]
            username = random.choice(patterns)()
            return username[:4].lower()
            
        elif style_num == 3:  # 5 letters
            patterns = [
                lambda: random.choice(rare_letters) + random.choice(vowels) + random.choice(rare_letters) + random.choice(vowels) + random.choice(rare_letters),
                lambda: random.choice(common_letters) + random.choice(rare_letters) + random.choice(vowels) + random.choice(rare_letters) + random.choice(numbers),
            ]
            username = random.choice(patterns)()
            return username[:5].lower()
            
        else:  # Mixed
            length = random.choice([3,4,5])
            return generate_one(length)
    
    # Generate usernames
    usernames = []
    for _ in range(count):
        if style == 4:
            # Mix of all lengths
            actual_style = random.choice([1,2,3])
        else:
            actual_style = style
            
        username = generate_one(actual_style)
        usernames.append(username)
    
    # Remove duplicates
    usernames = list(dict.fromkeys(usernames))
    
    # If we removed too many, generate more
    while len(usernames) < count:
        if style == 4:
            actual_style = random.choice([1,2,3])
        else:
            actual_style = style
        username = generate_one(actual_style)
        if username not in usernames:
            usernames.append(username)
    
    return jsonify({
        'usernames': usernames[:count],
        'style': style,
        'count': len(usernames[:count])
    })

@app.route('/send-telegram', methods=['POST'])
def send_telegram():
    """Send message to Telegram"""
    data = request.json
    token = data.get('token')
    chat_id = data.get('chat_id')
    message = data.get('message')
    
    if not token or not chat_id or not message:
        return jsonify({'success': False, 'error': 'Missing parameters'})
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        params = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Telegram API error'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# For local testing
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
