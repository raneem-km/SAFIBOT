import re
from typing import List, Dict, Any, Optional

try:
    import pymupdf
    HAS_PYMUPDF = True
except Exception:
    HAS_PYMUPDF = False

try:
    import pypdf
    HAS_PYPDF = True
except Exception:
    HAS_PYPDF = False
from typing import List, Dict, Any, Optional

def extract_text_by_pages(pdf_path: str) -> List[Dict[str, Any]]:
    pages_data = []
    if HAS_PYMUPDF:
        try:
            doc = pymupdf.open(pdf_path)
            for page_idx, page in enumerate(doc):
                pages_data.append({"page": page_idx + 1, "text": page.get_text("text").strip()})
            doc.close()
            return pages_data
        except Exception:
            pass
    if HAS_PYPDF:
        try:
            reader = pypdf.PdfReader(pdf_path)
            for page_idx, page in enumerate(reader.pages):
                pages_data.append({"page": page_idx + 1, "text": (page.extract_text() or "").strip()})
            return pages_data
        except Exception:
            pass
    return pages_data

def chunk_pdf_pages(
    pages_data: List[Dict[str, Any]],
    doc_id: int,
    doc_title: str,
    course: str = "ALL",
    semester: Optional[int] = None,
    department: str = "ALL",
    doc_type: str = "syllabus",
    chunk_size: int = 500,
    chunk_overlap: int = 80
) -> List[Dict[str, Any]]:
    """
    Splits page text into chunks while preserving page number and academic metadata.
    """
    chunks = []
    
    for page_item in pages_data:
        page_num = page_item["page"]
        text = page_item["text"]
        if not text:
            continue
            
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        
        current_chunk = ""
        for p in paragraphs:
            if len(current_chunk) + len(p) < chunk_size:
                current_chunk += ("\n\n" + p if current_chunk else p)
            else:
                if current_chunk:
                    chunks.append({
                        "id": f"doc_{doc_id}_p{page_num}_c{len(chunks)}",
                        "text": current_chunk,
                        "metadata": {
                            "doc_id": doc_id,
                            "doc_title": doc_title,
                            "page": page_num,
                            "course": course or "ALL",
                            "semester": semester or 0,
                            "department": department or "ALL",
                            "doc_type": doc_type
                        }
                    })
                current_chunk = p
                
        if current_chunk:
            chunks.append({
                "id": f"doc_{doc_id}_p{page_num}_c{len(chunks)}",
                "text": current_chunk,
                "metadata": {
                    "doc_id": doc_id,
                    "doc_title": doc_title,
                    "page": page_num,
                    "course": course or "ALL",
                    "semester": semester or 0,
                    "department": department or "ALL",
                    "doc_type": doc_type
                }
            })
            
    return chunks

def extract_timetable_rows_from_text(pages_data: List[Dict[str, Any]], doc_id: int, doc_title: str) -> List[Dict[str, Any]]:
    """
    Heuristic/rule-based extractor for timetable lines from PDF pages.
    Detects course (BBA, BCA, BCom, BSc), semester, date/day, time, subject, room.
    """
    rows = []
    course_pattern = re.compile(r'\b(BBA|BCA|B\.Com|BCom|BSc|BA)\b', re.IGNORECASE)
    sem_pattern = re.compile(r'\b(?:Semester|Sem|S)\s*([1-6])\b', re.IGNORECASE)
    date_pattern = re.compile(r'(\d{4}-\d{2}-\d{2}|\d{2}[/-]\d{2}[/-]\d{4}|\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Monday|Tuesday|Wednesday|Thursday|Friday|Saturday)\b)', re.IGNORECASE)
    time_pattern = re.compile(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?\s*[-–toTO]+\s*\d{1,2}:\d{2}\s*(?:AM|PM)?)', re.IGNORECASE)
    
    for page_item in pages_data:
        page_num = page_item["page"]
        lines = page_item["text"].split("\n")
        
        current_course = None
        current_sem = None
        
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
                
            # Check if line indicates course or semester
            c_match = course_pattern.search(line_str)
            s_match = sem_pattern.search(line_str)
            if c_match:
                current_course = c_match.group(1).upper().replace(".", "")
            if s_match:
                current_sem = int(s_match.group(1))
                
            # Check for schedule line: Date/Day + Subject + Time
            d_match = date_pattern.search(line_str)
            t_match = time_pattern.search(line_str)
            
            if d_match and current_course and current_sem:
                day_or_date = d_match.group(1)
                time_str = t_match.group(1) if t_match else "09:30 AM - 12:30 PM"
                
                # Subject is line content excluding date and time
                cleaned_subj = line_str.replace(day_or_date, "").replace(time_str if t_match else "", "").strip(" |-:,")
                if not cleaned_subj or len(cleaned_subj) < 3:
                    cleaned_subj = "Scheduled Examination"
                    
                rows.append({
                    "course": current_course,
                    "semester": current_sem,
                    "day_or_date": day_or_date,
                    "subject": cleaned_subj,
                    "time": time_str,
                    "room": "Exam Hall",
                    "is_exam": 1,
                    "document_id": doc_id,
                    "page_number": page_num,
                    "source": f"{doc_title}, Page {page_num}"
                })
                
    return rows
