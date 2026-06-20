import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EVIDENCE_PROMPT = """You are reviewing a bidder's submitted documents against a list of eligibility criteria.

Criteria list:
{criteria_json}

Bidder document text (with page markers):
{bidder_text}

For EACH criterion, search the ENTIRE document for ALL mentions of the relevant value —
not just the first one. Some bidders submit multiple documents (e.g. Balance Sheet AND
Income Tax Return) that may state DIFFERENT values for the same criterion (e.g. different
turnover figures). If you find MORE THAN ONE different value for the same criterion across
different documents/pages, this is a CONTRADICTION.

For EACH criterion, output:

- criterion_id: matching the criteria list
- extracted_value: the value found, or null if not found
  - if contradictory values exist, set this to null
- status: "FOUND", "NOT_FOUND", "UNREADABLE", or "CONTRADICTORY"
- source_page: page number where found, or null
- raw_snippet: exact text snippet where the value appears, or null
- confidence: your confidence 0.0 to 1.0
- alternate_values: if status is "CONTRADICTORY", an array of objects like
  [{{"value": X, "source_page": Y, "raw_snippet": "..."}}, {{"value": Z, "source_page": W, "raw_snippet": "..."}}]
  otherwise null

Return ONLY a JSON array of these objects. No explanation, no markdown.
"""

def extract_evidence(bidder_text: str, criteria: list) -> list:
    if not bidder_text or len(bidder_text.strip()) < 10:
        raise ValueError("Bidder document appears empty or could not be read.")

    prompt = EVIDENCE_PROMPT.format(
        criteria_json=json.dumps(criteria, indent=2),
        bidder_text=bidder_text
    )

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
    except Exception as e:
        raise RuntimeError(f"LLM request failed: {str(e)}")

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()

    try:
        evidence = json.loads(raw)
    except json.JSONDecodeError:
        raise RuntimeError("Could not parse bidder evaluation results. Please try again.")

    return evidence