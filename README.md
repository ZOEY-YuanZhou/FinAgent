# FinAgent-X: Multi-Agent Investment Intelligence Platform

FinAgent-X is a financial research system built with FastAPI, LangGraph, DuckDB, and Google Gemini LLM. It decouples quantitative risk calculation from LLMs to eliminate token costs while orchestrating specialized agents for qualitative market analysis.

---

## Key Features

- **Sequential Agent Pipeline**: Uses LangGraph to chain agents sequentially (Quant -> Fundamental -> Sentiment -> Supervisor) to enforce execution control and prevent API rate limits.
- **Zero-Token Quant Engine**: Computes Sharpe Ratio, Max Drawdown, VaR, and Beta using pure Python and DuckDB SQL without spending LLM tokens.
- **DuckDB Level-2 Cache**: Persists LLM outputs in an embedded SQL cache (`agent_cache`) to serve repeat daily requests instantly and conserve API quota.
- **Resilience & Fallback**: Features automatic LLM failover (e.g., Gemini Flash to Pro) paired with rate-limiting controls.
- **Web Dashboard**: Features a FastAPI server hosting a single-page dark terminal UI powered by Tailwind CSS and Marked.js.

---

## Architecture Flow

```text
User Request -> FastAPI (/api/v1/analyze)
  -> LangGraph Sequential Workflow
      1. Quant Agent (Python + DuckDB, 0 Tokens)
      2. Fundamental Agent (LLM + DuckDB Cache)
      3. Sentiment Agent (LLM + DuckDB Cache)
      4. CIO Supervisor Agent (LLM Final Synthesis)
  -> Return Combined JSON Report & Render Dashboard UI
```

---

## Project Structure

```text
finagent-x/
├── src/
│   ├── agents/
│   │   ├── state.py            # Global state schema (PortfolioState)
│   │   ├── quant_agent.py      # Quantitative risk node
│   │   ├── fundamental_agent.py# Fundamental analysis node
│   │   ├── sentiment_agent.py  # Market sentiment node
│   │   ├── supervisor_agent.py # CIO decision node
│   │   └── graph.py            # LangGraph workflow topology
│   ├── api/
│   │   ├── static/index.html   # Web UI dashboard
│   │   └── main.py             # FastAPI entrypoint
│   └── data_engine/
│       └── ingester.py         # DuckDB cache & market data sync
├── requirements.txt
└── README.md
```

---

## Quick Start

### 1. Installation

```bash
git clone [https://github.com/ZOEY-YuanZhou/finagent-x.git]
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Run Application

```bash
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000
```
