import os
import logging
import time
from functools import wraps
from flask import Flask, request, jsonify
from ocr_core import run_easyocr, get_reader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

app = Flask(__name__)

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise RuntimeError("API_KEY environment variable is not set")

def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if request.headers.get("X-API-Key") != API_KEY:
            log.warning("Unauthorized request from %s", request.remote_addr)
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    return wrapper

log.info("Loading EasyOCR model...")
get_reader()
log.info("Ready.")

@app.route("/ocr")
@require_api_key
def ocr():
    url = request.args.get("url")
    if not url:
        return jsonify({"error": "missing ?url="}), 400

    log.info("Request from %s | url=%s", request.remote_addr, url)
    start = time.monotonic()
    try:
        lines = run_easyocr(url)
        elapsed = time.monotonic() - start
        log.info("Done in %.2fs | lines=%s", elapsed, lines)
        return jsonify({"lines": lines})
    except Exception as e:
        elapsed = time.monotonic() - start
        log.error("Failed in %.2fs | url=%s | error=%s", elapsed, url, e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)