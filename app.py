import os
import sys
import time
import logging
import re
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
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');
    
    /* Global style overrides */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #030712 !important;
        color: #f3f4f6 !important;
    }
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 700;
        color: #ffffff;
    }
    
    /* Modern Glassmorphic Dashboard Containers */
    .dashboard-card {
        background: rgba(15, 23, 42, 0.65) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 16px !important;
        padding: 24px !important;
        margin-bottom: 20px !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        position: relative;
        overflow: hidden;
    }
    .dashboard-card:hover {
        border-color: rgba(56, 189, 248, 0.3) !important;
        box-shadow: 0 15px 35px rgba(0, 0, 0, 0.3), 0 0 25px rgba(56, 189, 248, 0.08) !important;
        transform: translateY(-2px);
    }
    
    /* Sidebar custom styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #090d16 0%, #05070c 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05) !important;
    }
    [data-testid="stSidebar"] h2 {
        font-family: 'Space Grotesk', sans-serif;
        font-weight: 800;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #38bdf8 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Premium button styles */
    div.stButton > button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 50%, #ec4899 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 12px 28px !important;
        font-weight: 700 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        letter-spacing: 0.03em !important;
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1) !important;
        box-shadow: 0 6px 20px rgba(139, 92, 246, 0.3) !important;
        width: 100%;
        margin-top: 10px;
    }
    div.stButton > button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 12px 30px rgba(139, 92, 246, 0.5) !important;
        filter: brightness(1.15) !important;
    }
    div.stButton > button:active {
        transform: translateY(-1px) scale(0.99) !important;
    }
    
    /* Target secondary button specifically */
    div.stButton button[kind="secondary"] {
        background: rgba(255, 255, 255, 0.05) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        box-shadow: none !important;
    }
    div.stButton button[kind="secondary"]:hover {
        background: rgba(255, 255, 255, 0.1) !important;
        border-color: rgba(255, 255, 255, 0.2) !important;
    }
    
    /* Premium input field overrides */
    .stTextArea textarea, .stTextInput input, .stSelectbox [data-baseweb="select"] {
        background: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        padding: 12px 16px !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    .stTextArea textarea:focus, .stTextInput input:focus, .stSelectbox [data-baseweb="select"]:focus {
        border-color: #38bdf8 !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.15) !important;
    }
    
    /* Header layout */
    .title-container {
        text-align: center;
        padding: 35px 0 25px 0;
        position: relative;
    }
    .title-gradient {
        font-family: 'Space Grotesk', sans-serif;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 40%, #ec4899 70%, #10b981 100%);
        background-size: 300% 300%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.8rem;
        font-weight: 800;
        letter-spacing: -0.03em;
        margin-bottom: 12px;
        animation: gradientShift 8s infinite alternate ease-in-out;
    }
    .subtitle {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 1.15rem;
        color: #94a3b8;
        font-weight: 400;
        max-width: 700px;
        margin: 0 auto;
        line-height: 1.6;
    }
    .pulse-badge {
        display: inline-flex;
        align-items: center;
        background: rgba(124, 58, 237, 0.12);
        border: 1px solid rgba(124, 58, 237, 0.3);
        padding: 6px 16px;
        border-radius: 50px;
        font-size: 0.8rem;
        font-weight: 700;
        color: #c084fc;
        margin-bottom: 16px;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: 0.05em;
    }
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    
    /* macOS retro-futuristic developer terminal */
    .terminal-window {
        background: #080c14;
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        box-shadow: 0 20px 40px rgba(0,0,0,0.6), 0 0 30px rgba(124, 58, 237, 0.15);
        overflow: hidden;
        margin-top: 15px;
        margin-bottom: 25px;
    }
    .terminal-header {
        background: #0f172a;
        padding: 12px 16px;
        display: flex;
        align-items: center;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
        position: relative;
    }
    .terminal-buttons {
        display: flex;
        gap: 8px;
    }
    .terminal-btn {
        width: 12px;
        height: 12px;
        border-radius: 50%;
        display: inline-block;
    }
    .terminal-btn.close { background-color: #ff5f56; }
    .terminal-btn.minimize { background-color: #ffbd2e; }
    .terminal-btn.expand { background-color: #27c93f; }
    
    .terminal-title {
        color: #94a3b8;
        font-size: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 500;
        position: absolute;
        left: 50%;
        transform: translateX(-50%);
    }
    .terminal-status {
        margin-left: auto;
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        font-size: 0.75rem;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 6px;
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: 'JetBrains Mono', monospace;
    }
    .status-dot {
        width: 6px;
        height: 6px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
    }
    .pulsing {
        animation: statusPulse 1.5s infinite ease-in-out;
    }
    @keyframes statusPulse {
        0% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1.2); opacity: 0.5; box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(1); opacity: 1; box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }
    
    .console-box {
        background-color: #04060a;
        color: #e2e8f0;
        font-family: 'JetBrains Mono', 'Space Mono', monospace;
        padding: 20px;
        height: 380px;
        overflow-y: auto;
        font-size: 0.85rem;
        line-height: 1.6;
        margin: 0;
        border: none;
        box-shadow: inset 0 10px 20px rgba(0, 0, 0, 0.8);
    }
    .console-box::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    .console-box::-webkit-scrollbar-track {
        background: #04060a;
    }
    .console-box::-webkit-scrollbar-thumb {
        background: #1e293b;
        border-radius: 4px;
    }
    .console-box::-webkit-scrollbar-thumb:hover {
        background: #334155;
    }
    
    /* Interactive metrics card grid */
    .metric-card {
        background: linear-gradient(135deg, rgba(15, 23, 42, 0.8) 0%, rgba(30, 41, 59, 0.5) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        text-align: center;
        position: relative;
        overflow: hidden;
        backdrop-filter: blur(16px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: radial-gradient(circle at top right, rgba(56, 189, 248, 0.1), transparent 60%);
        opacity: 0;
        transition: opacity 0.4s ease;
    }
    .metric-card:hover {
        transform: translateY(-6px);
        border-color: rgba(56, 189, 248, 0.4);
        box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4), 0 0 20px rgba(56, 189, 248, 0.2);
    }
    .metric-card:hover::before {
        opacity: 1;
    }
    .metric-icon {
        font-size: 2.2rem;
        margin-bottom: 12px;
        filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        transition: transform 0.3s ease;
    }
    .metric-card:hover .metric-icon {
        transform: scale(1.15) rotate(5deg);
    }
    .metric-value {
        font-family: 'Space Grotesk', sans-serif;
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #00f2fe 0%, #4facfe 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 8px;
    }
    /* Set custom colors for each column metric card card */
    .metric-card:nth-child(2) .metric-value {
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    .metric-card:nth-child(3) .metric-value {
        background: linear-gradient(135deg, #10b981 0%, #34d399 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    .metric-card:nth-child(4) .metric-value {
        background: linear-gradient(135deg, #f472b6 0%, #ec4899 100%) !important;
        -webkit-background-clip: text !important;
        -webkit-text-fill-color: transparent !important;
    }
    .metric-label {
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 0.75rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
    }
    
    /* Glassmorphic Capsule Tabs styling */
    div[data-baseweb="tab-list"] {
        background: rgba(15, 23, 42, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        padding: 8px !important;
        border-radius: 16px !important;
        gap: 10px !important;
        margin-bottom: 30px !important;
        backdrop-filter: blur(16px) !important;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2) !important;
    }
    button[data-baseweb="tab"] {
        background: transparent !important;
        color: #94a3b8 !important;
        font-family: 'Space Grotesk', sans-serif !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
        padding: 10px 22px !important;
        border-radius: 12px !important;
        border: 1px solid transparent !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    button[data-baseweb="tab"]:hover {
        background: rgba(255, 255, 255, 0.04) !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.05) !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(139, 92, 246, 0.15) 100%) !important;
        color: #38bdf8 !important;
        border: 1px solid rgba(56, 189, 248, 0.25) !important;
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.1) !important;
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
        
        # Color coding simple terms inside live terminal stream
        colored_logs = full_logs
        colored_logs = colored_logs.replace(" - INFO - ", " - <span style='color: #10B981;'>INFO</span> - ")
        colored_logs = colored_logs.replace(" - WARNING - ", " - <span style='color: #F59E0B;'>WARNING</span> - ")
        colored_logs = colored_logs.replace(" - ERROR - ", " - <span style='color: #EF4444;'>ERROR</span> - ")
        colored_logs = colored_logs.replace("Running Web Search:", "<span style='color: #38BDF8;'>Running Web Search:</span>")
        colored_logs = colored_logs.replace("Scraping page:", "<span style='color: #F472B6;'>Scraping page:</span>")
        colored_logs = colored_logs.replace("Entering new ReAct Step", "<span style='color: #A78BFA; font-weight: bold;'>Entering new ReAct Step</span>")
        colored_logs = colored_logs.replace("Executing ToolCall:", "<span style='color: #06B6D4;'>Executing ToolCall:</span>")
        
        terminal_html = f"""
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-buttons">
                    <span class="terminal-btn close"></span>
                    <span class="terminal-btn minimize"></span>
                    <span class="terminal-btn expand"></span>
                </div>
                <div class="terminal-title">aura-research-agent -- react-executor</div>
                <div class="terminal-status"><span class="status-dot pulsing"></span>RUNNING</div>
            </div>
            <div class="console-box">{colored_logs}</div>
        </div>
        """
        self.placeholder.markdown(terminal_html, unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Page Layout
# ---------------------------------------------------------
st.markdown("""
<div class="title-container">
    <div class="pulse-badge">🚀 DEEP COGNITIVE INTELLIGENCE</div>
    <div class="title-gradient">AuraResearch Agent</div>
    <div class="subtitle">A production-grade Planner-Executor ReAct Agent synthesizing hyper-grounded research reports with full source lineage.</div>
</div>
""", unsafe_allow_html=True)

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
        
        init_terminal = """
        <div class="terminal-window">
            <div class="terminal-header">
                <div class="terminal-buttons">
                    <span class="terminal-btn close"></span>
                    <span class="terminal-btn minimize"></span>
                    <span class="terminal-btn expand"></span>
                </div>
                <div class="terminal-title">aura-research-agent -- react-executor</div>
                <div class="terminal-status"><span class="status-dot pulsing"></span>STARTING</div>
            </div>
            <div class="console-box">Initializing execution trace...</div>
        </div>
        """
        console_placeholder.markdown(init_terminal, unsafe_allow_html=True)
        
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
                if 'orchestrator' in locals() and hasattr(orchestrator, 'logger'):
                    orchestrator.logger.logger.removeHandler(handler)
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
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">⚡</div>
            <div class="metric-value">{st.session_state.elapsed_time:.2f}s</div>
            <div class="metric-label">Execution Time</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🛡️</div>
            <div class="metric-value">{report.get("confidence_level", "Medium")}</div>
            <div class="metric-label">Confidence Score</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🔗</div>
            <div class="metric-value">{len(report.get("sources", []))}</div>
            <div class="metric-label">Verified Sources</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-icon">🤖</div>
            <div class="metric-value">{provider.upper()}</div>
            <div class="metric-label">Active Orchestrator</div>
        </div>
        """, unsafe_allow_html=True)
        
    # 2. Main structured report presentation in Tabs
    st.markdown("<br>### 📑 Synthesized Research Report", unsafe_allow_html=True)
    
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
                <div class="dashboard-card" style="margin-bottom: 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <h4 style="margin: 0px; font-size: 1.15rem; color: #ffffff;">
                            <span style="color: #38BDF8;">[{src.get("index")}]</span> {src.get("title")}
                        </h4>
                        <span style="background: rgba({16 if score>=8 else 245 if score>=5 else 239}, {185 if score>=8 else 158 if score>=5 else 68}, {129 if score>=8 else 11 if score>=5 else 68}, 0.15); color: {score_color}; border: 1px solid rgba({16 if score>=8 else 245 if score>=5 else 239}, {185 if score>=8 else 158 if score>=5 else 68}, {129 if score>=8 else 11 if score>=5 else 68}, 0.3); font-size: 0.75rem; font-weight: 800; padding: 4px 10px; border-radius: 50px; font-family: 'JetBrains Mono', monospace;">
                            CREDIBILITY: {score}/10
                        </span>
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-bottom: 12px; font-family: 'JetBrains Mono', monospace;">
                        <strong>Direct URL:</strong> <a href="{src.get("url")}" target="_blank" style="color: #38bdf8; text-decoration: none; border-bottom: 1px dashed rgba(56, 189, 248, 0.4);">{src.get("url")}</a>
                    </div>
                    <div style="font-size: 0.95rem; color: #e2e8f0; margin-bottom: 10px; line-height: 1.5;">
                        <strong>Relevance:</strong> {src.get("relevance_reasoning")}
                    </div>
                    <div style="font-size: 0.85rem; color: #94a3b8; background: rgba(0,0,0,0.3); padding: 12px 16px; border-radius: 8px; border-left: 3px solid #7c3aed; font-style: italic; line-height: 1.6;">
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
            colored_logs = logs
            colored_logs = colored_logs.replace(" - INFO - ", " - <span style='color: #10B981;'>INFO</span> - ")
            colored_logs = colored_logs.replace(" - WARNING - ", " - <span style='color: #F59E0B;'>WARNING</span> - ")
            colored_logs = colored_logs.replace(" - ERROR - ", " - <span style='color: #EF4444;'>ERROR</span> - ")
            colored_logs = colored_logs.replace("Running Web Search:", "<span style='color: #38BDF8;'>Running Web Search:</span>")
            colored_logs = colored_logs.replace("Scraping page:", "<span style='color: #F472B6;'>Scraping page:</span>")
            colored_logs = colored_logs.replace("Entering new ReAct Step", "<span style='color: #A78BFA; font-weight: bold;'>Entering new ReAct Step</span>")
            colored_logs = colored_logs.replace("Executing ToolCall:", "<span style='color: #06B6D4;'>Executing ToolCall:</span>")
            
            terminal_html = f"""
            <div class="terminal-window">
                <div class="terminal-header">
                    <div class="terminal-buttons">
                        <span class="terminal-btn close"></span>
                        <span class="terminal-btn minimize"></span>
                        <span class="terminal-btn expand"></span>
                    </div>
                    <div class="terminal-title">aura-research-agent -- react-executor</div>
                    <div class="terminal-status" style="color: #60A5FA; background: rgba(96, 165, 250, 0.15);"><span class="status-dot" style="background-color: #60A5FA;"></span>FINISHED</div>
                </div>
                <div class="console-box">{colored_logs}</div>
            </div>
            """
            st.markdown(terminal_html, unsafe_allow_html=True)
        else:
            st.info("No execution trace logs found for this run.")
