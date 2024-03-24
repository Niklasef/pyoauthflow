from flask import Flask, request, jsonify
import requests
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration variables
AUTH_SERVER_INTROSPECT_ENDPOINT = "http://localhost:5002/introspect"

@app.route('/contacts', methods=['GET'])
def get_contacts():
    # Extract the access token from the Authorization header
    auth_header = request.headers.get('Authorization', None)
    if auth_header is None:
        logger.warning("Authorization header is missing from the request.")
        return "Authorization header is missing", 401

    # Expecting header in the format 'Bearer <token>'
    token = auth_header.split(" ")[1] if len(auth_header.split(" ")) == 2 else None

    if not token:
        logger.warning("Bearer token is missing from the Authorization header.")
        return "Bearer token is missing", 401

    # Validate the token with the Authorization Server
    is_valid, token_data = validate_token(token)
    if not is_valid:
        logger.warning(f"Token validation failed. Token: {token}")
        return "Token is invalid or expired", 401

    # Simulate fetching contacts for the user associated with the access token
    contacts = [{"name": "John Doe", "email": "john@example.com"}, {"name": "Jane Doe", "email": "jane@example.com"}]
    return jsonify(contacts)

def validate_token(token):
    response = requests.post(AUTH_SERVER_INTROSPECT_ENDPOINT, data={'token': token})
    if response.status_code == 200:
        # Assuming a successful response includes token data
        token_data = response.json()
        return True, token_data
    return False, None

if __name__ == '__main__':
    logger.info("Starting the Resource Server...")
    app.run(port=5003, debug=True)
    logger.info("Resource Server has started.")
