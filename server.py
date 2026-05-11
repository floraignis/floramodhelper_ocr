import os
from functools import wraps
from flask import Flask, request, jsonify
from ocr_core import run_easyocr, get_reader

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is not set")

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_KEY:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper

get_reader()

@app.route("/ocr")
@require_api_key
def ocr():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing ?url="}), 400
    try:
        return jsonify({"lines": run_easyocr(url)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5005)