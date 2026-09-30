import os
import random
import json
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
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

# In-Memory Database
users_db = {}
usernames_db = set()
otp_store = {}

class SignupReq(BaseModel):
    name: str
    dob: str
    phone: str
    email: str
    password: str
    sex: str
    username: str

class OTPVerifyReq(BaseModel):
    contact: str
    otp: str

class LoginReq(BaseModel):
    username_or_contact: str
    password: str

class DoubtReq(BaseModel):
    cls: str
    subject: str
    chapter: str
    topic: str
    doubt: str

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    possible_paths = ["index.html", "templates/index.html", "static/index.html"]
    for path in possible_paths:
        if os.path.exists(path):
            return FileResponse(path)
    return "<h1>RamNotes AI Backend Active</h1>"

# 1. Registration System with Unique Username Check
@app.post("/api/auth/register")
async def register(user: SignupReq):
    if user.username in usernames_db:
        raise HTTPException(status_code=400, detail="Username already exist!")
    
    gen_otp = str(random.randint(100000, 999999))
    target = user.email if user.email else user.phone
    
    otp_store[target] = {
        "otp": gen_otp,
        "user_data": user.dict()
    }
    
    msg = f"OTP sent on Your Mobile no. ({gen_otp})" if user.phone else f"OTP sent on your Gmail ({gen_otp})"
    return {"message": msg, "target": target}

@app.post("/api/auth/verify-otp")
async def verify_otp(req: OTPVerifyReq):
    record = otp_store.get(req.contact)
    if not record or record["otp"] != req.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP!")
    
    data = record["user_data"]
    users_db[data["username"]] = data
    users_db[data["email"]] = data
    users_db[data["phone"]] = data
    usernames_db.add(data["username"])
    del otp_store[req.contact]
    
    return {"message": "Account created successfully!", "user": data}

@app.post("/api/auth/login")
async def login(req: LoginReq):
    user = users_db.get(req.username_or_contact)
    if not user or user["password"] != req.password:
        raise HTTPException(status_code=400, detail="Invalid Credentials!")
    return {"message": "Login successful", "user": user}

@app.post("/api/auth/reset-password")
async def reset_password(contact: str):
    return {"message": f"Password reset link sent on your contact: {contact}"}

# 2. AI Doubt Solver with Disclaimer
@app.post("/api/ai/doubt")
async def solve_doubt(req: DoubtReq):
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API Key missing.")
    
    prompt = f"Class: {req.cls}, Subject: {req.subject}, Chapter: {req.chapter}, Topic: {req.topic}\nDoubt: {req.doubt}"
    try:
        response = model.generate_content(prompt)
        return {
            "answer": response.text,
            "disclaimer": "It can make mistakes, please cooperate with it."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
        
