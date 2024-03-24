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
    # The callback endpoint might simply inform the user that the authorization was successful
    # and instruct them to use the authorization code with the send-email endpoint.
    code = request.args.get('code')
    if not code:
        return "No authorization code received", 400
    return f"Authorization successful. Please use the following code with the send-email endpoint: {code}"

@app.route('/send-email', methods=['POST'])
def send_email():
    # Expecting an authorization code in the request
    auth_code = request.form.get('code') or request.headers.get('Authorization-Code')
    if not auth_code:
        logger.info("No authorization code provided.")
        return "Authorization code is required", 401

    # Exchange the authorization code for an access token
    access_token = exchange_auth_code_for_token(auth_code)
    if not access_token:
        return "Failed to exchange authorization code for access token", 500

    logger.info("Access token received, fetching contacts.")
    contacts = get_contacts(access_token)

    logger.info("Contacts fetched successfully. Preparing to send emails.")
    # Logic to send emails to contacts goes here
    return f"Emails would be sent to the following contacts: {contacts}"

def exchange_auth_code_for_token(code):
    payload = {
        'grant_type': 'authorization_code',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'code': code,
        'redirect_uri': REDIRECT_URI
    }
    response = requests.post(AUTH_SERVER_TOKEN_ENDPOINT, data=payload)
    # Assuming the response contains the access token directly in the body
    return response.text.strip()

def get_contacts(access_token):
    contacts_url = "http://localhost:5003/contacts"
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(contacts_url, headers=headers)
    logger.info("Contacts retrieved successfully from resource server.")
    return response.text

if __name__ == '__main__':
    logger.info("Starting the email sender client application...")
    app.run(port=5001, debug=True)
    logger.info("Email Sender Client application has started.")
