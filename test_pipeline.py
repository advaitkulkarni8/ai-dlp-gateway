import os
import sys
import requests
from pypdf import PdfReader
import docx2txt

# Local endpoints exposed by our Docker containers
ANALYZER_URL = "http://localhost:5001/analyze"
ANONYMIZER_URL = "http://localhost:5002/anonymize"

def extract_text_from_file(file_path):
    """Simulates local text extraction based on file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    
    if ext == ".pdf":
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    
    elif ext == ".docx":
        return docx2txt.process(file_path)
    
    elif ext in [".txt", ".csv"]:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def clean_document(text):
    """Passes raw text through the local Presidio pipeline."""
    # Step 1: Analyze text to find PII locations
    analyzer_payload = {
        "text": text,
        "language": "en",
        "score_threshold": 0.5 # Confidence threshold (0.0 to 1.0)
    }
    
    analyzer_response = requests.post(ANALYZER_URL, json=analyzer_payload)
    analyzer_response.raise_for_status()
    analysis_results = analyzer_response.json()
    
    # Step 2: Pass text and analysis results to anonymize them
    anonymizer_payload = {
        "text": text,
        "analyzer_results": analysis_results
    }
    
    anonymizer_response = requests.post(ANONYMIZER_URL, json=anonymizer_payload)
    anonymizer_response.raise_for_status()
    return anonymizer_response.json().get("text")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_pipeline.py <path_to_local_file>")
        sys.exit(1)
        
    target_file = sys.argv[1]
    
    if not os.path.exists(target_file):
        print(f"Error: File '{target_file}' not found.")
        sys.exit(1)
        
    print(f"--- Processing: {target_file} ---")
    
    # 1. Extract text from your desktop file
    raw_text = extract_text_from_file(target_file)
    print(f"\n[RAW EXTRACTED TEXT]:\n{raw_text}")
    print("-" * 40)
    
    # 2. Scrub PII via Presidio HTTP API
    try:
        clean_text = clean_document(raw_text)
        print(f"\n[SAFE SCRUBBED TEXT TO SEND TO GENAI]:\n{clean_text}")
    except Exception as e:
        print(f"Pipeline error: {e}. Ensure your Docker containers are running.")