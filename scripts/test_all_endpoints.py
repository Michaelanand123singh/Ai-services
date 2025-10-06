"""
Comprehensive AI Services endpoint test

- Loads base URL and API key from environment (.env in AI-services/ if present)
- Exercises all public endpoints with minimal valid payloads
- Summarizes pass/fail with HTTP status, brief error details

Env vars:
  AI_SERVICE_URL       (default: http://localhost:8001)
  AI_SERVICE_API_KEY   (optional)
  GEMINI_MODEL         (default: gemini-pro)

Usage:
  python scripts/test_all_endpoints.py
"""
from __future__ import annotations

import os
import sys
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import requests
from dotenv import load_dotenv


@dataclass
class TestResult:
    name: str
    method: str
    url: str
    status: Optional[int]
    ok: bool
    note: str = ""


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    val = os.getenv(name)
    return val if val is not None else default


def load_env() -> Tuple[str, Dict[str, str], str]:
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(dotenv_path=str(env_path), override=False)
    base_url = get_env("AI_SERVICE_URL", "http://localhost:8001").rstrip("/")
    api_key = get_env("AI_SERVICE_API_KEY", "")
    gemini_model = get_env("GEMINI_MODEL", "gemini-pro")
    headers = {"x-api-key": api_key} if api_key else {}
    return base_url, headers, gemini_model


def req(method: str, url: str, headers: Dict[str, str], timeout: int = 30, **kwargs) -> requests.Response:
    return requests.request(method=method, url=url, headers=headers, timeout=timeout, **kwargs)


def safe_json_text(resp: requests.Response, max_len: int = 240) -> str:
    try:
        return json.dumps(resp.json())[:max_len]
    except Exception:
        return resp.text[:max_len]


