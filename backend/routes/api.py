import os
import shutil
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query, Depends, status
from fastapi.responses import FileResponse

from backend.database.db import get_connection
from backend.models.schemas import (
    StudentResponse, NoticeResponse, NoticeCreate,
    EventResponse, EventCreate, DocumentResponse,
    TimetableRowResponse, TimetableRowCreate,
    AnnouncementExtractRequest, ExtractedAnnouncement,
    ChatRequest, ChatResponse, ChatSource,
    ProgrammeResponse, DepartmentResponse, FacultyResponse,
    WebsitePageResponse, WebsiteSyncResponse,
    UserRegisterRequest, UserLoginRequest, UserResponse,
    AuthTokenResponse, DeadlineResponse,
    FeedbackCreate, FeedbackResponse, LearningQueueItem, ResolveQuestionRequest
)
from backend.services.pdf_processor import (
    extract_text_by_pages, chunk_pdf_pages, extract_timetable_rows_from_text
)
from backend.services.rag import index_document_chunks, search_chunks
from backend.services.personalization import is_item_relevant_to_student, filter_items_for_student
from backend.services.timetable import (
    get_timetable_rows, get_next_exam_for_student, format_timetable_as_text
)
from backend.services.llm import (
    classify_query_intent, extract_announcement, generate_rag_response
)
from backend.services.website_scraper import sync_college_website
from backend.services.retrieval_service import execute_college_retrieval, format_website_source, FALLBACK_UNKNOWN_MSG
from backend.services.auth import (
    hash_password, verify_password, create_access_token,
    get_current_user, get_optional_user, require_admin
)

router = APIRouter(prefix="/api")

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ----------------- Authentication & Profile -----------------
@router.post("/auth/register", response_model=AuthTokenResponse)
def register_student(req: UserRegisterRequest):
    """
    Registers a new student.
    - Required fields: Full Name, Roll Number, Admission Number, Email, Password, Course, Department, Semester, Batch, Interests.
    - Passwords are securely hashed with bcrypt (never stored as plain text).
    - Stores roll_number and admission_number in both SQLite users and students tables.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Check if email or admission_number already exists
    cursor.execute("""
    SELECT id, email, admission_number FROM users 
    WHERE LOWER(email) = ? OR LOWER(admission_number) = ?;
    """, (req.email.strip().lower(), req.admission_number.strip().lower()))
    existing = cursor.fetchone()
    if existing:
        conn.close()
        raise HTTPException(
            status_code=400,
            detail="A user with this email or admission number is already registered."
        )
        
    pw_hash = hash_password(req.password)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    roll_num = req.roll_number.strip() if req.roll_number else req.admission_number.strip()
    
    # 1. Insert into users table
    cursor.execute("""
    INSERT INTO users (name, roll_number, admission_number, email, password_hash, role, course, department, semester, batch, interests, created_at)
    VALUES (?, ?, ?, ?, ?, 'STUDENT', ?, ?, ?, ?, ?, ?);
    """, (
        req.name.strip(), roll_num, req.admission_number.strip(),
        req.email.strip().lower(), pw_hash, req.course.strip(), req.department.strip(),
        req.semester, req.batch.strip(), req.interests.strip() if req.interests else "", now_str
    ))
    user_id = cursor.lastrowid
    
    # 2. Insert into students table (structured / private store)
    stu_id = f"STU_{req.admission_number.strip()}"
    cursor.execute("""
    INSERT OR REPLACE INTO students (id, name, roll_number, admission_number, email, course, department, semester, batch, interests)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        stu_id, req.name.strip(), roll_num, req.admission_number.strip(),
        req.email.strip().lower(), req.course.strip(), req.department.strip(),
        req.semester, req.batch.strip(), req.interests.strip() if req.interests else ""
    ))
    
    conn.commit()
    cursor.execute("""
    SELECT id, name, roll_number, admission_number, email, role, course, department, semester, batch, interests, created_at
    FROM users WHERE id = ?;
    """, (user_id,))
    user_row = dict(cursor.fetchone())
    conn.close()
    
    token = create_access_token({
        "sub": str(user_id),
        "role": "STUDENT",
        "name": user_row["name"],
        "email": user_row["email"]
    })
    return AuthTokenResponse(access_token=token, user=UserResponse(**user_row))

