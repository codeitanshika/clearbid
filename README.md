# ClearBid

AI-based tender evaluation and eligibility analysis platform for CRPF procurement.

## Problem

Manual evaluation of bidder eligibility against tender criteria is slow,
inconsistent, and hard to audit. ClearBid extracts eligibility criteria
from tender documents, evaluates bidder submissions against those criteria,
and produces explainable, criterion-level verdicts (PASS / FAIL / NEEDS_REVIEW)
for a procurement officer to review and approve.

## Architecture

Tender PDF → Criteria Extractor (LLM) → Officer Approval Gate
→ Bidder PDF → Evidence Extractor (LLM) → Rule Engine (deterministic)
→ Officer Review Dashboard → Audit Log

See `docs/architecture_diagram.png` for full flow.

## What's implemented (Round 1)

- Criteria extraction from tender PDF using GPT-4o
- Evidence extraction from bidder PDFs using GPT-4o
- Deterministic rule engine producing PASS / FAIL / NEEDS_REVIEW
- Mock tender + 3 mock bidder documents demonstrating all three verdicts

## What's planned (Round 2)

- React officer review dashboard with approve/reject/clarify + justification
- OCR support for scanned documents (Tesseract)
- Fraud signal detection (shared GST, director names, price proximity)
- PostgreSQL audit log with PDF export
- Officer criteria-approval UI

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Add your OpenAI API key to .env

uvicorn main:app --reload
```

## Usage

1. POST `/upload-tender` with a tender PDF → returns extracted criteria
2. POST `/evaluate-bidder` with a bidder PDF + criteria JSON → returns verdicts

## Demo

Run with the mock files in `data/`:
- `mock_tender.pdf` → extracts 4 criteria
- `bidder_a.pdf` → all PASS
- `bidder_b.pdf` → FAIL on turnover and project count
- `bidder_c.pdf` → NEEDS_REVIEW on turnover (contradictory values)