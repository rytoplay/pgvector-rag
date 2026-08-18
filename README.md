# pgvector-rag

A RAG retrieval layer ported from ChromaDB to **PostgreSQL + pgvector**, measured against the
same corpus and the same 12-question evaluation set — so the migration produced a real
before-and-after instead of an impression.

**Result: 8/12, against a 7/12 ChromaDB baseline. Verified reproducible across runs.**

---

## The interesting finding is a negative one

The obvious way to make a RAG pipeline refuse unanswerable questions is a distance threshold:
if the nearest chunk is further away than *X*, say "I don't know." I swept all twelve eval
questions looking for a usable value of *X*.

**No value works on this corpus.**

| | nearest-chunk distance |
|---|---|
| B1 — *"how much does tuition cost?"* (**answer is not in the corpus**) | **0.210** |
| D2 — correct answer | 0.205 |
| A2, C1, C2, D1, F2 — correct answers | 0.237 – 0.262 |
| A1 — correct answer | 0.325 |
| F1 — correct answer | **0.360** |

B1's nearest chunk beats every correct answer except one. Any threshold strict enough to
reject it destroys the eval set; any threshold loose enough to keep F1 admits B1 anyway.

**Root cause:** cosine distance measures *topical proximity*, not *answer containment*. Those
two things diverge precisely when a question concerns something the corpus discusses at length
without ever answering — this manual is saturated with tuition language and never states a
price.

**The fix was architectural, not numerical.** Rejection moved out of the distance filter and
into the LLM re-ranker and the grounding prompt — a reader can tell that a page about tuition
grants doesn't state a price, and cosine distance structurally cannot. With distance filtering
switched off entirely, **all three unanswerable questions were correctly refused.**

A related heuristic — that answerable questions show a sharp distance "elbow" while
unanswerable ones plateau — looked compelling on the same four-question sample and **also
failed at twelve**: C2, D1 and F1 are all answerable yet plateau, because several chunks
legitimately cover those topics. Two confident conclusions drawn from four data points, both
demolished by the full run. Worth stating plainly rather than quietly deleting, since the
generalizable lesson is about sample size, not about pgvector.

## Why pgvector instead of a vector database

Vectors live as a column in the existing relational database, so an ordinary `WHERE` on
relational metadata and a vector `ORDER BY` resolve in **one statement, one round trip**, and
the rows that come back are already filtered. With a separate vector store you query it, get
IDs back, then round-trip to Postgres to filter — and you may end up with fewer than *k* after
filtering, so you over-fetch and guess.

```python
distance = Chunk.embedding.cosine_distance(qvec).label("distance")
stmt = select(Chunk.chunk_text, distance)
if section_idx is not None:
    stmt = stmt.where(Chunk.section_idx == section_idx)   # ← the part Chroma can't do
stmt = stmt.order_by(distance).limit(k)
```

## Pipeline

```
corpus ──▶ chunk ──▶ embed ──▶ Postgres/pgvector
                                     │
question ──▶ embed ──▶ retrieve wide (k=15) ──▶ LLM re-rank ──▶ grounded answer ──▶ LLM judge
```

| Stage | File | Notes |
|---|---|---|
| Schema | `models.py` | `Chunk` with `embedding vector(768)` + `section_idx` for metadata filtering |
| Ingest | `ingest.py` | Section-aware split on `<<<SECTION>>>`, then fixed-size windows with overlap. 596 chunks. |
| Retrieve | `retrieve.py` | `cosine_distance()` → the `<=>` operator; optional metadata `WHERE` in the same query |
| Answer | `answer.py` | Retrieve wide → LLM re-rank → grounded generation → LLM-as-judge scoring |
| Eval set | `tuning_questions.py` | 12 questions across 6 categories, including 3 deliberately unanswerable |

**Corpus:** a college policy manual — 596 chunks, `nomic-embed-text` (768-dim).
**Models:** Ollama locally — `nomic-embed-text` for embeddings, `gemma2:9b` for re-ranking,
answering, and judging.

## Failure analysis

Diagnosing the four misses turned out to be more useful than the score:

| # | Cause | Fixable |
|---|---|---|
| **A1** | **Chunk-boundary artifact.** The retrieved window starts mid-word (`"eed $1000..."`), stranding the sentence opening that attributes those penalties to *less than* one ounce. Right chunk, wrong boundary — the model quoted the >1oz half and refused the rest because the amounts had no subject. | Yes — sentence-aware chunking or larger overlap |
| **C2** | Retrieval found the right section but surfaced Title IX *definitions* rather than the *procedure* being asked about. | Partly — `k`/re-rank tuning |
| **E2** | Conservative refusal on a hallucination trap. Notably it did **not** invent an answer, which is the failure mode that would matter in production. | Prompt work |
| **F1** | **Probably an eval-set flaw, not a pipeline bug.** The answer given is accurate and responsive; the recorded ground truth only captures one of two valid answers. Left as-is — silently "fixing" the pipeline to match a narrow ground truth is overfitting. | Fix the test, not the code |

## Reproducibility

`evaluate()` was run twice and produced not merely the same total but the same twelve per-item
verdicts. Worth checking, because temperature 0 gives greedy decoding but **not guaranteed
determinism**: floating-point addition isn't associative, so parallel reductions can shift
logits slightly, argmax turns that into a coin flip on near-ties, and autoregression turns one
flipped token into a different answer. Running locally, one request at a time, avoids the
cross-request batching effects you'd get through a hosted API.

## Running it

Requires PostgreSQL with the `pgvector` extension, and Ollama with `nomic-embed-text` and
`gemma2:9b` pulled.

```bash
pip install -r requirements.txt
cp .env.example .env          # then fill in your local Postgres credentials
psql -d pgvector_rag -c "CREATE EXTENSION IF NOT EXISTS vector;"

python ingest.py              # chunk + embed the corpus  (~596 sequential Ollama calls)
python retrieve.py            # distance sweep across the eval set
python answer.py evaluate     # full scored run
python answer.py "what is the penalty for possession of less than one ounce?"
```

## Honest caveats

- The 8-vs-7 comparison isn't a controlled experiment. Between the two runs the chunk
  `.strip()` behavior changed and the embedding model was re-pulled. The defensible claim is
  **"the port didn't regress accuracy, and measured one point better"** — not that pgvector
  retrieves better than ChromaDB.
- n=2 is reproducibility evidence, not a variance study. A `--runs N` flag on `evaluate()`
  would give a real distribution.
- The ChromaDB baseline lives in a separate retrieval-quality lab; the corpus and eval set are
  identical, which is what makes the comparison meaningful at all.
