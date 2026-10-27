import streamlit as st

from src.charts import CHART_CONFIG, consultation_timeline
from src.components import filtered_policies, page_header, render_consultation, render_filter_notice, section, today
from src.loader import load_data
from src.models import CONSULTATION_STATUS_LABELS, consultation_status

result = load_data()
policies = filtered_policies(result)
now = today()

page_header("의견수렴 현황", "Have Your Say — Call for Evidence · Public Consultation · Draft act feedback")
render_filter_notice(len(policies), len(result.policies))

items = [(p, c, consultation_status(c, now)) for p in policies for c in p.consultations]
if not items:
    st.info("등록된 의견수렴이 없습니다.")
    st.stop()

groups = {s: [(p, c) for p, c, st_ in items if st_ == s] for s in ("open", "upcoming", "closed")}
with st.container(key="kpis"):
    cols = st.columns(3)
    for col, s in zip(cols, groups):
        col.metric(CONSULTATION_STATUS_LABELS[s], len(groups[s]), border=True)

order = {"open": lambda c: c.end, "upcoming": lambda c: c.start, "closed": lambda c: c.end}
tabs = st.tabs([f"{CONSULTATION_STATUS_LABELS[s]} ({len(groups[s])})" for s in groups])
for tab, s in zip(tabs, groups):
    with tab:
        entries = sorted(groups[s], key=lambda pc: order[s](pc[1]), reverse=(s == "closed"))
        if not entries:
            st.caption("해당 의견수렴이 없습니다.")
        for i, (p, c) in enumerate(entries):
            render_consultation(c, now, key=f"{s}_{i}", policy=p)

section("기간 보기")
with st.expander("전체 의견수렴 기간 차트", expanded=False):
    st.plotly_chart(consultation_timeline(items, now), width="stretch", config=CHART_CONFIG)
