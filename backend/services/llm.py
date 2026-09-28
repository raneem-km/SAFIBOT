import os
import re
import json
from typing import Dict, Any, List, Optional
import httpx

# Configuration from environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.5-flash" if GEMINI_API_KEY else "gpt-4o-mini")

def classify_query_intent(query: str) -> str:
    """
    Classifies user message to decide whether to query structured SQLite or ChromaDB RAG.
    """
    q = query.lower().strip()
    
    # Next exam / exam timetable
    if any(k in q for k in ["next exam", "exam date", "when is my exam", "when are my exams", "my exams", "exam timetable", "examination timetable", "date sheet"]):
        return "exam_timetable"
    
    # Class timetable
    if any(k in q for k in ["class timetable", "routine", "lecture", "when is my class", "schedule for today", "monday class"]):
        return "class_timetable"
        
    # General timetable query
    if "timetable" in q:
        return "exam_timetable"

    # Deadlines / tasks this week / urgent notices
    if any(k in q for k in ["what do i need to do", "deadline", "deadlines", "due date", "due this week", "pending submission"]):
        return "deadlines_notices"

    # Events / workshops / fests
    if any(k in q for k in ["event", "events", "workshop", "fest", "hackathon", "seminar", "webinar", "conclave"]):
        return "events"

    # Notices / announcements
    if any(k in q for k in ["notice", "notices", "announcement", "circular"]):
        return "notices"

    # Website Structured Questions (Programmes, Departments, HODs, Counts)
    if any(k in q for k in [
        "how many ug", "how many pg", "how many programmes", "how many courses",
        "how many departments", "what departments", "list departments", "departments are there",
        "who is the hod", "head of the department", "hod of",
        "programmes offered", "programmes are offered", "courses offered", "courses are offered",
        "programmes does", "courses in", "offered by the", "offered by",
        "programmes available", "programmes in", "courses available", "what programmes", "which programmes",
        "what courses", "available in", "list all b.sc", "b.sc programmes", "b.com programmes", "b.a. programmes"
    ]) or (("programme" in q or "course" in q) and any(d in q for d in [
        "computer application", "computer science", "management", "commerce",
        "biotechnology", "microbiology", "food technology", "physics", "psychology",
        "economics", "english", "journalism", "multimedia", "islamic", "social work"
    ])):
        return "website_structured"

    # Website Semantic / RAG Questions (Admission, Facilities, Library, Support)
    if any(k in q for k in [
        "admission", "prospectus", "eligibility", "how to apply", "application form",
        "facilities", "hostel", "canteen", "sports", "wi-fi", "wifi",
        "library", "plagiarism", "library hours", "reading room",
        "student support", "equal opportunity", "civil service coaching", "scholarship",
        "about sias", "about the college", "autonomous status", "naac"
    ]):
        return "website_rag"

    # Show document request (e.g., "show me the syllabus", "give me the pdf")
    if any(k in q for k in ["show me the syllabus", "show syllabus", "download syllabus", "academic calendar pdf", "regulations pdf"]):
        return "document_request"

    # Syllabus explanation / RAG
    if any(k in q for k in ["explain", "unit", "module", "chapter", "syllabus", "topics in", "what is covered in", "curriculum"]):
        return "syllabus_rag"

    return "general"

