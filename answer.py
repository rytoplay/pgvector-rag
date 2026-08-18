import ollama
import json
import sys
import time
from pprint import pprint
from config import RERANK_MODEL, CHAT_MODEL
from tuning_questions import EVAL_SET
from retrieve import retrieve


SYSTEM = """Answer the question using ONLY the context provided below.
If the answer is not in the context, say: "I don't know — it's not in the provided text."
Be specific and quote from the context where you can. Quote the exact sentence(s) from the context that your answer is based on.

  1. Permit reasoning/inference — "you may draw conclusions from the context," not just quote it verbatim.
  2. Handle the framing mismatch — "if the context addresses the topic but not the exact wording of the question, explain what the
  policy does say."
  3. Narrow the refusal trigger — say "I don't know" only when the context has nothing relevant, not when the exact phrase is missing.
"""

def judge_response(question: str, expected: str, generated_response: str)->str:
    payload = {"question": question, "correct_answer": expected, "returned_answer": generated_response}

    PROMPT = """You are judging whether a RAG chunk retrieval and evaluation program is returning correct results. 
            Examine the following question, correct answer, and the returned answer and return TRUE if the returned answer 
            contains the same information as the correct answer and return FALSE if the returned answer does not contain the 
            information in the correct answer.

            Example1:
            {"question":"What year was the college founded?", "correct_answer":"In
            1856 Bishop Andrew came to Cuthbert to dedicate the school to “the service
            of God.”, "returned_answer": "the first
            classroom building, was constructed in 1900 and Cuthbert Hall was
            constructed in 1912, thereby joining “Old Main” and Warren Bush into one
            unit. "}
            RESULT1: {"result": "False"}

            Example2:
            {"question":"Which is better, Star Trek or Star Wars?", 
            "correct_answer": "Not Found. Star Trek and Star Wars are not mentioned in the document.", 
            "returned_answer": "Not Found. Neither franshise is mentioned in the document."}
            RESULT2: {"result": "True"}
    """
    response = ollama.chat(
        model='gemma2:9b',
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": json.dumps(payload)},
        ],
        format={
            "type": "object",
            "properties": {"result": {"type": "string", "enum": ["True", "False"]}},
            "required": ["result"],
        },                   # ← forces parseable JSON output (Ollama feature)
        options={"temperature": 0},       # deterministic judge
    )
    return response["message"]["content"]

def rerank(question: str, chunks: list[str], keep: int = 5) -> list[str]:
    """LLM-as-judge: score each chunk 0-10 for relevance, keep the top `keep`."""
    numbered = "\n\n".join(f"[{i}] {c}" for i, c in enumerate(chunks))   # full c, no [:300]

    JUDGE_SYSTEM = """You score how well each numbered chunk helps answer the user's question.
    Score EVERY chunk 0–10 by this rubric:
    - 8–10: the chunk DIRECTLY contains the answer
    - 1–4: mentions the topic but does NOT contain the answer
    - 0: unrelated
    Do NOT give a high score just because a chunk mentions related words — reserve high
    scores for the chunk(s) that actually contain the answer.
    Return a JSON array with a score for EVERY chunk index, e.g. [{"index": 0, "score": 9}, ...]"""

    user_content = f"QUESTION: {question}\n\nCHUNKS:\n{numbered}"

    response = ollama.chat(
        model=RERANK_MODEL,
        messages=[
            {"role": "system", "content": JUDGE_SYSTEM},
            {"role": "user", "content": user_content},
        ],
        format={
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"index": {"type": "integer"}, "score": {"type": "integer"}},
                "required": ["index", "score"],
            },
        },                    # ← forces parseable JSON output (Ollama feature)
        options={"temperature": 0},       # deterministic judge
    )
    raw = response["message"]["content"]
    #print("=== RAW JUDGE ===", raw)
    
    try:
        scored = json.loads(raw)
        if isinstance(scored, dict):
            scored= [scored]
    except json.JSONDecodeError:
        print("judge returned bad JSON; keeping first", keep)
        return chunks[:keep]
    #print(f"scored results = {scored}")
    ranked = sorted(scored, key=lambda x: x["score"], reverse=True)
    top = [d for d in ranked if d["score"] > 0 and d["index"] < len(chunks)][:keep]
    return [chunks[d["index"]] for d in top]    # ← map index → chunk TEXT

def answer(question: str) -> str:
    candidates = [text for text, _dist in retrieve(question, 15)]

    # for i, c in enumerate(candidates):
    #     print(f"[{i}] {c[:90]}…")
    # print("-" * 40)

    top_chunks = rerank(question, candidates, keep=5)     # 2. re-score → best 5
    if not top_chunks:
        return "I don't know. The answer wasn't in the document."
    context = "\n\n---\n\n".join(top_chunks)              # 3. context from the BEST 5
    user_msg = f"Context:\n{context}\n\nQuestion: {question}"
    response = ollama.chat(                                # 4. generate from the 5
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user",   "content": user_msg},
        ],
        options={"temperature": 0},
    )
    return response["message"]["content"]                 # 5. return the answer text

def evaluate() -> tuple[int, int]:
    results = []
    for q in EVAL_SET:
        question = q["question"]
        print(f"---------------\n{q["id"]} - {question}:\ncorrect_answer: {q["expected"]}\n")
        generated_response = answer(question)
        print(f"generated_response: {generated_response}\n")

        verdict_raw = judge_response(question, q["expected"], generated_response)
        passed = json.loads(verdict_raw)["result"] == "True"
        print(f"evaluation: {verdict_raw}\npassed: {passed}\n")

        results.append({
            "id": q["id"],
            "question": question,
            "correct_answer": q["expected"],
            "generated_response": generated_response,
            "evaluation": verdict_raw,
            "passed": passed,
        })

    score = sum(1 for r in results if r["passed"])
    total = len(results)

    print(f"\n{'='*40}\nSCORE: {score}/{total}   (ChromaDB baseline: 7/12)")
    for r in results:
        print(f"  {'PASS' if r['passed'] else 'FAIL'}  [{r['id']}]")

    return score, total

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "evaluate":
        score, total = evaluate()
        sys.exit(0 if score >= 7 else 1)      # what's the baseline to beat?
    elif len(sys.argv) > 1:
        print(answer(" ".join(sys.argv[1:])))
    else:
        print("usage: python answer.py evaluate")
        print("       python answer.py <your question>")