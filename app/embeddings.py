
from pathlib import Path
import chromadb

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CHROMA_DIR = DATA_DIR / "chroma_db"
CHROMA_DIR.mkdir(parents=True, exist_ok=True)


COSINE_DISTANCE_THRESHOLD = 0.5

client = chromadb.PersistentClient(path=str(CHROMA_DIR))

collection = client.get_or_create_collection(
    name="taskflow_knowledge",
    metadata={"hnsw:space": "cosine"},
)


def add_text(text: str, text_id: str) -> None:
    collection.upsert(
        ids=[text_id],
        documents=[text],
    )


def search_text(query: str, limit: int = 5) -> list[dict]:
    results = collection.query(
        query_texts=[query],
        n_results=limit,
        include=["documents", "distances"],
    )

    matches = []

    if not results["ids"] or not results["ids"][0]:
        return matches

    for i, distance in enumerate(results["distances"][0]):
        if distance <= COSINE_DISTANCE_THRESHOLD:
            matches.append(
                {
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "distance": distance,
                }
            )

    matches.sort(key=lambda result: result["distance"])

    return matches
