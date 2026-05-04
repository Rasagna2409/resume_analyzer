# 🚀 Resume Analyzer — AI-Powered

Full-stack resume analyzer with spaCy NLP, ATS scoring, JD matching, Claude AI coaching, and SQLite history.

## 📁 Project Structure

resume_analyzer/
├── app.py               ← Flask backend (API + all logic)
├── requirements.txt     ← Python dependencies
├── .env                 ← Your Anthropic API key (don't commit this!)
├── setup.bat            ← One-click setup for Windows
├── setup.sh             ← One-click setup for Mac/Linux
├── resume_analyzer.db   ← SQLite database (auto-created on first run)
├── templates/
│   └── index.html       ← React SPA frontend
└── static/
    └── style.css        ← Full stylesheet


## ⚡ Quick Start

### Step 1 — Get your Anthropic API Key
Go to https://console.anthropic.com → create account → copy your API key

### Step 2 — Add it to .env
Open `.env` and replace `your_api_key_here`:

ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxx

### Step 3 — Run setup (one time only)

**Windows:**

setup.bat


**Mac / Linux:**

chmod +x setup.sh
./setup.sh


### Step 4 — Start the server

# Activate virtual environment first
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# Run
python app.py


### Step 5 — Open in browser

http://localhost:5000


## 🔧 Manual Setup (if setup scripts don't work)


# 1. Create and activate virtual environment
python -m venv venv
source venv/bin/activate          # Mac/Linux
# OR: venv\Scripts\activate       # Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Add API key to .env
echo "ANTHROPIC_API_KEY=your_key_here" > .env

# 5. Run
python app.py

## 🌐 API Endpoints

| Method | Endpoint        | Description                     |
|--------|-----------------|---------------------------------|
| POST   | /api/analyze    | Main analysis (upload PDF here) |
| GET    | /api/history    | Last 20 analyses from SQLite    |
| GET    | /api/stats      | Aggregate dashboard stats       |
| GET    | /api/roles      | All supported job roles         |
| GET    | /api/skills     | Full skills database list       |

## 🎯 Features

- **spaCy NLP** — bigram/trigram extraction, synonym normalization (ml→machine learning, etc.)
- **ATS Scoring** — 9-point weighted checklist (contact, sections, bullets, metrics, verbs...)
- **Role Matching** — 8 roles, weighted required (70%) + preferred (30%) scoring
- **JD Parsing** — paste any job description, Claude extracts required skills dynamically
- **AI Coaching** — Claude generates profile summary, gaps, quick wins, learning roadmap
- **Keyword Density** — shows how often each skill appears in your resume
- **SQLite History** — every analysis auto-saved, viewable in History tab
- **Dashboard** — aggregate stats across all scans

## 🚀 Deploy to Render (Free)

1. Push to GitHub
2. Go to https://render.com → New Web Service
3. Connect your repo
4. Set environment variable: `ANTHROPIC_API_KEY = your_key`
5. Build command: `pip install -r requirements.txt && python -m spacy download en_core_web_sm`
6. Start command: `python app.py`

## 🎤 Interview Description

> "I built an AI-powered Resume Analyzer using Flask and spaCy for NLP-based skill extraction with synonym normalization. It calculates a 9-point ATS score, supports dynamic job description parsing where Claude AI extracts required skills from any job posting, and provides personalized coaching including a learning roadmap. All analyses are persisted in SQLite with a dashboard for aggregate analytics. The frontend is a React SPA communicating with the Flask REST API."
