import streamlit as st

from src.components import DETAIL_PAGE, md, page_header
from src.loader import load_data
from src.theme import ICON

result = load_data()
names = {p.id: p.name_ko for p in result.policies}

page_header("변경 이력", "정책 데이터 업데이트 기록 · 주 1회 업데이트")

if not result.changelog:
    st.info("변경 이력이 없습니다.")
for entry in result.changelog:
    with st.container(border=True):
        target = names.get(entry.policy_id, entry.policy_id) if entry.policy_id else "전체 데이터"
        st.markdown(f"**{entry.date.isoformat()}** · {md(target)}")
        st.markdown(md(entry.summary))
        if entry.policy_id in names:
            st.page_link(DETAIL_PAGE, label="정책 상세", query_params={"policy": entry.policy_id}, icon=ICON["go"])
