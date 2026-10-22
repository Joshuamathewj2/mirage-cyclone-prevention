import os
import time
import abc
import json
from typing import Optional, Dict, Any, List
from mirage.models.llm import LLMResponse

class BaseLLMAdapter(abc.ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name
        self.provider_name = self.__class__.__name__.replace("Adapter", "").upper()

    @abc.abstractmethod
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        pass

class MockAdapter(BaseLLMAdapter):
    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        start_time = time.time()
        # Mock logic based on keywords
        output = f"Mock response for: {user_prompt[:50]}..."
        if "JSON" in system_prompt or "JSON" in user_prompt:
            output = json.dumps({
                "headline": "Mock Headline",
                "executive_summary": "Mock Summary.",
                "severity": "MEDIUM",
                "affected_shelters": ["sh-01"],
                "recommended_public_actions": ["Stay calm."],
                "governance_notes": "None.",
                "confidence": 1.0
            })
            
        return LLMResponse(
            provider=self.provider_name,
            model=self.model_name,
            latency_ms=(time.time() - start_time) * 1000,
            output_text=output,
            success=True,
            total_tokens=10,
            prompt_tokens=5,
            completion_tokens=5,
            cost_estimate=0.0
        )

class OpenAIAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str = "gpt-4o"):
        super().__init__(model_name)
        self.api_key = os.getenv("OPENAI_API_KEY")

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import openai
        client = openai.OpenAI(api_key=self.api_key)
        start_time = time.time()
        try:
            response = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                timeout=30.0
            )
            latency = (time.time() - start_time) * 1000
            usage = response.usage
            text = response.choices[0].message.content
            
            # Simple cost estimate
            cost = (usage.prompt_tokens * 0.005 + usage.completion_tokens * 0.015) / 1000
            
            return LLMResponse(
                provider=self.provider_name,
                model=self.model_name,
                latency_ms=latency,
                prompt_tokens=usage.prompt_tokens,
                completion_tokens=usage.completion_tokens,
                total_tokens=usage.total_tokens,
                cost_estimate=cost,
                output_text=text,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                provider=self.provider_name,
                model=self.model_name,
                latency_ms=(time.time() - start_time) * 1000,
                output_text="",
                success=False,
                error=str(e)
            )

class ClaudeAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str = "claude-3-5-sonnet-20240620"):
        super().__init__(model_name)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import anthropic
        client = anthropic.Anthropic(api_key=self.api_key)
        start_time = time.time()
        try:
            response = client.messages.create(
                model=self.model_name,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
                max_tokens=1024,
                timeout=30.0
            )
            latency = (time.time() - start_time) * 1000
            text = response.content[0].text
            usage = response.usage
            
            # Simple cost estimate
            cost = (usage.input_tokens * 0.003 + usage.output_tokens * 0.015) / 1000
            
            return LLMResponse(
                provider=self.provider_name,
                model=self.model_name,
                latency_ms=latency,
                prompt_tokens=usage.input_tokens,
                completion_tokens=usage.output_tokens,
                total_tokens=usage.input_tokens + usage.output_tokens,
                cost_estimate=cost,
                output_text=text,
                success=True
            )
        except Exception as e:
            return LLMResponse(
                provider=self.provider_name,
                model=self.model_name,
                latency_ms=(time.time() - start_time) * 1000,
                output_text="",
                success=False,
                error=str(e)
            )

class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, model_name: Optional[str] = None):
        super().__init__(model_name or os.getenv("GEMINI_MODEL", "gemini-2.5-flash"))
        self.api_key = os.getenv("GEMINI_API_KEY")

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        start_time = time.time()
        try:
            if not self.api_key:
                raise RuntimeError("GEMINI_API_KEY is not configured")
            from google import genai
            client = genai.Client(api_key=self.api_key)
            combined_prompt = f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
            response = client.models.generate_content(model=self.model_name, contents=combined_prompt)
            latency = (time.time() - start_time) * 1000
            text = response.text or ""
            usage = getattr(response, "usage_metadata", None)
            input_tokens = getattr(usage, "prompt_token_count", 0) or 0
            output_tokens = getattr(usage, "candidates_token_count", 0) or 0
            cost = (input_tokens * 0.0035 + output_tokens * 0.0105) / 1000
            return LLMResponse(provider=self.provider_name, model=self.model_name, latency_ms=latency,
                prompt_tokens=input_tokens, completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens, cost_estimate=cost,
                output_text=text, success=True)
        except Exception as e:
            return LLMResponse(provider=self.provider_name, model=self.model_name,
                latency_ms=(time.time() - start_time) * 1000, output_text="", success=False, error=str(e))
