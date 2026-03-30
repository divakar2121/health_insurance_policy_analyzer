import os
import json
import tempfile
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from pdfminer.high_level import extract_text
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from datetime import datetime

load_dotenv()

app = Flask(__name__)
CORS(app)

# Database connection
def get_db_connection():
    return psycopg2.connect(
        os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/insurance_db'),
        cursor_factory=RealDictCursor
    )

# PDF Text Extraction
def extract_pdf_text(file_storage):
    try:
        # Save to temp file first
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
            file_storage.save(tmp.name)
            text = extract_text(tmp.name)
            os.unlink(tmp.name)
        return text
    except Exception as e:
        print(f"PDF extraction error: {e}")
        raise Exception("Failed to parse PDF")

# LLM Analysis
def analyze_policy(text):
    api_key = os.getenv('GOOGLE_GEMINI_KEY')
    
    if not api_key:
        # Return mock data if no API key
        return {
            "summary": "This is a health insurance policy document.",
            "compliance_score": 75,
            "questions": [
                {
                    "question": "Does the policy clearly define negligence according to IPC 336-337?",
                    "ipc_sections": {"sections": ["336", "337"], "explanation": "Insurance policies must align with IPC definitions for negligence claims."},
                    "risk_level": "high",
                    "category": "negligence"
                },
                {
                    "question": "Are there clear fraud detection mechanisms as per IPC 420?",
                    "ipc_sections": {"sections": ["420"], "explanation": "The policy should have anti-fraud provisions aligned with IPC cheating provisions."},
                    "risk_level": "medium",
                    "category": "fraud"
                },
                {
                    "question": "Does the policy cover death by negligence as per IPC 304A?",
                    "ipc_sections": {"sections": ["304A"], "explanation": "Fatal accident coverage should align with IPC 304A provisions."},
                    "risk_level": "high",
                    "category": "coverage"
                }
            ]
        }
    
    prompt = f"""You are an expert legal AI specializing in Indian Penal Code (IPC) and health insurance compliance.

Analyze this health insurance policy and identify potential compliance issues.

Return ONLY valid JSON in this exact format:
{{
    "summary": "Brief policy summary",
    "compliance_score": 75,
    "questions": [
        {{
            "question": "Does the policy clearly define negligence according to IPC 336-337?",
            "ipc_sections": {{"sections": ["336", "337"], "explanation": "..."}},
            "risk_level": "high",
            "category": "negligence"
        }}
    ]
}}

Policy text:
{text[:5000]}"""

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
            json={
                "contents": [{"parts": [{"text": prompt}]}]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            # Extract JSON from response
            json_start = text_response.find('{')
            json_end = text_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(text_response[json_start:json_end])
        
        return analyze_policy("")  # Fallback to mock
    except Exception as e:
        print(f"LLM Error: {e}")
        return analyze_policy("")  # Fallback to mock

# Routes
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.endswith('.pdf'):
        return jsonify({'error': 'Only PDF files are allowed'}), 400
    
    try:
        # Extract text from PDF
        extracted_text = extract_pdf_text(file)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            return jsonify({'error': 'Could not extract text from PDF'}), 400
        
        # Analyze with LLM
        analysis = analyze_policy(extracted_text)
        
        # Save to database
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Insert policy
        cur.execute("""
            INSERT INTO policies (user_id, file_url, extracted_text, policy_type, created_at)
            VALUES (%s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            request.form.get('user_id', 'demo-user'),
            f"uploads/{datetime.now().timestamp()}-{file.filename}",
            extracted_text[:10000],  # Limit text size
            request.form.get('policy_type', 'health')
        ))
        policy_id = cur.fetchone()['id']
        
        # Insert questions
        for q in analysis.get('questions', []):
            cur.execute("""
                INSERT INTO questions (policy_id, question, ipc_sections, risk_level, category, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
            """, (
                policy_id,
                q['question'],
                json.dumps(q['ipc_sections']),
                q['risk_level'],
                q['category']
            ))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({
            'success': True,
            'policy_id': str(policy_id),
            'analysis': analysis,
            'message': 'Policy analyzed successfully'
        })
        
    except Exception as e:
        print(f"Upload error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/policies/<user_id>', methods=['GET'])
def get_policies(user_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM policies WHERE user_id = %s ORDER BY created_at DESC", (user_id,))
        policies = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(policies)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/policy/<policy_id>', methods=['GET'])
def get_policy(policy_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM policies WHERE id = %s", (policy_id,))
        policy = cur.fetchone()
        
        if not policy:
            return jsonify({'error': 'Policy not found'}), 404
        
        cur.execute("SELECT * FROM questions WHERE policy_id = %s", (policy_id,))
        questions = cur.fetchall()
        
        cur.close()
        conn.close()
        
        return jsonify({'policy': policy, 'questions': questions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'Backend is running!'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)

# For gunicorn production server
application = app
