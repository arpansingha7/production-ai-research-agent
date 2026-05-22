import json
import time
from typing import Type, TypeVar, Optional, Any
from pydantic import BaseModel, ValidationError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from google import genai
from google.genai import types
from google.genai.errors import APIError as GeminiAPIError
import groq as groq_module
from groq import Groq
from groq import APIError as GroqAPIError

from research_agent.config import settings
from research_agent.logger import AgentLogger

T = TypeVar("T", bound=BaseModel)

class UnifiedLLMClient:
    def __init__(self, logger: AgentLogger, provider: Optional[str] = None):
        self.logger = logger
        # Set primary provider, default to settings config
        self.provider = provider or settings.DEFAULT_LLM_PROVIDER
        
        # Initialize Gemini Client
        self.gemini_key = settings.GEMINI_API_KEY
        self.gemini_client = None
        if self.gemini_key:
            try:
                self.gemini_client = genai.Client(api_key=self.gemini_key)
            except Exception as e:
                self.logger.log_error("Failed to initialize Gemini Client", e)

        # Initialize Groq Client with a sensible HTTP timeout to prevent hangs
        self.groq_key = settings.GROQ_API_KEY
        self.groq_client = None
        if self.groq_key:
            try:
                import httpx
                self.groq_client = Groq(
                    api_key=self.groq_key,
                    http_client=httpx.Client(timeout=httpx.Timeout(30.0, connect=5.0))
                )
            except Exception as e:
                self.logger.log_error("Failed to initialize Groq Client", e)

    @retry(
        stop=stop_after_attempt(2),           # was 3 — fail faster
        wait=wait_exponential(multiplier=1, min=1, max=4),  # was min=2, max=8
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _call_gemini_structured(self, model: str, prompt: str, schema: Type[T]) -> tuple[str, int, int]:
        """Calls Gemini and returns (response_text, input_tokens, output_tokens)."""
        if not self.gemini_client:
            raise ValueError("Gemini API key is not configured or client failed to initialize.")
        
        # Build clean schema dictionary without additionalProperties to satisfy Gemini API constraints
        try:
            raw_schema = schema.model_json_schema()
            def clean_schema(s: Any) -> Any:
                if isinstance(s, dict):
                    s.pop("additionalProperties", None)
                    for k, v in list(s.items()):
                        s[k] = clean_schema(v)
                elif isinstance(s, list):
                    s = [clean_schema(x) for x in s]
                return s
            cleaned_schema = clean_schema(raw_schema)
        except Exception:
            cleaned_schema = schema
        
        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=cleaned_schema,
            temperature=0.2
        )
        
        response = self.gemini_client.models.generate_content(
            model=model,
            contents=prompt,
            config=config
        )
        
        input_tokens = 0
        output_tokens = 0
        if response.usage_metadata:
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            
        return response.text, input_tokens, output_tokens

    @retry(
        stop=stop_after_attempt(2),           # was 3 — fail faster
        wait=wait_exponential(multiplier=1, min=1, max=4),  # was min=2, max=8
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    def _call_groq_structured(self, model: str, prompt: str, schema: Type[T]) -> tuple[str, int, int]:
        """Calls Groq with JSON mode and returns (response_text, input_tokens, output_tokens)."""
        if not self.groq_client:
            raise ValueError("Groq API key is not configured or client failed to initialize.")
        
        system_instructions = (
            "You are a precise JSON generator. Your task is to populate the fields of the following JSON schema with actual data, findings, and content based on the user prompt.\n"
            "CRITICAL RULES:\n"
            "1. You MUST generate a direct JSON object containing the populated fields of the schema. Do NOT wrap it in a list or array.\n"
            "2. DO NOT output the schema structure itself (e.g., do NOT include 'properties', 'type', 'description', or '$defs' in your output keys).\n"
            "3. Every key in your JSON object must be a field from the schema. Fill the values with your actual responses and findings.\n"
            "4. Return ONLY the valid JSON object, without any introductory or concluding text.\n\n"
            f"Target Schema structure:\n{schema.model_json_schema()}"
        )
        
        response = self.groq_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_instructions},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            timeout=30  # Hard timeout per call in seconds
        )
        
        input_tokens = 0
        output_tokens = 0
        if response.usage:
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            
        return response.choices[0].message.content, input_tokens, output_tokens

    def generate_structured_output(self, prompt: str, schema: Type[T], max_retries: int = 2) -> T:
        """
        Generates structured JSON output conforming to a Pydantic schema.
        Handles provider failures, rate limits, and automatically falls back
        to an alternative provider if available. Includes a self-healing parser
        loop for model schema errors.
        """
        current_provider = self.provider
        fallback_provider = "groq" if current_provider == "gemini" else "gemini"
        
        model = settings.DEFAULT_GEMINI_MODEL if current_provider == "gemini" else settings.DEFAULT_GROQ_MODEL
        
        attempt = 0
        last_error = None
        
        while attempt < 2:
            self.logger.log_info(f"Invoking LLM structured generator (Provider: {current_provider.upper()}, Model: {model})")
            
            try:
                if current_provider == "gemini":
                    raw_text, in_t, out_t = self._call_gemini_structured(model, prompt, schema)
                    cost = (in_t * 0.075 / 1_000_000) + (out_t * 0.30 / 1_000_000)
                else:
                    raw_text, in_t, out_t = self._call_groq_structured(model, prompt, schema)
                    cost = (in_t * 0.59 / 1_000_000) + (out_t * 0.79 / 1_000_000)
                
                self.logger.add_tokens(in_t, out_t, cost)
                
                # Strip markdown code fences if model wraps output
                cleaned_text = raw_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()
                
                try:
                    parsed_obj = schema.model_validate_json(cleaned_text)
                    return parsed_obj
                except ValidationError as ve:
                    # Self-healing loop: feed error back to model to correct
                    self.logger.log_warning(f"JSON validation failed. Attempting self-healing correction. Error: {ve}")
                    correction_prompt = (
                        f"Your previous JSON response failed validation.\n"
                        f"Error: {ve}\n"
                        f"Raw input text you generated: {cleaned_text}\n"
                        "Please regenerate the corrected JSON object that perfectly conforms to the schema."
                    )
                    
                    if current_provider == "gemini":
                        raw_text, in_t, out_t = self._call_gemini_structured(model, correction_prompt, schema)
                    else:
                        raw_text, in_t, out_t = self._call_groq_structured(model, correction_prompt, schema)
                    
                    cleaned_text = raw_text.strip()
                    if cleaned_text.startswith("```json"):
                        cleaned_text = cleaned_text[7:]
                    if cleaned_text.endswith("```"):
                        cleaned_text = cleaned_text[:-3]
                    cleaned_text = cleaned_text.strip()
                    
                    return schema.model_validate_json(cleaned_text)
                    
            except (GeminiAPIError, GroqAPIError, Exception) as api_err:
                last_error = api_err
                self.logger.log_warning(f"LLM call failed on {current_provider.upper()} provider. Error detail: {api_err}")
                
                has_fallback = (
                    (fallback_provider == "groq" and self.groq_key is not None) or
                    (fallback_provider == "gemini" and self.gemini_key is not None)
                )
                
                if has_fallback:
                    self.logger.log_info(f"[FALLBACK TRIGGERED] Gracefully falling back to {fallback_provider.upper()} due to primary provider failure.")
                    current_provider = fallback_provider
                    model = settings.DEFAULT_GEMINI_MODEL if current_provider == "gemini" else settings.DEFAULT_GROQ_MODEL
                    fallback_provider = "none"
                    attempt += 1
                    continue
                else:
                    raise last_error
            
            attempt += 1
            
        raise last_error or RuntimeError("LLM structured output generation failed all attempts.")
