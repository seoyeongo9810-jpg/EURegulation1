"""[C] UI·반응형·접근성, [D] 데이터 정합성."""

from __future__ import annotations

import re

import pytest
from playwright.sync_api import Page

from src.models import LEVEL_LABELS, STATUS_LABELS
from tests.e2e.conftest import BY_ID, DATA, SHOTS, goto, main_text, norm, settle, shot

PAGES = {"dashboard": "", "list": "policies", "detail": "detail?policy=cbam_downstream",
         "consult": "consultations", "impact": "impact", "changelog": "changelog"}
WIDTHS = {"desktop": 1440, "tablet": 1024, "mobile": 390}
ISO = r"\d{4}-\d{2}-\d{2}"


def layout_problems(page: Page) -> dict:
    return page.evaluate(
        """() => {
            const vw = window.innerWidth;
            const main = document.querySelector('[data-testid=stMain]');
            // 표(dataframe) 내부의 가로 스크롤은 의도된 동작이므로 제외
            const overflow = [...main.querySelectorAll('*')].filter(e => {
                if (e.closest('[data-testid=stDataFrame]')) return false;
                const r = e.getBoundingClientRect();
                return r.width > 0 && r.right > vw + 1 && getComputedStyle(e).position !== 'fixed';
            }).map(e => e.dataset.testid || e.className || e.tagName).slice(0, 5);
            return {
                pageHScroll: document.documentElement.scrollWidth > vw,
                mainHScroll: main.scrollWidth > main.clientWidth + 1,
                overflow,
                exceptions: document.querySelectorAll('[data-testid=stException]').length,
            };
        }"""
    )


# C1 반응형 --------------------------------------------------------------------
@pytest.mark.parametrize("width_name", WIDTHS)
@pytest.mark.parametrize("name", PAGES)
def test_c1_responsive_no_horizontal_scroll(page: Page, app_url, name, width_name):
    w = WIDTHS[width_name]
    page.set_viewport_size({"width": w, "height": 844 if w < 500 else 900})
    goto(page, app_url, PAGES[name])
    shot(page, f"C1_{width_name}_{name}")
    problems = layout_problems(page)
    assert not problems["pageHScroll"] and not problems["mainHScroll"], problems
    assert not problems["overflow"], problems
    assert problems["exceptions"] == 0


def test_c1_mobile_kpis_two_per_row(page: Page, app_url):
    page.set_viewport_size({"width": 390, "height": 844})
    goto(page, app_url, "")
    tops = page.locator(".st-key-kpis [data-testid=stMetric]").evaluate_all(
        "els => els.map(e => Math.round(e.getBoundingClientRect().top))")
    assert len(tops) == 4
    assert tops[0] == tops[1] and tops[2] == tops[3] and tops[0] < tops[2], tops


def test_c1_mobile_title_not_hidden_by_header(page: Page, app_url):
    page.set_viewport_size({"width": 390, "height": 844})
    goto(page, app_url, "policies")
    title_top = page.locator("h1").first.bounding_box()["y"]
    header = page.locator("[data-testid=stHeader]").bounding_box()
    assert title_top >= header["y"] + header["height"] - 1, (title_top, header)


# C2 라이트·다크 테마 ----------------------------------------------------------------
@pytest.mark.parametrize("scheme,bg", [("light", "rgb(255, 255, 255)"), ("dark", "rgb(17, 22, 28)")])
@pytest.mark.parametrize("name", PAGES)
def test_c2_theme(page: Page, app_url, name, scheme, bg):
    page.emulate_media(color_scheme=scheme)
    goto(page, app_url, PAGES[name])
    shot(page, f"C2_{scheme}_{name}")
    assert page.locator("[data-testid=stApp]").evaluate("e => getComputedStyle(e).backgroundColor") == bg
    # 본문 글자와 배경의 명도 차이가 충분한지 (WCAG 대비 4.5:1 이상)
    ratio = page.locator("[data-testid=stMain] h1").first.evaluate(
        """e => {
            const lum = c => { const [r,g,b] = c.match(/\\d+/g).slice(0,3).map(v => { v/=255; return v<=0.03928 ? v/12.92 : ((v+0.055)/1.055)**2.4; }); return 0.2126*r+0.7152*g+0.0722*b; };
            const fg = lum(getComputedStyle(e).color), bgc = lum(getComputedStyle(document.querySelector('[data-testid=stApp]')).backgroundColor);
            return (Math.max(fg,bgc)+0.05)/(Math.min(fg,bgc)+0.05);
        }""")
    assert ratio >= 4.5, ratio


