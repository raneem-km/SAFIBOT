import os
import re
import json
import shutil
from typing import List, Dict, Any, Optional

try:
    import chromadb
    HAS_CHROMA = True
except Exception:
    HAS_CHROMA = False

IS_VERCEL = os.getenv("VERCEL") == "1" or os.getenv("VERCEL_ENV") is not None
ORIGINAL_CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "chroma_db")

if HAS_CHROMA:
    if IS_VERCEL:
        TMP_CHROMA_PATH = os.path.join("/tmp", "chroma_db")
        if not os.path.exists(TMP_CHROMA_PATH) and os.path.exists(ORIGINAL_CHROMA_PATH):
            try:
                shutil.copytree(ORIGINAL_CHROMA_PATH, TMP_CHROMA_PATH, dirs_exist_ok=True)
            except Exception:
                pass
        CHROMA_PATH = TMP_CHROMA_PATH if os.path.exists(TMP_CHROMA_PATH) else ORIGINAL_CHROMA_PATH
    else:
        CHROMA_PATH = ORIGINAL_CHROMA_PATH
    COLLECTION_NAME = "safibot_knowledge"

MEMORY_STORE_FILE = os.path.join("/tmp" if IS_VERCEL else os.path.dirname(os.path.dirname(__file__)), "database", "memory_chunks.json")
_memory_chunks = []

def load_memory_chunks():
    global _memory_chunks
    if os.path.exists(MEMORY_STORE_FILE):
        try:
            with open(MEMORY_STORE_FILE, "r", encoding="utf-8") as f:
                _memory_chunks = json.load(f)
        except Exception:
            _memory_chunks = []

def save_memory_chunks():
    try:
        os.makedirs(os.path.dirname(MEMORY_STORE_FILE), exist_ok=True)
        with open(MEMORY_STORE_FILE, "w", encoding="utf-8") as f:
            json.dump(_memory_chunks, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Memory chunk save note: {e}")

load_memory_chunks()

def get_chroma_client():
    if not HAS_CHROMA:
        return None
    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)

def get_collection():
    if not HAS_CHROMA:
        return None
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "SafiBot College Academic & Document Knowledge Base"}
    )

def index_document_chunks(chunks: List[Dict[str, Any]]) -> int:
    if not chunks:
        return 0
    if HAS_CHROMA:
        try:
            collection = get_collection()
            ids = [c["id"] for c in chunks]
            documents = [c["text"] for c in chunks]
            metadatas = [c["metadata"] for c in chunks]
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        except Exception as e:
            print(f"Chroma indexing note: {e}")
    global _memory_chunks
    chunk_dict = {c["id"]: c for c in _memory_chunks}
    for c in chunks:
        chunk_dict[c["id"]] = c
    _memory_chunks = list(chunk_dict.values())
    save_memory_chunks()
    return len(chunks)

def delete_document_chunks(doc_id: int):
    if HAS_CHROMA:
        try:
            collection = get_collection()
            collection.delete(where={"doc_id": doc_id})
        except Exception:
            pass
    global _memory_chunks
    _memory_chunks = [c for c in _memory_chunks if c.get("metadata", {}).get("doc_id") != doc_id]
    save_memory_chunks()

def delete_chunks_by_url(source_url: str):
    if HAS_CHROMA:
        try:
            collection = get_collection()
            existing = collection.get(where={"source_url": source_url})
            if existing and existing.get("ids"):
                collection.delete(ids=existing["ids"])
        except Exception:
            pass
    global _memory_chunks
    _memory_chunks = [c for c in _memory_chunks if c.get("metadata", {}).get("source_url") != source_url and c.get("metadata", {}).get("url") != source_url]
    save_memory_chunks()
    return 0

def score_chunk_relevance(query: str, chunk: Dict[str, Any]) -> float:
    text = chunk["text"].lower()
    query_words = [w.lower() for w in re.findall(r'\w+', query) if len(w) > 2]
    if not query_words:
        return 0.0
    score = 0.0
    for w in query_words:
        if w in text:
            score += 1.0
    unit_match = re.search(r'\bunit\s*([1-9])\b', query, re.IGNORECASE)
    if unit_match and f"unit {unit_match.group(1)}" in text:
        score += 5.0
    return score

def search_chunks(
    query: str,
    course: Optional[str] = None,
    semester: Optional[int] = None,
    doc_type: Optional[str] = None,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    extracted_chunks = []
    if HAS_CHROMA:
        try:
            collection = get_collection()
            conditions = []
            if course and course.upper() != "ALL":
                conditions.append({"": [{"course": course.upper()}, {"course": "ALL"}]})
            if doc_type:
                conditions.append({"doc_type": doc_type})
            where_filter = conditions[0] if len(conditions) == 1 else ({"": conditions} if len(conditions) > 1 else None)
            results = None
            if where_filter:
                results = collection.query(query_texts=[query], n_results=top_k, where=where_filter)
            if not results or not results.get("documents") or not results["documents"][0]:
                results = collection.query(query_texts=[query], n_results=top_k)
            if results and "documents" in results and results["documents"]:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
                distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
                for doc_text, meta, dist in zip(docs, metas, distances):
                    extracted_chunks.append({"text": doc_text, "metadata": meta, "distance": dist})
        except Exception as e:
            print(f"Chroma search exception: {e}")

    if not extracted_chunks and _memory_chunks:
        scored = []
        for c in _memory_chunks:
            meta = c.get("metadata", {})
            if course and course.upper() != "ALL":
                c_course = str(meta.get("course", "")).upper()
                if c_course != "ALL" and c_course != course.upper():
                    continue
            if doc_type and meta.get("doc_type") != doc_type:
                continue
            s = score_chunk_relevance(query, c)
            if s > 0:
                scored.append((s, c))
        scored.sort(key=lambda x: x[0], reverse=True)
        for s, c in scored[:top_k]:
            extracted_chunks.append({"text": c["text"], "metadata": c.get("metadata", {}), "distance": 1.0 / (s + 1.0)})

    unit_match = re.search(r'\bunit\s*([1-9])\b', query, re.IGNORECASE)
    if unit_match:
        target_unit = f"UNIT {unit_match.group(1)}"
        extracted_chunks.sort(key=lambda c: 0 if target_unit.lower() in c["text"].lower() else 1)

    return extracted_chunks
