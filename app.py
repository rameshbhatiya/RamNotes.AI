import os
import random
import sqlite3
from datetime import datetime
import streamlit as st
import google.generativeai as genai

# Page Configuration
st.set_page_config(
    page_title="RameshNotes AI | Enterprise Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Responsive Styling
st.markdown("""
    <style>
    .main { padding: 1rem; }
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; height: 3em; background-color: #0284c7; color: white; }
    .stButton>button:hover { background-color: #0369a1; }
    .auth-card { background-color: #1e293b; padding: 2rem; border-radius: 12px; border: 1px solid #334155; }
    .status-badge { background-color: #10b981; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# DATABASE INITIALIZATION
# ---------------------------------------------------------
def get_db_connection():
    return sqlite3.connect("academic_notes.db", check_same_thread=False)

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    # Users Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            identifier TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    # Notes Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            category TEXT NOT NULL,
            level TEXT NOT NULL,
            stream TEXT NOT NULL,
            subject TEXT NOT NULL,
            type TEXT NOT NULL,
            generated_content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------------------------------------------------
# SESSION STATE MANAGEMENT
# ---------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_identifier" not in st.session_state:
    st.session_state.user_identifier = ""
if "generated_otp" not in st.session_state:
    st.session_state.generated_otp = None

# ---------------------------------------------------------
# MODULE 1: AUTHENTICATION SYSTEM (OTP & SOCIAL LOGIN)
# ---------------------------------------------------------
if not st.session_state.authenticated:
    st.title("⚡ RameshNotes AI - Student & Graduate Portal")
    st.caption("Secure Multi-Auth Login | Access CBSE, RBSE, NCERT & University Academic Engines")

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("<div class='auth-card'>", unsafe_allow_html=True)
        st.subheader("🔑 User Login / Registration")
        
        auth_method = st.radio("Choose Login Verification Method:", ["Mobile Phone OTP", "Gmail / Email OTP", "Social Login (Google / Facebook)"])

        if auth_method in ["Mobile Phone OTP", "Gmail / Email OTP"]:
            input_label = "Enter 10-digit Phone Number:" if "Phone" in auth_method else "Enter Email Address:"
            user_input = st.text_input(input_label, placeholder="+91 9876543210" if "Phone" in auth_method else "student@domain.com")
            
            if st.button("📩 Request Verification OTP"):
                if user_input.strip():
                    st.session_state.generated_otp = str(random.randint(100000, 999999))
                    st.session_state.user_identifier = user_input.strip()
                    st.info(f"🔑 [SANDBOX OTP DEMO]: Your One-Time Password is **{st.session_state.generated_otp}**")
                else:
                    st.warning("Please provide a valid phone number or email.")

            if st.session_state.generated_otp:
                entered_otp = st.text_input("Enter 6-Digit OTP Code:", type="password")
                if st.button("✅ Verify OTP & Login"):
                    if entered_otp == st.session_state.generated_otp:
                        st.session_state.authenticated = True
                        # Register user in database
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("INSERT OR IGNORE INTO users (identifier, created_at) VALUES (?, ?)", 
                                       (st.session_state.user_identifier, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                        conn.commit()
                        conn.close()
                        st.success("Verification successful! Redirecting to workspace...")
                        st.rerun()
                    else:
                        st.error("Invalid OTP code. Please check and try again.")

        elif auth_method == "Social Login (Google / Facebook)":
            st.info("Direct Single Sign-On (SSO) Portal")
            social_user = st.text_input("Enter your Google / Facebook Email Account:", placeholder="user@gmail.com")
            if st.button("🌐 Authenticate via Single Sign-On"):
                if social_user.strip():
                    st.session_state.authenticated = True
                    st.session_state.user_identifier = social_user.strip()
                    st.rerun()
                else:
                    st.warning("Please provide your account email.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("""
        ### 🎓 Academic Core Coverage
        - **School Level:** CBSE, RBSE & NCERT (Class 9 to 12)
        - **Senior Streams:** Science (PCM/PCB), Commerce, Arts / Humanities
        - **Graduate Level:** B.Tech / B.E, B.Sc, B.Com, B.A, BCA / MCA
        - **Exam Engine:** Sample Papers, PYQs with Marking Schemes, & Structured Notes
        """)
    st.stop()

# ---------------------------------------------------------
# MODULE 2: ACADEMIC CORE WORKSPACE (AUTHENTICATED)
# ---------------------------------------------------------

# Top Bar Header
st.sidebar.markdown(f"👤 **Logged in as:** `{st.session_state.user_identifier}`")
if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.session_state.user_identifier = ""
    st.session_state.generated_otp = None
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.header("⚙️ API & System Setup")

# API Key Logic with Fallback Handling
api_key = st.secrets.get("GEMINI_API_KEY", "")
if not api_key:
    api_key = st.sidebar.text_input("Paste Gemini API Key", type="password", help="Get free key at aistudio.google.com")

if api_key:
    genai.configure(api_key=api_key)

st.title("⚡ RameshNotes AI - Multi-Stream Academic Engine")

# ---------------------------------------------------------
# STREAM & LEVEL SELECTION MATRIX
# ---------------------------------------------------------
st.sidebar.header("🎯 Academic Mapping")

academic_category = st.sidebar.selectbox("Select Academic Level", ["High School (Class 9 - 10)", "Senior Secondary (Class 11 - 12)", "Undergraduate / University"])

# Dynamic Options based on Level
if academic_category == "High School (Class 9 - 10)":
    class_level = st.sidebar.selectbox("Class", ["Class 9", "Class 10"])
    stream = "General Academics"
    board = st.sidebar.selectbox("Board Standard", ["CBSE", "RBSE", "NCERT Standard"])
    subject = st.sidebar.selectbox("Subject", ["Science (Physics/Chemistry/Biology)", "Mathematics", "Social Science", "English", "Computer Applications"])

elif academic_category == "Senior Secondary (Class 11 - 12)":
    class_level = st.sidebar.selectbox("Class", ["Class 11", "Class 12"])
    board = st.sidebar.selectbox("Board Standard", ["CBSE", "RBSE", "NCERT Standard"])
    stream = st.sidebar.selectbox("Stream", ["Science (PCM)", "Science (PCB)", "Commerce", "Arts / Humanities"])
    
    # Subjects mapped to stream
    if "PCM" in stream:
        subject = st.sidebar.selectbox("Subject", ["Physics", "Chemistry", "Mathematics", "Computer Science / IP", "English Core"])
    elif "PCB" in stream:
        subject = st.sidebar.selectbox("Subject", ["Physics", "Chemistry", "Biology", "Psychology", "English Core"])
    elif "Commerce" in stream:
        subject = st.sidebar.selectbox("Subject", ["Accountancy", "Business Studies", "Economics", "Applied Mathematics", "English"])
    else: # Arts
        subject = st.sidebar.selectbox("Subject", ["History", "Political Science", "Geography", "Economics", "Sociology", "Psychology"])

else:  # Higher Education / Graduate
    board = "University Curriculum"
    class_level = st.sidebar.selectbox("Degree Program", ["B.Tech / B.E", "B.Sc", "B.Com", "B.A", "BCA / MCA"])
    
    if class_level in ["B.Tech / B.E", "BCA / MCA"]:
        stream = st.sidebar.selectbox("Branch / Specialization", ["Computer Science & IT", "Electrical / Electronics", "Mechanical", "Civil / Marine"])
        subject = st.sidebar.text_input("Course / Subject Name", "Data Structures & Algorithms")
    elif class_level == "B.Sc":
        stream = st.sidebar.selectbox("Specialization", ["Physics Major", "Chemistry Major", "Mathematics Major", "Computer Science"])
        subject = st.sidebar.text_input("Course / Subject Name", "Quantum Mechanics / Physical Chemistry")
    elif class_level == "B.Com":
        stream = "Commerce & Finance"
        subject = st.sidebar.text_input("Course / Subject Name", "Corporate Accounting / Financial Management")
    else:
        stream = "Humanities & Social Sciences"
        subject = st.sidebar.text_input("Course / Subject Name", "Political Theory / World History")

content_type = st.sidebar.selectbox(
    "Output Document Type",
    ["Comprehensive Chapter Notes", "Board / University Sample Paper", "Previous Year Questions (PYQs) + Marking Scheme", "Quick Flashcards & Formula Sheet"]
)

# ---------------------------------------------------------
# MAIN GENERATION ENGINE
# ---------------------------------------------------------
st.subheader(f"📚 {academic_category} | {class_level} ({subject})")
topic_prompt = st.text_area("Enter Topic, Chapter Excerpt, or Specific Syllabus Points:", height=150, placeholder="e.g., Organic Chemistry Reaction Mechanisms, Gauss Law Numerical Problems, or Operating System Process Scheduling...")

if st.button("🚀 Generate Academic Material & Save to Database"):
    if not api_key:
        st.error("⚠️ API Key missing! Add GEMINI_API_KEY to Streamlit Secrets or paste it in the sidebar.")
    elif not topic_prompt.strip():
        st.warning("⚠️ Please provide a topic or prompt.")
    else:
        try:
            with st.spinner(f"Processing {subject} material via Gemini AI..."):
                model = genai.GenerativeModel('gemini-1.5-flash')
                
                system_prompt = f"""
                You are RameshNotes AI, an expert academic content generator specializing in {academic_category} for {class_level} ({board}).
                Stream: {stream} | Subject: {subject}
                
                Generate a structured document of type: '{content_type}' for the following content/topic:
                "{topic_prompt}"
                
                Formatting & Standard Guidelines:
                - Target Depth: Strictly align complexity to a {class_level} student level.
                - Formulas & Equations: Use clear LaTeX formatting ($inline$ or $$display$$).
                - Exam Structure: If Sample Paper or PYQ, organize into clear sections (MCQs, Short Answer, Long Derivations/Analysis) with step-by-step marking schemes.
                
                Required Markdown Headers:
                # 📌 {subject}: {content_type}
                **Level/Board:** {class_level} ({board}) | **Stream:** {stream}
                
                ## 💡 Core Theoretical Concepts
                ## 📐 Key Formulas, Equations & Derivations
                ## 📝 Solved Exam Questions & Marking Scheme
                ## ⚡ Key Revision Summary
                """
                
                response = model.generate_content(system_prompt)
                generated_notes = response.text
                
                # Save to Database
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO notes (user_id, category, level, stream, subject, type, generated_content, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (st.session_state.user_identifier, academic_category, class_level, stream, subject, content_type, generated_notes, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
                conn.commit()
                conn.close()
                
                st.success("✅ Notes generated and saved to your personal database history!")
                st.markdown("---")
                st.markdown(generated_notes)

        except Exception as e:
            st.error(f"❌ Generation Error: {str(e)}")

# ---------------------------------------------------------
# MODULE 3: USER DATABASE HISTORY & REVISION BANK
# ---------------------------------------------------------
st.markdown("---")
with st.expander("📚 Saved Study Bank History"):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, level, stream, subject, type, created_at FROM notes WHERE user_id = ? ORDER BY id DESC", (st.session_state.user_identifier,))
        records = cursor.fetchall()
        conn.close()
        
        if records:
            st.dataframe(
                records,
                column_config={0: "ID", 1: "Level", 2: "Stream", 3: "Subject", 4: "Type", 5: "Saved At"},
                use_container_width=True
            )
        else:
            st.info("No saved records found for your account yet.")
    except Exception as e:
        st.error(f"Error loading history: {e}")
                
