#!/usr/bin/env python3
"""
Update data/scholar.json from Google Scholar via SerpAPI.

API:
https://serpapi.com/google-scholar-author-api
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

import requests


# ==================================================
# Configuration
# ==================================================

SCHOLAR_USER_ID = "GDTyz2kAAAAJ"

SERPAPI_KEY = os.environ.get("SERPAPI_KEY")

if not SERPAPI_KEY:
    raise RuntimeError(
        "SERPAPI_KEY is not set"
    )


SERPAPI_URL = (
    "https://serpapi.com/search.json"
)


PROFILE_URL = (
    "https://scholar.google.com/citations"
    "?hl=en&user="
    + SCHOLAR_USER_ID
)


OUTPUT_PATH = (
    Path(__file__)
    .resolve()
    .parents[1]
    / "data"
    / "scholar.json"
)


# ==================================================
# Fetch SerpAPI
# ==================================================

def fetch_profile() -> dict:

    params = {
        "engine": "google_scholar_author",
        "author_id": SCHOLAR_USER_ID,
        "hl": "en",
        "api_key": SERPAPI_KEY,
    }


    response = requests.get(
        SERPAPI_URL,
        params=params,
        timeout=30,
    )


    response.raise_for_status()


    data = response.json()


    if "error" in data:
        raise RuntimeError(
            data["error"]
        )


    return data



# ==================================================
# Parse citations and h-index
# ==================================================

def parse_stats(data: dict) -> tuple[int, int]:

    cited_by = data.get(
        "cited_by",
        {}
    )


    table = cited_by.get(
        "table",
        []
    )


    citations = None
    hindex = None


    for item in table:

        title = (
            item.get(
                "title",
                ""
            )
            .lower()
        )


        value = item.get(
            "citations"
        )


        if value is None:
            continue


        value = int(
            str(value)
            .replace(",", "")
        )


        if "citation" in title:
            citations = value


        elif "h-index" in title:
            hindex = value



    if citations is None or hindex is None:

        raise ValueError(
            "Cannot parse citation statistics. "
            f"cited_by={cited_by}"
        )


    return citations, hindex



# ==================================================
# Parse yearly citations
# ==================================================

def parse_yearly_citations(data: dict) -> dict[str, int]:

    cited_by = data.get(
        "cited_by",
        {}
    )


    graph = cited_by.get(
        "graph",
        []
    )


    years = {}


    for item in graph:

        year = item.get(
            "year"
        )

        citations = item.get(
            "citations"
        )


        if year and citations is not None:

            years[str(year)] = int(
                citations
            )


    return years



# ==================================================
# Load old data
# ==================================================

def load_existing() -> dict:

    try:

        return json.loads(
            OUTPUT_PATH.read_text(
                encoding="utf-8"
            )
        )


    except (
        FileNotFoundError,
        json.JSONDecodeError,
        OSError,
    ):

        return {}



# ==================================================
# Save JSON
# ==================================================

def write_json(data: dict):

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )


    tmp = OUTPUT_PATH.with_suffix(
        ".json.tmp"
    )


    tmp.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


    tmp.replace(
        OUTPUT_PATH
    )



# ==================================================
# Main
# ==================================================

def main() -> int:


    existing = load_existing()


    try:

        profile = fetch_profile()


        citations, hindex = parse_stats(
            profile
        )


        yearly_citations = (
            parse_yearly_citations(
                profile
            )
        )


    except Exception as error:

        print(
            "Fetch failed; keeping existing data: "
            f"{error}"
        )

        return 0



    old_citations = int(
        existing.get(
            "citations",
            0
        )
    )


    old_hindex = int(
        existing.get(
            "hindex",
            0
        )
    )



    # 防止异常下降覆盖
    if (
        citations < old_citations
        or hindex < old_hindex
    ):

        print(
            "Fetched values are lower "
            "than existing values; "
            "keeping existing data."
        )

        return 0



    if not yearly_citations:

        yearly_citations = existing.get(
            "years",
            {}
        )


    changed = not (
        citations == old_citations
        and hindex == old_hindex
        and yearly_citations
        == existing.get(
            "years",
            {}
        )
        and existing.get(
            "updated"
        )
    )



    updated = (
        dt.date.today().isoformat()
        if changed
        else existing.get(
            "updated"
        )
    )



    if changed:

        write_json(
            {
                "citations": citations,
                "hindex": hindex,
                "updated": updated,
                "profile": PROFILE_URL,
                "years": yearly_citations,
            }
        )


        print(
            f"Updated: citations={citations}, "
            f"h-index={hindex}"
        )


    else:

        print(
            f"No statistics changed: "
            f"citations={citations}, "
            f"h-index={hindex}"
        )


    return 0



if __name__ == "__main__":
    raise SystemExit(main())
