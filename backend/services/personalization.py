from typing import List, Dict, Any, Optional

def is_item_relevant_to_student(student: Dict[str, Any], item: Dict[str, Any]) -> bool:
    """
    Deterministic rule engine matching student attributes (course, department, semester)
    against target attributes of an item (notice, event, document).
    General items with target 'ALL' or None are always relevant.
    """
    if not student:
        return True
        
    s_course = str(student.get("course", "")).strip().upper()
    s_dept = str(student.get("department", "")).strip().upper()
    s_sem = str(student.get("semester", "")).strip()

    # 1. Course Filter
    target_course = str(item.get("target_course", "ALL") or "ALL").strip().upper()
    if target_course and target_course != "ALL":
        # Split multiple courses: "BBA, BCA" or "BBA/BCA"
        courses = [c.strip().replace(".", "") for c in target_course.replace("/", ",").split(",")]
        clean_s_course = s_course.replace(".", "")
        if not any(c in clean_s_course or clean_s_course in c for c in courses):
            return False

    # 2. Semester Filter
    target_sem = str(item.get("target_semester", "ALL") or "ALL").strip().upper()
    if target_sem and target_sem != "ALL":
        # Check if s_sem is present in e.g. "3", "3,5", "S3", "SEM 3"
        sem_tokens = [tok.strip().lstrip("S").lstrip("SEM").strip() for tok in target_sem.replace("/", ",").split(",")]
        if s_sem not in sem_tokens:
            return False

    # 3. Department Filter
    target_dept = str(item.get("target_department", "ALL") or "ALL").strip().upper()
    if target_dept and target_dept != "ALL":
        # Department check
        if s_dept != target_dept and target_dept not in s_dept and s_dept not in target_dept:
            return False

    return True

def filter_items_for_student(student: Dict[str, Any], items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Returns only items that match the student profile according to personalization rules.
    """
    return [item for item in items if is_item_relevant_to_student(student, item)]
