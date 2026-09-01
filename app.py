import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import os
import time
from datetime import datetime
import verifier
import storage
import llm
from search_engine import GLOBAL_RAG_STORE

# Page Configuration
st.set_page_config(
    page_title="Enterprise AI Hallucination Guardrail & RAG Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ultra-High Readability & Custom Sidebar Styling
st.markdown("""
<style>
    /* Global Base Styling & Large Typography */
    html, body, [class*="css"], .stApp {
        background: linear-gradient(135deg, #0B0F19 0%, #111827 50%, #0F172A 100%);
        color: #F8FAFC !important;
        font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
        font-size: 1.15rem !important;
    }
    
    p, span, label, div {
        font-size: 1.12rem !important;
        color: #F8FAFC;
    }

    /* Fix Sidebar Width & Eliminate Unnecessary Scrollbar */
    section[data-testid="stSidebar"] {
        width: 360px !important;
        min-width: 360px !important;
        background-color: #0F172A !important;
        border-right: 1.5px solid rgba(255, 255, 255, 0.15) !important;
    }
    section[data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }
    section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] label {
        font-size: 1.05rem !important;
        color: #E2E8F0 !important;
        font-weight: 700 !important;
    }

    /* Header Container - Huge Prominent Title */
    .hero-container {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.9), rgba(15, 23, 42, 0.98));
        border: 2px solid rgba(56, 189, 248, 0.35);
        border-radius: 20px;
        padding: 30px 24px;
        margin-bottom: 24px;
        text-align: center;
        box-shadow: 0 12px 45px rgba(0, 0, 0, 0.6);
        backdrop-filter: blur(14px);
    }
    .hero-title {
        font-size: 3.4rem !important;
        font-weight: 900 !important;
        letter-spacing: -0.02em;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.25;
    }

    /* Headings & Subheaders */
    h1, h2, h3, .stSubheader {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        margin-top: 12px !important;
        margin-bottom: 12px !important;
    }

    /* Navigation Tabs - Large & Readable */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: rgba(15, 23, 42, 0.85);
        padding: 8px;
        border-radius: 14px;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #CBD5E1 !important;
        font-weight: 700 !important;
        padding: 12px 24px !important;
        font-size: 1.15rem !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #4F46E5, #3B82F6) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        box-shadow: 0 4px 20px rgba(59, 130, 246, 0.4);
    }

    /* Form Inputs, Text Areas & Select Boxes */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
        font-size: 1.15rem !important;
        color: #FFFFFF !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1.5px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
    }
    .stTextInput label, .stTextArea label, .stSelectbox label, .stSlider label {
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        color: #38BDF8 !important;
        margin-bottom: 6px !important;
    }

    /* Buttons - Large & Prominent */
    .stButton button {
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        padding: 10px 20px !important;
        border-radius: 10px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.2s ease !important;
    }
    .stButton button[kind="primary"] {
        background: linear-gradient(135deg, #2563EB, #4F46E5) !important;
        color: #FFFFFF !important;
        font-size: 1.3rem !important;
        padding: 12px 26px !important;
        box-shadow: 0 6px 25px rgba(37, 99, 235, 0.4) !important;
    }

    .status-box {
        background: rgba(16, 185, 129, 0.12);
        border: 1.5px solid rgba(16, 185, 129, 0.4);
        padding: 12px 14px;
        border-radius: 12px;
        margin-bottom: 14px;
    }
    .status-indicator {
        display: flex;
        align-items: center;
        gap: 8px;
        color: #34D399;
        font-weight: 800;
        font-size: 1.05rem !important;
    }
    .pulse-dot {
        height: 10px;
        width: 10px;
        background-color: #10B981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 10px #10B981;
    }

    /* Metric Cards - Large Numbers */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95));
        border: 1.5px solid rgba(255, 255, 255, 0.15);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(8px);
    }
    .metric-title {
        color: #94A3B8;
        font-size: 0.95rem !important;
        font-weight: 800 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        margin-bottom: 6px;
    }
    .metric-val {
        color: #FFFFFF;
        font-size: 2.3rem !important;
        font-weight: 900 !important;
    }

    /* High-Contrast Claim Callout Cards */
    .claim-card-supported {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.35), rgba(15, 23, 42, 0.9));
        border-left: 8px solid #10B981;
        border-top: 1.5px solid rgba(16, 185, 129, 0.3);
        border-right: 1.5px solid rgba(16, 185, 129, 0.3);
        border-bottom: 1.5px solid rgba(16, 185, 129, 0.3);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 6px 25px rgba(0,0,0,0.4);
    }
    .claim-card-hallucinated {
        background: linear-gradient(135deg, rgba(127, 29, 29, 0.35), rgba(15, 23, 42, 0.9));
        border-left: 8px solid #EF4444;
        border-top: 1.5px solid rgba(239, 68, 68, 0.3);
        border-right: 1.5px solid rgba(239, 68, 68, 0.3);
        border-bottom: 1.5px solid rgba(239, 68, 68, 0.3);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 6px 25px rgba(0,0,0,0.4);
    }
    .claim-card-uncertain {
        background: linear-gradient(135deg, rgba(120, 53, 15, 0.35), rgba(15, 23, 42, 0.9));
        border-left: 8px solid #F59E0B;
        border-top: 1.5px solid rgba(245, 158, 11, 0.3);
        border-right: 1.5px solid rgba(245, 158, 11, 0.3);
        border-bottom: 1.5px solid rgba(245, 158, 11, 0.3);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 18px;
        box-shadow: 0 6px 25px rgba(0,0,0,0.4);
    }

    .claim-header {
        font-size: 1.35rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        margin-bottom: 10px;
        line-height: 1.4;
    }
    .claim-meta {
        font-size: 1.05rem !important;
        color: #CBD5E1 !important;
        margin-bottom: 10px;
    }
    .claim-explanation {
        background: rgba(15, 23, 42, 0.75);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        padding: 14px 16px;
        color: #F1F5F9 !important;
        font-size: 1.12rem !important;
        line-height: 1.6;
        margin-bottom: 10px;
    }
    .claim-quote {
        background: rgba(30, 41, 59, 0.85);
        border-left: 4px solid #38BDF8;
        border-radius: 8px;
        padding: 12px 16px;
        color: #93C5FD !important;
        font-size: 1.08rem !important;
        font-style: italic;
        margin-bottom: 10px;
    }

    /* Badges */
    .badge-supported {
        background-color: #064E3B;
        color: #34D399 !important;
        padding: 5px 14px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.95rem !important;
        border: 1.5px solid #059669;
    }
    .badge-hallucinated {
        background-color: #7F1D1D;
        color: #FCA5A5 !important;
        padding: 5px 14px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.95rem !important;
        border: 1.5px solid #DC2626;
    }
    .badge-uncertain {
        background-color: #78350F;
        color: #FCD34D !important;
        padding: 5px 14px;
        border-radius: 20px;
        font-weight: 800;
        font-size: 0.95rem !important;
        border: 1.5px solid #D97706;
    }

    /* Glass Answer Box */
    .glass-answer-box {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.3), rgba(15, 23, 42, 0.9));
        border: 2px solid rgba(16, 185, 129, 0.5);
        border-radius: 16px;
        padding: 26px;
        margin-bottom: 26px;
        color: #FFFFFF !important;
        font-size: 1.25rem !important;
        line-height: 1.8;
        box-shadow: 0 10px 35px rgba(0, 0, 0, 0.4);
    }
    .glass-box {
        background: rgba(30, 41, 59, 0.6);
        border: 1.5px solid rgba(255, 255, 255, 0.15);
        border-radius: 14px;
        padding: 22px;
        margin-bottom: 20px;
        color: #F8FAFC !important;
        font-size: 1.15rem !important;
        line-height: 1.7;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State for Prompt Input
if "user_prompt_text" not in st.session_state:
    st.session_state.user_prompt_text = ""

# Sidebar Controls - Compact & Clean Layout (No Scroll Required)
with st.sidebar:
    st.markdown("<h2 style='font-size: 1.6rem !important; margin: 0 0 10px 0;'>🛡️ Engine Controls</h2>", unsafe_allow_html=True)
    
    st.markdown("""
    <div class="status-box">
        <div class="status-indicator">
            <span class="pulse-dot"></span>
            Guardrail Engine Active
        </div>
        <div style="color: #CBD5E1; font-size: 0.88rem !important; margin-top: 4px;">
            RAG Pre-Retrieval & Fact Audit Active
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    model_choice = st.selectbox(
        "🤖 Verification Model",
        ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768", "gemma2-9b-it"],
        index=0
    )
    
    search_mode = st.selectbox(
        "📚 Evidence Retrieval",
        ["hybrid", "wikipedia", "web"],
        format_func=lambda x: "🌐 Hybrid Search" if x == "hybrid" else ("📚 Wikipedia REST API" if x == "wikipedia" else "🔎 Web Search"),
        index=0
    )
    
    parallel_workers = st.slider(
        "⚡ Parallel Workers",
        min_value=1,
        max_value=8,
        value=5
    )
    
    st.markdown("---")
    
    ingested_count = len(GLOBAL_RAG_STORE.documents)
    chunk_count = len(GLOBAL_RAG_STORE.chunks)
    
    st.markdown(f"📚 **RAG Docs:** <b style='color: #38BDF8;'>{ingested_count}</b> &nbsp;|&nbsp; 🧩 **Chunks:** <b style='color: #38BDF8;'>{chunk_count}</b>", unsafe_allow_html=True)
    
    try:
        side_stats = storage.get_analytics_stats()
        st.markdown(f"📊 **Audits:** <b style='color: #34D399;'>{side_stats['total_runs']}</b> &nbsp;|&nbsp; 🛡️ **Trust:** <b style='color: #34D399;'>{round(side_stats['avg_trust_index'], 1)}%</b>", unsafe_allow_html=True)
    except Exception:
        pass

    st.markdown("<div style='margin-top: 14px; font-size: 0.82rem; color: #94A3B8;'>🚀 AI Hallucination Guardrail v3.5</div>", unsafe_allow_html=True)

# App Header - Huge Prominent Title
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🛡️ Enterprise AI Hallucination Guardrail & RAG Engine</div>
</div>
""", unsafe_allow_html=True)

# Main Navigation Tabs
tabs = st.tabs([
    "🚀 Prompt & Real-Time Audit", 
    "📄 Document & Custom RAG Audit", 
    "📊 Factual Analytics Dashboard", 
    "🧪 Model Benchmark Evaluator",
    "⚙️ Engine Diagnostics"
])

def render_agent_trace(report):
    trace = report.get("agent_trace", [])
    if trace:
        with st.expander("🤖 Autonomous Agent Execution Trace (RAG Retrieval & Step Log)", expanded=False):
            for step in trace:
                st.markdown(f"<code style='font-size: 1.05rem;'>{step}</code>", unsafe_allow_html=True)

def render_verification_summary(report):
    c1, c2, c3, c4, c5 = st.columns(5)
    
    trust_idx = report.get("trust_index", 0.0)
    risk_score = report.get("hallucination_risk", 0.0)
    risk_lvl = report.get("risk_level", "LOW")
    
    with c1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Trust Index</div>
            <div class="metric-val" style="color: {'#34D399' if trust_idx >= 75 else ('#FCD34D' if trust_idx >= 50 else '#FCA5A5')};">{trust_idx}%</div>
        </div>
        """, unsafe_allow_html=True)
    with c2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Hallucination Risk</div>
            <div class="metric-val" style="color: {'#FCA5A5' if risk_score >= 40 else ('#FCD34D' if risk_score >= 15 else '#34D399')};">{risk_score}%</div>
            <div style="color: #94A3B8; font-size: 0.9rem; font-weight: 700;">{risk_lvl} RISK</div>
        </div>
        """, unsafe_allow_html=True)
    with c3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Atomic Claims</div>
            <div class="metric-val">{report.get('claims_count', 0)}</div>
        </div>
        """, unsafe_allow_html=True)
    with c4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🟢 Supported</div>
            <div class="metric-val" style="color: #34D399;">{report['summary']['supported']}</div>
        </div>
        """, unsafe_allow_html=True)
    with c5:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">🔴 Hallucinated</div>
            <div class="metric-val" style="color: #FCA5A5;">{report['summary']['hallucinated']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.divider()

def render_rag_inspector(report):
    rag_items = report.get("rag_evidence", [])
    if rag_items:
        st.markdown("### 📚 RAG Trusted Knowledge Sources & Context Inspector")
        st.markdown("Top evidence passages retrieved via **Retrieval-Augmented Generation (RAG)** used to ground the response:")
        
        c_cols = st.columns(min(len(rag_items), 4))
        for idx, item in enumerate(rag_items[:4]):
            col = c_cols[idx % len(c_cols)]
            with col:
                sim_score = item.get("similarity_score", 90.0)
                src_type = item.get("source_type", "Trusted Source")
                title_short = item.get('title', 'Knowledge Chunk').replace("Wikipedia: ", "")
                st.markdown(f"""
                <div style="background: rgba(30, 41, 59, 0.85); border: 1.5px solid rgba(56, 189, 248, 0.4); border-radius: 14px; padding: 16px; margin-bottom: 14px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                        <span style="color: #38BDF8; font-weight: 800; font-size: 0.95rem;">Rank #{idx+1}</span>
                        <span style="background: rgba(16, 185, 129, 0.3); color: #34D399; padding: 3px 10px; border-radius: 12px; font-weight: 800; font-size: 0.9rem; border: 1px solid #059669;">Score: {sim_score}%</span>
                    </div>
                    <div style="color: #6EE7B7; font-size: 0.85rem; font-weight: 700; margin-bottom: 6px;">{src_type}</div>
                    <div style="color: #FFFFFF; font-weight: 800; font-size: 1.05rem; margin-bottom: 8px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="{title_short}">{title_short}</div>
                    <div style="color: #E2E8F0; font-size: 0.95rem; line-height: 1.5; max-height: 100px; overflow-y: auto;">"{item.get('snippet', '')[:180]}..."</div>
                </div>
                """, unsafe_allow_html=True)
                if item.get("url") and not str(item.get("url")).startswith("#"):
                    st.markdown(f"🔗 <a href='{item['url']}' target='_blank' style='font-size: 1rem; font-weight: 700; color: #38BDF8;'>View Source Document</a>", unsafe_allow_html=True)
        st.divider()

def render_claim_results(report, filter_verdict=None):
    st.markdown("### 🔍 Claim-Level Factual Audit & Evidence Attribution")
    
    results = report.get("results", [])
    if filter_verdict and filter_verdict != "ALL":
        results = [r for r in results if r["verdict"] == filter_verdict]
        
    if not results:
        st.info("No claims match the selected filter.")
        return
        
    for i, res in enumerate(results, 1):
        verdict = res["verdict"]
        if verdict == "SUPPORTED":
            card_class = "claim-card-supported"
            badge = '<span class="badge-supported">🟢 SUPPORTED</span>'
        elif verdict == "HALLUCINATED":
            card_class = "claim-card-hallucinated"
            badge = '<span class="badge-hallucinated">🔴 HALLUCINATED</span>'
        else:
            card_class = "claim-card-uncertain"
            badge = '<span class="badge-uncertain">🟡 UNCERTAIN</span>'
            
        st.markdown(f"""
        <div class="{card_class}">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <span style="color: #94A3B8; font-weight: 800; font-size: 0.95rem; text-transform: uppercase;">Atomic Claim #{i}</span>
                <div>{badge}</div>
            </div>
            <div class="claim-header">"{res['claim']}"</div>
            <div class="claim-meta">
                <b>Confidence:</b> <code style="color: #38BDF8; font-size: 1rem;">{res['confidence']}</code> &nbsp;|&nbsp; 
                <b>Target Search Query:</b> <code style="color: #C084FC; font-size: 1rem;">{res.get('search_query', 'N/A')}</code>
            </div>
            <div class="claim-explanation">
                <b>💬 Factual Explanation:</b> {res['explanation']}
            </div>
            {f'<div class="claim-quote"><b>📖 Verbatim RAG Quote:</b> "{res["quoted_evidence"]}"</div>' if res.get("quoted_evidence") and res["quoted_evidence"] != "None" else ''}
            {f'<div style="margin-top: 8px;">🔗 <b>Source:</b> <a href="{res["source_url"]}" target="_blank" style="color: #38BDF8; font-size: 1.05rem; font-weight: 700;">{res.get("source_title", "View Article")}</a></div>' if res.get("source_url") else ''}
        </div>
        """, unsafe_allow_html=True)

# ==========================================
# TAB 1: 🚀 PROMPT & REAL-TIME AUDIT
# ==========================================
with tabs[0]:
    st.subheader("🤖 Autonomous RAG Agent Prompt Answering & Fact Verification")
    st.markdown("Enter any prompt or select a sample question to trigger RAG evidence retrieval from trusted sources:")
    
    # Quick Sample Pills
    st.markdown("**⚡ Quick Sample Prompts:**")
    sample_col1, sample_col2, sample_col3, sample_col4 = st.columns(4)
    with sample_col1:
        if st.button("🏢 Corporate Leadership", use_container_width=True):
            st.session_state.user_prompt_text = "Who is the CEO of Microsoft and when was the company founded?"
    with sample_col2:
        if st.button("🚀 Astronomy & Space", use_container_width=True):
            st.session_state.user_prompt_text = "What is the average distance from Earth to Mars and who walked on the moon first?"
    with sample_col3:
        if st.button("📜 Historical Inventions", use_container_width=True):
            st.session_state.user_prompt_text = "Who invented the telephone in 1876 and where was he born?"
    with sample_col4:
        if st.button("🧬 Physics & Relativity", use_container_width=True):
            st.session_state.user_prompt_text = "Who discovered the law of the photoelectric effect and won the Nobel Prize for it?"

    st.markdown("<br>", unsafe_allow_html=True)
    user_prompt = st.text_input(
        "Enter prompt for RAG Fact-Checking Agent:", 
        value=st.session_state.user_prompt_text,
        placeholder="e.g. Who is the CEO of Microsoft and when was the company founded?"
    )
    
    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        btn_gen = st.button("🚀 Execute RAG Guardrail", type="primary", use_container_width=True)
        
    if btn_gen or (user_prompt and st.session_state.get("trigger_run", False)):
        if not user_prompt.strip():
            st.warning("Please enter a prompt to execute.")
        else:
            with st.spinner("🤖 RAG Agent retrieving trusted evidence, synthesizing answer & verifying claims..."):
                try:
                    report = verifier.process_prompt(user_prompt, search_engine=search_mode, model_name=model_choice)
                    
                    render_agent_trace(report)
                    render_verification_summary(report)
                    
                    st.markdown("### ✨ Grounded & Verified Output")
                    st.markdown(f"""
                    <div class="glass-answer-box">
                        <div style="color: #34D399; font-weight: 800; font-size: 1.05rem; text-transform: uppercase; margin-bottom: 10px;">
                            🟢 Fact-Grounded Verified Answer
                        </div>
                        {report.get("verified_answer", report.get("corrected_text", report.get("text")))}
                    </div>
                    """, unsafe_allow_html=True)
                    
                    with st.expander("🔍 View Highlighted Initial Response Analysis", expanded=False):
                        st.markdown(f'<div class="glass-box">{report.get("highlighted_html", report.get("text"))}</div>', unsafe_allow_html=True)
                    
                    render_rag_inspector(report)
                    render_claim_results(report)
                except Exception as e:
                    st.error(f"Error executing guardrail request: {e}")

# ==========================================
# TAB 2: 📄 DOCUMENT & CUSTOM RAG AUDIT
# ==========================================
with tabs[1]:
    st.subheader("Audit Factual Claims against Custom Trusted Knowledge Documents (RAG)")
    
    # Custom RAG Document Ingestion Section
    with st.expander("📥 Upload / Ingest Custom Trusted Documents into RAG Store", expanded=False):
        st.markdown("Ingest custom trusted documentation (.txt, .json, .csv, .md) to create an in-memory RAG vector index:")
        doc_name_in = st.text_input("Trusted Document Title:", value="Official Product Documentation")
        doc_text_in = st.text_area("Paste Trusted Document Content:", height=140, placeholder="Paste official reference documentation here...")
        
        c_ing1, c_ing2 = st.columns([1, 3])
        with c_ing1:
            if st.button("⚡ Ingest into RAG Store", type="primary"):
                if doc_text_in.strip():
                    added = GLOBAL_RAG_STORE.ingest_document(doc_text_in.strip(), doc_name=doc_name_in.strip())
                    st.success(f"Successfully indexed **{added}** semantic RAG chunks into trusted knowledge store!")
                else:
                    st.warning("Please paste document content to ingest.")
        with c_ing2:
            if st.button("🗑️ Clear Ingested RAG Documents"):
                GLOBAL_RAG_STORE.clear()
                st.info("Cleared all custom ingested RAG documents.")

    st.markdown("---")
    audit_mode = st.radio("Choose Audit Input Mode", ["Single Text Block", "Batch File Upload (.txt, .json, .csv)", "Load Preset Sample Document"], horizontal=True)
    
    if audit_mode == "Single Text Block":
        text_input = st.text_area(
            "Paste AI-generated text or response to verify:", 
            height=180, 
            placeholder="e.g. Satya Nadella is the CEO of Microsoft. Microsoft was founded in 1975 by Bill Gates and Paul Allen. Thomas Edison invented the telephone."
        )
        
        filter_choice = st.selectbox("Filter Results by Verdict", ["ALL", "SUPPORTED", "HALLUCINATED", "UNCERTAIN"], index=0)
        
        if st.button("🔍 Run Document Audit", type="primary"):
            if not text_input.strip():
                st.warning("Please paste text to audit.")
            else:
                with st.spinner("🤖 Agent extracting atomic claims & verifying against RAG evidence..."):
                    try:
                        report = verifier.verify_text(text_input, search_engine=search_mode, model_name=model_choice, source_type="text")
                        render_agent_trace(report)
                        render_verification_summary(report)
                        
                        st.markdown("### ✨ Grounded & Verified Output")
                        st.markdown(f"""
                        <div class="glass-answer-box">
                            <div style="color: #34D399; font-weight: 800; font-size: 1.05rem; text-transform: uppercase; margin-bottom: 10px;">
                                🟢 Agent Verified Corrected Version
                            </div>
                            {report.get("verified_answer", report.get("corrected_text", report.get("text")))}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        with st.expander("🔍 View Highlighted Factual Analysis", expanded=False):
                            st.markdown(f'<div class="glass-box">{report.get("highlighted_html", report.get("text"))}</div>', unsafe_allow_html=True)
                        
                        render_rag_inspector(report)
                        render_claim_results(report, filter_verdict=filter_choice)
                    except Exception as e:
                        st.error(f"Error auditing text: {e}")

    elif audit_mode == "Batch File Upload (.txt, .json, .csv)":
        uploaded_file = st.file_uploader("Upload document for batch audit", type=["txt", "json", "csv"])
        if uploaded_file is not None:
            content = uploaded_file.read().decode("utf-8")
            st.info(f"File uploaded: **{uploaded_file.name}** ({len(content)} characters)")
            
            if st.button("⚡ Audit Uploaded Document", type="primary"):
                with st.spinner("Running batch verification pipeline..."):
                    report = verifier.verify_text(content, search_engine=search_mode, model_name=model_choice, source_type="file")
                    render_verification_summary(report)
                    render_rag_inspector(report)
                    render_claim_results(report)
                    
                    report_bytes = json.dumps(report, indent=2).encode('utf-8')
                    st.download_button(
                        label="📥 Download Audit Report (JSON)",
                        data=report_bytes,
                        file_name=f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )

    else:
        st.markdown("#### Load Preset Sample Factual Test Documents")
        preset_choice = st.selectbox(
            "Select Preset Document",
            ["Corporate & Tech Leadership", "Historical & Scientific Claims", "Mixed Hallucination Stress Test"]
        )
        
        presets_dict = {
            "Corporate & Tech Leadership": "Satya Nadella is the chief executive officer of Microsoft. Tim Cook leads Apple Inc. Sundar Pichai serves as CEO of Alphabet and Google.",
            "Historical & Scientific Claims": "Alexander Graham Bell was awarded the first US patent for the telephone in 1876. Thomas Edison invented the light bulb. Albert Einstein discovered the law of the photoelectric effect.",
            "Mixed Hallucination Stress Test": "Thomas Edison invented the telephone in 1876. Satya Nadella leads Microsoft. Albert Einstein was the first person to walk on the moon."
        }
        
        selected_text = presets_dict[preset_choice]
        st.text_area("Preset Document Content:", value=selected_text, height=120, disabled=True)
        
        if st.button("🚀 Audit Preset Document", type="primary"):
            with st.spinner("Auditing preset document..."):
                report = verifier.verify_text(selected_text, search_engine=search_mode, model_name=model_choice, source_type="preset")
                render_verification_summary(report)
                render_rag_inspector(report)
                render_claim_results(report)

