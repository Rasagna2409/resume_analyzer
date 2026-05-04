"""
Resume Analyzer - Full Backend
Features: spaCy NLP, ATS scoring, JD matching, SQLite history,
          Free AI (Groq/Gemini/Anthropic fallback chain), keyword density, REST API
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import PyPDF2
import re
import sqlite3
import json
import os
import datetime
import requests
import spacy

# Auto-load .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ── App Setup ─────────────────────────────────────────────────────────────────

app = Flask(__name__)
CORS(app)

# Load spaCy model (run: python -m spacy download en_core_web_sm)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    nlp = None
    print("⚠️  spaCy model not found. Run: python -m spacy download en_core_web_sm")

# ── AI Provider Keys (set whichever you have in .env) ────────────────────────
GROQ_API_KEY      = os.environ.get("GROQ_API_KEY", "")
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")

DB_PATH = "resume_analyzer.db"


# ── Skills Database ────────────────────────────────────────────────────────────

SKILLS_DB = [
    # Languages
    "python", "java", "c++", "c", "c#", "javascript", "typescript",
    "go", "golang", "rust", "kotlin", "swift", "scala", "r", "matlab",
    "php", "ruby", "perl", "bash", "shell", "powershell", "dart",

    # Web Frontend
    "html", "css", "react", "angular", "vue", "next.js", "nuxt.js",
    "svelte", "tailwind", "sass", "webpack", "vite", "redux", "graphql",
    "jquery", "bootstrap", "material ui",

    # Web Backend
    "node.js", "flask", "django", "fastapi", "spring boot", "express",
    "laravel", "rails", "asp.net", "nestjs", "rest api", "grpc", "websocket",

    # Databases
    "sql", "mysql", "postgresql", "sqlite", "mongodb", "redis",
    "elasticsearch", "cassandra", "dynamodb", "firebase", "oracle",
    "mariadb", "neo4j", "influxdb",

    # ML / AI / Data
    "machine learning", "deep learning", "data science", "nlp",
    "computer vision", "tensorflow", "pytorch", "keras", "scikit-learn",
    "pandas", "numpy", "matplotlib", "seaborn", "scipy", "opencv",
    "hugging face", "langchain", "llm", "generative ai", "rag",
    "xgboost", "lightgbm", "spark", "hadoop", "airflow", "dbt",

    # DevOps / Cloud
    "docker", "kubernetes", "aws", "azure", "gcp", "terraform",
    "ansible", "jenkins", "github actions", "gitlab ci", "ci/cd",
    "linux", "nginx", "apache", "prometheus", "grafana", "elk stack",

    # Tools / Practices
    "git", "agile", "scrum", "jira", "system design", "microservices",
    "dsa", "data structures", "algorithms", "oop", "solid", "tdd",
    "api design", "data engineering", "data analysis",

    # Mobile
    "android", "ios", "react native", "flutter", "xamarin",

    # Security
    "cybersecurity", "penetration testing", "oauth", "jwt",

    # Other
    "excel", "tableau", "power bi", "figma", "photoshop"
]

SKILL_SYNONYMS = {
    "ml": "machine learning",
    "dl": "deep learning",
    "ai": "generative ai",
    "js": "javascript",
    "ts": "typescript",
    "py": "python",
    "k8s": "kubernetes",
    "tf": "tensorflow",
    "nlp": "nlp",
    "cv": "computer vision",
    "dsa": "dsa",
    "oop": "oop",
    "ci": "ci/cd",
    "cd": "ci/cd",
    "gpt": "llm",
    "chatgpt": "llm",
    "postgres": "postgresql",
    "mongo": "mongodb",
    "node": "node.js",
    "react.js": "react",
    "reactjs": "react",
    "vuejs": "vue",
    "vue.js": "vue",
    "nextjs": "next.js",
    "sklearn": "scikit-learn",
    "hf": "hugging face",
    "bert": "hugging face",
    "springboot": "spring boot",
    "expressjs": "express",
    "fast api": "fastapi",
    "gcp": "gcp",
    "aws": "aws",
    "azure": "azure"
}


# ── Job Roles ─────────────────────────────────────────────────────────────────

JOB_ROLES = {
    "sde": {
        "title": "Software Development Engineer",
        "required": ["python", "java", "dsa", "sql", "javascript", "git", "rest api"],
        "preferred": ["system design", "docker", "aws", "typescript", "microservices"],
        "description": "Backend/fullstack engineering roles at product companies"
    },
    "data_scientist": {
        "title": "Data Scientist",
        "required": ["python", "machine learning", "sql", "pandas", "numpy"],
        "preferred": ["deep learning", "tensorflow", "pytorch", "data science", "scikit-learn", "nlp"],
        "description": "ML modeling, statistical analysis, experiment design"
    },
    "frontend": {
        "title": "Frontend Developer",
        "required": ["html", "css", "javascript", "react", "git"],
        "preferred": ["typescript", "next.js", "tailwind", "redux", "webpack", "rest api"],
        "description": "UI development, web performance, component architecture"
    },
    "backend": {
        "title": "Backend Developer",
        "required": ["python", "sql", "rest api", "git", "docker"],
        "preferred": ["flask", "django", "fastapi", "postgresql", "redis", "aws", "microservices"],
        "description": "API design, database architecture, server-side logic"
    },
    "devops": {
        "title": "DevOps / SRE Engineer",
        "required": ["linux", "docker", "kubernetes", "git", "aws", "ci/cd"],
        "preferred": ["terraform", "ansible", "prometheus", "grafana", "azure", "gcp", "python"],
        "description": "Infrastructure, automation, reliability engineering"
    },
    "ml_engineer": {
        "title": "ML Engineer",
        "required": ["python", "machine learning", "deep learning", "pytorch", "tensorflow", "docker"],
        "preferred": ["mlops", "kubernetes", "spark", "aws", "airflow", "rag", "llm"],
        "description": "ML pipeline, model deployment, MLOps, LLM applications"
    },
    "data_engineer": {
        "title": "Data Engineer",
        "required": ["python", "sql", "spark", "airflow", "aws"],
        "preferred": ["dbt", "kafka", "postgresql", "mongodb", "docker", "scala", "data engineering"],
        "description": "Data pipelines, ETL, warehouse architecture"
    },
    "fullstack": {
        "title": "Full Stack Developer",
        "required": ["javascript", "react", "node.js", "sql", "rest api", "git", "css"],
        "preferred": ["typescript", "docker", "postgresql", "mongodb", "aws", "next.js"],
        "description": "End-to-end web application development"
    }
}

# Action verbs that indicate strong resume writing
ACTION_VERBS = [
    "developed", "built", "designed", "implemented", "led", "improved",
    "created", "managed", "optimized", "deployed", "architected", "engineered",
    "automated", "reduced", "increased", "delivered", "launched", "migrated",
    "integrated", "collaborated", "mentored", "researched", "analyzed"
]


# ── Database ──────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at  TEXT NOT NULL,
            role        TEXT NOT NULL,
            role_title  TEXT NOT NULL,
            match_score REAL NOT NULL,
            ats_score   REAL NOT NULL,
            skills_found TEXT NOT NULL,
            missing_required TEXT NOT NULL,
            file_name   TEXT
        );

        CREATE TABLE IF NOT EXISTS jd_analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            analysis_id INTEGER REFERENCES analyses(id),
            jd_snippet  TEXT,
            jd_score    REAL,
            jd_matched  TEXT,
            jd_missing  TEXT
        );
    """)
    conn.commit()
    conn.close()


