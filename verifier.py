import json
import re
from concurrent.futures import ThreadPoolExecutor
from llm import ask_llm, extract_claims, generate_response, generate_grounded_response, generate_search_query, detect_prompt_intent
from search_engine import get_rag_evidence, get_hybrid_evidence, GLOBAL_RAG_STORE
from wikipedia import clean_question_query
import storage

def find_best_verbatim_quote(claim: str, passage_snippet: str) -> str:
    """Find a clean verbatim sentence from snippet that matches the claim context."""
    if not passage_snippet:
        return "None"
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', passage_snippet) if len(s.strip()) > 10]
    if not sentences:
        return passage_snippet[:200]
    
    claim_words = [w.lower() for w in re.findall(r'\w+', claim) if len(w) > 2]
    best_sent = sentences[0]
    max_matches = -1
    for sent in sentences:
        sent_lower = sent.lower()
        matches = sum(1 for w in claim_words if w in sent_lower)
        if matches > max_matches:
            max_matches = matches
            best_sent = sent
            
    return best_sent

def verify_claim(claim: str, evidence_passages: list[dict]) -> dict:
    """
    Compare a single claim against retrieved evidence passages with strict classification rules.
    """
    if not evidence_passages:
        return {
            "verdict": "UNCERTAIN",
            "confidence": "Low",
            "explanation": "No evidence passages could be retrieved for this claim.",
            "quoted_evidence": "None",
            "source_title": None,
            "source_url": None
        }

    formatted_evidence = ""
    for i, ep in enumerate(evidence_passages, 1):
        formatted_evidence += f"Passage [{i}]: {ep['title']} (URL: {ep['url']})\nSnippet: {ep['snippet']}\n\n"

    prompt = f"""You are a strict, highly accurate factual hallucination verifier.
Compare the CLAIM with the retrieved EVIDENCE PASSAGES.

CLAIM TO VERIFY:
"{claim}"

RETRIEVED EVIDENCE PASSAGES:
{formatted_evidence}

STRICT VERDICT CLASSIFICATION RULES:

1. 'SUPPORTED':
   - Mark as 'SUPPORTED' ONLY IF at least one evidence passage explicitly states, confirms, or notes the exact relationship/assertion made in the claim.
   - DO NOT mark as 'SUPPORTED' just because the passage mentions the person or subject! The specific action, role, date, or statement MUST be explicitly confirmed in the passage text.

2. 'HALLUCINATED':
   - Mark as 'HALLUCINATED' if the evidence passage directly refutes or contradicts the claim (e.g. claim attributes an action/role to X, but passage states Y did it, or claim states a fact contradicted by the passage).
   - Mark as 'HALLUCINATED' if the claim asserts false attribution, incorrect dates, or false facts that conflict with the retrieved evidence.

3. 'UNCERTAIN':
   - Mark as 'UNCERTAIN' if the evidence passages do NOT contain sufficient factual information to either confirm or refute the claim.
   - If the evidence is silent, off-topic, or lacks information about the specific assertion in the claim, mark as 'UNCERTAIN'.

CRITICAL INSTRUCTIONS FOR QUOTES:
- "quoted_evidence" MUST be an exact verbatim substring copied word-for-word from one of the EVIDENCE PASSAGES above.
- Do NOT fabricate quotes. Do NOT copy text from instructions or rules. If verdict is UNCERTAIN, set "quoted_evidence" to "None".

JSON OUTPUT FORMAT:
Return strictly valid JSON only:
{{
  "verdict": "SUPPORTED" | "HALLUCINATED" | "UNCERTAIN",
  "confidence": "High" | "Medium" | "Low",
  "explanation": "Concise factual reason for the verdict based on the evidence.",
  "quoted_evidence": "Exact verbatim quote from evidence passage",
  "best_source_index": 1
}}
"""
    raw_response = ask_llm(prompt, temperature=0.0)
    
    clean_resp = re.sub(r'<think>.*?</think>', '', raw_response, flags=re.DOTALL).strip()
    clean_json = re.sub(r'^```(?:json)?\s*', '', clean_resp, flags=re.MULTILINE)
    clean_json = re.sub(r'```$', '', clean_json, flags=re.MULTILINE).strip()
    
    verdict = "UNCERTAIN"
    confidence = "Low"
    explanation = ""
    quoted_evidence = ""
    best_source_idx = 0

    try:
        json_match = re.search(r'\{.*\}', clean_json, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group(0))
        else:
            data = json.loads(clean_json)

        raw_v = str(data.get("verdict", "")).strip().upper()
        if raw_v in ["SUPPORTED", "HALLUCINATED", "UNCERTAIN"]:
            verdict = raw_v
        
        confidence = str(data.get("confidence", "High" if verdict != "UNCERTAIN" else "Low"))
        explanation = str(data.get("explanation", "")).strip()
        quoted_evidence = str(data.get("quoted_evidence", "")).strip()
        
        best_idx_val = data.get("best_source_index", 1)
        if isinstance(best_idx_val, int):
            best_source_idx = best_idx_val - 1
            
    except Exception:
        upper_resp = clean_resp.upper()
        if "VERDICT\": \"HALLUCINATED\"" in upper_resp or "VERDICT: HALLUCINATED" in upper_resp:
            verdict = "HALLUCINATED"
        elif "VERDICT\": \"SUPPORTED\"" in upper_resp or "VERDICT: SUPPORTED" in upper_resp:
            verdict = "SUPPORTED"
        elif "HALLUCINATED" in upper_resp and "SUPPORTED" not in upper_resp:
            verdict = "HALLUCINATED"
        elif "SUPPORTED" in upper_resp and "HALLUCINATED" not in upper_resp:
            verdict = "SUPPORTED"
            
        explanation = f"Evaluated claim against evidence passages. Classification: {verdict}."

    if best_source_idx < 0 or best_source_idx >= len(evidence_passages):
        best_source_idx = 0
        
    best_source = evidence_passages[best_source_idx]
    
    quote_valid = False
    if quoted_evidence and quoted_evidence != "None" and "STRICT VERDICT" not in quoted_evidence and "RULE" not in quoted_evidence:
        for ep in evidence_passages:
            if quoted_evidence.lower() in ep["snippet"].lower():
                quote_valid = True
                break
                
    if not quote_valid:
        if verdict != "UNCERTAIN":
            quoted_evidence = find_best_verbatim_quote(claim, best_source["snippet"])
        else:
            quoted_evidence = "None"
            
    return {
        "verdict": verdict,
        "confidence": confidence,
        "explanation": explanation if explanation else f"Claim is {verdict.lower()} based on retrieved evidence.",
        "quoted_evidence": quoted_evidence,
        "source_title": best_source["title"],
        "source_url": best_source["url"]
    }