def run_tests() -> int:
    base_url, headers, gemini_model = load_env()
    results: List[TestResult] = []

    def run(name: str, method: str, path: str, **kwargs) -> None:
        url = f"{base_url}{path}"
        try:
            r = req(method, url, headers, **kwargs)
            ok = r.ok
            note = safe_json_text(r)
            results.append(TestResult(name, method, url, r.status_code, ok, note))
        except Exception as e:
            results.append(TestResult(name, method, url, None, False, f"ERROR: {e}"))

    # Health suite
    run("health_root", "GET", "/health/")
    run("health_detailed", "GET", "/health/detailed")
    run("health_ready", "GET", "/health/ready")
    run("health_live", "GET", "/health/live")

    # AI Providers suite
    run("providers_status", "GET", "/ai/providers/status")
    run("providers_models", "GET", "/ai/providers/models")
    run("providers_health", "GET", "/ai/providers/health")
    run("providers_usage", "GET", "/ai/providers/usage-stats")
    run("providers_test_gemini", "POST", "/ai/providers/test", json={
        "provider": "gemini", "model": gemini_model, "test_prompt": "Ping"
    })

    # Suggestions suite (minimal payload; expect 200 or 503 if disabled)
    suggestions_payload = {
        "user_id": "u_demo",
        "content_type": "post",
        "platform": "instagram",
        "content": "Launching our new product today!",
        "target_audience": "tech enthusiasts",
        "goals": ["engagement"],
        "tone": "friendly",
        "include_hashtags": True,
        "include_captions": True,
        "include_posting_times": True,
        "include_content_ideas": True,
        "max_suggestions": 5,
    }
    run("suggestions_full", "POST", "/ai/suggestions", json=suggestions_payload)
    run("suggestions_hashtags", "POST", "/ai/suggestions/hashtags", json=suggestions_payload)
    run("suggestions_captions", "POST", "/ai/suggestions/captions", json=suggestions_payload)
    run("suggestions_posting_times", "POST", "/ai/suggestions/posting-times", json=suggestions_payload)
    run("suggestions_content_ideas", "POST", "/ai/suggestions/content-ideas", json=suggestions_payload)

    # Predictions suite
    content_pred_payload = {
        "user_id": "u_demo",
        "content_type": "reel",
        "platform": "instagram",
        "content_description": "30-sec teaser video for launch",
        "hashtags": ["#launch", "#tech"],
        "caption": "Big day!",
        "posting_time": "2025-10-01T10:00:00Z",
        "target_audience": "tech enthusiasts",
        "campaign_goals": ["engagement", "reach"],
        "budget": 1000,
        "creator_profile": {"followers": 50000, "avg_engagement": 0.04},
    }
    run("pred_content", "POST", "/ai/predictions/content", json=content_pred_payload)

    campaign_pred_payload = {
        "user_id": "u_demo",
        "campaign_id": "c_demo",
        "campaign_type": "product_launch",
        "platforms": ["instagram", "youtube"],
        "budget": 50000,
        "duration_days": 30,
        "target_audience": {"age": "18-35", "interests": ["tech", "gadgets"]},
        "content_strategy": {"mix": ["reels", "shorts", "posts"]},
        "creator_requirements": {"min_followers": 10000},
    }
    run("pred_campaign", "POST", "/ai/predictions/campaign", json=campaign_pred_payload)

    creator_pred_payload = {
        "creator_id": "cr_demo",
        "brand_id": "b_demo",
        "campaign_type": "collab",
        "platform": "instagram",
        "content_type": "reel",
        "budget": 2000,
        "target_audience": {"region": "IN"},
    }
    run("pred_creator", "POST", "/ai/predictions/creator", json=creator_pred_payload)
    run("pred_history", "GET", "/ai/predictions/historical-performance/u_demo?days=30")

    # Trends suite
    trends_payload = {
        "user_id": "u_demo",
        "platforms": ["instagram", "twitter"],
        "categories": ["tech"],
        "hashtags": ["#launch"],
        "time_period_days": 7,
        "analysis_type": "comprehensive",
        "include_competitor_trends": True,
        "include_audience_trends": True,
        "include_content_trends": True,
    }
    run("trends_analyze", "POST", "/ai/trends/analyze", json=trends_payload)

    run("trends_hashtag", "POST", "/ai/trends/hashtag", json={
        "hashtag": "#launch", "platform": "instagram", "time_period_days": 7, "include_related": True
    })
    run("trends_trending_hashtags", "GET", "/ai/trends/trending-hashtags?platform=instagram&limit=10")
    run("trends_trending_content", "GET", "/ai/trends/trending-content?platform=instagram&limit=10")
    run("trends_audience_insights", "GET", "/ai/trends/audience-insights?platform=instagram&limit=10")

    # Matchmaking suite
    brand_profile = {
        "brand_id": "b_demo",
        "name": "Demo Brand",
        "industry": "tech",
        "target_audience": ["tech enthusiasts"],
        "content_preferences": ["reels", "shorts"],
        "budget_range": "1000-5000",
        "campaign_goals": ["reach", "engagement"],
        "brand_values": ["innovation"],
        "preferred_content_types": ["video"],
        "social_media_presence": {"instagram": 100000},
    }
    match_req = {
        "brand_profile": brand_profile,
        "creator_criteria": {"min_followers": 10000},
        "max_matches": 5,
        "min_compatibility_score": 0.5,
        "platforms": ["instagram"],
        "budget_constraints": {"max_per_creator": 3000},
    }
    run("match_brand_creator", "POST", "/ai/matchmaking/brand-creator", json=match_req)
    run("match_compatibility", "GET", "/ai/matchmaking/compatibility/b_demo/cr_demo")
    run("match_trending_creators", "GET", "/ai/matchmaking/trending-creators?platform=instagram&limit=10")

    # Competitor analysis suite (stateless analysis-only)
    competitor_payload = {
        "user_id": "u_demo",
        "campaign_id": "c_demo",
        "competitors_data": [
            {
                "platform": "instagram",
                "username": "comp_one",
                "profile_url": "https://instagram.com/comp_one",
                "profile_metrics": {"followers": 120000, "following": 120, "posts": 400},
                "content_analysis": {"themes": ["tech"], "frequency": "daily"},
                "engagement_metrics": {"rate": 0.045},
                "recent_posts": [{"id": "p1", "likes": 1200, "comments": 50}],
                "data_quality": {"fresh": True},
            }
        ],
        "analysis_type": "comprehensive",
        "analysis_options": {"include_swot": True},
        "collected_at": "2025-10-01T00:00:00Z",
    }
    run("competitor_analyze", "POST", "/ai/competitor-analysis/", json=competitor_payload)

    # Summarize
    passed = sum(1 for r in results if r.ok)
    total = len(results)

    print("\n=== AI Services Endpoint Test Summary ===")
    print(f"Base URL: {base_url}")
    print(f"Total: {total} | Passed: {passed} | Failed: {total - passed}")

    if total - passed:
        print("\nFailures:")
        for r in results:
            if not r.ok:
                print(f"- {r.name} {r.method} {r.url} -> status={r.status} note={r.note}")

    # Return non-zero if any failed
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(run_tests())
