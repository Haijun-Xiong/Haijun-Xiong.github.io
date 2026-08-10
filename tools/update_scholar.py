#!/usr/bin/env python3
"""Update data/scholar.json from a public Google Scholar profile."""

from __future__ import annotations

import datetime as dt
import json
import re
import urllib.request
from pathlib import Path


SCHOLAR_USER_ID = "GDTyz2kAAAAJ"
PROFILE_URL = (
    "https://scholar.google.com/citations?hl=en&user=" + SCHOLAR_USER_ID
)
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "scholar.json"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/126.0.0.0 Safari/537.36"
)


def fetch_profile() -> str:
    request = urllib.request.Request(
        PROFILE_URL,
        headers={
            "Accept-Language": "en-US,en;q=0.9",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", "ignore")


def parse_stats(html: str) -> tuple[int, int]:
    values = re.findall(
        r'class=["\']gsc_rsb_std["\'][^>]*>\s*([\d,]+)\s*<',
        html,
    )
    if len(values) < 3:
        raise ValueError("Google Scholar statistics table was not found")

    citations = int(values[0].replace(",", ""))
    hindex = int(values[2].replace(",", ""))
    return citations, hindex


def parse_yearly_citations(html: str) -> dict[str, int]:
    """Extract the citation graph as ``{year: citation_count}``."""
    years = re.findall(
        r'class=["\']gsc_g_t["\'][^>]*>\s*(\d{4})\s*<',
        html,
    )
    citations = re.findall(
        r'class=["\']gsc_g_al["\'][^>]*>\s*([\d,]+)\s*<',
        html,
    )

    if not years or len(years) != len(citations):
        return {}

    return {
        year: int(count.replace(",", ""))
        for year, count in zip(years, citations)
    }


def load_existing() -> dict:
    try:
        return json.loads(OUTPUT_PATH.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def write_json(data: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = OUTPUT_PATH.with_suffix(".json.tmp")
    temporary_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary_path.replace(OUTPUT_PATH)


def main() -> int:
    existing = load_existing()

    try:
        profile_html = fetch_profile()
        citations, hindex = parse_stats(profile_html)
        yearly_citations = parse_yearly_citations(profile_html)
    except Exception as error:
        print(f"Fetch failed; keeping existing data: {error}")
        return 0

    old_citations = int(existing.get("citations", 0))
    old_hindex = int(existing.get("hindex", 0))

    # A lower value usually means Google returned an incomplete or blocked page.
    if citations < old_citations or hindex < old_hindex:
        print(
            "Fetched values are lower than the existing values; "
            "keeping existing data."
        )
        return 0

    if not yearly_citations:
        yearly_citations = existing.get("years", {})

    data_changed = not (
        citations == old_citations
        and hindex == old_hindex
        and yearly_citations == existing.get("years", {})
        and existing.get("updated")
    )
    updated_date = (
        dt.date.today().isoformat()
        if data_changed
        else str(existing["updated"])
    )

    if data_changed:
        write_json(
            {
                "citations": citations,
                "hindex": hindex,
                "updated": updated_date,
                "profile": PROFILE_URL,
                "years": yearly_citations,
            }
        )

    if data_changed:
        print(f"Updated: citations={citations}, h-index={hindex}")
    else:
        print(f"No statistics changed: citations={citations}, h-index={hindex}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
