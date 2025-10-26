from flask import Flask, request, jsonify
import json
import os
import base64
import firebase_admin
from firebase_admin import credentials, firestore  # <-- Import firestore, not db
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv() 

app = Flask(__name__)

# --- Connect to Firebase ---
# Get credentials from environment variables
FIREBASE_KEY_BASE64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_BASE64")

# We only need the service account for Firestore, not the Database URL
firebase_initialized = False 
db_client = None # <-- We will store the client here

try:
    if not FIREBASE_KEY_BASE64:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_BASE64 env var not set.")

    # Decode the base64 service account key
    decoded_key = base64.b64decode(FIREBASE_KEY_BASE64).decode('utf-8')
    cred_dict = json.loads(decoded_key)
    
    # Initialize credentials
    cred = credentials.Certificate(cred_dict)
    
    # Initialize Firebase app (no databaseURL needed)
    firebase_admin.initialize_app(cred)
    
    # Get the Firestore client
    db_client = firestore.client() 
    
    firebase_initialized = True
    app.logger.info("Successfully connected to Firebase Cloud Firestore.")

except Exception as e:
    app.logger.critical(f"FATAL ERROR: Failed to initialize Firebase: {e}", exc_info=True)
    # The app will still run, but firebase_initialized will remain False

# --- End Firebase Setup ---


@app.route("/api/update-params", methods=["POST"])
def update_params():
    """
    Receives JSON and saves it to a Firestore document.
    """
    if not firebase_initialized:
         return jsonify({"error": "Firebase connection not available"}), 503
         
    try:
        params = request.get_json()
        if not params:
            return jsonify({"error": "No JSON payload"}), 400

        # Get a reference to the document
        # 'settings' is the collection, 'vr_params' is the document ID
        doc_ref = db_client.collection("settings").document("vr_params")
        
        # Set the data in that document (this overwrites)
        doc_ref.set(params)
        
        app.logger.info(f"Successfully wrote params to Firestore path: settings/vr_params")
        return jsonify({"success": True, "params_saved": params}), 200

    except Exception as e:
        app.logger.error(f"Error in update_params writing to Firestore: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-params", methods=["GET"])
def get_params():
    """
    Attempts to read the parameters from the Firestore document.
    """
    if not firebase_initialized:
         return jsonify({"error": "Firebase connection not available"}), 503
         
    try:
        # Get a reference to the document
        doc_ref = db_client.collection("settings").document("vr_params")
        
        # Get the data from the document
        doc = doc_ref.get()
        
        if doc.exists:
            # If the document exists, get its data
            params = doc.to_dict()
            app.logger.info(f"Successfully read params from Firestore path: settings/vr_params")
            return jsonify(params)
        else:
            # If the document doesn't exist
            app.logger.warning(f"Document settings/vr_params not found in Firestore, returning default.")
            default_params = {"seed": 1234, "octaves": 4, "period": 20.0, "persistence": 0.8, "status": "firestore_doc_not_found"}
            return jsonify(default_params)

    except Exception as e:
        app.logger.error(f"Error in get_params reading from Firestore: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Your original test endpoint
@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"
