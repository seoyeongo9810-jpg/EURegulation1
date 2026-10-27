from src.loader import (
    CHANGELOG_PATH,
    POLICIES_PATH,
    load_from_paths,
    parse_changelog,
    parse_policies,
)
from tests.test_models import make_policy


SEED_IDS = {
    "cbam", "eu_ets", "ied", "espr", "cpr", "nzia", "red3", "climate_law_2040", "steel_trade_measure",
    "cbam_downstream", "cbam_export", "ets_review", "industrial_accelerator_act", "espr_steel",
    "steel_bref", "elv_regulation", "cbam_secondary_acts",
}


def test_policy_data_loads_without_errors():
    result = load_from_paths(POLICIES_PATH, CHANGELOG_PATH)
    assert result.errors == []
    assert result.changelog
    statuses = {p.status for p in result.policies}
    assert statuses == {"in_force", "pending"}


def test_prd_seed_policies_are_kept():
    """PRD 5장의 정책 17건은 삭제되지 않아야 한다 (상태는 바뀔 수 있음)."""
    ids = {p.id for p in load_from_paths(POLICIES_PATH, CHANGELOG_PATH).policies}
    assert SEED_IDS <= ids


def test_verify_needed_entries_explain_why():
    for p in load_from_paths(POLICIES_PATH, CHANGELOG_PATH).policies:
        if p.verify_needed:
            assert p.note, f"{p.id}: verify_needed인데 note(사유)가 없습니다"


def test_changelog_policy_ids_exist():
    result = load_from_paths(POLICIES_PATH, CHANGELOG_PATH)
    ids = {p.id for p in result.policies}
    for e in result.changelog:
        assert e.policy_id is None or e.policy_id in ids, e.policy_id


def test_invalid_entry_is_skipped_not_fatal():
    raw = [make_policy(id="good"), make_policy(id="bad", status="unknown"), "not a dict"]
    policies, errors = parse_policies(raw)
    assert [p.id for p in policies] == ["good"]
    assert len(errors) == 2
    assert "bad" in errors[0]


def test_duplicate_id_reported():
    policies, errors = parse_policies([make_policy(), make_policy()])
    assert len(policies) == 1
    assert any("중복" in e for e in errors)


def test_invalid_entry_referenced_by_others_counts_once():
    """깨진 항목을 다른 정책이 related로 가리켜도 오류는 1건 (1차 e2e B7에서 11건으로 부풀려졌던 문제)."""
    raw = [make_policy(id="broken", status="unknown"), make_policy(id="a", related=["broken"]),
           make_policy(id="b", related=["broken"])]
    policies, errors = parse_policies(raw)
    assert [p.id for p in policies] == ["a", "b"]
    assert len(errors) == 1 and "broken" in errors[0]


def test_unknown_related_id_reported():
    _, errors = parse_policies([make_policy(related=["missing"])])
    assert any("missing" in e for e in errors)


def test_non_list_root():
    policies, errors = parse_policies({"id": "x"})
    assert policies == [] and errors


def test_empty_file():
    assert parse_policies(None) == ([], [])


def test_missing_and_broken_files(tmp_path):
    broken = tmp_path / "broken.yaml"
    broken.write_text("- id: [unclosed", encoding="utf-8")
    result = load_from_paths(broken, tmp_path / "missing.yaml")
    assert result.policies == []
    assert any("YAML" in e for e in result.errors)
    assert any("찾을 수 없습니다" in e for e in result.errors)


def test_changelog_sorted_desc():
    entries, errors = parse_changelog(
        [{"date": "2026-01-01", "summary": "a"}, {"date": "2026-03-01", "summary": "b"}]
    )
    assert errors == []
    assert [e.summary for e in entries] == ["b", "a"]
