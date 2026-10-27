"""[B] 기능·버그 탐색: 필터, 정렬, 직접 링크, 새로고침·뒤로 가기, 외부 링크, 잘못된 데이터, 콘솔 오류, 성능."""

from __future__ import annotations

import re
import time

import pytest
from playwright.sync_api import Page

from src.filters import Filters, SORT_LABELS, TARGET_LABELS, apply_filters
from src.models import CATEGORY_LABELS, LEVEL_LABELS, STATUS_LABELS
from tests.e2e.conftest import (
    BENIGN_FAILED_REQUEST,
    BY_ID,
    DATA,
    goto,
    main_text,
    multiselect,
    nav,
    record,
    selectbox,
    settle,
    shot,
    type_keyword,
    visible_card_titles,
)

TOTAL = len(DATA.policies)

COMBOS = {
    "category_carbon": Filters(categories=["carbon_pricing_trade"]),
    "korea_high": Filters(targets=["korea"], relevance=["high"]),
    "keyword_cbam": Filters(keyword="CBAM"),
    "product_eu": Filters(categories=["product_footprint"], targets=["eu"]),
    "pending_keyword": Filters(statuses=["pending"], keyword="철강"),
    "all_four": Filters(categories=["carbon_pricing_trade"], targets=["non_eu"], relevance=["high"], keyword="수입"),
}


def apply_in_ui(page: Page, f: Filters) -> None:
    if f.statuses:
        multiselect(page, "상태", [STATUS_LABELS[s] for s in f.statuses])
    if f.categories:
        multiselect(page, "정책 분야", [CATEGORY_LABELS[c] for c in f.categories])
    if f.targets:
        multiselect(page, "영향 대상", [TARGET_LABELS[t] for t in f.targets])
    if f.relevance:
        multiselect(page, "철강 관련도", [LEVEL_LABELS[r] for r in f.relevance])
    if f.keyword:
        type_keyword(page, f.keyword)


def tab_counts(page: Page) -> list[int]:
    return [int(re.search(r"\((\d+)\)", t).group(1)) for t in page.get_by_role("tab").all_inner_texts()]


# B1 필터 조합 ------------------------------------------------------------------
@pytest.mark.parametrize("name", COMBOS)
def test_b1_filter_combinations(page: Page, app_url, name):
    f = COMBOS[name]
    expected = apply_filters(DATA.policies, f)
    goto(page, app_url, "policies")
    apply_in_ui(page, f)
    shot(page, f"B1_filter_{name}")
    assert tab_counts(page) == [sum(p.status == "in_force" for p in expected), sum(p.status == "pending" for p in expected)]
    assert f"전체 {TOTAL}건 중 {len(expected)}건 표시" in main_text(page)
    titles = set(visible_card_titles(page))
    assert titles == {p.name_ko for p in expected if p.status == "in_force"}


@pytest.mark.parametrize("path,empty_text", [
    ("policies", "조건에 맞는 정책이 없습니다"),
    ("impact", "조건에 맞는 정책이 없습니다"),
    ("consultations", "등록된 의견수렴이 없습니다"),
    ("", "표시할 마일스톤이 없습니다"),
])
def test_b1_zero_results_empty_state(page: Page, app_url, path, empty_text):
    goto(page, app_url, path)
    type_keyword(page, "존재하지않는검색어zzz")
    shot(page, f"B1_empty_{path or 'dashboard'}")
    assert empty_text in main_text(page)
    assert page.locator("[data-testid=stException]").count() == 0


# B2 페이지 이동 시 필터 유지 ------------------------------------------------------
def test_b2_filter_persists_across_pages(page: Page, app_url):
    f = Filters(relevance=["high"])
    n = len(apply_filters(DATA.policies, f))
    goto(page, app_url, "")
    apply_in_ui(page, f)
    for title in ("정책 목록", "의견수렴 현황", "영향 매트릭스", "변경 이력", "정책 상세", "대시보드"):
        nav(page, title)
        chips = page.locator("[data-testid=stSidebar] [data-baseweb=tag]").all_inner_texts()
        assert [c.strip() for c in chips] == ["상"], (title, chips)
        if title in ("정책 목록", "의견수렴 현황", "영향 매트릭스", "대시보드"):
            assert f"전체 {TOTAL}건 중 {n}건 표시" in main_text(page), title
    shot(page, "B2_filter_persisted")


