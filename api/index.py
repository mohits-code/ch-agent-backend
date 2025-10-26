from flask import Flask, request, jsonify
import json
import os
import redis
from dotenv import load_dotenv # <-- Import dotenv

# --- Load environment variables ---
# This line loads variables from a .env file (if it exists)
# This is for LOCAL DEVELOPMENT. Vercel uses its own dashboard.
load_dotenv() 

app = Flask(__name__)

# --- Connect to Redis using Environment Variables ---
# Get the REDIS_URL from the environment.
# os.environ.get() will return None if the variable is not set.
REDIS_URL = os.environ.get("REDIS_URL")

# Initialize Redis client variable
r = None

if not REDIS_URL:
    # If the variable is missing, log a critical error.
    # The app can't run without it.
    app.logger.critical("FATAL ERROR: REDIS_URL environment variable is not set.")
else:
    try:
        # Connect using the URL from the environment
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.ping() # Test the connection
        app.logger.info("Successfully connected to Redis.")
    except Exception as e:
        app.logger.error(f"Failed to connect to Redis at {REDIS_URL}: {e}", exc_info=True)
        # r remains None, so endpoints will fail gracefully

# Define a key to store our JSON data in Redis
REDIS_KEY = "vr_params"
# --- End Redis Setup ---


@app.route("/api/update-params", methods=["POST"])
def update_params():
    """
    Receives JSON and saves it to a Redis key.
    """
    if not r:
        # This check now handles both connection failure and missing URL
        return jsonify({"error": "Redis connection not available"}), 503

    try:
        params = request.get_json()
        if not params:
            return jsonify({"error": "No JSON payload"}), 400

        json_string = json.dumps(params, indent=4)
        r.set(REDIS_KEY, json_string)
        
        app.logger.info(f"Successfully wrote params to Redis key: {REDIS_KEY}")
        return jsonify({"success": True, "params_saved": params}), 200

    except Exception as e:
        app.logger.error(f"Error in update_params writing to Redis: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-params", methods=["GET"])
def get_params():
    """
    Attempts to read the parameters from the Redis key.
    """
    if not r:
        return jsonify({"error": "Redis connection not available"}), 503

    try:
        json_string = r.get(REDIS_KEY)
        
        if json_string:
            params = json.loads(json_string)
            app.logger.info(f"Successfully read params from Redis key: {REDIS_KEY}")
            return jsonify(params)
        else:
            app.logger.warning(f"Key not found in Redis: {REDIS_KEY}, returning default.")
            default_params = {"seed": 1234, "octaves": 4, "period": 20.0, "persistence": 0.8, "status": "redis_key_not_found"}
            return jsonify(default_params)

    except Exception as e:
        app.logger.error(f"Error in get_params reading from Redis: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# Your original test endpoint
@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"
