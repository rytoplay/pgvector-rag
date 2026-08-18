# config.py — P1 skeleton. Fill the blanks; peeking at module12/config.py is allowed.
#
# Mirrors module12/config.py, minus the ChromaDB bits (DB_PATH / COLLECTION are gone —
# Postgres replaces both), plus the DB connection assembled from .env.

import os
from dotenv import load_dotenv

load_dotenv()

# --- models (same two as module12/config.py) ---------------------------------
EMBED_MODEL = "nomic-embed-text"          # the Ollama embedding model — 768 dims
CHAT_MODEL  = "gemma2:9b"          # the generation/judge model
RERANK_MODEL = "llama3.2"

# --- embedding dimension -----------------------------------------------------
# Must match EMBED_MODEL's output exactly. If this and the column width disagree,
# Postgres rejects the INSERT — a good error to have seen once on purpose.
EMBED_DIM = 768

# --- database ----------------------------------------------------------------
# .env supplies: DB_USER, DB_PASSWORD, DB_HOST, DB_NAME
DB_USER     = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST     = os.getenv("DB_HOST")
DB_NAME     = os.getenv("DB_NAME")

if not all([DB_USER, DB_PASSWORD, DB_HOST, DB_NAME]):
    raise RuntimeError("Missing DB settings — check .env")

# SQLAlchemy URL format:  postgresql+psycopg://user:password@host/dbname
# (the "+psycopg" picks psycopg 3, which is what's in requirements.txt —
#  omit it and SQLAlchemy reaches for psycopg2 and fails)
DATABASE_URL = f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

# --- retrieval knobs ---------------------------------------------------------
# ⚠️ Do NOT port module12's max_distance=330.0. That number came from ChromaDB's
# distance scale. pgvector's <=> is COSINE DISTANCE, bounded [0, 2]:
#     0   = identical direction
#     1   = orthogonal / unrelated
#     2   = opposite
# A 330 threshold would let every chunk through. Leave this as None for P1-P2,
# then derive it empirically in P3 once you can see real distances.
TOP_K        = 5           # module12 used 5 — probably transfers, but verify
MAX_DISTANCE = None       # set in P3 from observed values, not by porting
