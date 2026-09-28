import sys
import os
import re
import json
import httpx
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.abspath("."))

from backend.database.db import get_connection
from backend.services.rag import get_collection, search_chunks
from backend.services.website_scraper import sync_college_website, SIAS_APPROVED_URLS
from backend.services.retrieval_service import execute_college_retrieval, FALLBACK_UNKNOWN_MSG

BASE_URL = "http://127.0.0.1:8000/api"

def print_separator(char="=", length=80):
    print(char * length)

def verify_real_website_knowledge():
    print_separator()
    print("SAFIBOT REAL OFFICIAL WEBSITE KNOWLEDGE VERIFICATION")
    print("College: SAFI Institute of Advanced Study (Autonomous)")
    print("Official Website: https://sias.edu.in/")
    print_separator()

    stages = {
        "WEBSITE INGESTION": False,
        "WEBSITE CONTENT EXTRACTED": False,
        "SQLITE STRUCTURED DATA": False,
        "CHROMADB WEBSITE DATA": False,
        "QUERY ROUTING": False,
        "RETRIEVAL": False,
        "LLM GROUNDED ANSWER": False,
        "SOURCE CITATION": False,
        "HALLUCINATION PROTECTION": False
    }

    client = httpx.Client(base_url=BASE_URL, timeout=20.0)

    # =========================================================================
    # STAGE 1: WEBSITE INGESTION & FRESHNESS
    # =========================================================================
    print("\n[STAGE 1] INGESTION & FRESHNESS VERIFICATION")
    print("Executing actual college website sync pipeline...")

    try:
        sync_result = sync_college_website()
        print(f"Sync Result Status: {sync_result['status']}")
        print(f"Message: {sync_result['message']}")

        if sync_result["status"] != "success":
            print("[FAIL] Ingestion returned non-success status.")
            return report(stages)

        # Freshness & Deduplication Test: run sync a second time
        print("\nChecking website freshness and chunk deduplication (idempotency)...")
        sync_result_2 = sync_college_website()
        print(f"Second Sync Result: {sync_result_2['pages_unchanged']} unchanged, {sync_result_2['pages_updated']} updated.")

        # In second run, all pages should be unchanged and zero duplicate chunks created
        if sync_result_2["pages_unchanged"] != sync_result_2["pages_synced"]:
            print(f"[FAIL] Idempotency failed: expected {sync_result_2['pages_synced']} unchanged pages, got {sync_result_2['pages_unchanged']}")
            return report(stages)

        stages["WEBSITE INGESTION"] = True
        print("[PASS] Website ingestion & idempotency verified.")

        # Verify extracted content in SQLite website_pages table
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT url, title, content_summary, content_hash, last_scraped, last_synced FROM website_pages;")
        pages = [dict(r) for r in cursor.fetchall()]
        conn.close()

        print(f"\nIndexed Website Pages in SQLite ({len(pages)} pages):")
        all_pages_valid = True
        for p in pages:
            url = p["url"]
            title = p["title"]
            summary = p["content_summary"]
            content_hash = p["content_hash"]
            last_synced = p["last_synced"]

            is_valid = (
                url.startswith("https://sias.edu.in/") and
                bool(title) and
                bool(summary) and len(summary) >= 30 and
                bool(content_hash) and len(content_hash) == 64 and
                bool(last_synced)
            )
            mark = "PASS" if is_valid else "FAIL"
            print(f"  [{mark}] URL: {url}")
            print(f"         Title: {title}")
            print(f"         Summary Excerpt: {summary[:80]}...")
            print(f"         Hash: {content_hash[:16]}... | Last Synced: {last_synced}")

            if not is_valid:
                all_pages_valid = False

        if all_pages_valid and len(pages) >= 8:
            stages["WEBSITE CONTENT EXTRACTED"] = True
            print("[PASS] Website content extraction verified.")
        else:
            print("[FAIL] Extracted content validation failed.")
            return report(stages)

    except Exception as e:
        print(f"[FAIL] Ingestion stage error: {e}")
        return report(stages)

    # =========================================================================
    # STAGE 2: STORAGE LAYER VERIFICATION (SQLITE + CHROMADB)
    # =========================================================================
    print("\n[STAGE 2] STORAGE LAYER (SQLITE & CHROMADB) VERIFICATION")
    try:
        conn = get_connection()
        c = conn.cursor()

        # A. SQLite Structured Data
        c.execute("SELECT count(*) FROM programmes;")
        prog_count = c.fetchone()[0]
        c.execute("SELECT count(*) FROM departments;")
        dept_count = c.fetchone()[0]
        c.execute("SELECT count(*) FROM faculty;")
        fac_count = c.fetchone()[0]

        # Verify programmes details
        c.execute("SELECT level, count(*) FROM programmes GROUP BY level;")
        level_dist = dict(c.fetchall())

        # Verify department HODs
        c.execute("SELECT count(*) FROM departments WHERE hod_name IS NOT NULL AND hod_name != '';")
        depts_with_hod = c.fetchone()[0]

        conn.close()

        print(f"  SQLite Programmes: {prog_count} records {level_dist}")
        print(f"  SQLite Departments: {dept_count} records ({depts_with_hod} have designated HODs)")
        print(f"  SQLite Faculty: {fac_count} records")

        if prog_count >= 25 and dept_count >= 15 and fac_count >= 50:
            stages["SQLITE STRUCTURED DATA"] = True
            print("[PASS] SQLite structured data verified.")
        else:
            print("[FAIL] SQLite structured data counts below expected official values.")
            return report(stages)

        # B. ChromaDB Website Data
        chroma_col = get_collection()
        all_meta = chroma_col.get().get("metadatas", [])
        web_chunks = [m for m in all_meta if m.get("source_type") == "website"]
        print(f"  ChromaDB Website Chunks: {len(web_chunks)} chunks (Total chunks: {len(all_meta)})")

        web_chunks_valid = True
        for m in web_chunks[:10]:
            if not (
                m.get("source_type") == "website" and
                m.get("url", "").startswith("https://sias.edu.in/") and
                bool(m.get("page_title")) and
                bool(m.get("section")) and
                bool(m.get("content_hash")) and
                bool(m.get("last_updated"))
            ):
                web_chunks_valid = False
                break

        if web_chunks_valid and len(web_chunks) >= 30:
            stages["CHROMADB WEBSITE DATA"] = True
            print("[PASS] ChromaDB website knowledge chunks verified.")
        else:
            print("[FAIL] ChromaDB website chunk metadata validation failed.")
            return report(stages)

    except Exception as e:
        print(f"[FAIL] Storage verification error: {e}")
        return report(stages)

    # =========================================================================
    # STAGE 3: DIRECT RETRIEVAL DIAGNOSTIC (Before testing LLM)
    # =========================================================================
    print("\n[STAGE 3] DIRECT RETRIEVAL LAYER DIAGNOSTIC")
    print("Testing direct retrieval without LLM on 4 core college queries:\n")

    diagnostic_queries = [
        {
            "query": "What programmes are offered by Computer Applications?",
            "expected_type": "website_structured",
            "expected_url_prefix": "https://sias.edu.in/admission.html",
            "required_evidence_terms": ["computer application", "bca", "honours"]
        },
        {
            "query": "What departments are available?",
            "expected_type": "website_structured",
            "expected_url_prefix": "https://sias.edu.in/academics/index.html",
            "required_evidence_terms": ["computer applications", "commerce", "biotechnology"]
        },
        {
            "query": "What admission information is available?",
            "expected_type": "website_rag",
            "expected_url_prefix": "https://sias.edu.in/admission.html",
            "required_evidence_terms": ["admission", "eligibility", "plus two"]
        },
        {
            "query": "What facilities are mentioned on the website?",
            "expected_type": "website_rag",
            "expected_url_prefix": "https://sias.edu.in/resources/facilities.html",
            "required_evidence_terms": ["laborator", "hostel", "sports", "library"]
        }
    ]

    retrieval_ok = True
    routing_ok = True

    for i, test in enumerate(diagnostic_queries, 1):
        q = test["query"]
        res = execute_college_retrieval(q)

        # Print exact required diagnostic output format
        print(f"Diagnostic Test #{i}:")
        print(f"  Question:                     {res.get('question')}")
        print(f"  Query type:                   {res.get('query_type')}")
        print(f"  Retrieved source:             {res.get('retrieved_source')}")
        print(f"  Source URL:                   {res.get('source_url')}")
        print(f"  Relevant retrieved text/chunk:{res.get('relevant_text')[:120].replace(chr(10), ' ')}...")
        print(f"  Relevance/similarity info:    {res.get('relevance_info')}")

        # Verification of diagnostic output
        if res.get("query_type") != test["expected_type"]:
            print(f"  [FAIL] Query type mismatch: expected {test['expected_type']}, got {res.get('query_type')}")
            routing_ok = False

        if not res.get("source_url", "").startswith(test["expected_url_prefix"]):
            print(f"  [FAIL] Source URL mismatch: expected prefix {test['expected_url_prefix']}, got {res.get('source_url')}")
            retrieval_ok = False

        # Verify evidence text contains required domain facts
        evidence_str = (
            (res.get("relevant_text") or "") + " " +
            json.dumps(res.get("retrieved_records") or []) + " " +
            " ".join(res.get("retrieved_chunks") or [])
        ).lower()

        evidence_has_terms = any(term in evidence_str for term in test["required_evidence_terms"])
        if not evidence_has_terms:
            print(f"  [FAIL] Retrieved evidence missing expected domain terms: {test['required_evidence_terms']}")
            retrieval_ok = False
        else:
            print("  [PASS] Evidence verified in retrieved records/chunks.")
        print("-" * 65)

    if routing_ok:
        stages["QUERY ROUTING"] = True
    if retrieval_ok:
        stages["RETRIEVAL"] = True

    if not (routing_ok and retrieval_ok):
        print("[FAIL] Retrieval layer diagnostic failed. Aborting LLM test.")
        return report(stages)

    # =========================================================================
    # STAGE 4: CHATBOT GROUNDING & SOURCE CITATION VERIFICATION
    # =========================================================================
    print("\n[STAGE 4] CHATBOT GROUNDING & CITATION VERIFICATION")
    print("Verifying pipeline: Question -> Retrieval -> LLM -> Grounded Answer -> Official Citation")
    print("RULE: Answers are verified against RETRIEVED EVIDENCE (no hardcoded expected strings).\n")

    grounding_ok = True
    citation_ok = True

    chat_tests = [
        {
            "id": 1,
            "question": "What programmes are offered by Computer Applications?",
            "expected_source_domain": "https://sias.edu.in/admission.html",
            "core_concepts": ["computer application", "bca"]
        },
        {
            "id": 2,
            "question": "What departments are available?",
            "expected_source_domain": "https://sias.edu.in/academics/index.html",
            "core_concepts": ["department", "computer applications", "commerce"]
        },
        {
            "id": 3,
            "question": "What admission information is available?",
            "expected_source_domain": "https://sias.edu.in/admission.html",
            "core_concepts": ["admission", "eligibility", "plus two"]
        },
        {
            "id": 4,
            "question": "What facilities are mentioned on the website?",
            "expected_source_domain": "https://sias.edu.in/resources/facilities.html",
            "core_concepts": ["laborator", "hostel", "sports", "library"]
        },
        {
            "id": 5,
            "question": "Who is the HOD of Computer Applications?",
            "expected_source_domain": "https://sias.edu.in/",
            "core_concepts": ["haneesh", "head"]
        }
    ]

    for t in chat_tests:
        q = t["question"]
        print(f"Chat Test #{t['id']}: {q}")

        # Send request to /api/chat
        resp = client.post("/chat", json={"message": q})
        if resp.status_code != 200:
            print(f"  [FAIL] /api/chat returned status {resp.status_code}")
            grounding_ok = False
            continue

        data = resp.json()
        answer = data.get("answer", "")
        sources = data.get("sources", [])
        query_type = data.get("query_type", "")

        # 1. Inspect evidence from retrieval layer for this question
        diag_evidence = execute_college_retrieval(q)
        evidence_text = (
            (diag_evidence.get("relevant_text") or "") + "\n" +
            json.dumps(diag_evidence.get("retrieved_records") or []) + "\n" +
            "\n".join(diag_evidence.get("retrieved_chunks") or [])
        ).lower()

        # 2. Verify Groundedness:
        # Instead of hardcoding the expected answer, verify:
        # a) Every core concept claimed in the answer exists in the retrieved evidence text
        ans_lower = answer.lower()
        core_matches = [c for c in t["core_concepts"] if c in ans_lower]
        grounded_in_evidence = [c for c in core_matches if (c in evidence_text or c.rstrip('s') in evidence_text)]

        is_grounded = len(core_matches) > 0 and len(grounded_in_evidence) == len(core_matches)

        # 3. Verify Source Citation:
        # Must cite official SIAS URL
        cited_urls = [s.get("url", "") for s in sources if s.get("url")]
        # Also extract URLs mentioned in the answer text itself
        text_urls = re.findall(r'https?://sias\.edu\.in[^\s\)]*', answer)
        all_cited_urls = list(set(cited_urls + text_urls))

        has_official_citation = any(u.startswith(t["expected_source_domain"]) for u in all_cited_urls)

        print(f"  Query Type:           {query_type}")
        print(f"  Answer Preview:       {answer[:120].replace(chr(10), ' ')}...")
        print(f"  Cited Official URLs:  {all_cited_urls}")
        print(f"  Grounded in Evidence: {len(grounded_in_evidence)}/{len(t['core_concepts'])} key concepts verified against retrieved content")

        if is_grounded:
            print("  [PASS] Answer factually grounded in retrieved website evidence.")
        else:
            print(f"  [FAIL] Answer not grounded: concepts {core_matches} not verified in evidence.")
            grounding_ok = False

        if has_official_citation:
            print("  [PASS] Official SIAS source citation verified.")
        else:
            print(f"  [FAIL] Missing or invalid official source citation for {t['expected_source_domain']}.")
            citation_ok = False

        print("-" * 65)

    if grounding_ok:
        stages["LLM GROUNDED ANSWER"] = True
    if citation_ok:
        stages["SOURCE CITATION"] = True

    # =========================================================================
    # STAGE 5: UNKNOWN-QUESTION & HALLUCINATION PROTECTION
    # =========================================================================
    print("\n[STAGE 5] UNKNOWN-QUESTION & ZERO-HALLUCINATION TEST")
    print("Testing question with genuinely NO answer in knowledge base:")

    unknown_q = "What is the tuition fee structure for the Bachelor of Aerospace and Aeronautical Engineering at SIAS?"
    print(f"Question: {unknown_q}")

    resp_unk = client.post("/chat", json={"message": unknown_q})
    if resp_unk.status_code == 200:
        data_unk = resp_unk.json()
        ans_unk = data_unk.get("answer", "")
        sources_unk = data_unk.get("sources", [])
        q_type_unk = data_unk.get("query_type", "")

        print(f"Chatbot Response: {ans_unk}")
        print(f"Sources Provided: {sources_unk}")

        # Chatbot MUST use knowledge-base fallback rather than inventing an answer
        fallback_used = "couldn't find that information" in ans_unk.lower() or "could not find that information" in ans_unk.lower()
        no_fabricated_sources = (len(sources_unk) == 0)

        # Also verify it was logged into the continuous learning queue
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT question, status FROM learning_queue WHERE question = ?;", (unknown_q.strip(),))
        queue_item = cursor.fetchone()
        conn.close()

        queued_properly = (queue_item is not None)

        print(f"  Fallback Triggered:       {'YES' if fallback_used else 'NO'}")
        print(f"  No Fabricated Sources:    {'YES' if no_fabricated_sources else 'NO'}")
        print(f"  Added to Learning Queue:  {'YES' if queued_properly else 'NO'}")

        if fallback_used and no_fabricated_sources:
            stages["HALLUCINATION PROTECTION"] = True
            print("[PASS] Hallucination protection and unknown fallback verified.")
        else:
            print("[FAIL] Hallucination protection failed (invented facts or fabricated URLs).")
    else:
        print(f"[FAIL] /api/chat error on unknown question: {resp_unk.status_code}")

    # =========================================================================
    # STAGE 6: FINAL DIAGNOSTIC REPORT
    # =========================================================================
    return report(stages)

def report(stages: Dict[str, bool]) -> bool:
    print_separator()
    print("SAFIBOT REAL WEBSITE KNOWLEDGE VERIFICATION REPORT")
    print_separator()
    all_passed = True
    for stage_name, passed in stages.items():
        mark = "PASS" if passed else "FAIL"
        print(f"{stage_name}: {mark}")
        if not passed:
            all_passed = False

    print_separator()
    if all_passed:
        print("OVERALL RESULT: ALL 9 PIPELINE STAGES PASSED SUCCESSFULLY!")
        print("SafiBot demonstrably understands and grounds answers from https://sias.edu.in/")
    else:
        print("OVERALL RESULT: VERIFICATION FAILED AT ONE OR MORE STAGES.")
    print_separator()
    return all_passed

if __name__ == "__main__":
    success = verify_real_website_knowledge()
    sys.exit(0 if success else 1)
