"""
Test Gemini directly in the AI services context
"""
import sys
import os
sys.path.append('src')

from src.models.multi_llm_client import MultiLLMClient
import asyncio

async def test_gemini():
    print("🧪 Testing Gemini in AI Services Context...")
    
    try:
        # Initialize the client
        client = MultiLLMClient()
        print("✅ MultiLLMClient initialized")
        
        # Test text generation
        response = await client.generate_text(
            prompt="Hello, this is a test message",
            max_tokens=100,
            temperature=0.7
        )
        
        print(f"✅ Gemini response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_gemini())

