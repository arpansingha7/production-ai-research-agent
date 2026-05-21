# ResearchAgent: Production-Oriented AI Research Agent

ResearchAgent is a production-grade, highly resilient agentic AI system designed to answer complex, multi-step research questions. Built with a custom **Planner-Executor (ReAct) architecture**, the system utilizes web search and content scraping tools to gather facts, handles real-world API rate limits and structural failures with self-healing fallbacks, and synthesizes structured, source-grounded research reports.

---

## 🚀 Setup & Execution Instructions

Ensure you have Python 3.10+ installed.

### 1. Installation
Clone the repository, navigate into the project directory, and install the required dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration
Create a `.env` file in the root directory (based on `.env.example`) and supply your API keys:
```env
GEMINI_API_KEY=your_google_ai_studio_api_key
GROQ_API_KEY=your_groq_console_api_key

DEFAULT_LLM_PROVIDER=groq
DEFAULT_GROQ_MODEL=llama-3.3-70b-versatile
```

### 3. Run the Streamlit Dashboard (GUI)
Start the high-fidelity web dashboard featuring real-time execution trace visualization:
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser. You can configure models, track planning logs, and view citations interactively.

### 4. Run the Command-Line Interface (CLI)
Execute research queries directly inside your terminal:
```bash
python cli.py "Compare the top 3 open-source vector databases for a startup building RAG products."
```

### 5. Run the Automated Evaluation Suite
Execute the programmatic benchmarking framework against 5 standard research queries (including happy paths and edge cases):
```bash
python evaluator.py
```
This generates an automated report file: `evaluation_report.md`.

### 6. Run Unit & Integration Tests
Verify core scraper, search retries, and LLM structured validation compliance:
```bash
python run_tests.py
```

---

## 🏛️ System Architecture

ResearchAgent is designed with a highly modular, decoupled structure to ensure reliability, visibility, and testability.

```
AI Startup Intern Assignment/
├── research_agent/
│   ├── __init__.py
│   ├── config.py         # Configuration settings & environment variables
│   ├── models.py         # Enforced Pydantic data schemas 
│   ├── llm.py            # Unified LLM interface with fallback and self-healing JSON
│   ├── tools.py          # Research tools (WebSearchTool & WebScraperTool)
│   ├── logger.py         # Structured JSON execution tracing and logging
│   └── orchestrator.py   # ReAct Planner-Executor orchestrator
├── app.py                # Premium Streamlit web app interface
├── cli.py                # Command-Line execution wrapper
├── evaluator.py          # Automatic benchmark runner
├── run_tests.py          # Test suite containing unit and integration checks
└── requirements.txt      # Python library dependencies
```

### Flow Walkthrough
1. **Plan Generation**: The `Planner` module receives the question and constructs a custom `ResearchPlan` (roadmap milestones & target sub-questions) using the active LLM.
2. **ReAct Orchestration Loop**: The agent loop evaluates remaining roadmap items. It selects either `search_web` to discover relevant URLs or `fetch_webpage` to extract deep factual contents.
3. **Execution & Fallbacks**: Tools are invoked with strict timeouts, rotated headers, and robust retries to handle rate limits and request errors.
4. **Structured Synthesis & Citations**: The synthesizer aggregates findings, evaluates source credibility, compiles inline citations, and structures the final `ResearchReport` Pydantic object.

---

## 📝 Design Decisions & Core Tradeoffs

### 1. Why choose an agentic approach here?
Traditional single-prompt RAG or simple search wrappers suffer from **context limits, information noise, and lack of synthesis depth**. 
An agentic approach is appropriate because:
- **Autonomous Roadmapping**: Complex queries (e.g. comparing vector databases or SaaS market positioning) are broad. The agent breaks them into sub-questions and sequences searches.
- **Dynamic Adaptability**: If a primary web search returns irrelevant links or a webpage fails to scrape (HTTP 403, Cloudflare block, 404), the agent evaluates the failure in its history, reframes its query, and selects alternative paths rather than failing.
- **Grounded Verification**: Instead of relying purely on search snippets (which are short and prone to SEO spam), the agent dynamically reads full webpages to verify deep claims, reducing hallucinations.

