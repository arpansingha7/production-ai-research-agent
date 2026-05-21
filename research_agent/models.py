from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, model_validator

class ResearchPlan(BaseModel):
    overview: str = Field(description="High-level summary of the research methodology and target insights.")
    steps: List[str] = Field(description="Step-by-step sequential tasks to perform during research.")
    target_questions: List[str] = Field(description="Core sub-questions that must be answered to satisfy the user request.")

class ToolCall(BaseModel):
    tool_name: str = Field(description="Name of the tool to invoke: 'search_web' or 'fetch_webpage' or 'synthesize'.")
    rationale: str = Field(description="Explanation of why this tool call is necessary at this step.")
    query: Optional[str] = Field(default=None, description="The search query parameter. REQUIRED if tool_name is 'search_web'.")
    url: Optional[str] = Field(default=None, description="The target URL parameter. REQUIRED if tool_name is 'fetch_webpage'.")
    arguments: Dict[str, Any] = Field(default_factory=dict, description="Arguments for the tool (e.g. {'query': '...'} or {'url': '...'}). Keep empty if tool_name is 'synthesize'.")

    @model_validator(mode="before")
    @classmethod
    def sync_arguments(cls, data: Any) -> Any:
        if isinstance(data, dict):
            args = data.get("arguments") or {}
            if not isinstance(args, dict):
                args = {}
            
            # Map query
            if "query" in args and not data.get("query"):
                data["query"] = args["query"]
            elif data.get("query") and "query" not in args:
                args["query"] = data["query"]
                
            # Map url
            if "url" in args and not data.get("url"):
                data["url"] = args["url"]
            elif data.get("url") and "url" not in args:
                args["url"] = data["url"]
                
            data["arguments"] = args
        return data

class ToolResult(BaseModel):
    tool_name: str = Field(description="Name of the tool that was executed.")
    success: bool = Field(description="Whether the tool execution succeeded without critical errors.")
    content: str = Field(description="Extracted clean text or error message from the tool execution.")
    url: Optional[str] = Field(default=None, description="Source URL associated with the execution, if applicable.")
    error: Optional[str] = Field(default=None, description="Detailed error message if execution failed.")

class Source(BaseModel):
    index: int = Field(description="Unique numeric citation index for referencing in key findings (e.g., 1, 2).")
    title: str = Field(description="Title of the source webpage or article.")
    url: str = Field(description="Direct absolute URL of the source.")
    credibility_score: int = Field(description="Trust score from 1 (unreliable) to 10 (extremely authoritative/reputable).")
    relevance_reasoning: str = Field(description="Short rationale explaining how this source helps answer the research question.")
    snippet: str = Field(description="A concise summary of key findings retrieved from this source.")

class ResearchReport(BaseModel):
    user_question: str = Field(description="The original question submitted by the user.")
    executive_summary: str = Field(description="A high-impact 2-3 paragraph summary of the research findings.")
    key_findings: List[str] = Field(description="List of core discoveries. Each discovery must be detailed and end with inline citations, e.g., '[1]' or '[2]'.")
    sources: List[Source] = Field(description="List of verified web sources with unique indices corresponding to inline citations.")
    confidence_level: str = Field(description="Overall confidence in the report: 'High', 'Medium', or 'Low'.")
    confidence_reasoning: str = Field(description="Explanatory logic justifying the chosen confidence level.")
    limitations_and_assumptions: List[str] = Field(description="Potential blindspots, failing searches, scope limits, or unverified assumptions.")
    suggested_next_steps: List[str] = Field(description="Actionable recommendations for deeper investigation.")
