from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union

class StudentBase(BaseModel):
    id: str
    name: str
    roll_number: Optional[str] = ""
    admission_number: Optional[str] = ""
    email: Optional[str] = ""
    course: str
    department: str
    semester: int
    batch: str
    interests: Optional[str] = ""

class StudentResponse(StudentBase):
    pass

class NoticeBase(BaseModel):
    title: str
    category: str
    content: str
    target_course: Optional[str] = "ALL"
    target_department: Optional[str] = "ALL"
    target_semester: Optional[str] = "ALL"
    date: str
    deadline: Optional[str] = None
    source: Optional[str] = "Notice Board"
    source_type: Optional[str] = "Notice Board"
    file_path: Optional[str] = None
    is_approved: Optional[int] = 1

class NoticeCreate(NoticeBase):
    pass

class NoticeResponse(NoticeBase):
    id: int

class EventBase(BaseModel):
    title: str
    description: str
    date: str
    time: str
    venue: str
    organizer: str
    target_course: Optional[str] = "ALL"
    target_department: Optional[str] = "ALL"
    target_semester: Optional[str] = "ALL"
    registration_deadline: Optional[str] = None
    source: Optional[str] = "Announcement"
    is_approved: Optional[int] = 1

class EventCreate(EventBase):
    pass

class EventResponse(EventBase):
    id: int

class DocumentBase(BaseModel):
    title: str
    document_type: str  # syllabus, exam_timetable, class_timetable, academic_calendar, regulations
    course: Optional[str] = "ALL"
    semester: Optional[Any] = None
    department: Optional[str] = "ALL"
    file_path: str
    source: Optional[str] = None
    upload_date: str
    total_pages: Optional[int] = 1

class DocumentResponse(DocumentBase):
    id: int

class TimetableRowBase(BaseModel):
    course: str
    semester: int
    day_or_date: str
    subject: str
    time: str
    room: str
    is_exam: Optional[int] = 1
    document_id: Optional[int] = None
    page_number: Optional[int] = None
    source: Optional[str] = None

class TimetableRowCreate(TimetableRowBase):
    pass

class TimetableRowResponse(TimetableRowBase):
    id: int

class AnnouncementExtractRequest(BaseModel):
    text: str

class ExtractedAnnouncement(BaseModel):
    type: str = "event"  # "event" or "notice"
    title: str
    description: Optional[str] = ""
    date: Optional[str] = ""
    time: Optional[str] = ""
    venue: Optional[str] = ""
    organizer: Optional[str] = ""
    target_course: Optional[str] = "ALL"
    target_department: Optional[str] = "ALL"
    target_semester: Optional[str] = "ALL"
    registration_deadline: Optional[str] = ""
    source: Optional[str] = "WhatsApp Announcement"

class ChatRequest(BaseModel):
    student_id: Optional[Union[str, int]] = None
    message: str
    course: Optional[str] = None
    semester: Optional[Union[str, int]] = None
    department: Optional[str] = None

class ChatSource(BaseModel):
    title: str
    page: Optional[int] = None
    document_type: Optional[str] = None
    details: Optional[str] = None
    url: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    query_type: str  # "timetable", "exam_timetable", "events", "notices", "rag_syllabus", "rag_document", "website_structured", "website_rag", "general"
    data: Optional[Any] = None
    sources: List[ChatSource] = []

class ProgrammeResponse(BaseModel):
    id: int
    name: str
    level: str
    department: str
    duration: Optional[str] = "3 Years"
    description: Optional[str] = ""
    source_url: Optional[str] = ""
    last_updated: Optional[str] = ""

class DepartmentResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    source_url: Optional[str] = ""
    last_updated: Optional[str] = ""

class FacultyResponse(BaseModel):
    id: int
    name: str
    designation: str
    department: str
    profile_url: Optional[str] = ""
    last_updated: Optional[str] = ""

class WebsitePageResponse(BaseModel):
    id: int
    url: str
    title: str
    content_summary: Optional[str] = ""
    last_synced: Optional[str] = ""

class WebsiteSyncResponse(BaseModel):
    status: str
    pages_synced: int
    programmes_updated: int
    departments_updated: int
    faculty_updated: int
    chunks_indexed: int
    message: str

class UserRegisterRequest(BaseModel):
    name: str
    roll_number: Optional[str] = ""
    admission_number: str
    email: str
    password: str
    course: str
    department: str
    semester: int
    batch: str
    interests: Optional[str] = ""

class UserLoginRequest(BaseModel):
    identifier: str  # email or admission_number
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    roll_number: Optional[str] = ""
    admission_number: Optional[str] = ""
    email: str
    role: str
    course: Optional[str] = ""
    department: Optional[str] = ""
    semester: Optional[int] = None
    batch: Optional[str] = ""
    interests: Optional[str] = ""
    created_at: Optional[str] = ""

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class DeadlineResponse(BaseModel):
    item_type: str
    item_id: int
    title: str
    category: str
    description: str
    due_date: str
    target_course: str
    target_department: str
    target_semester: str
    source: Optional[str] = ""

class FeedbackCreate(BaseModel):
    question: str
    answer: str
    source: Optional[str] = ""
    feedback: str  # 'helpful' or 'not_helpful'
    comment: Optional[str] = ""

class FeedbackResponse(BaseModel):
    id: int
    user_id: Optional[str] = ""
    question: str
    answer: str
    source: Optional[str] = ""
    feedback: str
    comment: Optional[str] = ""
    timestamp: str

class LearningQueueItem(BaseModel):
    id: int
    question: str
    user_id: Optional[str] = ""
    status: str  # 'UNANSWERED', 'RESOLVED', 'IGNORED'
    verified_answer: Optional[str] = None
    added_source: Optional[str] = None
    timestamp: str
    resolved_at: Optional[str] = None
    resolved_by: Optional[str] = None

class ResolveQuestionRequest(BaseModel):
    verified_answer: str
    added_source: Optional[str] = "Admin Verified Answer"
    index_to_chroma: bool = True




