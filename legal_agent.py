import os
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
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

# Initialize database tables
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS legal_queries (
            id SERIAL PRIMARY KEY,
            query_text TEXT NOT NULL,
            response_text TEXT NOT NULL,
            category VARCHAR(100),
            risk_level VARCHAR(20),
            ipc_sections TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    
    conn.commit()
    cur.close()
    conn.close()

init_db()

# Get all policies and questions for context
def get_user_context():
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Get recent policies with their questions
    cur.execute("""
        SELECT p.id, p.policy_type, p.extracted_text, p.created_at,
               q.question, q.ipc_sections, q.risk_level, q.category
        FROM policies p
        LEFT JOIN questions q ON p.id = q.policy_id
        ORDER BY p.created_at DESC
        LIMIT 5
    """)
    
    rows = cur.fetchall()
    cur.close()
    conn.close()
    
    if not rows:
        return "No policies analyzed yet. User has not uploaded any policy documents."
    
    context = "User's Analyzed Policies and Questions:\n\n"
    current_policy = None
    
    for row in rows:
        if current_policy != row['id']:
            current_policy = row['id']
            context += f"=== Policy #{row['id']} ({row['policy_type']}) ===\n"
            context += f"Extracted Text: {row['extracted_text'][:1000] if row['extracted_text'] else 'N/A'}\n"
            context += "Generated Questions:\n"
        
        if row['question']:
            context += f"- [{row['risk_level']}] {row['question']}\n"
            if row['ipc_sections']:
                try:
                    ipc = json.loads(row['ipc_sections'])
                    context += f"  IPC Sections: {ipc.get('sections', [])}\n"
                except:
                    pass
    
    return context

# LLM Response with context
def get_legal_response(query, user_context=""):
    api_key = os.getenv('GOOGLE_GEMINI_KEY')
    
    system_prompt = """You are a senior legal advocate specializing in Indian insurance law and the Indian Penal Code (IPC).

Your expertise includes:
- Insurance policies (health, life, motor, general)
- IPC sections relevant to insurance: 336 (rash/negligent acts), 337 (hurt by rash acts), 304A (death by negligence), 420 (cheating), 463 (forgery), 464 (document falsification)
- IRDAI regulations and guidelines
- Contract law and policy interpretation
- Identifying loopholes, ambiguities, and potential disputes
- Claim rejection scenarios and legal remedies

CRITICAL: You must reference the user's uploaded policies when answering. If there are existing policies and questions, cite them specifically in your response.

For each query:
1. Analyze the query against the user's policy context
2. Provide a thorough legal analysis with IPC references
3. Identify potential loopholes or disputes in their specific policies
4. Suggest protective measures or recommendations
5. Rate the risk level (low/medium/high)
6. Cite specific sections from their uploaded policies if relevant

Return ONLY valid JSON in this format:
{
    "answer": "Detailed legal response referencing user's policies...",
    "category": "coverage/fraud/negligence/exclusions/claims/documentation",
    "risk_level": "high/medium/low",
    "ipc_sections": ["336", "337", "304A", etc.],
    "recommendations": ["Recommendation 1", "Recommendation 2"],
    "policy_references": ["Reference to specific policy/question if applicable"]
}"""

    prompt = f"{system_prompt}\n\n### USER'S POLICY DATA ###\n{user_context}\n\n### USER QUERY ###\n{query}"

    if not api_key:
        return {
            "answer": "API key not configured. Please set GOOGLE_GEMINI_KEY in .env file.",
            "category": "system",
            "risk_level": "low",
            "ipc_sections": [],
            "recommendations": [],
            "policy_references": []
        }

    try:
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}",
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            text_response = result['candidates'][0]['content']['parts'][0]['text']
            json_start = text_response.find('{')
            json_end = text_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                return json.loads(text_response[json_start:json_end])
        
        return {"error": "Failed to get response from AI"}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def index():
    return jsonify({
        "name": "Insurance Legal AI Agent",
        "description": "Expert advocate for insurance law - connected to user policies database",
        "endpoints": {
            "POST /api/query": "Submit a legal query (uses policy context)",
            "GET /api/queries": "Get all saved queries",
            "GET /api/context": "Get current policy context",
            "GET /api/query/<id>": "Get specific query by ID",
            "GET /health": "Health check"
        }
    })

@app.route('/api/query', methods=['POST'])
def submit_query():
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Query is required'}), 400
    
    query = data['query']
    
    # Get user's policy context from database
    user_context = get_user_context()
    
    # Get AI response with context
    response = get_legal_response(query, user_context)
    
    if 'error' in response:
        return jsonify(response), 500
    
    # Save to database
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO legal_queries (query_text, response_text, category, risk_level, ipc_sections)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id, created_at
    """, (
        query,
        json.dumps(response),
        response.get('category', 'general'),
        response.get('risk_level', 'low'),
        json.dumps(response.get('ipc_sections', []))
    ))
    
    result = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({
        'id': result['id'],
        'query': query,
        'response': response,
        'context_used': True,
        'created_at': result['created_at'].isoformat()
    })

@app.route('/api/context', methods=['GET'])
def get_context():
    try:
        context = get_user_context()
        return jsonify({
            'context': context,
            'has_policies': 'Policy #' in context
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/queries', methods=['GET'])
def get_all_queries():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT id, query_text, category, risk_level, ipc_sections, created_at 
            FROM legal_queries 
            ORDER BY created_at DESC
        """)
        queries = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify(queries)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/query/<int:query_id>', methods=['GET'])
def get_query(query_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM legal_queries WHERE id = %s", (query_id,))
        query = cur.fetchone()
        cur.close()
        conn.close()
        
        if not query:
            return jsonify({'error': 'Query not found'}), 404
        
        return jsonify(query)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    return jsonify({'status': 'AI Agent is running!', 'db_connected': True})

if __name__ == '__main__':
    print("=" * 50)
    print("Insurance Legal AI Agent")
    print("Expert advocate - connected to policy database")
    print("=" * 50)
    app.run(host='0.0.0.0', port=5001, debug=False)