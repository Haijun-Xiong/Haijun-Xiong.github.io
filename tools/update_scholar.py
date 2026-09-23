#!/usr/bin/env python3
"""
Update data/scholar.json from Google Scholar via SerpAPI.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

import requests


# =========================
# Google Scholar profile
# =========================

SCHOLAR_USER_ID = "GDTyz2kAAAAJ"

SERPAPI_KEY = os.environ["SERPAPI_KEY"]

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


# =========================
# Fetch SerpAPI
# =========================

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

    return response.json()


# =========================
# Parse statistics
# =========================

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

        title = item.get(
            "title"
        )

        value = item.get(
            "citations"
        )


        if title == "Citations":
            citations = int(value)


        elif title == "h-index":
            hindex = int(value)


    if citations is None or hindex is None:
        raise ValueError(
            "SerpAPI citation statistics not found"
        )


    return citations, hindex



# =========================
# Load existing
# =========================

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



# =========================
# Write JSON
# =========================

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



# =========================
# Main
# =========================

def main() -> int:


    existing = load_existing()


    try:

        profile = fetch_profile()

        citations, hindex = parse_stats(
            profile
        )


    except Exception as error:

        print(
            f"Fetch failed; keeping existing data: {error}"
        )

        return 0



    old_citations = int(
        existing.get(
            "citations",
            0,
        )
    )


    old_hindex = int(
        existing.get(
            "hindex",
            0,
        )
    )



    # 防止异常数据覆盖
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



    changed = not (
        citations == old_citations
        and hindex == old_hindex
        and existing.get("updated")
    )


    updated = (
        dt.date.today().isoformat()
        if changed
        else existing["updated"]
    )


    if changed:

        write_json(
            {
                "citations": citations,
                "hindex": hindex,
                "updated": updated,
                "profile": PROFILE_URL,
                "years": existing.get(
                    "years",
                    {},
                ),
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
