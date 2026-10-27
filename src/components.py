"""여러 페이지에서 공통으로 쓰는 UI 조각. 색·아이콘은 src/theme.py, CSS는 assets/style.css."""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from html import escape
from pathlib import Path

import streamlit as st

from src.filters import SORT_LABELS, TARGET_LABELS, Filters, apply_filters
from src.loader import LoadResult
from src.models import (
    CATEGORY_LABELS,
    CONSULTATION_STATUS_LABELS,
    CONSULTATION_TYPE_LABELS,
    LEVEL_LABELS,
    REQUIREMENT_LABELS,
    STAGE_LABELS,
    STAGE_ORDER,
    STATUS_LABELS,
    STALE_THRESHOLD_DAYS,
    Consultation,
    Policy,
    consultation_status,
    days_until_end,
    is_stale,
    stage_progress,
)
from src.theme import BADGE, ICON, LEVEL_BADGE

DISCLAIMER = (
    "사내용 참고 자료입니다. 본 정보는 법적 효력이 없으며, "
    "의사결정 전 EU 공식 출처를 반드시 확인하세요."
)
ROOT = Path(__file__).resolve().parent.parent
VIEWS_DIR = ROOT / "views"
CSS_PATH = ROOT / "assets" / "style.css"
DETAIL_PAGE = VIEWS_DIR / "policy_detail.py"
DEADLINE_ALERT_DAYS = 30


def today() -> date:
    return date.today()


def data_as_of(result: LoadResult) -> date | None:
    """데이터 기준일 = 정책 중 가장 최근 last_verified."""
    return max((p.last_verified for p in result.policies), default=None)


def md(text: str | None) -> str:
    """데이터 문자열을 마크다운에 안전하게 넣는다.

    '2031~2040' 같은 물결표 범위가 취소선으로, '$'가 수식으로 렌더링되지 않도록 이스케이프한다.
    """
    return (text or "").replace("\\", "\\\\").replace("~", "\\~").replace("$", "\\$")


def format_d_day(days: int) -> str:
    if days > 0:
        return f"D-{days}"
    if days == 0:
        return "D-Day"
    return f"D+{-days}"


# ---- 페이지 공통 ----

@lru_cache(maxsize=1)
def _css(mtime: float) -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def inject_css() -> None:
    st.html(f"<style>{_css(CSS_PATH.stat().st_mtime)}</style>")


def page_header(title: str, subtitle: str | None = None) -> None:
    st.title(title)
    if subtitle:
        st.html(f'<p class="page-sub">{escape(subtitle)}</p>')


def section(title: str) -> None:
    st.html(f'<div class="section-title">{escape(title)}</div>')


def render_load_errors(result: LoadResult) -> None:
    if not result.errors:
        return
    st.warning(f"데이터 검증 오류 {len(result.errors)}건 — 해당 항목은 화면에 표시되지 않습니다.", icon=":material/error:")
    with st.expander("오류 상세 보기"):
        for err in result.errors:
            st.markdown(f"- {md(err)}")


# ---- 사이드바·필터 ----

def closing_soon(policies: list[Policy], now: date) -> list[tuple[Policy, Consultation, int]]:
    items = []
    for p in policies:
        for c in p.consultations:
            if consultation_status(c, now) == "open":
                d = days_until_end(c, now)
                if d <= DEADLINE_ALERT_DAYS:
                    items.append((p, c, d))
    return sorted(items, key=lambda x: x[2])


def render_sidebar(result: LoadResult) -> None:
    now = today()
    with st.sidebar:
        st.subheader("필터", anchor=False)
        st.multiselect(
            "상태", list(STATUS_LABELS), format_func=STATUS_LABELS.get, key="f_statuses", placeholder="전체"
        )
        st.multiselect(
            "정책 분야", list(CATEGORY_LABELS), format_func=CATEGORY_LABELS.get, key="f_categories", placeholder="전체"
        )
        st.multiselect(
            "영향 대상",
            list(TARGET_LABELS),
            format_func=TARGET_LABELS.get,
            key="f_targets",
            placeholder="전체",
            help="선택한 대상에 대한 영향도가 '중' 이상인 정책만 표시합니다.",
        )
        st.multiselect(
            "철강 관련도", list(LEVEL_LABELS), format_func=LEVEL_LABELS.get, key="f_relevance", placeholder="전체"
        )
        st.text_input("키워드 검색", key="f_keyword", placeholder="예: CBAM, 탄소발자국, 쿼터")
        st.selectbox("정렬", list(SORT_LABELS), format_func=SORT_LABELS.get, key="f_sort")
        if current_filters().active:
            st.button("필터 초기화", on_click=_reset_filters, width="stretch", icon=":material/restart_alt:")

        st.subheader("마감 임박 의견수렴", anchor=False)
        alerts = closing_soon(result.policies, now)
        if not alerts:
            st.caption(f"{DEADLINE_ALERT_DAYS}일 이내 마감되는 의견수렴이 없습니다.")
        for p, c, d in alerts:
            st.html(
                # D-day와 정책명 사이 공백: 화면은 CSS 여백으로 띄우지만 텍스트·스크린리더에서도 구분되도록
                f'<div class="alert-item"><b>{format_d_day(d)}</b> {escape(p.name_ko)}'
                f'<span class="meta">{escape(CONSULTATION_TYPE_LABELS[c.type])} · 마감 {c.end.isoformat()}</span></div>'
            )
            st.page_link(DETAIL_PAGE, label="정책 상세", query_params={"policy": p.id}, icon=ICON["go"])

        st.divider()
        as_of = data_as_of(result)
        st.caption(f"데이터 기준일: {as_of.isoformat() if as_of else '—'} · 주 1회 업데이트")
        st.caption(DISCLAIMER)
        with st.expander("배지 색상 안내"):
            render_legend()