def extract_announcement_with_rules(text: str) -> Dict[str, Any]:
    """
    High-accuracy deterministic fallback extractor for WhatsApp-style announcements.
    Handles dates, times, venues, target courses, and organizers.
    """
    extracted = {
        "type": "event",
        "title": "College Announcement",
        "description": text.strip(),
        "date": "2026-10-15",
        "time": "10:00 AM",
        "venue": "Campus Seminar Hall",
        "organizer": "Department Faculty",
        "target_course": "ALL",
        "target_department": "ALL",
        "target_semester": "ALL",
        "registration_deadline": "",
        "source": "WhatsApp Announcement"
    }
    
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    if lines:
        first_line = lines[0]
        # Clean title from common prefixes
        title_clean = re.sub(r'^(announcement|notice|event|urgent|reminder)\s*[:\-–]\s*', '', first_line, flags=re.IGNORECASE)
        extracted["title"] = title_clean[:80]
        
    # Detect title if containing 'workshop', 'seminar', 'fest', 'session'
    t_match = re.search(r'([A-Za-z0-9\s\+\#]+(?:Workshop|Fest|Seminar|Webinar|Conclave|Session|Drive|Competition|Hackathon))', text, re.IGNORECASE)
    if t_match:
        extracted["title"] = t_match.group(1).strip()

    # Time extraction
    time_match = re.search(r'\b(\d{1,2}(?::\d{2})?\s*(?:AM|PM|am|pm))\b|\bat\s+(\d{1,2}(?::\d{2})?)\b', text)
    if time_match:
        extracted["time"] = (time_match.group(1) or (time_match.group(2) + " PM")).strip()

    # Venue extraction
    venue_match = re.search(r'\b(?:in|at|venue:?)\s+((?:Room|Lab|Hall|Auditorium|Campus|Seminar\s*Hall)\s*[A-Za-z0-9]*)', text, re.IGNORECASE)
    if venue_match:
        extracted["venue"] = venue_match.group(1).strip()

    # Date extraction (e.g., 'tomorrow', 'Friday', '2026-10-12', '12th Oct')
    date_match = re.search(r'(\b\d{4}-\d{2}-\d{2}\b|\b\d{1,2}(?:st|nd|rd|th)?\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*|\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|tomorrow|today)\b)', text, re.IGNORECASE)
    if date_match:
        extracted["date"] = date_match.group(1).capitalize()

    # Target course eligibility
    courses_found = []
    for c in ["BCA", "BBA", "BCOM", "BSC", "BA", "MCA", "MBA"]:
        if re.search(rf'\b{c}\b', text, re.IGNORECASE):
            courses_found.append(c)
    if courses_found:
        extracted["target_course"] = ",".join(courses_found)

    # Semester eligibility
    sem_match = re.findall(r'\b(?:S|Semester|Sem)\s*([1-6])\b', text, re.IGNORECASE)
    if sem_match:
        extracted["target_semester"] = ",".join(sorted(list(set(sem_match))))

    # Registration deadline
    deadline_match = re.search(r'(?:registration closes|last date|deadline)\s*(?:is|on|before)?\s*([A-Za-z0-9\s,]+?(?:\.|\n|$))', text, re.IGNORECASE)
    if deadline_match:
        extracted["registration_deadline"] = deadline_match.group(1).strip()

    # Organizer
    org_match = re.search(r'(?:organized by|organizer:?)\s*([A-Za-z0-9\s]+?(?:\.|\n|$))', text, re.IGNORECASE)
    if org_match:
        extracted["organizer"] = org_match.group(1).strip()
    elif "computer" in text.lower() or "bca" in text.lower():
        extracted["organizer"] = "Department of Computer Applications"
    elif "management" in text.lower() or "bba" in text.lower():
        extracted["organizer"] = "Department of Management Studies"

    return extracted

def extract_announcement(text: str) -> Dict[str, Any]:
    """
    Extracts structured fields from WhatsApp announcement using configured LLM,
    with automatic fallback to deterministic extraction.
    """
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={GEMINI_API_KEY}"
            prompt = f"""You are a college information extractor for SafiBot.
Extract structured details from the following announcement.
Return ONLY valid JSON matching this schema:
{{
    "type": "event",
    "title": "string",
    "description": "brief summary",
    "date": "YYYY-MM-DD or day/date string",
    "time": "HH:MM AM/PM or time string",
    "venue": "venue name or online",
    "organizer": "organizing department/club",
    "target_course": "BCA or BBA or ALL",
    "target_department": "Computer Science or Management Studies or ALL",
    "target_semester": "e.g. 3 or ALL",
    "registration_deadline": "string or empty",
    "source": "WhatsApp Announcement"
}}

Announcement text:
{text}
"""
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = httpx.post(url, json=payload, timeout=12.0)
            if res.status_code == 200:
                data = res.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                # Parse JSON block
                clean_json = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if clean_json:
                    return json.loads(clean_json.group(0))
        except Exception as e:
            print(f"Gemini extraction failed, falling back to rule engine: {e}")

    # Fallback to robust deterministic extractor
    return extract_announcement_with_rules(text)

RAG_STOPWORDS = {
    "is", "there", "a", "an", "the", "are", "was", "were", "what", "when", "where",
    "which", "who", "whom", "how", "why", "do", "does", "did", "have", "has", "had",
    "can", "could", "will", "would", "shall", "should", "may", "might", "must", "to",
    "from", "in", "on", "at", "by", "for", "with", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "up", "down", "out", "off",
    "over", "under", "again", "further", "then", "once", "here", "all", "any", "both",
    "each", "few", "more", "most", "other", "some", "such", "no", "nor", "not", "only",
    "own", "same", "so", "than", "too", "very", "just", "now", "college", "safi", "sias",
    "autonomous", "campus", "please", "tell", "me", "give", "show", "explain", "detail",
    "details", "information", "provide", "directly", "available", "listed", "offers",
    "offered"
}

