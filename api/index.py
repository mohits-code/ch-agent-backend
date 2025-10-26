from flask import Flask, request, jsonify # Correct Flask import
from werkzeug.utils import safe_join # Correct safe_join import
import json
import os

app = Flask(__name__)

# --- Use Vercel's temporary directory ---
# NOTE: Files written here are NOT guaranteed to persist between requests!
TEMP_DIR = "/tmp"
# Use safe_join to prevent path traversal issues, though less critical in /tmp
PARAMS_FILE_PATH = safe_join(TEMP_DIR, "vr_params.json")
# --- Use Vercel's temporary directory ---


@app.route("/api/update-params", methods=["POST"])
def update_params():
    """
    Receives JSON from the Maestro agent and attempts to save it to /tmp.
    """
    try:
        params = request.get_json()
        if not params:
            return jsonify({"error": "No JSON payload"}), 400

        # Attempt to write the file in the /tmp directory
        with open(PARAMS_FILE_PATH, "w") as f:
            json.dump(params, f, indent=4)
        
        # Log success (this might appear in Vercel logs)
        app.logger.info(f"Successfully wrote params to {PARAMS_FILE_PATH}")
        return jsonify({"success": True, "params_saved": params}), 200

    except Exception as e:
        app.logger.error(f"Error in update_params writing file: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-params", methods=["GET"])
def get_params():
    """
    Attempts to read the parameters file from /tmp.
    """
    try:
        # Check if the file exists in the /tmp directory
        if os.path.exists(PARAMS_FILE_PATH):
            with open(PARAMS_FILE_PATH, "r") as f:
                params = json.load(f)
            app.logger.info(f"Successfully read params from {PARAMS_FILE_PATH}")
            return jsonify(params)
        else:
            # If the file doesn't exist (very likely), return a default
            app.logger.warning(f"File not found at {PARAMS_FILE_PATH}, returning default.")
            default_params = {"seed": 1234, "octaves": 4, "period": 20.0, "persistence": 0.8, "status": "file_not_found"}
            return jsonify(default_params)

    except Exception as e:
        app.logger.error(f"Error in get_params reading file: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Your original test endpoint
@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"
