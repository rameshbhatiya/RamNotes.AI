import os
import random
import json
import uuid
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel, EmailStr
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

# In-Memory Database (Production ke liye SQLite/PostgreSQL use karein)
users_db = {}
otp_store = {}

# Pydantic Schemas
class ManualSignup(BaseModel):
    name: str
    contact: str # Email or Phone
    password: str
    dob: str
    captcha: str

class OTPVerify(BaseModel):
    contact: str
    otp: str

class LoginRequest(BaseModel):
    contact: str
    password: str

class AIDoubtRequest(BaseModel):
    prompt: str

# 1. Root Route
@app.get("/", response_class=HTMLResponse)
async def serve_home():
    possible_paths = ["index.html", "templates/index.html", "static/index.html"]
    for path in possible_paths:
        if os.path.exists(path):
            return FileResponse(path)
    return "<h1>RamNotes AI Server Active Hai!</h1>"

# 2. Local NCERT Book Download (Direct File Response instead of external site)
@app.get("/api/download-book")
async def download_book(cls: str, subject: str, chapter: str):
    # Local PDF file path check
    file_path = f"books/class_{cls}/{subject}/{chapter}.pdf"
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=f"{subject}_ch{chapter}.pdf")
    else:
        # Dummy PDF stream response agar local file present na ho
        raise HTTPException(status_code=404, detail="Book PDF locally not found in server directory.")

# 3. Manual Signup & OTP / Captcha System
@app.post("/api/auth/signup")
async def signup(user: ManualSignup):
    if user.captcha.upper() != "RAM78": # Static demo captcha check
        raise HTTPException(status_code=400, detail="Invalid Captcha!")
    
    if user.contact in users_db:
        raise HTTPException(status_code=400, detail="User already exists!")
    
    # Generate 6-Digit OTP
    generated_otp = str(random.randint(100000, 999999))
    otp_store[user.contact] = {
        "otp": generated_otp,
        "temp_user": user.dict()
    }
    
    # Print OTP in server logs (In production, send via SMS/Email API)
    print(f"[OTP SERVICE] Sent OTP {generated_otp} to {user.contact}")
    return {"message": "OTP sent successfully on phone/email!", "demo_otp": generated_otp}

@app.post("/api/auth/verify-otp")
async def verify_otp(data: OTPVerify):
    record = otp_store.get(data.contact)
    if not record or record["otp"] != data.otp:
        raise HTTPException(status_code=400, detail="Incorrect OTP!")
    
    # Save user to DB
    user_data = record["temp_user"]
    users_db[data.contact] = user_data
    del otp_store[data.contact]
    
    return {"message": "Account created successfully!", "user": {"name": user_data["name"], "contact": user_data["contact"]}}

@app.post("/api/auth/login")
async def login(data: LoginRequest):
    user = users_db.get(data.contact)
    if not user or user["password"] != data.password:
        raise HTTPException(status_code=400, detail="Invalid Contact or Password!")
    
    return {"message": "Login successful", "user": {"name": user["name"], "contact": user["contact"]}}

# 4. AI Doubt Solver Endpoint
@app.post("/api/ai/doubt")
async def solve_doubt(req: AIDoubtRequest):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing in backend.")
    try:
        response = model.generate_content(f"Solve this student doubt step-by-step: {req.prompt}")
        return {"answer": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
