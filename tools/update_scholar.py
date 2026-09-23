#!/usr/bin/env python3
"""
Update data/scholar.json using SerpAPI Google Scholar Author API.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path

import requests


AUTHOR_ID = "GDTyz2kAAAAJ"
API_KEY = os.environ["SERPAPI_KEY"]

API_URL = "https://serpapi.com/search.json"

PROFILE_URL = (
    f"https://scholar.google.com/citations?hl=en&user={AUTHOR_ID}"
)

OUTPUT = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "scholar.json"
)


def fetch() -> dict:
    r = requests.get(
        API_URL,
        params={
            "engine": "google_scholar_author",
            "author_id": AUTHOR_ID,
            "hl": "en",
            "api_key": API_KEY,
        },
        timeout=30,
    )

    r.raise_for_status()

    data = r.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return data


def number(value):
    """Parse SerpAPI number formats."""

    if isinstance(value, dict):
        value = value.get("all", 0)

    return int(
        str(value).replace(",", "")
    )


def parse(data: dict):

    citations = None
    hindex = None

    for item in data.get("cited_by", {}).get("table", []):

        title = item.get(
            "title",
            ""
        ).lower()

        value = item.get(
            "citations"
        )

        if "citation" in title:
            citations = number(value)

        elif "h-index" in title:
            hindex = number(value)


    # fallback
    author = data.get("author", {})

    citations = citations or author.get(
        "cited_by"
    )

    hindex = hindex or author.get(
        "h_index"
    )


    if citations is None or hindex is None:
        raise ValueError(
            "Citation data not found"
        )


    years = {}

    for item in data.get("cited_by", {}).get("graph", []):

        if "year" in item:
            years[str(item["year"])] = item["citations"]


    return int(citations), int(hindex), years



def load():

    try:
        return json.loads(
            OUTPUT.read_text(
                encoding="utf-8"
            )
        )

    except Exception:
        return {}



def save(data):

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )



def main():

    old = load()

    try:
        result = fetch()
        citations, hindex, years = parse(result)

    except Exception as e:
        print(
            f"Fetch failed; keeping existing data: {e}"
        )
        return 0


    # 防止异常下降
    if (
        citations < old.get("citations", 0)
        or hindex < old.get("hindex", 0)
    ):
        print(
            "New values are smaller; keeping old data."
        )
        return 0


    data = {
        "citations": citations,
        "hindex": hindex,
        "updated": dt.date.today().isoformat(),
        "profile": PROFILE_URL,
        "years": years or old.get("years", {}),
    }


    if data != old:
        save(data)
        print(
            f"Updated: citations={citations}, h-index={hindex}"
        )

    else:
        print(
            f"No change: citations={citations}, h-index={hindex}"
        )


    return 0



if __name__ == "__main__":
    raise SystemExit(main())
