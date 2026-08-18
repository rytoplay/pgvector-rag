# Retrieval Eval Set — Andrew College Policy & Procedures Manual

Purpose: a fixed set of questions with known answers, used to tune the RAG
pipeline (chunk size, overlap, `keep`, score threshold) against the AGGREGATE
instead of overfitting to one question. Each item logs the expected answer and a
source citation so the scoring script can check whether retrieval surfaced the
right chunk.

Categories:
- **answerable** — fact is in the doc; pipeline should retrieve + answer it.
- **not_found** — fact is NOT in the doc; pipeline should refuse ("I don't know"),
  optionally noting related info. Tests the grounding/refusal behavior.
- **generic** — a question anyone might ask a P&P manual, written without peeking;
  answer found afterward. Tests real-world question coverage.

---

## Claude's 6

| # | Category | Question | Expected answer | Source |
|---|----------|----------|-----------------|--------|
| A1 | answerable | Under the drug policy, what is the penalty for possession of less than one ounce of marijuana? | Misdemeanor: up to 12 months imprisonment, or a fine not to exceed $1,000, or both; possible loss of driver's license. | §"Notification of Civil Sanctions", ~L3385–3388 |
| A2 | answerable | How long is a Board of Trustees term, and how many regular members may the Board have? | Three-year term; not less than 15 and not more than 39 regular elected members. | §2.1.3, L255–264 |
| B1 | not_found | How much does tuition cost for a student at Andrew College? | Not found (employee P&P manual, not a cost sheet). Related: employee tuition-grant benefit for full-time employees + spouses/dependents. | n/a; related §10.1.5, ~L5813–5822 |
| B2 | not_found | What is the campus Wi-Fi network name and password / how do I connect? | Not found. Distractors that should NOT be used: Technology Committee, library help desk, "wireless communication devices" (= hands-free driving). | n/a; distractors L6737, L7491 |
| C1 | generic | What is the inclement-weather / emergency closing policy — who decides to close? | President decides to close/delay; Academic Dean + CFO consult and recommend; communicated via college email, website, and/or emergency alert systems. | §4.5, L1395–1402 |
| C2 | generic | How does an employee report sexual harassment? | Title IX process: file a Formal Complaint (by Complainant or signed by Title IX Coordinator) requesting investigation; College takes prompt equitable action; two-employee cases may use Title IX or Title VII. | §4.8, ~L1456–1535 |

---

## Robert's 6

<!-- 2 from a fact you found, 2 likely-not-found, 2 generic guesses. Log answers + source. -->

| # | Category | Question | Expected answer | Source |
|---|----------|----------|-----------------|--------|
| D1 | answerable | Are student employees eligible for the college's benefits program? | No — student employees (College-hired or work-study) receive only legally-mandated benefits (e.g., workers' comp); ineligible for all other Andrew benefit programs. | §5.8.2 |
| D2 | answerable | Who must approve a vendor before a purchase order can be written? | The Vice President for Finance or the Controller, prior to any purchase. | §8.1.2 |
| E1 | not_found | Does the college football team have exempt status? | Not found. No football team is mentioned anywhere; "exempt" appears only re: FLSA exempt/non-exempt staff, officers exempt from the weapons policy, and the College's tax-exempt status — none apply to a team. Distractor-heavy. | n/a; distractors §5.8.1, §4.4, L4305 |
| E2 | partial / hallucination-trap | How does the penalty differ for Molly vs marijuana? | Manual never names "Molly"/MDMA. Marijuana: <1 oz = misdemeanor (≤12 mo or ≤$1,000); >1 oz = felony. All "other illicit drugs" = felony (up to 30 yrs). So Molly falls under "other illicit drugs" → felony; no Molly-specific figure. Correct answer must NOT invent one. | §"Notification of Civil Sanctions", ~L3385–3390 |
| F1 | generic | Are there any ways of earning tuition-free credits? | Yes — Educational Benefits: tuition grants for full-time employees + spouses + dependents; part-time employees up to 3 credit hrs/semester; dependents may also get a housing grant. | §10.1.5, L5812–5837 |
| F2 | generic | Is it permissible to do contract work on the side while employed by the college? | Permitted with approval: staff need immediate supervisor's permission; faculty need Dean of Academic Affairs approval; must not create a conflict of interest or adversely impact the College; written approval filed in personnel record. | §"Outside Employment", L3597–3621 |