@router.post("/auth/login", response_model=AuthTokenResponse)
def login_student(req: UserLoginRequest):
    """
    Student login endpoint.
    Accepts identifier (Email OR Admission Number) + Password.
    Returns signed JWT access token and student user profile.
    """
    ident = req.identifier.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, roll_number, admission_number, email, password_hash, role, course, department, semester, batch, interests, created_at
    FROM users 
    WHERE LOWER(email) = ? OR LOWER(admission_number) = ?;
    """, (ident, ident))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email/admission number or password."
        )
        
    user_data = dict(row)
    del user_data["password_hash"]
    token = create_access_token({
        "sub": str(user_data["id"]),
        "role": user_data["role"],
        "name": user_data["name"],
        "email": user_data["email"]
    })
    return AuthTokenResponse(access_token=token, user=UserResponse(**user_data))

@router.post("/auth/admin/login", response_model=AuthTokenResponse)
def login_admin(req: UserLoginRequest):
    """
    Administrative login endpoint.
    Requires role == 'ADMIN'.
    """
    ident = req.identifier.strip().lower()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id, name, roll_number, admission_number, email, password_hash, role, course, department, semester, batch, interests, created_at
    FROM users 
    WHERE (LOWER(email) = ? OR LOWER(admission_number) = ?) AND role = 'ADMIN';
    """, (ident, ident))
    row = cursor.fetchone()
    conn.close()
    
    if not row or not verify_password(req.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials or non-admin account."
        )
        
    user_data = dict(row)
    del user_data["password_hash"]
    token = create_access_token({
        "sub": str(user_data["id"]),
        "role": "ADMIN",
        "name": user_data["name"],
        "email": user_data["email"]
    })
    return AuthTokenResponse(access_token=token, user=UserResponse(**user_data))

@router.get("/auth/me", response_model=UserResponse)
def get_auth_me(current_user: dict = Depends(get_current_user)):
    """Returns currently authenticated user profile."""
    return UserResponse(**current_user)

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: dict = Depends(get_current_user)):
    """Returns current student/admin detailed profile."""
    return UserResponse(**current_user)

# ----------------- Student Profile & Dashboard Helpers -----------------
def find_student_profile(student_id: Optional[str]) -> Optional[dict]:
    """
    Robust student profile resolver.
    Matches student by:
      - 'guest' (returns campus guest visitor profile)
      - students.id (e.g. 'STU_BBA_01', 'STU_217292')
      - students.admission_number (e.g. 'ADM2024BBA01', '217292')
      - students.email (e.g. 'ajsal@gmail.com')
      - users.id (auto-increment integer e.g. 7 or '7')
      - users.admission_number / email
    """
    if not student_id:
        return None
        
    s_id = str(student_id).strip()
    if s_id.lower() == "guest":
        return {
            "id": "guest",
            "name": "Guest Visitor",
            "roll_number": "GUEST",
            "admission_number": "GUEST",
            "email": "guest@sias.edu.in",
            "course": "ALL",
            "department": "Campus Visitor",
            "semester": 1,
            "batch": "2024-2027",
            "interests": "College Programmes, Facilities & Admissions",
            "role": "GUEST"
        }
        
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Search in students table
    cursor.execute("""
        SELECT * FROM students 
        WHERE id = ? 
           OR admission_number = ? 
           OR LOWER(email) = ? 
           OR id = ?;
    """, (s_id, s_id, s_id.lower(), f"STU_{s_id}"))
    row = cursor.fetchone()
    if row:
        conn.close()
        return dict(row)
        
    # 2. Search in users table
    cursor.execute("""
        SELECT * FROM users 
        WHERE id = ? 
           OR admission_number = ? 
           OR LOWER(email) = ?;
    """, (s_id, s_id, s_id.lower()))
    user_row = cursor.fetchone()
    if user_row:
        u = dict(user_row)
        adm = u.get("admission_number") or ""
        em = u.get("email") or ""
        # Check if linked row exists in students
        cursor.execute("SELECT * FROM students WHERE admission_number = ? OR LOWER(email) = ?;", (adm, em.lower()))
        s_row = cursor.fetchone()
        conn.close()
        if s_row:
            return dict(s_row)
        else:
            return {
                "id": f"STU_{adm}" if adm else str(u["id"]),
                "name": u["name"],
                "roll_number": u.get("roll_number", ""),
                "admission_number": adm,
                "email": em,
                "course": u.get("course", "ALL"),
                "department": u.get("department", "ALL"),
                "semester": u.get("semester", 1),
                "batch": u.get("batch", ""),
                "interests": u.get("interests", "")
            }

    conn.close()
    return None

