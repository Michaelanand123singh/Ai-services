"""
Multi-LLM Client for handling different AI providers
"""
from typing import Dict, Any, List, Optional, Union
import asyncio
import openai
import google.generativeai as genai
from dataclasses import dataclass

from src.core.config import settings
from src.core.logger import ai_logger, log_ai_model_call
from src.core.exceptions import AIServiceException, AIProviderError


@dataclass
class AIResponse:
    """Standardized AI response format"""
    content: str
    provider: str
    model: str
    tokens_used: Optional[int] = None
    finish_reason: Optional[str] = None


class MultiLLMClient:
    """Multi-provider LLM client with fallback support"""
    
    def __init__(self):
        self.primary_provider = settings.primary_ai_provider
        self.fallback_provider = settings.fallback_ai_provider
        self.enable_fallback = settings.enable_ai_fallback
        
        # Initialize OpenAI if available
        if settings.openai_api_key:
            openai.api_key = settings.openai_api_key
            
        # Initialize Gemini if available
        if settings.gemini_api_key:
            genai.configure(api_key=settings.gemini_api_key)
    
    async def generate_text(
        self,
        prompt: str,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None
    ) -> AIResponse:
        """Generate text using the configured AI provider"""
        try:
            return await self._generate_with_provider(
                self.primary_provider, prompt, max_tokens, temperature, model, system_prompt
            )
        except Exception as e:
            ai_logger.log_error(e, {"provider": self.primary_provider})
            
            if self.enable_fallback and self.fallback_provider != self.primary_provider:
                try:
                    ai_logger.logger.warning(f"Falling back to {self.fallback_provider}")
                    return await self._generate_with_provider(
                        self.fallback_provider, prompt, max_tokens, temperature, model, system_prompt
                    )
                except Exception as fallback_error:
                    ai_logger.log_error(fallback_error, {"provider": self.fallback_provider})
                    raise AIProviderError(f"Both primary and fallback providers failed")
            else:
                raise AIProviderError(f"Primary provider failed: {str(e)}")
    
    async def _generate_with_provider(
        self,
        provider: str,
        prompt: str,
        max_tokens: int,
        temperature: float,
        model: Optional[str],
        system_prompt: Optional[str]
    ) -> AIResponse:
        """Generate text with a specific provider"""
        if provider == "openai":
            return await self._generate_openai(prompt, max_tokens, temperature, model, system_prompt)
        elif provider == "gemini":
            return await self._generate_gemini(prompt, max_tokens, temperature, model, system_prompt)
        else:
            raise AIProviderError(f"Unsupported provider: {provider}")
    
    async def _generate_openai(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        model: Optional[str],
        system_prompt: Optional[str]
    ) -> AIResponse:
        """Generate text using OpenAI"""
        if not settings.openai_api_key:
            raise AIProviderError("OpenAI API key not configured")
        
        model = model or settings.openai_model or "gpt-3.5-turbo"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return AIResponse(
                content=response.choices[0].message.content,
                provider="openai",
                model=model,
                tokens_used=response.usage.total_tokens if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
        except Exception as e:
            raise AIProviderError(f"OpenAI error: {str(e)}")
    
    async def _generate_gemini(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        model: Optional[str],
        system_prompt: Optional[str]
    ) -> AIResponse:
        """Generate text using Google Gemini"""
        if not settings.gemini_api_key:
            raise AIProviderError("Gemini API key not configured")
        
        model_name = model or settings.gemini_model or "gemini-1.5-flash"
        
        try:
            model = genai.GenerativeModel(model_name)
            
            # Combine system prompt and user prompt for Gemini
            full_prompt = prompt
            if system_prompt:
                full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = await asyncio.to_thread(
                model.generate_content,
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=max_tokens,
                    temperature=temperature
                )
            )
            
            return AIResponse(
                content=response.text,
                provider="gemini",
                model=model_name,
                tokens_used=None,  # Gemini doesn't provide token count in this simple usage
                finish_reason=None
            )
        except Exception as e:
            raise AIProviderError(f"Gemini error: {str(e)}")
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers based on API keys"""
        providers = []
        if settings.openai_api_key:
            providers.append("openai")
        if settings.gemini_api_key:
            providers.append("gemini")
        return providers