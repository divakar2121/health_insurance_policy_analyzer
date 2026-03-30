# Insurance Policy Analyzer

An AI-powered web application that analyzes insurance policy PDFs for IPC (Indian Penal Code) compliance issues and provides a legal AI advocate chatbot.

## Features

- **PDF Upload & Analysis**: Upload insurance policy PDFs and get IPC compliance analysis
- **AI Legal Advocate**: Chat with an expert AI that knows insurance law and IPC sections
- **PostgreSQL Storage**: All policies and queries stored in database
- **Risk Assessment**: Questions rated as High/Medium/Low risk

## Tech Stack

- **Backend**: Flask (Python)
- **Frontend**: HTML, Tailwind CSS, JavaScript
- **Database**: PostgreSQL
- **AI**: Google Gemini API

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set up Database
Run the SQL in `database.sql` on your PostgreSQL server

### 3. Configure Environment
Create `.env` file with:
```
GOOGLE_GEMINI_KEY=your_api_key
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

### 4. Run Servers
```bash
# Terminal 1 - Main App
python app.py

# Terminal 2 - AI Agent
python legal_agent.py
```

### 5. Open Browser
Go to http://localhost:5000

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment instructions on:
- Railway
- Render
- Fly.io
- PythonAnywhere

## IPC Sections Used

- **336**: Acts endangering life or personal safety
- **337**: Causing hurt by rash/negligent acts
- **304A**: Death by negligence
- **420**: Cheating and fraud

## License

MIT