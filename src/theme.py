"""색·아이콘 체계. 모든 페이지가 같은 의미에 같은 색을 쓰도록 여기서만 정의한다.

- 배지(st.badge)는 Streamlit 팔레트 이름을 쓰고, 실제 색은 .streamlit/config.toml의
  [theme.light]/[theme.dark]에서 정한다.
- 차트(Plotly)는 아래 HEX를 쓴다. 라이트·다크 배경 모두에서 읽히는 중간 톤이며,
  assets/style.css의 D-day·단계 표시도 같은 값을 쓴다.
- 색만으로 의미를 전달하지 않도록 배지·셀에는 항상 텍스트 라벨을 함께 표시한다.
"""

# 의미 → 배지 색 이름
BADGE = {
    "in_force": "green",     # 시행 중
    "pending": "blue",       # 제정 중·시행 예정
    "stage": "gray",         # 입법 단계
    "open": "violet",        # 의견수렴 진행 중
    "upcoming": "blue",      # 의견수렴 예정
    "closed": "gray",        # 의견수렴 마감
    "urgent": "red",         # 마감 임박 (30일 이내)
    "stale": "orange",       # 재확인 필요 (last_verified 14일 초과)
    "verify": "yellow",      # 확인 필요 (공식 출처 미확인 사항 있음)
    "tag": "gray",           # 요구사항·의견수렴 유형 태그
}
LEVEL_BADGE = {"high": "red", "medium": "orange", "low": "gray"}

# 차트용 HEX
CHART = {
    "in_force": "#3E8E41",
    "pending": "#3B78C2",
    "open": "#7B61C9",
    "upcoming": "#3B78C2",
    "closed": "#9AA0A8",
    "today": "#D64545",
}
LEVEL_HEX = {"high": "#D64545", "medium": "#E39B2D", "low": "#B7BEC8"}
FONT_FAMILY = "Noto Sans KR, Malgun Gothic, Apple SD Gothic Neo, sans-serif"

# Material 아이콘
ICON = {
    "dashboard": ":material/space_dashboard:",
    "list": ":material/format_list_bulleted:",
    "detail": ":material/article:",
    "consultation": ":material/forum:",
    "impact": ":material/grid_view:",
    "changelog": ":material/history:",
    "link": ":material/open_in_new:",
    "go": ":material/arrow_forward:",
    "verify": ":material/help:",
    "stale": ":material/schedule:",
    "download": ":material/download:",
    "filter": ":material/filter_alt:",
}
