from flask import Flask, request, jsonify, redirect
import requests
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration variables
AUTH_SERVER_AUTH_ENDPOINT = "http://localhost:5002/authorize"
AUTH_SERVER_TOKEN_ENDPOINT = "http://localhost:5002/token"
CLIENT_ID = 'email-sender'
CLIENT_SECRET = 'email-sender-secret-1234'
REDIRECT_URI = 'http://localhost:5001/callback'

@app.route('/login')
def login():
    # Redirect user to the Authorization Server's authorization endpoint
    return redirect(f"{AUTH_SERVER_AUTH_ENDPOINT}?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}")

@app.route('/callback')
def callback():
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400

    access_token = exchange_auth_code_for_token(code)
    if not access_token:
        return jsonify({'error': 'Failed to obtain access token'}), 500

    # Return the access token to the client (e.g., Insomnia)
    return jsonify({'access_token': access_token})

@app.route('/send-email', methods=['POST'])
def send_email():
    access_token = request.headers.get('Authorization')
    if not access_token:
        logger.info("No access token provided.")
        return jsonify({'error': 'Access token is required'}), 401

    logger.info("Access token received, fetching contacts.")
    contacts = get_contacts(access_token)
    if 'error' in contacts:
        logger.error("Failed to fetch contacts: %s", contacts['error'])
        return jsonify(contacts), 500
    
    logger.info("Contacts fetched successfully. Preparing to send emails.")
    # Logic to send emails to contacts goes here
    return jsonify({'message': 'Emails would be sent to the following contacts:', 'contacts': contacts})

def exchange_auth_code_for_token(code):
    payload = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(AUTH_SERVER_TOKEN_ENDPOINT, data=payload)
    if response.status_code == 200:
        return response.json().get('access_token')
    return None


def get_contacts(access_token):
    contacts_url = "http://localhost:5003/contacts"
    headers = {'Authorization': access_token}
    response = requests.get(contacts_url, headers=headers)
    if response.status_code == 200:
        logger.info("Contacts retrieved successfully from resource server.")
        return response.json()
    logger.error("Error fetching contacts from resource server, status code: %d", response.status_code)
    return {'error': 'Failed to fetch contacts'}

if __name__ == '__main__':
    logger.info("Starting the email sender client application...")
    app.run(port=5001, debug=True)
    logger.info("Email Sender Client application has started.")
