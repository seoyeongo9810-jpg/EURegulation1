from datetime import timedelta
from html import escape

import streamlit as st

from src.charts import CHART_CONFIG, milestone_figure
from src.components import (
    DEADLINE_ALERT_DAYS,
    DETAIL_PAGE,
    closing_soon,
    filtered_policies,
    format_d_day,
    md,
    page_header,
    render_filter_notice,
    render_policy_badges,
    section,
    today,
)
from src.loader import load_data
from src.models import CONSULTATION_TYPE_LABELS, consultation_status
from src.theme import ICON

result = load_data()
policies = filtered_policies(result)
now = today()

page_header("대시보드", "EU 철강 탄소중립 정책 현황 요약")
render_filter_notice(len(policies), len(result.policies))

open_consultations = [c for p in policies for c in p.consultations if consultation_status(c, now) == "open"]
upcoming_milestones = [m for p in policies for m in p.milestones if now <= m.date <= now + timedelta(days=90)]

with st.container(key="kpis"):
    kpis = st.columns(4)
    kpis[0].metric("시행 중 정책", sum(p.status == "in_force" for p in policies), border=True)
    kpis[1].metric("제정 중 정책", sum(p.status == "pending" for p in policies), border=True)
    kpis[2].metric("진행 중 의견수렴", len(open_consultations), border=True)
    kpis[3].metric("90일 이내 마일스톤", len(upcoming_milestones), border=True)

with st.container(horizontal=True, vertical_alignment="bottom"):
    section("통합 타임라인 (2023~2035)")
    group = st.segmented_control(
        "묶음 기준", ["분야별", "정책별"], default="분야별", key="timeline_group", label_visibility="collapsed"
    )
fig = milestone_figure(policies, now, group_by="policy" if group == "정책별" else "category")
if fig is None:
    st.info("표시할 마일스톤이 없습니다.")
else:
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)

left, right = st.columns(2, gap="large")
with left:
    section(f"마감 임박 의견수렴 ({DEADLINE_ALERT_DAYS}일 이내)")
    alerts = closing_soon(policies, now)
    if not alerts:
        st.caption(f"{DEADLINE_ALERT_DAYS}일 이내 마감되는 의견수렴이 없습니다.")
    for p, c, d in alerts:
        with st.container(border=True):
            box, body = st.columns([1, 4], vertical_alignment="center")
            box.html(f'<div class="dday urgent">{format_d_day(d)}<small>마감 {c.end.isoformat()}</small></div>')
            with body:
                st.markdown(f"**{md(p.name_ko)}** · {CONSULTATION_TYPE_LABELS[c.type]}")
                st.html(f'<div class="card-sub" title="{escape(c.title)}">{escape(c.title)}</div>')
                st.page_link(DETAIL_PAGE, label="정책 상세", query_params={"policy": p.id}, icon=ICON["go"])

with right:
    section("최근 확인·변경된 정책")
    latest_change = {}
    for entry in result.changelog:  # 최신순
        if entry.policy_id and entry.policy_id not in latest_change:
            latest_change[entry.policy_id] = entry
    recent = sorted(
        policies,
        key=lambda p: max(p.last_verified, latest_change[p.id].date if p.id in latest_change else p.last_verified),
        reverse=True,
    )[:5]
    if not recent:
        st.caption("표시할 정책이 없습니다.")
    for p in recent:
        with st.container(border=True):
            st.markdown(f"**{md(p.name_ko)}**")
            render_policy_badges(p, now, show_stage=False)
            change = latest_change.get(p.id)
            if change:
                st.caption(md(f"{change.date.isoformat()} 변경: {change.summary}"))
            else:
                st.caption(f"마지막 확인 {p.last_verified.isoformat()}")
            st.page_link(DETAIL_PAGE, label="정책 상세", query_params={"policy": p.id}, icon=ICON["go"])
