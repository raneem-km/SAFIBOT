import os
import chromadb
from typing import List, Dict, Any, Optional

import shutil
IS_VERCEL = os.getenv("VERCEL") == "1" or os.getenv("VERCEL_ENV") is not None
ORIGINAL_CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "database", "chroma_db")

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

def get_chroma_client():
    os.makedirs(CHROMA_PATH, exist_ok=True)
    return chromadb.PersistentClient(path=CHROMA_PATH)

def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"description": "SafiBot College Academic & Document Knowledge Base"}
    )

def index_document_chunks(chunks: List[Dict[str, Any]]) -> int:
    """
    Inserts a list of chunks into ChromaDB.
    Each chunk is a dict: {'id': ..., 'text': ..., 'metadata': {...}}
    """
    if not chunks:
        return 0
        
    collection = get_collection()
    
    ids = [c["id"] for c in chunks]
    documents = [c["text"] for c in chunks]
    metadatas = [c["metadata"] for c in chunks]
    
    # Chroma upsert ensures idempotency
    collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas
    )
    return len(chunks)

def delete_document_chunks(doc_id: int):
    """
    Deletes all chunks associated with a specific doc_id.
    """
    collection = get_collection()
    collection.delete(where={"doc_id": doc_id})

def delete_chunks_by_url(source_url: str):
    """
    Deletes all ChromaDB chunks associated with a specific website source_url.
    Retrieves matching IDs first for safe, reliable deletion.
    """
    collection = get_collection()
    try:
        existing = collection.get(where={"source_url": source_url})
        if existing and existing.get("ids"):
            collection.delete(ids=existing["ids"])
            return len(existing["ids"])
        # Also check with url key
        existing_url = collection.get(where={"url": source_url})
        if existing_url and existing_url.get("ids"):
            collection.delete(ids=existing_url["ids"])
            return len(existing_url["ids"])
    except Exception as e:
        print(f"Notice: deletion by source_url ({source_url}) encountered: {e}")
    return 0


def search_chunks(
    query: str,
    course: Optional[str] = None,
    semester: Optional[int] = None,
    doc_type: Optional[str] = None,
    top_k: int = 4
) -> List[Dict[str, Any]]:
    """
    Searches ChromaDB for semantic relevance.
    Applies course and doc_type filtering if specified.
    """
    collection = get_collection()
    
    conditions = []
    if course and course.upper() != "ALL":
        conditions.append({
            "$or": [
                {"course": course.upper()},
                {"course": "ALL"}
            ]
        })
    if doc_type:
        conditions.append({"doc_type": doc_type})
        
    where_filter = None
    if len(conditions) == 1:
        where_filter = conditions[0]
    elif len(conditions) > 1:
        where_filter = {"$and": conditions}
    
    results = None
    try:
        if where_filter:
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter
            )
    except Exception as e:
        print(f"Filtered query failed ({e}), falling back to broader query.")
        
    if not results or not results.get("documents") or not results["documents"][0]:
        # Fallback to query without doc_type or where_filter
        try:
            results = collection.query(
                query_texts=[query],
                n_results=top_k
            )
        except Exception as e:
            print(f"Fallback query error: {e}")
            results = {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        
    extracted_chunks = []
    if results and "documents" in results and results["documents"]:
        docs = results["documents"][0]
        metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
        distances = results["distances"][0] if "distances" in results else [0.0] * len(docs)
        
        for doc_text, meta, dist in zip(docs, metas, distances):
            extracted_chunks.append({
                "text": doc_text,
                "metadata": meta,
                "distance": dist
            })
            
    # Unit prioritization if "unit X" is in query
    import re
    unit_match = re.search(r'\bunit\s*([1-9])\b', query, re.IGNORECASE)
    if unit_match:
        target_unit = f"UNIT {unit_match.group(1)}"
        extracted_chunks.sort(
            key=lambda c: 0 if target_unit.lower() in c["text"].lower() else 1
        )
            
    return extracted_chunks

