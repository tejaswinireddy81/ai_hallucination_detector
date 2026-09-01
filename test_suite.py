import json
import time
import verifier
import storage
import server
from fastapi.testclient import TestClient

def clean_console_str(text: str) -> str:
    if not text:
        return ""
    return text.encode('ascii', 'ignore').decode('ascii')

def test_storage():
    print("\n--- TEST 1: DATABASE PERSISTENCE (`storage.py`) ---")
    storage.init_db()
    
    sample_report = {
        "text": "Thomas Edison invented the telephone.",
        "claims_count": 1,
        "summary": {"supported": 0, "hallucinated": 1, "uncertain": 0},
        "trust_index": 0.0,
        "hallucination_risk": 100.0,
        "risk_level": "HIGH",
        "corrected_text": "Alexander Graham Bell invented the telephone.",
        "results": [
            {
                "claim": "Thomas Edison invented the telephone.",
                "verdict": "HALLUCINATED",
                "confidence": "High",
                "search_query": "Thomas Edison telephone invention",
                "explanation": "Alexander Graham Bell invented the telephone.",
                "quoted_evidence": "Alexander Graham Bell was awarded the first US patent for the telephone.",
                "source_title": "Telephone",
                "source_url": "https://en.wikipedia.org/wiki/Telephone"
            }
        ]
    }
    
    run_id = storage.save_verification_run(sample_report, source_type="test_run", model_used="Test Model")
    print(f"Saved test run with ID: {run_id}")
    
    history = storage.get_history(limit=5)
    assert len(history) > 0, "History should not be empty"
    print(f"History count: {len(history)}")
    
    stats = storage.get_analytics_stats()
    print(f"Stats summary: Total runs={stats['total_runs']}, Total claims={stats['total_claims']}, Avg trust={stats['avg_trust_index']}%")
    print("Database test PASSED.")

def test_autonomous_agent():
    print("\n--- TEST 2: AUTONOMOUS AGENT ENGINE (`verifier.py`) ---")
    test_prompt = "Who invented the telephone and when?"
    print(f"Running Autonomous Agent on prompt: \"{test_prompt}\"")
    
    t0 = time.time()
    report = verifier.run_autonomous_agent(test_prompt, input_type="prompt", save_to_db=False)
    elapsed = time.time() - t0
    
    print(f"Completed in {elapsed:.2f}s")
    print(f"Verified Answer: {clean_console_str(report.get('verified_answer'))}")
    print(f"Agent Trace Steps ({len(report.get('agent_trace', []))}):")
    for step in report.get("agent_trace", []):
        print(f"  - {clean_console_str(step)}")

        
    assert "verified_answer" in report, "Report missing verified_answer"
    assert "agent_trace" in report, "Report missing agent_trace"
    print("Autonomous Agent Engine test PASSED.")

def test_api_server():
    print("\n--- TEST 3: REST API SERVER ENDPOINTS (`server.py`) ---")
    client = TestClient(server.app)
    
    # Test /api/health
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    print("GET /api/health PASSED.")
    
    # Test /api/agent-verify
    agent_resp = client.post("/api/agent-verify", json={"input": "What is the capital of France?", "type": "prompt"})
    assert agent_resp.status_code == 200
    assert "verified_answer" in agent_resp.json()
    print("POST /api/agent-verify PASSED.")

    # Test /api/stats
    response = client.get("/api/stats")
    assert response.status_code == 200
    assert "total_runs" in response.json()
    print("GET /api/stats PASSED.")
    
    # Test /api/history
    response = client.get("/api/history")
    assert response.status_code == 200
    assert "history" in response.json()
    print("GET /api/history PASSED.")
    
    print("REST API Server tests PASSED.")


def run_all_tests():
    print("============================================================")
    print("RUNNING AI HALLUCINATION DETECTOR ENTERPRISE SUITE")
    print("============================================================")
    
    test_storage()
    test_autonomous_agent()
    test_api_server()

    
    print("============================================================")
    print("ALL TESTS PASSED SUCCESSFULLY!")
    print("============================================================")

if __name__ == "__main__":
    run_all_tests()
