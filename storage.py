import sqlite3
import json
import os
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "hallucinations.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Table for verification runs
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS verification_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        source_type TEXT DEFAULT 'prompt', -- 'prompt', 'text', 'file'
        prompt TEXT,
        input_text TEXT,
        generated_text TEXT,
        claims_count INTEGER DEFAULT 0,
        supported_count INTEGER DEFAULT 0,
        hallucinated_count INTEGER DEFAULT 0,
        uncertain_count INTEGER DEFAULT 0,
        trust_index REAL DEFAULT 0.0,
        hallucination_risk REAL DEFAULT 0.0,
        risk_level TEXT DEFAULT 'LOW',
        corrected_text TEXT,
        model_used TEXT,
        raw_report_json TEXT
    );
    """)
    
    # Table for individual atomic claims
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS claims (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_id INTEGER,
        claim_text TEXT,
        verdict TEXT, -- 'SUPPORTED', 'HALLUCINATED', 'UNCERTAIN'
        confidence TEXT,
        search_query TEXT,
        explanation TEXT,
        quoted_evidence TEXT,
        source_title TEXT,
        source_url TEXT,
        FOREIGN KEY (run_id) REFERENCES verification_runs (id) ON DELETE CASCADE
    );
    """)
    
    conn.commit()
    conn.close()

def save_verification_run(report: dict, source_type: str = "text", prompt: str = None, model_used: str = "Llama 3.3 (Groq)") -> int:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    summary = report.get("summary", {})
    claims_count = report.get("claims_count", 0)
    supported = summary.get("supported", 0)
    hallucinated = summary.get("hallucinated", 0)
    uncertain = summary.get("uncertain", 0)
    
    trust_index = report.get("trust_index", 0.0)
    hallucination_risk = report.get("hallucination_risk", 0.0)
    risk_level = report.get("risk_level", "LOW")
    corrected_text = report.get("corrected_text", "")
    
    input_text = report.get("text", "")
    generated_text = report.get("generated_text", input_text)
    
    cursor.execute("""
        INSERT INTO verification_runs (
            source_type, prompt, input_text, generated_text, claims_count,
            supported_count, hallucinated_count, uncertain_count, trust_index,
            hallucination_risk, risk_level, corrected_text, model_used, raw_report_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        source_type, prompt, input_text, generated_text, claims_count,
        supported, hallucinated, uncertain, trust_index,
        hallucination_risk, risk_level, corrected_text, model_used, json.dumps(report)
    ))
    
    run_id = cursor.lastrowid
    
    for res in report.get("results", []):
        cursor.execute("""
            INSERT INTO claims (
                run_id, claim_text, verdict, confidence, search_query,
                explanation, quoted_evidence, source_title, source_url
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            run_id,
            res.get("claim"),
            res.get("verdict"),
            res.get("confidence"),
            res.get("search_query"),
            res.get("explanation"),
            res.get("quoted_evidence"),
            res.get("source_title"),
            res.get("source_url")
        ))
        
    conn.commit()
    conn.close()
    return run_id

def get_history(limit: int = 50) -> list[dict]:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, timestamp, source_type, prompt, claims_count, supported_count, 
               hallucinated_count, uncertain_count, trust_index, hallucination_risk, 
               risk_level, model_used
        FROM verification_runs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]

def get_run_details(run_id: int) -> dict:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT raw_report_json FROM verification_runs WHERE id = ?", (run_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["raw_report_json"]:
        return json.loads(row["raw_report_json"])
    return None

def delete_run(run_id: int):
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM verification_runs WHERE id = ?", (run_id,))
    conn.commit()
    conn.close()

def clear_history():
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM verification_runs;")
    cursor.execute("DELETE FROM claims;")
    conn.commit()
    conn.close()

def get_analytics_stats() -> dict:
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            COUNT(*) as total_runs,
            COALESCE(SUM(claims_count), 0) as total_claims,
            COALESCE(SUM(supported_count), 0) as total_supported,
            COALESCE(SUM(hallucinated_count), 0) as total_hallucinated,
            COALESCE(SUM(uncertain_count), 0) as total_uncertain,
            COALESCE(AVG(trust_index), 0.0) as avg_trust_index,
            COALESCE(AVG(hallucination_risk), 0.0) as avg_risk
        FROM verification_runs
    """)
    stats = dict(cursor.fetchone())
    
    cursor.execute("""
        SELECT timestamp, trust_index, hallucination_risk, claims_count, supported_count, hallucinated_count, uncertain_count
        FROM verification_runs
        ORDER BY timestamp ASC
    """)
    timeline_rows = [dict(r) for r in cursor.fetchall()]
    stats["timeline"] = timeline_rows
    
    cursor.execute("""
        SELECT claim_text, count(*) as freq
        FROM claims
        WHERE verdict = 'HALLUCINATED'
        GROUP BY claim_text
        ORDER BY freq DESC
        LIMIT 10
    """)
    stats["top_hallucinated_claims"] = [dict(r) for r in cursor.fetchall()]
    
    conn.close()
    return stats

def export_history_df() -> pd.DataFrame:
    init_db()
    conn = get_connection()
    df = pd.read_sql_query("""
        SELECT id, timestamp, source_type, prompt, claims_count, supported_count, 
               hallucinated_count, uncertain_count, trust_index, hallucination_risk, risk_level, model_used
        FROM verification_runs
        ORDER BY id DESC
    """, conn)
    conn.close()
    return df

# Initialize database upon import
init_db()
