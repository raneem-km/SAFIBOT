import sys
import os
sys.path.insert(0, os.path.abspath("."))
import json
import httpx

BASE_URL = "http://127.0.0.1:8000/api"

TEST_SUITE = [
    {
        "id": 1,
        "question": "How many UG programmes are available?",
        "expected_intent": "website_structured",
        "expected_source": "https://sias.edu.in/admission.html",
        "expected_keywords": ["15", "undergraduate", "bca"]
    },
    {
        "id": 2,
        "question": "How many PG programmes are available?",
        "expected_intent": "website_structured",
        "expected_source": "https://sias.edu.in/admission.html",
        "expected_keywords": ["postgraduate", "mba", "m.com", "m.sc"]
    },
    {
        "id": 3,
        "question": "What programmes are offered by the Department of Computer Applications?",
        "expected_intent": "website_structured",
        "expected_source": "https://sias.edu.in/admission.html",
        "expected_keywords": ["bachelor of computer application", "bca", "4 years"]
    },
    {
        "id": 4,
        "question": "What departments are available?",
        "expected_intent": "website_structured",
        "expected_source": "https://sias.edu.in/academics/index.html",
        "expected_keywords": ["computer applications", "biotechnology", "management", "departments"]
    },
    {
        "id": 5,
        "question": "Who is the HOD of Computer Applications?",
        "expected_intent": "website_structured",
        "expected_source": "https://sias.edu.in/academics/faculty.html",
        "expected_keywords": ["muhammed haneesh", "head"]
    },
    {
        "id": 6,
        "question": "What courses are offered by the college?",
        "expected_intent": "website_structured",
        "expected_source": "https://sias.edu.in/admission.html",
        "expected_keywords": ["programmes", "undergraduate", "postgraduate", "itep", "ph.d"]
    },
    {
        "id": 7,
        "question": "What are the admission requirements?",
        "expected_intent": "website_rag",
        "expected_source": "https://sias.edu.in/admission.html",
        "expected_keywords": ["plus two", "eligibility", "admission", "bachelor"]
    },
    {
        "id": 8,
        "question": "What facilities does the college provide?",
        "expected_intent": "website_rag",
        "expected_source": "https://sias.edu.in/resources/facilities.html",
        "expected_keywords": ["laborator", "library", "hostel", "sports", "campus"]
    },
    {
        "id": 9,
        "question": "Give me information about the Computer Applications department.",
        "expected_intent": "website_hybrid",
        "expected_source": "https://sias.edu.in/academics/computer-applications/index.html",
        "expected_keywords": ["2010", "muhammed haneesh", "bca", "curriculum", "vision"]
    },
    {
        "id": 10,
        "question": "What is the tuition fee structure for aeronautical engineering at SIAS?",
        "expected_intent": "general_knowledge_rag",
        "expected_source": None,
        "expected_keywords": ["couldn't find that information"]
    }
]

def run_tests():
    print("=" * 80)
    print("SAFIBOT OFFICIAL COLLEGE WEBSITE KNOWLEDGE VERIFICATION")
    print("Official College Website: https://sias.edu.in/")
    print("=" * 80)

    client = httpx.Client(base_url=BASE_URL, timeout=15.0)

    # 1. Verify Admin Website Sync
    print("\n[PHASE 1] Checking Admin Sync College Website Endpoint (/api/admin/sync-website)...")
    try:
        from backend.services.website_scraper import sync_college_website
        sync_result = sync_college_website()
        print(f"Sync Result: {json.dumps(sync_result, indent=2)}")
        assert sync_result["status"] == "success"
        print("[PASS] Website sync engine verified successfully!")
    except Exception as e:
        print(f"[FAIL] Sync error: {e}")
        return False

    # 2. Run Test Questions against /api/chat/diagnose
    print("\n[PHASE 2] Executing 10 Test Questions against /api/chat/diagnose and /api/chat...")
    passed = 0
    failed = 0

    for test in TEST_SUITE:
        t_id = test["id"]
        q = test["question"]
        print(f"\n" + "-" * 75)
        print(f"TEST {t_id}: {q}")
        print("-" * 75)

        res = client.post("/chat/diagnose", json={"message": q})
        if res.status_code != 200:
            print(f"[FAIL] HTTP Status Error: {res.status_code}")
            failed += 1
            continue

        data = res.json()
        intent = data.get("detected_intent")
        method = data.get("retrieval_method")
        query_exec = data.get("query_executed")
        urls = data.get("source_urls", [])
        answer = data.get("final_answer", "")

        print(f"Question:           {q}")
        print(f"Detected Intent:    {intent}")
        print(f"Retrieval Method:   {method}")
        print(f"Query Executed:     {query_exec}")
        print(f"Source URLs:        {urls}")
        print(f"Final Answer:")
        for line in answer.split("\n"):
            print(f"    {line}")

        # Verification checks
        ans_lower = answer.lower()
        checks = []

        # Check intent
        intent_match = (intent == test["expected_intent"])
        checks.append(("Intent Classification", intent_match))

        # Check source
        if test["expected_source"]:
            src_match = any(test["expected_source"] in u for u in urls)
            checks.append(("Source Citation URL", src_match))
        else:
            # Non-existent question should not have fabricated URLs
            no_fab = (len(urls) == 0)
            checks.append(("No Fabricated Source", no_fab))

        # Check keywords
        kw_match = all(k.lower() in ans_lower for k in test["expected_keywords"])
        checks.append(("Factual Keyword Evidence", kw_match))

        # Check zero hallucination for test 10
        if t_id == 10:
            no_hallucination = "couldn't find that information" in ans_lower
            checks.append(("Zero Hallucination Fallback", no_hallucination))

        all_ok = all(c[1] for c in checks)
        for check_name, status in checks:
            mark = "[PASS]" if status else "[FAIL]"
            print(f"  {mark} {check_name}: {'PASS' if status else 'FAIL'}")

        if all_ok:
            passed += 1
            print(f"RESULT: PASSED")
        else:
            failed += 1
            print(f"RESULT: FAILED")

    print("\n" + "=" * 80)
    print(f"TEST SUMMARY: {passed}/{len(TEST_SUITE)} PASSED ({failed} FAILED)")
    print("=" * 80)
    return failed == 0

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
