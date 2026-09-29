import os
import random
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import google.generativeai as genai

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gemini API Setup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')

# Root URL (/) par index.html load karega
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    if os.path.exists("index.html"):
        return FileResponse("index.html")
    return "<h1>RamNotes AI Server is Running!</h1><p>index.html file not found in root directory.</p>"

class RequestModel(BaseModel):
    level: str
    subject: str
    chapter: str
    prompt: str = ""

NCERT_PDF_BASE = "https://ncert.nic.in/textbook.php"

@app.post("/api/generate")
async def generate_content(req: RequestModel):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY environment variable missing.")

        if "quiz" in req.prompt.lower():
            prompt_text = f"""
            Generate 20 multiple-choice questions (MCQs) for {req.level}, Subject: {req.subject}, Chapter: {req.chapter}.
            Return STRICTLY a JSON array of 20 objects. No markdown outside JSON.
            Structure:
            [
              {{
                "q": "Question text",
                "options": ["Opt A", "Opt B", "Opt C", "Opt D"],
                "answer": 0
              }}
            ]
            """
            response = model.generate_content(prompt_text)
            return {"result": response.text}

        response = model.generate_content(req.prompt)
        return {"result": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf-link")
async def get_pdf_link(cls: str, subject: str):
    return {"pdf_url": f"{NCERT_PDF_BASE}?{cls}/{subject}"}
    