def build_dashboard_data(student_profile: dict) -> dict:
    """
    Builds structured, personalized dashboard payload for a student or guest visitor.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Notices
    cursor.execute("SELECT * FROM notices WHERE is_approved = 1 ORDER BY date DESC;")
    all_notices = [dict(r) for r in cursor.fetchall()]
    personalized_notices = filter_items_for_student(student_profile, all_notices)
    
    # 2. Events
    cursor.execute("SELECT * FROM events WHERE is_approved = 1 ORDER BY date ASC;")
    all_events = [dict(r) for r in cursor.fetchall()]
    personalized_events = filter_items_for_student(student_profile, all_events)
    
    # 3. Deadlines
    deadlines = [n for n in personalized_notices if n.get("deadline")]
    event_deadlines = [e for e in personalized_events if e.get("registration_deadline")]
    
    # 4. Next Exam
    course = student_profile.get("course") or "ALL"
    sem = student_profile.get("semester") or 1
    next_exam = get_next_exam_for_student(course, sem)
    
    # 5. Documents
    cursor.execute("SELECT * FROM documents ORDER BY upload_date DESC;")
    all_docs = [dict(r) for r in cursor.fetchall()]
    relevant_docs = [
        d for d in all_docs
        if d.get("course") == "ALL" or d.get("course") == course
    ]
    
    conn.close()
    
    return {
        "student": student_profile,
        "notices": personalized_notices[:5],
        "events": personalized_events[:5],
        "deadlines": deadlines[:5],
        "event_deadlines": event_deadlines[:5],
        "next_exam": next_exam,
        "documents": relevant_docs[:5]
    }

@router.get("/dashboard/me")
def get_my_dashboard(current_user: dict = Depends(get_current_user)):
    """
    Returns personalized dashboard data for the authenticated student.
    Uses student's course, semester, department from SQLite.
    """
    return build_dashboard_data(current_user)

@router.get("/deadlines", response_model=List[DeadlineResponse])
def get_deadlines(course: Optional[str] = None, semester: Optional[int] = None):
    """
    Returns deadlines consolidated from notices and events via SQLite deadlines view.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM deadlines ORDER BY due_date ASC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if course:
        rows = [r for r in rows if r["target_course"] in ["ALL", course]]
    if semester:
        rows = [r for r in rows if r["target_semester"] == "ALL" or str(semester) in str(r["target_semester"]).split(",")]
        
    return rows

