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
    description="Multi-Subject Academic AI Platform",
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
            username TEXT,
            level TEXT,
            subject TEXT,
            category TEXT,
            topic TEXT,
            content TEXT,
            created_at TEXT
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

# Serve static frontend folder
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.get("/")
async def serve_index():
    """Serves the main Instagram/YouTube-style single-page interface."""
    return FileResponse("static/index.html")

@app.post("/api/generate")
async def generate_note(req: GenerateRequest):
    """Handles AI generation requests and persists posts into SQLite."""
    # Retrieve key from user input or environment variable
    key = req.api_key.strip() if req.api_key else os.environ.get("GEMINI_API_KEY", "").strip()
    
    if not key:
        raise HTTPException(
            status_code=400, 
            detail="Gemini API Key is missing. Please set GEMINI_API_KEY in your deployment environment or enter it manually."
        )

    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")

        prompt = f"""
        You are RamNotes AI, an elite academic assistant engine for student learning.
        Academic Level: {req.level}
        Subject: {req.subject}
        Content Format: {req.category}
        Topic / Problem Statement: "{req.topic}"

        Provide comprehensive, highly structured academic material:
        # 📌 {req.subject}: {req.topic}
        **Level:** {req.level} | **Category:** {req.category}

        ## 💡 Core Theoretical Concepts
        Provide a clear step-by-step breakdown.

        ## 📐 Formulas, Reactions & Equations
        Use precise formatting ($inline$ or $$display$$ for math).

        ## 📝 Model Exam Questions & Answers
        Include typical board/university standard questions with answers.

        ## ⚡ Key Revision Points
        Bullet points summarizing key takeaways.
        """

        response = model.generate_content(prompt)
        content = response.text

        # Save generated post to database
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

@app.get("/api/feed/{username}")
async def get_user_feed(username: str):
    """Retrieves all generated timeline posts for the user."""
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
        
