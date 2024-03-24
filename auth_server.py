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
clients = {
    'email-sender': {
        'client_secret': 'email-sender-secret-1234',
        'redirect_uris': ['http://localhost:5001/callback']
    }
}
authorized_codes = {}  # Store authorization codes temporarily
# Token storage, mapping tokens to their data
tokens = {}

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

@app.route('/token', methods=['POST'])
def token():
    client_id = request.form.get('client_id')
    client_secret = request.form.get('client_secret')
    code = request.form.get('code')
    redirect_uri = request.form.get('redirect_uri')

    # Validate client credentials and authorization code
    if (client_id in clients and
            clients[client_id]['client_secret'] == client_secret and
            redirect_uri in clients[client_id]['redirect_uris'] and
            code in authorized_codes and
            authorized_codes[code]['client_id'] == client_id):

        # Remove the used authorization code
        del authorized_codes[code]

        # Generate an access token (for simplicity, we're using a random string here)
        access_token = secrets.token_urlsafe(32)
        # Store token data
        tokens[access_token] = {
            'user': authorized_codes[code]['user'],
            'scopes': ['email'],  # Example scope
            'expires_in': 3600  # Example expiration, in seconds
        }

        # In a real application, you might want to associate this token with user data,
        # set an expiration, and store it so it can be validated later.
        logger.info(f"Access token issued: {access_token}")

        # Return the access token to the client
        return access_token
    else:
        logger.error("Invalid request for token")
        return "Invalid request", 400

@app.route('/introspect', methods=['POST'])
def introspect():
    token = request.form.get('token')

    # Check if the token exists and is valid
    token_data = tokens.get(token)
    if token_data:
        # In a real app, you'd also check if the token has expired
        return token_data  # Simplified for demo; consider what data should be shared
    else:
        return "Token is invalid or expired", 401

if __name__ == '__main__':
    logger.info("Starting the auth server...")
    app.run(port=5002, debug=True)
    logger.info("Auth server has started.")