def test_b2_reset_button_clears_filters(page: Page, app_url):
    goto(page, app_url, "policies")
    apply_in_ui(page, Filters(relevance=["high"], keyword="CBAM"))
    page.get_by_role("button", name=re.compile("필터 초기화")).click()
    settle(page)
    assert "필터 적용 중" not in main_text(page)
    assert sum(tab_counts(page)) == TOTAL
    assert page.get_by_role("textbox", name="키워드 검색").input_value() == ""


# B3 정렬 ----------------------------------------------------------------------
@pytest.mark.parametrize("key", list(SORT_LABELS))
def test_b3_sort_order(page: Page, app_url, key):
    goto(page, app_url, "policies")
    selectbox(page, "정렬", SORT_LABELS[key])
    expected = [p.name_ko for p in apply_filters(DATA.policies, Filters(sort=key)) if p.status == "in_force"]
    # 카드는 2열(왼쪽: 짝수 번째, 오른쪽: 홀수 번째)로 배치되므로 열 순서대로 다시 맞춘다
    shown = visible_card_titles(page)
    left, right = expected[0::2], expected[1::2]
    assert shown == left + right, shown
    shot(page, f"B3_sort_{key}")


def test_b3_sort_changes_order(page: Page, app_url):
    orders = {}
    goto(page, app_url, "policies")
    for key in SORT_LABELS:
        selectbox(page, "정렬", SORT_LABELS[key])
        orders[key] = visible_card_titles(page)
    assert len({tuple(o) for o in orders.values()}) == len(SORT_LABELS)


# B4 직접 링크 -------------------------------------------------------------------
def test_b4_unknown_policy_id_shows_message(page: Page, app_url):
    goto(page, app_url, "detail?policy=does_not_exist")
    shot(page, "B4_unknown_policy")
    assert "'does_not_exist'에 해당하는 정책이 없습니다" in main_text(page)
    assert page.locator("[data-testid=stException]").count() == 0


def test_b4_card_link_opens_matching_detail(page: Page, app_url):
    pid = DATA.policies[3].id
    goto(page, app_url, "policies")
    tab = "시행 중" if BY_ID[pid].status == "in_force" else "제정 중"
    page.get_by_role("tab", name=re.compile(tab)).click()
    page.locator(f".st-key-card_{pid} a", has_text="상세 보기").click()
    page.locator("h2", has_text=BY_ID[pid].name_ko).wait_for()
    assert f"policy={pid}" in page.url


def test_b4_selectbox_change_updates_url(page: Page, app_url):
    a, b = DATA.policies[0], DATA.policies[5]
    goto(page, app_url, f"detail?policy={a.id}")
    selectbox(page, "정책 선택", b.name_ko)
    page.locator("h2", has_text=b.name_ko).wait_for()
    assert f"policy={b.id}" in page.url


# B5 새로고침·뒤로 가기 ------------------------------------------------------------
@pytest.mark.parametrize("path", ["", "policies", "detail?policy=cbam", "consultations", "impact", "changelog"])
def test_b5_reload(page: Page, app_url, path):
    goto(page, app_url, path)
    title = page.locator("h1").first.inner_text()
    page.reload()
    page.locator("h1").first.wait_for()
    settle(page)
    assert page.locator("h1").first.inner_text() == title
    assert page.locator("[data-testid=stException]").count() == 0


def test_b5_back_navigation(page: Page, app_url):
    goto(page, app_url, "")
    nav(page, "정책 목록")
    nav(page, "영향 매트릭스")
    page.go_back()
    page.locator("h1", has_text="정책 목록").wait_for(timeout=15000)
    page.go_back()
    page.locator("h1", has_text="대시보드").wait_for(timeout=15000)


