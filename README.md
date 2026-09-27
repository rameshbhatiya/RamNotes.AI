# ⚡ RameshNotes AI

An adaptive, full-stack study assistant that transforms raw study material, lecture notes, and textbook excerpts into structured Markdown notes tailored for **Class 9 through University students**.

---

## 🌟 Key Features

- 🎓 **Multi-Level Academic Formatting:** Automatically adjusts depth, formulas, and language based on the target level (Class 9–10, Class 11–12 PCM/PCB, or University).
- 📐 **LaTeX & Math Support:** Renders mathematical formulas and chemical equations clearly.
- 📝 **Revision & Flashcards:** Generates quick revision bullet points and key takeaways alongside structured concepts.
- ⚡ **Lightweight & Fast:** Built on Python FastAPI and powered by the Google Gemini API.

---

## 🛠️ Tech Stack

- **Backend:** Python, FastAPI, Uvicorn
- **AI Engine:** Google Gemini API (`gemini-1.5-flash`)
- **Frontend:** HTML5, CSS3, JavaScript, Marked.js

---

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install fastapi uvicorn google-generativeai
```

### 2. Configure API Key & Run
Set your Gemini API key in your terminal and launch the server:

**Windows (CMD/PowerShell):**
```cmd
set GEMINI_API_KEY=your_gemini_api_key_here
uvicorn app:app --reload
```

**Linux / Mac:**
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
uvicorn app:app --reload
```

### 3. Open Application
Navigate to `http://127.0.0.1:8000` in your web browser.

---

## 📁 Project Structure

```text
rameshnotes-ai/
├── app.py          # Unified FastAPI backend & embedded frontend
└── README.md       # Project documentation
```
