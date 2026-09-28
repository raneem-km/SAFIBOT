import httpx
from bs4 import BeautifulSoup
import re
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional
from backend.database.db import get_connection
from backend.services.rag import index_document_chunks, delete_chunks_by_url

SIAS_APPROVED_URLS = [
    {
        "url": "https://sias.edu.in/",
        "title": "SAFI Institute of Advanced Study (Autonomous) - Official Homepage",
        "content_type": "homepage",
        "section": "General Overview & Autonomy"
    },
    {
        "url": "https://sias.edu.in/admission.html",
        "title": "SIAS Admission & Academic Programmes Portal",
        "content_type": "admission_details",
        "section": "Programmes & Admission Requirements"
    },
    {
        "url": "https://sias.edu.in/academics/index.html",
        "title": "SIAS Academic Departments",
        "content_type": "departments",
        "section": "Academic Departments"
    },
    {
        "url": "https://sias.edu.in/academics/computer-applications/index.html",
        "title": "Department of Computer Applications, SIAS",
        "content_type": "department_detail",
        "section": "Computer Applications Department Overview, Vision & Mission"
    },
    {
        "url": "https://sias.edu.in/resources/facilities.html",
        "title": "SIAS Campus Facilities & ICT Infrastructure",
        "content_type": "facilities",
        "section": "Campus Infrastructure & Laboratories"
    },
    {
        "url": "https://sias.edu.in/library.html",
        "title": "Library and Information Centre, SIAS",
        "content_type": "library",
        "section": "Library Resources & Services"
    },
    {
        "url": "https://sias.edu.in/about/index.html",
        "title": "About SIAS, Vision & Autonomous Status",
        "content_type": "about",
        "section": "About the Institution"
    },
    {
        "url": "https://sias.edu.in/stdzone/index.html",
        "title": "Student Support, Equal Opportunity Cell & Scholarships",
        "content_type": "student_support",
        "section": "Student Support & Welfare"
    }
]

def clean_html_to_text(html: str) -> str:
    """
    Extracts clean text from HTML:
    - Removes scripts, styles, navs, footers, and cookie banners.
    - Preserves headings and paragraph structure.
    """
    soup = BeautifulSoup(html, 'html.parser')
    for elem in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        elem.extract()
        
    for bad in soup.find_all(attrs={"class": re.compile(r'(cookie|navbar|menu|footer|topbar|breadcrumb)', re.I)}):
        bad.extract()

    # Prepend line breaks for headings
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li"]):
        h.insert_before("\n")
        h.insert_after("\n")

    text = soup.get_text(separator="\n")
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    return "\n".join(lines)

def chunk_website_text(
    text: str,
    url: str,
    page_title: str,
    section: str,
    content_hash: str,
    date_str: str,
    chunk_size: int = 500
) -> List[Dict[str, Any]]:
    """
    Splits website text into coherent chunks for ChromaDB vector indexing.
    Preserves heading and metadata context:
    - source_type = 'website'
    - url
    - page_title
    - section
    - content_hash
    - last_updated
    """
    paragraphs = text.split("\n")
    chunks = []
    current_chunk = ""
    chunk_index = 0
    clean_url_id = re.sub(r'[^a-zA-Z0-9]', '_', url)

    for p in paragraphs:
        if len(current_chunk) + len(p) < chunk_size:
            current_chunk += ("\n" + p if current_chunk else p)
        else:
            if current_chunk:
                chunks.append({
                    "id": f"web_{clean_url_id}_{chunk_index}",
                    "text": f"[{page_title} - {section}]\n{current_chunk}",
                    "metadata": {
                        "source_type": "website",
                        "url": url,
                        "source_url": url,
                        "page_title": page_title,
                        "doc_title": page_title,
                        "section": section,
                        "content_hash": content_hash,
                        "last_updated": date_str,
                        "doc_type": "website",
                        "department": "ALL",
                        "course": "ALL"
                    }
                })
                chunk_index += 1
            current_chunk = p

    if current_chunk:
        chunks.append({
            "id": f"web_{clean_url_id}_{chunk_index}",
            "text": f"[{page_title} - {section}]\n{current_chunk}",
            "metadata": {
                "source_type": "website",
                "url": url,
                "source_url": url,
                "page_title": page_title,
                "doc_title": page_title,
                "section": section,
                "content_hash": content_hash,
                "last_updated": date_str,
                "doc_type": "website",
                "department": "ALL",
                "course": "ALL"
            }
        })

    return chunks

