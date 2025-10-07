from flask import Flask, request, jsonify
import os
import time
import json
import urllib.parse
import requests
from pathlib import Path
import tempfile

app = Flask(__name__)

# ==== CONFIG ====
RATE_LIMIT = 5           # Max requests
RATE_WINDOW = 60         # In seconds
TMP_DIR = Path(tempfile.gettempdir()) / 'rate_limit'

# ==== SETUP ====
TMP_DIR.mkdir(exist_ok=True, parents=True)

def check_rate_limit(ip):
    """Check if IP has exceeded rate limit"""
    rate_file = TMP_DIR / f"{ip.replace(':', '_')}.json"
    now = time.time()
    
    access_log = []
    
    if rate_file.exists():
        try:
            with open(rate_file, 'r') as f:
                access_log = json.load(f)
        except:
            access_log = []
    
    # Remove old timestamps
    access_log = [ts for ts in access_log if (ts + RATE_WINDOW) >= now]
    
    if len(access_log) >= RATE_LIMIT:
        return False, access_log
    
    # Log current request
    access_log.append(now)
    
    try:
        with open(rate_file, 'w') as f:
            json.dump(access_log, f)
    except:
        pass
    
    return True, access_log

@app.route('/api/fetch')
def fetch_url():
    # ==== RATE LIMIT CHECK ====
    ip = request.remote_addr
    allowed, access_log = check_rate_limit(ip)
    
    if not allowed:
        return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
    
    # ==== VALIDATION ====
    if 'url' not in request.args or not request.args['url']:
        return jsonify({"error": "Missing 'url' parameter"}), 400
    
    # ==== BUILD API CALL ====
    input_url = request.args['url']
    encoded_url = urllib.parse.quote(input_url)
    
    api_url = f"https://utdqxiuahh.execute-api.ap-south-1.amazonaws.com/pro/fetch?url={encoded_url}&user_id=h2"
    
    headers = {
        "x-api-key": "fAtAyM17qm9pYmsaPlkAT8tRrDoHICBb2NnxcBPM",
        "User-Agent": "okhttp/4.12.0",
        "Accept-Encoding": "gzip"
    }
    
    try:
        response = requests.get(api_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # ==== RETURN RESULT ====
        return jsonify(response.json())
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found. Use /api/fetch?url=YOUR_URL"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

# For Vercel serverless deployment
def handler(request):
    with app.app_context():
        return app.full_dispatch_request()
