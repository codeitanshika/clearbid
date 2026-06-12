import os
import json
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

EXTRACTION_PROMPT = """You are analyzing a government tender document.
Extract every eligibility criterion mentioned. For each criterion, output:

- criterion_id: C1, C2, C3...
- name: short name
- type: "financial", "technical", or "compliance"
- mandatory: true or false (true if "shall/must/mandatory", false if "may/preferred")
- threshold: numeric value if applicable, else null
- unit: "INR", "years", "count", or null
- comparison: "greater_than_or_equal", "exists", "valid_on_date", or null
- raw_text: the exact sentence from the tender this was extracted from

Return ONLY a JSON array of these objects. No explanation, no markdown.

Tender text:
{tender_text}
"""

def extract_criteria(tender_text: str) -> list:
    prompt = EXTRACTION_PROMPT.format(tender_text=tender_text)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    raw = response.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.replace("json", "", 1).strip()

    try:
        criteria = json.loads(raw)
    except json.JSONDecodeError:
        criteria = []

    return criteria