# B6 외부 링크 -------------------------------------------------------------------
def test_b6_external_links_open_new_tab(page: Page, app_url):
    collected = {}
    for pid in BY_ID:
        goto(page, app_url, f"detail?policy={pid}")
        links = page.locator("[data-testid=stMain] a[href^=http]").evaluate_all(
            "els => els.map(e => ({href: e.getAttribute('href'), target: e.getAttribute('target'), text: e.innerText.trim()}))")
        collected[pid] = links
    record("B6_external_links", collected)
    bad = [(pid, l) for pid, ls in collected.items() for l in ls if l["target"] != "_blank" or not l["href"].strip()]
    assert not bad, bad[:5]
    assert sum(len(v) for v in collected.values()) > len(BY_ID)


# B7 잘못된 데이터 ----------------------------------------------------------------
def test_b7_invalid_entry_is_skipped_with_warning(page: Page, custom_server):
    def mutate(policies):
        policies[0]["status"] = "unknown_status"
        return policies

    url = custom_server(mutate)
    goto(page, url, "policies")
    shot(page, "B7_invalid_entry")
    text = main_text(page)
    assert "데이터 검증 오류 1건" in text
    assert sum(tab_counts(page)) == TOTAL - 1
    assert page.locator("[data-testid=stException]").count() == 0


def test_b7_yaml_syntax_error_does_not_crash(page: Page, custom_server):
    url = custom_server(raw_policies="- id: [broken\n  name_ko: 깨진 파일\n")
    for path in ("", "policies", "detail", "consultations", "impact", "changelog"):
        goto(page, url, path)
        assert "데이터 검증 오류" in main_text(page), path
        assert page.locator("[data-testid=stException]").count() == 0, path
    shot(page, "B7_yaml_syntax_error")


# B8 콘솔 오류·예외 ---------------------------------------------------------------
def test_b8_no_console_errors_or_exceptions(page: Page, app_url):
    errors, failed = [], []
    page.on("console", lambda m: m.type == "error" and errors.append(m.text))
    page.on("response", lambda r: r.status >= 400 and failed.append(f"{r.status} {r.url}"))
    paths = ["", "policies", "detail?policy=cbam_downstream", "consultations", "impact", "changelog"]
    exceptions = {}
    for path in paths:  # 주소로 바로 접속
        goto(page, app_url, path)
        exceptions[path] = page.locator("[data-testid=stException]").count()
    goto(page, app_url, "")
    for title in ("정책 목록", "정책 상세", "의견수렴 현황", "영향 매트릭스", "변경 이력"):  # 메뉴로 이동
        nav(page, title)
        exceptions[title] = page.locator("[data-testid=stException]").count()
    unexpected = [f for f in failed if not BENIGN_FAILED_REQUEST.search(f.split(" ", 1)[1])]
    benign = [f for f in failed if f not in unexpected]
    # 콘솔 오류 중 허용된 404 요청에 대한 'Failed to load resource' 메시지 수만큼은 제외
    console_unexpected = [e for e in errors if "Failed to load resource" not in e] + \
        [e for e in errors if "Failed to load resource" in e][len(benign):]
    record("B8_console", {"failed_requests": failed, "console_errors": errors, "exceptions": exceptions})
    assert not any(exceptions.values()), exceptions
    assert not unexpected, unexpected
    assert not console_unexpected, console_unexpected


# B9 성능 ----------------------------------------------------------------------
def test_b9_first_load_under_3s(browser, app_url):
    # 서버 예열 (첫 요청 시 모듈 로드)
    warm = browser.new_page()
    goto(warm, app_url, "")
    warm.close()

    timings = {}
    for path in ("", "policies", "detail?policy=cbam", "consultations", "impact", "changelog"):
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})  # 캐시 없는 새 방문자
        page = ctx.new_page()
        start = time.perf_counter()
        goto(page, app_url, path)
        timings[path or "dashboard"] = round(time.perf_counter() - start, 2)
        ctx.close()

    page = browser.new_page()
    goto(page, app_url, "")
    transitions = {}
    for title in ("정책 목록", "정책 상세", "의견수렴 현황", "영향 매트릭스", "변경 이력", "대시보드"):
        start = time.perf_counter()
        nav(page, title)
        transitions[title] = round(time.perf_counter() - start, 2)
    page.close()
    record("B9_performance", {"first_load_sec": timings, "page_transition_sec": transitions})
    slow = {k: v for k, v in timings.items() if v > 3.0}
    assert not slow, f"첫 로딩 3초 초과: {slow}"
