#!/usr/bin/env python3
"""LinuxBox - Hands-on Linux Learning Platform"""

import json
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
from datetime import datetime

PORT = 3333
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROGRESS_FILE = os.path.join(BASE_DIR, 'progress.json')
WAITLIST_FILE = os.path.join(BASE_DIR, 'waitlist.json')

CHALLENGES = [
    {
        'id': 1,
        'title': 'Broken Apache',
        'subtitle': 'Month 1 - Web Server Basics',
        'difficulty': 'Beginner',
        'scenario': 'A web server stopped working after a config change. Fix it!',
        'tasks': ['Find the typo in the config', 'Restart the service', 'Verify it works'],
        'hints': ['Check for missing semicolons', 'Use systemctl status'],
        'badge': '🔧 Apache Apprentice'
    },
    {
        'id': 2,
        'title': 'Permission Denied',
        'subtitle': 'Month 2 - Security Fundamentals',
        'difficulty': 'Beginner',
        'scenario': 'A script refuses to run. Diagnose and fix the permissions.',
        'tasks': ['Identify the permission issue', 'Fix without chmod 777', 'Run successfully'],
        'hints': ['Check owner and group', 'Look at execute bit'],
        'badge': '🔐 Permission Pro'
    },
    {
        'id': 3,
        'title': 'Network Nightmare',
        'subtitle': 'Month 3 - Networking',
        'difficulty': 'Intermediate',
        'scenario': 'Server cant reach the internet. Debug the network!',
        'tasks': ['Ping localhost', 'Check DNS resolution', 'Fix connectivity'],
        'hints': ['cat /etc/resolv.conf', 'nslookup google.com'],
        'badge': '🌐 Network Ninja'
    },
    {
        'id': 4,
        'title': 'Systemd Struggles',
        'subtitle': 'Month 4 - Service Management',
        'difficulty': 'Intermediate',
        'scenario': 'A service wont start. Debug the systemd unit file.',
        'tasks': ['Check service status', 'Find the syntax error', 'Reload and start'],
        'hints': ['journalctl -xe', 'systemctl daemon-reload'],
        'badge': '⚙️ Systemd Master'
    },
    {
        'id': 5,
        'title': 'Disk Disaster',
        'subtitle': 'Month 5 - Storage',
        'difficulty': 'Advanced',
        'scenario': 'Disk is full but du shows space. Find the hidden culprit!',
        'tasks': ['Find processes holding deleted files', 'Restart or kill them', 'Reclaim space'],
        'hints': ['lsof | grep deleted', 'Check /proc/*/fd'],
        'badge': '💾 Storage Sherlock'
    }
]

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {'completed': [], 'badges': [], 'currentChallenge': 1}

def save_progress(data):
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_waitlist():
    if os.path.exists(WAITLIST_FILE):
        with open(WAITLIST_FILE) as f:
            return json.load(f)
    return []

def save_waitlist(email):
    waitlist = load_waitlist()
    if email not in [w['email'] for w in waitlist]:
        waitlist.append({
            'email': email,
            'signed_up': datetime.now().isoformat()
        })
        with open(WAITLIST_FILE, 'w') as f:
            json.dump(waitlist, f, indent=2)
        return True
    return False

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=os.path.join(BASE_DIR, 'public'), **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/challenges':
            self.send_json(CHALLENGES)
        elif parsed.path == '/api/progress':
            self.send_json(load_progress())
        else:
            super().do_GET()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length) if content_length else b'{}'
        
        if parsed.path == '/api/waitlist':
            try:
                data = json.loads(body)
                email = data.get('email', '').strip().lower()
                
                if not email or '@' not in email:
                    self.send_error(400, 'Invalid email')
                    return
                
                added = save_waitlist(email)
                self.send_json({'success': True, 'added': added})
            except Exception as e:
                self.send_error(400, str(e))
        elif parsed.path.startswith('/api/complete/'):
            try:
                challenge_id = int(parsed.path.split('/')[-1])
                progress = load_progress()
                challenge = next((c for c in CHALLENGES if c['id'] == challenge_id), None)
                
                if challenge and challenge_id not in progress['completed']:
                    progress['completed'].append(challenge_id)
                    progress['badges'].append(challenge['badge'])
                    progress['currentChallenge'] = challenge_id + 1
                    save_progress(progress)
                
                self.send_json({'success': True, 'badge': challenge['badge'] if challenge else None, 'progress': progress})
            except Exception as e:
                self.send_error(400, str(e))
        else:
            self.send_error(404)
    
    def send_json(self, data):
        content = json.dumps(data).encode()
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', len(content))
        self.end_headers()
        self.wfile.write(content)

if __name__ == '__main__':
    print(f'🐧 LinuxBox running at http://localhost:{PORT}')
    print(f'Network: http://37.60.229.29:{PORT}')
    HTTPServer(('0.0.0.0', PORT), Handler).serve_forever()