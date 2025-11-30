from flask import Flask, send_from_directory, jsonify, request
import json
import os

app = Flask(__name__)

LEADERBOARD_FILE = 'leaderboard.json'

def load_leaderboard():
    if os.path.exists(LEADERBOARD_FILE):
        with open(LEADERBOARD_FILE, 'r') as f:
            return json.load(f)
    return []

def save_leaderboard(data):
    with open(LEADERBOARD_FILE, 'w') as f:
        json.dump(data, f)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/api/leaderboard', methods=['GET'])
def get_leaderboard():
    leaderboard = load_leaderboard()
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    return jsonify(sorted_leaderboard)

@app.route('/api/check-username', methods=['POST'])
def check_username():
    data = request.get_json()
    username = data.get('username', '').strip()
    
    if not username:
        return jsonify({'available': False, 'error': 'Username required'}), 400
    
    leaderboard = load_leaderboard()
    existing_user = next((u for u in leaderboard if u['username'].lower() == username.lower()), None)
    
    return jsonify({'available': existing_user is None})

@app.route('/api/leaderboard', methods=['POST'])
def update_leaderboard():
    data = request.get_json()
    username = data.get('username', '').strip()
    score = data.get('score', 0)
    
    if not username:
        return jsonify({'error': 'Username required'}), 400
    
    leaderboard = load_leaderboard()
    
    existing_user = next((u for u in leaderboard if u['username'].lower() == username.lower()), None)
    
    if existing_user:
        if score > existing_user['score']:
            existing_user['score'] = score
    else:
        leaderboard.append({'username': username, 'score': score})
    
    save_leaderboard(leaderboard)
    
    sorted_leaderboard = sorted(leaderboard, key=lambda x: x['score'], reverse=True)[:10]
    return jsonify(sorted_leaderboard)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
