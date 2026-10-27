import streamlit as st

from src.charts import CHART_CONFIG, milestone_figure
from src.components import (
    DETAIL_PAGE,
    md,
    page_header,
    render_consultations,
    render_impact,
    render_links,
    render_policy_badges,
    render_requirements,
    render_stage_steps,
    section,
    today,
)
from src.loader import load_data
from src.models import CATEGORY_LABELS
from src.theme import ICON

result = load_data()
by_id = {p.id: p for p in result.policies}
now = today()

page_header("정책 상세")

if not by_id:
    st.warning("표시할 정책이 없습니다.")
    st.stop()

ids = list(by_id)
requested = st.query_params.get("policy")
if requested and requested not in by_id:
    st.warning(f"'{requested}'에 해당하는 정책이 없습니다. 아래에서 정책을 선택하세요.")
# URL(?policy=)이 바뀌어 들어온 경우(다른 페이지의 링크 등) 선택값을 URL에 맞춘다
if requested in by_id:
    st.session_state["detail_policy"] = requested
elif st.session_state.get("detail_policy") not in by_id:
    st.session_state["detail_policy"] = ids[0]


def _sync_url() -> None:
    st.query_params["policy"] = st.session_state["detail_policy"]


selected = st.selectbox(
    "정책 선택",
    ids,
    key="detail_policy",
    on_change=_sync_url,
    format_func=lambda i: by_id[i].name_ko,
)
st.query_params["policy"] = selected
p = by_id[selected]

# ---- 헤더: 정책명 · 상태 · 법령 · 링크 ----
with st.container(border=True):
    st.header(p.name_ko, anchor=False)
    st.caption(md(p.name_en))
    render_policy_badges(p, now)
    info = st.columns(4)
    # 값이 '-' 한 글자면 마크다운 setext 제목으로 렌더링되므로 '—' 사용
    info[0].markdown(f"**법령**  \n{md(p.legal_ref) or '—'}")
    info[1].markdown(f"**법적 형태 · 총국**  \n{p.legal_form} · DG {p.dg}")
    info[2].markdown(f"**분야**  \n{', '.join(CATEGORY_LABELS[c] for c in p.category)}")
    info[3].markdown(f"**시행일**  \n{p.effective_date.isoformat() if p.effective_date else '—'}")
    render_links(p)
    if p.verify_needed and p.note:
        with st.expander("확인 필요 사항", icon=ICON["verify"]):
            st.markdown(md(p.note))

section("개요")
st.markdown(md(p.summary))
if p.scope:
    st.markdown(f"**적용 대상** — {md(p.scope)}")

section("주요 요구사항")
render_requirements(p)

if p.status == "pending":
    section("입법 단계")
    render_stage_steps(p)

section("주요 일정")
fig = milestone_figure([p], now, fit=True)
if fig is None:
    st.caption("등록된 마일스톤이 없습니다.")
else:
    st.plotly_chart(fig, width="stretch", config=CHART_CONFIG)
    for m in sorted(p.milestones, key=lambda m: m.date):
        badge = ":gray-badge[완료]" if m.date <= now else ":blue-badge[예정]"
        st.markdown(f"{badge} **{m.date.isoformat()}** — {md(m.label)}")

section("의견수렴")
render_consultations(p, now)

section("철강사 영향 — 역내 · 역외 · 한국")
render_impact(p)

if p.sub_acts:
    section("관련 하위 법령")
    for s in p.sub_acts:
        st.markdown(f"- {md(s)}")

if p.related:
    section("관련 정책")
    with st.container(horizontal=True, gap="small"):
        for rid in p.related:
            if rid in by_id:
                st.page_link(DETAIL_PAGE, label=by_id[rid].name_ko, query_params={"policy": rid}, icon=ICON["go"])

st.divider()
st.caption(f"마지막 확인일 {p.last_verified.isoformat()} · 출처는 위 공식 링크와 데이터 파일 주석을 참고하세요.")
