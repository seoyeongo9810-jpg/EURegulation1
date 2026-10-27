from datetime import date

import pandas as pd

from src.export import policies_to_frame, to_csv_bytes, to_excel_bytes
from src.filters import Filters, apply_filters, matches, sort_policies
from src.models import Policy
from tests.test_models import make_policy


def policy(**kw) -> Policy:
    return Policy.model_validate(make_policy(**kw))


A = policy(
    id="a", name_ko="탄소국경조정", steel_relevance="high", effective_date=date(2023, 10, 1),
    last_verified=date(2026, 10, 1),
    impact={"eu_producers": {"level": "low"}, "non_eu_producers": {"level": "high"}, "korea_note": "열연 수출"},
)
B = policy(
    id="b", name_ko="배출권", status="pending", stage="proposal", category=["industrial_emissions"],
    steel_relevance="low", last_verified=date(2026, 10, 20),
    impact={"eu_producers": {"level": "high"}, "non_eu_producers": {"level": "low"}, "korea_level": "medium"},
)
C = policy(id="c", name_ko="가나다", steel_relevance="medium", effective_date=date(2025, 1, 1),
           last_verified=date(2026, 9, 1))


def ids(policies):
    return [p.id for p in policies]


def test_no_filter_returns_all_sorted_by_relevance():
    assert ids(apply_filters([B, C, A], Filters())) == ["a", "c", "b"]


def test_status_and_category():
    assert ids(apply_filters([A, B, C], Filters(statuses=["pending"]))) == ["b"]
    assert ids(apply_filters([A, B, C], Filters(categories=["industrial_emissions"]))) == ["b"]


def test_target_filter_uses_medium_or_higher():
    # C는 make_policy 기본값(역내 high)
    assert ids(apply_filters([A, B, C], Filters(targets=["eu"]))) == ["c", "b"]
    assert set(ids(apply_filters([A, B, C], Filters(targets=["non_eu"])))) == {"a"}
    # 한국: korea_level 우선, 없으면 역외 영향도
    assert set(ids(apply_filters([A, B, C], Filters(targets=["korea"])))) == {"a", "b"}


def test_keyword_is_case_insensitive_and_and_combined():
    assert matches(A, Filters(keyword="SAMPLE"))  # name_en
    assert matches(A, Filters(keyword="열연"))  # korea_note
    assert not matches(A, Filters(keyword="열연 없는단어"))


def test_sorting():
    assert ids(sort_policies([A, B, C], "effective_date")) == ["c", "a", "b"]  # 시행일 없는 b는 맨 뒤
    assert ids(sort_policies([A, B, C], "last_verified")) == ["b", "a", "c"]


def test_filters_active_flag():
    assert not Filters().active
    assert not Filters(keyword="   ").active
    assert Filters(relevance=["high"]).active


def test_export_csv_has_bom_and_korean():
    df = policies_to_frame([A, B])
    data = to_csv_bytes(df)
    assert data.startswith(b"\xef\xbb\xbf")
    assert "탄소국경조정" in data.decode("utf-8-sig")
    assert df.loc[1, "한국 영향도"] == "중"


def test_export_excel_roundtrip(tmp_path):
    path = tmp_path / "out.xlsx"
    path.write_bytes(to_excel_bytes(policies_to_frame([A, B, C])))
    df = pd.read_excel(path)
    assert len(df) == 3
    assert df.loc[0, "정책명"] == "탄소국경조정"
