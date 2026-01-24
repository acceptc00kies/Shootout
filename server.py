"""
Wild West Shootout - Stats API Backend
Flask server for user authentication, stats, and leaderboards
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import os
import hashlib
from datetime import datetime

app = Flask(__name__)
CORS(app)  # Enable cross-origin requests

# Data storage (JSON file)
DATA_FILE = 'data.json'

def load_data():
    """Load data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'users': {}, 'created': datetime.now().isoformat()}

def save_data(data):
    """Save data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def hash_password(password):
    """Simple password hashing"""
    return hashlib.sha256(password.encode()).hexdigest()

# ============================================================================
# AUTH ENDPOINTS
# ============================================================================

@app.route('/api/register', methods=['POST'])
def register():
    """Register a new user"""
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

        # Create new user
        data['users'][username] = {
            'password': hash_password(password),
            'created': datetime.now().isoformat(),
            'ai_stats': {},
            'pvp_wins': 0,
            'pvp_losses': 0,
            'pvp_draws': 0,
            'pvp_games': 0,
            'pvp_streak': 0,
            'pvp_best_streak': 0,
            'total_wagered': 0,
            'achievements': [],
            'total_wins': 0,
            'total_draws': 0
        }

        save_data(data)
        return jsonify({'success': True, 'message': 'Account created'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Login existing user"""
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

        if user['password'] != hash_password(password):
            return jsonify({'error': 'Invalid password'}), 401

        return jsonify({'success': True, 'username': actual_username})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STATS ENDPOINTS
# ============================================================================

@app.route('/api/stats/<username>', methods=['GET'])
def get_stats(username):
    """Get user stats"""
    try:
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
    """Save user stats"""
    try:
        body = request.get_json()
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

        # Update stats
        if 'ai_stats' in body:
            user['ai_stats'] = body['ai_stats']
        if 'pvp_wins' in body:
            user['pvp_wins'] = body['pvp_wins']
        if 'pvp_losses' in body:
            user['pvp_losses'] = body['pvp_losses']
        if 'pvp_draws' in body:
            user['pvp_draws'] = body['pvp_draws']
        if 'pvp_games' in body:
            user['pvp_games'] = body['pvp_games']
        if 'pvp_streak' in body:
            user['pvp_streak'] = body['pvp_streak']
        if 'pvp_best_streak' in body:
            user['pvp_best_streak'] = body['pvp_best_streak']
        if 'total_wagered' in body:
            user['total_wagered'] = body['total_wagered']
        if 'achievements' in body:
            user['achievements'] = body['achievements']
        if 'total_wins' in body:
            user['total_wins'] = body['total_wins']
        if 'total_draws' in body:
            user['total_draws'] = body['total_draws']

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
    """Get AI wins leaderboard"""
    try:
        limit = request.args.get('limit', 10, type=int)
        data = load_data()

        leaderboard = []
        for username, user in data['users'].items():
            ai_stats = user.get('ai_stats', {})
            total_wins = sum(s.get('w', 0) for s in ai_stats.values())
            if total_wins > 0:
                leaderboard.append({
                    'username': username,
                    'value': total_wins
                })

        leaderboard.sort(key=lambda x: x['value'], reverse=True)
        return jsonify({'leaderboard': leaderboard[:limit]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/leaderboard/pvp/wins', methods=['GET'])
def pvp_leaderboard():
    """Get PvP wins leaderboard"""
    try:
        limit = request.args.get('limit', 10, type=int)
        data = load_data()

        leaderboard = []
        for username, user in data['users'].items():
            pvp_wins = user.get('pvp_wins', 0)
            if pvp_wins > 0:
                leaderboard.append({
                    'username': username,
                    'value': pvp_wins
                })

        leaderboard.sort(key=lambda x: x['value'], reverse=True)
        return jsonify({'leaderboard': leaderboard[:limit]})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.route('/', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'service': 'Wild West Shootout API',
        'version': '1.0.0'
    })

@app.route('/api', methods=['GET'])
def api_info():
    """API info endpoint"""
    return jsonify({
        'status': 'ok',
        'endpoints': [
            'POST /api/register',
            'POST /api/login',
            'GET /api/stats/:username',
            'POST /api/stats/:username',
            'GET /api/leaderboard/ai/wins',
            'GET /api/leaderboard/pvp/wins'
        ]
    })

# ============================================================================
# MAIN
# ============================================================================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
