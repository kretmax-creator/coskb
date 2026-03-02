from __future__ import annotations

import json
import subprocess
from urllib.parse import urlencode

import pytest

SEARCH_API_CONTAINER = "coskb-search-api"
SEARCH_MODES = ("hybrid", "vector", "fts")
NOISE_QUERY = "zzzzzz_nonexistent_coskb_2026_qa_signal"
EPS = 1e-6

REFERENCE_SECTIONS = (
    "# Настройка подключения к VPN контура разработки и тестирования\n"
    "Сайт: cvpn.vtb.ru\n"
    "Server address = ext.vpn.vtb.ru\n"
    "Работа в домене DevCorp с активным VPN ВТБ ext.",
    "# Сфера\n"
    "Сфера.Задачи: https://sfera.inno.local\n"
    "Сфера.Знания/Документы: https://sfera.vtb.ru",
    "# Траблы Outlook\n"
    "Outlook запрашивает данные для входа после обновления пароля к ВРМ.",
    "# Сакура\n"
    "Требование по установке агента NAC Сакура при подключении к vpn ext.vtb.ru.",
    "# Тех. поддержка ВТБ\n"
    "Каналы обращения: spp3@vtb.ru, телефон 8 495 933 22 44.",
    "# УЗ ГК Иннотех\n"
    "УЗ ГК Иннотех нужна для VPN ГК Иннотех и контура Т1/Иннотех.",
    "# Токен\n"
    "Для использования Rutoken требуется установка драйвера и ПО.",
)

SEARCH_CASES_STRICT = (
    ("vpn", "Настройка подключения к VPN", ("vpn", "cvpn", "ext")),
    ("сфера", "Сфера", ("сфера", "sfera")),
    ("outlook", "Траблы Outlook", ("outlook",)),
    ("сакура", "Сакура", ("сакура", "nac")),
    ("иннотех", "УЗ ГК Иннотех", ("иннотех", "inno")),
    ("токен", "Токен", ("токен", "rutoken")),
)

SEARCH_QUERIES_SMOKE = ("vpn", "cvpn", "devcorp", "сфера", "outlook", "сакура", "иннотех", "токен")


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


def _search_api_get_raw(path: str, **params: object) -> tuple[int, dict]:
    query = urlencode(params, doseq=True)
    url = f"http://localhost:8000{path}"
    if query:
        url = f"{url}?{query}"
    script = f"""
import json, urllib.request, urllib.error
url = {url!r}
try:
    with urllib.request.urlopen(url, timeout=20) as r:
        body = r.read().decode("utf-8", errors="replace")
        print(json.dumps({{"status_code": r.getcode(), "body": body}}, ensure_ascii=False))
except urllib.error.HTTPError as e:
    print(json.dumps({{"status_code": e.code, "body": e.read().decode("utf-8", errors="replace")}}, ensure_ascii=False))
except Exception as e:
    print(json.dumps({{"status_code": 0, "error": str(e)}}, ensure_ascii=False))
"""
    raw = _run_container_python(script)
    try:
        envelope = json.loads(raw)
    except json.JSONDecodeError as exc:
        pytest.fail(f"Invalid JSON envelope: {exc}\nraw: {raw}")
    if envelope.get("status_code") == 0:
        pytest.fail(f"GET {path} failed: {envelope.get('error', 'unknown error')}")
    status_code = int(envelope.get("status_code", 0))
    body_raw = envelope.get("body", "")
    if not isinstance(body_raw, str):
        body_raw = str(body_raw)
    try:
        payload = json.loads(body_raw)
    except json.JSONDecodeError:
        payload = {"raw_body": body_raw}
    if not isinstance(payload, dict):
        payload = {"raw_body": body_raw}
    return status_code, payload


def _search_api_get(path: str, **params: object) -> dict:
    status_code, payload = _search_api_get_raw(path, **params)
    if status_code != 200:
        pytest.fail(f"GET {path} expected HTTP 200, got {status_code}. Payload: {payload}")
    return payload


def _extract_first_list(payload: dict, *keys: str) -> list:
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            return value
    pytest.fail(f"Expected list in one of keys {keys}, got payload: {payload}")


