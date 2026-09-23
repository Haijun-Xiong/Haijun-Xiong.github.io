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


def fetch():
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



def num(v):
    if isinstance(v, dict):
        v = v.get("all")

    return int(
        str(v).replace(",", "")
    )



def parse(data):

    citations = None
    hindex = None

    cited = data.get(
        "cited_by",
        {}
    )


    # citation table
    for x in cited.get("table", []):

        title = x.get(
            "title",
            ""
        ).lower()

        value = x.get(
            "citations"
        )

        if value is None:
            continue


        if "citation" in title:
            citations = num(value)

        elif "h-index" in title:
            hindex = num(value)


    # fallback author
    author = data.get(
        "author",
        {}
    )

    if citations is None:
        citations = num(
            author.get("cited_by")
        )

    if hindex is None:
        hindex = num(
            author.get("h_index")
        )


    if citations is None or hindex is None:
        raise ValueError(
            "Cannot find citation statistics"
        )


    years = {}

    for x in cited.get("graph", []):

        if "year" in x:
            years[str(x["year"])] = x["citations"]


    return citations, hindex, years



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
        exist_ok=True
    )

    OUTPUT.write_text(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False
        ) + "\n",
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



    old_citations = old.get(
        "citations",
        0
    )

    old_hindex = old.get(
        "hindex",
        0
    )


    # 仅当已有数据存在时保护下降
    if old and (
        citations < old_citations
        or hindex < old_hindex
    ):

        print(
            f"New values are smaller; "
            f"old=({old_citations},{old_hindex}), "
            f"new=({citations},{hindex})"
        )

        return 0



    data = {
        "citations": citations,
        "hindex": hindex,
        "updated": dt.date.today().isoformat(),
        "profile": PROFILE_URL,
        "years": years or old.get(
            "years",
            {}
        ),
    }


    if data != old:

        save(data)

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
