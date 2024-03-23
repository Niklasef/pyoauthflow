from flask import Flask, request, redirect
import os
import secrets
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # A secret key for session management

# Dummy in-memory 'database' for this example
users = {'user1': 'password1'}
authorized_codes = {}  # Store authorization codes temporarily

@app.route('/authorize')
def authorize():
    user = request.args.get('user')
    password = request.args.get('password')
    grant = request.args.get('grant', 'no').lower() == 'yes'

    if user not in users:
        # User not found
        return "User not found", 404

    if users[user] != password:
        # Password does not match
        return "Authentication failed", 401

    if grant:
        # User authenticated and grant is 'yes'
        client_id = request.args.get('client_id')
        redirect_uri = request.args.get('redirect_uri')
        
        # Generate an authorization code
        auth_code = secrets.token_urlsafe(16)
        
        # Store the code temporarily with associated client_id and user
        authorized_codes[auth_code] = {'client_id': client_id, 'user': user}
        
        # Redirect back to the client with the authorization code
        return redirect(f"{redirect_uri}?code={auth_code}")
    else:
        # User authenticated but grant is not 'yes'
        return "Access not granted by user. Add 'grant=yes' to grant access.", 401

if __name__ == '__main__':
    logger.info("Starting the auth server...")
    app.run(port=5002, debug=True)
    logger.info("Auth server has started.")
