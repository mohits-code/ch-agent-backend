from flask import Flask, request, jsonify
import json
import os
import base64
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
from dotenv import load_dotenv

# Load .env file for local development
load_dotenv() 

app = Flask(__name__)

# --- Connect to Firebase ---
# Get credentials from environment variables
FIREBASE_KEY_BASE64 = os.environ.get("FIREBASE_SERVICE_ACCOUNT_BASE64")

firebase_initialized = False 
db_client = None

try:
    if not FIREBASE_KEY_BASE64:
        raise ValueError("FIREBASE_SERVICE_ACCOUNT_BASE64 env var not set.")
    
    # Decode the base64 service account key
    decoded_key = base64.b64decode(FIREBASE_KEY_BASE64).decode('utf-8')
    cred_dict = json.loads(decoded_key)
    
    # Initialize credentials
    cred = credentials.Certificate(cred_dict)
    
    # Initialize Firebase app
    firebase_admin.initialize_app(cred)
    
    # Get the Firestore client
    db_client = firestore.client() 
    
    firebase_initialized = True
    app.logger.info("Successfully connected to Firebase Cloud Firestore.")
except Exception as e:
    app.logger.critical(f"FATAL ERROR: Failed to initialize Firebase: {e}", exc_info=True)

# --- End Firebase Setup ---


@app.route("/api/update-params", methods=["POST"])
def update_params():
    """
    Receives JSON, adds a timestamp, and saves it to a Firestore document.
    """
    if not firebase_initialized:
          return jsonify({"error": "Firebase connection not available"}), 503
          
    try:
        params = request.get_json()
        if not params:
            return jsonify({"error": "No JSON payload"}), 400
        
        # --- MODIFICATION ---
        # 1. Create a timestamp, just like in /api/submit-prompt
        timestamp = datetime.utcnow().isoformat()
        
        # 2. Add the timestamp directly to the params dictionary
        #    Any client polling /get-params can now check this field.
        params["last_updated_timestamp"] = timestamp
        # --- END MODIFICATION ---
        
        # Get a reference to the document
        doc_ref = db_client.collection("settings").document("vr_params")
        
        # Set the data in that document (this overwrites)
        # This will now save the original params + the new timestamp field
        doc_ref.set(params)
        
        app.logger.info(f"Successfully wrote params to Firestore path: settings/vr_params with timestamp: {timestamp}")
        
        # Return the new timestamp in the success response for consistency
        return jsonify({"success": True, "params_saved": params, "timestamp": timestamp}), 200
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
            params = doc.to_dict()
            app.logger.info(f"Successfully read params from Firestore path: settings/vr_params")
            return jsonify(params)
        else:
            app.logger.warning(f"Document settings/vr_params not found in Firestore, returning default.")
            default_params = {"seed": 1234, "octaves": 4, "period": 20.0, "persistence": 0.8, "status": "firestore_doc_not_found"}
            return jsonify(default_params)
    except Exception as e:
        app.logger.error(f"Error in get_params reading from Firestore: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/submit-prompt", methods=["POST"])
def submit_prompt():
    """
    Receives a prompt from the frontend/user and stores it with a timestamp.
    The agent will poll this endpoint to check for new prompts.
    """
    if not firebase_initialized:
        return jsonify({"error": "Firebase connection not available"}), 503
    
    try:
        data = request.get_json()
        if not data or "prompt" not in data:
            return jsonify({"error": "No prompt provided"}), 400
        
        prompt_text = data["prompt"]
        
        # Create a timestamp
        timestamp = datetime.utcnow().isoformat()
        
        # Store in Firestore
        doc_ref = db_client.collection("settings").document("prompt_request")
        doc_ref.set({
            "prompt": prompt_text,
            "timestamp": timestamp,
            "processed": False
        })
        
        app.logger.info(f"Stored new prompt request with timestamp: {timestamp}")
        return jsonify({"success": True, "timestamp": timestamp}), 200
        
    except Exception as e:
        app.logger.error(f"Error in submit_prompt: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/get-prompt-request", methods=["GET"])
def get_prompt_request():
    """
    Returns the current prompt request for the agent to poll.
    Agent checks if timestamp has changed to know if there's a new prompt.
    """
    if not firebase_initialized:
        return jsonify({"error": "Firebase connection not available"}), 503
    
    try:
        # Get the prompt request document
        doc_ref = db_client.collection("settings").document("prompt_request")
        doc = doc_ref.get()
        
        if doc.exists:
            data = doc.to_dict()
            return jsonify(data), 200
        else:
            # No prompt request exists yet
            return jsonify({}), 200
            
    except Exception as e:
        app.logger.error(f"Error in get_prompt_request: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"


if __name__ == "__main__":
    app.run(debug=True)
