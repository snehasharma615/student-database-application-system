import os
from pathlib import Path
import chromadb
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CHROMA_PATH = Path(os.getenv("CHROMA_PATH", str(BASE_DIR / "chroma_db")))
COLLECTION_NAME = os.getenv("CHROMA_COLLECTION", "student_knowledge")

_client = chromadb.PersistentClient(path=str(CHROMA_PATH))
_collection = _client.get_or_create_collection(name=COLLECTION_NAME)

def add_knowledge(documents: list[str], ids: list[str], metadatas: list[dict] | None = None):
    _collection.upsert(
        ids=ids,
        documents=documents,
        metadatas=metadatas,
    )

def search_knowledge(query: str, n_results: int = 3) -> list[str]:
    if _collection.count() == 0:
        return []
    result = _collection.query(
        query_texts=[query],
        n_results=min(n_results, _collection.count()),
    )
    return result.get("documents", [[]])[0]

def collection_count() -> int:
    return _collection.count()
