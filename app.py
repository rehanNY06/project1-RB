"""
Milestone 5 — Generation & Interface
Rice CS Unofficial Guide RAG Pipeline

Pipeline stage: Query → Retrieval → Groq LLM → Grounded Answer + Sources
Interface: Gradio web UI at http://localhost:7860

Setup:
1. pip install groq gradio sentence-transformers chromadb python-dotenv
2. Add GROQ_API_KEY=your_key_here to your .env file
   Get a free key at: https://console.groq.com
3. Run: python app.py
"""

import os
import json
import chromadb
import gradio as gr
from groq import Groq
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

load_dotenv()

GROQ_API_KEY    = os.getenv("GROQ_API_KEY")
GROQ_MODEL      = "llama-3.3-70b-versatile"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CHROMA_DIR      = "./chroma_db"
COLLECTION_NAME = "rice_cs_reviews"
TOP_K           = 4

# ---------------------------------------------------------------------------
# Load embedding model and ChromaDB collection once at startup
# ---------------------------------------------------------------------------

print("[STARTUP] Loading embedding model...")
embed_model = SentenceTransformer(EMBEDDING_MODEL)

print("[STARTUP] Connecting to ChromaDB...")
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
collection = chroma_client.get_collection(name=COLLECTION_NAME)

print("[STARTUP] Initializing Groq client...")
groq_client = Groq(api_key=GROQ_API_KEY)

print("[STARTUP] Ready.\n")


# ---------------------------------------------------------------------------
# Retrieval — reused from Milestone 4
# ---------------------------------------------------------------------------

def retrieve(query: str, top_k: int = TOP_K) -> list[dict]:
    """Embed query and return top-k most relevant chunks with metadata."""
    query_embedding = embed_model.encode([query]).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
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
            "distance":    round(dist, 4),
        })
    return hits


# ---------------------------------------------------------------------------
# Generation — grounded, sources enforced programmatically
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are a helpful assistant that answers questions about 
Rice University's Computer Science department.

CRITICAL RULES — you must follow these exactly:
1. Answer ONLY using the information provided in the context documents below.
2. Do NOT use any outside knowledge, even if you think it's correct.
3. If the context does not contain enough information to answer the question, 
   respond with exactly: "I don't have enough information on that based on the 
   available student reviews and sources."
4. Be specific and quote or closely paraphrase the context when possible.
5. Do NOT make up professor names, ratings, policies, or contact details.
6. When citing a source, use the source name given in brackets (e.g. 
   "RateMyProfessors", "Reddit", "Quora – Worth it") — never say 
   "Document 1" or "Document 2".
"""

def build_context_block(hits: list[dict]) -> str:
    """Format retrieved chunks into a numbered context block for the prompt."""
    lines = []
    for i, hit in enumerate(hits, 1):
        lines.append(f"[Source: {hit['source_name']}]")
        lines.append(hit["text"])
        lines.append("")
    return "\n".join(lines)


def generate_answer(query: str, hits: list[dict]) -> str:
    """Send query + retrieved context to Groq and return grounded answer."""
    context = build_context_block(hits)

    user_message = f"""Context documents:
{context}

Question: {query}

Answer using only the context documents above. If the answer isn't in the 
documents, say you don't have enough information."""

    response = groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_message},
        ],
        temperature=0.2,   # low temp = more faithful to context
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Source attribution — programmatically guaranteed, not left to the LLM
# ---------------------------------------------------------------------------

def format_sources(hits: list[dict]) -> list[str]:
    """
    Build source list from metadata — independent of what the LLM says.
    Even if the LLM forgets to cite, sources are always shown.
    """
    seen = set()
    sources = []
    for hit in hits:
        label = f"{hit['source_name']} (distance: {hit['distance']})"
        if label not in seen:
            seen.add(label)
            sources.append(label)
    return sources


# ---------------------------------------------------------------------------
# End-to-end ask() function
# ---------------------------------------------------------------------------

def ask(question: str) -> dict:
    """
    Full RAG pipeline:
    1. Retrieve top-k chunks
    2. Generate grounded answer via Groq
    3. Return answer + programmatic source attribution
    """
    if not question.strip():
        return {"answer": "Please enter a question.", "sources": []}

    hits    = retrieve(question, TOP_K)
    answer  = generate_answer(question, hits)
    sources = format_sources(hits)

    return {"answer": answer, "sources": sources}


# ---------------------------------------------------------------------------
# Gradio Interface
# ---------------------------------------------------------------------------

def handle_query(question: str):
    result  = ask(question)
    sources = "\n".join(f"• {s}" for s in result["sources"])
    return result["answer"], sources


with gr.Blocks(title="Rice CS Unofficial Guide") as demo:
    gr.Markdown("## 🦉 Rice CS Unofficial Guide")
    gr.Markdown(
        "Ask questions about Rice University's CS department based on "
        "real student reviews, Reddit posts, Quora answers, and more."
    )

    with gr.Row():
        inp = gr.Textbox(
            label="Your question",
            placeholder="e.g. Is Devika Subramanian a good professor for first semester?",
            lines=2,
        )

    btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        answer = gr.Textbox(label="Answer", lines=8)

    with gr.Row():
        sources = gr.Textbox(label="Retrieved from (sources)", lines=4)

    # Example questions from your eval plan
    gr.Examples(
        examples=[
            "Is Devika Subramanian a decent professor for my first semester?",
            "Is there grade inflation within Rice at all, or is it extremely difficult?",
            "Who is the department chair of the CS department?",
            "Is Rice University's CS department worth it for grad school?",
            "What do students say about CS professors at Rice?",
        ],
        inputs=inp,
    )

    btn.click(handle_query, inputs=inp, outputs=[answer, sources])
    inp.submit(handle_query, inputs=inp, outputs=[answer, sources])


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    demo.launch()
