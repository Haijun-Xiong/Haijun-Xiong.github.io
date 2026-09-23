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

SERPAPI_KEY = os.environ["SERPAPI_KEY"]

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
    """Fetch Google Scholar author profile from SerpAPI."""

    response = requests.get(
        API_URL,
        params={
            "engine": "google_scholar_author",
            "author_id": AUTHOR_ID,
            "hl": "en",
            "api_key": SERPAPI_KEY,
        },
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if "error" in data:
        raise RuntimeError(data["error"])

    return data



def normalize_number(value):
    """Convert SerpAPI number formats to int."""

    if value is None:
        return None

    if isinstance(value, dict):
        value = (
            value.get("all")
            or value.get("total")
            or value.get("since_2021")
        )

    try:
        return int(
            str(value)
            .replace(",", "")
        )
    except Exception:
        return None



def find_values(obj, result=None):
    """
    Recursively search possible citation fields.
    """

    if result is None:
        result = {
            "citations": None,
            "hindex": None,
        }


    if isinstance(obj, dict):

        for key, value in obj.items():

            key_lower = key.lower()


            if key_lower in [
                "citations",
                "cited_by",
                "citation_count",
            ]:

                number = normalize_number(value)

                if number is not None:
                    result["citations"] = number



            if key_lower in [
                "h_index",
                "h-index",
                "hindex",
            ]:

                number = normalize_number(value)

                if number is not None:
                    result["hindex"] = number



            find_values(
                value,
                result,
            )


    elif isinstance(obj, list):

        for item in obj:
            find_values(
                item,
                result,
            )


    return result



def parse(data: dict):

    values = find_values(data)

    citations = values["citations"]
    hindex = values["hindex"]


    if citations is None or hindex is None:

        raise ValueError(
            "Citation data not found"
        )


    years = {}

    graph = (
        data
        .get("cited_by", {})
        .get("graph", [])
    )


    for item in graph:

        year = item.get("year")
        count = item.get("citations")

        if year and count is not None:
            years[str(year)] = int(count)


    return (
        citations,
        hindex,
        years,
    )



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

        data = fetch()

        citations, hindex, years = parse(
            data
        )


    except Exception as error:

        print(
            f"Fetch failed; keeping existing data: {error}"
        )

        return 0



    old_citations = old.get(
        "citations",
        0
    )

    old_hindex = old.get(
        "hindex",
        0
    )


    # 防止异常数据覆盖
    if (
        citations < old_citations
        or hindex < old_hindex
    ):

        print(
            "New values are smaller; keeping old data."
        )

        return 0



    result = {
        "citations": citations,
        "hindex": hindex,
        "updated": dt.date.today().isoformat(),
        "profile": PROFILE_URL,
        "years": years or old.get(
            "years",
            {}
        ),
    }


    if result != old:

        save(result)

        print(
            f"Updated: citations={citations}, "
            f"h-index={hindex}"
        )

    else:

        print(
            f"No change: citations={citations}, "
            f"h-index={hindex}"
        )


    return 0



if __name__ == "__main__":
    raise SystemExit(main())
