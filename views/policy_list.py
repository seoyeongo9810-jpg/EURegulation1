import streamlit as st

from src.components import filtered_policies, page_header, render_filter_notice, render_policy_card, today
from src.export import policies_to_frame, to_csv_bytes, to_excel_bytes
from src.loader import load_data
from src.theme import ICON

TAB_IN_FORCE = "시행 중인 법·정책"
TAB_PENDING = "제정 중·시행 예정"

result = load_data()
policies = filtered_policies(result)
now = today()

page_header("정책 목록", "시행 중인 법·정책과 제정 중인 법안을 나눠 보여줍니다.")
render_filter_notice(len(policies), len(result.policies))

in_force = [p for p in policies if p.status == "in_force"]
pending = [p for p in policies if p.status == "pending"]

frame = policies_to_frame(policies)
with st.container(horizontal=True, vertical_alignment="center", gap="small"):
    view = st.segmented_control(
        "보기", ["카드", "표"], default="카드", key="list_view", label_visibility="collapsed"
    )
    st.space("stretch")
    stamp = now.strftime("%Y%m%d")
    st.download_button(
        "CSV", to_csv_bytes(frame), f"eu_steel_policies_{stamp}.csv", "text/csv",
        icon=ICON["download"], disabled=frame.empty, on_click="ignore",
        help=f"현재 필터가 적용된 {len(policies)}건",
    )
    st.download_button(
        "Excel", to_excel_bytes(frame), f"eu_steel_policies_{stamp}.xlsx",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        icon=ICON["download"], disabled=frame.empty, on_click="ignore",
        help=f"현재 필터가 적용된 {len(policies)}건",
    )

tab_in_force, tab_pending = st.tabs([f"{TAB_IN_FORCE} ({len(in_force)})", f"{TAB_PENDING} ({len(pending)})"])
for tab, items in ((tab_in_force, in_force), (tab_pending, pending)):
    with tab:
        if not items:
            st.info("조건에 맞는 정책이 없습니다. 사이드바 필터를 조정해 보세요.")
        elif view == "표":
            st.dataframe(
                policies_to_frame(items).drop(columns=["ID", "요약", "주요 요구사항", "한국 철강사 시사점"]),
                hide_index=True,
                width="stretch",
                column_config={
                    "정책명": st.column_config.TextColumn(pinned=True),
                    "Commission 링크": st.column_config.LinkColumn(display_text="열기"),
                    "EUR-Lex 링크": st.column_config.LinkColumn(display_text="열기"),
                },
            )
        else:
            cols = st.columns(2)
            for i, p in enumerate(items):
                with cols[i % 2]:
                    render_policy_card(p, now)