def render_legend() -> None:
    items = [
        ("시행 중", BADGE["in_force"], None),
        ("제정 중·시행 예정", BADGE["pending"], None),
        ("의견수렴 진행 중", BADGE["open"], None),
        ("마감 임박(30일 이내)", BADGE["urgent"], None),
        ("재확인 필요(14일 경과)", BADGE["stale"], ICON["stale"]),
        ("확인 필요(출처 미확인)", BADGE["verify"], ICON["verify"]),
        ("영향도·관련도 상", LEVEL_BADGE["high"], None),
        ("영향도·관련도 중", LEVEL_BADGE["medium"], None),
        ("영향도·관련도 하", LEVEL_BADGE["low"], None),
    ]
    with st.container(horizontal=True, gap="small"):
        for label, color, icon in items:
            st.badge(label, color=color, icon=icon)


def _reset_filters() -> None:
    for key in ("f_statuses", "f_categories", "f_targets", "f_relevance"):
        st.session_state[key] = []
    st.session_state["f_keyword"] = ""


def current_filters() -> Filters:
    s = st.session_state
    return Filters(
        statuses=s.get("f_statuses", []),
        categories=s.get("f_categories", []),
        targets=s.get("f_targets", []),
        relevance=s.get("f_relevance", []),
        keyword=s.get("f_keyword", ""),
        sort=s.get("f_sort", "relevance"),
    )


def filtered_policies(result: LoadResult) -> list[Policy]:
    return apply_filters(result.policies, current_filters())


def render_filter_notice(shown: int, total: int) -> None:
    if current_filters().active:
        st.caption(f"사이드바 필터 적용 중: 전체 {total}건 중 {shown}건 표시")


# ---- 배지·카드 ----

def render_policy_badges(p: Policy, now: date, show_stage: bool = True) -> None:
    with st.container(horizontal=True, gap="small"):
        st.badge(STATUS_LABELS[p.status], color=BADGE[p.status])
        if show_stage and p.stage and p.status == "pending":
            st.badge(STAGE_LABELS[p.stage], color=BADGE["stage"])
        st.badge(f"관련도 {LEVEL_LABELS[p.steel_relevance]}", color=LEVEL_BADGE[p.steel_relevance])
        if p.verify_needed:
            st.badge("확인 필요", icon=ICON["verify"], color=BADGE["verify"], help=md(p.note))
        if is_stale(p, now):
            st.badge(
                "재확인 필요",
                icon=ICON["stale"],
                color=BADGE["stale"],
                help=f"마지막 확인일 후 {STALE_THRESHOLD_DAYS}일이 지났습니다.",
            )


def render_policy_card(p: Policy, now: date) -> None:
    # key → CSS 클래스 st-key-card_<id> (e2e 테스트에서 카드를 찾는 데 사용)
    with st.container(border=True, key=f"card_{p.id}"):
        st.html(
            f'<div class="card-title">{escape(p.name_ko)}</div>'
            f'<div class="card-sub" title="{escape(p.name_en)}">{escape(p.name_en)}</div>'
        )
        render_policy_badges(p, now)
        meta = [p.legal_ref or p.legal_form, f"DG {p.dg}"]
        meta.append(f"시행일 {p.effective_date.isoformat()}" if p.effective_date else "시행일 미정")
        st.caption(md(" · ".join(meta)))
        st.page_link(DETAIL_PAGE, label="상세 보기", query_params={"policy": p.id}, icon=ICON["go"])


# ---- 상세 구성 요소 ----

