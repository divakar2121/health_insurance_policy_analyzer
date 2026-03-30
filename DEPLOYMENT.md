# Deployment Guide for Insurance Policy Analyzer

## Option 1: Railway (Recommended - Free Tier Available)

### Steps:
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub"
4. Select your repo or push this project to GitHub first
5. Add Environment Variables:
   - `DATABASE_URL` → Supabase PostgreSQL connection string
   - `GOOGLE_GEMINI_KEY` → Your Gemini API key
6. Railway will auto-detect Python/Flask
7. Set start command: `gunicorn app:app --bind 0.0.0.0:8000`

### For PostgreSQL (use Supabase):
1. Go to https://supabase.com
2. Create new project
3. Get connection string from Settings → Database
4. Run database.sql in Supabase SQL Editor

---

## Option 2: Render (Free Tier Available)

### Steps:
1. Go to https://render.com
2. Sign up with GitHub
3. Click "New" → "Web Service"
4. Connect your GitHub repo
5. Settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app --bind 0.0.0.0:8000`
6. Add Environment Variables (same as above)
7. Deploy!

---

## Option 3: Fly.io (Free Tier Available)

### Steps:
1. Install Fly CLI: `curl -L https://fly.io/install.sh | sh`
2. `fly auth login`
3. `fly launch` (inside project folder)
4. `fly secrets set GOOGLE_GEMINI_KEY=your_key`
5. `fly secrets set DATABASE_URL=your_postgres_url`
6. `fly deploy`

---

## Option 4: PythonAnywhere (Free Tier Available)

### Steps:
1. Go to https://pythonanywhere.com
2. Create account
3. Open Bash console
4. `git clone your_repo`
5. `cd your_project`
6. `pip install -r requirements.txt`
7. Go to Web tab → Create new web app
8. Set WSGI file to point to app.py
9. Configure static files and environment variables

---

## Setting up Supabase Database

1. Create account at https://supabase.com
2. Create new project
3. In SQL Editor, run the contents of database.sql
4. Get connection string from Settings → Connection Pooling
5. Format: `postgresql://postgres:[PASSWORD]@aws-[REGION].pooler.supabase.com:6543/postgres`

---

## Pushing to GitHub

```bash
cd /home/deva/ai_test/rag_bot/insurance-ai-webapp
git init
git add .
git commit -m "Insurance Policy Analyzer - Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/insurance-policy-analyzer.git
git push -u origin main
```

---

## Important: Before Deployment

1. Remove `.env` file from git tracking (add to .gitignore)
2. Create `.env.example` with placeholder values
3. Update app.py to handle missing environment variables gracefully

---

## Files to push to GitHub:
- app.py
- legal_agent.py
- index.html
- requirements.txt
- database.sql
- .env.example
- run_commands.txt (optional)
- README.md (optional)