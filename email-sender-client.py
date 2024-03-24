from flask import Flask, request, redirect, render_template_string
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
        return "No authorization code received", 401

    access_token = exchange_auth_code_for_token(code)
    return f"Access token: {access_token}"

@app.route('/send-email', methods=['POST'])
def send_email():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        logger.info("No Authorization header provided.")
        return "Authorization header is required", 401

    # Split the header value to extract the token part after 'Bearer'
    parts = auth_header.split()
    if len(parts) == 2 and parts[0].lower() == 'bearer':
        access_token = parts[1]
    else:
        logger.info("Authorization header must be in 'Bearer <token>' format.")
        return "Invalid Authorization header format", 401

    logger.info("Bearer token received, fetching contacts.")
    contacts = get_contacts(access_token)
    if 'error' in contacts:
        return f"Error retrieving contacts: {contacts['error']}"

    contacts_info = ', '.join([f"{contact['name']} ({contact['email']})" for contact in contacts])
    logger.info("Contacts fetched successfully. Preparing to send emails.")
    return f"Emails would be sent to the following contacts: {contacts_info}"

def exchange_auth_code_for_token(code):
    payload = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(AUTH_SERVER_TOKEN_ENDPOINT, data=payload)
    return response.text.strip()  # Assuming the response is just the access token as plain text

def get_contacts(access_token):
    contacts_url = "http://localhost:5003/contacts"
    headers = {'Authorization': f'Bearer {access_token}'}
    
    # Log the outgoing request details
    logger.info(f"Making request to Resource Server: {contacts_url}")
    logger.info(f"Request headers: {headers}")
    
    response = requests.get(contacts_url, headers=headers)

    if response.status_code == 200:
        logger.info("Contacts retrieved successfully from resource server.")
        return response.json()  # Parse the JSON response to get the contacts list
    else:
        logger.error(f"Failed to fetch contacts. Status code: {response.status_code}, Response: {response.text}")
        return {'error': f"HTTP {response.status_code}"}


if __name__ == '__main__':
    logger.info("Starting the email sender client application...")
    app.run(port=5001, debug=True)
    logger.info("Email Sender Client application has started.")
