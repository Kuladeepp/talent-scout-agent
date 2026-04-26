"""Stage 1: ingest JD text or URL -> JDStruct."""
from __future__ import annotations

import json

import httpx

from app.cache import disk_cache
from app.config import settings
from app.gemini_client import generate_json
from app.models import JDStruct

JD_SCHEMA = {
    "type": "object",
    "properties": {
        "role": {"type": "string"},
        "skills_required": {"type": "array", "items": {"type": "string"}},
        "skills_nice": {"type": "array", "items": {"type": "string"}},
        "experience_min": {"type": "integer"},
        "experience_max": {"type": "integer"},
        "location": {"type": "string"},
        "must_haves": {"type": "array", "items": {"type": "string"}},
        "soft_skills": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "role", "skills_required", "skills_nice",
        "experience_min", "experience_max", "location",
        "must_haves", "soft_skills",
    ],
}

PARSE_SYSTEM = (
    "You parse job descriptions into structured data. "
    "Be specific about skill names (frameworks, tools). "
    "experience_min/max are integers in years; if a single number is given, "
    "use that for min and add 3 for max. If location is unstated, use 'Unspecified'."
)


async def fetch_url(url: str) -> str:
    """Use Firecrawl /scrape to convert a URL into markdown."""
    if not settings.firecrawl_api_key:
        raise RuntimeError("FIRECRAWL_API_KEY not set")
    async with httpx.AsyncClient(timeout=30) as http:
        r = await http.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {settings.firecrawl_api_key}"},
            json={"url": url, "formats": ["markdown"]},
        )
        r.raise_for_status()
        body = r.json()
        md = body.get("data", {}).get("markdown")
        if not md:
            raise RuntimeError(f"Firecrawl returned no markdown for {url}")
        return md


async def parse_jd(text: str) -> JDStruct:
    cache_key = disk_cache.key(text, "jd_parse")
    cached = disk_cache.get(cache_key)
    if cached:
        return JDStruct.model_validate(cached)

    prompt = f"Parse this job description:\n\n---\n{text}\n---"
    raw = await generate_json(
        model=settings.model_flash,
        prompt=prompt,
        schema=JD_SCHEMA,
        system=PARSE_SYSTEM,
        temperature=0.2,
    )
    jd = JDStruct.model_validate(raw)
    disk_cache.put(cache_key, jd.model_dump())
    return jd


async def ingest(*, jd_text: str | None, jd_url: str | None) -> JDStruct:
    if not jd_text and not jd_url:
        raise ValueError("Provide jd_text or jd_url")
    text = jd_text or await fetch_url(jd_url)  # type: ignore[arg-type]
    if not text.strip():
        raise ValueError("JD content is empty")
    return await parse_jd(text)
