import streamlit as st
import os
import tempfile
import json
import re
import pandas as pd
import altair as alt
from pypdf import PdfReader
import wikipedia
import yfinance as yf
from groq import Groq

# ---------------------------- PAGE CONFIG ----------------------------
st.set_page_config(page_title="Business AI Suite", layout="wide", page_icon="📊")
st.title("📊 Business AI Suite")
st.markdown("*DealIntel AI + Ops Dashboard + Automation*")

# ---------------------------- GROQ CLIENT SETUP ----------------------------
# Try to read from secrets, but fall back to sidebar input if not available
try:
    if "GROQ_API_KEY" in st.secrets:
        groq_api_key = st.secrets["GROQ_API_KEY"]
        groq_client = Groq(api_key=groq_api_key)
        st.sidebar.success("✅ Using API key from secrets")
    else:
        raise KeyError("GROQ_API_KEY not found in secrets")
except (FileNotFoundError, KeyError, AttributeError):
    # No secrets file or key found – fall back to sidebar input
    with st.sidebar:
        st.header("🔑 Configuration")
        groq_api_key = st.text_input("Groq API Key", type="password", help="Get free key at console.groq.com")
        if groq_api_key:
            os.environ["GROQ_API_KEY"] = groq_api_key
            groq_client = Groq(api_key=groq_api_key)
        else:
            st.warning("Please enter your Groq API key to proceed.")
            st.stop()
        st.divider()
        st.caption("Built with Groq (free) – using openai/gpt-oss-20b")

# ---------------------------- HELPER FUNCTIONS (Project 1) ----------------------------
def load_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def get_company_web_data(company_name):
    context = ""
    try:
        wiki_summary = wikipedia.summary(company_name, sentences=5)
        context += f"Wikipedia Summary:\n{wiki_summary}\n\n"
    except:
        context += "Wikipedia summary not available.\n\n"
    
    try:
        ticker = yf.Ticker(company_name.replace(" ", "").upper())
        info = ticker.info
        if info:
            financials = f"Market Cap: {info.get('marketCap', 'N/A')}\n"
            financials += f"Revenue: {info.get('totalRevenue', 'N/A')}\n"
            financials += f"Gross Profit: {info.get('grossProfits', 'N/A')}\n"
            financials += f"Industry: {info.get('industry', 'N/A')}\n"
            context += f"Yahoo Finance Data:\n{financials}\n\n"
    except:
        context += "Yahoo Finance data not available.\n\n"
    return context

def call_groq(prompt, model="openai/gpt-oss-20b", temperature=0.3):
    try:
        response = groq_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"Groq API error: {e}")
        return f"ERROR: {e}"

def run_agent_pipeline(company_name, pdf_text=None):
    with st.spinner("🔍 Step 1/4: Gathering data..."):
        web_context = get_company_web_data(company_name)
        pdf_context = ""
        if pdf_text:
            pdf_context = pdf_text[:8000]
            if len(pdf_text) > 8000:
                pdf_context += "\n... (PDF truncated for length)"

    with st.spinner("📊 Step 2/4: Extracting structured data..."):
        extraction_prompt = f"""
        You are a financial analyst assistant. Given the context below about {company_name}, extract:
        1. Key Financial Metrics (Revenue, EBITDA, Net Income, Cash, Debt) – if available.
        2. Top 3 Competitors.
        3. Any major Red Flags (lawsuits, declining revenue, leadership exits).
        Return ONLY a valid JSON object with keys: "financials", "competitors", "red_flags".
        Context (web):
        {web_context}
        """
        if pdf_context:
            extraction_prompt += f"\n\nContext from uploaded PDF (excerpt):\n{pdf_context}"

        try:
            extracted_json_str = call_groq(extraction_prompt, temperature=0.2)
            if extracted_json_str.startswith("ERROR:"):
                raise Exception(extracted_json_str)
            extracted_json_str = re.sub(r'```json\s*', '', extracted_json_str)
            extracted_json_str = re.sub(r'```\s*', '', extracted_json_str)
            extracted_json = json.loads(extracted_json_str)
        except Exception as e:
            st.error(f"Extraction failed: {e}. Using fallback.")
            extracted_json = {"financials": "N/A", "competitors": ["N/A"], "red_flags": ["N/A"]}

    with st.spinner("✅ Step 3/4: Verifying facts..."):
        verification_prompt = f"""
        You are a fact-checker. Given the extracted data and original context, identify if any numbers or claims conflict.
        Extracted: {json.dumps(extracted_json)}
        Original Web Context: {web_context}
        {f"PDF excerpt: {pdf_context}" if pdf_context else ""}
        If conflicts exist, list them. If not, state "No major conflicts".
        Return a short paragraph.
        """
        try:
            verification_note = call_groq(verification_prompt, temperature=0.3)
            if verification_note.startswith("ERROR:"):
                verification_note = "Verification skipped due to API error."
        except:
            verification_note = "Verification skipped."

    with st.spinner("✍️ Step 4/4: Drafting memo..."):
        memo_prompt = f"""
        You are a senior analyst at a private equity firm. Write a concise, professional Investment Memo for {company_name}.
        
        STRUCTURE:
        1. **Executive Summary** (2 sentences)
        2. **Business Overview** (what they do, market position)
        3. **Financial Highlights** (use extracted data)
        4. **Competitive Landscape** (who they compete with)
        5. **Key Risks / Red Flags** (from extraction)
        6. **Sources Cited** (mention Wikipedia, Yahoo Finance, and uploaded PDF if provided)
        7. **Overall Confidence Score** (High/Medium/Low) with a brief reasoning.

        Extracted Data:
        {json.dumps(extracted_json, indent=2)}

        Web Context:
        {web_context}

        PDF Context (if any):
        {pdf_context if pdf_context else 'No PDF uploaded.'}

        Verification Note: {verification_note}
        """
        try:
            memo_text = call_groq(memo_prompt, temperature=0.5)
            if memo_text.startswith("ERROR:"):
                memo_text = "Memo generation failed: " + memo_text
        except Exception as e:
            st.error(f"Memo generation failed: {e}")
            memo_text = "Memo generation failed. Please try again."

    return memo_text, extracted_json, verification_note

