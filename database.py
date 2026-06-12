import sqlite3
import json
from datetime import datetime, timezone

DB_PATH = "clearbid.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS tenders (
            tender_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            criteria_json TEXT,
            approved INTEGER DEFAULT 0,
            created_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS bidders (
            bidder_id INTEGER PRIMARY KEY AUTOINCREMENT,
            tender_id INTEGER,
            filename TEXT,
            created_at TEXT,
            FOREIGN KEY (tender_id) REFERENCES tenders(tender_id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS verdicts (
            verdict_id INTEGER PRIMARY KEY AUTOINCREMENT,
            bidder_id INTEGER,
            criterion_id TEXT,
            criterion_name TEXT,
            mandatory INTEGER,
            extracted_value TEXT,
            source_page INTEGER,
            raw_snippet TEXT,
            confidence REAL,
            verdict TEXT,
            reason TEXT,
            officer_action TEXT,
            officer_justification TEXT,
            decided_at TEXT,
            FOREIGN KEY (bidder_id) REFERENCES bidders(bidder_id)
        )
    """)

    conn.commit()
    conn.close()


def save_tender(filename: str, criteria: list) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tenders (filename, criteria_json, approved, created_at) VALUES (?, ?, 0, ?)",
        (filename, json.dumps(criteria), datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    tender_id = cur.lastrowid
    conn.close()
    return tender_id


def approve_tender(tender_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tenders SET approved = 1 WHERE tender_id = ?", (tender_id,))
    conn.commit()
    conn.close()


def get_tender(tender_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tenders WHERE tender_id = ?", (tender_id,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        return None
    return {
        "tender_id": row["tender_id"],
        "filename": row["filename"],
        "criteria": json.loads(row["criteria_json"]),
        "approved": bool(row["approved"]),
        "created_at": row["created_at"]
    }


def save_bidder(tender_id: int, filename: str) -> int:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO bidders (tender_id, filename, created_at) VALUES (?, ?, ?)",
        (tender_id, filename, datetime.now(timezone.utc).isoformat())
    )
    conn.commit()
    bidder_id = cur.lastrowid
    conn.close()
    return bidder_id


def save_verdicts(bidder_id: int, verdicts: list):
    conn = get_connection()
    cur = conn.cursor()
    for v in verdicts:
        cur.execute("""
            INSERT INTO verdicts (
                bidder_id, criterion_id, criterion_name, mandatory,
                extracted_value, source_page, raw_snippet, confidence,
                verdict, reason, officer_action, officer_justification, decided_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, NULL)
        """, (
            bidder_id,
            v["criterion_id"],
            v["criterion_name"],
            int(v["mandatory"]),
            json.dumps(v["extracted_value"]),
            v.get("source_page"),
            v.get("raw_snippet"),
            v.get("confidence"),
            v["verdict"],
            v["reason"]
        ))
    conn.commit()
    conn.close()


def get_bidder_verdicts(bidder_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM verdicts WHERE bidder_id = ?", (bidder_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_tender_bidders(tender_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM bidders WHERE tender_id = ?", (tender_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_officer_action(verdict_id: int, action: str, justification: str):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE verdicts
        SET officer_action = ?, officer_justification = ?, decided_at = ?
        WHERE verdict_id = ?
    """, (action, justification, datetime.now(timezone.utc).isoformat(), verdict_id))
    conn.commit()
    conn.close()


def get_needs_review(tender_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT v.*, b.filename as bidder_filename
        FROM verdicts v
        JOIN bidders b ON v.bidder_id = b.bidder_id
        WHERE b.tender_id = ? AND v.verdict = 'NEEDS_REVIEW' AND v.officer_action IS NULL
    """, (tender_id,))
    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]