def _find_section_by_marker(sections: list[str], marker: str) -> str:
    marker_l = marker.lower()
    for section in sections:
        if marker_l in section.lower():
            return section
    pytest.fail(f"Section marker '{marker}' not found in embedded materials")


def _assert_scores_sorted_desc(results: list[dict], context: str) -> None:
    scores = [float(item.get("score", 0.0)) for item in results if isinstance(item, dict)]
    for idx in range(len(scores) - 1):
        assert scores[idx] + EPS >= scores[idx + 1], (
            f"Scores must be sorted desc for {context}: {scores}"
        )


def _assert_result_contract(item: dict, context: str) -> None:
    assert isinstance(item.get("page_id"), int), f"page_id must be int in {context}: {item}"
    assert isinstance(item.get("title"), str), f"title must be str in {context}: {item}"
    assert isinstance(item.get("snippet"), str), f"snippet must be str in {context}: {item}"
    assert len(item["snippet"]) <= 200, f"snippet must be <= 200 in {context}: {item}"
    assert "score" in item, f"score is required in {context}: {item}"
    float(item["score"])


@pytest.fixture(scope="session", autouse=True)
def ensure_search_api_container_running() -> None:
    check = subprocess.run(
        ["docker", "inspect", "-f", "{{.State.Running}}", SEARCH_API_CONTAINER],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    if check.returncode != 0 or check.stdout.strip().lower() != "true":
        pytest.fail(
            f"Container {SEARCH_API_CONTAINER} is not running. "
            "Start docker compose services before running tests."
        )


@pytest.fixture(scope="session")
def reference_sections() -> list[str]:
    sections = [chunk.strip() for chunk in REFERENCE_SECTIONS if chunk.strip()]
    if not sections:
        pytest.fail("Embedded reference sections are empty.")
    return sections


@pytest.fixture(scope="session")
def indexed_stats() -> dict:
    payload = _search_api_get("/stats")
    indexed_pages = payload.get("indexed_pages")
    if not isinstance(indexed_pages, int):
        pytest.fail(f"/stats returned invalid indexed_pages: {payload}")
    if indexed_pages <= 0:
        pytest.fail(
            "No indexed embeddings found (indexed_pages=0). "
            "Run POST /index before running iteration-9 tests."
        )
    return payload


@pytest.fixture(scope="session")
def api_min_scores() -> dict[str, float]:
    script = """
import json, os
print(json.dumps({
  "hybrid": float(os.environ.get("MIN_SCORE_HYBRID", "0.52")),
  "vector": float(os.environ.get("MIN_SCORE_VECTOR", "0.55")),
  "fts": float(os.environ.get("MIN_SCORE_FTS", "0.001"))
}, ensure_ascii=False))
"""
    raw = _run_container_python(script)
    values = json.loads(raw)
    return {
        "hybrid": float(values.get("hybrid", 0.52)),
        "vector": float(values.get("vector", 0.55)),
        "fts": float(values.get("fts", 0.001)),
    }


@pytest.fixture(scope="session")
def seed_page_id(indexed_stats: dict) -> int:
    _ = indexed_stats
    payload = _search_api_get("/search", q="vpn", mode="hybrid", top_k=1)
    results = _extract_first_list(payload, "results")
    if not results:
        pytest.fail("Cannot resolve seed page_id from /search?q=vpn.")
    page_id = results[0].get("page_id")
    if not isinstance(page_id, int):
        pytest.fail(f"Expected integer page_id in seed result, got: {page_id}")
    return page_id


def test_reference_materials_loaded(reference_sections: list[str]) -> None:
    assert len(reference_sections) >= 7


def test_health_endpoint_contract() -> None:
    payload = _search_api_get("/health")
    assert payload.get("status") in {"ok", "degraded"}
    assert isinstance(payload.get("model_loaded"), bool)
    assert isinstance(payload.get("db_connected"), bool)


def test_stats_endpoint_contract(indexed_stats: dict) -> None:
    assert isinstance(indexed_stats.get("indexed_pages"), int)
    assert indexed_stats["indexed_pages"] >= 0
    assert "last_indexed_at" in indexed_stats


@pytest.mark.parametrize("query, section_marker, expected_terms", SEARCH_CASES_STRICT)
def test_search_relevant_queries_from_reference_sections(
    reference_sections: list[str],
    indexed_stats: dict,
    query: str,
    section_marker: str,
    expected_terms: tuple[str, ...],
) -> None:
    _ = indexed_stats
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


@pytest.mark.parametrize("query", SEARCH_QUERIES_SMOKE)
def test_search_smoke_queries_return_results(indexed_stats: dict, query: str) -> None:
    _ = indexed_stats
    results = _extract_first_list(_search_api_get("/search", q=query, mode="hybrid", top_k=5), "results")
    assert results, f"Expected non-empty results for smoke query '{query}'."


@pytest.mark.parametrize("mode", SEARCH_MODES)
def test_search_response_contract_for_each_mode(indexed_stats: dict, mode: str) -> None:
    _ = indexed_stats
    payload = _search_api_get("/search", q="vpn", mode=mode, top_k=5)
    assert payload.get("mode") == mode
    assert isinstance(payload.get("query"), str)
    for item in _extract_first_list(payload, "results"):
        assert isinstance(item, dict)
        _assert_result_contract(item, f"/search mode={mode}")


@pytest.mark.parametrize("mode", SEARCH_MODES)
def test_search_results_are_sorted_by_score_desc(indexed_stats: dict, mode: str) -> None:
    _ = indexed_stats
    results = _extract_first_list(_search_api_get("/search", q="vpn", mode=mode, top_k=10), "results")
    _assert_scores_sorted_desc(results, f"/search mode={mode}")


@pytest.mark.parametrize("mode", SEARCH_MODES)
@pytest.mark.parametrize("top_k", (1, 2, 3, 5))
def test_search_respects_top_k(indexed_stats: dict, mode: str, top_k: int) -> None:
    _ = indexed_stats
    results = _extract_first_list(_search_api_get("/search", q="vpn", mode=mode, top_k=top_k), "results")
    assert len(results) <= top_k


@pytest.mark.parametrize("mode", SEARCH_MODES)
def test_search_scores_respect_min_score(indexed_stats: dict, api_min_scores: dict[str, float], mode: str) -> None:
    _ = indexed_stats
    results = _extract_first_list(_search_api_get("/search", q="vpn", mode=mode, top_k=20), "results")
    min_score = float(api_min_scores[mode])
    for item in results:
        score = float(item.get("score", 0.0))
        assert score + EPS >= min_score, f"Score below mode min_score: mode={mode}, score={score}"


def test_search_filters_irrelevant_queries_by_min_score() -> None:
    results = _extract_first_list(_search_api_get("/search", q=NOISE_QUERY, mode="hybrid", top_k=5), "results")
    assert results == []


def test_search_empty_query_returns_422() -> None:
    status_code, payload = _search_api_get_raw("/search", q="", mode="hybrid", top_k=5)
    assert status_code == 422, f"Expected 422 for empty q, got {status_code}. Payload: {payload}"


@pytest.mark.parametrize("top_k", (0, 21))
def test_search_invalid_top_k_returns_422(top_k: int) -> None:
    status_code, payload = _search_api_get_raw("/search", q="vpn", mode="hybrid", top_k=top_k)
    assert status_code == 422, f"Expected 422 for invalid top_k={top_k}, got {status_code}. Payload: {payload}"


def test_similar_endpoint_returns_3_to_5_related_articles(seed_page_id: int) -> None:
    similar_items = _extract_first_list(_search_api_get("/similar", page_id=seed_page_id), "similar", "results", "articles")
    assert 3 <= len(similar_items) <= 5
    similar_ids = {item.get("page_id") for item in similar_items if isinstance(item, dict)}
    assert seed_page_id not in similar_ids
    for item in similar_items:
        assert isinstance(item, dict)
        _assert_result_contract(item, "/similar")


@pytest.mark.parametrize("top_k", (1, 3, 5))
def test_similar_respects_top_k(seed_page_id: int, top_k: int) -> None:
    similar_items = _extract_first_list(_search_api_get("/similar", page_id=seed_page_id, top_k=top_k), "similar", "results", "articles")
    assert len(similar_items) <= top_k


def test_similar_scores_are_sorted_desc(seed_page_id: int) -> None:
    similar_items = _extract_first_list(_search_api_get("/similar", page_id=seed_page_id, top_k=10), "similar", "results", "articles")
    _assert_scores_sorted_desc(similar_items, "/similar")


def test_similar_missing_page_returns_404() -> None:
    status_code, payload = _search_api_get_raw("/similar", page_id=999999999, top_k=5)
    assert status_code == 404, f"Expected 404 for missing page_id, got {status_code}. Payload: {payload}"


def test_similar_invalid_page_id_type_returns_422() -> None:
    status_code, payload = _search_api_get_raw("/similar", page_id="not-an-int", top_k=5)
    assert status_code == 422, f"Expected 422 for page_id type, got {status_code}. Payload: {payload}"


@pytest.mark.parametrize("top_k", (0, 21))
def test_similar_invalid_top_k_returns_422(seed_page_id: int, top_k: int) -> None:
    status_code, payload = _search_api_get_raw("/similar", page_id=seed_page_id, top_k=top_k)
    assert status_code == 422, f"Expected 422 for /similar top_k={top_k}, got {status_code}. Payload: {payload}"


def test_duplicates_endpoint_contract() -> None:
    payload = _search_api_get("/duplicates", threshold=0.9)
    duplicates = _extract_first_list(payload, "duplicates", "results", "pairs")
    assert float(payload.get("threshold")) == pytest.approx(0.9, abs=EPS)
    assert isinstance(duplicates, list)


def test_duplicates_endpoint_respects_threshold() -> None:
    threshold = 0.9
    payload = _search_api_get("/duplicates", threshold=threshold)
    duplicates = _extract_first_list(payload, "duplicates", "results", "pairs")
    if "threshold" in payload:
        assert float(payload["threshold"]) == pytest.approx(threshold, abs=EPS)
    for pair in duplicates:
        assert isinstance(pair, dict)
        assert "score" in pair
        assert float(pair["score"]) >= threshold
        left_id = pair.get("page_id_1", pair.get("left_page_id"))
        right_id = pair.get("page_id_2", pair.get("right_page_id"))
        if left_id is not None and right_id is not None:
            assert left_id != right_id


def test_duplicates_pairs_sorted_and_unique() -> None:
    duplicates = _extract_first_list(_search_api_get("/duplicates", threshold=0.9), "duplicates", "results", "pairs")
    _assert_scores_sorted_desc(duplicates, "/duplicates")
    seen_pairs: set[tuple[int, int]] = set()
    for pair in duplicates:
        left_id = pair.get("page_id_1")
        right_id = pair.get("page_id_2")
        assert isinstance(left_id, int)
        assert isinstance(right_id, int)
        assert left_id < right_id
        key = (left_id, right_id)
        assert key not in seen_pairs
        seen_pairs.add(key)


def test_duplicates_monotonicity_by_threshold() -> None:
    duplicates_lo = _extract_first_list(_search_api_get("/duplicates", threshold=0.9), "duplicates", "results", "pairs")
    duplicates_hi = _extract_first_list(_search_api_get("/duplicates", threshold=0.95), "duplicates", "results", "pairs")
    assert len(duplicates_hi) <= len(duplicates_lo)


@pytest.mark.parametrize("threshold", (0.49, 1.01))
def test_duplicates_invalid_threshold_returns_422(threshold: float) -> None:
    status_code, payload = _search_api_get_raw("/duplicates", threshold=threshold)
    assert status_code == 422, f"Expected 422 for threshold={threshold}, got {status_code}. Payload: {payload}"


@pytest.mark.parametrize("threshold", (0.5, 1.0))
def test_duplicates_accepts_threshold_bounds(threshold: float) -> None:
    payload = _search_api_get("/duplicates", threshold=threshold)
    duplicates = _extract_first_list(payload, "duplicates", "results", "pairs")
    assert float(payload.get("threshold")) == pytest.approx(threshold, abs=EPS)
    assert isinstance(duplicates, list)
