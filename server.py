"""
Wild West Shootout - Stats API Backend
Secure Flask server with authentication, rate limiting, and CORS protection
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import json
import os
import bcrypt
import hashlib
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)

# CORS: Only allow known frontends
CORS(app, origins=[
    'https://wild-west-shootout.vercel.app',
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5500',
    'http://127.0.0.1:5500'
])

# Rate limiting
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# Session management (in-memory)
active_sessions = {}
SESSION_DURATION = timedelta(hours=24)
DATA_FILE = 'data.json'

# ============================================================================
# HELPERS
# ============================================================================

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'users': {}, 'created': datetime.now().isoformat()}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    """Secure bcrypt hashing"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, stored_hash):
    """Verify password - supports SHA256 migration"""
    # Legacy SHA256 hash (64 hex chars)
    if len(stored_hash) == 64 and all(c in '0123456789abcdef' for c in stored_hash):
        return hashlib.sha256(password.encode()).hexdigest() == stored_hash
    # bcrypt
    try:
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    except:
        return False

def is_legacy_hash(stored_hash):
    """Check if using old SHA256"""
    return len(stored_hash) == 64 and all(c in '0123456789abcdef' for c in stored_hash)

def create_session(username):
    """Generate session token"""
    token = secrets.token_urlsafe(32)
    active_sessions[token] = {
        'username': username,
        'expires': datetime.now() + SESSION_DURATION
    }
    return token

def get_auth_user():
    """Extract username from Bearer token"""
    auth = request.headers.get('Authorization', '')
    if not auth.startswith('Bearer '):
        return None
    token = auth[7:]
    session = active_sessions.get(token)
    if not session or datetime.now() > session['expires']:
        if token in active_sessions:
            del active_sessions[token]
        return None
    return session['username']

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.route('/api/register', methods=['POST'])
@limiter.limit("3 per minute")
def register():
    try:
        body = request.get_json()
        username = body.get('username', '').strip()
        password = body.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        if len(username) < 2 or len(username) > 15:
            return jsonify({'error': 'Username must be 2-15 characters'}), 400

        data = load_data()
        if username.lower() in [u.lower() for u in data['users'].keys()]:
            return jsonify({'error': 'Username already exists'}), 400

        data['users'][username] = {
            'password': hash_password(password),
            'created': datetime.now().isoformat(),
            'ai_stats': {},
            'pvp_wins': 0, 'pvp_losses': 0, 'pvp_draws': 0,
            'pvp_games': 0, 'pvp_streak': 0, 'pvp_best_streak': 0,
            'total_wagered': 0, 'achievements': [],
            'total_wins': 0, 'total_draws': 0
        }
        save_data(data)

        token = create_session(username)
        return jsonify({'success': True, 'token': token, 'username': username})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
@limiter.limit("5 per minute")
def login():
    try:
        body = request.get_json()
        username = body.get('username', '').strip()
        password = body.get('password', '')

        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400

        data = load_data()

        # Find user (case-insensitive)
        actual_username = None
        for u in data['users'].keys():
            if u.lower() == username.lower():
                actual_username = u
                break

        if not actual_username:
            return jsonify({'error': 'User not found'}), 404

        user = data['users'][actual_username]

        if not verify_password(password, user['password']):
            return jsonify({'error': 'Invalid password'}), 401

        # Migrate legacy SHA256 to bcrypt
        if is_legacy_hash(user['password']):
            user['password'] = hash_password(password)
            user['password_migrated'] = datetime.now().isoformat()
            save_data(data)

        token = create_session(actual_username)
        return jsonify({'success': True, 'token': token, 'username': actual_username})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/logout', methods=['POST'])
def logout():
    auth = request.headers.get('Authorization', '')
    if auth.startswith('Bearer '):
        token = auth[7:]
        active_sessions.pop(token, None)
    return jsonify({'success': True})

# ============================================================================
# STATS ENDPOINTS
# ============================================================================

@app.route('/api/stats/<username>', methods=['GET'])
def get_stats(username):
    try:
        data = load_data()
        actual_username = None
        for u in data['users'].keys():
            if u.lower() == username.lower():
                actual_username = u
                break

        if not actual_username:
            return jsonify({'error': 'User not found'}), 404

        user = data['users'][actual_username]
        return jsonify({
            'username': actual_username,
            'ai_stats': user.get('ai_stats', {}),
            'pvp_wins': user.get('pvp_wins', 0),
            'pvp_losses': user.get('pvp_losses', 0),
            'pvp_draws': user.get('pvp_draws', 0),
            'pvp_games': user.get('pvp_games', 0),
            'pvp_streak': user.get('pvp_streak', 0),
            'pvp_best_streak': user.get('pvp_best_streak', 0),
            'total_wagered': user.get('total_wagered', 0),
            'achievements': user.get('achievements', []),
            'total_wins': user.get('total_wins', 0),
            'total_draws': user.get('total_draws', 0)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats/<username>', methods=['POST'])
def save_stats(username):
    try:
        # AUTHENTICATION REQUIRED
        auth_user = get_auth_user()
        if not auth_user:
            return jsonify({'error': 'Authentication required'}), 401
        if auth_user.lower() != username.lower():
            return jsonify({'error': 'Cannot modify other users'}), 403

        body = request.get_json()
        data = load_data()

        actual_username = None
        for u in data['users'].keys():
            if u.lower() == username.lower():
                actual_username = u
                break

        if not actual_username:
            return jsonify({'error': 'User not found'}), 404

        user = data['users'][actual_username]

        # Update allowed fields only
        for field in ['ai_stats', 'pvp_wins', 'pvp_losses', 'pvp_draws',
                      'pvp_games', 'pvp_streak', 'pvp_best_streak',
                      'total_wagered', 'achievements', 'total_wins', 'total_draws']:
            if field in body:
                user[field] = body[field]

        user['last_updated'] = datetime.now().isoformat()
        save_data(data)
        return jsonify({'success': True})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# LEADERBOARD ENDPOINTS
# ============================================================================

@app.route('/api/leaderboard/ai/wins', methods=['GET'])
def ai_leaderboard():
    try:
        limit = request.args.get('limit', 10, type=int)
        data = load_data()
        leaderboard = []
        for username, user in data['users'].items():
            ai_stats = user.get('ai_stats', {})
            total_wins = sum(s.get('w', 0) for s in ai_stats.values())
            if total_wins > 0:
                leaderboard.append({'username': username, 'value': total_wins})
        leaderboard.sort(key=lambda x: x['value'], reverse=True)
        return jsonify({'leaderboard': leaderboard[:limit]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard/pvp/wins', methods=['GET'])
def pvp_leaderboard():
    try:
        limit = request.args.get('limit', 10, type=int)
        data = load_data()
        leaderboard = []
        for username, user in data['users'].items():
            pvp_wins = user.get('pvp_wins', 0)
            if pvp_wins > 0:
                leaderboard.append({'username': username, 'value': pvp_wins})
        leaderboard.sort(key=lambda x: x['value'], reverse=True)
        return jsonify({'leaderboard': leaderboard[:limit]})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/', methods=['GET'])
def health():
    return jsonify({'status': 'ok', 'service': 'Wild West Shootout API', 'version': '2.0.0'})

@app.route('/api', methods=['GET'])
def api_info():
    return jsonify({
        'status': 'ok',
        'version': '2.0.0',
        'security': ['bcrypt', 'rate-limiting', 'cors-restricted', 'token-auth']
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
