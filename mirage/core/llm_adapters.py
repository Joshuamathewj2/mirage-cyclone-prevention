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
    def __init__(self, model_name: str = "gemini-1.5-pro"):
        super().__init__(model_name)
        self.api_key = os.getenv("GOOGLE_API_KEY")

    def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model_name)
        start_time = time.time()
        try:
            # Note: Gemini often puts system instruction in model init or starts chat
            # Using simple content generation with combined prompt for abstraction
            combined_prompt = f"SYSTEM: {system_prompt}\n\nUSER: {user_prompt}"
            response = model.generate_content(combined_prompt)
            latency = (time.time() - start_time) * 1000
            text = response.text
            
            # Token counting is slightly more complex in Gemini API, using estimates for v1
            usage_metadata = response.usage_metadata
            input_tokens = usage_metadata.prompt_token_count
            output_tokens = usage_metadata.candidates_token_count
            
            # Simple cost estimate
            cost = (input_tokens * 0.0035 + output_tokens * 0.0105) / 1000
            
            return LLMResponse(
                provider=self.provider_name,
                model=self.model_name,
                latency_ms=latency,
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
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
