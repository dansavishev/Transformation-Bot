import logging
from typing import Optional
from config import CHROMA_PATH, RAG_TOP_K

logger = logging.getLogger(__name__)

COLLECTION_NAME = "knowledge_base"

_client: Optional[object] = None
_collection = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        ef = ONNXMiniLM_L6_V2()
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=ef,
        )
    return _collection


def add_chunks(chunks: list[str], metadatas: list[dict], ids: list[str]) -> None:
    col = _get_collection()
    col.add(documents=chunks, metadatas=metadatas, ids=ids)
    logger.info("Added %d chunks to ChromaDB", len(chunks))


def search(query: str, top_k: int = RAG_TOP_K) -> list[str]:
    col = _get_collection()
    try:
        results = col.query(query_texts=[query], n_results=top_k)
        docs = results.get("documents", [[]])[0]
        return docs
    except Exception as exc:
        logger.warning("RAG search failed: %s", exc)
        return []


def delete_by_source(source: str) -> int:
    col = _get_collection()
    results = col.get(where={"source": source})
    ids = results.get("ids", [])
    if ids:
        col.delete(ids=ids)
    return len(ids)


def unload() -> None:
    global _client, _collection
    _collection = None
    _client = None
    import gc
    gc.collect()


def list_sources() -> list[dict]:
    col = _get_collection()
    results = col.get(include=["metadatas"])
    metadatas = results.get("metadatas", [])
    seen: dict[str, dict] = {}
    for m in metadatas:
        src = m.get("source", "unknown")
        if src not in seen:
            seen[src] = {"source": src, "date": m.get("date", ""), "chunks": 0}
        seen[src]["chunks"] += 1
    return list(seen.values())