# ==========================================
# TAB 3: 📊 FACTUAL ANALYTICS DASHBOARD
# ==========================================
with tabs[2]:
    st.subheader("📊 Factual Integrity & Hallucination Analytics Dashboard")
    
    stats = storage.get_analytics_stats()
    
    if stats["total_runs"] == 0:
        st.info("No audit logs recorded yet. Run prompts or text audits in Tab 1 & Tab 2 to generate analytics!")
    else:
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Audits Run", stats["total_runs"])
        c2.metric("Total Claims Verified", stats["total_claims"])
        c3.metric("Average Trust Index", f"{round(stats['avg_trust_index'], 1)}%")
        c4.metric("Avg Hallucination Rate", f"{round(stats['avg_risk'], 1)}%")
        
        st.divider()
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            st.markdown("#### 🍩 Claim Verdict Distribution")
            labels = ["Supported", "Hallucinated", "Uncertain"]
            values = [stats["total_supported"], stats["total_hallucinated"], stats["total_uncertain"]]
            
            fig_donut = px.pie(
                names=labels, values=values, hole=0.5,
                color=labels, color_discrete_map={"Supported":"#10B981", "Hallucinated":"#EF4444", "Uncertain":"#F59E0B"}
            )
            fig_donut.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
            st.plotly_chart(fig_donut, use_container_width=True)
            
        with col_chart2:
            st.markdown("#### 📈 Trust Index & Hallucination Risk Timeline")
            df_timeline = pd.DataFrame(stats["timeline"])
            if not df_timeline.empty:
                fig_line = px.line(
                    df_timeline, x="timestamp", y=["trust_index", "hallucination_risk"],
                    labels={"value": "Percentage (%)", "variable": "Metric"},
                    color_discrete_map={"trust_index": "#34D399", "hallucination_risk": "#EF4444"}
                )
                fig_line.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font_color="#F8FAFC")
                st.plotly_chart(fig_line, use_container_width=True)
            else:
                st.caption("Insufficient timeline data.")

        st.divider()
        st.markdown("#### 📜 Audit History & Database Log")
        
        df_history = storage.export_history_df()
        if not df_history.empty:
            st.dataframe(
                df_history,
                column_config={
                    "trust_index": st.column_config.NumberColumn("Trust Index (%)", format="%.1f%%"),
                    "hallucination_risk": st.column_config.NumberColumn("Risk (%)", format="%.1f%%"),
                    "source_type": st.column_config.TextColumn("Source"),
                    "timestamp": st.column_config.DatetimeColumn("Timestamp")
                },
                use_container_width=True
            )
            
            csv_data = df_history.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Export Full Audit History (CSV)",
                data=csv_data,
                file_name="hallucination_audit_history.csv",
                mime="text/csv"
            )

