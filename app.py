import os
import sys
import time
import logging
import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Make sure project directory is in PATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_agent.orchestrator import ResearchOrchestrator
from research_agent.config import settings

# ---------------------------------------------------------
# Streamlit Styling (Premium Aesthetics & Modern UI)
# ---------------------------------------------------------
st.set_page_config(
    page_title="AuraResearch - Production AI Research Agent",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium CSS
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=Space+Grotesk:wght@400;500;600;700&display=swap');
    
    /* Global style overrides */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    h1, h2, h3, h4 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 600;
    }
    
    /* Modern Glassmorphic Dashboard Containers */
    .dashboard-card {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(48, 54, 61, 0.8);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(10px);
    }
    
    /* Gaps & alignment */
    .title-gradient {
        background: linear-gradient(135deg, #60A5FA 0%, #8B5CF6 50%, #EC4899 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 5px;
    }
    
    /* Realtime scrollable logger console */
    .console-box {
        background-color: #0A0D14;
        color: #38BDF8;
        font-family: 'Courier New', Courier, monospace;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #1E293B;
        height: 250px;
        overflow-y: scroll;
        white-space: pre-wrap;
        font-size: 0.9rem;
        margin-top: 10px;
    }
    
    /* Custom metric card tags */
    .metric-container {
        display: flex;
        gap: 15px;
        margin-bottom: 20px;
    }
    .metric-card {
        flex: 1;
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    .metric-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .metric-label {
        font-size: 0.8rem;
        color: #94A3B8;
        text-transform: uppercase;
        margin-top: 5px;
    }
    
    /* Highlighting citations */
    .citation-tag {
        color: #38BDF8;
        font-weight: 600;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Sidebar Configuration Panel
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/nolan/96/search.png", width=70)
st.sidebar.markdown("<h2 style='margin-top: 0px;'>Control Center</h2>", unsafe_allow_html=True)
st.sidebar.markdown("Configure agent settings and credentials in real-time.")

provider = st.sidebar.selectbox(
    "LLM Provider Target",
    options=["groq", "gemini"],
    index=0,
    help="Select the principal LLM orchestration engine."
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔑 API Keys Override")
st.sidebar.markdown("<small>Optional: Override values from `.env` file for this active session.</small>", unsafe_allow_html=True)

gemini_key = st.sidebar.text_input("Google AI Studio Key", type="password", value=os.getenv("GEMINI_API_KEY", ""))
groq_key = st.sidebar.text_input("Groq Console Key", type="password", value=os.getenv("GROQ_API_KEY", ""))

# Update global settings in-memory
if gemini_key:
    settings.GEMINI_API_KEY = gemini_key
if groq_key:
    settings.GROQ_API_KEY = groq_key

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Agent Hyperparameters")
max_steps = st.sidebar.slider("Max Search/Scrape Steps", min_value=2, max_value=8, value=settings.MAX_STEPS)
search_limit = st.sidebar.slider("Max Results Per Search", min_value=2, max_value=8, value=settings.SEARCH_LIMIT)

# Update config limits in-memory
settings.MAX_STEPS = max_steps
settings.SEARCH_LIMIT = search_limit

# ---------------------------------------------------------
# Session State Init
# ---------------------------------------------------------
if "trace_logs" not in st.session_state:
    st.session_state.trace_logs = ""
if "research_results" not in st.session_state:
    st.session_state.research_results = None
if "elapsed_time" not in st.session_state:
    st.session_state.elapsed_time = 0.0

# Custom logging handler to stream logs live to Streamlit
class StreamlitLogHandler(logging.Handler):
    def __init__(self, placeholder):
        super().__init__()
        self.placeholder = placeholder
        self.log_data = []

    def emit(self, record):
        log_entry = self.format(record)
        self.log_data.append(log_entry)
        full_logs = "\n".join(self.log_data)
        st.session_state.trace_logs = full_logs
        self.placeholder.markdown(f'<div class="console-box">{full_logs}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Page Layout
# ---------------------------------------------------------
st.markdown('<div class="title-gradient">AuraResearch Agent</div>', unsafe_allow_html=True)
st.markdown("<p style='font-size: 1.1rem; color: #94A3B8; margin-top: -10px;'>Production-Oriented ReAct Agent for Deep Analytical Research</p>", unsafe_allow_html=True)

# Example Queries dropdown
example_selection = st.selectbox(
    "💡 Need inspiration? Try an example query:",
    options=[
        "",
        "Compare the top 3 open-source vector databases for a startup building RAG products.",
        "Find 5 Indian B2B SaaS startups in HR tech and summarize their positioning.",
        "Research the pros and cons of using a multi-agent architecture for customer support automation.",
        "Compare different approaches to adding memory in an AI support agent."
    ]
)

query_input = st.text_area(
    "Enter your research-style question:",
    value=example_selection if example_selection else "Compare the top 3 open-source vector databases for a startup building RAG products.",
    height=80
)

col_run, col_clear = st.columns([1, 8])
with col_run:
    run_btn = st.button("🚀 Run Research", type="primary", use_container_width=True)
with col_clear:
    if st.button("🧹 Clear Results"):
        st.session_state.research_results = None
        st.session_state.trace_logs = ""
        st.session_state.elapsed_time = 0.0
        st.rerun()

# ---------------------------------------------------------
# Orchestration Execution Trigger
# ---------------------------------------------------------
if run_btn:
    if not query_input.strip():
        st.error("Please enter a valid research question.")
    elif not settings.GEMINI_API_KEY and not settings.GROQ_API_KEY:
        st.error("Error: Please provide at least one API Key (Gemini or Groq) in the sidebar or a local .env file.")
    else:
        st.session_state.trace_logs = ""
        st.session_state.research_results = None
        
        st.markdown("### 🔍 Live Orchestration Trace")
        console_placeholder = st.empty()
        console_placeholder.markdown('<div class="console-box">Initializing execution trace...</div>', unsafe_allow_html=True)
        
        # Attach Streamlit logging handler
        handler = StreamlitLogHandler(console_placeholder)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', '%H:%M:%S')
        handler.setFormatter(formatter)
        
        # We target the root agent logger
        run_id = f"run_{int(time.time())}"
        agent_logger = logging.getLogger(f"ResearchAgent_{run_id}")
        agent_logger.addHandler(handler)
        
        start_time = time.time()
        
        with st.spinner("Agent is actively researching the web. Please wait..."):
            try:
                # Run ReAct Orchestrator
                orchestrator = ResearchOrchestrator(provider=provider.lower(), run_id=run_id)
                # Override the default logger instance's inner logger handler
                orchestrator.logger.logger.addHandler(handler)
                
                report = orchestrator.run_research(query_input)
                
                st.session_state.research_results = report.model_dump()
                st.session_state.elapsed_time = time.time() - start_time
                st.success(f"Research completed successfully in {st.session_state.elapsed_time:.2f} seconds!")
                
            except Exception as e:
                st.error(f"Critical execution error: {str(e)}")
            finally:
                agent_logger.removeHandler(handler)
                
        # Rerun to cleanly update page display
        st.rerun()

# ---------------------------------------------------------
# Display Final Structured Report
# ---------------------------------------------------------
if st.session_state.research_results:
    report = st.session_state.research_results
    
    # 1. Metric stats
    st.markdown("---")
    st.markdown("### 📊 Research Run Metadata")
    
    # Estimate tokens / cost from session logger if available
    tok_in = report.get("total_tokens_in", 0)
    tok_out = report.get("total_tokens_out", 0)
    cost = report.get("total_cost_usd", 0.0)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{st.session_state.elapsed_time:.2f}s</div><div class="metric-label">Execution Time</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{report.get("confidence_level", "Medium")}</div><div class="metric-label">Confidence Score</div></div>', unsafe_allow_html=True)
    with col3:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{len(report.get("sources", []))}</div><div class="metric-label">Verified Sources</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{provider.upper()}</div><div class="metric-label">Active Orchestrator</div></div>', unsafe_allow_html=True)
        
    # 2. Main structured report presentation in Tabs
    st.markdown("### 📑 Synthesized Research Report")
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📝 Executive Summary",
        "🔍 Key Findings",
        "🔗 Verified Sources",
        "⚠️ Limitations & Next Steps",
        "⚙️ Trace Log"
    ])
    
    with tab1:
        st.markdown("#### Executive Summary")
        st.write(report.get("executive_summary", ""))
        
    with tab2:
        st.markdown("#### Core Key Findings")
        findings = report.get("key_findings", [])
        if findings:
            for finding in findings:
                # Add highlighting styling for citations e.g. [1]
                formatted_finding = finding
                # Simple regex replace to make [1] bold and colored
                formatted_finding = re.sub(r'\[(\d+)\]', r'**<span style="color: #38BDF8;">[\1]</span>**', formatted_finding)
                st.markdown(f"- {formatted_finding}", unsafe_allow_html=True)
        else:
            st.info("No key findings compiled.")
            
    with tab3:
        st.markdown("#### Verified Web Sources & Grounding Credibility")
        sources = report.get("sources", [])
        if sources:
            for src in sources:
                score = src.get("credibility_score", 5)
                # Color code credibility score
                score_color = "#10B981" if score >= 8 else "#F59E0B" if score >= 5 else "#EF4444"
                
                st.markdown(f"""
                <div class="dashboard-card" style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                        <h4 style="margin: 0px; font-size: 1.1rem; color: #F8FAFC;">
                            <span style="color: #38BDF8;">[{src.get("index")}]</span> {src.get("title")}
                        </h4>
                        <span style="background-color: {score_color}; color: #FFFFFF; font-size: 0.75rem; font-weight: 700; padding: 3px 8px; border-radius: 20px;">
                            CREDIBILITY: {score}/10
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94A3B8; margin-bottom: 10px;">
                        <strong>Direct URL:</strong> <a href="{src.get("url")}" target="_blank" style="color: #60A5FA;">{src.get("url")}</a>
                    </div>
                    <div style="font-size: 0.9rem; color: #E2E8F0; margin-bottom: 5px;">
                        <strong>Relevance:</strong> {src.get("relevance_reasoning")}
                    </div>
                    <div style="font-size: 0.85rem; color: #64748B; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 5px; font-style: italic;">
                        "{src.get("snippet")}"
                    </div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No sources were cataloged.")
            
    with tab4:
        st.markdown("#### Confidence Analysis & Grounding Logic")
        st.markdown(f"**Confidence Level:** `{report.get('confidence_level')}`")
        st.markdown(f"**Reasoning:** {report.get('confidence_reasoning')}")
        
        st.markdown("---")
        st.markdown("#### Scope Limitations & Execution Assumptions")
        limits = report.get("limitations_and_assumptions", [])
        if limits:
            for lim in limits:
                st.markdown(f"- ⚠️ {lim}")
        else:
            st.info("No limitations cataloged.")
            
        st.markdown("---")
        st.markdown("#### Suggested Future Deep-dive Directions")
        steps = report.get("suggested_next_steps", [])
        if steps:
            for step in steps:
                st.markdown(f"- 💡 {step}")
        else:
            st.info("No next steps suggested.")
            
    with tab5:
        st.markdown("#### Execution Trace Console")
        st.markdown("Review the exact sequential operations and tool queries performed by the ReAct Agent.")
        logs = st.session_state.trace_logs
        if logs:
            st.markdown(f'<div class="console-box">{logs}</div>', unsafe_allow_html=True)
        else:
            st.info("No execution trace logs found for this run.")
