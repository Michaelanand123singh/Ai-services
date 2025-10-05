"""
AI Services integration smoke test

Runs a comprehensive set of checks against the AI Services and Backend to
verify endpoints, provider status, and basic model generation work.

Usage:
  python scripts/test_ai_integration.py [--ai http://localhost:8001] [--backend http://localhost:5000]

Environment (optional):
  AI_SERVICE_URL, BACKEND_URL, AI_SERVICE_API_KEY, BACKEND_API_KEY
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from typing import Any, Dict, Optional

import httpx


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
  val = os.getenv(name)
  return val if val is not None else default


async def req(client: httpx.AsyncClient, method: str, url: str, **kwargs) -> Dict[str, Any]:
  try:
    r = await client.request(method, url, timeout=30.0, **kwargs)
    data = None
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


async def test_ai_service(ai_base: str, ai_key: Optional[str]) -> bool:
  print("\n=== AI SERVICE TESTS ===")
  headers = {"x-api-key": ai_key} if ai_key else {}
  ok_all = True
  async with httpx.AsyncClient(base_url=ai_base, headers=headers, follow_redirects=True) as c:
    # Health
    r = await req(c, "GET", "/health")
    print_line(r["ok"], f"AI {ai_base}/health", r["status"]) ; ok_all &= r["ok"]

    # Providers status
    r = await req(c, "GET", "/ai/providers/status")
    print_line(r["ok"], "/ai/providers/status", r["status"])
    ok_all &= r["ok"]

    # Models list
    r = await req(c, "GET", "/ai/providers/models")
    print_line(r["ok"], "/ai/providers/models", r["status"])
    ok_all &= r["ok"]

    # Test a short generation on primary (gemini flash by default)
    payload = {"provider": "gemini", "model": "gemini-1.5-flash", "test_prompt": "Say hello"}
    r = await req(c, "POST", "/ai/providers/test", json=payload)
    print_line(r["ok"], "/ai/providers/test (gemini flash)", r["status"])
    ok_all &= r["ok"]

    # Suggestions API (basic prompt)
    sugg = await req(c, "POST", "/ai/suggestions/", json={
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
      "max_suggestions": 3
    })
    print_line(sugg["ok"], "/ai/suggestions/", sugg["status"])
    ok_all &= sugg["ok"]

    # Matchmaking API (minimal payload)
    mm = await req(c, "POST", "/ai/matchmaking/brand-creator", json={
      "brand_profile": {
        "brand_id": "brand-1",
        "name": "Test Brand",
        "industry": "tech",
        "target_audience": ["developers"],
        "content_preferences": ["short-form"],
        "budget_range": "low",
        "campaign_goals": ["engagement"],
        "brand_values": ["innovation"],
        "preferred_content_types": ["post"],
        "social_media_presence": {"twitter": "@testbrand"}
      },
      "creator_criteria": {"min_followers": 500},
      "max_matches": 2,
      "min_compatibility_score": 0.5,
      "platforms": ["twitter"],
      "budget_constraints": {"max": 1000}
    })
    print_line(mm["ok"], "/ai/matchmaking/brand-creator", mm["status"])
    ok_all &= mm["ok"]

    # Trends API (simple)
    tr = await req(c, "POST", "/ai/trends/analyze", json={
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
    print_line(tr["ok"], "/ai/trends/analyze", tr["status"])
    ok_all &= tr["ok"]

    # Predictions API (simple)
    pr = await req(c, "POST", "/ai/predictions/content", json={
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
    print_line(pr["ok"], "/ai/predictions/content", pr["status"])
    ok_all &= pr["ok"]

    # Competitor analysis (minimal synthesized payload)
    comp = await req(c, "POST", "/ai/competitor-analysis/", json={
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
    print_line(comp["ok"], "/ai/competitor-analysis", comp["status"])
    ok_all &= comp["ok"]

  return ok_all


async def test_backend_integration(backend_base: str, backend_key: Optional[str]) -> bool:
  print("\n=== BACKEND INTEGRATION TESTS ===")
  headers = {"Authorization": f"Bearer {backend_key}"} if backend_key else {}
  ok_all = True
  async with httpx.AsyncClient(base_url=backend_base, headers=headers) as c:
    # Backend health
    r = await req(c, "GET", "/api/health")
    print_line(r["ok"], f"Backend {backend_base}/api/health", r["status"]) ; ok_all &= r["ok"]

    # Backend AI endpoints should proxy to AI services (authenticated in your app)
    # Here we simply check they exist; full auth depends on your local token.
    for ep in ["/api/ai/competitor-analysis", "/api/ai/suggestions", "/api/ai/matchmaking"]:
      r = await req(c, "OPTIONS", ep)  # preflight/exists check
      print_line(r["ok"], f"{ep} (exists?)", r["status"]) ; ok_all &= r["ok"]

  return ok_all


async def main() -> int:
  parser = argparse.ArgumentParser()
  parser.add_argument("--ai", dest="ai", default=get_env("AI_SERVICE_URL", "http://localhost:8001"))
  parser.add_argument("--backend", dest="backend", default=get_env("BACKEND_URL", "http://localhost:5000"))
  args = parser.parse_args()

  ai_key = get_env("AI_SERVICE_API_KEY")
  backend_key = get_env("BACKEND_API_KEY")

  ai_ok = await test_ai_service(args.ai, ai_key)
  be_ok = await test_backend_integration(args.backend, backend_key)

  print("\nSummary:")
  print(f"AI Service: {'OK' if ai_ok else 'FAILED'}")
  print(f"Backend Integration: {'OK' if be_ok else 'FAILED'}")

  return 0 if (ai_ok and be_ok) else 1


if __name__ == "__main__":
  try:
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
  except KeyboardInterrupt:
    sys.exit(130)


