"""
Milestone 4 — Embedding & Retrieval
Rice CS Unofficial Guide RAG Pipeline

Pipeline stage: Chunks → Embedding (all-MiniLM-L6-v2) → ChromaDB → Retrieval
Input:  chunks.json  (produced by ingest_and_chunk_local.py)
Output: ChromaDB collection stored in ./chroma_db/

Install dependencies first:
    pip install sentence-transformers chromadb
"""

import json
import chromadb
from pathlib import Path
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Config — matches planning.md Retrieval Approach section
# ---------------------------------------------------------------------------

CHUNKS_FILE    = "chunks.json"
CHROMA_DIR     = "./chroma_db"
COLLECTION_NAME = "rice_cs_reviews"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K          = 4   # your diagram says top-k = 4

# ---------------------------------------------------------------------------
# Evaluation queries from your planning.md
# ---------------------------------------------------------------------------

EVAL_QUERIES = [
    "Is Devika Subramanian a decent professor for my first semester?",
    "Is there grade inflation within Rice at all, or is it extremely difficult?",
    "Who is the department chair of the CS department and their contact information?",
    "What's the most recent workshop they've held for students?",
    "Is Rice University's CS department worth it for grad school in terms of job prospects?",
]


# ---------------------------------------------------------------------------
# Step 1 — Load chunks from JSON
# ---------------------------------------------------------------------------

def load_chunks(path: str = CHUNKS_FILE) -> list[dict]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(
            f"Could not find {path}. Run ingest_and_chunk_local.py first."
        )
    with p.open(encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"[LOADED] {len(chunks)} chunks from {path}")
    return chunks


# ---------------------------------------------------------------------------
# Step 2 — Set up ChromaDB collection
# ---------------------------------------------------------------------------

def get_or_create_collection(chroma_dir: str = CHROMA_DIR,
                              collection_name: str = COLLECTION_NAME):
    """
    PersistentClient saves the vector store to disk so you don't
    have to re-embed every time you restart the script.
    """
    client = chromadb.PersistentClient(path=chroma_dir)
    # Delete existing collection so we start fresh on each run
    try:
        client.delete_collection(collection_name)
    except Exception:
        pass
    collection = client.create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}   # cosine similarity = lower score is better
    )
    print(f"[CHROMA] Collection '{collection_name}' created at {chroma_dir}")
    return collection


# ---------------------------------------------------------------------------
# Step 3 — Embed chunks and store in ChromaDB
# ---------------------------------------------------------------------------

def embed_and_store(chunks: list[dict], collection) -> SentenceTransformer:
    print(f"\n[EMBED] Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    texts     = [c["text"]        for c in chunks]
    ids       = [c["chunk_id"]    for c in chunks]
    metadatas = [
        {
            "source_id":   c["source_id"],
            "source_name": c["source_name"],
            "filename":    c["filename"],
            "token_count": c["token_count"],
            # chunk position within its source document
            "chunk_index": i,
        }
        for i, c in enumerate(chunks)
    ]

    print(f"[EMBED] Embedding {len(texts)} chunks (this takes ~10-30 seconds)…")
    embeddings = model.encode(texts, show_progress_bar=True).tolist()

    # ChromaDB has a max batch size; insert in batches of 100 to be safe
    batch_size = 100
    for start in range(0, len(chunks), batch_size):
        end = start + batch_size
        collection.add(
            ids        = ids[start:end],
            embeddings = embeddings[start:end],
            documents  = texts[start:end],
            metadatas  = metadatas[start:end],
        )

    print(f"[CHROMA] Stored {len(chunks)} embeddings with metadata")
    return model


# ---------------------------------------------------------------------------
# Step 4 — Retrieval function
# ---------------------------------------------------------------------------

def retrieve(query: str,
             collection,
             model: SentenceTransformer,
             top_k: int = TOP_K) -> list[dict]:
    """
    Embed the query, search ChromaDB for the top-k closest chunks.
    Returns a list of dicts with text, metadata, and distance score.
    """
    query_embedding = model.encode([query]).tolist()

    results = collection.query(
        query_embeddings = query_embedding,
        n_results        = top_k,
        include          = ["documents", "metadatas", "distances"],
    )

    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({
            "text":        doc,
            "source_name": meta["source_name"],
            "filename":    meta["filename"],
            "chunk_index": meta["chunk_index"],
            "distance":    round(dist, 4),
        })
    return hits


# ---------------------------------------------------------------------------
# Step 5 — Print retrieval results with quality assessment
# ---------------------------------------------------------------------------

def assess_distance(score: float) -> str:
    if score < 0.3:
        return "STRONG match"
    elif score < 0.6:
        return "OK match"
    else:
        return "WEAK match — may be off-topic"


def run_eval_queries(collection, model):
    print("\n" + "=" * 60)
    print("RETRIEVAL EVALUATION — 3 test queries")
    print("=" * 60)

    for i, query in enumerate(EVAL_QUERIES[:3], 1):
        print(f"\n--- Query {i} ---")
        print(f"Q: {query}\n")

        hits = retrieve(query, collection, model, TOP_K)

        for rank, hit in enumerate(hits, 1):
            assessment = assess_distance(hit["distance"])
            print(f"  Rank {rank} | distance: {hit['distance']} | {assessment}")
            print(f"  Source: {hit['source_name']} (chunk {hit['chunk_index']})")
            print(f"  Text: {hit['text'][:300]}…")
            print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Rice CS RAG Pipeline — Milestone 4: Embed & Retrieve")
    print(f"Model: {EMBEDDING_MODEL} | Top-k: {TOP_K}")
    print("=" * 60)

    chunks     = load_chunks()
    collection = get_or_create_collection()
    model      = embed_and_store(chunks, collection)

    run_eval_queries(collection, model)

    print("\n" + "=" * 60)
    print("DONE — ChromaDB is saved to ./chroma_db/")
    print("Import retrieve() into your generation script for Milestone 5.")
    print("=" * 60)


if __name__ == "__main__":
    main()
