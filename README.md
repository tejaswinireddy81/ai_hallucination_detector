# 🛡️ Enterprise AI Hallucination Guardrail & Analytics Engine

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%2070B-orange.svg)](https://groq.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An end-to-end **Enterprise AI Safety & Hallucination Guardrail Platform** that autonomously decomposes LLM responses into atomic claims, resolves coreferences, pre-retrieves multi-source evidence (Wikipedia REST API + Hybrid Web Search), runs parallel claim verification, and executes closed-loop self-correction to output **Fact-Guaranteed Answers**.

---

## 🏗️ System Architecture

```
                                ┌──────────────────────────────────┐
                                │  Chrome Extension (Manifest V3) │
                                │  - Real-time Web Fact Audit     │
                                └────────────────┬─────────────────┘
                                                 │ (POST /api/agent-verify)
                                                 ▼
┌─────────────────────────┐             ┌──────────────────────────────────┐
│ Streamlit UI            │ ──────────► │ FastAPI REST Server (server.py)  │
│ (app.py)                │             └────────────────┬─────────────────┘
└─────────────────────────┘                              │
                                                         ▼
                                        ┌──────────────────────────────────┐
                                        │ Autonomous Agent Engine          │
                                        │ (verifier.py)                    │
                                        └────────────────┬─────────────────┘
                                                         │
       ┌─────────────────────────────────────────────────┼─────────────────────────────────────────────────┐
       ▼                                                 ▼                                                 ▼
┌───────────────────────────┐             ┌───────────────────────────┐             ┌───────────────────────────┐
│ Groq API (Llama 3.3 70B)  │             │ Multi-Source Search       │             │ SQLite Database           │
│ - Atomic Claim Extraction │             │ - Wikipedia REST API      │             │ (storage.py)              │
│ - Coreference Resolution  │             │ - DuckDuckGo Web Search   │             │ - Analytics & Audit Logs  │
│ - Fact Grounding          │             │ - Entity Location Cleaner │             │                           │
└───────────────────────────┘             └───────────────────────────┘             └───────────────────────────┘
```

---

## 🔥 Key Features

- 🤖 **Autonomous Fact-Checking Agent**: Extracts standalone atomic claims, resolves pronouns to explicit entity names, and pre-retrieves multi-source evidence.
- 🔄 **Closed-Loop Self-Correction**: Detects hallucinated claims, re-queries evidence knowledge bases, and automatically synthesizes fact-corrected outputs.
- 🔒 **Zero UI Exposure Key Management**: Automatically loads environment keys from `.env` while featuring a 0-key hybrid fallback engine out of the box.
- 📊 **Factual Analytics Dashboard**: Real-time Plotly charts including Verdict Distribution Donut Chart, Trust Index vs Risk Timeline, and searchable SQLite audit logs.
- 🧪 **AI Hallucination Benchmark Evaluator**: Built-in 4-category factual stress test suite measuring precision across Historical, Corporate, Scientific, and Trap prompts.
- 🔌 **Chrome MV3 Extension & REST API**: Full FastAPI server integration for browser context-menu auditing and external LLM guardrail pipelines.

---

## 📐 Mathematical Formulation

### Factual Trust Index
$$\text{Trust Index (\%)} = \left( \frac{S + 0.5 \cdot U}{N} \right) \times 100$$
*Where $S$ = Supported claims, $U$ = Uncertain claims, and $N$ = Total atomic claims.*

### Hallucination Risk Score
$$\text{Risk (\%)} = \left( \frac{H}{N} \right) \times 100$$
*Where $H$ = Hallucinated claims and $N$ = Total atomic claims.*

---

## 🚀 Quick Start & Installation

### 1. Clone Repository & Setup Virtual Environment
```bash
git clone https://github.com/your-username/hallucination-detector.git
cd hallucination-detector

python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment Key (Optional)
Create or edit `.env` in the root folder:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```
*(Note: If no API key is provided, the engine automatically runs in Multi-Source Hybrid Search Fallback mode!)*

### 4. Launch Streamlit Analytics Dashboard
```bash
python -m streamlit run app.py
```
Open **[http://localhost:8501](http://localhost:8501)** in your browser.

### 5. Launch FastAPI REST Server
```bash
python server.py
```
Backend API will be live at **[http://localhost:8000](http://localhost:8000)** (Interactive Docs at `/docs`).

---

## 🔌 API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/agent-verify` | Execute full autonomous agent workflow (Intent -> Grounding -> Claim Extraction -> Parallel Verification -> Correction). |
| `POST` | `/api/generate-and-verify` | Generate LLM response for a prompt, audit factual claims, and log metrics. |
| `POST` | `/api/verify` | Audit arbitrary text block for hallucinations. |
| `GET` | `/api/stats` | Retrieve aggregate analytics statistics for visual reporting. |
| `GET` | `/api/history` | Retrieve full SQLite audit log history. |

---

## 🧩 Chrome Extension Setup (Manifest V3)

1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Enable **Developer mode** (top right toggle).
3. Click **Load unpacked** and select the `extension/` directory.
4. Ensure `python server.py` is running on port 8000.
5. Highlight any text on any webpage -> Right click -> **Audit Factual Claims**.

---

## 📜 Citation & Research Reference

If you use this system or architecture in academic research, please cite:

```bibtex
@article{hallucination_guardrail_2026,
  title={An Autonomous Multi-Source Agentic Framework for Real-Time LLM Hallucination Detection, Fact-Grounding, and Closed-Loop Self-Correction},
  author={Tejaswini et al.},
  journal={Enterprise AI Safety & Guardrail Architecture},
  year={2026}
}
```

---

## 📄 License
Distributed under the **MIT License**. See `LICENSE` for more information.