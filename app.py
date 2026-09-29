import os
import sqlite3
import random
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(
    title="RamNotes AI Core Engine",
    description="Multi-Feature Academic & NCERT AI Engine by Ramesh Kumawat",
    version="3.0.0"
)

# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------
DB_FILE = "ramnotes.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. User Profiles & Verification
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            full_name TEXT,
            auth_provider TEXT DEFAULT 'phone_email',
            created_at TEXT NOT NULL
        )
    """)
    
    # 2. Saved Notes & Material
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            level TEXT NOT NULL,
            subject TEXT NOT NULL,
            category TEXT NOT NULL,
            topic TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # 3. Leaderboard & Quiz Scores
    c.execute("""
        CREATE TABLE IF NOT EXISTS quiz_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            level TEXT NOT NULL,
            subject TEXT NOT NULL,
            score INTEGER NOT NULL,
            max_score INTEGER DEFAULT 20,
            timestamp TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# REQUEST SCHEMAS
# ---------------------------------------------------------
class AuthRequest(BaseModel):
    username: str
    full_name: str = ""
    auth_provider: str = "phone_email"

class DoubtRequest(BaseModel):
    username: str
    level: str
    subject: str
    chapter: str
    doubt: str

class QuizSubmitRequest(BaseModel):
    username: str
    level: str
    subject: str
    score: int
    max_score: int = 20

class GenerateRequest(BaseModel):
    username: str
    level: str
    subject: str
    category: str
    topic: str

# Serve Static Folder
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------
# HELPER: AI GENERATION
# ---------------------------------------------------------
def get_ai_response(prompt_text: str):
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not key:
        raise HTTPException(
            status_code=400, 
            detail="Gemini API key is missing in server environment variables."
        )
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt_text)
        return response.text
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI Engine Error: {str(e)}")

# ---------------------------------------------------------
# API ROUTES
# ---------------------------------------------------------

@app.get("/")
async def serve_index():
    """Serves the main application frontend."""
    return FileResponse("static/index.html")

@app.post("/api/auth/login")
async def user_login(req: AuthRequest):
    """Registers or logs in a user profile."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO users (username, full_name, auth_provider, created_at) VALUES (?, ?, ?, ?)",
              (req.username, req.full_name, req.auth_provider, datetime.now().strftime("%Y-%m-%d %H:%M")))
    conn.commit()
    conn.close()
    return {"status": "success", "username": req.username}

@app.post("/api/doubt/solve")
async def solve_doubt(req: DoubtRequest):
    """Step 4: AI Doubt Clearing Engine."""
    prompt = f"""
    You are an expert tutor solving a student's doubt.
    Academic Standard: {req.level}
    Subject: {req.subject}
    Chapter: {req.chapter}
    Student Question: "{req.doubt}"

    Provide a clear, encouraging, step-by-step solution formatted with Markdown:
    - Clear concept explanation
    - Step-by-step calculation or derivation (if applicable)
    - Key takeaway point
    """
    answer = get_ai_response(prompt)
    
    # Save doubt solution as a note
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO notes (username, level, subject, category, topic, content, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (req.username, req.level, req.subject, "Doubt Solution", f"Doubt: {req.doubt[:30]}...", answer, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

    return {"status": "success", "answer": answer}

@app.post("/api/quiz/submit")
async def submit_quiz(req: QuizSubmitRequest):
    """Step 6: Saves 20-mark quiz score to database for Leaderboard tracking."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO quiz_scores (username, level, subject, score, max_score, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
        (req.username, req.level, req.subject, req.score, req.max_score, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Score recorded on leaderboard!"}

@app.get("/api/leaderboard/{level}/{subject}")
async def get_leaderboard(level: str, subject: str):
    """Step 8: Generates dynamic student rankings organized by Class & Subject."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    query = """
        SELECT username, MAX(score) as top_score, COUNT(id) as total_quizzes 
        FROM quiz_scores 
        WHERE level = ? AND subject = ?
        GROUP BY username 
        ORDER BY top_score DESC, total_quizzes DESC 
        LIMIT 20
    """
    c.execute(query, (level, subject))
    rows = c.fetchall()
    conn.close()

    rankings = []
    for rank, r in enumerate(rows, start=1):
        rankings.append({
            "rank": rank,
            "username": r[0],
            "top_score": r[1],
            "quizzes_played": r[2]
        })
    return {"leaderboard": rankings}

@app.post("/api/generate")
async def generate_note(req: GenerateRequest):
    """Generates NCERT chapter notes, solutions, and books."""
    prompt = f"""
    You are RamNotes AI academic engine.
    Level: {req.level} | Subject: {req.subject} | Category: {req.category}
    Topic/Chapter: "{req.topic}"

    Generate comprehensive educational material structured with headers, formulas, and key points.
    """
    content = get_ai_response(prompt)

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "INSERT INTO notes (username, level, subject, category, topic, content, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (req.username, req.level, req.subject, req.category, req.topic, content, datetime.now().strftime("%Y-%m-%d %H:%M"))
    )
    conn.commit()
    conn.close()

    return {"status": "success", "content": content}

@app.get("/api/feed/{username:path}")
async def get_user_feed(username: str):
    """Retrieves saved study materials for the user's timeline."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, level, subject, category, topic, content, created_at FROM notes WHERE username = ? ORDER BY id DESC", (username,))
    rows = c.fetchall()
    conn.close()

    feed = [{"id": r[0], "level": r[1], "subject": r[2], "category": r[3], "topic": r[4], "content": r[5], "created_at": r[6]} for r in rows]
    return {"feed": feed}
    
