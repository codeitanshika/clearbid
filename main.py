from dotenv import load_dotenv
load_dotenv()

import os
import shutil
from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware

from agents.document_parser import parse_pdf
from agents.criteria_extractor import extract_criteria
from agents.evidence_extractor import extract_evidence
from engines.rule_engine import evaluate

app = FastAPI(title="ClearBid API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/upload-tender")
async def upload_tender(file: UploadFile):
    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = parse_pdf(path)
    criteria = extract_criteria(text)

    return {"criteria": criteria}


@app.post("/evaluate-bidder")
async def evaluate_bidder(file: UploadFile, criteria: str = Form(...)):
    import json
    criteria_list = json.loads(criteria)

    path = os.path.join(UPLOAD_DIR, file.filename)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    text = parse_pdf(path)
    evidence = extract_evidence(text, criteria_list)
    verdicts = evaluate(evidence, criteria_list)

    return {"bidder": file.filename, "verdicts": verdicts}


@app.get("/")
def root():
    return {"status": "ClearBid API running"}