def generate_rag_response(
    question: str,
    chunks: List[Dict[str, Any]],
    student_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates a grounded answer based strictly on retrieved chunks.
    Never hallucinates ungrounded college facts.
    """
    FALLBACK_MSG = "I couldn't find that information in the current SafiBot knowledge base."

    if not chunks:
        return {
            "answer": FALLBACK_MSG,
            "sources": []
        }

    # Format context and sources
    context_blocks = []
    sources = []
    seen_sources = set()
    verified_faq_chunk = None

    for i, chunk in enumerate(chunks):
        meta = chunk.get("metadata") or {}
        doc_type = meta.get("doc_type", "document")
        if doc_type == "verified_faq":
            verified_faq_chunk = chunk

        doc_title = meta.get("doc_title") or meta.get("page_title") or "College Document"
        page = meta.get("page", 1)
        source_key = f"{doc_title}_p{page}_{meta.get('source_url', '')}"
        
        context_blocks.append(f"--- Document: {doc_title} (Page {page}) ---\n{chunk.get('text', '')}\n")
        
        if source_key not in seen_sources:
            seen_sources.add(source_key)
            src_item = {
                "title": doc_title,
                "document_type": doc_type,
                "details": f"Page {page}" if page else ""
            }
            if page:
                try:
                    src_item["page"] = int(page)
                except Exception:
                    pass
            if meta.get("source_url"):
                src_item["url"] = meta.get("source_url")
            sources.append(src_item)

    joined_context = "\n".join(context_blocks)
    student_course = student_context.get("course", "College Student") if student_context else "College Student"
    student_sem = student_context.get("semester", "") if student_context else ""

    # 1. Prioritize verified knowledge FAQ from administrative learning queue
    if verified_faq_chunk:
        verified_text = verified_faq_chunk.get("text", "").strip()
        match_ans = re.search(r'Verified Answer:\s*(.+?)(?:\nSource:|$)', verified_text, re.DOTALL)
        clean_ans = match_ans.group(1).strip() if match_ans else verified_text
        v_meta = verified_faq_chunk.get("metadata") or {}
        v_source = [{
            "title": v_meta.get("doc_title", "Verified College FAQ"),
            "document_type": "verified_faq",
            "details": v_meta.get("source_url", "SIAS Continuous Knowledge Improvement")
        }]
        return {
            "answer": clean_ans,
            "sources": v_source
        }

    # 2. Strict grounding & hallucination prevention:
    # Check whether core query keywords exist in the retrieved excerpts
    clean_q = re.sub(r'[^a-zA-Z0-9\s]', ' ', question.lower())
    q_tokens = [w for w in clean_q.split() if len(w) >= 3 and w not in RAG_STOPWORDS]
    if q_tokens:
        ctx_lower = joined_context.lower()
        matching_tokens = [t for t in q_tokens if t in ctx_lower]
        match_ratio = len(matching_tokens) / len(q_tokens)
        if match_ratio < 0.5:
            return {
                "answer": FALLBACK_MSG,
                "sources": []
            }

    # 3. Call LLM if API Key is configured
    if GEMINI_API_KEY:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{LLM_MODEL}:generateContent?key={GEMINI_API_KEY}"
            prompt = f"""You are SafiBot, the official college academic assistant for SAFI Autonomous College.
The user is a {student_course} (Semester {student_sem}) student.
Answer the student's question SOLELY based on the provided document excerpts below.
DO NOT invent or extrapolate facts not present in the text.
If the information to answer the question is NOT found in the excerpts, respond EXACTLY:
"{FALLBACK_MSG}"
Always refer to the specific unit, topic, or document section referenced.
Keep your explanation clear, well-structured, and helpful for academic study.

DOCUMENT EXCERPTS:
{joined_context}

STUDENT QUESTION:
{question}
"""
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            res = httpx.post(url, json=payload, timeout=15.0)
            if res.status_code == 200:
                data = res.json()
                ans_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if "couldn't find that information" in ans_text.lower() or "not found" in ans_text.lower():
                    return {"answer": FALLBACK_MSG, "sources": []}
                return {
                    "answer": ans_text,
                    "sources": sources
                }
        except Exception as e:
            print(f"Gemini RAG synthesis error: {e}, using local synthesis.")

    # 4. High-quality local synthesis from retrieved chunks
    best_chunk = chunks[0]
    best_text = (best_chunk.get("text") or "").strip()
    primary_source = sources[0] if sources else None
    source_citation = ""
    if primary_source:
        if primary_source.get("page"):
            source_citation = f" (Source: {primary_source['title']}, Page {primary_source['page']})"
        else:
            source_citation = f" (Source: {primary_source['title']})"

    explanation = f"Based on the official curriculum document{source_citation}:\n\n{best_text}"
    if len(chunks) > 1 and chunks[1].get("text"):
        secondary_text = (chunks[1].get("text") or "").strip()
        explanation += f"\n\n**Additional Details:**\n{secondary_text}"

    return {
        "answer": explanation,
        "sources": sources
    }
