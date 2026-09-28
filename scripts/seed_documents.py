import os
import shutil
from backend.database.db import get_connection, init_db, seed_demo_data
from backend.services.pdf_processor import extract_text_by_pages, chunk_pdf_pages
from backend.services.rag import index_document_chunks

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "backend", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

DOCS_TO_INGEST = [
    {
        "file": "data/syllabus/BBA_Semester_3_Syllabus.pdf",
        "title": "BBA Semester 3 Official Curriculum & Syllabus",
        "doc_type": "syllabus",
        "course": "BBA",
        "semester": 3,
        "department": "Management Studies",
        "source": "SAFI Board of Studies - Management"
    },
    {
        "file": "data/syllabus/BCA_Semester_3_Syllabus.pdf",
        "title": "BCA Semester 3 Official Curriculum & Syllabus",
        "doc_type": "syllabus",
        "course": "BCA",
        "semester": 3,
        "department": "Computer Applications",
        "source": "SAFI Board of Studies - Computer Applications"
    },
    {
        "file": "data/timetables/SAFI_End_Semester_Exam_Timetable_Nov2026.pdf",
        "title": "Master End Semester Examination Schedule - Nov 2026",
        "doc_type": "exam_timetable",
        "course": "ALL",
        "semester": 3,
        "department": "ALL",
        "source": "Office of the Controller of Examinations"
    },
    {
        "file": "data/academic/SAFI_Academic_Calendar_2026_27.pdf",
        "title": "Academic Calendar & Key Dates 2026-27",
        "doc_type": "academic_calendar",
        "course": "ALL",
        "semester": None,
        "department": "ALL",
        "source": "Academic Affairs Committee"
    }
]

def seed_documents():
    init_db()
    seed_demo_data()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    for item in DOCS_TO_INGEST:
        src_path = item["file"]
        if not os.path.exists(src_path):
            continue
            
        cursor.execute("SELECT id FROM documents WHERE title = ?;", (item["title"],))
        existing = cursor.fetchone()
        if existing:
            print(f"Already ingested: {item['title']}")
            continue
            
        # Use canonical original PDF directly without creating duplicates
        abs_file_path = os.path.abspath(src_path)
        pages_data = extract_text_by_pages(abs_file_path)
        total_pages = len(pages_data)
        
        cursor.execute("""
        INSERT INTO documents (title, document_type, course, semester, department, file_path, source, upload_date, total_pages)
        VALUES (?, ?, ?, ?, ?, ?, ?, DATE('now'), ?);
        """, (
            item["title"], item["doc_type"], item["course"], item["semester"],
            item["department"], abs_file_path, item["source"], total_pages
        ))
        doc_id = cursor.lastrowid
        conn.commit()
        
        # Chunk and index to ChromaDB
        chunks = chunk_pdf_pages(
            pages_data=pages_data,
            doc_id=doc_id,
            doc_title=item["title"],
            course=item["course"],
            semester=item["semester"],
            department=item["department"],
            doc_type=item["doc_type"]
        )
        count = index_document_chunks(chunks)
        print(f"Indexed {count} chunks for {item['title']} (Doc ID: {doc_id})")
        
    conn.close()

if __name__ == "__main__":
    seed_documents()