### 2. What tools were used, and why?
- **`WebSearchTool` (DuckDuckGo Search)**: DuckDuckGo was selected because it is a free, zero-config search engine that requires no external API keys. We implemented text search with a nested news search fallback to avoid transient IP rate-limiting blocks.
- **`WebScraperTool` (BeautifulSoup4)**: Used to retrieve full article text. Features rotate standard browser header sets and strip clutter tags (script, style, header, footer, interactive forms, button elements) to minimize token consumption and ignore non-factual contents.

### 3. How does the system handle bad tool results?
- **Transient Failures (Timeouts, blocks)**: The search tool integrates a 3-tier retry loop with exponential backoff. The scraper utilizes rotated User-Agents.
- **Permanent Errors (404, 403 blocks)**: If a tool execution fails, the system captures the error message, logs it into the trace, and feeds it directly into the agent's context history. The agent uses this feedback loop to adapt (e.g., searches for a different keyword or scrapes an alternative link).
- **Infinite Runaways**: We enforce a hard loop boundary of `MAX_STEPS` (default 5) and track duplicate tool calls. If the agent repeats the exact same tool and arguments twice, the loop breaks to protect tokens and prevent runaway execution costs.

### 4. How do you reduce hallucinations?
- **Pydantic Schema Grounding**: Enforcing strict Pydantic schemas restricts LLMs from generating conversational fluff or stray facts not verified.
- **Citations Mandate**: The synthesis engine prompt is strictly configured to only cite sources cataloged during the active scraping phase. Claims must end with numbered inline citations (e.g. `[1]`, `[2]`), mapping to a detailed sources registry containing direct URLs and crawled snippets.
- **Untrusted Context Guardrails**: Scraped webpage contents are packaged inside distinct XML tags inside the prompt, and the synthesizer treats them as unverified external input.

### 5. How would you make this production-ready?
- **Async Execution**: Implement asynchronous HTTP scraping (`asyncio` and `aiohttp` / `httpx`) to crawl multiple webpages in parallel, reducing overall research latency by 50-60%.
- **Persistent Caching**: Add an SQLite / Redis caching layer for crawled URLs to prevent hitting the same links across subsequent user queries, reducing network dependencies.
- **Semantic Chunking & Vector Search**: For large scraped documents, chunk text and store them in an in-memory vector index (e.g., using `Faiss` or `Chroma`) to perform semantic searches instead of loading full text into context.

### 6. What would you monitor in production?
- **Latency Breakdown**: Time spent on LLM planning vs. Search vs. Scraping vs. Synthesis.
- **Direct Costs**: Token consumption rates and USD charges per LLM provider.
- **Grounding Compliance**: Automated checks to ensure 100% of final inline citations perfectly map to live crawled sources.
- **Tool Failure Rates**: Occurrences of HTTP 403 blocks, DNS lookup errors, and DuckDuckGo search empty arrays to trigger automated proxy rotation.

### 7. What were your key tradeoffs?
- **Sequential Crawling vs. Simple Snippets**: We chose to fully scrape webpage text sequentially instead of relying strictly on Google search snippets. This increases overall execution time (latency) but results in significantly higher-quality, factual research reports.
- **Unified Fallback Client vs. Pure Single Engine**: We designed a custom client that handles fallback from Gemini to Groq. This adds minor system complexity but solves real-world quota blocks (Gemini free-tier 429 errors), ensuring 100% system availability.
- **Custom Orchestrator vs. LangGraph**: We built a lightweight custom ReAct controller instead of using LangGraph. This reduces framework bloat, avoids heavy abstraction overhead, and makes tracing, debugging, and self-healing highly readable.
