from pathlib import Path
from ingest import load_chunks, FIXED_SIZE


def _write_corpus(tmp_path: Path, sections: list[str]) -> Path:
    """Build a corpus file from a list of sections and return its path."""
    corpus = tmp_path / "corpus.txt"
    corpus.write_text("<<<SECTION>>>".join(sections))
    return corpus


def test_every_chunk_is_stripped(tmp_path):
    # named bug: .strip() gets dropped from one branch of load_chunks and
    # chunks get stored with leading/trailing whitespace
    corpus = _write_corpus(tmp_path, [
        "\n  section zero has padding  \n",
        "\n  section one has padding  \n",
    ])

    pairs = load_chunks(corpus)

    assert pairs                      # guard: an empty result makes the loop below vacuous
    for _, text in pairs:
        assert text == text.strip()


def test_windows_inherit_their_section_index(tmp_path):
    # catches the hardcoded-0 bug
    corpus = _write_corpus(tmp_path, [
        "section zero",
        "x" * 4000,        # oversized — the only line that makes this test mean anything
    ])

    pairs = load_chunks(corpus)
    distinct = {i for i, t in pairs if "xxxxxxxxxx" in t}
    assert distinct == {1}, f"expected windows to carry index 1, got {distinct}"
    

def test_no_chunk_exceeds_fixed_size(tmp_path):
    # catches the appended-section-instead-of-window bug
    corpus = _write_corpus(tmp_path, [
        "section zero",
        "x" * 4000,        # oversized — the only line that makes this test mean anything
    ])

    pairs = load_chunks(corpus)

    assert pairs                      # guard: an empty result makes the loop below vacuous
    assert max(len(t) for _, t in pairs) <= FIXED_SIZE

def test_empty_sections_dropped_but_section_zero_kept(tmp_path):
    # catches the `if i > 0` filter bug
    corpus = _write_corpus(tmp_path, [
        "section zero",
        "x" * 40, 
        "",  #empty section
        "x" * 18
    ])

    pairs = load_chunks(corpus)
    indices = {i for i, _ in pairs}
    assert 0 in indices, "section zero was dropped"
    assert 2 not in indices, "the empty section was kept"