def process_single_claim(args: tuple) -> dict:
    """Helper to verify one claim in parallel thread with target entity fallback."""
    claim, search_engine = args
    search_query = generate_search_query(claim)
    evidence_passages = get_rag_evidence(search_query, max_results=4, engine=search_engine)
    
    clean_target = clean_question_query(claim)
    if not evidence_passages or (clean_target and clean_target.lower() not in search_query.lower()):
        target_evidence = get_rag_evidence(clean_target if clean_target else claim, max_results=4, engine=search_engine)
        if target_evidence:
            evidence_passages = target_evidence + [ep for ep in evidence_passages if ep not in target_evidence]
        
    evaluation = verify_claim(claim, evidence_passages[:4])
    
    return {
        "claim": claim,
        "search_query": search_query,
        "verdict": evaluation.get("verdict", "UNCERTAIN"),
        "confidence": evaluation.get("confidence", "Medium"),
        "explanation": evaluation.get("explanation", ""),
        "quoted_evidence": evaluation.get("quoted_evidence", ""),
        "source_title": evaluation.get("source_title"),
        "source_url": evaluation.get("source_url")
    }

def correct_hallucinations(text: str, results: list[dict]) -> str:
    """Generate an AI fact-corrected version of the text based on claim results."""
    hallucinated_items = [r for r in results if r["verdict"] == "HALLUCINATED"]
    if not hallucinated_items:
        return text

    corrections_instructions = ""
    for r in hallucinated_items:
        corrections_instructions += f"- FALSE CLAIM: \"{r['claim']}\"\n  EVIDENCE / REASON: {r['explanation']}\n\n"

    prompt = f"""You are a professional fact-checker and text editor.
Rewrite the ORIGINAL TEXT to fix all hallucinated factual claims based on the factual evidence provided.

ORIGINAL TEXT:
"{text}"

HALLUCINATED CLAIMS & CORRECTIONS TO APPLY:
{corrections_instructions}

INSTRUCTIONS:
1. Preserve the style, flow, and intent of the original text as closely as possible.
2. Replace every false or hallucinated statement with the accurate fact indicated by the evidence.
3. Return ONLY the final corrected paragraph/text without meta-commentary.
"""
    corrected = ask_llm(prompt, temperature=0.2)
    return corrected.strip()

