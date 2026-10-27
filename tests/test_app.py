"""Streamlit AppTest 기반 페이지 테스트 (실제 data/*.yaml 사용)."""

from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from src.components import closing_soon
from src.loader import CHANGELOG_PATH, POLICIES_PATH, load_from_paths
from src.navigation import PAGE_SPECS
from src.models import Consultation, Policy, stage_progress
from tests.test_models import make_policy

PAGES = [file for file, *_ in PAGE_SPECS]

DATA = load_from_paths(POLICIES_PATH, CHANGELOG_PATH)
N_IN_FORCE = sum(p.status == "in_force" for p in DATA.policies)
N_PENDING = sum(p.status == "pending" for p in DATA.policies)


def app() -> AppTest:
    """app.py 라우터 + 공통 사이드바 (기본 페이지: 대시보드)."""
    return AppTest.from_file("app.py", default_timeout=30).run()


def page(file: str, query: dict | None = None, state: dict | None = None) -> AppTest:
    """실제 라우터(run_app)를 해당 페이지를 기본 페이지로 지정해 실행한다.

    AppTest.switch_page는 pages/ 자동 탐색에 의존해 views/ 구조에서는 동작하지 않는다.
    사이드바 필터 값은 session_state로 주입한다 (실제 브라우저 동작은 4단계 e2e에서 검증).
    """
    script = f"from src.navigation import run_app\nrun_app(default={file!r})"
    at = AppTest.from_string(script, default_timeout=30)
    for k, v in (query or {}).items():
        at.query_params[k] = v
    for k, v in (state or {}).items():
        at.session_state[k] = v
    return at.run()


def test_router_renders_dashboard_and_sidebar():
    at = app()
    assert not at.exception, at.exception
    assert at.title[0].value == "대시보드"
    assert at.sidebar.multiselect(key="f_statuses")
    assert any("사내용" in c.value for c in at.sidebar.caption)


@pytest.mark.parametrize("path", PAGES)
def test_page_renders(path):
    at = page(path)
    assert not at.exception, at.exception
    assert at.title


@pytest.mark.parametrize("policy_id", [p.id for p in DATA.policies])
def test_every_policy_detail_renders(policy_id):
    at = page("policy_detail.py", query={"policy": policy_id})
    assert not at.exception, at.exception
    policy = next(p for p in DATA.policies if p.id == policy_id)
    assert at.header[0].value == policy.name_ko


def test_policy_list_tabs():
    at = page("policy_list.py")
    labels = [t.label for t in at.tabs]
    assert labels == [f"시행 중인 법·정책 ({N_IN_FORCE})", f"제정 중·시행 예정 ({N_PENDING})"]


def test_status_filter_applies_to_list():
    at = page("policy_list.py", state={"f_statuses": ["pending"]})
    assert [t.label for t in at.tabs] == ["시행 중인 법·정책 (0)", f"제정 중·시행 예정 ({N_PENDING})"]
    notice = f"전체 {len(DATA.policies)}건 중 {N_PENDING}건 표시"
    assert any(notice in c.value for c in at.caption)


@pytest.mark.parametrize("path", PAGES)
def test_pages_survive_empty_filter_result(path):
    at = page(path, state={"f_keyword": "존재하지않는검색어xyz"})
    assert not at.exception, at.exception


def test_filter_with_no_results_shows_empty_state():
    at = page("policy_list.py", state={"f_keyword": "존재하지않는검색어xyz"})
    assert any("조건에 맞는 정책이 없습니다" in i.value for i in at.info)


@pytest.mark.parametrize("group", ["분야별", "정책별"])
def test_dashboard_timeline_grouping(group):
    at = page("dashboard.py", state={"timeline_group": group})
    assert not at.exception, at.exception


def test_table_view():
    at = page("policy_list.py", state={"list_view": "표"})
    assert not at.exception, at.exception
    assert at.dataframe


def test_detail_unknown_policy_id_shows_warning():
    at = page("policy_detail.py", query={"policy": "does_not_exist"})
    assert not at.exception
    assert any("does_not_exist" in w.value for w in at.warning)


def test_detail_follows_new_query_param():
    ids = [p.id for p in DATA.policies]
    at = page("policy_detail.py", query={"policy": ids[0]})
    assert at.selectbox(key="detail_policy").value == ids[0]
    at.query_params["policy"] = ids[1]
    at.run()
    assert at.selectbox(key="detail_policy").value == ids[1]


def test_detail_selectbox_updates_url():
    ids = [p.id for p in DATA.policies]
    at = page("policy_detail.py", query={"policy": ids[0]})
    at.selectbox(key="detail_policy").set_value(ids[2]).run()
    assert at.query_params["policy"] == [ids[2]]
    assert at.header[0].value == DATA.policies[2].name_ko


@pytest.mark.parametrize("path", PAGES)
def test_no_calculator_ui(path):
    """PRD 13장: 탄소발자국·CBAM 비용 계산 기능은 만들지 않는다."""
    assert not page(path).number_input


# ---- 순수 함수 ----

def test_stage_progress():
    pending = Policy.model_validate(make_policy(status="pending", stage="proposal"))
    assert stage_progress(pending) == (4, 8)
    assert stage_progress(Policy.model_validate(make_policy())) == (8, 8)


def test_closing_soon_window():
    def c(end):
        return Consultation(type="public_consultation", title=str(end), start=date(2026, 9, 1), end=end)

    p = Policy.model_validate(
        make_policy(consultations=[
            c(date(2026, 11, 26)).model_dump(),  # D-30 → 포함
            c(date(2026, 11, 27)).model_dump(),  # D-31 → 제외
            c(date(2026, 10, 26)).model_dump(),  # 마감 → 제외
            c(date(2026, 10, 27)).model_dump(),  # D-Day → 포함
        ])
    )
    got = [(cons.title, d) for _, cons, d in closing_soon([p], date(2026, 10, 27))]
    assert got == [("2026-10-27", 0), ("2026-11-26", 30)]


def test_md_escapes_markdown_specials():
    from src.components import md

    assert md("2031~2040") == r"2031\~2040"  # 취소선 방지
    assert md("$5 and $6") == r"\$5 and \$6"  # 수식 방지
    assert md(None) == ""
