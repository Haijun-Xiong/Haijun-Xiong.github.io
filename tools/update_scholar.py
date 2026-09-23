#!/usr/bin/env python3
"""Update data/scholar.json through the SerpAPI Scholar Author API."""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


AUTHOR_ID = "GDTyz2kAAAAJ"
API_URL = "https://serpapi.com/search.json"
OUTPUT = Path(__file__).resolve().parents[1] / "data" / "scholar.json"
PROFILE_URL = f"https://scholar.google.com/citations?hl=en&user={AUTHOR_ID}"
BEIJING_TIME = dt.timezone(dt.timedelta(hours=8))


def number(value, field: str) -> int:
    """Convert a SerpAPI numeric value to a non-negative integer."""

    if isinstance(value, dict):
        value = value.get("all")
    if value is None or isinstance(value, bool):
        raise RuntimeError(f"invalid {field}")

    try:
        result = int(str(value).replace(",", "").strip())
    except ValueError as error:
        raise RuntimeError(f"invalid {field}") from error
    if result < 0:
        raise RuntimeError(f"invalid {field}")
    return result


def fetch(api_key: str) -> dict:
    params = urllib.parse.urlencode(
        {
            "engine": "google_scholar_author",
            "author_id": AUTHOR_ID,
            "hl": "en",
            "api_key": api_key,
        }
    )
    request = urllib.request.Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": "ScholarStatsUpdater/1.0"},
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read()
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"SerpAPI returned HTTP {error.code}") from None
    except (urllib.error.URLError, TimeoutError, OSError) as error:
        # Do not print the exception: it may contain the URL and API key.
        raise RuntimeError(
            f"SerpAPI request failed ({error.__class__.__name__})"
        ) from None

    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("SerpAPI returned invalid JSON") from error
    if not isinstance(data, dict):
        raise RuntimeError("SerpAPI returned invalid data")
    if data.get("error"):
        raise RuntimeError("SerpAPI returned an API error")
    return data


def parse(data: dict) -> tuple[int, int, dict[str, int]]:
    cited_by = data.get("cited_by")
    if not isinstance(cited_by, dict):
        raise RuntimeError("cited_by data is missing")

    citations = None
    hindex = None
    table = cited_by.get("table", [])
    if not isinstance(table, list):
        raise RuntimeError("citation table is invalid")

    for row in table:
        if not isinstance(row, dict):
            continue
        if "citations" in row:
            citations = number(row["citations"], "citations")
        elif "h_index" in row:
            hindex = number(row["h_index"], "h-index")

    if citations is None or hindex is None:
        raise RuntimeError("citation statistics are missing")
    if hindex > citations:
        raise RuntimeError("h-index is greater than total citations")

    graph = cited_by.get("graph", [])
    if not isinstance(graph, list):
        raise RuntimeError("citation graph is invalid")

    years = {}
    for row in graph:
        if not isinstance(row, dict):
            raise RuntimeError("citation graph entry is invalid")
        year = number(row.get("year"), "citation year")
        count = number(row.get("citations"), "yearly citations")
        if not 1900 <= year <= 3000:
            raise RuntimeError("citation year is invalid")
        years[str(year)] = count

    return citations, hindex, dict(sorted(years.items()))


def load_existing() -> dict:
    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as error:
        raise RuntimeError("existing scholar.json is invalid") from error
    except OSError as error:
        raise RuntimeError("cannot read existing scholar.json") from error

    if not isinstance(data, dict):
        raise RuntimeError("existing scholar.json is invalid")
    return data


def save(data: dict) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".json.tmp")
    try:
        temporary.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, OUTPUT)
    finally:
        temporary.unlink(missing_ok=True)


def main() -> int:
    api_key = os.environ.get("SERPAPI_KEY", "").strip()
    if not api_key:
        print("Error: SERPAPI_KEY is not set", file=sys.stderr)
        return 1

    try:
        old = load_existing()
        citations, hindex, years = parse(fetch(api_key))

        if old:
            old_citations = number(old.get("citations"), "existing citations")
            old_hindex = number(old.get("hindex"), "existing h-index")
            if citations < old_citations or hindex < old_hindex:
                raise RuntimeError(
                    "new citation statistics are lower than the existing data"
                )

        if not years:
            old_years = old.get("years", {})
            if not isinstance(old_years, dict):
                raise RuntimeError("existing citation graph is invalid")
            years = old_years

        unchanged = (
            citations == old.get("citations")
            and hindex == old.get("hindex")
            and years == old.get("years", {})
            and PROFILE_URL == old.get("profile")
        )
        if unchanged:
            print(f"No change: citations={citations}, h-index={hindex}")
            return 0

        data = {
            "citations": citations,
            "hindex": hindex,
            "updated": dt.datetime.now(BEIJING_TIME).date().isoformat(),
            "profile": PROFILE_URL,
            "years": years,
        }
        save(data)
        print(f"Updated: citations={citations}, h-index={hindex}")
        return 0
    except (OSError, RuntimeError) as error:
        print(f"Error: {error}; existing data was left unchanged", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