def generate_highlighted_html(text: str, results: list[dict]) -> str:
    """Generate clean HTML rendering of the text with claim-level colored badges and highlights."""
    html = text
    for r in results:
        verdict = r["verdict"]
        claim = r["claim"]
        if verdict == "SUPPORTED":
            bg = "#D1FAE5"
            border = "#059669"
            badge = "🟢 SUPPORTED"
        elif verdict == "HALLUCINATED":
            bg = "#FEE2E2"
            border = "#DC2626"
            badge = "🔴 HALLUCINATED"
        else:
            bg = "#FEF3C7"
            border = "#D97706"
            badge = "🟡 UNCERTAIN"
            
        highlight_span = f'<span style="background-color: {bg}; border-bottom: 2px solid {border}; padding: 2px 4px; border-radius: 4px; color: #1F2937; font-weight: 500;" title="{badge}: {r["explanation"]}">{claim}</span>'
        
        if claim in html:
            html = html.replace(claim, highlight_span)
            
    return html

def run_autonomous_agent(prompt_or_text: str, input_type: str = "prompt", search_engine: str = "hybrid", model_name: str = "Llama 3.3 (Groq)", save_to_db: bool = True) -> dict:
    agent_trace = []
    agent_trace.append(f"🧠 [AGENT STEP 1] Analyzing input intent (Type: {input_type.upper()})...")
    
    intent_info = detect_prompt_intent(prompt_or_text) if input_type == "prompt" else {"is_code_or_logic": False, "type": "text"}
    
    if intent_info.get("is_code_or_logic"):
        agent_trace.append("⚡ [AGENT STEP 1.1] Input identified as logic/programming request. Formulating direct technical response...")
        generated_text = generate_response(prompt_or_text)
        claims = extract_claims(generated_text)
        if not claims:
            report = {
                "text": generated_text,
                "generated_text": generated_text,
                "verified_answer": generated_text,
                "claims_count": 0,
                "results": [],
                "summary": {"supported": 0, "hallucinated": 0, "uncertain": 0},
                "trust_index": 100.0,
                "hallucination_risk": 0.0,
                "risk_level": "LOW",
                "highlighted_html": generated_text,
                "corrected_text": generated_text,
                "agent_trace": agent_trace,
                "rag_evidence": []
            }
            if save_to_db:
                storage.save_verification_run(report, source_type=input_type, prompt=prompt_or_text, model_used=model_name)
            return report

    # Step 2: RAG Multi-Source Pre-Retrieval
    agent_trace.append("📚 [RAG STEP 2] Performing Retrieval-Augmented Generation (RAG) pre-retrieval from trusted knowledge bases...")
    context_evidence = []
    if input_type == "prompt":
        search_q = prompt_or_text[:100]
        context_evidence = get_rag_evidence(search_q, max_results=4, engine=search_engine)
        agent_trace.append(f"📚 [RAG STEP 2.1] Retrieved {len(context_evidence)} trusted RAG evidence passages with semantic ranking.")
        
        # Step 3: Grounded Answer Generation
        agent_trace.append("🤖 [RAG STEP 3] Synthesizing response grounded strictly in retrieved RAG context...")
        initial_text = generate_grounded_response(prompt_or_text, context_evidence)
    else:
        initial_text = prompt_or_text
        context_evidence = get_rag_evidence(prompt_or_text[:100], max_results=4, engine=search_engine)
        agent_trace.append("📄 [RAG STEP 3] Using provided input document + RAG knowledge store for verification.")

    # Step 4: Atomic Claim Extraction & Coreference Resolution
    agent_trace.append("✂️ [AGENT STEP 4] Decomposing text into atomic factual claims with coreference resolution...")
    claims = extract_claims(initial_text)
    agent_trace.append(f"📌 [AGENT STEP 4.1] Extracted {len(claims)} atomic verifiable claims.")

    if not claims:
        report = {
            "text": initial_text,
            "generated_text": initial_text,
            "verified_answer": initial_text,
            "claims_count": 0,
            "results": [],
            "summary": {"supported": 0, "hallucinated": 0, "uncertain": 0},
            "trust_index": 100.0,
            "hallucination_risk": 0.0,
            "risk_level": "LOW",
            "highlighted_html": initial_text,
            "corrected_text": initial_text,
            "agent_trace": agent_trace,
            "rag_evidence": context_evidence
        }
        if save_to_db:
            storage.save_verification_run(report, source_type=input_type, prompt=prompt_or_text if input_type == "prompt" else None, model_used=model_name)
        return report

    # Step 5: Multi-Source Claim Verification
    agent_trace.append(f"⚡ [AGENT STEP 5] Running parallel verification on {len(claims)} claims against RAG evidence...")
    tasks = [(c, search_engine) for c in claims]
    with ThreadPoolExecutor(max_workers=min(len(claims), 5)) as executor:
        results = list(executor.map(process_single_claim, tasks))

    summary = {"supported": 0, "hallucinated": 0, "uncertain": 0}
    for res in results:
        verdict = res["verdict"]
        if verdict == "SUPPORTED":
            summary["supported"] += 1
        elif verdict == "HALLUCINATED":
            summary["hallucinated"] += 1
        else:
            summary["uncertain"] += 1

    agent_trace.append(f"📊 [AGENT STEP 5.1] Initial Audit Results -> Supported: {summary['supported']}, Hallucinated: {summary['hallucinated']}, Uncertain: {summary['uncertain']}")

    # Step 6: Agentic Self-Correction Loop
    verified_answer = initial_text
    if summary["hallucinated"] > 0:
        agent_trace.append("🔄 [AGENT STEP 6] Hallucinations detected! Triggering Agentic Self-Correction Loop...")
        for r in results:
            if r["verdict"] == "HALLUCINATED":
                agent_trace.append(f"🚨 [AGENT RE-SEARCH] Re-querying RAG evidence for false claim: '{r['claim']}'...")
                re_evidence = get_rag_evidence(r["claim"], max_results=3, engine="hybrid")
                if re_evidence:
                    re_eval = verify_claim(r["claim"], re_evidence)
                    if re_eval.get("explanation"):
                        r["explanation"] = re_eval["explanation"]

        corrected = correct_hallucinations(initial_text, results)
        verified_answer = corrected
        agent_trace.append("✨ [AGENT STEP 6.1] Generated fact-corrected final output.")
    else:
        agent_trace.append("✅ [AGENT STEP 6] All claims verified as SUPPORTED or UNCERTAIN. Output confirmed accurate.")

    total = len(claims)
    trust_index = round(((summary["supported"] + 0.5 * summary["uncertain"]) / total) * 100, 1)
    hallucination_risk = round((summary["hallucinated"] / total) * 100, 1)

    if hallucination_risk >= 40.0:
        risk_level = "HIGH"
    elif hallucination_risk >= 15.0:
        risk_level = "MODERATE"
    else:
        risk_level = "LOW"

    highlighted_html = generate_highlighted_html(initial_text, results)

    report = {
        "text": initial_text,
        "generated_text": initial_text,
        "verified_answer": verified_answer,
        "claims_count": total,
        "results": results,
        "summary": summary,
        "trust_index": trust_index,
        "hallucination_risk": hallucination_risk,
        "risk_level": risk_level,
        "highlighted_html": highlighted_html,
        "corrected_text": verified_answer,
        "agent_trace": agent_trace,
        "rag_evidence": context_evidence
    }

    if save_to_db:
        run_id = storage.save_verification_run(
            report, 
            source_type=input_type, 
            prompt=prompt_or_text if input_type == "prompt" else None, 
            model_used=model_name
        )
        report["run_id"] = run_id

    return report

def verify_text(text: str, search_engine: str = "hybrid", save_to_db: bool = True, source_type: str = "text", prompt: str = None, model_name: str = "Llama 3.3 (Groq)") -> dict:
    return run_autonomous_agent(text, input_type="text", search_engine=search_engine, model_name=model_name, save_to_db=save_to_db)

def process_prompt(prompt: str, search_engine: str = "hybrid", model_name: str = "Llama 3.3 (Groq)") -> dict:
    return run_autonomous_agent(prompt, input_type="prompt", search_engine=search_engine, model_name=model_name, save_to_db=True)
