from flask import Flask, jsonify, request
import aiohttp
import asyncio
from typing import Dict, Optional

# Initialize Flask app
app = Flask(__name__)

def add_cors_headers(response):
    """Add CORS headers manually"""
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    response.headers['Access-Control-Max-Age'] = '86400'
    return response

@app.after_request
def after_request(response):
    """Apply CORS headers to all responses"""
    return add_cors_headers(response)

@app.before_request
def handle_preflight():
    """Handle preflight OPTIONS requests"""
    if request.method == "OPTIONS":
        response = jsonify({'status': 'ok'})
        response = add_cors_headers(response)
        return response

async def check_ban_garena(uid: str, lang: str = "en") -> Optional[Dict]:
    """
    Check ban status using official Garena Free Fire API
    
    Args:
        uid (str): Free Fire user ID
        lang (str): Language code (en, id, th, vi, etc.)
        
    Returns:
        Dict with ban information or None if failed
    """
    api_url = "https://ff.garena.com/api/antihack/check_banned"
    
    # Headers to mimic browser request
    headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://ff.garena.com/en/support/',
        'Sec-Ch-Ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-origin',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
        'X-Requested-With': 'B6FksShzIgjfrYImLpTsadjS86sddhFH'
    }
    
    params = {
        'lang': lang,
        'uid': uid
    }
    
    # Set timeout for the request
    timeout = aiohttp.ClientTimeout(total=15)
    
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(api_url, params=params, headers=headers) as response:
                # Check response status
                if response.status != 200:
                    print(f"API returned status {response.status} for UID {uid}")
                    return {"error": True, "message": f"API returned status {response.status}"}
                
                # Parse JSON response
                response_data = await response.json()
                return response_data
                
    except aiohttp.ClientError as e:
        print(f"API request failed for UID {uid}: {e}")
        return None
    except asyncio.TimeoutError:
        print(f"API request timed out for UID {uid}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred for UID {uid}: {e}")
        return None

@app.route('/')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "success",
        "message": "Free Fire Ban Check API is running",
        "version": "2.0.0",
        "api_source": "Official Garena API",
        "cors": "Manual implementation"
    })

@app.route('/api/check-ban/<uid>')
def check_ban_status(uid):
    """
    Check ban status for a Free Fire user ID using official Garena API
    
    Args:
        uid (str): Free Fire user ID
        
    Returns:
        JSON response with ban status information
    """
    try:
        # Validate UID
        if not uid or not uid.isdigit():
            return jsonify({
                "status": "error",
                "message": "Invalid UID. Please provide a valid numeric user ID.",
                "data": None
            }), 400
        
        # Get language from query parameter (default: en)
        lang = request.args.get('lang', 'en')
        
        # Check ban status using async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ban_data = loop.run_until_complete(check_ban_garena(uid, lang))
        loop.close()
        
        if ban_data is None:
            return jsonify({
                "status": "error",
                "message": "Could not retrieve ban information. Please try again later.",
                "data": None
            }), 503
        
        # Handle API error responses
        if ban_data.get("error"):
            return jsonify({
                "status": "error",
                "message": ban_data.get("message", "API returned an error"),
                "data": None
            }), 400
        
        # Format response based on Garena API structure
        response_data = {
            "uid": uid,
            "language": lang,
            "garena_response": ban_data,
            "api_source": "Official Garena API"
        }
        
        return jsonify({
            "status": "success",
            "message": "Ban check completed successfully",
            "data": response_data
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An unexpected error occurred: {str(e)}",
            "data": None
        }), 500

@app.route('/api/check-ban', methods=['POST'])
def check_ban_post():
    """
    Check ban status via POST request
    
    Expected JSON body:
    {
        "uid": "123456789",
        "lang": "en" (optional, defaults to "en")
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'uid' not in data:
            return jsonify({
                "status": "error",
                "message": "Missing 'uid' in request body",
                "data": None
            }), 400
        
        uid = str(data['uid'])
        lang = data.get('lang', 'en')
        
        # Validate UID
        if not uid.isdigit():
            return jsonify({
                "status": "error",
                "message": "Invalid UID. Please provide a valid numeric user ID.",
                "data": None
            }), 400
        
        # Check ban status
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        ban_data = loop.run_until_complete(check_ban_garena(uid, lang))
        loop.close()
        
        if ban_data is None:
            return jsonify({
                "status": "error",
                "message": "Could not retrieve ban information. Please try again later.",
                "data": None
            }), 503
        
        # Handle API error responses
        if ban_data.get("error"):
            return jsonify({
                "status": "error",
                "message": ban_data.get("message", "API returned an error"),
                "data": None
            }), 400
        
        # Format response
        response_data = {
            "uid": uid,
            "language": lang,
            "garena_response": ban_data,
            "api_source": "Official Garena API"
        }
        
        return jsonify({
            "status": "success",
            "message": "Ban check completed successfully",
            "data": response_data
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Invalid JSON format: {str(e)}",
            "data": None
        }), 400

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        "status": "error",
        "message": "Endpoint not found",
        "available_endpoints": [
            "GET /",
            "GET /api/check-ban/<uid>?lang=<lang>",
            "POST /api/check-ban"
        ]
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        "status": "error",
        "message": "Internal server error",
        "data": None
    }), 500

if __name__ == '__main__':
    # Simple configuration without environment variables
    PORT = 5000
    DEBUG = False
    
    print(f"🚀 Starting Free Fire Ban Check API on port {PORT}")
    print(f"📡 Using Official Garena API: https://ff.garena.com/api/antihack/check_banned")
    print(f"🌐 API will be available at: http://localhost:{PORT}")
    print(f"✅ CORS: Manual implementation (Vercel compatible)")
    
    app.run(
        host='0.0.0.0',
        port=PORT,
        debug=DEBUG
    )