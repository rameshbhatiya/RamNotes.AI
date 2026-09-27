import os
import sqlite3
from datetime import datetime
import streamlit as st
import google.generativeai as genai

# Page Configuration
st.set_page_config(
    page_title="RameshNotes AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Mobile-friendly styling
st.markdown("""
    <style>
    .main { padding: 1rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; }
    .stTextArea textarea { border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

st.title("⚡ RameshNotes AI - Academic Core")
st.caption("Adaptive Study Assistant for CBSE, RBSE & NCERT Curriculums")

# 1. API Key Retrieval (Handles Streamlit Secrets & Local Fallback)
api_key = None
if "GEMINI_API_KEY" in st.secrets:
    api_key = st.secrets["GEMINI_API_KEY"]
else:
    api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")

if api_key:
    genai.configure(api_key=api_key)

# 2. SQLite Database Setup (Error-Handled)
def get_db_connection():
    conn = sqlite3.connect("academic_notes.db", check_same_thread=False)
    return conn

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
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
    except Exception as e:
        st.error(f"Database Initialization Error: {e}")

init_db()

# 3. Sidebar Selection Panel
st.sidebar.header("📋 Academic Configuration")
board = st.sidebar.selectbox("Board Standard", ["CBSE", "RBSE", "NCERT General"])
level = st.sidebar.selectbox("Class / Grade Level", ["Class 9", "Class 10", "Class 11", "Class 12"])
subject = st.sidebar.text_input("Subject", "Physics")
category = st.sidebar.selectbox(
    "Content Type", 
    ["NCERT Chapter Notes", "Board Sample Paper", "Previous Year Questions (PYQs)"]
)

# 4. Main Input & Generation
st.subheader("📝 Input Topic or Chapter Excerpt")
topic_content = st.text_area(
    "Enter topic name, syllabus points, or chapter text:",
    placeholder="e.g., Gauss Law and its applications, Ray Optics PYQs, or Organic Chemistry Reactions...",
    height=140
)

if st.button("🚀 Generate & Save Content", type="primary"):
    if not api_key:
        st.error("⚠️ Gemini API Key missing! Add `GEMINI_API_KEY` to Streamlit Secrets or paste it in the sidebar.")
    elif not topic_content.strip():
        st.warning("⚠️ Please enter a topic or chapter text.")
    else:
        try:
            with st.spinner("⏳ Analyzing syllabus & generating notes via Gemini AI..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                prompt = f"""
                You are RameshNotes AI, an expert academic tutor for {board} curriculum and NCERT standards targeting {level} {subject}.

                Generate structured study material for category: '{category}' based on topic:
                "{topic_content}"

                Rules:
                - Board Context: Follow {board} exam structures and official marking criteria.
                - If 'NCERT Chapter Notes': Detail key definitions, step-by-step formula derivations, and standard equations using proper LaTeX formatting ($inline$ or $$display$$).
                - If 'Board Sample Paper' or 'Previous Year Questions (PYQs)': Format into clear sections (Section A: 1 Mark MCQs, Section B: Short 2/3 Mark Questions, Section C: Long 5 Mark Derivations/Problems) with complete step-by-step solutions.

                Output Layout:
                # 📌 {board} - {level} {subject}
                **Type:** {category}

                ## 💡 Core Concepts & Definitions
                ## 📐 Formulas, Equations & Derivations
                ## 📝 Exam Questions & Solutions ({board} Pattern)
                ## ⚡ Quick Revision Points
                """

                response = model.generate_content(prompt)
                generated_text = response.text

                # Save to Database
                conn = get_db_connection()
                cursor = conn.cursor()
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO notes (board, subject, level, category, generated_content, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (board, subject, level, category, generated_text, created_at)
                )
                conn.commit()
                conn.close()

                st.success("✅ Content generated and stored in SQLite database!")
                st.markdown("---")
                st.markdown(generated_text)

        except Exception as e:
            st.error(f"❌ Error generating content: {str(e)}")

# 5. Database Search & History Drawer
st.markdown("---")
with st.expander("📚 Saved Study Bank History"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, board, level, subject, category, created_at FROM notes ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        if rows:
            st.dataframe(
                rows,
                column_config={
                    0: "ID", 
                    1: "Board", 
                    2: "Level", 
                    3: "Subject", 
                    4: "Category", 
                    5: "Created At"
                },
                use_container_width=True
            )
        else:
            st.info("No saved records in the database yet.")
    except Exception as e:
        st.error(f"Could not load database records: {e}")
    
