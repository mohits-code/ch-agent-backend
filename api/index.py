from flask import Flask, request, jsonify
import json
import os
import base64
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv() 

app = Flask(__name__)

# --- Connect to Firebase ---
# Get credentials from environment variables
FIREBASE_DB_URL = os.environ.get("FIREBASE_DATABASE_URL")
FIREBASE_KEY_BASE64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_BASE64")

#  FIX 1: Create a flag to track initialization
firebase_initialized = False 

try:
    if not FIREBASE_DB_URL or not FIREBASE_KEY_BASE64:
        raise ValueError("FIREBASE_DATABASE_URL or FIREBASE_SERVICE_ACCOUNT_BASE64 env vars not set.")

    # Decode the base64 service account key
    decoded_key = base64.b64decode(FIREBASE_KEY_BASE64).decode('utf-8')
    cred_dict = json.loads(decoded_key)
    
    # Initialize credentials
    cred = credentials.Certificate(cred_dict)
    
    # Initialize Firebase app
    firebase_admin.initialize_app(cred, {
        'databaseURL': FIREBASE_DB_URL
    })
    
    #  FIX 2: Set the flag to True on success
    firebase_initialized = True
    app.logger.info("Successfully connected to Firebase Realtime Database.")

except Exception as e:
    app.logger.critical(f"FATAL ERROR: Failed to initialize Firebase: {e}", exc_info=True)
    # The app will still run, but firebase_initialized will remain False

# --- End Firebase Setup ---


@app.route("/api/update-params", methods=["POST"])
def update_params():
    """
    Receives JSON and saves it to a Firebase Realtime Database path.
    """
    #  FIX 3: Check our custom flag
    if not firebase_initialized:
         return jsonify({"error": "Firebase connection not available"}), 503
         
    try:
        params = request.get_json()
        if not params:
            return jsonify({"error": "No JSON payload"}), 400

        # Get a reference to the path '/vr_params'
        ref = db.reference("vr_params")
        
        # Set the data at that path (this overwrites any existing data)
        ref.set(params)
        
        app.logger.info(f"Successfully wrote params to Firebase path: /vr_params")
        return jsonify({"success": True, "params_saved": params}), 200

    except Exception as e:
        app.logger.error(f"Error in update_params writing to Firebase: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-params", methods=["GET"])
def get_params():
    """
    Attempts to read the parameters from the Firebase path.
    """
    #  FIX 3 (repeated): Check our custom flag
    if not firebase_initialized:
         return jsonify({"error": "Firebase connection not available"}), 503
         
    try:
        # Get a reference to the path '/vr_params'
        ref = db.reference("vr_params")
        
        # Get the data from the path
        params = ref.get()
        
        if params:
            # If the path exists, 'params' will be our dictionary
            app.logger.info(f"Successfully read params from Firebase path: /vr_params")
            return jsonify(params)
        else:
            # If the path doesn't exist, ref.get() returns None
            app.logger.warning(f"Path /vr_params not found in Firebase, returning default.")
            default_params = {"seed": 1234, "octaves": 4, "period": 20.0, "persistence": 0.8, "status": "firebase_path_not_found"}
            return jsonify(default_params)

    except Exception as e:
        app.logger.error(f"Error in get_params reading from Firebase: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Your original test endpoint
@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"