# ---------------------------- PROJECT 2: BUSINESS OPS DASHBOARD ----------------------------
def load_sample_data():
    data = {
        "Company": ["AlphaTech", "BetaSolutions", "GammaVentures", "DeltaCapital", "EpsilonHealth"],
        "Industry": ["Tech", "Consulting", "Fintech", "Real Estate", "Healthcare"],
        "Revenue": [150, 75, 200, 120, 180],
        "EBITDA": [30, 15, 40, 25, 35],
        "Employees": [50, 25, 80, 40, 60],
        "Status": ["Active", "Active", "Exited", "Active", "Active"]
    }
    return pd.DataFrame(data)

def run_business_ops_dashboard():
    st.subheader("📊 Business Ops Dashboard")
    df = load_sample_data()
    
    st.sidebar.markdown("### Filters")
    industry_filter = st.sidebar.multiselect("Industry", options=df["Industry"].unique(), default=df["Industry"].unique())
    status_filter = st.sidebar.multiselect("Status", options=df["Status"].unique(), default=df["Status"].unique())
    
    filtered_df = df[df["Industry"].isin(industry_filter) & df["Status"].isin(status_filter)]
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Companies", len(filtered_df))
    col2.metric("Total Revenue", f"${filtered_df['Revenue'].sum():.1f}M")
    col3.metric("Total EBITDA", f"${filtered_df['EBITDA'].sum():.1f}M")
    
    col1, col2 = st.columns(2)
    with col1:
        st.altair_chart(
            alt.Chart(filtered_df).mark_bar().encode(
                x="Company", y="Revenue", color="Industry"
            ).properties(title="Revenue by Company"),
            use_container_width=True
        )
    with col2:
        st.altair_chart(
            alt.Chart(filtered_df).mark_bar().encode(
                x="Company", y="EBITDA", color="Status"
            ).properties(title="EBITDA by Company"),
            use_container_width=True
        )
    
    st.dataframe(filtered_df, use_container_width=True)
    csv = filtered_df.to_csv(index=False)
    st.download_button("⬇️ Download filtered data as CSV", data=csv, file_name="portfolio_data.csv", mime="text/csv")

# ---------------------------- PROJECT 3: WORKFLOW AUTOMATION ----------------------------
def draft_email(memo_text, company_name):
    prompt = f"""
    You are a senior analyst. Draft a concise, professional email to a client summarizing the investment memo for {company_name}.
    Include:
    - A brief introduction.
    - Key financial highlights (if any).
    - Major risks.
    - Next steps (recommend further due diligence or schedule a meeting).
    Keep it professional and to the point (max 200 words).
    
    Memo:
    {memo_text[:2000]}
    """
    try:
        email_draft = call_groq(prompt, temperature=0.4)
        if email_draft.startswith("ERROR:"):
            email_draft = "Could not generate email draft."
    except:
        email_draft = "Could not generate email draft."
    return email_draft

def run_automation(memo_text, company_name):
    st.subheader("📧 Workflow Automation – Client Email Draft")
    if not memo_text or memo_text.startswith("Memo generation failed"):
        st.warning("Please generate a memo in the DealIntel AI tab first.")
        return
    
    if st.button("✍️ Draft Client Email"):
        with st.spinner("Drafting email..."):
            email = draft_email(memo_text, company_name)
            st.text_area("Email Draft", email, height=200)
            st.info("This is a draft – you can copy, edit, and send it manually.")
            if st.button("📤 Simulate Send"):
                st.success("Email draft ready. (Simulated – not actually sent.)")

# ---------------------------- UI WITH 3 TABS ----------------------------
tab1, tab2, tab3 = st.tabs(["📈 DealIntel AI", "📊 Business Ops Dashboard", "📧 Automation"])

with tab1:
    col1, col2 = st.columns([2, 1])
    with col1:
        company_name = st.text_input("🏢 Company Name", placeholder="e.g., Tesla, Apple, Microsoft")
    with col2:
        uploaded_file = st.file_uploader("📎 Upload Pitch Deck / Annual Report (PDF)", type="pdf")
    
    if st.button("🚀 Generate Investment Memo", type="primary"):
        if not company_name:
            st.error("Please enter a company name.")
        else:
            pdf_text = None
            if uploaded_file:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                pdf_text = load_pdf(tmp_path)
                os.unlink(tmp_path)
                st.success(f"Loaded PDF: {uploaded_file.name} ({len(pdf_text)} characters)")
            
            memo, extracted, verification = run_agent_pipeline(company_name, pdf_text)
            st.divider()
            st.subheader("📝 Investment Memo")
            st.markdown(memo)
            with st.expander("🔎 View Extracted Structured Data (JSON)"):
                st.json(extracted)
            with st.expander("✅ Verification Notes"):
                st.write(verification)
            st.download_button(
                label="⬇️ Download Memo as Markdown",
                data=memo,
                file_name=f"{company_name}_investment_memo.md",
                mime="text/markdown"
            )
            st.session_state['last_memo'] = memo
            st.session_state['last_company'] = company_name

with tab2:
    run_business_ops_dashboard()

with tab3:
    memo_text = st.session_state.get('last_memo', '')
    company_name = st.session_state.get('last_company', '')
    run_automation(memo_text, company_name)