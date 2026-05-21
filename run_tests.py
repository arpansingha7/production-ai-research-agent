import os
import sys
import unittest
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment
load_dotenv()
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from research_agent.tools import WebSearchTool, WebScraperTool
from research_agent.logger import AgentLogger
from research_agent.llm import UnifiedLLMClient

class TestSearchTool(unittest.TestCase):
    def setUp(self):
        import time
        time.sleep(2.0)  # Rate limiting safeguard
        self.tool = WebSearchTool(limit=2)

    def test_search_execution(self):
        print("\n[TEST] Running WebSearchTool...")
        res = self.tool.execute("python")
        self.assertTrue(res.success)
        self.assertIn("python", res.content.lower())
        self.assertIsNone(res.error)
        print("-> Search tool is working perfectly.")

class TestScraperTool(unittest.TestCase):
    def setUp(self):
        self.tool = WebScraperTool()

    def test_scrape_success(self):
        print("\n[TEST] Running WebScraperTool on example.com...")
        res = self.tool.execute("http://example.com")
        self.assertTrue(res.success)
        self.assertIn("example domain", res.content.lower())
        self.assertEqual(res.url, "http://example.com")
        self.assertIsNone(res.error)
        print("-> Web scraping tool is working perfectly.")

    def test_scrape_invalid_url(self):
        print("\n[TEST] Testing Scraper on invalid URL...")
        res = self.tool.execute("not_a_valid_url")
        self.assertFalse(res.success)
        self.assertEqual(res.error, "Invalid URL")
        print("-> Invalid URL failure correctly caught and reported.")

class TestLLMClient(unittest.TestCase):
    class DummySchema(BaseModel):
        response: str = Field(description="A dummy test response phrase.")
        number: int = Field(description="A dummy test number.")

    def setUp(self):
        self.logger = AgentLogger(run_id="test_run")
        self.client = UnifiedLLMClient(logger=self.logger)

    def test_structured_generation(self):
        print("\n[TEST] Testing UnifiedLLMClient structured output...")
        
        # Determine active provider
        provider = self.client.provider
        key_exists = (
            (provider == "gemini" and self.client.gemini_key is not None) or
            (provider == "groq" and self.client.groq_key is not None)
        )
        
        if not key_exists:
            print("-> Skipping LLM integration test: Active API Key not configured.")
            return
            
        prompt = "Respond with a response 'success' and a number 42."
        try:
            res = self.client.generate_structured_output(prompt, self.DummySchema)
            self.assertEqual(res.response.lower(), "success")
            self.assertEqual(res.number, 42)
            print("-> LLM Structured outputs & Pydantic validation are working perfectly.")
        except Exception as e:
            self.fail(f"LLM integration test failed: {e}")

if __name__ == "__main__":
    unittest.main()
