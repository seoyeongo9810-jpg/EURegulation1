import pandas as pd
import streamlit as st

from src.charts import CHART_CONFIG, impact_heatmap
from src.components import filtered_policies, page_header, render_filter_notice, section
from src.loader import load_data
from src.models import LEVEL_LABELS

result = load_data()
policies = filtered_policies(result)

page_header("영향 매트릭스", "정책별 EU 역내 · 역외 · 한국 철강사 영향도 (상 · 중 · 하)")
render_filter_notice(len(policies), len(result.policies))

if not policies:
    st.info("조건에 맞는 정책이 없습니다. 사이드바 필터를 조정해 보세요.")
    st.stop()

st.plotly_chart(impact_heatmap(policies), width="stretch", config=CHART_CONFIG)
st.caption("셀의 글자가 영향도입니다. 한국 철강사 영향도를 따로 입력하지 않은 정책은 역외 철강사 영향도를 따릅니다.")

section("비교표")
frame = pd.DataFrame(
    [
        {
            "정책": p.name_ko,
            "역내": LEVEL_LABELS[p.impact.eu_producers.level],
            "역외": LEVEL_LABELS[p.impact.non_eu_producers.level],
            "한국": LEVEL_LABELS[p.impact.korea_effective_level],
            "역외 직접 의무": p.impact.non_eu_producers.obligations,
            "한국 철강사 시사점": p.impact.korea_note or "",
        }
        for p in policies
    ]
)
st.dataframe(
    frame,
    hide_index=True,
    width="stretch",
    column_config={
        "정책": st.column_config.TextColumn(pinned=True, width="medium"),
        "역내": st.column_config.TextColumn(width="small"),
        "역외": st.column_config.TextColumn(width="small"),
        "한국": st.column_config.TextColumn(width="small"),
        "한국 철강사 시사점": st.column_config.TextColumn(width="large"),
    },
)
