#!/usr/bin/env python3
"""
Box OAuth 2.0 - Get Refresh Token (Run this ONCE locally)

This script helps you obtain a refresh token for Box OAuth 2.0.
You only need to run this once, then store the refresh token in GitHub Secrets.

Instructions:
1. Run: python scripts/get_box_refresh_token.py
2. A browser will open asking you to authorize the app
3. After authorization, copy the REFRESH_TOKEN printed
4. Add it to GitHub Secrets as BOX_REFRESH_TOKEN
"""

import requests
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import threading

# Box OAuth 2.0 Configuration
CLIENT_ID = '0o35l8woygv1tnj13sg85uf26ei2f0n7'
CLIENT_SECRET = 'AFcqfModQrmyY0hIzOS1BeaXS5DKzCdI'
REDIRECT_URI = 'http://localhost:8080/callback'

# Global variable to store the authorization code
auth_code = None
server_done = False

class CallbackHandler(BaseHTTPRequestHandler):
    """Handle the OAuth callback"""
    
    def do_GET(self):
        global auth_code, server_done
        
        # Parse the query parameters
        query = urlparse(self.path).query
        params = parse_qs(query)
        
        if 'code' in params:
            auth_code = params['code'][0]
            
            # Send success response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''<html><body>
                <h1>Authorization Successful!</h1>
                <p>You can close this window and return to the terminal.</p>
                </body></html>''')
            
            server_done = True
        else:
            # Send error response
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'''<html><body>
                <h1>Authorization Failed</h1>
                <p>No authorization code received.</p>
                </body></html>''')
    
    def log_message(self, format, *args):
        # Suppress log messages
        pass

def start_callback_server():
    """Start local server to receive OAuth callback"""
    server = HTTPServer(('localhost', 8080), CallbackHandler)
    
    while not server_done:
        server.handle_request()
    
    server.server_close()

def get_authorization_code():
    """Open browser for user authorization"""
    auth_url = (
        f'https://account.box.com/api/oauth2/authorize'
        f'?client_id={CLIENT_ID}'
        f'&response_type=code'
        f'&redirect_uri={REDIRECT_URI}'
    )
    
    print("\n" + "="*80)
    print("BOX OAUTH 2.0 - GET REFRESH TOKEN")
    print("="*80)
    print("\nStep 1: Opening browser for authorization...")
    print(f"If browser doesn't open, visit: {auth_url}\n")
    
    # Start callback server in separate thread
    server_thread = threading.Thread(target=start_callback_server, daemon=True)
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Wait for authorization code
    print("Waiting for authorization...")
    server_thread.join(timeout=300)  # 5 minute timeout
    
    return auth_code

def exchange_code_for_tokens(code):
    """Exchange authorization code for access and refresh tokens"""
    token_url = 'https://api.box.com/oauth2/token'
    
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    
    print("\nStep 2: Exchanging authorization code for tokens...")
    response = requests.post(token_url, data=data)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"ERROR: Failed to get tokens: {response.status_code}")
        print(response.text)
        return None

def main():
    # Get authorization code
    code = get_authorization_code()
    
    if not code:
        print("\nERROR: Failed to get authorization code")
        return
    
    print(f"✓ Authorization code received: {code[:20]}...")
    
    # Exchange for tokens
    tokens = exchange_code_for_tokens(code)
    
    if not tokens:
        return
    
    print("\n" + "="*80)
    print("SUCCESS! Tokens received:")
    print("="*80)
    print(f"\nAccess Token: {tokens['access_token'][:40]}...")
    print(f"Refresh Token: {tokens['refresh_token']}")
    print(f"Expires in: {tokens['expires_in']} seconds")
    
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("="*80)
    print("\n1. Copy the REFRESH_TOKEN above")
    print("2. Go to GitHub repository Settings > Secrets and variables > Actions")
    print("3. Add a new secret named: BOX_REFRESH_TOKEN")
    print("4. Paste the refresh token as the value")
    print("\nThe refresh token will be used to automatically get access tokens forever!\n")

if __name__ == '__main__':
    main()
