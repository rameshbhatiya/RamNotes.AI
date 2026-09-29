import os
import random
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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

# Gemini API setup (Environment Variable se secure call)
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel('gemini-pro')

class RequestModel(BaseModel):
    level: str
    subject: str
    chapter: str
    prompt: str = ""

# Official NCERT Direct Links Mapper
NCERT_PDF_BASE = "https://ncert.nic.in/textbook.php"

@app.post("/api/generate")
async def generate_content(req: RequestModel):
    try:
        if not GEMINI_API_KEY:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in environment variables.")

        # Quiz Generation with Daily Seed Logic
        if "quiz" in req.prompt.lower():
            today_seed = req.prompt + str(os.getenv("SEED_DATE", "2026-09-29"))
            prompt_text = f"""
            Generate 20 multiple-choice questions (MCQs) for {req.level}, Subject: {req.subject}, Chapter: {req.chapter}.
            Return STRICTLY a JSON array of 20 objects. No markdown, no explanations outside JSON.
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

        # AI Doubt / Solutions
        response = model.generate_content(req.prompt)
        return {"result": response.text}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pdf-link")
async def get_pdf_link(cls: str, subject: str):
    # Generates online NCERT portal redirect
    return {"pdf_url": f"{NCERT_PDF_BASE}?{cls}/{subject}"}
    