def render_requirements(p: Policy) -> None:
    if not p.requirements:
        st.caption("등록된 요구사항이 없습니다.")
        return
    for r in p.requirements:
        with st.container(horizontal=True, gap="small", vertical_alignment="center"):
            st.badge(REQUIREMENT_LABELS[r.type], color=BADGE["tag"])
            st.markdown(md(r.text))


def render_stage_steps(p: Policy) -> None:
    """입법 단계를 단계 이름이 보이는 스텝으로 표시한다."""
    current, total = stage_progress(p)
    labels = [STAGE_LABELS[s] for s in STAGE_ORDER] + ["시행"]
    items = []
    for i, label in enumerate(labels, start=1):
        cls = "done" if i < current else "current" if i == current else ""
        mark = "현재" if i == current else f"{i}단계"
        items.append(f'<li class="{cls}"><span class="num">{mark}</span>{escape(label)}</li>')
    st.html(f'<ol class="stepper" aria-label="입법 단계 {current}/{total}">{"".join(items)}</ol>')


def render_consultations(p: Policy, now: date) -> None:
    if not p.consultations:
        st.caption("등록된 의견수렴이 없습니다.")
        return
    for i, c in enumerate(sorted(p.consultations, key=lambda c: c.end, reverse=True)):
        render_consultation(c, now, key=f"{p.id}_{i}")


def _dday_box(c: Consultation, now: date) -> str:
    status = consultation_status(c, now)
    if status == "open":
        d = days_until_end(c, now)
        cls = "urgent" if d <= DEADLINE_ALERT_DAYS else "open"
        return f'<div class="dday {cls}">{format_d_day(d)}<small>마감까지</small></div>'
    if status == "upcoming":
        d = (c.start - now).days
        return f'<div class="dday upcoming">D-{d}<small>시작까지</small></div>'
    return '<div class="dday closed">마감<small>종료됨</small></div>'


def render_consultation(c: Consultation, now: date, key: str, policy: Policy | None = None) -> None:
    status = consultation_status(c, now)
    with st.container(border=True):
        left, right = st.columns([1, 6], vertical_alignment="top")
        with left:
            st.html(_dday_box(c, now))
        with right:
            with st.container(horizontal=True, gap="small"):
                st.badge(CONSULTATION_STATUS_LABELS[status], color=BADGE[status])
                st.badge(CONSULTATION_TYPE_LABELS[c.type], color=BADGE["tag"])
            if policy:
                st.markdown(f"**{md(policy.name_ko)}**")
            st.markdown(md(c.title))
            st.caption(md(f"기간 {c.start.isoformat()} ~ {c.end.isoformat()}"))
            if c.summary:
                st.markdown(md(c.summary))
            with st.container(horizontal=True, gap="small"):
                if c.url:
                    st.link_button("Have Your Say", c.url, icon=ICON["link"], key=f"hys_{key}")
                if policy:
                    st.page_link(DETAIL_PAGE, label="정책 상세", query_params={"policy": policy.id}, icon=ICON["go"])


def render_impact(p: Policy) -> None:
    cols = st.columns(3)
    for col, target, detail in (
        (cols[0], "eu", p.impact.eu_producers),
        (cols[1], "non_eu", p.impact.non_eu_producers),
    ):
        with col.container(border=True, height="stretch"):
            st.markdown(f"**{TARGET_LABELS[target]}**")
            st.badge(f"영향도 {LEVEL_LABELS[detail.level]}", color=LEVEL_BADGE[detail.level])
            for label, text in (
                ("직접 의무", detail.obligations),
                ("비용 영향", detail.costs),
                ("준비 사항", detail.preparation),
                ("기회 요인", detail.opportunities),
            ):
                if text:
                    st.markdown(f"**{label}**  \n{md(text)}")
    with cols[2].container(border=True, height="stretch"):
        level = p.impact.korea_effective_level
        st.markdown(f"**{TARGET_LABELS['korea']}**")
        st.badge(f"영향도 {LEVEL_LABELS[level]}", color=LEVEL_BADGE[level])
        if p.impact.korea_level is None:
            st.caption("영향도는 역외 철강사 기준을 따릅니다.")
        st.markdown(md(p.impact.korea_note) or "_시사점이 아직 작성되지 않았습니다._")


LINK_LABELS = {
    "commission": "EU Commission",
    "eurlex": "EUR-Lex 원문",
    "have_your_say": "Have Your Say",
    "oeil": "유럽의회 OEIL",
    "guidance": "가이던스·FAQ",
}


def render_links(p: Policy) -> None:
    with st.container(horizontal=True, gap="small"):
        for field, label in LINK_LABELS.items():
            url = getattr(p.links, field)
            if url:
                st.link_button(label, url, icon=ICON["link"], key=f"link_{p.id}_{field}")
