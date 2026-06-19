"""Gemini API client wrapper with retry, backoff, and token tracking.

Uses the google-genai SDK with structured JSON output mode.
"""

import asyncio
import time
import json
from google import genai
from google.genai import types

from config import GOOGLE_API_KEY, GEMINI_MODEL, MAX_RETRIES, INITIAL_BACKOFF_SECONDS, BACKOFF_MULTIPLIER


class TokenTracker:
    """Track cumulative token usage across all API calls."""
    
    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0
        self.failed_calls = 0
    
    def record(self, input_tokens: int, output_tokens: int):
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_calls += 1
    
    def record_failure(self):
        self.failed_calls += 1
    
    def summary(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "failed_calls": self.failed_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
        }


class GeminiClient:
    """Wrapper around google-genai SDK for multimodal analysis."""
    
    def __init__(self, api_key: str = "", model: str = ""):
        self.api_key = api_key or GOOGLE_API_KEY
        self.model = model or GEMINI_MODEL
        self.client = genai.Client(api_key=self.api_key)
        self.tracker = TokenTracker()
    
    async def analyze_with_images(
        self,
        system_prompt: str,
        user_prompt: str,
        image_parts: list[types.Part],
        semaphore: asyncio.Semaphore | None = None,
    ) -> dict:
        """Send a multimodal request to Gemini and return parsed JSON.
        
        Args:
            system_prompt: System instruction text
            user_prompt: Per-claim context text
            image_parts: List of image Part objects
            semaphore: Optional concurrency limiter
            
        Returns:
            Parsed JSON dict from Gemini's response
            
        Raises:
            RuntimeError: If all retries exhausted
        """
        if semaphore:
            async with semaphore:
                return await self._call_with_retry(system_prompt, user_prompt, image_parts)
        return await self._call_with_retry(system_prompt, user_prompt, image_parts)
    
    async def _call_with_retry(
        self,
        system_prompt: str,
        user_prompt: str,
        image_parts: list[types.Part],
    ) -> dict:
        """Call Gemini with exponential backoff retry."""
        backoff = INITIAL_BACKOFF_SECONDS
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                return await self._single_call(system_prompt, user_prompt, image_parts)
            except Exception as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    await asyncio.sleep(backoff)
                    backoff *= BACKOFF_MULTIPLIER
                else:
                    self.tracker.record_failure()
        
        raise RuntimeError(f"Gemini API failed after {MAX_RETRIES + 1} attempts: {last_error}")
    
    async def _single_call(
        self,
        system_prompt: str,
        user_prompt: str,
        image_parts: list[types.Part],
    ) -> dict:
        """Make a single Gemini API call with structured JSON output."""
        # Build contents: text prompt + images
        contents = [types.Part.from_text(text=user_prompt)] + image_parts
        
        config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            temperature=0.1,  # Low temperature for deterministic output
        )
        
        # Run sync call in thread pool to not block event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: self.client.models.generate_content(
                model=self.model,
                contents=contents,
                config=config,
            )
        )
        
        # Track tokens
        if response.usage_metadata:
            self.tracker.record(
                input_tokens=response.usage_metadata.prompt_token_count or 0,
                output_tokens=response.usage_metadata.candidates_token_count or 0,
            )
        else:
            self.tracker.record(0, 0)
        
        # Parse JSON response
        text = response.text
        if not text:
            raise ValueError("Empty response from Gemini")
        
        return json.loads(text)


def create_image_part(image_bytes: bytes, mime_type: str) -> types.Part:
    """Create a Gemini Part from image bytes."""
    return types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
