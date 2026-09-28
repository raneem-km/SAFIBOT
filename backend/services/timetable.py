from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.database.db import get_connection

def get_timetable_rows(course: str, semester: int, is_exam: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Retrieves structured timetable rows for a specific course and semester from SQLite.
    Never hallucinates timetable data.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    clean_course = course.strip().upper().replace(".", "")
    
    # Query with LIKE or exact match on course
    if is_exam is not None:
        query = """
        SELECT id, course, semester, day_or_date, subject, time, room, is_exam, document_id, page_number, source
        FROM timetables
        WHERE (UPPER(REPLACE(course, '.', '')) = ? OR UPPER(course) LIKE ?)
          AND semester = ?
          AND is_exam = ?
        ORDER BY day_or_date ASC, time ASC;
        """
        cursor.execute(query, (clean_course, f"%{clean_course}%", semester, is_exam))
    else:
        query = """
        SELECT id, course, semester, day_or_date, subject, time, room, is_exam, document_id, page_number, source
        FROM timetables
        WHERE (UPPER(REPLACE(course, '.', '')) = ? OR UPPER(course) LIKE ?)
          AND semester = ?
        ORDER BY is_exam DESC, day_or_date ASC, time ASC;
        """
        cursor.execute(query, (clean_course, f"%{clean_course}%", semester))
        
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

def get_next_exam_for_student(course: str, semester: int) -> Optional[Dict[str, Any]]:
    """
    Returns the next upcoming examination row for the student.
    """
    exams = get_timetable_rows(course, semester, is_exam=1)
    if not exams:
        return None
        
    # Return the first scheduled exam in chronological order
    return exams[0]

def format_timetable_as_text(rows: List[Dict[str, Any]], title: str = "Timetable") -> str:
    """
    Formats structured rows into a clear, tabular text representation with source citations.
    """
    if not rows:
        return f"No scheduled entries found for this timetable."
        
    output = [f"### {title}"]
    output.append("| Date / Day | Subject | Time | Room |")
    output.append("| --- | --- | --- | --- |")
    for r in rows:
        output.append(f"| {r['day_or_date']} | {r['subject']} | {r['time']} | {r['room']} |")
        
    # Collect unique sources
    sources = list(set([r['source'] for r in rows if r.get('source')]))
    if sources:
        output.append("\n**Source:** " + ", ".join(sources))
        
    return "\n".join(output)