# ==========================================
# TAB 4: 🧪 MODEL BENCHMARK EVALUATOR
# ==========================================
with tabs[3]:
    st.subheader("🧪 Built-in AI Hallucination Benchmark Evaluator")
    st.markdown("Evaluate model accuracy across pre-set factual categories (Historical, Corporate, Science & Trick Questions).")
    
    benchmark_suite = [
        {"name": "Historical Attribution Test", "text": "Thomas Edison invented the telephone in 1876. Alexander Graham Bell was born in Scotland."},
        {"name": "Corporate Leadership Test", "text": "Satya Nadella is the CEO of Microsoft. Tim Cook leads Apple Inc."},
        {"name": "Scientific Astronomy Test", "text": "The Earth revolves around the Sun. Jupiter is the smallest planet in the Solar System."},
        {"name": "Common Hallucination Trap", "text": "Albert Einstein won the Nobel Prize in Physics for his discovery of the law of the photoelectric effect. He was the first person to set foot on the moon."}
    ]
    
    if st.button("⚡ Run Full Benchmark Suite", type="primary"):
        results_bench = []
        progress_bar = st.progress(0)
        
        for idx, item in enumerate(benchmark_suite):
            st.markdown(f"Running **{item['name']}**...")
            rep = verifier.verify_text(item["text"], search_engine=search_mode, model_name=model_choice, save_to_db=False)
            results_bench.append({
                "Test Name": item["name"],
                "Input Text": item["text"],
                "Trust Index (%)": rep["trust_index"],
                "Hallucination Risk (%)": rep["hallucination_risk"],
                "Supported": rep["summary"]["supported"],
                "Hallucinated": rep["summary"]["hallucinated"],
                "Uncertain": rep["summary"]["uncertain"]
            })
            progress_bar.progress((idx + 1) / len(benchmark_suite))
            
        st.success("Benchmark Execution Complete!")
        df_bench = pd.DataFrame(results_bench)
        st.dataframe(df_bench, use_container_width=True)