def save_analysis(data: dict) -> int:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        INSERT INTO analyses
            (created_at, role, role_title, match_score, ats_score,
             skills_found, missing_required, file_name)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.datetime.utcnow().isoformat(),
        data["role"],
        data["role_title"],
        data["match_score"],
        data["ats_score"],
        json.dumps(data["skills_found"]),
        json.dumps(data["missing_required"]),
        data.get("file_name", "")
    ))
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_history(limit: int = 10) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    rows = c.execute("""
        SELECT id, created_at, role_title, match_score, ats_score,
               skills_found, missing_required, file_name
        FROM analyses
        ORDER BY id DESC LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats() -> dict:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    total   = c.execute("SELECT COUNT(*) FROM analyses").fetchone()[0]
    avg_match = c.execute("SELECT AVG(match_score) FROM analyses").fetchone()[0] or 0
    avg_ats   = c.execute("SELECT AVG(ats_score)   FROM analyses").fetchone()[0] or 0
    top_role  = c.execute("""
        SELECT role_title, COUNT(*) as cnt FROM analyses
        GROUP BY role_title ORDER BY cnt DESC LIMIT 1
    """).fetchone()
    conn.close()
    return {
        "total_analyses": total,
        "avg_match_score": round(avg_match, 1),
        "avg_ats_score":   round(avg_ats, 1),
        "most_analyzed_role": top_role[0] if top_role else "—"
    }


# ── NLP: Skill Extraction ─────────────────────────────────────────────────────

def normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[_\-]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def extract_skills(text: str) -> list[str]:
    text_norm = normalize(text)

    # Apply synonym normalization
    for alias, canonical in SKILL_SYNONYMS.items():
        text_norm = re.sub(r'\b' + re.escape(alias) + r'\b', canonical, text_norm)

    found = set()

    if nlp:
        doc = nlp(text_norm)
        tokens = [t.text for t in doc]
        bigrams  = [tokens[i] + " " + tokens[i+1] for i in range(len(tokens)-1)]
        trigrams = [tokens[i] + " " + tokens[i+1] + " " + tokens[i+2] for i in range(len(tokens)-2)]
        candidates = set(tokens + bigrams + trigrams)
    else:
        # Fallback: regex n-grams
        words = text_norm.split()
        bigrams  = [words[i] + " " + words[i+1] for i in range(len(words)-1)]
        trigrams = [words[i] + " " + words[i+1] + " " + words[i+2] for i in range(len(words)-2)]
        candidates = set(words + bigrams + trigrams)

    for skill in SKILLS_DB:
        if skill in candidates:
            found.add(skill)
        elif re.search(r'\b' + re.escape(skill) + r'\b', text_norm):
            found.add(skill)

    return sorted(found)


def extract_skills_from_jd(jd_text: str) -> list[str]:
    """Extract skills specifically from a job description."""
    return extract_skills(jd_text)


# ── ATS Scoring ───────────────────────────────────────────────────────────────

def calculate_ats_score(text: str, skills: list[str]) -> dict:
    checks = {}
    word_count = len(text.split())

    # 1. Word count / length
    if 300 <= word_count <= 1000:
        checks["length"] = {"pass": True,  "label": "Ideal length (300–1000 words)",     "weight": 10}
    elif word_count < 300:
        checks["length"] = {"pass": False, "label": "Too short — add more detail",        "weight": 10}
    else:
        checks["length"] = {"pass": False, "label": "Too long — trim to 1–2 pages",       "weight": 10}

    # 2. Email
    checks["email"] = {
        "pass": bool(re.search(r'[\w.+-]+@[\w-]+\.\w+', text)),
        "label": "Email address present", "weight": 10
    }

    # 3. Phone
    checks["phone"] = {
        "pass": bool(re.search(r'[\+\(]?\d[\d\s\-\(\)]{8,}\d', text)),
        "label": "Phone number present", "weight": 8
    }

    # 4. LinkedIn / GitHub
    checks["links"] = {
        "pass": bool(re.search(r'linkedin\.com|github\.com', text, re.I)),
        "label": "LinkedIn or GitHub profile", "weight": 7
    }

    # 5. Sections
    section_hits = sum(1 for s in ["experience", "education", "projects", "skills", "certifications"]
                       if re.search(r'\b' + s + r'\b', text, re.I))
    checks["sections"] = {
        "pass": section_hits >= 3,
        "label": f"Key sections present ({section_hits}/5 found)", "weight": 15
    }

    # 6. Quantified achievements
    checks["numbers"] = {
        "pass": bool(re.search(
            r'\d+\s*[%xX\+]|\d+\s*(users?|clients?|projects?|years?|months?|k\b|million)',
            text, re.I)),
        "label": "Quantified achievements (numbers/metrics)", "weight": 15
    }

    # 7. Action verbs
    verb_hits = sum(1 for v in ACTION_VERBS if re.search(r'\b' + v + r'\b', text, re.I))
    checks["action_verbs"] = {
        "pass": verb_hits >= 5,
        "label": f"Strong action verbs ({verb_hits} found, need 5+)", "weight": 10
    }

    # 8. Bullet points
    checks["bullets"] = {
        "pass": bool(re.search(r'[•\-\*]\s+\w', text)),
        "label": "Bullet point formatting", "weight": 10
    }

    # 9. Skills density
    checks["skill_density"] = {
        "pass": len(skills) >= 8,
        "label": f"Sufficient skill keywords ({len(skills)} found, need 8+)", "weight": 15
    }

    # Compute weighted score
    total_weight = sum(c["weight"] for c in checks.values())
    earned       = sum(c["weight"] for c in checks.values() if c["pass"])
    score        = round((earned / total_weight) * 100)

    return {"score": score, "checks": checks, "word_count": word_count}


# ── Match Calculation ─────────────────────────────────────────────────────────

def calculate_match(resume_skills: list[str], role_key: str, custom_role: dict = None) -> dict:
    if custom_role:
        role_data = custom_role
    else:
        role_data = JOB_ROLES.get(role_key, JOB_ROLES["sde"])

    required  = role_data.get("required", [])
    preferred = role_data.get("preferred", [])
    rs_lower  = [s.lower() for s in resume_skills]

    matched_req  = [s for s in required  if s in rs_lower]
    missing_req  = [s for s in required  if s not in rs_lower]
    matched_pref = [s for s in preferred if s in rs_lower]
    missing_pref = [s for s in preferred if s not in rs_lower]

    req_score  = (len(matched_req)  / len(required))  * 70 if required  else 0
    pref_score = (len(matched_pref) / len(preferred)) * 30 if preferred else 0
    total      = round(req_score + pref_score, 1)

    return {
        "score":           total,
        "matched_required":  matched_req,
        "missing_required":  missing_req,
        "matched_preferred": matched_pref,
        "missing_preferred": missing_pref
    }


# ── Keyword Density ───────────────────────────────────────────────────────────

def keyword_density(text: str, skills: list[str]) -> dict:
    text_lower = text.lower()
    density = {}
    for skill in skills:
        count = len(re.findall(r'\b' + re.escape(skill) + r'\b', text_lower))
        if count:
            density[skill] = count
    return dict(sorted(density.items(), key=lambda x: -x[1]))


# ── AI Provider: Free Fallback Chain ─────────────────────────────────────────
# Priority: Groq (free) → Gemini (free) → Anthropic (paid)
# Set whichever key you have in .env — the rest are skipped automatically.

def _build_prompt(role_title, resume_text, skills, missing, match_score, ats_score):
    return f"""You are a senior tech recruiter and resume coach. Analyze this resume for a {role_title} position.

Resume (first 2000 chars):
{resume_text[:2000]}

Analysis:
- Skills found: {', '.join(skills[:20])}
- Missing required skills: {', '.join(missing)}
- Role match: {match_score}%  |  ATS score: {ats_score}%

Return ONLY valid JSON, no markdown, no backticks:
{{
  "profile_summary": "2-3 sentence honest candidate assessment",
  "strengths": ["up to 3 genuine strengths based on skills found"],
  "critical_gaps": ["top 3 missing skills with brief why-it-matters"],
  "quick_wins": ["3 specific resume improvements doable this week"],
  "learning_roadmap": [
    {{"skill": "skill name", "resource": "specific free course/resource", "timeline": "e.g. 2 weeks"}}
  ],
  "interview_talking_points": ["2 skills that are strong differentiators for this role"],
  "readiness_verdict": "one of: Not Ready | Needs Work | Almost There | Strong Candidate"
}}"""


def _parse_json(raw: str) -> dict:
    raw = re.sub(r"^```json\s*|\s*```$", "", raw.strip(), flags=re.MULTILINE)
    return json.loads(raw)


def _call_groq(prompt: str) -> dict:
    """Free — sign up at console.groq.com, set GROQ_API_KEY in .env"""
    resp = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "llama-3.1-8b-instant",   # fast, free
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 1200,
            "temperature": 0.3
        },
        timeout=30
    )
    resp.raise_for_status()
    return _parse_json(resp.json()["choices"][0]["message"]["content"])


def _call_gemini(prompt: str) -> dict:
    """Free — sign up at aistudio.google.com, set GEMINI_API_KEY in .env"""
    resp = requests.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}",
        headers={"Content-Type": "application/json"},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30
    )
    resp.raise_for_status()
    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    return _parse_json(text)


def _call_anthropic(prompt: str) -> dict:
    """Paid — set ANTHROPIC_API_KEY in .env"""
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        },
        json={
            "model": "claude-haiku-4-5-20251001",
            "max_tokens": 1200,
            "messages": [{"role": "user", "content": prompt}]
        },
        timeout=30
    )
    resp.raise_for_status()
    return _parse_json(resp.json()["content"][0]["text"])


def generate_ai_suggestions(resume_text: str, role_key: str,
                             skills: list[str], missing: list[str],
                             ats_score: int, match_score: float) -> dict:
    role   = JOB_ROLES.get(role_key, JOB_ROLES["sde"])
    prompt = _build_prompt(role["title"], resume_text, skills, missing, match_score, ats_score)

    # Try each provider in order — first key that works wins
    providers = []
    if GROQ_API_KEY:
        providers.append(("Groq",      _call_groq))
    if GEMINI_API_KEY:
        providers.append(("Gemini",    _call_gemini))
    if ANTHROPIC_API_KEY:
        providers.append(("Anthropic", _call_anthropic))

    last_error = "No AI API key set."
    for name, fn in providers:
        try:
            result = fn(prompt)
            result["_provider"] = name   # lets frontend show which AI was used
            return result
        except Exception as e:
            last_error = f"{name} failed: {e}"
            continue

    # All providers failed — return rule-based fallback
    return {
        "profile_summary": (
            f"Candidate has {len(skills)} relevant skills including "
            f"{', '.join(skills[:3]) or 'none detected'}. "
            f"Role match is {match_score}% with {len(missing)} required skills missing."
        ),
        "strengths":    [f"Has {s}" for s in skills[:3]],
        "critical_gaps": missing[:3],
        "quick_wins": [
            f"Add '{missing[0]}' to your skills section" if missing else "Quantify your achievements with numbers",
            "Add LinkedIn and GitHub URLs to the top of your resume",
            "Include metrics: users impacted, % improvement, team size"
        ],
        "learning_roadmap": [
            {"skill": s, "resource": "Search on freeCodeCamp or YouTube", "timeline": "2-4 weeks"}
            for s in missing[:3]
        ],
        "interview_talking_points": skills[:2],
        "readiness_verdict": (
            "Strong Candidate" if match_score >= 70 else
            "Almost There"     if match_score >= 50 else
            "Needs Work"       if match_score >= 30 else
            "Not Ready"
        ),
        "_provider": f"Rule-based fallback ({last_error})"
    }


# ── PDF Extraction ─────────────────────────────────────────────────────────────

def extract_text_from_pdf(file) -> str:
    try:
        reader = PyPDF2.PdfReader(file)
        pages = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        return "\n".join(pages)
    except Exception as e:
        return ""


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/analyze", methods=["POST"])
def analyze():
    """Main analysis endpoint. Accepts multipart form data."""
    file     = request.files.get("resume")
    role_key = request.form.get("job_role", "sde")
    job_desc = request.form.get("job_desc", "").strip()
    use_ai   = request.form.get("use_ai", "true").lower() == "true"

    # Validate
    if not file or file.filename == "":
        return jsonify({"error": "No file uploaded"}), 400
    if not file.filename.lower().endswith(".pdf"):
        return jsonify({"error": "Only PDF files are supported"}), 400
    if role_key not in JOB_ROLES:
        return jsonify({"error": "Invalid job role"}), 400

    # Extract text
    resume_text = extract_text_from_pdf(file)
    if len(resume_text.strip()) < 100:
        return jsonify({"error": "Could not extract text from PDF. Use a text-based (non-scanned) PDF."}), 422

    # Skill extraction
    skills   = extract_skills(resume_text)
    density  = keyword_density(resume_text, skills)

    # ATS scoring
    ats      = calculate_ats_score(resume_text, skills)

    # Role match
    match    = calculate_match(skills, role_key)

    # JD matching (if provided)
    jd_result = None
    if job_desc:
        jd_skills  = extract_skills_from_jd(job_desc)
        jd_match   = calculate_match(skills, role_key, {
            "required": jd_skills, "preferred": []
        })
        jd_result = {
            "jd_skills":   jd_skills,
            "jd_score":    jd_match["score"],
            "jd_matched":  jd_match["matched_required"],
            "jd_missing":  jd_match["missing_required"]
        }

    # AI suggestions
    ai_result = None
    if use_ai:
        ai_result = generate_ai_suggestions(
            resume_text, role_key, skills,
            match["missing_required"], ats["score"], match["score"]
        )

    # Persist to DB
    analysis_id = save_analysis({
        "role":             role_key,
        "role_title":       JOB_ROLES[role_key]["title"],
        "match_score":      match["score"],
        "ats_score":        ats["score"],
        "skills_found":     skills,
        "missing_required": match["missing_required"],
        "file_name":        file.filename
    })

    return jsonify({
        "analysis_id":   analysis_id,
        "role":          role_key,
        "role_info":     JOB_ROLES[role_key],
        "skills":        skills,
        "keyword_density": density,
        "word_count":    ats["word_count"],
        "match":         match,
        "ats":           ats,
        "jd":            jd_result,
        "ai":            ai_result
    })


@app.route("/api/history", methods=["GET"])
def history():
    limit = int(request.args.get("limit", 10))
    rows  = get_history(limit)
    # Deserialize JSON fields
    for r in rows:
        r["skills_found"]     = json.loads(r["skills_found"])
        r["missing_required"] = json.loads(r["missing_required"])
    return jsonify(rows)


@app.route("/api/stats", methods=["GET"])
def stats():
    return jsonify(get_stats())


@app.route("/api/roles", methods=["GET"])
def roles():
    return jsonify(JOB_ROLES)


@app.route("/api/skills", methods=["GET"])
def skills_list():
    return jsonify(sorted(SKILLS_DB))


# ── Init & Run ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    init_db()
    print("✅ Database initialized")
    print("✅ Server starting on http://localhost:5000")
    app.run(debug=True, port=5000)