# ----------------- Continuous Knowledge Improvement (Feedback & Learning Queue) -----------------
@router.post("/feedback", response_model=FeedbackResponse)
def submit_feedback(fb: FeedbackCreate, current_user: Optional[dict] = Depends(get_optional_user)):
    """
    Submits student feedback (Helpful 👍 or Not Helpful 👎).
    If marked Not Helpful, automatically queues question for administrative review.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user_id = current_user.get("admission_number") or current_user.get("id") if current_user else "anonymous"

    cursor.execute("""
    INSERT INTO feedback (user_id, question, answer, source, feedback, comment, timestamp)
    VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (user_id, fb.question, fb.answer, fb.source or "", fb.feedback, fb.comment or "", now_str))
    new_id = cursor.lastrowid

    # If student found the answer not helpful, flag to learning_queue if not already there
    if fb.feedback == "not_helpful":
        cursor.execute("SELECT id FROM learning_queue WHERE question = ? AND status = 'UNANSWERED';", (fb.question.strip(),))
        if not cursor.fetchone():
            cursor.execute("""
            INSERT INTO learning_queue (question, user_id, status, timestamp)
            VALUES (?, ?, 'UNANSWERED', ?);
            """, (fb.question.strip(), user_id, now_str))

    conn.commit()
    cursor.execute("SELECT * FROM feedback WHERE id = ?;", (new_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return FeedbackResponse(**row)

@router.get("/admin/learning-queue", response_model=List[LearningQueueItem])
def get_learning_queue(admin_user: dict = Depends(require_admin)):
    """
    Returns questions in the learning queue for administrative review.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM learning_queue ORDER BY timestamp DESC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return [LearningQueueItem(**r) for r in rows]

@router.post("/admin/learning-queue/{item_id}/resolve")
def resolve_learning_queue_item(
    item_id: int,
    req: ResolveQuestionRequest,
    admin_user: dict = Depends(require_admin)
):
    """
    Administrative approval of new verified college answer.
    Updates learning_queue and indexes into ChromaDB knowledge base.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM learning_queue WHERE id = ?;", (item_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Question not found in learning queue.")
        
    question_text = row["question"]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    UPDATE learning_queue 
    SET status = 'RESOLVED', verified_answer = ?, added_source = ?, resolved_at = ?, resolved_by = ?
    WHERE id = ?;
    """, (req.verified_answer, req.added_source or "Admin Verified Knowledge", now_str, admin_user.get("email", "admin"), item_id))
    conn.commit()
    conn.close()

    # Index into ChromaDB as verified FAQ chunk for immediate semantic recall
    if req.index_to_chroma:
        try:
            qa_chunk = (
                f"College Information FAQ:\n"
                f"Question: {question_text}\n"
                f"Verified Answer: {req.verified_answer}\n"
                f"Source: {req.added_source or 'College Administration'}"
            )
            index_document_chunks([{
                "id": f"learning_faq_{item_id}",
                "text": qa_chunk,
                "metadata": {
                    "doc_id": item_id,
                    "doc_title": f"Verified FAQ: {question_text[:35]}",
                    "course": "ALL",
                    "semester": 0,
                    "department": "ALL",
                    "doc_type": "verified_faq",
                    "page": 1,
                    "source_url": "https://sias.edu.in/"
                }
            }])
        except Exception as e:
            print(f"Error indexing resolved answer to Chroma: {e}")

    return {
        "status": "success",
        "message": f"Question resolved and knowledge verified successfully.",
        "id": item_id
    }

@router.post("/admin/learning-queue/{item_id}/ignore")
def ignore_learning_queue_item(item_id: int, admin_user: dict = Depends(require_admin)):
    """
    Marks question as ignored / irrelevant.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE learning_queue SET status = 'IGNORED' WHERE id = ?;", (item_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "Question marked as ignored."}

@router.get("/admin/feedback")
def get_admin_feedback(admin_user: dict = Depends(require_admin)):
    """
    Returns all student feedback records and analytics.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM feedback ORDER BY timestamp DESC LIMIT 50;")
    rows = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT feedback, COUNT(*) as count FROM feedback GROUP BY feedback;")
    counts = dict(cursor.fetchall())
    conn.close()
    return {"feedback": rows, "stats": counts}


# ----------------- Students -----------------
@router.get("/students", response_model=List[StudentResponse])
def get_students():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM students;")
    students = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return students

@router.get("/students/{student_id}", response_model=StudentResponse)
def get_student(student_id: str):
    student = find_student_profile(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return StudentResponse(**student)

# ----------------- Dashboard -----------------
@router.get("/dashboard/{student_id}")
def get_student_dashboard(student_id: str, current_user: Optional[dict] = Depends(get_optional_user)):
    user_dict = current_user if isinstance(current_user, dict) else None
    s_id = str(student_id).strip()
    if s_id.lower() == "me" and user_dict:
        student = user_dict
    else:
        student = find_student_profile(s_id)
        if not student and user_dict:
            student = user_dict
            
    if not student:
        # Graceful fallback to guest profile so the dashboard never crashes with 404
        student = find_student_profile("guest")
        
    return build_dashboard_data(student)

# ----------------- Notices -----------------
@router.get("/notices", response_model=List[NoticeResponse])
def get_notices(student_id: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM notices WHERE is_approved = 1 ORDER BY date DESC;")
    notices = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if student_id:
        student = find_student_profile(student_id)
        if student:
            notices = filter_items_for_student(student, notices)
            
    return notices

@router.post("/notices", response_model=NoticeResponse)
def create_notice(notice: NoticeCreate, admin_user: dict = Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO notices (title, category, content, target_course, target_department, target_semester, date, deadline, source, source_type, file_path, is_approved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        notice.title, notice.category, notice.content,
        notice.target_course or "ALL", notice.target_department or "ALL", notice.target_semester or "ALL",
        notice.date, notice.deadline, notice.source, notice.source_type, notice.file_path, notice.is_approved
    ))
    new_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM notices WHERE id = ?;", (new_id,))
    row = dict(cursor.fetchone())
    conn.close()

    # Index into ChromaDB for college knowledge
    try:
        chunk_text = (
            f"Official Notice: {row['title']}\n"
            f"Category: {row['category']}\n"
            f"Date: {row['date']}\n"
            f"Deadline: {row.get('deadline') or 'None'}\n"
            f"Target: {row['target_course']} Sem {row['target_semester']}\n"
            f"Details: {row['content']}\n"
            f"Source: {row.get('source', 'Notice Board')}"
        )
        index_document_chunks([{
            "id": f"notice_{new_id}",
            "text": chunk_text,
            "metadata": {
                "doc_id": new_id,
                "doc_title": row["title"],
                "course": row["target_course"],
                "semester": 0 if row["target_semester"] == "ALL" else int(str(row["target_semester"]).split(",")[0]) if row["target_semester"] else 0,
                "department": row["target_department"],
                "doc_type": "notice",
                "page": 1,
                "source_url": "https://sias.edu.in/"
            }
        }])
    except Exception as e:
        print(f"Notice indexing error: {e}")

    return row

# ----------------- Events -----------------
@router.get("/events", response_model=List[EventResponse])
def get_events(student_id: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM events WHERE is_approved = 1 ORDER BY date ASC;")
    events = [dict(r) for r in cursor.fetchall()]
    conn.close()
    
    if student_id:
        student = find_student_profile(student_id)
        if student:
            events = filter_items_for_student(student, events)
            
    return events

@router.post("/events", response_model=EventResponse)
def create_event(event: EventCreate, admin_user: dict = Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO events (title, description, date, time, venue, organizer, target_course, target_department, target_semester, registration_deadline, source, is_approved)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        event.title, event.description, event.date, event.time, event.venue,
        event.organizer, event.target_course or "ALL", event.target_department or "ALL",
        event.target_semester or "ALL", event.registration_deadline, event.source, event.is_approved
    ))
    new_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM events WHERE id = ?;", (new_id,))
    row = dict(cursor.fetchone())
    conn.close()
    return row

# ----------------- Timetable -----------------
@router.get("/timetable", response_model=List[TimetableRowResponse])
def get_timetable(
    course: str = Query(..., description="Student course e.g. BBA, BCA"),
    semester: int = Query(..., description="Semester number e.g. 3"),
    is_exam: Optional[int] = Query(None, description="1 for exam, 0 for class timetable")
):
    return get_timetable_rows(course=course, semester=semester, is_exam=is_exam)

@router.post("/timetable", response_model=TimetableRowResponse)
def add_timetable_row(row: TimetableRowCreate, admin_user: dict = Depends(require_admin)):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO timetables (course, semester, day_or_date, subject, time, room, is_exam, document_id, page_number, source)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        row.course, row.semester, row.day_or_date, row.subject, row.time,
        row.room, row.is_exam, row.document_id, row.page_number, row.source
    ))
    new_id = cursor.lastrowid
    conn.commit()
    cursor.execute("SELECT * FROM timetables WHERE id = ?;", (new_id,))
    res = dict(cursor.fetchone())
    conn.close()
    return res

# ----------------- Documents & PDF Upload -----------------
@router.get("/documents", response_model=List[DocumentResponse])
def get_documents():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM documents ORDER BY upload_date DESC;")
    docs = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return docs

@router.get("/documents/{doc_id}/file")
def get_document_file(doc_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT file_path, title FROM documents WHERE id = ?;", (doc_id,))
    row = cursor.fetchone()
    conn.close()
    if not row or not os.path.exists(row["file_path"]):
        raise HTTPException(status_code=404, detail="Document file not found")
    return FileResponse(row["file_path"], filename=os.path.basename(row["file_path"]))

@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    document_type: str = Form("syllabus"),  # syllabus, exam_timetable, class_timetable, academic_calendar, regulations
    course: str = Form("ALL"),
    semester: Optional[int] = Form(None),
    department: str = Form("ALL"),
    source: Optional[str] = Form("Admin Upload"),
    admin_user: dict = Depends(require_admin)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF documents are supported.")
        
    safe_filename = f"{os.path.splitext(file.filename)[0]}_{os.urandom(4).hex()}.pdf"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # 1. Extract text and page structure with PyMuPDF
    pages_data = extract_text_by_pages(file_path)
    total_pages = len(pages_data)
    
    # 2. Record Document in SQLite
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO documents (title, document_type, course, semester, department, file_path, source, upload_date, total_pages)
    VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'), ?);
    """, (
        title, document_type, course or "ALL", semester, department or "ALL",
        file_path, source or title, total_pages
    ))
    doc_id = cursor.lastrowid
    conn.commit()
    
    # 3. Index into ChromaDB
    chunks = chunk_pdf_pages(
        pages_data=pages_data,
        doc_id=doc_id,
        doc_title=title,
        course=course or "ALL",
        semester=semester,
        department=department or "ALL",
        doc_type=document_type
    )
    indexed_count = index_document_chunks(chunks)
    
    # 4. If this is an exam or class timetable, extract structured rows
    if document_type in ["exam_timetable", "class_timetable"]:
        extracted_rows = extract_timetable_rows_from_text(pages_data, doc_id, title)
        for r in extracted_rows:
            cursor.execute("""
            INSERT INTO timetables (course, semester, day_or_date, subject, time, room, is_exam, document_id, page_number, source)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                r["course"], r["semester"], r["day_or_date"], r["subject"], r["time"],
                r["room"], 1 if document_type == "exam_timetable" else 0,
                doc_id, r["page_number"], r["source"]
            ))
        conn.commit()
        
    cursor.execute("SELECT * FROM documents WHERE id = ?;", (doc_id,))
    saved_doc = dict(cursor.fetchone())
    conn.close()
    
    return saved_doc

# ----------------- Admin Announcement Extraction & Approval -----------------
@router.post("/admin/extract-announcement", response_model=ExtractedAnnouncement)
def extract_announcement_route(req: AnnouncementExtractRequest, admin_user: dict = Depends(require_admin)):
    """
    Extracts structured fields from WhatsApp announcement.
    Admin reviews before publishing.
    """
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Announcement text is empty.")
    extracted = extract_announcement(req.text)
    return extracted

@router.post("/admin/publish-announcement")
def publish_announcement(announcement: ExtractedAnnouncement, admin_user: dict = Depends(require_admin)):
    """
    Approves and officially saves the extracted announcement as an event or notice.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if announcement.type == "notice":
        cursor.execute("""
        INSERT INTO notices (title, category, content, target_course, target_department, target_semester, date, deadline, source, source_type, is_approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
        """, (
            announcement.title, "Announcement", announcement.description or announcement.title,
            announcement.target_course or "ALL", announcement.target_department or "ALL",
            announcement.target_semester or "ALL", announcement.date or "2026-10-01",
            announcement.registration_deadline or None, announcement.source or "Admin Approved Announcement",
            "WhatsApp Announcement"
        ))
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()

        # Also index notice into ChromaDB for college knowledge
        try:
            chunk_text = (
                f"Official Notice: {announcement.title}\n"
                f"Target Course: {announcement.target_course or 'ALL'}\n"
                f"Target Semester: {announcement.target_semester or 'ALL'}\n"
                f"Deadline: {announcement.registration_deadline or 'None'}\n"
                f"Content: {announcement.description or announcement.title}\n"
                f"Source: {announcement.source or 'Admin Approved Announcement'}"
            )
            index_document_chunks([{
                "id": f"notice_{item_id}",
                "text": chunk_text,
                "metadata": {
                    "doc_id": item_id,
                    "doc_title": announcement.title,
                    "course": announcement.target_course or "ALL",
                    "semester": 0 if not announcement.target_semester or announcement.target_semester == "ALL" else int(str(announcement.target_semester).split(",")[0]),
                    "department": announcement.target_department or "ALL",
                    "doc_type": "notice",
                    "page": 1,
                    "source_url": "https://sias.edu.in/"
                }
            }])
        except Exception as e:
            print(f"Notice indexing error: {e}")
    else:
        cursor.execute("""
        INSERT INTO events (title, description, date, time, venue, organizer, target_course, target_department, target_semester, registration_deadline, source, is_approved)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1);
        """, (
            announcement.title, announcement.description or announcement.title,
            announcement.date or "2026-10-15", announcement.time or "10:00 AM",
            announcement.venue or "Campus", announcement.organizer or "College",
            announcement.target_course or "ALL", announcement.target_department or "ALL",
            announcement.target_semester or "ALL", announcement.registration_deadline or None,
            announcement.source or "Admin Approved Announcement"
        ))
        item_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
    return {
        "status": "success",
        "message": f"Announcement successfully published as {announcement.type} (ID: {item_id})",
        "id": item_id
    }

# ----------------- College Website Ingestion -----------------
@router.post("/admin/sync-website", response_model=WebsiteSyncResponse)
def sync_website(admin_user: dict = Depends(require_admin)):
    """
    Admin-controlled synchronization of approved public SIAS website pages.
    """
    res = sync_college_website()
    return res

@router.get("/programmes", response_model=List[ProgrammeResponse])
def get_programmes(level: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if level:
        cursor.execute("SELECT * FROM programmes WHERE UPPER(level) = ? ORDER BY name ASC;", (level.upper(),))
    else:
        cursor.execute("SELECT * FROM programmes ORDER BY level DESC, name ASC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@router.get("/departments", response_model=List[DepartmentResponse])
def get_departments():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM departments ORDER BY name ASC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@router.get("/faculty", response_model=List[FacultyResponse])
def get_faculty(department: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if department:
        cursor.execute("SELECT * FROM faculty WHERE LOWER(department) LIKE ? ORDER BY name ASC;", (f"%{department.lower()}%",))
    else:
        cursor.execute("SELECT * FROM faculty ORDER BY department ASC, name ASC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

@router.get("/website-pages", response_model=List[WebsitePageResponse])
def get_website_pages():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM website_pages ORDER BY id ASC;")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

# ----------------- Chatbot Endpoint -----------------
@router.post("/chat", response_model=ChatResponse)
def handle_chat(req: ChatRequest, current_user: Optional[dict] = Depends(get_optional_user)):
    """
    Unified intelligent chatbot endpoint:
    - Identifies student context from authenticated user or request
    - Routes to structured SQLite queries or ChromaDB RAG
    - Never hallucinates facts
    - Always provides source citations
    """
    # 1. Resolve Student Context
    student = None
    if req.student_id:
        student = find_student_profile(req.student_id)
    user_dict = current_user if isinstance(current_user, dict) else None
    if not student and user_dict:
        student = user_dict
            
    course = (req.course or (student.get("course") if student else "BBA")).strip()
    semester = req.semester or (student.get("semester") if student else 3)
    department = req.department or (student.get("department") if student else "Management Studies")
    
    def respond(**kwargs) -> ChatResponse:
        resp = ChatResponse(**kwargs)
        try:
            log_conn = get_connection()
            log_cur = log_conn.cursor()
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            u_id = current_user.get("admission_number") or current_user.get("id") if current_user else (req.student_id or "anonymous")
            st_name = student.get("name") if student else "Guest"
            log_cur.execute("""
            INSERT INTO chat_history (user_id, student_name, course, semester, query, intent, answer, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (u_id, st_name, course, semester, req.message, resp.query_type, resp.answer, now_str))

            # Continuous Knowledge Improvement: auto-add unanswered questions
            is_unknown = (
                "couldn't find that information" in resp.answer.lower() or
                "could not find that information" in resp.answer.lower()
            )
            if is_unknown:
                log_cur.execute("SELECT id FROM learning_queue WHERE question = ? AND status = 'UNANSWERED';", (req.message.strip(),))
                if not log_cur.fetchone():
                    log_cur.execute("""
                    INSERT INTO learning_queue (question, user_id, status, timestamp)
                    VALUES (?, ?, 'UNANSWERED', ?);
                    """, (req.message.strip(), u_id, now_str))
            log_conn.commit()
            log_conn.close()
        except Exception as log_err:
            print(f"Chat logging error: {log_err}")
        return resp

    # 2. Classify User Intent
    intent = classify_query_intent(req.message)
    
    # 3. Handle by Intent
    conn = get_connection()
    cursor = conn.cursor()
    
    if intent == "exam_timetable":
        rows = get_timetable_rows(course=course, semester=semester, is_exam=1)
        if not rows:
            conn.close()
            return respond(
                answer=f"No scheduled exams were found in the official exam timetable for {course} Semester {semester}.",
                query_type="exam_timetable",
                data=[],
                sources=[]
            )
            
        formatted_table = format_timetable_as_text(rows, title=f"{course} Semester {semester} Examination Schedule")
        sources = [
            ChatSource(
                title=r.get("source", "Official Examination Schedule"),
                page=r.get("page_number", 1),
                document_type="exam_timetable",
                details=f"{r['subject']} ({r['day_or_date']})"
            )
            for r in rows if r.get("source")
        ]
        conn.close()
        return respond(
            answer=f"Here is your official examination timetable:\n\n{formatted_table}",
            query_type="exam_timetable",
            data=rows,
            sources=sources[:3]
        )

    elif intent == "class_timetable":
        rows = get_timetable_rows(course=course, semester=semester, is_exam=0)
        if not rows:
            rows = get_timetable_rows(course=course, semester=semester)
            
        if not rows:
            conn.close()
            return respond(
                answer=f"No regular class routine was found for {course} Semester {semester}.",
                query_type="class_timetable",
                data=[],
                sources=[]
            )
            
        formatted_table = format_timetable_as_text(rows, title=f"{course} Semester {semester} Class Routine")
        conn.close()
        return respond(
            answer=f"Here is your class routine:\n\n{formatted_table}",
            query_type="class_timetable",
            data=rows,
            sources=[ChatSource(title=f"{course} S{semester} Routine", document_type="class_timetable")]
        )

    elif intent == "events":
        cursor.execute("SELECT * FROM events WHERE is_approved = 1 ORDER BY date ASC;")
        all_events = [dict(r) for r in cursor.fetchall()]
        student_obj = student or {"course": course, "semester": semester, "department": department}
        rel_events = filter_items_for_student(student_obj, all_events)
        conn.close()
        
        if not rel_events:
            return respond(
                answer=f"There are currently no upcoming events specifically targetted to {course} Semester {semester}.",
                query_type="events",
                data=[],
                sources=[]
            )
            
        lines = [f"### Relevant Events for {course} (Semester {semester})"]
        for e in rel_events:
            lines.append(f"- **{e['title']}**\n  - **Date & Time:** {e['date']} at {e['time']}\n  - **Venue:** {e['venue']}\n  - **Organizer:** {e['organizer']}" + (f"\n  - **Reg. Deadline:** {e['registration_deadline']}" if e.get('registration_deadline') else ""))
            
        return respond(
            answer="\n".join(lines),
            query_type="events",
            data=rel_events,
            sources=[ChatSource(title=e.get("source", "College Event Circular"), document_type="event") for e in rel_events[:2]]
        )

    elif intent in ["deadlines_notices", "notices"]:
        cursor.execute("SELECT * FROM notices WHERE is_approved = 1 ORDER BY date DESC;")
        all_notices = [dict(r) for r in cursor.fetchall()]
        student_obj = student or {"course": course, "semester": semester, "department": department}
        rel_notices = filter_items_for_student(student_obj, all_notices)
        conn.close()
        
        target_list = rel_notices if rel_notices else all_notices
        if intent == "deadlines_notices":
            deadlines = [n for n in target_list if n.get("deadline")]
            target_list = deadlines if deadlines else target_list
            header = f"### Upcoming Deadlines & Important Notices ({course})"
        else:
            header = f"### Latest Official College News & Announcements ({course})"
            
        if not target_list:
            return respond(
                answer=f"There are currently no active notices or announcements for {course} Semester {semester}.",
                query_type=intent,
                data=[],
                sources=[]
            )
            
        lines = [header]
        for n in target_list[:4]:
            category_tag = f"[{n.get('category', 'Notice').upper()}]"
            deadline_str = f" | **Deadline:** {n['deadline']}" if n.get("deadline") else ""
            lines.append(f"- **{category_tag} {n['title']}**\n  - {n['content']}\n  - **Date:** {n.get('date', 'Recent')}{deadline_str}\n  - **Reference:** {n.get('source', 'Official Notice Board')}")
            
        return respond(
            answer="\n".join(lines),
            query_type=intent,
            data=target_list,
            sources=[ChatSource(title=n.get("source", "Official Notice Board"), document_type="notice", details=f"{n['title']} ({n.get('date', 'Recent')})") for n in target_list[:3]]
        )

    elif intent in ["website_structured", "website_rag", "website_hybrid"]:
        conn.close()
        retrieval_res = execute_college_retrieval(req.message, student)
        sources = [ChatSource(**s) for s in retrieval_res.get("sources", [])]
        return respond(
            answer=retrieval_res["final_answer"],
            query_type=retrieval_res["detected_intent"],
            data=retrieval_res.get("retrieved_records", []),
            sources=sources
        )

    elif intent == "document_request":
        cursor.execute("SELECT * FROM documents WHERE course = ? OR course = 'ALL' ORDER BY upload_date DESC;", (course,))
        docs = [dict(r) for r in cursor.fetchall()]
        conn.close()
        
        if not docs:
            return respond(
                answer=f"No academic documents have been uploaded for {course} yet.",
                query_type="document_request",
                data=[],
                sources=[]
            )
            
        lines = [f"### Academic Documents for {course}:"]
        for d in docs:
            lines.append(f"- **{d['title']}** ({d['document_type'].upper()}) - Total Pages: {d.get('total_pages', 1)}")
            
        return respond(
            answer="\n".join(lines),
            query_type="document_request",
            data=docs,
            sources=[ChatSource(title=d["title"], document_type=d["document_type"]) for d in docs]
        )

    else:
        # Default / Syllabus RAG with fallback to website knowledge
        conn.close()
        student_obj = student or {"course": course, "semester": semester, "department": department}
        target_doc_type = "syllabus" if any(w in req.message.lower() for w in ["syllabus", "curriculum", "unit", "module"]) else None
        retrieved_chunks = search_chunks(
            query=req.message,
            course=course,
            semester=semester,
            doc_type=target_doc_type,
            top_k=4
        )
        rag_res = generate_rag_response(req.message, retrieved_chunks, student_obj)
        if "couldn't find that information" in rag_res["answer"].lower():
            # Fallback to college website retrieval
            web_fallback = execute_college_retrieval(req.message, student_obj)
            if "couldn't find that information" not in web_fallback["final_answer"].lower():
                sources = [ChatSource(**s) for s in web_fallback.get("sources", [])]
                return respond(
                    answer=web_fallback["final_answer"],
                    query_type=web_fallback["detected_intent"],
                    data=web_fallback.get("retrieved_records", []),
                    sources=sources
                )
            return respond(
                answer=FALLBACK_UNKNOWN_MSG,
                query_type="unknown_fallback",
                data=[],
                sources=[]
            )
        
        return respond(
            answer=rag_res["answer"],
            query_type="rag_syllabus",
            data={"retrieved_chunks_count": len(retrieved_chunks)},
            sources=[ChatSource(**s) for s in rag_res.get("sources", [])]
        )

# ----------------- Diagnostic Test Endpoint (Section 4) -----------------
@router.post("/chat/diagnose")
@router.post("/website/test-retrieval")
def test_retrieval_diagnostic(req: ChatRequest, current_user: Optional[dict] = Depends(get_optional_user)):
    """
    Dedicated diagnostic test endpoint as required by Section 4:
    Question
    ↓
    Detected intent
    ↓
    Database query / retrieval method
    ↓
    Retrieved records/chunks
    ↓
    Source URLs
    ↓
    Final LLM answer
    """
    student = None
    if req.student_id:
        student = find_student_profile(req.student_id)
    user_dict = current_user if isinstance(current_user, dict) else None
    if not student and user_dict:
        student = user_dict

    result = execute_college_retrieval(req.message, student)

    # Print clear development log trace
    print(f"\n[DIAGNOSTIC TEST RETRIEVAL TRACE]")
    print(f"Question: {result['question']}")
    print(f"Detected Intent: {result['detected_intent']}")
    print(f"Retrieval Method: {result['retrieval_method']}")
    print(f"Query Executed: {result['query_executed']}")
    print(f"Retrieved Records: {len(result['retrieved_records']) if isinstance(result['retrieved_records'], list) else 'Dict'}")
    print(f"Retrieved Chunks: {len(result['retrieved_chunks'])}")
    print(f"Source URLs: {result['source_urls']}")
    print(f"Final Answer Preview:\n{result['final_answer'][:150]}...\n")

    return result

