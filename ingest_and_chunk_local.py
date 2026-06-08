"""
Milestone 3 — Document Ingestion & Chunking (Local Files Version)
Rice CS Unofficial Guide RAG Pipeline

How to use:
1. Create a folder called raw_docs/ in the same directory as this script
2. For each source, paste the review/post text into a .txt file:
      raw_docs/s01_ratemyprofessors.txt
      raw_docs/s02_reddit_cs.txt
      raw_docs/s03_academicjobs.txt
      raw_docs/s04_quora_profrecs.txt
      raw_docs/s05_riceedu.txt
      raw_docs/s06_facebook.txt
      raw_docs/s07_quora_gradprospects.txt
      raw_docs/s08_reddit_postgrad.txt
      raw_docs/s09_gradcafe.txt
      raw_docs/s10_linkedin.txt
3. Run: python ingest_and_chunk_local.py
4. Outputs: raw_text.json and chunks.json
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, asdict

# ---------------------------------------------------------------------------
# Config — matches planning.md exactly
# ---------------------------------------------------------------------------

CHUNK_SIZE  = 300   # tokens
OVERLAP     = 30    # tokens
RAW_DIR     = Path("raw_docs")
RAW_OUTPUT  = "raw_text.json"
CHUNK_OUTPUT = "chunks.json"

SOURCES = [
    {"id": "s01", "name": "RateMyProfessors",       "file": "ratemyprofessor.txt"},
    {"id": "s02", "name": "Reddit",                 "file": "reddit.txt"},
    {"id": "s03", "name": "AcademicJobs",            "file": "academicjobs.txt"},
    {"id": "s04", "name": "Quora – Prof recs",       "file": "quoraprofessors.txt"},
    {"id": "s05", "name": "About the Degree",        "file": "aboutthedegreefromrice.txt"},
    {"id": "s06", "name": "Facebook – RiceCS",       "file": "recentpostsfromfacebook.txt"},
    {"id": "s07", "name": "Quora – Worth it",        "file": "worthfromquora.txt"},
    {"id": "s08", "name": "Quora – Why attend",      "file": "whyattendquora.txt"},
    {"id": "s09", "name": "GradCafe – PhD",          "file": "gradcafe.txt"},
    {"id": "s10", "name": "LinkedIn – RiceCS",       "file": "linkedin.txt"},
]

# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    chunk_id:    str
    source_id:   str
    source_name: str
    filename:    str
    text:        str
    token_count: int


# ---------------------------------------------------------------------------
# Step 1 — Load raw text from local files
# ---------------------------------------------------------------------------

def load_raw_docs() -> list[dict]:
    """Load each .txt file and return list of {source, raw_text} dicts."""
    docs = []
    for source in SOURCES:
        path = RAW_DIR / source["file"]
        if not path.exists():
            print(f"  [MISSING] {path} — skipping. Add this file to raw_docs/")
            continue
        raw = path.read_text(encoding="utf-8", errors="replace")
        docs.append({"source": source, "raw_text": raw})
        print(f"  [LOADED] {source['name']} — {len(raw)} characters")
    return docs


# ---------------------------------------------------------------------------
# Step 2 — Clean text
# Remove: HTML tags, entities, nav boilerplate, ads, share buttons, footers
# Keep:   Review text, opinions, ratings, professor names, course numbers
# ---------------------------------------------------------------------------

def clean_text(raw: str) -> str:
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", raw)

    # Decode HTML entities
    entities = {
        "&amp;": "&", "&lt;": "<", "&gt;": ">",
        "&quot;": '"', "&#39;": "'", "&nbsp;": " ",
        "&mdash;": "—", "&ndash;": "–", "&hellip;": "...",
    }
    for ent, char in entities.items():
        text = text.replace(ent, char)

    # Remove leftover URLs
    text = re.sub(r"https?://\S+", "", text)

    # Remove common boilerplate phrases (add more as you spot them)
    boilerplate = [
        r"Cookie Policy.*",
        r"Privacy Policy.*",
        r"Terms of Service.*",
        r"Sign up.*",
        r"Log in.*",
        r"Share this.*",
        r"Read more.*",
        r"\d+ upvotes?",
        r"\d+ comments?",
        r"Reply\s*$",
        r"Report\s*$",
        r"See more\s*$",
        r"Show more\s*$",
        r"Advertisement",
        r"Sponsored",
        # RateMyProfessors UI noise
        r"Thumbs up\s*\d*",
        r"Thumbs down\s*\d*",
        r"Helpful\s*$",
        r"Arrow Icon",
        r"Rate\s*$",
        r"Compare\s*$",
        r"Rating Distribution",
        r"Similar Professors",
        r"Would Take Again:.*",
        r"For Credit:.*",
        r"Attendance:.*",
        r"Textbook:.*",
        r"All courses\s*$",
        r"Awesome \d+\s*\d*",
        r"Great \d+\s*\d*",
        r"Good \d+\s*\d*",
        r"OK \d+\s*\d*",
        r"Awful \d+\s*\d*",
    ]
    for pattern in boilerplate:
        text = re.sub(pattern, "", text, flags=re.IGNORECASE)

    # Remove non-printable characters
    text = re.sub(r"[^\x20-\x7E\n]", " ", text)

    # Collapse extra whitespace and blank lines
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# Step 3 — Tokenize (whitespace split — no external libraries needed)
# ---------------------------------------------------------------------------

def tokenize(text: str) -> list[str]:
    return text.split()

def detokenize(tokens: list[str]) -> str:
    return " ".join(tokens)


# ---------------------------------------------------------------------------
# Step 4 — Sliding window chunker (300 tokens, 30 overlap)
# ---------------------------------------------------------------------------

def chunk_tokens(tokens: list[str],
                 chunk_size: int = CHUNK_SIZE,
                 overlap: int = OVERLAP) -> list[str]:
    """
    Sliding window: each chunk is `chunk_size` tokens.
    Advances by `chunk_size - overlap` (270 tokens) each step.
    The 30-token overlap preserves context across chunk boundaries.
    """
    if not tokens:
        return []

    step   = chunk_size - overlap  # 270
    chunks = []
    start  = 0

    while start < len(tokens):
        window = tokens[start : start + chunk_size]
        chunks.append(detokenize(window))
        if start + chunk_size >= len(tokens):
            break
        start += step

    return chunks


# ---------------------------------------------------------------------------
# Step 5 — Orchestrate
# ---------------------------------------------------------------------------

def run_pipeline():
    print("=" * 60)
    print("Rice CS RAG Pipeline — Milestone 3: Ingest & Chunk")
    print(f"Config: chunk_size={CHUNK_SIZE}, overlap={OVERLAP}")
    print("=" * 60)

    # --- Load ---
    print("\n[STAGE 1] Loading raw documents from raw_docs/")
    docs = load_raw_docs()

    if not docs:
        print("\n[ERROR] No documents found. Create raw_docs/ and add your .txt files.")
        return

    # Save raw text snapshot (good habit before cleaning)
    raw_snapshot = [{"source": d["source"]["name"],
                     "file": d["source"]["file"],
                     "raw_text": d["raw_text"]} for d in docs]
    Path(RAW_OUTPUT).write_text(
        json.dumps(raw_snapshot, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\n[SAVED] Raw text snapshot → {RAW_OUTPUT}")

    # --- Clean & print first doc for inspection ---
    print("\n[STAGE 2] Cleaning documents")
    cleaned_docs = []
    for d in docs:
        cleaned = clean_text(d["raw_text"])
        cleaned_docs.append({"source": d["source"], "cleaned_text": cleaned})
        print(f"  {d['source']['name']}: {len(d['raw_text'])} chars → {len(cleaned)} chars after cleaning")

    # Print first document so you can inspect it
    print("\n" + "=" * 60)
    print("INSPECTION — First cleaned document (read this carefully):")
    print("Look for: leftover HTML, &amp; entities, nav text, cookie banners")
    print("=" * 60)
    first = cleaned_docs[0]
    print(f"Source: {first['source']['name']}\n")
    print(first["cleaned_text"][:2000])
    print("... [truncated to 2000 chars for inspection]")

    # --- Chunk ---
    print("\n[STAGE 3] Chunking")
    all_chunks: list[Chunk] = []
    chunk_counter = 0

    for d in cleaned_docs:
        tokens  = tokenize(d["cleaned_text"])
        windows = chunk_tokens(tokens, CHUNK_SIZE, OVERLAP)
        print(f"  {d['source']['name']}: {len(tokens)} tokens → {len(windows)} chunks")

        for window_text in windows:
            chunk_counter += 1
            all_chunks.append(Chunk(
                chunk_id    = f"chunk_{chunk_counter:04d}",
                source_id   = d["source"]["id"],
                source_name = d["source"]["name"],
                filename    = d["source"]["file"],
                text        = window_text,
                token_count = len(window_text.split()),
            ))

    # --- Print 5 representative chunks for inspection ---
    print("\n" + "=" * 60)
    print("INSPECTION — 5 representative chunks")
    print("For each, ask: does this make sense on its own?")
    print("Could someone answer a question from this chunk alone?")
    print("=" * 60)

    step = max(1, len(all_chunks) // 5)
    sample_indices = [0, step, step*2, step*3, len(all_chunks)-1]

    for i, idx in enumerate(sample_indices):
        if idx >= len(all_chunks):
            continue
        c = all_chunks[idx]
        print(f"\n--- Chunk {i+1} (index {idx}) ---")
        print(f"Source : {c.source_name}")
        print(f"Tokens : {c.token_count}")
        print(f"Text   : {c.text}\n")

    # --- Summary ---
    sizes = [c.token_count for c in all_chunks]
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"  Total chunks : {len(all_chunks)}")
    print(f"  Min tokens   : {min(sizes)}")
    print(f"  Max tokens   : {max(sizes)}")
    print(f"  Avg tokens   : {sum(sizes)/len(sizes):.1f}")

    # Warn if outside healthy range
    if len(all_chunks) < 50:
        print("\n  [WARN] Fewer than 50 chunks — chunks may be too large,")
        print("         or you need more source text. Consider lowering CHUNK_SIZE")
        print("         or adding more content to your raw_docs/ files.")
    elif len(all_chunks) > 2000:
        print("\n  [WARN] More than 2000 chunks — chunks may be too small.")
        print("         Consider increasing CHUNK_SIZE.")
    else:
        print("\n  [OK] Chunk count is in the healthy range (50–2000).")

    # --- Save ---
    Path(CHUNK_OUTPUT).write_text(
        json.dumps([asdict(c) for c in all_chunks], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )
    print(f"\n[DONE] Saved {len(all_chunks)} chunks → {CHUNK_OUTPUT}")
    print("       This file is your input for Milestone 4 (embedding + ChromaDB).")


if __name__ == "__main__":
    run_pipeline()
