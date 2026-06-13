from dotenv import load_dotenv
load_dotenv()

import os
import shutil
import json
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from agents.document_parser import parse_pdf
from agents.criteria_extractor import extract_criteria
from agents.evidence_extractor import extract_evidence
from engines.rule_engine import evaluate
from agents.fraud_checker import check_fraud_signals
import database as db

app = FastAPI(title="ClearBid API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

db.init_db()


@app.post("/upload-tender")
async def upload_tender(file: UploadFile):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = parse_pdf(path)
    criteria = extract_criteria(text)

    tender_id = db.save_tender(file.filename, criteria)

    return {"tender_id": tender_id, "criteria": criteria}


@app.post("/approve-tender/{tender_id}")
async def approve_tender(tender_id: int):
    db.approve_tender(tender_id)
    return {"status": "approved", "tender_id": tender_id}


@app.get("/tender/{tender_id}")
async def get_tender(tender_id: int):
    tender = db.get_tender(tender_id)
    if tender is None:
        return {"error": "Tender not found"}
    return tender


@app.post("/evaluate-bidder")
async def evaluate_bidder(file: UploadFile, tender_id: int = Form(...)):
    tender = db.get_tender(tender_id)
    if tender is None:
        return {"error": "Tender not found"}

    if not tender["approved"]:
        return {"error": "Tender criteria not yet approved by officer"}

    criteria_list = tender["criteria"]

    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = parse_pdf(path)
    evidence = extract_evidence(text, criteria_list)
    verdicts = evaluate(evidence, criteria_list)

    bidder_id = db.save_bidder(tender_id, file.filename)
    db.save_verdicts(bidder_id, verdicts)

    return {"bidder_id": bidder_id, "bidder": file.filename, "verdicts": verdicts}


@app.get("/tender/{tender_id}/bidders")
async def get_bidders(tender_id: int):
    bidders = db.get_tender_bidders(tender_id)
    result = []
    for b in bidders:
        verdicts = db.get_bidder_verdicts(b["bidder_id"])
        result.append({
            "bidder_id": b["bidder_id"],
            "filename": b["filename"],
            "verdicts": verdicts
        })
    return {"tender_id": tender_id, "bidders": result}


@app.get("/tender/{tender_id}/needs-review")
async def needs_review(tender_id: int):
    items = db.get_needs_review(tender_id)
    return {"items": items}


@app.post("/review-decision/{verdict_id}")
async def review_decision(verdict_id: int, action: str = Form(...), justification: str = Form(...)):
    db.update_officer_action(verdict_id, action, justification)
    return {"status": "recorded", "verdict_id": verdict_id}


@app.get("/")
def root():
    return {"status": "ClearBid API running"}

@app.get("/tender/{tender_id}/fraud-check")
async def fraud_check(tender_id: int):
    bidders = db.get_tender_bidders(tender_id)
    bidders_data = []
    for b in bidders:
        verdicts = db.get_bidder_verdicts(b["bidder_id"])
        bidders_data.append({
            "bidder_id": b["bidder_id"],
            "filename": b["filename"],
            "verdicts": verdicts
        })

    flags = check_fraud_signals(bidders_data)
    return {"tender_id": tender_id, "flags": flags}

@app.get("/tender/{tender_id}/audit-report")
async def audit_report(tender_id: int):
    report = db.get_full_audit_report(tender_id)
    if report is None:
        return {"error": "Tender not found"}
    return report

@app.get("/tenders")
async def list_tenders():
    return {"tenders": db.get_all_tenders()}