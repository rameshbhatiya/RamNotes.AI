import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(
    title="RamNotes AI Engine",
    description="NCERT & Academic Core AI Portal",
    version="2.0.0"
)

# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------
DB_FILE = "ramnotes.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
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
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# REQUEST SCHEMAS
# ---------------------------------------------------------
class GenerateRequest(BaseModel):
    username: str
    level: str
    subject: str
    category: str
    topic: str
    api_key: str = ""

# Serve Static Assets
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------

@app.get("/")
async def serve_index():
    """Serves the NCERT Books & Solutions UI dashboard."""
    return FileResponse("static/index.html")

@app.post("/api/generate")
async def generate_note(req: GenerateRequest):
    """Generates NCERT/CBSE notes using Gemini AI and stores them in SQLite."""
    key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY", "").strip()
    
    if not key:
        raise HTTPException(
            status_code=400, 
            detail="Gemini API key missing. Please ensure GEMINI_API_KEY is configured in Render Environment Variables."
        )

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        You are RamNotes AI, an expert academic engine specialized in NCERT books, solutions, and CBSE board standards.
        Academic Target: {req.level}
        Subject: {req.subject}
        Category/Feature: {req.category}
        Topic: "{req.topic}"

        Generate structured educational content:
        # 📌 {req.subject} ({req.level}) - {req.topic}
        **Type:** {req.category}

        ## 💡 Core Definitions & Concepts
        Provide clear, step-by-step explanations according to official NCERT standards.

        ## 📐 Formulas, Reactions & Key Equations
        Use standard mathematical/scientific notation.

        ## 📝 NCERT Solutions & Exam Questions
        Provide solved short and long answer questions with step-by-step marking schemes.

        ## ⚡ Quick Revision Notes
        Summary bullet points for fast exam prep.
        """

        response = model.generate_content(prompt)
        content = response.text

        # Persist generated note to database
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute(
            """INSERT INTO notes (username, level, subject, category, topic, content, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (req.username, req.level, req.subject, req.category, req.topic, content, datetime.now().strftime("%Y-%m-%d %H:%M"))
        )
        conn.commit()
        conn.close()

        return {"status": "success", "content": content}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation Error: {str(e)}")

@app.get("/api/feed/{username:path}")
async def get_user_feed(username: str):
    """Fetches user study bank history from SQLite."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute(
        "SELECT id, level, subject, category, topic, content, created_at FROM notes WHERE username = ? ORDER BY id DESC",
        (username,)
    )
    rows = c.fetchall()
    conn.close()

    feed = []
    for r in rows:
        feed.append({
            "id": r[0],
            "level": r[1],
            "subject": r[2],
            "category": r[3],
            "topic": r[4],
            "content": r[5],
            "created_at": r[6]
        })
    return {"feed": feed}
        
