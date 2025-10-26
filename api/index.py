from flask import Flask, request, jsonify
from vercel_kv import kv 
import json

app = Flask(__name__)

PARAMS_KEY = "vr_params"

@app.route("/api/update-params", methods=["POST"])
def update_params():
    """
    Receives JSON from the Maestro agent and saves it to Vercel KV.
    """
    try:
        params = request.get_json()
        if not params:
            return jsonify({"error": "No JSON payload"}), 400
            
        # Save the new params to the KV store
        kv.set(PARAMS_KEY, json.dumps(params))
        
        return jsonify({"success": True, "params_saved": params}), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/get-params", methods=["GET"])
def get_params():
    """
    The endpoint your VR app will poll.
    It fetches the latest parameters from Vercel KV.
    """
    try:
        # Get the params from the KV store
        params_str = kv.get(PARAMS_KEY)
        
        if params_str is None:
            # If no params are set, return a default
            default_params = {"seed": 1234, "octaves": 4, "period": 20.0, "persistence": 0.8}
            return jsonify(default_params)
            
        # Parse the string and return the JSON
        params = json.loads(params_str)
        return jsonify(params)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Your original test endpoint
@app.route("/api/python")
def hello_world():
    return "<p>Hello, World!</p>"