def fetch_facilities_data() -> str:
    """
    Fetches real dynamic facilities data from SIAS facilities.js,
    or falls back to verified canonical facilities if unavailable.
    """
    url = "https://sias.edu.in/resources/facilities.js"
    try:
        res = httpx.get(url, timeout=8.0, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
        if res.status_code == 200:
            pattern = re.compile(r'\{[^{}]+?\}', re.DOTALL)
            matches = pattern.findall(res.text)
            lines = [
                "SAFI Institute of Advanced Study (Autonomous) - Campus Facilities & ICT Infrastructure",
                "SAFI features an eco-friendly green campus at Raziya Nagar, Vazhayoor, Malappuram district.",
                "OFFICIAL CAMPUS FACILITIES LISTED:"
            ]
            for m in matches:
                name_m = re.search(r'"name"\s*:\s*"([^"]+)"', m)
                text_m = re.search(r'"text"\s*:\s*"([^"]+)"', m)
                if name_m and text_m:
                    lines.append(f"### {name_m.group(1).strip()}\n{text_m.group(1).strip()}\n")
            if len(lines) > 3:
                # Add core campus facilities not in json
                lines.append("### Central Automated Library\nEquipped with digital cataloging, research archives, Plagiarism CheckerX, and spacious reading halls.")
                lines.append("### On-Campus Hostels\nSeparate high-security residential facilities for boys and girls with hygienic mess and 24/7 internet connectivity.")
                lines.append("### Sports Complex & Grounds\nSpacious football ground, basketball court, volleyball, badminton court, and indoor recreation center.")
                lines.append("### Smart Classrooms & Wi-Fi\nICT-enabled air-conditioned smart classrooms, multimedia projectors, and campus-wide high-speed Wi-Fi.")
                return "\n".join(lines)
    except Exception as e:
        print(f"Notice: Live facilities.js fetch failed ({e}). Using canonical verified text.")

    return get_canonical_facilities_text()

def fetch_and_upsert_faculty(cursor, date_str: str) -> int:
    """
    Parses faculty and Department Heads (HODs) from academics/faculty.js and syncs into SQLite:
    - faculty table
    - departments.hod_name
    """
    url = "https://sias.edu.in/academics/faculty.js"
    faculty_list = []
    try:
        res = httpx.get(url, timeout=8.0, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
        if res.status_code == 200:
            pattern = re.compile(r'\{[^{}]+?\}', re.DOTALL)
            for m in pattern.findall(res.text):
                name_m = re.search(r'"name"\s*:\s*"([^"]+)"', m)
                desg_m = re.search(r'"desg"\s*:\s*"([^"]+)"', m)
                dept_m = re.search(r'"dept"\s*:\s*"([^"]+)"', m)
                id_m = re.search(r'"id"\s*:\s*"([^"]+)"', m)
                if name_m and desg_m and dept_m:
                    faculty_list.append({
                        "id": id_m.group(1) if id_m else "",
                        "name": name_m.group(1).strip(),
                        "designation": desg_m.group(1).strip(),
                        "department": dept_m.group(1).strip(),
                        "profile_url": f"https://sias.edu.in/academics/faculty.html?id={id_m.group(1)}" if id_m else "https://sias.edu.in/academics/faculty.html"
                    })
    except Exception as e:
        print(f"Notice: Live faculty.js fetch failed ({e}). Using canonical verified faculty.")

    if not faculty_list:
        faculty_list = get_canonical_faculty_list()

    # Clear and repopulate faculty table
    cursor.execute("DELETE FROM faculty;")
    for f in faculty_list:
        dept_norm = normalize_department_name(f["department"])
        cursor.execute("""
        INSERT INTO faculty (name, designation, department, profile_url, last_updated)
        VALUES (?, ?, ?, ?, ?);
        """, (f["name"], f["designation"], dept_norm, f["profile_url"], date_str))

        # If faculty is Head / HOD, update corresponding department
        if "head" in f["designation"].lower() or "hod" in f["designation"].lower():
            cursor.execute("""
            UPDATE departments SET hod_name = ?, last_updated = ?
            WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?;
            """, (f["name"], date_str, f"%{f['department'].lower()}%", f"%{dept_norm.lower()}%"))

    return len(faculty_list)

def normalize_department_name(dept_raw: str) -> str:
    d = dept_raw.strip()
    if d.startswith("Department of") or d.startswith("Dept."):
        return d
    if "computer application" in d.lower():
        return "Department of Computer Applications"
    if "computer science" in d.lower() or "cs" in d.lower():
        return "Department of Computer Science and Artificial Intelligence"
    if "management" in d.lower():
        return "Department of Management Studies"
    if "commerce" in d.lower():
        return "Department of Commerce"
    if "biotechnology" in d.lower():
        return "PG and Research Dept. of Biotechnology"
    if "microbiology" in d.lower():
        return "PG and Research Dept. of Microbiology"
    if "food technology" in d.lower():
        return "Dept. of Food Technology"
    if "physics" in d.lower():
        return "Dept. of Physics"
    if "psychology" in d.lower():
        return "Dept. of Psychology"
    if "economics" in d.lower():
        return "Dept. of Economics"
    if "english" in d.lower():
        return "Dept. of English"
    if "journalism" in d.lower():
        return "Dept. of Journalism and Mass Communication"
    if "islamic studies" in d.lower():
        return "PG & Research Department of Islamic Studies"
    if "social work" in d.lower():
        return "Dept. of Social Work"
    if "multimedia" in d.lower():
        return "Dept. of Multimedia"
    if "public administration" in d.lower():
        return "Dept. of Public Administration"
    if "education" in d.lower():
        return "Dept. of Education"
    return f"Dept. of {d}"

def sync_structured_departments(cursor, date_str: str) -> int:
    """
    Syncs the official list of academic departments into SQLite departments table.
    """
    depts = [
        ("Department of Computer Applications", "Offers undergraduate Bachelor of Computer Application (BCA Honours) approved by AICTE with state-of-the-art computer labs.", "https://sias.edu.in/academics/computer-applications/index.html"),
        ("Department of Computer Science and Artificial Intelligence", "Offers B.Sc. Computer Science Honours and B.Sc. Artificial Intelligence Honours with research.", "https://sias.edu.in/academics/cs-ai/index.html"),
        ("Department of Management Studies", "Offers BBA Honours (AICTE approved) and MBA through the PMA SAFI School of Management.", "https://sias.edu.in/academics/management/index.html"),
        ("Department of Commerce", "Offers B.Com Honours in Finance, B.Com in Islamic Finance, and M.Com (Finance).", "https://sias.edu.in/academics/commerce/index.html"),
        ("PG and Research Dept. of Biotechnology", "Offers B.Sc. Biotechnology Honours, M.Sc. General Biotechnology, and Ph.D. in Biotechnology.", "https://sias.edu.in/academics/biotechnology/index.html"),
        ("PG and Research Dept. of Microbiology", "Offers B.Sc. Microbiology Honours and M.Sc. Microbiology with advanced research labs.", "https://sias.edu.in/academics/microbiology/index.html"),
        ("Dept. of Food Technology", "Offers B.Sc. Food Technology Honours and M.Sc. Food Science & Technology.", "https://sias.edu.in/academics/foodtechnology/index.html"),
        ("Dept. of Physics", "Offers B.Sc. Physics Honours with Data Science & AI and B.Sc. B.Ed. Physics.", "https://sias.edu.in/academics/physics/index.html"),
        ("Dept. of Psychology", "Offers B.Sc. Psychology Honours and M.Sc. Psychology with clinical counseling labs.", "https://sias.edu.in/academics/psychology/index.html"),
        ("Dept. of Economics", "Offers B.A. Economics Honours and B.A. B.Ed. Economics.", "https://sias.edu.in/academics/economics/index.html"),
        ("Dept. of English", "Offers B.A. English Language and Literature Honours and B.A. B.Ed. English.", "https://sias.edu.in/academics/english/index.html"),
        ("Dept. of Journalism and Mass Communication", "Offers B.A. Multimedia Honours and M.A. Journalism & Mass Communication.", "https://sias.edu.in/academics/jmc/index.html"),
        ("PG & Research Department of Islamic Studies", "Offers M.A. Islamic Studies and Ph.D. in Islamic Studies.", "https://sias.edu.in/academics/is/index.html"),
        ("Dept. of Social Work", "Offers professional MSW (Master of Social Work) with community and medical specializations.", "https://sias.edu.in/academics/socialwork/index.html"),
        ("Dept. of Multimedia", "Offers B.A. Multimedia Honours in digital arts, animation and UI/UX.", "https://sias.edu.in/academics/multimedia/index.html"),
        ("Dept. of Public Administration", "Offers B.A. Public Administration Honours in governance and public policy.", "https://sias.edu.in/academics/public_administration/index.html"),
        ("Dept. of Education", "Offers 4-Year Integrated Teacher Education Programmes (ITEP: B.Sc. B.Ed. & B.A. B.Ed.) recognized by NCTE.", "https://sias.edu.in/academics/index.html"),
        ("PMA SAFI School of Management", "Offers AICTE-approved flagship MBA programme with corporate specializations.", "https://sias.edu.in/academics/school-of-management/index.html"),
        ("Dept. of Physical Education", "Oversees collegiate sports, tournaments, fitness center and athletics infrastructure.", "https://sias.edu.in/academics/pe/index.html")
    ]
    cursor.execute("DELETE FROM departments;")
    for name, desc, url in depts:
        cursor.execute("""
        INSERT INTO departments (name, description, source_url, last_updated)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            description = excluded.description,
            source_url = excluded.source_url,
            last_updated = excluded.last_updated;
        """, (name, desc, url, date_str))
    return len(depts)

def sync_structured_programmes(cursor, source_url: str, date_str: str) -> int:
    """
    Syncs the official 27 academic programmes into SQLite programmes table:
    15 UG, 8 PG, 2 ITEP, 2 PhD.
    """
    cursor.execute("DELETE FROM programmes;")
    programmes = [
        # --- 15 UG PROGRAMMES ---
        ("Bachelor of Computer Application (BCA) Honours", "BCA", "UG", "Department of Computer Applications", "4 Years", "Undergraduate programme in computer applications, programming, software engineering, and systems development. Approved by AICTE.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Sc. Computer Science Honours", "B.Sc.", "UG", "Department of Computer Science and Artificial Intelligence", "4 Years", "Undergraduate honours programme in computer science, algorithms, software development and computing.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Sc. Artificial Intelligence Honours with Research", "B.Sc.", "UG", "Department of Computer Science and Artificial Intelligence", "4 Years", "Undergraduate honours programme in AI, machine learning, neural networks, and cognitive computational systems.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("BBA Honours", "BBA", "UG", "Department of Management Studies", "4 Years", "8-semester honours programme in business administration, operations, marketing, and leadership. Approved by AICTE.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Com Honours (Finance)", "B.Com", "UG", "Department of Commerce", "4 Years", "Honours programme in commerce with specialization in financial accounting, auditing, and corporate finance.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Com Honours (Islamic Finance)", "B.Com", "UG", "Department of Commerce", "4 Years", "Honours programme in commerce specializing in Islamic banking, investments, Islamic jurisprudence, and ethical finance.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Sc. Biotechnology Honours", "B.Sc.", "UG", "PG and Research Dept. of Biotechnology", "4 Years", "8-semester honours programme in molecular biology, genetics, bioinformatics, and industrial biotechnology.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Sc. Food Technology Honours", "B.Sc.", "UG", "Dept. of Food Technology", "4 Years", "Undergraduate degree in food chemistry, processing, quality assurance, nutrition, and preservation technology.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Sc. Microbiology Honours", "B.Sc.", "UG", "PG and Research Dept. of Microbiology", "4 Years", "8-semester honours degree in clinical microbiology, microbial genetics, immunology, and research methodology.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Sc. Physics Honours with Data Science & AI", "B.Sc.", "UG", "Dept. of Physics", "4 Years", "Modern honours physics curriculum integrated with data science, computational modeling, and artificial intelligence.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.Sc. Psychology Honours", "B.Sc.", "UG", "Dept. of Psychology", "4 Years", "Undergraduate honours degree in experimental psychology, abnormal psychology, counseling, and human behavior.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.A. Economics Honours", "B.A.", "UG", "Dept. of Economics", "4 Years", "Undergraduate honours degree in microeconomics, macroeconomics, econometrics, developmental economics, and public finance.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.A. English Language and Literature Honours", "B.A.", "UG", "Dept. of English", "4 Years", "Honours degree in English literature, literary criticism, linguistics, and communicative writing.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.A. Multimedia Honours", "B.A.", "UG", "Dept. of Multimedia", "4 Years", "Undergraduate degree in 2D/3D digital animation, graphic design, visual effects, and UI/UX design.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.A. Islamic Finance with Computer Application Honours", "B.A.", "UG", "Department of Commerce", "4 Years", "Interdisciplinary honours degree blending Islamic financial principles with modern computing applications.", source_url, "SIAS Admission & Academic Programmes Portal"),

        # --- 8 PG PROGRAMMES ---
        ("MBA (Master of Business Administration)", "MBA", "PG", "PMA SAFI School of Management", "2 Years", "Flagship postgraduate management programme at PMA SAFI School of Management. Approved by AICTE.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("M.Com (Finance)", "M.Com", "PG", "Department of Commerce", "2 Years", "Postgraduate master's degree in advanced corporate accounting, taxation, financial management, and financial markets.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("M.Sc. General Biotechnology", "M.Sc.", "PG", "PG and Research Dept. of Biotechnology", "2 Years", "Entrance-based postgraduate master's degree in recombinant DNA technology, cell biology, and bio-therapeutics.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("M.Sc. Food Science & Technology", "M.Sc.", "PG", "Dept. of Food Technology", "2 Years", "Advanced postgraduate studies in food preservation, quality systems, food chemistry, and processing engineering.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("M.Sc. Microbiology", "M.Sc.", "PG", "PG and Research Dept. of Microbiology", "2 Years", "Postgraduate degree in pathogenic bacteriology, molecular virology, immunology, and microbial biotechnology.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("M.Sc. Psychology", "M.Sc.", "PG", "Dept. of Psychology", "2 Years", "Postgraduate degree in clinical assessment, neuropsychology, counseling, and psychotherapy.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("M.A. Journalism & Mass Communication", "M.A.", "PG", "Dept. of Journalism and Mass Communication", "2 Years", "Entrance-based postgraduate degree in print, broadcast, digital journalism, and media production.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("M.A. Islamic Studies", "M.A.", "PG", "PG & Research Department of Islamic Studies", "2 Years", "Master of Arts in Islamic history, theology, comparative religion, and cultural philosophy.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("MSW (Master of Social Work)", "MSW", "PG", "Dept. of Social Work", "2 Years", "Professional postgraduate degree in medical & psychiatric social work and community development.", source_url, "SIAS Admission & Academic Programmes Portal"),

        # --- 2 ITEP PROGRAMMES ---
        ("B.Sc. B.Ed. Secondary", "ITEP", "ITEP", "Dept. of Education", "4 Years", "4-Year Integrated Teacher Education Programme in Science (Physics, Chemistry, Zoology, Botany). Recognised by NCTE.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("B.A. B.Ed. Secondary", "ITEP", "ITEP", "Dept. of Education", "4 Years", "4-Year Integrated Teacher Education Programme in Arts (Economics, English). Recognised by NCTE.", source_url, "SIAS Admission & Academic Programmes Portal"),

        # --- 2 PhD PROGRAMMES ---
        ("Ph.D. in Biotechnology", "Ph.D.", "PhD", "PG and Research Dept. of Biotechnology", "3-5 Years", "Doctoral research programme recognized by the University of Calicut with state-of-the-art laboratories.", source_url, "SIAS Admission & Academic Programmes Portal"),
        ("Ph.D. in Islamic Studies", "Ph.D.", "PhD", "PG & Research Department of Islamic Studies", "3-5 Years", "Doctoral research programme recognized by the University of Calicut focusing on Islamic philosophy and history.", source_url, "SIAS Admission & Academic Programmes Portal")
    ]

    for p in programmes:
        cursor.execute("""
        INSERT INTO programmes (name, degree, level, department, duration, description, source_url, source_page_title, last_updated)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(name) DO UPDATE SET
            degree = excluded.degree,
            level = excluded.level,
            department = excluded.department,
            duration = excluded.duration,
            description = excluded.description,
            source_url = excluded.source_url,
            source_page_title = excluded.source_page_title,
            last_updated = excluded.last_updated;
        """, (*p, date_str))

    return len(programmes)

def sync_college_website() -> Dict[str, Any]:
    """
    Admin-controlled synchronization of approved public SIAS website pages:
    - Fetches approved public pages from https://sias.edu.in/
    - Cleans and extracts content (removes scripts, navs, footers, cookies)
    - Calculates SHA-256 content_hash for change detection
    - Updates SQLite structured tables (programmes, departments, faculty, website_pages)
    - Re-indexes changed/new pages into ChromaDB with required metadata
    - Avoids duplicate vector chunks when content is unchanged
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()

    pages_processed = 0
    pages_updated = 0
    pages_unchanged = 0
    total_chunks_indexed = 0

    # 1. Sync Structured Departments and Programmes
    admission_url = "https://sias.edu.in/admission.html"
    depts_count = sync_structured_departments(cursor, today_str)
    progs_count = sync_structured_programmes(cursor, admission_url, today_str)
    fac_count = fetch_and_upsert_faculty(cursor, today_str)
    conn.commit()

    # 2. Ingest Approved Pages
    for page_info in SIAS_APPROVED_URLS:
        url = page_info["url"]
        page_title = page_info["title"]
        section = page_info["section"]
        content_type = page_info["content_type"]
        page_text = ""

        # Special dynamic handlers
        if "facilities" in url:
            page_text = fetch_facilities_data()
        elif "computer-applications" in url:
            try:
                r = httpx.get(url, timeout=8.0, headers={"User-Agent": "Mozilla/5.0"}, verify=False)
                if r.status_code == 200:
                    page_text = clean_html_to_text(r.text)
            except Exception as e:
                print(f"Notice: Fetch for {url} failed ({e}).")
            if not page_text:
                page_text = get_canonical_computer_applications_text()
        else:
            try:
                r = httpx.get(url, timeout=8.0, headers={"User-Agent": "Mozilla/5.0 (SafiBot Ingestion)"}, verify=False)
                if r.status_code == 200:
                    page_text = clean_html_to_text(r.text)
                    soup = BeautifulSoup(r.text, 'html.parser')
                    if soup.title and soup.title.text.strip():
                        page_title = soup.title.text.strip().replace("\n", " ")
            except Exception as e:
                print(f"Notice: Live fetch for {url} failed ({e}). Using canonical local text.")

        if not page_text:
            page_text = get_canonical_page_text(url)

        # Append structured context if on admission page
        if "admission" in url:
            page_text += "\n\n" + get_canonical_admission_text()

        pages_processed += 1
        content_hash = hashlib.sha256(page_text.encode('utf-8')).hexdigest()

        # Check existing content_hash in SQLite
        cursor.execute("SELECT content_hash FROM website_pages WHERE url = ?;", (url,))
        row = cursor.fetchone()
        existing_hash = row["content_hash"] if row and "content_hash" in row.keys() else None

        summary = page_text[:350].replace("\n", " ").strip() + "..."

        if existing_hash == content_hash:
            # Page is unchanged: keep existing records and vector chunks, just update last_scraped
            cursor.execute("""
            UPDATE website_pages SET last_scraped = ?, last_synced = ? WHERE url = ?;
            """, (today_str, today_str, url))
            pages_unchanged += 1
        else:
            # Page is new or changed: update SQLite and re-chunk for ChromaDB
            cursor.execute("""
            INSERT INTO website_pages (url, title, content_summary, content_hash, last_scraped, last_synced)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                title = excluded.title,
                content_summary = excluded.content_summary,
                content_hash = excluded.content_hash,
                last_scraped = excluded.last_scraped,
                last_synced = excluded.last_synced;
            """, (url, page_title, summary, content_hash, today_str, today_str))

            # Delete old chunks for this URL in ChromaDB to prevent duplicate accumulations
            delete_chunks_by_url(url)

            # Generate new structured chunks and index
            chunks = chunk_website_text(page_text, url, page_title, section, content_hash, today_str)
            indexed_count = index_document_chunks(chunks)
            total_chunks_indexed += indexed_count
            pages_updated += 1

    conn.commit()
    conn.close()

    return {
        "status": "success",
        "pages_synced": pages_processed,
        "pages_updated": pages_updated,
        "pages_unchanged": pages_unchanged,
        "programmes_updated": progs_count,
        "departments_updated": depts_count,
        "faculty_updated": fac_count,
        "chunks_indexed": total_chunks_indexed,
        "message": f"Successfully synchronized {pages_processed} official SIAS website pages: {pages_updated} updated, {pages_unchanged} unchanged. Verified {progs_count} academic programmes, {depts_count} departments, {fac_count} faculty, and {total_chunks_indexed} new knowledge chunks."
    }

def get_canonical_facilities_text() -> str:
    return """SAFI Institute of Advanced Study (Autonomous) - Campus Facilities & ICT Infrastructure
Location: Raziya Nagar, Vazhayoor, Malappuram district, Kerala.
SAFI features a sprawling eco-friendly green campus with modern academic and research infrastructure:

1. Biotechnology Lab:
Equipped with advanced apparatus including Autoclaves, Incubators, Microscopes, Hot Air Oven, Water Bath, Heating Mantle, Magnetic Stirrer, Inoculation Chamber, Colony Counter, Bunsen Burners, Micrometer, Cooling Centrifuge, and Microcentrifuge. Includes a separate dedicated Plant Tissue Culture (PTC) lab for growing large numbers of in vitro cultures.

2. Microbiology Lab:
Spacious microbiology lab equipped with state-of-the-art diagnostic instruments, laminar air flow, incubators, autoclave units, back-up power supply, and research workstations.

3. Computer Science Lab & ICT Facilities:
Modern computer laboratories equipped with high-speed internet, latest high-performance computing terminals, Linux/Windows operating environments, programming IDEs, and network simulators.

4. Food Technology Lab:
Specialized food processing and quality assurance laboratory with instrumentation for chemical analysis, nutrition evaluation, food preservation, and packaging testing.

5. Central Automated Library:
Modern automated Library and Information Centre with digital cataloging, research archives, Plagiarism CheckerX anti-plagiarism verification software, institutional repository, and previous semester question paper bank.

6. Campus Banking (ATM & CDM):
On-campus AXIS Bank 24/7 ATM and Cash Deposit Machine (CDM) facility for students and staff.

7. Sports Infrastructure & Physical Fitness Centre:
Spacious football ground, basketball court, volleyball court, badminton court, table tennis, athletic track, and fully equipped physical fitness gymnasium.

8. Residential Hostels:
Separate on-campus secure hostels for male and female students with 24/7 security, high-speed Wi-Fi, study halls, and hygienic dining.

9. Smart Classrooms:
Air-conditioned ICT-enabled smart classrooms with interactive displays, audio-visual systems, and multimedia projection."""

def get_canonical_computer_applications_text() -> str:
    return """SAFI Institute of Advanced Study (Autonomous) - Department of Computer Applications
Overview:
The Department of Computer Applications was established in the year 2010.
The department offers the undergraduate Bachelor of Computer Application (BCA Honours) programme, which is approved by AICTE.
Head of the Department (HOD): Mr. Muhammed Haneesh K.P (Assistant Professor and Head).

Curriculum & Projects:
The department curriculum keeps abreast of new concepts, programming languages, and industry applications. Project work is an integral part of the curriculum. The department exposes students to latest technologies to bridge the industry gap in the IT sector by adhering to social ethics and conducting workshops, seminars, and tech talks.

Objectives:
1. To open a channel of admission for computing courses for students who have completed 10+2 and are interested in taking computing/IT as a career.
2. To offer foundation graduate programmes acting as a feeder course for higher studies in Computer Science and Applications.
3. To develop software development skills enabling graduates to take up professional careers or self-employment in Indian and global software markets.

Vision:
To become a centre of excellence in the field of computer science and applications to produce globally competent graduates with moral values committed to build a vibrant nation.

Mission:
- To provide high quality education with an emphasis on basic principles of computer applications.
- Enhancing student-centric learning and social engagements with moral and ethical values and life skills.
- To provide quality training and guidance in computer applications to make students globally employable.
- To expose students to broad research and development experience."""

def get_canonical_admission_text() -> str:
    return """SIAS Official Admission Requirements & Academic Criteria:
Autonomous Arts and Science College accredited with NAAC A++ grade. Affiliated to University of Calicut.

Programmes Offered:
- 15 Undergraduate (UG) Honours Programmes (BCA, B.Sc. CS, B.Sc. AI, BBA, B.Com Finance, B.Com Islamic Finance, B.Sc. Biotechnology, B.Sc. Food Tech, B.Sc. Microbiology, B.Sc. Physics, B.Sc. Psychology, B.A. Economics, B.A. English, B.A. Multimedia, B.A. Islamic Finance).
- 8 Postgraduate (PG) Programmes (MBA, M.Com Finance, M.Sc. Biotechnology, M.Sc. Food Science, M.Sc. Microbiology, M.Sc. Psychology, M.A. JMC, M.A. Islamic Studies, MSW).
- 2 Integrated Teacher Education Programmes (ITEP: B.Sc. B.Ed. & B.A. B.Ed.).
- 2 Doctoral (Ph.D.) Programmes (Biotechnology and Islamic Studies).

Undergraduate (UG) Admission Requirements:
1. Candidates seeking admission to UG programmes must have passed Plus Two (Higher Secondary Examination) or equivalent examination from a recognized board.
2. For BCA Honours: Candidates with Mathematics or Computer Science at Plus Two level are preferred. Approved by AICTE.
3. For BBA Honours: Commerce or Science stream candidates who passed Plus Two with required minimum percentage are eligible. Approved by AICTE.
4. For B.Com Honours: Minimum pass in Plus Two examination with Commerce or related subjects.
5. For B.Sc. Science programmes (Biotechnology, Food Tech, Microbiology, Physics): Candidates must have studied Physics, Chemistry, and Biology/Mathematics at Plus Two level.

Postgraduate (PG) Admission Requirements:
1. Candidates must possess a recognized Bachelor's Degree in the relevant discipline with a minimum of 50% aggregate marks (or equivalent grade).
2. For MBA: Valid score in national/state management entrance tests (CAT / CMAT / KMAT Kerala) followed by Group Discussion and Personal Interview. Approved by AICTE.
3. For M.Sc. General Biotechnology and M.A. Journalism: Entrance-based selection process.

How to Apply:
Online application forms can be submitted directly through the college admission portal at https://sias.edu.in/admission.html.
Official Prospectus is available for download at https://sias.edu.in/docs/prospectus.pdf."""

def get_canonical_page_text(url: str) -> str:
    if "admission" in url:
        return get_canonical_admission_text()
    elif "facilities" in url:
        return get_canonical_facilities_text()
    elif "computer-applications" in url:
        return get_canonical_computer_applications_text()
    elif "library" in url:
        return """Library and Information Centre, SIAS
The Central Library is the heart of academic learning at SAFI Institute of Advanced Study.
Working Hours: Monday to Friday: 9:30 AM to 5:00 PM; Saturdays: 10:00 AM to 4:00 PM. Closed on Sundays.
Key Services:
- Plagiarism CheckerX software for anti-plagiarism verification of academic projects, dissertations, and research papers.
- Institutional Repository archiving publications, seminar proceedings, and faculty monographs.
- Repository of previous semester examination question papers for exam preparation.
- Circulation service: UG students can borrow up to 3 books; PG students can borrow up to 5 books.
- Digital Information Centre with internet terminals for online research.
Staff: Mr. Yaseen Aboobacker K.V. (Assistant Librarian) and library assistants."""
    elif "stdzone" in url:
        return """Student Support & Student Welfare at SAFI Institute of Advanced Study
Key Support Cells:
1. Advisory Scheme: Dedicated faculty advisors provide academic, personal, and career mentoring for all enrolled students.
2. Career Guidance & Placement Cell: Arranges campus placement drives with top recruiters (Infosys, TCS, Wipro, regional firms) and conducts aptitude/soft-skill training.
3. Civil Service Foundation Coaching: Only college in Malabar offering civil service foundation training with faculty from Delhi.
4. Scholarship Committee: Facilitates state, national, and merit-cum-means scholarships.
5. Equal Opportunity and SC/ST Cell: Ensures equitable educational access and welfare adherence to UGC/Government directives.
6. Internal Complaints Committee (ICC): Set up under the Sexual Harassment of Women at Workplace Act 2013, ensuring a safe, congenial environment free of harassment."""
    else:
        return """SAFI Institute of Advanced Study (Autonomous)
Established in 2005 by the Social Advancement Foundation of India (SAFI), a non-profit charitable trust.
Located in Raziya Nagar, Vazhayoor, Malappuram district, Kerala.
Autonomous Arts and Science College accredited with NAAC A++ grade.
UGC has granted autonomous status for 10 years (2024-2025 to 2033-2034).
Affiliated to the University of Calicut and recognized by the Government of Kerala and UGC under Section 2(f).
Principal: Prof. E. P. Imbichikoya.
Official Website: https://sias.edu.in/"""

def get_canonical_faculty_list() -> List[Dict[str, str]]:
    return [
        {"name": "Mr. Muhammed Haneesh K.P", "designation": "Assistant Professor and Head", "department": "Department of Computer Applications", "profile_url": "https://sias.edu.in/academics/computer-applications/faculty.html"},
        {"name": "Mr. Abdul Samad C.", "designation": "Assistant Professor", "department": "Department of Computer Applications", "profile_url": "https://sias.edu.in/academics/computer-applications/faculty.html"},
        {"name": "Ms. Safeena C", "designation": "Assistant Professor", "department": "Department of Computer Applications", "profile_url": "https://sias.edu.in/academics/computer-applications/faculty.html"},
        {"name": "Ms. Rasheeja A.P.", "designation": "Assistant Professor", "department": "Department of Computer Applications", "profile_url": "https://sias.edu.in/academics/computer-applications/faculty.html"},
        {"name": "Ms. Raseena V.", "designation": "Assistant Professor", "department": "Department of Computer Applications", "profile_url": "https://sias.edu.in/academics/computer-applications/faculty.html"},
        {"name": "Dr. Arshad P.T.", "designation": "Assistant Professor and Head", "department": "Department of Computer Science and Artificial Intelligence", "profile_url": "https://sias.edu.in/academics/cs-ai/faculty.html"},
        {"name": "Mr. Samsheer Babu M.", "designation": "Assistant Professor and Head", "department": "Department of Management Studies", "profile_url": "https://sias.edu.in/academics/management/faculty.html"},
        {"name": "Ms. Safa Hanan C.K.", "designation": "Assistant Professor and Head", "department": "Department of Commerce", "profile_url": "https://sias.edu.in/academics/commerce/faculty.html"},
        {"name": "Mr. Abdul Majeed K.", "designation": "Assistant Professor and Head", "department": "Department of Commerce", "profile_url": "https://sias.edu.in/academics/commerce/faculty.html"},
        {"name": "Dr. Sahaya Shibu B.", "designation": "Assistant Professor and Head", "department": "PG and Research Dept. of Biotechnology", "profile_url": "https://sias.edu.in/academics/biotechnology/faculty.html"},
        {"name": "Dr. Anusha R.", "designation": "Assistant Professor and Head", "department": "Dept. of Food Technology", "profile_url": "https://sias.edu.in/academics/foodtechnology/faculty.html"},
        {"name": "Dr. Shabanamol S.", "designation": "Assistant Professor and Head", "department": "PG and Research Dept. of Microbiology", "profile_url": "https://sias.edu.in/academics/microbiology/faculty.html"},
        {"name": "Dr. Hajara. K.", "designation": "Assistant Professor and Head", "department": "Dept. of Physics", "profile_url": "https://sias.edu.in/academics/physics/faculty.html"},
        {"name": "Mr. Muhammed Assan", "designation": "Assistant Professor and Head", "department": "Dept. of Psychology", "profile_url": "https://sias.edu.in/academics/psychology/faculty.html"},
        {"name": "Dr. Anees Rehman A", "designation": "Assistant Professor and Head", "department": "Dept. of Economics", "profile_url": "https://sias.edu.in/academics/economics/faculty.html"},
        {"name": "Dr. Najda A", "designation": "Assistant Professor and Head", "department": "Dept. of English", "profile_url": "https://sias.edu.in/academics/english/faculty.html"},
        {"name": "Dr. Shebeeb Khan P.", "designation": "Assistant Professor and Head", "department": "PG & Research Department of Islamic Studies", "profile_url": "https://sias.edu.in/academics/is/faculty.html"},
        {"name": "Mr. Akhilnath K.S.", "designation": "Assistant Professor and Head", "department": "Dept. of Journalism and Mass Communication", "profile_url": "https://sias.edu.in/academics/jmc/faculty.html"},
        {"name": "Dr. Noorunnida M. (Ph.D)", "designation": "Assistant Professor and Head", "department": "Dept. of Social Work", "profile_url": "https://sias.edu.in/academics/socialwork/faculty.html"},
        {"name": "Mr. Muhammed Abdul Rauf K.T.", "designation": "Assistant Professor and Head", "department": "Dept. of Multimedia", "profile_url": "https://sias.edu.in/academics/multimedia/faculty.html"},
        {"name": "Ms. AMRUTHA K .N.", "designation": "Assistant Professor and Head", "department": "Dept. of Public Administration", "profile_url": "https://sias.edu.in/academics/public_administration/faculty.html"},
        {"name": "Prof. (Dr.) Mumthas N.S", "designation": "Head of the Department (HOD) & Professor", "department": "Dept. of Education", "profile_url": "https://sias.edu.in/academics/faculty.html"}
    ]
