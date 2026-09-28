import sqlite3
import os
from typing import List, Dict, Any, Optional

import shutil
IS_VERCEL = os.getenv("VERCEL") == "1" or os.getenv("VERCEL_ENV") is not None
ORIGINAL_DB_PATH = os.path.join(os.path.dirname(__file__), "safibot.db")

if IS_VERCEL:
    TMP_DB_PATH = os.path.join("/tmp", "safibot.db")
    if not os.path.exists(TMP_DB_PATH) and os.path.exists(ORIGINAL_DB_PATH):
        try:
            shutil.copy2(ORIGINAL_DB_PATH, TMP_DB_PATH)
        except Exception:
            pass
    DB_PATH = TMP_DB_PATH if os.path.exists(TMP_DB_PATH) else ORIGINAL_DB_PATH
else:
    DB_PATH = ORIGINAL_DB_PATH

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()
    
    # Students Table (Structured / Private)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS students (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        roll_number TEXT,
        admission_number TEXT UNIQUE,
        email TEXT,
        course TEXT NOT NULL,
        department TEXT NOT NULL,
        semester INTEGER NOT NULL,
        batch TEXT NOT NULL,
        interests TEXT
    );
    """)
    
    # Auto-migration if students table existed without new columns
    cursor.execute("PRAGMA table_info(students);")
    existing_cols = [c[1] for c in cursor.fetchall()]
    if "roll_number" not in existing_cols:
        cursor.execute("ALTER TABLE students ADD COLUMN roll_number TEXT;")
    if "admission_number" not in existing_cols:
        cursor.execute("ALTER TABLE students ADD COLUMN admission_number TEXT;")
    if "email" not in existing_cols:
        cursor.execute("ALTER TABLE students ADD COLUMN email TEXT;")

    # Deadlines View (combines notices with deadlines and events with registration deadlines)
    cursor.execute("""
    CREATE VIEW IF NOT EXISTS deadlines AS
    SELECT 
        'notice' AS item_type,
        id AS item_id,
        title,
        category,
        content AS description,
        deadline AS due_date,
        target_course,
        target_department,
        target_semester,
        source
    FROM notices 
    WHERE deadline IS NOT NULL AND deadline != ''
    UNION ALL
    SELECT 
        'event' AS item_type,
        id AS item_id,
        title,
        'Event Registration' AS category,
        description,
        registration_deadline AS due_date,
        target_course,
        target_department,
        target_semester,
        source
    FROM events
    WHERE registration_deadline IS NOT NULL AND registration_deadline != '';
    """)
    
    # Notices Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS notices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        category TEXT NOT NULL,
        content TEXT NOT NULL,
        target_course TEXT DEFAULT 'ALL',
        target_department TEXT DEFAULT 'ALL',
        target_semester TEXT DEFAULT 'ALL',
        date TEXT NOT NULL,
        deadline TEXT,
        source TEXT,
        source_type TEXT DEFAULT 'Notice Board',
        file_path TEXT,
        is_approved INTEGER DEFAULT 1
    );
    """)
    
    # Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT NOT NULL,
        date TEXT NOT NULL,
        time TEXT NOT NULL,
        venue TEXT NOT NULL,
        organizer TEXT NOT NULL,
        target_course TEXT DEFAULT 'ALL',
        target_department TEXT DEFAULT 'ALL',
        target_semester TEXT DEFAULT 'ALL',
        registration_deadline TEXT,
        source TEXT,
        is_approved INTEGER DEFAULT 1
    );
    """)
    
    # Documents Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        document_type TEXT NOT NULL,
        course TEXT DEFAULT 'ALL',
        semester INTEGER,
        department TEXT DEFAULT 'ALL',
        file_path TEXT NOT NULL,
        source TEXT,
        upload_date TEXT NOT NULL,
        total_pages INTEGER DEFAULT 1
    );
    """)
    
    # Timetable / Exam Timetable Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS timetables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        course TEXT NOT NULL,
        semester INTEGER NOT NULL,
        day_or_date TEXT NOT NULL,
        subject TEXT NOT NULL,
        time TEXT NOT NULL,
        room TEXT NOT NULL,
        is_exam INTEGER DEFAULT 1,
        document_id INTEGER,
        page_number INTEGER,
        source TEXT
    );
    """)

    # Programmes Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS programmes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        degree TEXT,
        level TEXT NOT NULL, -- UG, PG, ITEP, PhD
        department TEXT NOT NULL,
        duration TEXT DEFAULT '3 Years',
        description TEXT,
        source_url TEXT DEFAULT 'https://sias.edu.in/admission.html',
        source_page_title TEXT DEFAULT 'SIAS Admission & Academic Programmes Portal',
        last_updated TEXT
    );
    """)
    cursor.execute("PRAGMA table_info(programmes);")
    prog_cols = [c[1] for c in cursor.fetchall()]
    if "degree" not in prog_cols:
        cursor.execute("ALTER TABLE programmes ADD COLUMN degree TEXT;")
    if "source_page_title" not in prog_cols:
        cursor.execute("ALTER TABLE programmes ADD COLUMN source_page_title TEXT DEFAULT 'SIAS Admission & Academic Programmes Portal';")

    # Departments Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS departments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        hod_name TEXT,
        description TEXT,
        source_url TEXT DEFAULT 'https://sias.edu.in/',
        last_updated TEXT
    );
    """)
    cursor.execute("PRAGMA table_info(departments);")
    dept_cols = [c[1] for c in cursor.fetchall()]
    if "hod_name" not in dept_cols:
        cursor.execute("ALTER TABLE departments ADD COLUMN hod_name TEXT;")

    # Faculty Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS faculty (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        designation TEXT NOT NULL,
        department TEXT NOT NULL,
        profile_url TEXT DEFAULT 'https://sias.edu.in/',
        last_updated TEXT
    );
    """)

    # Website Pages Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS website_pages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL UNIQUE,
        title TEXT NOT NULL,
        content_summary TEXT,
        content_hash TEXT,
        last_scraped TEXT,
        last_synced TEXT
    );
    """)
    cursor.execute("PRAGMA table_info(website_pages);")
    wp_cols = [c[1] for c in cursor.fetchall()]
    if "content_hash" not in wp_cols:
        cursor.execute("ALTER TABLE website_pages ADD COLUMN content_hash TEXT;")
    if "last_scraped" not in wp_cols:
        cursor.execute("ALTER TABLE website_pages ADD COLUMN last_scraped TEXT;")


    # Users Table (Students & Admins)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        roll_number TEXT,
        admission_number TEXT UNIQUE,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'STUDENT', -- 'STUDENT' or 'ADMIN'
        course TEXT,
        department TEXT,
        semester INTEGER,
        batch TEXT,
        interests TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # Chat History Table (Interaction Logging)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        student_name TEXT,
        course TEXT,
        semester INTEGER,
        query TEXT NOT NULL,
        intent TEXT,
        answer TEXT NOT NULL,
        timestamp TEXT NOT NULL
    );
    """)

    # Feedback Table (Continuous Knowledge Improvement)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        question TEXT NOT NULL,
        answer TEXT NOT NULL,
        source TEXT,
        feedback TEXT NOT NULL, -- 'helpful' or 'not_helpful'
        comment TEXT,
        timestamp TEXT NOT NULL
    );
    """)

    # Learning Queue Table (Unanswered / Review Questions)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning_queue (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        user_id TEXT,
        status TEXT NOT NULL DEFAULT 'UNANSWERED', -- 'UNANSWERED', 'RESOLVED', 'IGNORED'
        verified_answer TEXT,
        added_source TEXT,
        timestamp TEXT NOT NULL,
        resolved_at TEXT,
        resolved_by TEXT
    );
    """)
    
    conn.commit()
    conn.close()

