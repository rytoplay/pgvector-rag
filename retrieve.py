# retrieve.py — P3 skeleton. This is the file the whole project exists for.
#
# module12's retrieve() called ChromaDB:
#     results = collection.query(query_embeddings=[qvec], n_results=k)
#     docs   = results["documents"][0]
#     dists  = results["distances"][0]
#     return [d for d, dist in zip(docs, dists) if dist <= max_distance]
#
# Here it's a SELECT. Same four ideas — embed the question, order by distance,
# take k, drop anything too far — but expressed as SQL instead of an API call.

from sqlalchemy import select

from config import TOP_K, MAX_DISTANCE
from models import Chunk, SessionLocal
from ingest import embed          # safe to import: ingest's work is under __main__


def retrieve(
    question: str,
    k: int = TOP_K,
    max_distance: float | None = MAX_DISTANCE,
    section_idx: int | None = None,
) -> list[tuple[str, float]]:
    """
    Return up to k (chunk_text, distance) pairs, nearest first.

    Fewer than k comes back when max_distance filters some out — same behavior as
    module12, which retrieved k from Chroma and then dropped the far ones in Python.
    """
    qvec = embed(question)                    # question and chunks must go through the
                                             # SAME embedding model or the vectors aren't
                                             # comparable at all

    # .cosine_distance() is pgvector's SQLAlchemy comparator — it compiles to the
    # <=> operator. .label() names the computed column so you can order by it and
    # read it back out.
    distance = Chunk.embedding.cosine_distance(qvec).label("distance")

    stmt = select(Chunk.chunk_text, distance)

    # --- the thing ChromaDB cannot do ---------------------------------------
    # An ordinary WHERE, on ordinary relational metadata, in the SAME query as the
    # vector search. This is the interview line made real. Optional here, but the
    # capability is the point.
    if section_idx is not None:
        stmt = stmt.where(Chunk.section_idx == section_idx)

    # nearest first, then cut to k. Ascending, because these are DISTANCES —
    # smaller means more similar.
    stmt = stmt.order_by(distance).limit(k)

    with SessionLocal() as session:
        rows = session.execute(stmt).all()   # list of (chunk_text, distance) tuples

    if max_distance is None:                 # None means "no threshold yet" (P3 sets it)
        return [(text, dist) for text, dist in rows]

    return [(text, dist) for text, dist in rows if dist <= max_distance]


if __name__ == "__main__":
    from tuning_questions import EVAL_SET

    for q in EVAL_SET:
        print(f"\n=== [{q['id']}] {q['category']}: {q['question']}")
        for text, dist in retrieve(q["question"], k=8, max_distance=None):
            print(f"  {dist:.3f}  {text[:90]!r}")