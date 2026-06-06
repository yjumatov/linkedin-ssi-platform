"""AI recommendation engine with OpenAI and Claude adapters."""
from __future__ import annotations

import json
from datetime import date
from typing import Optional

from app.core.config import settings
from app.core.logging import get_logger
from app.db.models.ssi_snapshot import SSISnapshot
from app.schemas.analytics import AnalyticsResponse

logger = get_logger(__name__)

_SYSTEM_PROMPT = """\
You are an expert LinkedIn Social Selling Index (SSI) coach and analyst.
Your role is to analyze SSI score history and trends, identify root causes of score changes,
and provide specific, actionable recommendations to improve LinkedIn sales effectiveness.

SSI is scored out of 100, split across four equal components (each max 25):
1. Establish Your Professional Brand — profile completeness, thought leadership, content sharing
2. Find the Right People — search usage, profile views of decision-makers, InMail usage
3. Engage with Insights — content engagement, sharing relevant articles, commenting
4. Build Relationships — connection requests, relationship strength, network growth

Respond ONLY with valid JSON matching the schema provided.
"""

_RECOMMENDATION_SCHEMA = """\
{
  "recommendations": [
    {
      "category": "overall | professional_brand | find_right_people | engage_insights | build_relationships",
      "priority": "high | medium | low",
      "title": "Short actionable title (max 80 chars)",
      "root_cause": "Why is this score low or declining? (2-3 sentences)",
      "recommendation": "What specific actions should be taken? (3-5 sentences)",
      "expected_impact": "What improvement can be expected and in what timeframe? (1-2 sentences)",
      "action_steps": ["step 1", "step 2", "step 3"]
    }
  ]
}
"""


def _build_user_prompt(
    analytics: AnalyticsResponse,
    recent_snapshots: list[SSISnapshot],
) -> str:
    # Build history table
    history_rows = []
    for s in recent_snapshots[-14:]:  # Last 14 days max
        history_rows.append(
            f"  {s.snapshot_date} | Total: {s.total_score:.0f} | "
            f"Brand: {s.professional_brand_score:.0f} | "
            f"People: {s.find_right_people_score:.0f} | "
            f"Insights: {s.engage_with_insights_score:.0f} | "
            f"Relationships: {s.build_relationships_score:.0f}"
        )
    history_str = "\n".join(history_rows) if history_rows else "  No historical data available"

    # Build analytics summary
    def fmt_component(name: str, label: str, comp) -> str:
        delta_7d = f"{comp.delta_7d:+.1f}" if comp.delta_7d is not None else "N/A"
        delta_30d = f"{comp.delta_30d:+.1f}" if comp.delta_30d is not None else "N/A"
        return (
            f"  {label}: {comp.current:.1f}/25 | "
            f"7d: {delta_7d} | 30d: {delta_30d} | "
            f"Trend: {comp.trend} | Velocity: {comp.velocity or 'N/A'} pts/week"
        )

    components_str = "\n".join([
        fmt_component("total", "Overall SSI (max 100)", analytics.total),
        fmt_component("professional_brand", "Professional Brand (max 25)", analytics.professional_brand),
        fmt_component("find_right_people", "Find Right People (max 25)", analytics.find_right_people),
        fmt_component("engage_with_insights", "Engage with Insights (max 25)", analytics.engage_with_insights),
        fmt_component("build_relationships", "Build Relationships (max 25)", analytics.build_relationships),
    ])

    weakest_label = {
        "professional_brand": "Professional Brand",
        "find_right_people": "Find the Right People",
        "engage_with_insights": "Engage with Insights",
        "build_relationships": "Build Relationships",
    }.get(analytics.weakest_component or "", "N/A")

    industry_line = (
        f"  Industry average: {analytics.industry_avg:.1f}" if analytics.industry_avg else ""
    )
    network_line = (
        f"  Network average: {analytics.network_avg:.1f}" if analytics.network_avg else ""
    )

    return f"""\
Analyze this LinkedIn SSI profile and provide recommendations.

## Current Scores & Trends
{components_str}

## Benchmarks
{industry_line or "  Industry average: not available"}
{network_line or "  Network average: not available"}

## Score History (last 14 days)
{history_str}

## Context
- Data points available: {analytics.data_points}
- Weakest component: {weakest_label}
- Strongest component: {analytics.strongest_component or "N/A"}
- System insights: {"; ".join(analytics.insights[:3])}

## Task
Generate 5-7 specific, actionable recommendations.
- Include at least 1 "high" priority recommendation targeting the weakest component
- Include overall strategy and quick wins
- Be specific — name LinkedIn features, actions, and frequencies
- Base root causes on actual score data and trends

Respond using this exact JSON schema:
{_RECOMMENDATION_SCHEMA}
"""


async def _call_openai(prompt: str) -> str:
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model=settings.OPENAI_MODEL,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        response_format={"type": "json_object"},
        temperature=0.4,
        max_tokens=3000,
    )
    return response.choices[0].message.content


async def _call_claude(prompt: str) -> str:
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = await client.messages.create(
        model=settings.ANTHROPIC_MODEL,
        max_tokens=3000,
        system=_SYSTEM_PROMPT + "\nYou must respond with valid JSON only.",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
    )
    return message.content[0].text


def _parse_recommendations(raw_json: str, provider: str, model: str) -> list[dict]:
    """Parse raw JSON response into recommendation dicts."""
    try:
        data = json.loads(raw_json)
        items = data.get("recommendations", [])
        parsed = []
        for item in items:
            parsed.append(
                {
                    "category": item.get("category", "overall"),
                    "priority": item.get("priority", "medium"),
                    "title": item.get("title", "Recommendation")[:255],
                    "root_cause": item.get("root_cause", ""),
                    "recommendation": item.get("recommendation", ""),
                    "expected_impact": item.get("expected_impact", ""),
                    "action_steps": json.dumps(item.get("action_steps", [])),
                    "ai_provider": provider,
                    "ai_model": model,
                }
            )
        return parsed
    except json.JSONDecodeError as exc:
        logger.error("recommendation_parse_failed", error=str(exc), raw=raw_json[:500])
        return []


async def generate_recommendations(
    analytics: AnalyticsResponse,
    recent_snapshots: list[SSISnapshot],
    provider: Optional[str] = None,
) -> list[dict]:
    """
    Call the configured AI provider and return parsed recommendation dicts.
    Each dict corresponds to a Recommendation model row.
    """
    used_provider = provider or settings.AI_PROVIDER
    prompt = _build_user_prompt(analytics, recent_snapshots)

    logger.info("generating_recommendations", provider=used_provider)

    try:
        if used_provider == "claude":
            raw = await _call_claude(prompt)
            model = settings.ANTHROPIC_MODEL
        else:
            raw = await _call_openai(prompt)
            model = settings.OPENAI_MODEL

        recs = _parse_recommendations(raw, used_provider, model)
        logger.info("recommendations_generated", count=len(recs))
        return recs

    except Exception as exc:
        logger.error("recommendation_generation_failed", provider=used_provider, error=str(exc))
        raise
