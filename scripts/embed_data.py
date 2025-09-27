#!/usr/bin/env python3
"""
Script to preprocess and embed competitor data for vector search
"""
import asyncio
import argparse
import json
import time
from pathlib import Path
from typing import List, Dict, Any

from src.core.config import settings
from src.core.logger import setup_logging, ai_logger
from src.models.embedding_model import EmbeddingModel
from src.models.vector_store import get_vector_store
from src.services.competitor_service import CompetitorAnalysisService


async def embed_competitor_data(
    competitors: List[str],
    platforms: List[str],
    output_file: str = "embedded_data.json"
):
    """Embed competitor data for vector search"""
    try:
        ai_logger.logger.info("Starting data embedding process", 
                            competitors=competitors, 
                            platforms=platforms)
        
        # Initialize services
        embedding_model = EmbeddingModel()
        vector_store = get_vector_store()
        competitor_service = CompetitorAnalysisService()
        
        # Collect competitor data
        ai_logger.logger.info("Collecting competitor data...")
        competitor_data = await competitor_service.analyze_competitors(
            user_id="system",
            campaign_id=None,
            competitors=competitors,
            platforms=platforms,
            analysis_type="comprehensive",
            include_content_analysis=True,
            include_engagement_analysis=True,
            include_audience_analysis=True,
            time_period_days=30,
            max_posts_per_competitor=100
        )
        
        # Process and embed data
        embedded_documents = []
        document_id = 0
        
        for competitor, data in competitor_data.get("competitors", {}).items():
            if "error" in data:
                continue
                
            for platform, platform_data in data.get("platforms", {}).items():
                if "error" in platform_data:
                    continue
                
                # Extract text content for embedding
                text_content = []
                
                # Add profile information
                profile = platform_data.get("profile", {})
                if profile.get("bio"):
                    text_content.append(f"Bio: {profile['bio']}")
                
                # Add post content
                posts = platform_data.get("posts", [])
                for post in posts[:10]:  # Limit to first 10 posts
                    if post.get("caption"):
                        text_content.append(f"Post: {post['caption']}")
                
                # Create document for embedding
                if text_content:
                    document_text = " ".join(text_content)
                    
                    # Generate embedding
                    embedding_result = await embedding_model.embed_text(document_text)
                    
                    # Create document metadata
                    document_metadata = {
                        "competitor": competitor,
                        "platform": platform,
                        "followers": profile.get("followers", 0),
                        "engagement_rate": profile.get("engagement_rate", 0),
                        "posts_count": len(posts),
                        "document_type": "competitor_profile",
                        "created_at": time.time()
                    }
                    
                    embedded_documents.append({
                        "id": f"comp_{document_id}",
                        "text": document_text,
                        "embedding": embedding_result["embedding"],
                        "metadata": document_metadata
                    })
                    
                    document_id += 1
        
        # Store embeddings in vector database
        if embedded_documents:
            ai_logger.logger.info(f"Storing {len(embedded_documents)} embedded documents...")
            
            vectors = [doc["embedding"] for doc in embedded_documents]
            metadata = [doc["metadata"] for doc in embedded_documents]
            ids = [doc["id"] for doc in embedded_documents]
            
            await vector_store.add_vectors(vectors, metadata, ids)
            
            ai_logger.logger.info("Successfully stored embeddings in vector database")
        
        # Save embedded data to file
        output_data = {
            "embedded_documents": embedded_documents,
            "total_documents": len(embedded_documents),
            "competitors": competitors,
            "platforms": platforms,
            "created_at": time.time()
        }
        
        with open(output_file, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        ai_logger.logger.info(f"Embedded data saved to {output_file}")
        
        return output_data
        
    except Exception as e:
        ai_logger.log_error(e, {"operation": "embed_competitor_data"})
        raise


async def search_similar_content(
    query: str,
    top_k: int = 5
):
    """Search for similar content using vector similarity"""
    try:
        ai_logger.logger.info("Searching for similar content", query=query)
        
        # Initialize services
        embedding_model = EmbeddingModel()
        vector_store = get_vector_store()
        
        # Generate query embedding
        query_embedding = await embedding_model.embed_text(query)
        
        # Search for similar content
        results = await vector_store.search_vectors(
            query_vector=query_embedding["embedding"],
            top_k=top_k
        )
        
        ai_logger.logger.info(f"Found {len(results)} similar documents")
        
        # Display results
        for i, result in enumerate(results, 1):
            print(f"\n{i}. Similarity Score: {result['score']:.3f}")
            print(f"   Competitor: {result['metadata'].get('competitor', 'Unknown')}")
            print(f"   Platform: {result['metadata'].get('platform', 'Unknown')}")
            print(f"   Followers: {result['metadata'].get('followers', 0):,}")
            print(f"   Engagement Rate: {result['metadata'].get('engagement_rate', 0):.2f}%")
        
        return results
        
    except Exception as e:
        ai_logger.log_error(e, {"operation": "search_similar_content"})
        raise


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Embed competitor data for vector search")
    parser.add_argument("--competitors", nargs="+", required=True, help="List of competitor usernames")
    parser.add_argument("--platforms", nargs="+", required=True, help="List of platforms to analyze")
    parser.add_argument("--output", default="embedded_data.json", help="Output file for embedded data")
    parser.add_argument("--search", help="Search query for similar content")
    parser.add_argument("--top-k", type=int, default=5, help="Number of similar results to return")
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging()
    
    if args.search:
        # Search mode
        await search_similar_content(args.search, args.top_k)
    else:
        # Embed mode
        await embed_competitor_data(args.competitors, args.platforms, args.output)


if __name__ == "__main__":
    asyncio.run(main())
