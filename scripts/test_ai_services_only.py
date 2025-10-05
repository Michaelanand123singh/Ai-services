"""
AI Services-only deep test suite

Checks:
- Service health and provider endpoints (requires x-api-key if configured)
- Core AI endpoints exercising RAG pipelines (suggestions, predictions, trends, competitor)
- Embedding model availability and sample embedding (direct import)
- Vector DB add/search lifecycle using the configured vector store (direct import)

Usage:
  python scripts/test_ai_services_only.py --ai http://localhost:8001

Environment (optional):
  AI_SERVICE_URL, AI_SERVICE_API_KEY
"""
from __future__ import annotations

import argparse
import asyncio
import os
from typing import Any, Dict, Optional, List
from pathlib import Path

import httpx
from dotenv import load_dotenv


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    return val if val is not None else default


async def req(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> Dict[str, Any]:
    try:
        r = await client.request(method, url, timeout=30.0, **kwargs)
        try:
            data = r.json()
        except Exception:
            data = {"text": r.text[:500]}
        return {"ok": r.is_success, "status": r.status_code, "data": data}
    except Exception as e:
        return {"ok": False, "status": 0, "data": {"error": str(e)}}


def print_line(ok: bool, label: str, status: int, extra: str = "") -> None:
    icon = "✅" if ok else "❌"
    suffix = f"  {extra}" if extra else ""
    print(f"{icon} {label} [{status}]{suffix}")


async def run_http_tests(ai_base: str, ai_key: Optional[str]) -> bool:
    ok_all = True
    headers = {"x-api-key": ai_key} if ai_key else {}
    async with httpx.AsyncClient(base_url=ai_base, headers=headers, follow_redirects=True) as c:
        r = await req(c, "GET", "/health")
        print_line(r["ok"], f"AI {ai_base}/health", r["status"]) ; ok_all &= r["ok"]

        # Provider endpoints (protected)
        r = await req(c, "GET", "/ai/providers/status")
        print_line(r["ok"], "/ai/providers/status", r["status"]) ; ok_all &= r["ok"]
        r = await req(c, "GET", "/ai/providers/models")
        print_line(r["ok"], "/ai/providers/models", r["status"]) ; ok_all &= r["ok"]

        # Light model invocation if provider configured (uses Gemini by default)
        gemini_model = get_env("GEMINI_MODEL", "gemini-1.5-pro-latest")
        payload = {"provider": "gemini", "model": gemini_model, "test_prompt": "Say hello"}
        r = await req(c, "POST", "/ai/providers/test", json=payload)
        extra = ""
        if not r["ok"]:
            extra = str(r["data"])[:200]
        print_line(r["ok"], f"/ai/providers/test ({gemini_model})", r["status"], extra) ; ok_all &= r["ok"]

        # RAG-backed endpoints
        r = await req(c, "POST", "/ai/suggestions/", json={
            "user_id": "test-user",
            "campaign_id": None,
            "content_type": "post",
            "platform": "twitter",
            "content": "A short post about AI.",
            "target_audience": "tech enthusiasts",
            "goals": ["engagement"],
            "tone": "professional",
            "include_hashtags": True,
            "include_captions": True,
            "include_posting_times": True,
            "include_content_ideas": True,
            "max_suggestions": 2
        })
        extra = ""
        if not r["ok"]:
            extra = str(r["data"])[:200]
        print_line(r["ok"], "/ai/suggestions/", r["status"], extra) ; ok_all &= r["ok"]

        r = await req(c, "POST", "/ai/predictions/content", json={
            "user_id": "test-user",
            "content_type": "post",
            "platform": "twitter",
            "content_description": "A sample tweet about AI.",
            "hashtags": ["#AI"],
            "caption": "AI is awesome!",
            "posting_time": None,
            "target_audience": "techies",
            "campaign_goals": ["engagement"],
            "budget": 0,
            "creator_profile": None
        })
        extra = ""
        if not r["ok"]:
            extra = str(r["data"])[:200]
        print_line(r["ok"], "/ai/predictions/content", r["status"], extra) ; ok_all &= r["ok"]

        r = await req(c, "POST", "/ai/trends/analyze", json={
            "user_id": "test-user",
            "platforms": ["twitter"],
            "categories": ["tech"],
            "hashtags": ["#AI"],
            "time_period_days": 7,
            "analysis_type": "comprehensive",
            "include_competitor_trends": False,
            "include_audience_trends": True,
            "include_content_trends": True
        })
        extra = ""
        if not r["ok"]:
            extra = str(r["data"])[:200]
        print_line(r["ok"], "/ai/trends/analyze", r["status"], extra) ; ok_all &= r["ok"]

        r = await req(c, "POST", "/ai/competitor-analysis/", json={
            "user_id": "test-user",
            "competitors_data": [
                {
                    "platform": "twitter",
                    "username": "comp1",
                    "profile_url": "https://x.com/comp1",
                    "profile_metrics": {"followers": 1000},
                    "content_analysis": {"topics": ["ai", "ml"]},
                    "engagement_metrics": {"rate": 0.05},
                    "recent_posts": [{"id": "1", "text": "post"}],
                    "data_quality": {"fresh": True}
                }
            ],
            "analysis_type": "comprehensive",
            "collected_at": "2025-10-05T00:00:00Z"
        })
        extra = ""
        if not r["ok"]:
            extra = str(r["data"])[:200]
        print_line(r["ok"], "/ai/competitor-analysis/", r["status"], extra) ; ok_all &= r["ok"]

    return ok_all


async def run_direct_component_tests() -> bool:
    """Direct imports to validate embeddings and vector DB without HTTP."""
    ok_all = True

    # Embedding test
    try:
        # Only run if OPENAI_API_KEY is configured, otherwise skip (we may be using Gemini only)
        if get_env("OPENAI_API_KEY"):
            from src.models.embedding_model import EmbeddingModel
            emb = EmbeddingModel()
            result = await emb.embed_text("hello world")
            print_line(True, "EmbeddingModel.embed_text", 200, f"dim={result.get('dimension')}")
        else:
            print_line(True, "EmbeddingModel.embed_text (skipped - no OPENAI_API_KEY)", 200)
    except Exception as e:
        print_line(False, "EmbeddingModel.embed_text", 500, str(e))
        ok_all = False

    # Vector store test
    try:
        # Prefer FAISS locally to avoid optional Chroma dependency
        os.environ.setdefault("CHROMA_PERSIST_DIRECTORY", "")
        from src.models.vector_store import get_vector_store
        import random
        import math

        store = get_vector_store()
        # Create 3 random unit vectors matching configured VECTOR_DIMENSION
        from src.core.config import settings as _settings
        dim = int(getattr(_settings, "vector_dimension", 1536))
        vectors: List[List[float]] = []
        for _ in range(3):
            v = [random.random() for _ in range(dim)]
            norm = math.sqrt(sum(x*x for x in v)) or 1.0
            vectors.append([x / norm for x in v])

        metadata = [
            {"type": "test", "i": 0},
            {"type": "test", "i": 1},
            {"type": "test", "i": 2},
        ]
        ok_add = await store.add_vectors(vectors, metadata)
        if not ok_add:
            raise RuntimeError("add_vectors returned False")

        # Search using first vector
        results = await store.search_vectors(vectors[0], top_k=2)
        print_line(True, "VectorStore add/search", 200, f"hits={len(results)}")
    except Exception as e:
        print_line(False, "VectorStore add/search", 500, str(e))
        ok_all = False

    return ok_all


async def main() -> int:
    # Load environment from AI-services/.env if present
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=str(env_path), override=False)

    parser = argparse.ArgumentParser()
    parser.add_argument("--ai", dest="ai", default=get_env("AI_SERVICE_URL", "http://localhost:8001"))
    args = parser.parse_args()

    ai_key = get_env("AI_SERVICE_API_KEY")

    http_ok = await run_http_tests(args.ai, ai_key)
    direct_ok = await run_direct_component_tests()

    print("\nSummary:")
    print(f"HTTP Endpoints: {'OK' if http_ok else 'FAILED'}")
    print(f"Direct Components (Embeddings/Vector): {'OK' if direct_ok else 'FAILED'}")

    return 0 if (http_ok and direct_ok) else 1


if __name__ == "__main__":
    try:
        import sys
        sys.exit(asyncio.run(main()))
    except KeyboardInterrupt:
        sys.exit(130)


