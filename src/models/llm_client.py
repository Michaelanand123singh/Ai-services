"""
Large Language Model client for AI operations
"""
from typing import List, Dict, Any, Optional
import openai
from openai import AsyncOpenAI
import time
from src.core.config import settings
from src.core.logger import ai_logger, log_ai_model_call
from src.core.exceptions import ModelNotAvailableError, AIServiceException


class LLMClient:
    """Client for interacting with Large Language Models"""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.max_tokens = settings.max_tokens
        self.temperature = settings.temperature
        self.top_p = settings.top_p
        self.frequency_penalty = settings.frequency_penalty
        self.presence_penalty = settings.presence_penalty
        self.logger = ai_logger
    
    async def generate_text(
        self,
        prompt: str,
        system_message: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate text using the LLM"""
        try:
            start_time = time.time()
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Set parameters
            params = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature,
                "top_p": self.top_p,
                "frequency_penalty": self.frequency_penalty,
                "presence_penalty": self.presence_penalty,
                **kwargs
            }
            
            # Log API call
            log_ai_model_call(self.model, "text_generation")
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract response
            content = response.choices[0].message.content
            usage = response.usage
            
            # Log successful operation
            self.logger.log_ai_operation(
                operation="text_generation",
                model=self.model,
                tokens_used=usage.total_tokens if usage else 0,
                duration_ms=processing_time,
                success=True
            )
            
            return {
                "content": content,
                "tokens_used": usage.total_tokens if usage else 0,
                "prompt_tokens": usage.prompt_tokens if usage else 0,
                "completion_tokens": usage.completion_tokens if usage else 0,
                "processing_time_ms": processing_time,
                "model": self.model
            }
            
        except openai.APIError as e:
            self.logger.log_error(e, {"operation": "generate_text", "model": self.model})
            raise ModelNotAvailableError(self.model, f"OpenAI API error: {str(e)}")
        
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_text"})
            raise AIServiceException(f"Failed to generate text: {str(e)}")
    
    async def generate_structured_output(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_message: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Generate structured output using function calling"""
        try:
            start_time = time.time()
            
            # Prepare messages
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            # Prepare function definition
            functions = [{
                "name": "generate_structured_output",
                "description": "Generate structured output based on the given schema",
                "parameters": output_schema
            }]
            
            # Set parameters
            params = {
                "model": self.model,
                "messages": messages,
                "functions": functions,
                "function_call": {"name": "generate_structured_output"},
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                **kwargs
            }
            
            # Log API call
            log_ai_model_call(self.model, "structured_output_generation")
            
            # Make API call
            response = await self.client.chat.completions.create(**params)
            
            processing_time = int((time.time() - start_time) * 1000)
            
            # Extract function call result
            function_call = response.choices[0].message.function_call
            if function_call and function_call.name == "generate_structured_output":
                import json
                result = json.loads(function_call.arguments)
            else:
                raise AIServiceException("Failed to generate structured output")
            
            usage = response.usage
            
            # Log successful operation
            self.logger.log_ai_operation(
                operation="structured_output_generation",
                model=self.model,
                tokens_used=usage.total_tokens if usage else 0,
                duration_ms=processing_time,
                success=True
            )
            
            return {
                "result": result,
                "tokens_used": usage.total_tokens if usage else 0,
                "processing_time_ms": processing_time,
                "model": self.model
            }
            
        except openai.APIError as e:
            self.logger.log_error(e, {"operation": "generate_structured_output", "model": self.model})
            raise ModelNotAvailableError(self.model, f"OpenAI API error: {str(e)}")
        
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_structured_output"})
            raise AIServiceException(f"Failed to generate structured output: {str(e)}")
    
    async def analyze_text(
        self,
        text: str,
        analysis_type: str = "general",
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze text for various insights"""
        try:
            # Build analysis prompt based on type
            if analysis_type == "sentiment":
                prompt = f"Analyze the sentiment of the following text and provide a detailed analysis:\n\n{text}"
                system_message = "You are an expert sentiment analysis AI. Provide detailed sentiment analysis including polarity, subjectivity, and emotional tone."
            
            elif analysis_type == "content_quality":
                prompt = f"Analyze the quality and effectiveness of the following social media content:\n\n{text}"
                system_message = "You are an expert social media content analyst. Evaluate content quality, engagement potential, and provide improvement suggestions."
            
            elif analysis_type == "hashtag_analysis":
                prompt = f"Analyze the hashtags in the following text and suggest improvements:\n\n{text}"
                system_message = "You are an expert social media hashtag strategist. Analyze hashtag effectiveness and suggest better alternatives."
            
            elif analysis_type == "competitor_analysis":
                prompt = f"Analyze the following competitor content and provide strategic insights:\n\n{text}"
                system_message = "You are an expert competitive intelligence analyst. Analyze competitor content and provide strategic insights."
            
            else:
                prompt = f"Analyze the following text and provide insights:\n\n{text}"
                system_message = "You are an expert text analyst. Provide comprehensive analysis and insights."
            
            # Add context if provided
            if context:
                context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
                prompt += f"\n\nContext:\n{context_str}"
            
            # Generate analysis
            result = await self.generate_text(
                prompt=prompt,
                system_message=system_message,
                max_tokens=2000
            )
            
            return {
                "analysis_type": analysis_type,
                "text": text,
                "analysis": result["content"],
                "tokens_used": result["tokens_used"],
                "processing_time_ms": result["processing_time_ms"]
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "analyze_text", "analysis_type": analysis_type})
            raise AIServiceException(f"Failed to analyze text: {str(e)}")
    
    async def generate_insights(
        self,
        data: Dict[str, Any],
        insight_type: str = "general",
        user_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate insights from structured data"""
        try:
            # Build insight generation prompt
            data_str = self._format_data_for_prompt(data)
            
            if insight_type == "competitor_insights":
                prompt = f"Based on the following competitor analysis data, generate actionable insights and recommendations:\n\n{data_str}"
                system_message = "You are an expert competitive intelligence analyst. Generate strategic insights and actionable recommendations."
            
            elif insight_type == "content_strategy":
                prompt = f"Based on the following content data, generate content strategy recommendations:\n\n{data_str}"
                system_message = "You are an expert content strategist. Generate content strategy recommendations and best practices."
            
            elif insight_type == "engagement_optimization":
                prompt = f"Based on the following engagement data, suggest optimization strategies:\n\n{data_str}"
                system_message = "You are an expert social media engagement strategist. Suggest optimization strategies."
            
            else:
                prompt = f"Based on the following data, generate insights and recommendations:\n\n{data_str}"
                system_message = "You are an expert data analyst. Generate insights and recommendations."
            
            # Add user context if provided
            if user_context:
                context_str = "\n".join([f"{k}: {v}" for k, v in user_context.items()])
                prompt += f"\n\nUser Context:\n{context_str}"
            
            # Generate insights
            result = await self.generate_text(
                prompt=prompt,
                system_message=system_message,
                max_tokens=3000
            )
            
            return {
                "insight_type": insight_type,
                "data": data,
                "insights": result["content"],
                "tokens_used": result["tokens_used"],
                "processing_time_ms": result["processing_time_ms"]
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "generate_insights", "insight_type": insight_type})
            raise AIServiceException(f"Failed to generate insights: {str(e)}")
    
    async def summarize_text(
        self,
        text: str,
        max_length: int = 200,
        focus: Optional[str] = None
    ) -> Dict[str, Any]:
        """Summarize text content"""
        try:
            # Build summarization prompt
            if focus:
                prompt = f"Summarize the following text focusing on {focus}. Keep it under {max_length} characters:\n\n{text}"
            else:
                prompt = f"Summarize the following text in under {max_length} characters:\n\n{text}"
            
            system_message = "You are an expert text summarizer. Create concise, accurate summaries that capture the key points."
            
            # Generate summary
            result = await self.generate_text(
                prompt=prompt,
                system_message=system_message,
                max_tokens=500
            )
            
            return {
                "original_text": text,
                "summary": result["content"],
                "max_length": max_length,
                "focus": focus,
                "tokens_used": result["tokens_used"],
                "processing_time_ms": result["processing_time_ms"]
            }
            
        except Exception as e:
            self.logger.log_error(e, {"operation": "summarize_text"})
            raise AIServiceException(f"Failed to summarize text: {str(e)}")
    
    def _format_data_for_prompt(self, data: Dict[str, Any]) -> str:
        """Format data dictionary for use in prompts"""
        formatted_lines = []
        
        def format_value(value, indent=0):
            if isinstance(value, dict):
                for k, v in value.items():
                    if isinstance(v, (dict, list)):
                        formatted_lines.append("  " * indent + f"{k}:")
                        format_value(v, indent + 1)
                    else:
                        formatted_lines.append("  " * indent + f"{k}: {v}")
            elif isinstance(value, list):
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        formatted_lines.append("  " * indent + f"Item {i + 1}:")
                        format_value(item, indent + 1)
                    else:
                        formatted_lines.append("  " * indent + f"- {item}")
            else:
                formatted_lines.append("  " * indent + str(value))
        
        format_value(data)
        return "\n".join(formatted_lines)
    
    async def check_model_availability(self) -> bool:
        """Check if the LLM model is available"""
        try:
            # Simple test call
            test_result = await self.generate_text(
                prompt="Test",
                max_tokens=1
            )
            return True
        except Exception:
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "frequency_penalty": self.frequency_penalty,
            "presence_penalty": self.presence_penalty,
            "available": await self.check_model_availability()
        }
