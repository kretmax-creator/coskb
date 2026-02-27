from __future__ import annotations

import json
import subprocess
from pathlib import Path
from urllib.parse import urlencode

import pytest


SEARCH_API_CONTAINER = "coskb-search-api"
REFERENCE_FILENAME = "2025_Полезная информация.md"
NOISE_QUERY = "zzzzzz_nonexistent_coskb_2026_qa_signal"

SEARCH_CASES = (
    ("vpn", "Настройка подключения к VPN", ("vpn", "cvpn", "ext")),
    ("сфера", "Сфера", ("сфера", "sfera")),
    ("outlook", "Траблы Outlook", ("outlook",)),
    ("сакура", "Сакура", ("сакура", "nac")),
)


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _run_container_python(script: str) -> str:
    try:
        completed = subprocess.run(
            ["docker", "exec", SEARCH_API_CONTAINER, "python", "-c", script],
            check=False,
            capture_output=True,
            text=True,
            timeout=45,
        )
    except subprocess.TimeoutExpired as exc:
        pytest.fail(f"Timed out while executing docker command: {exc}")

    if completed.returncode != 0:
        pytest.fail(
            "docker exec failed for search-api container:\n"
            f"stdout: {completed.stdout}\n"
            f"stderr: {completed.stderr}"
        )

    output = (completed.stdout or "").strip()
    if not output:
        pytest.fail("search-api container returned empty response")
    return output


def _search_api_get(path: str, **params: object) -> dict:
    query = urlencode(params, doseq=True)
    url = f"http://localhost:8000{path}"
    if query:
        url = f"{url}?{query}"

    script = f"""
import json
import urllib.error
import urllib.request

url = {url!r}
try:
    with urllib.request.urlopen(url, timeout=20) as response:
        print(response.read().decode("utf-8"))
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    print(json.dumps({{"__http_error__": exc.code, "__body__": body}}, ensure_ascii=False))
except Exception as exc:
    print(json.dumps({{"__error__": str(exc)}}, ensure_ascii=False))
"""

    payload_raw = _run_container_python(script)
    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError as exc:
        pytest.fail(f"Invalid JSON response from search-api: {exc}\nraw: {payload_raw}")

    if "__http_error__" in payload:
        pytest.fail(
            f"GET {path} returned HTTP {payload['__http_error__']}: "
            f"{payload.get('__body__', '')}"
        )
    if "__error__" in payload:
        pytest.fail(f"GET {path} failed: {payload['__error__']}")
    return payload


def _extract_first_list(payload: dict, *keys: str) -> list:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    pytest.fail(f"Expected list in one of keys {keys}, got payload: {payload}")


def _find_section_by_marker(sections: list[str], marker: str) -> str:
    marker_lower = marker.lower()
    for section in sections:
        if marker_lower in section.lower():
            return section
    pytest.fail(f"Section marker '{marker}' not found in reference file")


@pytest.fixture(scope="session", autouse=True)
def ensure_search_api_container_running() -> None:
    check = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", SEARCH_API_CONTAINER],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if check.returncode != 0:
        pytest.fail(
            f"Container {SEARCH_API_CONTAINER} is not available. "
            "Start docker compose services before running tests."
        )

    if check.stdout.strip().lower() != "true":
        pytest.fail(
            f"Container {SEARCH_API_CONTAINER} is not running. "
            "Start docker compose services before running tests."
        )


@pytest.fixture(scope="session")
def reference_sections() -> list[str]:
    reference_path = _project_root() / REFERENCE_FILENAME
    if not reference_path.exists():
        pytest.fail(f"Reference file not found: {reference_path}")

    text = reference_path.read_text(encoding="utf-8")
    sections = [chunk.strip() for chunk in text.split("-----") if chunk.strip()]
    if not sections:
        pytest.fail(f"No sections found in {REFERENCE_FILENAME} with delimiter '-----'")
    return sections


def test_reference_file_sections_loaded(reference_sections: list[str]) -> None:
    assert len(reference_sections) >= 5


@pytest.mark.parametrize("query, section_marker, expected_terms", SEARCH_CASES)
def test_search_relevant_queries_from_reference_sections(
    reference_sections: list[str],
    query: str,
    section_marker: str,
    expected_terms: tuple[str, ...],
) -> None:
    section_text = _find_section_by_marker(reference_sections, section_marker)
    assert query.lower() in section_text.lower()

    payload = _search_api_get("/search", q=query, mode="hybrid", top_k=5)
    results = _extract_first_list(payload, "results")
    assert results, f"Expected non-empty search results for query: {query}"

    searchable_blob = " ".join(
        f"{item.get('title', '')} {item.get('snippet', '')} {item.get('path', '')}".lower()
        for item in results
        if isinstance(item, dict)
    )
    assert any(term in searchable_blob for term in expected_terms), (
        f"Results for query '{query}' do not look relevant. "
        f"Expected one of: {expected_terms}. Payload: {payload}"
    )


def test_search_filters_irrelevant_queries_by_min_score() -> None:
    payload = _search_api_get("/search", q=NOISE_QUERY, mode="hybrid", top_k=5)
    results = _extract_first_list(payload, "results")
    assert results == [], (
        "Expected empty results for irrelevant query. "
        "Iteration 9 requires score filtering by min_score."
    )


def test_similar_endpoint_returns_3_to_5_related_articles() -> None:
    seed_payload = _search_api_get("/search", q="vpn", mode="hybrid", top_k=1)
    seed_results = _extract_first_list(seed_payload, "results")
    assert seed_results, "Cannot run /similar test because seed search returned no results."

    seed_page_id = seed_results[0].get("page_id")
    assert isinstance(seed_page_id, int), f"Expected integer page_id, got: {seed_page_id}"

    payload = _search_api_get("/similar", page_id=seed_page_id)
    similar_items = _extract_first_list(payload, "similar", "results", "articles")
    assert 3 <= len(similar_items) <= 5, (
        f"Expected 3..5 similar articles, got {len(similar_items)}. Payload: {payload}"
    )

    similar_ids = {item.get("page_id") for item in similar_items if isinstance(item, dict)}
    assert seed_page_id not in similar_ids, "Source page_id must not be present in similar list."

    for item in similar_items:
        assert isinstance(item, dict), f"Expected dict item, got: {type(item)}"
        assert "score" in item, f"Expected score in similar item: {item}"
        float(item["score"])


def test_duplicates_endpoint_respects_threshold() -> None:
    threshold = 0.9
    payload = _search_api_get("/duplicates", threshold=threshold)
    duplicates = _extract_first_list(payload, "duplicates", "results", "pairs")

    if "threshold" in payload:
        assert float(payload["threshold"]) == pytest.approx(threshold, abs=1e-6)

    for pair in duplicates:
        assert isinstance(pair, dict), f"Expected dict pair, got: {type(pair)}"
        assert "score" in pair, f"Expected score field in pair: {pair}"
        assert float(pair["score"]) >= threshold, (
            f"Duplicate pair score is below threshold {threshold}: {pair}"
        )

        left_id = pair.get("page_id_1", pair.get("left_page_id"))
        right_id = pair.get("page_id_2", pair.get("right_page_id"))
        if left_id is not None and right_id is not None:
            assert left_id != right_id, f"Duplicate pair has same page_id: {pair}"
