"""
Eval set for tuning the RAG pipeline against the Andrew College Policy &
Procedures Manual.

Used to tune chunk size / overlap / `keep` / score-threshold against the
AGGREGATE of all questions, instead of overfitting to a single question.

Import into retrieval_lab.py:
    from tuning_questions import EVAL_SET

Each item:
    id        – short label
    category  – "answerable" | "not_found" | "trap"
                  answerable → pipeline should retrieve the chunk AND answer
                  not_found  → pipeline should REFUSE ("I don't know") and not
                               get lured by distractors
                  trap       → partially answerable; must answer the real part
                               WITHOUT inventing the missing part (hallucination test)
    question  – the question to ask the pipeline
    expected  – the known-correct answer (ground truth), or the refusal expectation
    keywords  – facts that a correct answer should contain (a starting point for a
                deterministic check; tweak/replace as you design the scorer)
    avoid     – terms a correct answer should NOT assert (distractors / invented facts)
    source    – where the answer lives in the doc (for retrieval-recall scoring)
"""

EVAL_SET = [
    # ---- Claude's 6 ----
    {
        "id": "A1",
        "category": "answerable",
        "question": "Under the drug policy, what is the penalty for possession of less than one ounce of marijuana?",
        "expected": "Misdemeanor: up to 12 months imprisonment, or a fine not to exceed $1,000, or both; possible loss of driver's license.",
        "keywords": ["misdemeanor", "12 months", "$1,000"],
        "avoid": [],
        "source": "Notification of Civil Sanctions, ~L3385-3388",
    },
    {
        "id": "A2",
        "category": "answerable",
        "question": "How long is a Board of Trustees term, and how many regular members may the Board have?",
        "expected": "Three-year term; not less than 15 and not more than 39 regular elected members.",
        "keywords": ["three", "15", "39"],
        "avoid": [],
        "source": "Section 2.1.3, L255-264",
    },
    {
        "id": "B1",
        "category": "not_found",
        "question": "How much does tuition cost for a student at Andrew College?",
        "expected": "Not found — this is an employee P&P manual, not a cost sheet. (Related: an employee tuition-grant benefit exists.)",
        "keywords": [],
        "avoid": [],
        "source": "n/a; related Section 10.1.5",
    },
    {
        "id": "B2",
        "category": "not_found",
        "question": "What is the campus Wi-Fi network name and password, and how do I connect to it?",
        "expected": "Not found. Should not be lured by distractors (Technology Committee, library help desk, 'wireless communication devices' = hands-free driving).",
        "keywords": [],
        "avoid": ["Technology Committee", "help desk", "Hands Free", "driving"],
        "source": "n/a; distractors L6737, L7491",
    },
    {
        "id": "C1",
        "category": "answerable",
        "question": "What is the inclement-weather / emergency closing policy — who decides to close?",
        "expected": "The President decides to close/delay; the Academic Dean and CFO consult and recommend; communicated via college email, the website, and/or emergency alert systems.",
        "keywords": ["President", "email", "website"],
        "avoid": [],
        "source": "Section 4.5, L1395-1402",
    },
    {
        "id": "C2",
        "category": "answerable",
        "question": "How does an employee report sexual harassment?",
        "expected": "Through the Title IX process: file a Formal Complaint (by the Complainant or signed by the Title IX Coordinator) requesting an investigation; the College takes prompt, equitable action. Two-employee cases may use Title IX or Title VII.",
        "keywords": ["Title IX", "Formal Complaint"],
        "avoid": [],
        "source": "Section 4.8, ~L1456-1535",
    },

    # ---- Robert's 6 ----
    {
        "id": "D1",
        "category": "answerable",
        "question": "Are student employees eligible for the college's benefits program?",
        "expected": "No — student employees (College-hired or work-study) receive only legally-mandated benefits (e.g., workers' comp); ineligible for all other Andrew benefit programs.",
        "keywords": ["legally-mandated", "ineligible"],
        "avoid": [],
        "source": "Section 5.8.2",
    },
    {
        "id": "D2",
        "category": "answerable",
        "question": "Who must approve a vendor before a purchase order can be written?",
        "expected": "The Vice President for Finance or the Controller, prior to any purchase.",
        "keywords": ["Vice President for Finance", "Controller"],
        "avoid": [],
        "source": "Section 8.1.2",
    },
    {
        "id": "E1",
        "category": "not_found",
        "question": "Does the college football team have exempt status?",
        "expected": "Not found. No football team is mentioned anywhere; 'exempt' appears only re: FLSA staff classification, officers exempt from the weapons policy, and the College's tax-exempt status — none apply to a team.",
        "keywords": [],
        "avoid": ["FLSA", "non-exempt", "weapons", "tax exempt"],
        "source": "n/a; distractors Section 5.8.1, Section 4.4, L4305",
    },
    {
        "id": "E2",
        "category": "trap",
        "question": "How does the penalty differ for Molly vs marijuana?",
        "expected": "The manual never names 'Molly'/MDMA. Marijuana: <1 oz = misdemeanor (<=12 mo or <=$1,000); >1 oz = felony. All 'other illicit drugs' = felony (up to 30 yrs), so Molly falls under 'other illicit drugs' -> felony. Must NOT invent a Molly-specific figure.",
        "keywords": ["other illicit drugs", "felony", "marijuana"],
        "avoid": [],   # success = does not fabricate a Molly-specific penalty
        "source": "Notification of Civil Sanctions, ~L3385-3390",
    },
    {
        "id": "F1",
        "category": "answerable",
        "question": "Are there any ways of earning tuition-free credits?",
        "expected": "Yes — Educational Benefits: tuition grants for full-time employees + spouses + dependents; part-time employees up to 3 credit hours/semester; dependents may also get a housing grant.",
        "keywords": ["tuition grant", "dependents"],
        "avoid": [],
        "source": "Section 10.1.5, L5812-5837",
    },
    {
        "id": "F2",
        "category": "answerable",
        "question": "Is it permissible to do contract work on the side while employed by the college?",
        "expected": "Permitted with approval: staff need their immediate supervisor's permission; faculty need Dean of Academic Affairs approval; must not create a conflict of interest or adversely impact the College; written approval is filed in the personnel record.",
        "keywords": ["supervisor", "conflict of interest"],
        "avoid": [],
        "source": "Outside Employment, L3597-3621",
    },
]
