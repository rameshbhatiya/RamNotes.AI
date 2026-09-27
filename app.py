import os
import sqlite3
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI(title="RameshNotes AI - Academic Core")

# Configure Gemini API Key
API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
genai.configure(api_key=API_KEY)

# Database Setup: Creates SQLite tables for notes and paper bank
def init_db():
    conn = sqlite3.connect("academic_notes.db")
    cursor = conn.cursor()
    # Notes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            board TEXT NOT NULL,
            subject TEXT NOT NULL,
            level TEXT NOT NULL,
            category TEXT NOT NULL,
            generated_content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

class AcademicRequest(BaseModel):
    board: str        # "CBSE", "RBSE", or "NCERT General"
    subject: str      # "Physics", "Chemistry", "Mathematics", etc.
    level: str        # "Class 9", "Class 10", "Class 11", "Class 12"
    category: str     # "NCERT Chapter Notes", "Sample Paper", "PYQ Practice"
    topic_content: str

@app.post("/api/generate")
async def generate_academic_material(req: AcademicRequest):
    if API_KEY == "YOUR_GEMINI_API_KEY_HERE":
        raise HTTPException(status_code=500, detail="Please set your Gemini API Key in app.py")

    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        You are RameshNotes AI, an expert academic engine specialized in {req.board} board curriculum and NCERT standards for {req.level} {req.subject}.

        Generate structured output based on category: '{req.category}' for topic/content:
        "{req.topic_content}"

        Formatting Rules:
        - Board Focus: Adapt specifically to {req.board} examination patterns and official marking schemes.
        - If 'NCERT Chapter Notes': Include Core Definitions, Formulas/Reactions, and Step-by-Step Concepts.
        - If 'Sample Paper' or 'PYQ Practice': Include Section-wise Questions (1 Mark MCQs, 2/3 Mark Short Answers, 5 Mark Long Derivations/Numericals) with Detailed Solutions & Marking Hints.
        
        Output Structure:
        # 📌 {req.board} - {req.level} {req.subject}
        **Type:** {req.category}
        
        ## 💡 Core Content & Concepts
        ## 📐 Formulas / Equations / Derivations
        ## 📝 Exam Questions & Solutions (CBSE/RBSE Pattern)
        ## ⚡ Quick Revision Hints
        """
        
        res = model.generate_content(prompt)
        generated_text = res.text

        # Store in SQLite Database
        conn = sqlite3.connect("academic_notes.db")
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO notes (board, subject, level, category, generated_content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (req.board, req.subject, req.level, req.category, generated_text, created_at)
        )
        conn.commit()
        conn.close()

        return {"output": generated_text, "status": "Saved to Database"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_history():
    """Fetch stored CBSE/RBSE papers and NCERT notes."""
    conn = sqlite3.connect("academic_notes.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id, board, level, subject, category, created_at FROM notes ORDER BY id DESC")
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r[0], "board": r[1], "level": r[2], "subject": r[3], "category": r[4], "date": r[5]} for r in rows]

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>RameshNotes AI - Academic Engine (CBSE / RBSE / NCERT)</title>
        <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background: #0f172a; color: #fff; padding: 20px; max-width: 1000px; margin: auto; }
            h1 { color: #38bdf8; text-align: center; }
            .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
            @media(max-width: 768px){ .grid { grid-template-columns: 1fr; } }
            .box { background: #1e293b; padding: 20px; border-radius: 8px; border: 1px solid #334155; }
            label { font-weight: bold; color: #94a3b8; display: block; margin-top: 10px; }
            input, select, textarea { width: 100%; padding: 10px; margin: 5px 0; background: #0f172a; color: #fff; border: 1px solid #475569; border-radius: 4px; box-sizing: border-box; }
            textarea { height: 120px; }
            button { width: 100%; padding: 12px; background: #0284c7; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; margin-top: 15px; }
            button:hover { background: #0369a1; }
            #output { background: #0f172a; padding: 15px; border-radius: 4px; border: 1px solid #334155; min-height: 250px; overflow-y: auto; }
            .status { font-size: 12px; color: #10b981; margin-top: 5px; text-align: right; }
        </style>
    </head>
    <body>
        <h1>⚡ RameshNotes AI - CBSE, RBSE & NCERT Core</h1>
        <div class="grid">
            <div class="box">
                <label>Board Standard</label>
                <select id="board">
                    <option value="CBSE">CBSE Board</option>
                    <option value="RBSE">RBSE Board</option>
                    <option value="NCERT General">NCERT Standard</option>
                </select>

                <label>Class Level</label>
                <select id="level">
                    <option value="Class 9">Class 9</option>
                    <option value="Class 10">Class 10</option>
                    <option value="Class 11">Class 11</option>
                    <option value="Class 12" selected>Class 12 (PCM/PCB)</option>
                </select>

                <label>Subject</label>
                <input id="subject" value="Physics" placeholder="e.g., Physics, Chemistry, Math">

                <label>Category / Output Type</label>
                <select id="category">
                    <option value="NCERT Chapter Notes">NCERT Chapter Key Notes</option>
                    <option value="Sample Paper">Board Sample Paper with Marking Scheme</option>
                    <option value="PYQ Practice">Previous Year Questions (PYQs) + Solutions</option>
                </select>

                <label>Topic / Material Prompt</label>
                <textarea id="topic" placeholder="e.g., Electrostatics Gauss Law derivations or Ray Optics PYQs..."></textarea>
                
                <button onclick="run()">Generate & Save to DB</button>
                <div id="status" class="status"></div>
            </div>

            <div class="box">
                <h2>Generated Study Bank</h2>
                <div id="output"><em>Your CBSE/RBSE papers, PYQs, and NCERT notes will render here...</em></div>
            </div>
        </div>

        <script>
            async function run() {
                const board = document.getElementById('board').value;
                const level = document.getElementById('level').value;
                const subject = document.getElementById('subject').value;
                const category = document.getElementById('category').value;
                const topic_content = document.getElementById('topic').value;
                const output = document.getElementById('output');
                const status = document.getElementById('status');
                
                if(!topic_content.trim()) { alert('Please enter a topic or prompt.'); return; }

                output.innerHTML = '<em>Generating ' + board + ' ' + category + '...</em>';
                status.innerHTML = '';
                
                const res = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ board, level, subject, category, topic_content })
                });
                const data = await res.json();
                if(res.ok) {
                    output.innerHTML = marked.parse(data.output);
                    status.innerHTML = '✅ Saved to SQLite Database (academic_notes.db)';
                } else {
                    output.innerHTML = '<b style="color:red">' + data.detail + '</b>';
                }
            }
        </script>
    </body>
    </html>
    """
