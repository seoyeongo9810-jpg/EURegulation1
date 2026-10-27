"""앱 라우터. app.py와 테스트가 같은 구성을 쓰도록 분리했다.

페이지 폴더 이름을 pages/가 아닌 views/로 둔 이유: pages/가 있으면 Streamlit이 구형 자동 페이지
탐색을 함께 수행해, /dashboard 같은 주소로 바로 들어올 때 app.py(사이드바 필터 포함)를 거치지 않고
페이지 파일만 단독 실행된다.
"""

from __future__ import annotations

import streamlit as st

from src.components import VIEWS_DIR, inject_css, render_load_errors, render_sidebar
from src.loader import load_data
from src.theme import ICON

# (파일, 제목, 아이콘, url_path)
PAGE_SPECS = [
    ("dashboard.py", "대시보드", ICON["dashboard"], "dashboard"),
    ("policy_list.py", "정책 목록", ICON["list"], "policies"),
    ("policy_detail.py", "정책 상세", ICON["detail"], "detail"),
    ("consultations.py", "의견수렴 현황", ICON["consultation"], "consultations"),
    ("impact_matrix.py", "영향 매트릭스", ICON["impact"], "impact"),
    ("changelog.py", "변경 이력", ICON["changelog"], "changelog"),
]


def run_app(default: str = "dashboard.py") -> None:
    st.set_page_config(
        page_title="EU 철강 탄소중립 정책 트래커",
        page_icon=":material/factory:",
        layout="wide",
        initial_sidebar_state="auto",
    )
    inject_css()
    pages = [
        st.Page(VIEWS_DIR / file, title=title, icon=icon, url_path=url_path, default=(file == default))
        for file, title, icon, url_path in PAGE_SPECS
    ]
    nav = st.navigation(pages)

    result = load_data()
    render_sidebar(result)
    render_load_errors(result)

    nav.run()
