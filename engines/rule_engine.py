CONFIDENCE_THRESHOLD = 0.75

def evaluate(evidence: list, criteria: list) -> list:
    """
    Pure deterministic logic. No LLM.
    Returns a verdict per criterion: PASS, FAIL, or NEEDS_REVIEW
    """
    criteria_by_id = {c["criterion_id"]: c for c in criteria}
    results = []

    for ev in evidence:
        cid = ev["criterion_id"]
        criterion = criteria_by_id.get(cid)

        if criterion is None:
            continue

        verdict = None
        reason = ""
        # Rule 0: contradictory values across documents
        if ev["status"] == "CONTRADICTORY":
            verdict = "NEEDS_REVIEW"
            alternates = ev.get("alternate_values", [])
            values_str = " vs ".join(
                f"{a['value']} (page {a['source_page']})" for a in alternates
            )
            reason = f"Contradictory values found across documents: {values_str}"

        elif ev["status"] == "NOT_FOUND":

        # Rule 1: document missing or value not found
            verdict = "NEEDS_REVIEW"
            reason = "Required document or value was not found in submission"

        elif ev["status"] == "UNREADABLE":
            verdict = "NEEDS_REVIEW"
            reason = "Value could not be read with sufficient confidence"

        # Rule 2: low confidence always escalates
        elif ev.get("confidence", 0) < CONFIDENCE_THRESHOLD:
            verdict = "NEEDS_REVIEW"
            reason = f"Confidence {ev['confidence']} below threshold {CONFIDENCE_THRESHOLD}"

        # Rule 3: numeric threshold comparison
        elif criterion.get("comparison") == "greater_than_or_equal":
            try:
                extracted = float(ev["extracted_value"])
                threshold = float(criterion["threshold"])

                if extracted >= threshold:
                    verdict = "PASS"
                    reason = f"{extracted} meets required threshold {threshold}"
                else:
                    verdict = "FAIL"
                    reason = f"{extracted} below required threshold {threshold}"
            except (ValueError, TypeError):
                verdict = "NEEDS_REVIEW"
                reason = "Could not compare extracted value to threshold"

        # Rule 4: existence-based criteria
        elif criterion.get("comparison") == "exists":
            if ev["extracted_value"]:
                verdict = "PASS"
                reason = "Required document/certification found"
            else:
                verdict = "FAIL"
                reason = "Required document/certification not found"

        else:
            verdict = "NEEDS_REVIEW"
            reason = "Criterion type not recognized by rule engine"

        results.append({
            "criterion_id": cid,
            "criterion_name": criterion["name"],
            "mandatory": criterion["mandatory"],
            "extracted_value": ev["extracted_value"],
            "source_page": ev.get("source_page"),
            "raw_snippet": ev.get("raw_snippet"),
            "confidence": ev.get("confidence"),
            "verdict": verdict,
            "reason": reason
        })

    return results