# ingest.py — P2 skeleton. Fill the blanks; peeking at module12/ingest.py is expected.
#
# Reuse map says: chunking logic ports over, embed() ports over. The ONLY genuinely
# new thing in this file is the write path — SQLAlchemy INSERT instead of
# collection.add() — plus tracking section_idx, which module12 threw away.

from pathlib import Path
import ollama

from config import EMBED_MODEL
from models import Chunk, SessionLocal, init_db

CORPUS = Path("./data/andrew_college_sectioned.txt")
FIXED_SIZE = 1500
OVERLAP = 500


# --- ported unchanged from module12 ------------------------------------------
def embed(text: str) -> list:
    """Return the embedding vector for one string."""
    response = ollama.embeddings(model=EMBED_MODEL, prompt=text)
    return response["embedding"]


def fixed_size_chunks(text: str, size: int = FIXED_SIZE, overlap: int = OVERLAP) -> list[str]:
    """Slice an oversized section into overlapping windows. Straight port."""
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


# --- MODIFIED: this is the one function that changes shape -------------------
def load_chunks(path: Path) -> list[tuple[int, str]]:
    """
    Read the corpus and split into chunks, KEEPING the section each chunk came from.

    module12's version returned list[str] and discarded section identity. This one
    returns (section_idx, chunk_text) pairs so section_idx has something to store.

    Everything else — the <<<SECTION>>> split, the size test, the overlap windowing —
    is identical to module12/ingest.py. Peek freely.
    """
    text = path.read_text()
    sections = text.split("<<<SECTION>>>")            # the marker from the 2026-06-18 session

    pairs: list[tuple[int, str]] = []

    # enumerate() gives you the index AND the value — the index is the whole point here.
    for idx, section in enumerate(sections):
        if len(section) <= FIXED_SIZE:
            pairs.append((idx, section.strip()))
        else:
            # every window from this section shares the SAME section index
            for window in fixed_size_chunks(section):
                pairs.append((idx, window.strip()))

    # module12 dropped empty chunks at the end. Same idea, but you're filtering
    # tuples now, so unpack in the comprehension.
    return [(i, t) for i, t in pairs if t.strip()]


# --- NEW: the write path -----------------------------------------------------
def wipe() -> None:
    """
    module12 did `client.delete_collection(COLLECTION)` to nuke stale data before
    re-ingesting. Same need here — running this twice should REPLACE the corpus,
    not double it. Simplest equivalent: delete every row.
    """
    with SessionLocal() as session:
        session.query(Chunk).delete()
        session.commit()


def ingest() -> int:
    """Load → chunk → embed → insert. Returns how many rows were written."""
    pairs = load_chunks(CORPUS)
    print(f"{len(pairs)} chunks")
    print(f"longest: {max(len(t) for i, t in pairs)}")

    rows = []
    for i, (section_idx, chunk_text) in enumerate(pairs):
        # Progress matters — this is N sequential Ollama calls and it is not fast.
        print(f"  embedding {i + 1}/{len(pairs)}", end="\r")

        vector = embed(chunk_text)          # which function turns text into a vector?

        # No id= here: the column is SERIAL, so Postgres assigns it.
        # pgvector's type adapter takes a plain Python list[float] as-is —
        # no json.dumps, no str() conversion.
        rows.append(Chunk(chunk_text=chunk_text, embedding=vector, section_idx=section_idx))

    with SessionLocal() as session:
        session.add_all(rows)                 # add MANY objects at once, not one at a time
        session.commit()                     # nothing is written until this happens

    return len(rows)


if __name__ == "__main__":
    init_db()          # no-op if the table already exists
    wipe()
    n = ingest()
    print(f"\nstored {n} chunks in Postgres")
