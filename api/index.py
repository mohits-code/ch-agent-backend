from flask import Flask, request, jsonify
import json
import os
import redis

app = Flask(__name__)

# --- Connect to Redis ---
# This pulls the connection string from an environment variable.
# Vercel KV or services like Upstash provide this URL.
REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    # Fallback for local testing (assumes Redis is running on localhost:6379)
    # WARNING: Vercel will not use this. Set the REDIS_URL env var in Vercel.
    REDIS_URL = "redis://localhost:6379" 
    app.logger.warning("REDIS_URL not set, falling back to localhost.")

try:
    # Initialize the Redis client
    # decode_responses=True automatically handles decoding from bytes to strings
    r = redis.from_url(REDIS_URL, decode_responses=True)
    r.ping() # Test the connection
    app.logger.info("Successfully connected to Redis.")
except Exception as e:
    app.logger.error(f"Failed to connect to Redis: {e}", exc_info=True)
    # If we can't connect, we can't really run the app.
    # In a real app, you might have more graceful error handling.
    r = None 

# Define a key to store our JSON data in Redis
REDIS_KEY = "vr_params"
# --- End Redis Setup ---


@app.route("/api/update-params", methods=["POST"])
def update_params():
    """
    Receives JSON and saves it to a Redis key.
    """
    if not r:
        return jsonify({"error": "Redis connection not available"}), 503

    try:
        params = request.get_json()
        if not params:
            return jsonify({"error": "No JSON payload"}), 400

        # Serialize the Python dict to a JSON string before saving
        json_string = json.dumps(params, indent=4)
        
        # Save the string to Redis using the SET command
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
        # Get the value (string) from Redis using the GET command
        json_string = r.get(REDIS_KEY)
        
        if json_string:
            # If the key exists, parse the JSON string back into a Python dict
            params = json.loads(json_string)
            app.logger.info(f"Successfully read params from Redis key: {REDIS_KEY}")
            return jsonify(params)
        else:
            # If the key doesn't exist, r.get() returns None
            app.logger.warning(f"Key not found in Redis: {REDIS_KEY}, returning default.")
            default_params = {"seed": 1234, "octaves": 4, "period": 20.0, "persistence": 0.8, "status": "redis_key_not_found"}
            return jsonify(default_params)

    except Exception as e:
        app.logger.error(f"Error in get_params reading from Redis: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