# ==========================================
# TAB 5: ⚙️ ENGINE DIAGNOSTICS & SYSTEM CONTROLS
# ==========================================
with tabs[4]:
    st.subheader("⚙️ Guardrail System Diagnostics & Controls")
    
    # Diagnostics Cards
    d1, d2, d3, d4 = st.columns(4)
    with d1:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">RAG Engine</div>
            <div class="metric-val" style="color: #34D399; font-size: 1.3rem !important;">RAG Active</div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">Semantic Chunks + Wiki</div>
        </div>
        """, unsafe_allow_html=True)
    with d2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Database Storage</div>
            <div class="metric-val" style="color: #38BDF8; font-size: 1.3rem !important;">SQLite Active</div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">hallucinations.db</div>
        </div>
        """, unsafe_allow_html=True)
    with d3:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Coreference Engine</div>
            <div class="metric-val" style="color: #C084FC; font-size: 1.3rem !important;">Atomic Resolver</div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">Claim Extraction v3</div>
        </div>
        """, unsafe_allow_html=True)
    with d4:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-title">Parallel Workers</div>
            <div class="metric-val" style="color: #FCD34D; font-size: 1.3rem !important;">Multi-Threaded</div>
            <div style="color: #94A3B8; font-size: 0.9rem; margin-top: 4px;">Concurrent Pool</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    
    st.markdown("#### 🔒 Backend Environment Configuration (.env)")
    env_key = os.getenv("GROQ_API_KEY", "")
    if env_key and not env_key.startswith("your_"):
        st.success("🟢 **Groq API Key Active**: Configured in `.env`. High-speed Llama 3.3 70B live model generation is active!")
    else:
        st.info("ℹ️ Running in **Multi-Source Hybrid Search Mode** (Wikipedia REST API + Web Search).")
        with st.expander("🔑 Save Groq API Key to .env file (One-Time Setup)", expanded=False):
            st.markdown("Paste your free Groq API key (get one free at [console.groq.com](https://console.groq.com/keys)) to activate Llama 3.3 70B AI generation:")
            key_input = st.text_input("Enter GROQ_API_KEY:", type="password", placeholder="gsk_...")
            if st.button("💾 Save Key to .env"):
                if key_input.strip():
                    llm.set_groq_api_key(key_input.strip())
                    with open(".env", "w") as f:
                        f.write(f"GROQ_API_KEY={key_input.strip()}\n")
                    st.success("API Key saved to .env file and activated successfully!")
                    st.rerun()

    st.divider()
    
    st.markdown("#### Database Administration")
    col_db1, col_db2 = st.columns(2)
    with col_db1:
        if st.button("🗑️ Clear Audit History Database"):
            storage.clear_history()
            st.success("Database audit history wiped successfully!")
            st.rerun()
    with col_db2:
        if st.button("🔄 Refresh Analytics Cache"):
            st.success("Analytics cache refreshed!")
            st.rerun()
