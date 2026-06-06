import os
import requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Dynamically fall back to localhost if running outside Docker
ANALYZER_HOST = os.getenv("ANALYZER_HOST", "localhost")
ANONYMIZER_HOST = os.getenv("ANONYMIZER_HOST", "localhost")

# Note: Within the internal Docker network, containers communicate via internal target ports (3000)
ANALYZER_URL = f"http://{ANALYZER_HOST}:3000/analyze"
ANONYMIZER_URL = f"http://{ANONYMIZER_HOST}:3000/anonymize"

@app.route("/scrub", methods=["POST"])
def scrub_text():
    data = request.json or {}
    raw_text = data.get("text", "")
    
    if not raw_text:
        return jsonify({"error": "No text provided"}), 400

    try:
        # 1. Hit Presidio Analyzer
        analyzer_res = requests.post(ANALYZER_URL, json={"text": raw_text, "language": "en"})
        analyzer_res.raise_for_status()
        
        # 2. Hit Presidio Anonymizer
        anonymizer_res = requests.post(ANONYMIZER_URL, json={
            "text": raw_text,
            "analyzer_results": analyzer_res.json()
        })
        anonymizer_res.raise_for_status()
        
        return jsonify({"safe_text": anonymizer_res.json().get("text")})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)