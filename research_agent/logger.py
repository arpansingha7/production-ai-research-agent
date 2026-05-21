import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from research_agent.config import settings

class AgentLogger:
    def __init__(self, run_id: Optional[str] = None):
        self.run_id = run_id or f"run_{int(time.time())}"
        self.trace: Dict[str, Any] = {
            "run_id": self.run_id,
            "timestamp": time.time(),
            "question": "",
            "plan": None,
            "steps": [],
            "final_report": None,
            "total_tokens_in": 0,
            "total_tokens_out": 0,
            "total_cost_usd": 0.0,
            "errors": []
        }
        
        # Configure console logging
        self.logger = logging.getLogger(f"ResearchAgent_{self.run_id}")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)

    def log_info(self, msg: str):
        self.logger.info(msg)

    def log_warning(self, msg: str):
        self.logger.warning(msg)

    def log_error(self, msg: str, err: Optional[Exception] = None):
        err_msg = f"{msg}: {str(err)}" if err else msg
        self.logger.error(err_msg)
        self.trace["errors"].append({
            "timestamp": time.time(),
            "message": msg,
            "error_detail": str(err) if err else None
        })

    def start_run(self, question: str):
        self.trace["question"] = question
        self.trace["timestamp"] = time.time()
        self.log_info(f"Starting research run for query: '{question}'")

    def set_plan(self, plan: Dict[str, Any]):
        self.trace["plan"] = plan
        self.log_info("Research plan established successfully.")
        for i, step in enumerate(plan.get("steps", [])):
            self.log_info(f"Plan Step {i+1}: {step}")

    def add_step(self, step_num: int, thinking: str, tool_call: Dict[str, Any]):
        step_entry = {
            "step_number": step_num,
            "timestamp": time.time(),
            "thinking": thinking,
            "tool_call": tool_call,
            "tool_result": None,
            "elapsed_seconds": 0.0
        }
        self.trace["steps"].append(step_entry)
        self.log_info(f"[Step {step_num}] Rationale: {thinking}")
        self.log_info(f"[Step {step_num}] Invoking Tool: '{tool_call.get('tool_name')}' with args {tool_call.get('arguments')}")

    def complete_step(self, step_num: int, tool_result: Dict[str, Any], elapsed_seconds: float):
        for step in self.trace["steps"]:
            if step["step_number"] == step_num:
                step["tool_result"] = tool_result
                step["elapsed_seconds"] = elapsed_seconds
                break
        status = "SUCCESS" if tool_result.get("success") else "FAILED"
        self.log_info(f"[Step {step_num}] Tool '{tool_result.get('tool_name')}' finished with status: {status} in {elapsed_seconds:.2f}s")
        if not tool_result.get("success"):
            self.log_warning(f"[Step {step_num}] Tool encountered error: {tool_result.get('error')}")

    def set_final_report(self, report: Dict[str, Any]):
        self.trace["final_report"] = report
        self.log_info("Final structured report synthesized successfully.")

    def add_tokens(self, tokens_in: int, tokens_out: int, cost_usd: float):
        self.trace["total_tokens_in"] += tokens_in
        self.trace["total_tokens_out"] += tokens_out
        self.trace["total_cost_usd"] += cost_usd

    def save_trace_to_file(self):
        log_dir = os.path.join(settings.BASE_DIR, ".logs")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{self.run_id}_trace.json")
        try:
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(self.trace, f, indent=2, ensure_ascii=False)
            self.log_info(f"Execution trace log saved to: {log_file}")
        except Exception as e:
            self.log_error("Failed to write trace log file", e)

    def get_trace(self) -> Dict[str, Any]:
        return self.trace