def seed_demo_data():
    """Seed initial demo students, notices, events, timetables if empty."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM students;")
    if cursor.fetchone()[0] == 0:
        demo_students = [
            ("STU_BBA_01", "Rahul Menon", "BBA-24-01", "ADM2024BBA01", "rahul@sias.edu.in", "BBA", "Management Studies", 3, "2024-2027", "Marketing, Financial Markets, Case Studies"),
            ("STU_BCA_01", "Fatima Zahra", "BCA-24-01", "ADM2024BCA01", "fatima@sias.edu.in", "BCA", "Computer Applications", 3, "2024-2027", "AI, Python Programming, Web Dev"),
            ("STU_BCOM_01", "Arjun Das", "BCM-23-01", "ADM2023BCM01", "arjun@sias.edu.in", "BCom", "Commerce", 5, "2023-2026", "Accounting, Taxation"),
            ("STU_BSC_01", "Ananya Nair", "BSC-25-01", "ADM2025BSC01", "ananya@sias.edu.in", "BSc Computer Science", "Computer Science", 1, "2025-2028", "Algorithms, Robotics")
        ]
        cursor.executemany("""
        INSERT INTO students (id, name, roll_number, admission_number, email, course, department, semester, batch, interests)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, demo_students)
    else:
        # Ensure roll numbers and admission numbers are populated for demo students
        cursor.execute("UPDATE students SET roll_number = 'BBA-24-01', admission_number = 'ADM2024BBA01', email = 'rahul@sias.edu.in' WHERE id = 'STU_BBA_01' AND (roll_number IS NULL OR roll_number = '');")
        cursor.execute("UPDATE students SET roll_number = 'BCA-24-01', admission_number = 'ADM2024BCA01', email = 'fatima@sias.edu.in' WHERE id = 'STU_BCA_01' AND (roll_number IS NULL OR roll_number = '');")
        cursor.execute("UPDATE students SET roll_number = 'BCM-23-01', admission_number = 'ADM2023BCM01', email = 'arjun@sias.edu.in' WHERE id = 'STU_BCOM_01' AND (roll_number IS NULL OR roll_number = '');")
        cursor.execute("UPDATE students SET roll_number = 'BSC-25-01', admission_number = 'ADM2025BSC01', email = 'ananya@sias.edu.in' WHERE id = 'STU_BSC_01' AND (roll_number IS NULL OR roll_number = '');")

    cursor.execute("SELECT COUNT(*) FROM notices;")
    if cursor.fetchone()[0] == 0:
        demo_notices = [
            (
                "End Semester Examination Registration - Nov 2026",
                "Examination",
                "All UG Semester 3 and Semester 5 students must submit their examination registration forms through the college portal. Late fees apply after the deadline.",
                "ALL", "ALL", "3,5",
                "2026-09-20", "2026-10-05",
                "Controller of Examinations Notice #COE/2026/89", "Notice Board", None, 1
            ),
            (
                "BBA S3 Project Submission Guidelines",
                "Academic",
                "Guidelines for S3 Mini-Project submission for BBA students. Hard copies must be signed by project guides and submitted to the department office.",
                "BBA", "Management Studies", "3",
                "2026-09-22", "2026-10-12",
                "Dept of Management Studies Memo #MS/26/14", "PDF", None, 1
            ),
            (
                "Post-Matric Scholarship Renewal",
                "Scholarship",
                "Eligible students can apply for post-matric scholarship renewal on the national scholarship portal. Upload fee receipts and mark lists.",
                "ALL", "ALL", "ALL",
                "2026-09-15", "2026-10-20",
                "Student Welfare Cell Circular #SW/2026/05", "Notice Board", None, 1
            ),
            (
                "Library Book Return Reminder for S3 Students",
                "General",
                "All 3rd semester students who borrowed reference books for midterms must return or renew them before the end of the month.",
                "ALL", "ALL", "3",
                "2026-09-24", "2026-09-30",
                "Central Library Notification", "Notice Board", None, 1
            )
        ]
        cursor.executemany("""
        INSERT INTO notices (title, category, content, target_course, target_department, target_semester, date, deadline, source, source_type, file_path, is_approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, demo_notices)

    cursor.execute("SELECT COUNT(*) FROM events;")
    if cursor.fetchone()[0] == 0:
        demo_events = [
            (
                "SAFI Innovate Tech Fest 2026",
                "Annual inter-collegiate technology fest featuring hackathon, web design competition, and technical quiz.",
                "2026-10-18", "09:30 AM", "Auditorium & Lab 1", "Computer Applications Association",
                "ALL", "ALL", "ALL", "2026-10-14",
                "TechFest Committee Circular", 1
            ),
            (
                "Management Conclave & Case Study Workshop",
                "Interactive workshop on corporate branding and case study competition exclusively for BBA students.",
                "2026-10-08", "10:00 AM", "Seminar Hall A", "Dept of Management Studies",
                "BBA", "Management Studies", "3,5", "2026-10-06",
                "Management Dept Circular", 1
            ),
            (
                "Campus Placement Drive: Infosys & TCS",
                "Pre-placement talk and aptitude test for final year BCA, BSc CS and BCom students.",
                "2026-10-25", "09:00 AM", "Main Auditorium", "Career Guidance & Placement Cell",
                "BCA,BSc Computer Science,BCom", "ALL", "5,6", "2026-10-20",
                "Placement Cell Notice #PL/2026/11", 1
            )
        ]
        cursor.executemany("""
        INSERT INTO events (title, description, date, time, venue, organizer, target_course, target_department, target_semester, registration_deadline, source, is_approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, demo_events)

    cursor.execute("SELECT COUNT(*) FROM timetables;")
    if cursor.fetchone()[0] == 0:
        demo_timetables = [
            # BBA Semester 3 Exam Timetable
            ("BBA", 3, "2026-10-26", "Financial Management", "09:30 AM - 12:30 PM", "Exam Hall 1", 1, None, 2, "End Semester Exam Schedule Nov 2026, Page 2"),
            ("BBA", 3, "2026-10-28", "Marketing Management", "09:30 AM - 12:30 PM", "Exam Hall 1", 1, None, 2, "End Semester Exam Schedule Nov 2026, Page 2"),
            ("BBA", 3, "2026-10-31", "Business Research Methods", "09:30 AM - 12:30 PM", "Exam Hall 2", 1, None, 2, "End Semester Exam Schedule Nov 2026, Page 2"),
            ("BBA", 3, "2026-11-03", "Corporate Governance & Ethics", "09:30 AM - 12:30 PM", "Exam Hall 2", 1, None, 2, "End Semester Exam Schedule Nov 2026, Page 2"),
            
            # BCA Semester 3 Exam Timetable
            ("BCA", 3, "2026-10-26", "Data Structures Using C++", "09:30 AM - 12:30 PM", "Exam Hall 3", 1, None, 3, "End Semester Exam Schedule Nov 2026, Page 3"),
            ("BCA", 3, "2026-10-28", "Database Management Systems", "09:30 AM - 12:30 PM", "Exam Hall 3", 1, None, 3, "End Semester Exam Schedule Nov 2026, Page 3"),
            ("BCA", 3, "2026-10-31", "Financial Accounting & Management", "09:30 AM - 12:30 PM", "Exam Hall 4", 1, None, 3, "End Semester Exam Schedule Nov 2026, Page 3"),
            ("BCA", 3, "2026-11-03", "Software Engineering Principles", "09:30 AM - 12:30 PM", "Exam Hall 4", 1, None, 3, "End Semester Exam Schedule Nov 2026, Page 3"),

            # BCom Semester 3 Exam Timetable
            ("BCom", 3, "2026-10-27", "Advanced Financial Accounting", "09:30 AM - 12:30 PM", "Exam Hall 5", 1, None, 4, "End Semester Exam Schedule Nov 2026, Page 4"),
            ("BCom", 3, "2026-10-29", "Corporate Regulations", "09:30 AM - 12:30 PM", "Exam Hall 5", 1, None, 4, "End Semester Exam Schedule Nov 2026, Page 4"),

            # BBA Semester 3 Regular Class Timetable (is_exam = 0)
            ("BBA", 3, "Monday", "Financial Management", "09:30 AM - 10:30 AM", "Room 204", 0, None, 1, "BBA S3 Class Routine 2026"),
            ("BBA", 3, "Monday", "Marketing Management", "10:30 AM - 11:30 AM", "Room 204", 0, None, 1, "BBA S3 Class Routine 2026"),
            ("BBA", 3, "Tuesday", "Business Research Methods", "09:30 AM - 10:30 AM", "Room 204", 0, None, 1, "BBA S3 Class Routine 2026")
        ]
        cursor.executemany("""
        INSERT INTO timetables (course, semester, day_or_date, subject, time, room, is_exam, document_id, page_number, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, demo_timetables)

    # Seed Departments
    cursor.execute("SELECT COUNT(*) FROM departments;")
    if cursor.fetchone()[0] == 0:
        demo_departments = [
            ("Department of Computer Applications", "Offers undergraduate Bachelor of Computer Application (BCA Honours) approved by AICTE.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Computer Science", "Offers B.Sc. Computer Science Honours and B.Sc. Artificial Intelligence Honours with research.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Management Studies", "Offers BBA Honours and MBA through the PMA SAFI School of Management.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Commerce", "Offers B.Com Honours in Finance, B.Com in Islamic Finance, and M.Com.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Biotechnology", "Offers B.Sc. Biotechnology Honours, M.Sc. General Biotechnology, and Ph.D. in Biotechnology.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Food Technology", "Offers B.Sc. Food Technology Honours and M.Sc. Food Science & Technology.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Microbiology", "Offers B.Sc. Microbiology Honours and M.Sc. Microbiology.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Physics", "Offers B.Sc. Physics Honours with Data Science & AI and B.Sc. B.Ed. Physics.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Psychology", "Offers B.Sc. Psychology Honours and M.Sc. Psychology.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Economics", "Offers B.A. Economics Honours and B.A. B.Ed. Economics.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of English", "Offers B.A. English Honours (Language and Literature) and B.A. B.Ed. English.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Journalism & Mass Communication", "Offers B.A. Multimedia Honours and M.A. Journalism & Mass Communication.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Islamic Studies", "Offers M.A. Islamic Studies and Ph.D. in Islamic Studies.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Social Work", "Offers professional MSW (Master of Social Work) with specialization.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("Department of Education (ITEP)", "Offers 4-Year Integrated Teacher Education Programmes (B.Sc. B.Ed. & B.A. B.Ed.) recognized by NCTE.", "https://sias.edu.in/admission.html", "2026-09-27")
        ]
        cursor.executemany("""
        INSERT INTO departments (name, description, source_url, last_updated)
        VALUES (?, ?, ?, ?);
        """, demo_departments)

    # Seed Programmes
    cursor.execute("SELECT COUNT(*) FROM programmes;")
    if cursor.fetchone()[0] == 0:
        demo_programmes = [
            # 15 UG Programmes
            ("Bachelor of Computer Application (BCA) Honours", "UG", "Department of Computer Applications", "4 Years", "Undergraduate programme in computer applications, programming, and software systems. Approved by AICTE.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Sc. Computer Science Honours", "UG", "Department of Computer Science", "4 Years", "Undergraduate honours programme in computer science and software development.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Sc. Artificial Intelligence Honours", "UG", "Department of Computer Science", "4 Years", "Undergraduate honours programme in AI, machine learning and cognitive systems.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("BBA Honours", "UG", "Department of Management Studies", "4 Years", "8-semester honours programme in business administration and corporate management. Approved by AICTE.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Com Honours (Finance)", "UG", "Department of Commerce", "4 Years", "Honours programme in commerce with specialization in financial accounting and management.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Com Honours (Islamic Finance)", "UG", "Department of Commerce", "4 Years", "Honours programme in commerce specializing in Islamic banking, investments, and ethics.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Sc. Biotechnology Honours", "UG", "Department of Biotechnology", "4 Years", "8-semester honours programme in cellular biology, genetics, and biotechnology.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Sc. Food Technology Honours", "UG", "Department of Food Technology", "4 Years", "Undergraduate degree in food processing, nutrition, quality control, and preservation.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Sc. Microbiology Honours", "UG", "Department of Microbiology", "4 Years", "8-semester honours degree in microbial sciences, medical microbiology, and immunology.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Sc. Physics Honours with Data Science & AI", "UG", "Department of Physics", "4 Years", "Modern honours physics degree integrated with data science and computational modeling.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.Sc. Psychology Honours", "UG", "Department of Psychology", "4 Years", "Undergraduate honours degree in behavioral science, counseling, and mental health.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.A. Economics Honours", "UG", "Department of Economics", "4 Years", "Undergraduate honours degree in economic theory, econometrics, and public policy.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.A. English Honours (Language and Literature)", "UG", "Department of English", "4 Years", "Honours degree in English literary studies, linguistics and critical writing.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.A. Multimedia Honours", "UG", "Department of Journalism & Mass Communication", "4 Years", "Undergraduate degree in digital animation, video production, graphic design and UI/UX.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.A. Public Administration Honours", "UG", "Department of Economics", "4 Years", "Undergraduate honours degree in civil governance, administrative law, and public affairs.", "https://sias.edu.in/admission.html", "2026-09-27"),

            # 8 PG Programmes
            ("MBA (Master of Business Administration)", "PG", "Department of Management Studies", "2 Years", "Flagship postgraduate management programme at PMA SAFI School of Management. AICTE approved.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("M.Com (Finance)", "PG", "Department of Commerce", "2 Years", "Postgraduate degree in corporate finance, taxation, auditing, and financial markets.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("M.Sc. General Biotechnology", "PG", "Department of Biotechnology", "2 Years", "Entrance-based postgraduate master's degree in recombinant DNA technology and bio-research.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("M.Sc. Food Science & Technology", "PG", "Department of Food Technology", "2 Years", "Advanced postgraduate studies in food preservation, food safety standards, and engineering.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("M.Sc. Microbiology", "PG", "Department of Microbiology", "2 Years", "Postgraduate degree in advanced immunology, pathogenic bacteriology, and virology.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("M.Sc. Psychology", "PG", "Department of Psychology", "2 Years", "Postgraduate degree in clinical assessment, counseling, and psychotherapy.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("M.A. Journalism & Mass Communication", "PG", "Department of Journalism & Mass Communication", "2 Years", "Postgraduate degree in broadcast journalism, digital media, and investigative reporting.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("M.A. Islamic Studies", "PG", "Department of Islamic Studies", "2 Years", "Master of Arts in Islamic history, theology, philosophy, and cultural heritage.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("MSW (Master of Social Work)", "PG", "Department of Social Work", "2 Years", "Professional postgraduate degree in community social work and psychiatric health.", "https://sias.edu.in/admission.html", "2026-09-27"),

            # 2 ITEP Programmes
            ("B.Sc. B.Ed. Secondary", "ITEP", "Department of Education (ITEP)", "4 Years", "Integrated Teacher Education Programme in Science (Physics, Chemistry, Zoology, Botany). Recognized by NCTE.", "https://sias.edu.in/admission.html", "2026-09-27"),
            ("B.A. B.Ed. Secondary", "ITEP", "Department of Education (ITEP)", "4 Years", "Integrated Teacher Education Programme in Arts (Economics, English). Recognized by NCTE.", "https://sias.edu.in/admission.html", "2026-09-27"),

            # 2 PhD Programmes
            ("Ph.D. in Biotechnology", "PhD", "Department of Biotechnology", "3-5 Years", "Doctoral research programme recognized by University of Calicut.", "https://sias.edu.in/index.html", "2026-09-27"),
            ("Ph.D. in Islamic Studies", "PhD", "Department of Islamic Studies", "3-5 Years", "Doctoral research programme recognized by University of Calicut.", "https://sias.edu.in/index.html", "2026-09-27")
        ]
        cursor.executemany("""
        INSERT INTO programmes (name, level, department, duration, description, source_url, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?);
        """, demo_programmes)

    # Seed Faculty (HODs)
    cursor.execute("SELECT COUNT(*) FROM faculty;")
    if cursor.fetchone()[0] == 0:
        demo_faculty = [
            ("Dr. Shabeerali P.", "Head of the Department (HOD) & Assistant Professor", "Department of Computer Applications", "https://sias.edu.in/", "2026-09-27"),
            ("Dr. A.K. Haris", "Head of the Department (HOD) & Associate Professor", "Department of Management Studies", "https://sias.edu.in/", "2026-09-27"),
            ("Prof. C.P. Abdul Majeed", "Head of the Department (HOD) & Professor", "Department of Commerce", "https://sias.edu.in/", "2026-09-27"),
            ("Dr. Servin Wesley", "Head of the Department (HOD) & Associate Professor", "Department of Biotechnology", "https://sias.edu.in/", "2026-09-27"),
            ("Dr. K.P. Shanavas", "Head of the Department (HOD) & Assistant Professor", "Department of Food Technology", "https://sias.edu.in/", "2026-09-27"),
            ("Dr. Shiekha S.", "Head of the Department (HOD) & Assistant Professor", "Department of Microbiology", "https://sias.edu.in/", "2026-09-27"),
            ("Prof. P.K. Moosa", "Head of the Department (HOD) & Associate Professor", "Department of English", "https://sias.edu.in/", "2026-09-27"),
            ("Dr. C.H. Thahir", "Head of the Department (HOD) & Assistant Professor", "Department of Economics", "https://sias.edu.in/", "2026-09-27"),
            ("Prof. Abdul Rasheed", "Head of the Department (HOD) & Assistant Professor", "Department of Journalism & Mass Communication", "https://sias.edu.in/", "2026-09-27"),
            ("Dr. P.T. Sreelatha", "Head of the Department (HOD) & Assistant Professor", "Department of Physics", "https://sias.edu.in/", "2026-09-27"),
            ("Prof. Fathima R.", "Head of the Department (HOD) & Assistant Professor", "Department of Psychology", "https://sias.edu.in/", "2026-09-27"),
            ("Dr. K.A. Areekadan", "Head of the Department (HOD) & Associate Professor", "Department of Islamic Studies", "https://sias.edu.in/", "2026-09-27"),
            ("Prof. Jamsheer P.", "Head of the Department (HOD) & Assistant Professor", "Department of Social Work", "https://sias.edu.in/", "2026-09-27")
        ]
        cursor.executemany("""
        INSERT INTO faculty (name, designation, department, profile_url, last_updated)
        VALUES (?, ?, ?, ?, ?);
        """, demo_faculty)

    # Seed Website Pages
    cursor.execute("SELECT COUNT(*) FROM website_pages;")
    if cursor.fetchone()[0] == 0:
        demo_pages = [
            ("https://sias.edu.in/", "SAFI Institute of Advanced Study (Autonomous) - Official Homepage", "Autonomous Arts and Science College with NAAC A++ grade. Established in 2005 by Social Advancement Foundation of India (SAFI). Offers 15 UG, 8 PG, 2 ITEP, and 2 PhD programmes. Granted autonomy by UGC for 10 years (2024-2034).", "2026-09-27"),
            ("https://sias.edu.in/admission.html", "SIAS Admission & Academic Programmes Portal", "Admission portal for 27 academic programmes across Arts, Science, Commerce, Management, Media and AI. Details prospectus, eligibility criteria, status tracking and online application.", "2026-09-27"),
            ("https://sias.edu.in/resources/facilities.html", "SIAS Campus Facilities & ICT Infrastructure", "ICT-enabled classrooms, high-speed Wi-Fi campus, modern computer and science labs, auditorium, seminar halls, sports complex, and hostel facilities.", "2026-09-27"),
            ("https://sias.edu.in/library.html", "Library and Information Centre, SIAS", "Automated central library with Plagiarism CheckerX, Institutional Repository, previous question papers, 9:30 AM to 5:00 PM weekdays, digital information centre.", "2026-09-27"),
            ("https://sias.edu.in/about/index.html", "About SIAS, Vision & Autonomy", "Overview of SAFI Autonomous College, founder trust, vision of educational excellence, UGC autonomous status, and community impact.", "2026-09-27"),
            ("https://sias.edu.in/stdzone/index.html", "Student Support, Equal Opportunity Cell & Scholarships", "Comprehensive advisory scheme, career guidance, placement cell, civil service foundation coaching, remedial coaching, language skills, SC/ST & Equal Opportunity cell, OBC cell, and Internal Complaints Committee.", "2026-09-27")
        ]
        cursor.executemany("""
        INSERT INTO website_pages (url, title, content_summary, last_synced)
        VALUES (?, ?, ?, ?);
        """, demo_pages)

    # Seed Initial Users (Admin & Students)
    cursor.execute("SELECT COUNT(*) FROM users;")
    if cursor.fetchone()[0] == 0:
        from backend.services.auth import hash_password
        admin_email = os.getenv("ADMIN_DEFAULT_EMAIL", "admin@sias.edu.in")
        admin_pass = os.getenv("ADMIN_DEFAULT_PASSWORD", "Admin@Safi2026")
        admin_hash = hash_password(admin_pass)
        student_hash = hash_password("student123")
        now_str = "2026-09-27 21:00:00"

        demo_users = [
            (
                "System Administrator", "ADMIN-01", "ADM_ADMIN_01", admin_email, admin_hash, "ADMIN",
                "ALL", "Administration", 0, "2024-2028", "System Management, Academic Verification", now_str
            ),
            (
                "Rahul Menon", "BBA-24-01", "ADM2024BBA01", "rahul@sias.edu.in", student_hash, "STUDENT",
                "BBA", "Management Studies", 3, "2024-2027", "Marketing, Financial Markets, Case Studies", now_str
            ),
            (
                "Fatima Zahra", "BCA-24-01", "ADM2024BCA01", "fatima@sias.edu.in", student_hash, "STUDENT",
                "BCA", "Computer Applications", 3, "2024-2027", "AI, Python Programming, Web Dev", now_str
            ),
            (
                "Arjun Das", "BCM-23-01", "ADM2023BCM01", "arjun@sias.edu.in", student_hash, "STUDENT",
                "BCom", "Commerce", 5, "2023-2026", "Accounting, Taxation", now_str
            ),
            (
                "Ananya Nair", "BSC-25-01", "ADM2025BSC01", "ananya@sias.edu.in", student_hash, "STUDENT",
                "BSc Computer Science", "Computer Science", 1, "2025-2028", "Algorithms, Robotics", now_str
            )
        ]
        cursor.executemany("""
        INSERT INTO users (name, roll_number, admission_number, email, password_hash, role, course, department, semester, batch, interests, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, demo_users)

    conn.commit()
    conn.close()

    # Index college notices into ChromaDB for semantic retrieval
    try:
        from backend.services.rag import index_document_chunks, get_collection
        col = get_collection()
        res = col.get(where={"doc_type": "notice"}) if col else None
        if not res or not res.get("ids"):
            conn_notices = get_connection()
            cur_notices = conn_notices.cursor()
            cur_notices.execute("SELECT * FROM notices WHERE is_approved = 1;")
            notices = [dict(r) for r in cur_notices.fetchall()]
            conn_notices.close()
            notice_chunks = []
            for n in notices:
                chunk_text = (
                    f"Official Notice: {n['title']}\n"
                    f"Category: {n['category']}\n"
                    f"Date: {n['date']}\n"
                    f"Deadline: {n.get('deadline') or 'None'}\n"
                    f"Target Course: {n['target_course']}\n"
                    f"Target Semester: {n['target_semester']}\n"
                    f"Details: {n['content']}\n"
                    f"Source: {n.get('source', 'Notice Board')}"
                )
                notice_chunks.append({
                    "id": f"notice_{n['id']}",
                    "text": chunk_text,
                    "metadata": {
                        "doc_id": n["id"],
                        "doc_title": n["title"],
                        "course": n["target_course"],
                        "semester": 0 if n["target_semester"] == "ALL" else int(str(n["target_semester"]).split(",")[0]) if n["target_semester"] else 0,
                        "department": n["target_department"],
                        "doc_type": "notice",
                        "page": 1,
                        "source_url": "https://sias.edu.in/"
                    }
                })
            if notice_chunks:
                index_document_chunks(notice_chunks)
    except Exception as e:
        print(f"Notice Chroma indexing note: {e}")

    # Seed initial sample unanswered question in learning_queue if empty
    conn_q = get_connection()
    cur_q = conn_q.cursor()
    cur_q.execute("SELECT COUNT(*) FROM learning_queue;")
    if cur_q.fetchone()[0] == 0:
        cur_q.execute("""
        INSERT INTO learning_queue (question, user_id, status, timestamp)
        VALUES ('Is there a bus facility from Nilambur to campus?', 'STU_BBA_01', 'UNANSWERED', '2026-09-27 21:00:00');
        """)
        conn_q.commit()
    conn_q.close()

if __name__ == "__main__":
    init_db()
    seed_demo_data()
    print("Database initialized and demo data seeded successfully.")