# C3 색 + 텍스트 ----------------------------------------------------------------
@pytest.mark.parametrize("name", ["dashboard", "list", "detail", "consult"])
def test_c3_badges_have_text(page: Page, app_url, name):
    goto(page, app_url, PAGES[name])
    texts = page.locator("[data-testid=stMain] .stMarkdownBadge").all_inner_texts()
    assert texts, "배지가 없습니다"
    assert all(t.strip() for t in texts)


def test_c3_heatmap_cells_have_text_labels(page: Page, app_url):
    goto(page, app_url, "impact")
    data = page.locator(".js-plotly-plot").first.evaluate(
        "gd => ({tpl: gd.data[0].texttemplate, text: gd.data[0].text.flat(), y: gd.data[0].y})")
    assert data["tpl"] == "%{text}"
    assert set(data["text"]) <= set(LEVEL_LABELS.values())
    # 긴 정책명은 축에서 줄이고(…) 전체 이름은 hover로 제공
    assert all(len(y) <= 24 for y in data["y"])


def test_c3_stage_steps_labelled(page: Page, app_url):
    pending = next(p for p in DATA.policies if p.status == "pending")
    goto(page, app_url, f"detail?policy={pending.id}")
    steps = page.locator("ol.stepper li").all_inner_texts()
    assert len(steps) == 8 and all(norm(s) for s in steps)
    assert page.locator("ol.stepper").get_attribute("aria-label").startswith("입법 단계")


# D 데이터 정합성 -----------------------------------------------------------------
def test_d1_cards_match_yaml(page: Page, app_url):
    goto(page, app_url, "policies")
    problems = []
    for status in ("in_force", "pending"):
        page.get_by_role("tab", name=re.compile(STATUS_LABELS[status].split("·")[0])).click()
        settle(page)
        for p in (p for p in DATA.policies if p.status == status):
            card = page.locator(f".st-key-card_{p.id}")
            text = norm(card.inner_text())
            if not text.startswith(p.name_ko):
                problems.append((p.id, "정책명"))
            if card.locator(".card-sub").get_attribute("title") != p.name_en:
                problems.append((p.id, "영문명"))
            if p.legal_ref and norm(p.legal_ref) not in text:
                problems.append((p.id, "법령"))
            date_text = f"시행일 {p.effective_date.isoformat()}" if p.effective_date else "시행일 미정"
            if date_text not in text:
                problems.append((p.id, date_text))
            if ("확인 필요" in text.replace("재확인 필요", "")) != p.verify_needed:
                problems.append((p.id, "확인 필요 배지"))
    shot(page, "D1_cards")
    assert not problems, problems


def test_d2_app_generated_dates_are_iso(page: Page, app_url):
    """앱이 만드는 날짜 표기는 YYYY-MM-DD로 통일 (데이터 원문 속 날짜는 대상 아님)."""
    found = {}
    goto(page, app_url, "")
    found["dashboard_dday"] = page.locator("[data-testid=stMain] .dday").all_inner_texts()
    found["sidebar"] = page.locator("[data-testid=stSidebar] .alert-item .meta").all_inner_texts()
    found["sidebar_asof"] = [t for t in page.locator("[data-testid=stSidebar] [data-testid=stCaptionContainer]").all_inner_texts() if "기준일" in t]
    goto(page, app_url, "consultations")
    found["consult_period"] = [t for t in page.locator("[data-testid=stMain] [data-testid=stCaptionContainer]").all_inner_texts() if t.startswith("기간")]
    goto(page, app_url, "changelog")
    found["changelog"] = re.findall(r"^\S+", main_text(page))
    bad = {}
    for k, values in found.items():
        for v in values:
            for m in re.findall(r"\d{1,4}[./-]\d{1,2}(?:[./-]\d{1,2})?", v):
                if not re.fullmatch(ISO, m):
                    bad.setdefault(k, []).append(v)
    assert not bad, bad


def test_d3_data_as_of_is_latest_verification(page: Page, app_url):
    goto(page, app_url, "")
    latest = max(p.last_verified for p in DATA.policies)
    assert f"데이터 기준일: {latest.isoformat()}" in norm(page.locator("[data-testid=stSidebar]").inner_text())


def test_d4_changelog_matches_yaml(page: Page, app_url):
    goto(page, app_url, "changelog")
    text = main_text(page)
    for e in DATA.changelog:
        assert norm(e.summary)[:40] in text, e.summary[:40]
