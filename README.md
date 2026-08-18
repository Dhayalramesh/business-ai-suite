# Business AI Suite

**A 3-in-1 business intelligence platform** that combines AI-powered research, interactive data dashboards, and workflow automation – built for private markets, advisory, and general business operations.

🔗 **Live Demo:** [https://business-ai-suite.streamlit.app](https://business-ai-suite.streamlit.app)  
📂 **GitHub:** [https://business-ai-suite-g9pkaycuvcthqtbunbgcxv.streamlit.app/](https://github.com/Dhayalramesh/business-ai-suite)

---

## 🧩 Features

### 1. 📈 DealIntel AI – Investment Memo Generator
- Enter a company name or upload a PDF (pitch deck / annual report).
- Multi‑step AI agent: **Gather → Extract → Verify → Write**.
- Outputs a structured **Investment Memo** with:
  - Executive Summary
  - Business Overview
  - Financial Highlights (from Wikipedia & Yahoo Finance)
  - Competitive Landscape
  - Key Risks / Red Flags
  - Confidence Score
- Download memos as Markdown.

### 2. 📊 Business Ops Dashboard
- Interactive dashboard for portfolio companies.
- Filter by **Industry** and **Status**.
- Key metrics: Total Companies, Total Revenue, Total EBITDA.
- Visual charts (Revenue & EBITDA by company).
- Export filtered data as CSV.

### 3. 📧 Workflow Automation – Client Email Drafting
- After generating a memo, automatically draft a **client update email**.
- Uses Groq LLM to summarize key points into a professional email.
- Simulated send – ready for copy-paste into your email client.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | Streamlit |
| **Backend** | Python 3.12 |
| **LLM** | Groq (free tier) – `openai/gpt-oss-20b` |
| **Data Sources** | Wikipedia, Yahoo Finance (`yfinance`) |
| **PDF Parsing** | `pypdf` |
| **Data Processing** | Pandas |
| **Visualization** | Altair (Vega-Lite) |
| **Deployment** | Streamlit Cloud |

---

## 🏗️ Architecture – Build vs Buy

**Why I built this instead of using Zapier + GPT or Airtable:**

- **Multi-step verification:** Off‑the‑shelf tools can't perform a multi‑step loop where extracted data is fact‑checked against original sources.
- **Private PDF handling:** Zapier doesn't natively support semantic search or structured extraction from private, unstructured documents (pitch decks, internal memos).
- **Domain‑specific output:** The memo format is tailored for private‑equity and advisory workflows.
- **Cost:** Groq's free tier makes this sustainable for prototyping without per‑query costs.

**Trade‑offs:**
- Used Wikipedia + Yahoo Finance (free, but rate‑limited) instead of paid Bloomberg or S&P Capital IQ APIs.
- Used Streamlit for rapid UI iteration; for production, a Next.js + FastAPI split would offer more granular control.

---

## 📂 Project Structure
business-ai-suite/
├── app.py # Main application (3 tabs)
├── requirements.txt # Python dependencies
├── README.md # This file
├── .gitignore # Excludes venv, secrets, cache
└── .streamlit/
└── secrets.toml # (Optional) Store Groq API key locally



---

## 🧪 How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Dhayalramesh/business-ai-suite.git
   cd business-ai-suite

   python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

streamlit run app.py
