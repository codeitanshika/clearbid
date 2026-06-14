# ClearBid

AI-based tender evaluation and eligibility analysis platform for government procurement (CRPF Theme 3).

## What it does

ClearBid automates the evaluation of bidder submissions against government tender eligibility criteria. It extracts criteria from tender documents, evaluates each bidder's documents, produces explainable PASS/FAIL/NEEDS_REVIEW verdicts per criterion, detects cross-bidder fraud signals, and maintains a complete audit trail of every decision.

## Architecture

```
Tender PDF → Criteria Extractor (LLM) → Officer Approval Gate
     ↓
Bidder PDFs → Document Parser → Evidence Extractor (LLM)
     ↓
Rule Engine (deterministic Python) → PASS / FAIL / NEEDS_REVIEW
     ↓
Officer Review Dashboard → Approve / Reject / Clarify
     ↓
Fraud Signal Checker (cross-bidder) → Shared GST / Price Proximity
     ↓
Audit Log (SQLite) → JSON Export
```
## Tech stack

| Layer | Technology | Why |
|---|---|---|
| LLM | Groq (Llama 3.3 70B) | Free tier, fast, reliable JSON output |
| PDF extraction | PyMuPDF | Fast, accurate, preserves page numbers |
| Rule engine | Pure Python | Deterministic — same input always gives same output |
| Database | SQLite | File-based, no server setup, audit-grade append |
| Backend | FastAPI | Lightweight, auto-generates API docs |
| Frontend | React + Vite | Fast build, clean component structure |

## Key design decisions

- **LLM never makes pass/fail decisions** — it only extracts and maps evidence. A deterministic rule engine makes all verdicts.
- **Officer approval gate** — criteria are confirmed by officer before any bidder is evaluated. Misreads are caught at source.
- **Three document states** — FOUND / NOT_FOUND / DOCUMENT_MISSING are tracked separately (different legal treatments).
- **No silent disqualification** — ambiguous, low-confidence, or contradictory cases always go to NEEDS_REVIEW, never auto-fail.

## What's implemented

- Tender PDF upload and criteria extraction
- Officer criteria approval gate
- Multi-bidder PDF evaluation (typed PDFs)
- Deterministic rule engine (PASS / FAIL / NEEDS_REVIEW)
- Contradiction detection across documents from same bidder
- Officer review dashboard with approve / reject / clarify + mandatory justification
- Cross-bidder fraud signal detection (shared GST, price proximity)
- Full audit trail per tender with JSON export
- Multi-tender management dashboard

## What's planned (next steps)

- OCR support for scanned documents and photographs (Tesseract)
- PostgreSQL for production deployment
- PDF audit report export (currently JSON)
- User authentication and role-based access
- Cloud deployment (Render / Railway)

## Setup

### Prerequisites
- Python 3.11+
- Node.js 18+
- Groq API key (free at https://console.groq.com)

### Backend

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
echo GROQ_API_KEY=your_key_here > .env

# Create uploads folder
mkdir uploads

# Run backend
uvicorn main:app --reload
```

Backend runs at `http://127.0.0.1:8000`
API docs at `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://localhost:5173`

## Demo scenario

The `data/` folder contains mock documents:

- `mock_tender.pdf` — construction services tender with 4 eligibility criteria
- `bidder_a.pdf` — all criteria met, clear PASS
- `bidder_b.pdf` — fails turnover and project count criteria
- `bidder_c.pdf` — contradictory turnover figures across two documents, triggers NEEDS_REVIEW
- `bidder_d.pdf` — shares GST number with Bidder A, triggers fraud flag

## API endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/tenders` | List all tenders |
| POST | `/upload-tender` | Upload and extract criteria from tender PDF |
| POST | `/approve-tender/{id}` | Officer approves criteria |
| GET | `/tender/{id}` | Get tender details and criteria |
| POST | `/evaluate-bidder` | Evaluate a bidder PDF against approved criteria |
| GET | `/tender/{id}/bidders` | Get all bidder results for a tender |
| GET | `/tender/{id}/needs-review` | Get pending review queue |
| POST | `/review-decision/{id}` | Record officer decision with justification |
| GET | `/tender/{id}/fraud-check` | Run cross-bidder fraud signal detection |
| GET | `/tender/{id}/audit-report` | Download full audit report |

## Project structure

```
clearbid/
├── agents/
│   ├── criteria_extractor.py   # LLM-based criteria extraction
│   ├── document_parser.py      # PDF text extraction
│   ├── evidence_extractor.py   # LLM-based evidence mapping
│   └── fraud_checker.py        # Cross-bidder fraud signals
├── engines/
│   └── rule_engine.py          # Deterministic verdict logic
├── data/
│   ├── mock_tender.pdf
│   └── mock_bidders/
├── frontend/                   # React application
│   └── src/
│       ├── App.jsx
│       └── App.css
├── database.py                 # SQLite operations
├── main.py                     # FastAPI application
├── requirements.txt
└── .env                        # Not in repo — create locally
```