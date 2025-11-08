"""
Test RAG service directly
"""
import sys
import os
sys.path.append('src')

from src.services.rag_service import RAGService
import asyncio

async def test_rag_service():
    print("🧪 Testing RAG Service...")
    
    try:
        # Initialize the service
        rag_service = RAGService()
        print("✅ RAGService initialized")
        
        # Test rewrite content
        response = await rag_service.rewrite_content(
            field="title",
            current_content="Test post",
            platform="instagram",
            content_type="post",
            tone="professional",
            goals=[],
            max_length=2200,
            user_id="test_user"
        )
        
        print(f"✅ RAG rewrite response: {response}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_rag_service())

