# models.py — P1 skeleton.

from sqlalchemy import create_engine, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker
from pgvector.sqlalchemy import Vector          # <-- the only genuinely new import

from config import DATABASE_URL, EMBED_DIM


class Base(DeclarativeBase):  # which class does Base inherit from?
    pass


class Chunk(Base):
    """One retrievable piece of the Andrew College corpus, plus its embedding."""

    __tablename__ = "chunks"                       # plan says `chunks` unless you renamed it

    # --- primary key ---------------------------------------------------------
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- the text that gets returned to the LLM as context -------------------
    chunk_text: Mapped[str] = mapped_column(Text)

    # --- the vector ----------------------------------------------------------
    embedding: Mapped[list[float]] = mapped_column(Vector(EMBED_DIM))

    section_idx: Mapped[int | None] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:
        return f"<Chunk id={self.id} text={self.chunk_text[:40]!r}...>"


# --- engine + session --------------------------------------------------------
engine = create_engine(DATABASE_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)

def init_db() -> None:
    """Create the table. Assumes `CREATE EXTENSION vector;` already ran (it has)."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("tables created")                                 # confirm it ran
