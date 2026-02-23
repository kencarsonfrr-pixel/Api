from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import random
import os

app = Flask(__name__)
CORS(app)  # This allows any frontend to connect

@app.route('/')
def home():
    return jsonify({
        'status': 'online',
        'message': 'EREN API is running',
        'endpoints': {
            '/check/username': 'GET - Check Instagram username',
            '/generate': 'POST - Generate usernames',
            '/send-telegram': 'POST - Send to Telegram'
        }
    })

@app.route('/check/<username>')
def check_instagram(username):
    """Real-time Instagram username check"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'X-Requested-With': 'XMLHttpRequest',
        'Origin': 'https://www.instagram.com',
    }
    
    try:
        # Try Instagram API
        api_url = 'https://www.instagram.com/api/v1/web/accounts/web_create_ajax/attempt/'
        response = requests.post(api_url, headers=headers, data=f'username={username}', timeout=10)
        
        if 'username_is_taken' in response.text.lower():
            return jsonify({'available': False, 'username': username})
        else:
            return jsonify({'available': True, 'username': username})
            
    except:
        # Fallback: check profile page
        try:
            profile_url = f'https://www.instagram.com/{username}/'
            r = requests.get(profile_url, timeout=10)
            
            if r.status_code == 404:
                return jsonify({'available': True, 'username': username})
            elif 'The link you followed may be broken' in r.text:
                return jsonify({'available': True, 'username': username})
            else:
                return jsonify({'available': False, 'username': username})
        except:
            return jsonify({'available': False, 'username': username, 'error': True})

@app.route('/generate', methods=['POST'])
def generate():
    """Generate cool usernames"""
    data = request.json
    style = data.get('style', 4)
    count = data.get('count', 10)
    
    rare = 'xzqjwvy'
    vowels = 'aeiou'
    cons = 'bcdfghjklmnpqrstvwxyz'
    nums = '0123456789'
    
    usernames = []
    patterns = [
        lambda: random.choice(rare) + random.choice(vowels) + random.choice(rare),
        lambda: random.choice(cons) + random.choice(vowels) + random.choice(cons) + random.choice(vowels),
        lambda: random.choice(rare) + random.choice(rare) + random.choice(vowels),
        lambda: random.choice(rare) + random.choice(nums) + random.choice(rare),
    ]
    
    for _ in range(count * 2):
        u = random.choice(patterns)()
        if style == 1:
            u = u[:3]
        elif style == 2:
            u = u[:4]
        elif style == 3:
            u = u[:5]
        else:
            u = u[:random.randint(3,5)]
        usernames.append(u.lower())
    
    usernames = list(dict.fromkeys(usernames))[:count]
    return jsonify({'usernames': usernames})

@app.route('/send-telegram', methods=['POST'])
def send_telegram():
    """Send message to Telegram"""
    data = request.json
    token = data.get('token')
    chat_id = data.get('chat_id')
    message = data.get('message')
    
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        params = {'chat_id': chat_id, 'text': message, 'parse_mode': 'HTML'}
        r = requests.get(url, params=params, timeout=10)
        return jsonify({'success': r.status_code == 200})
    except:
        return jsonify({'success': False})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
