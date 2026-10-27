from datetime import date

import pytest
from pydantic import ValidationError

from src.models import (
    Consultation,
    Policy,
    consultation_status,
    days_until_end,
    is_stale,
)


def make_policy(**overrides) -> dict:
    data = {
        "id": "sample",
        "name_ko": "샘플",
        "name_en": "Sample",
        "status": "in_force",
        "legal_form": "Regulation",
        "dg": "CLIMA",
        "category": ["carbon_pricing_trade"],
        "steel_relevance": "high",
        "summary": "요약",
        "impact": {
            "eu_producers": {"level": "high"},
            "non_eu_producers": {"level": "low"},
        },
        "links": {"commission": "https://climate.ec.europa.eu/x_en"},
        "last_verified": date(2026, 10, 1),
    }
    data.update(overrides)
    return data


def test_valid_policy():
    p = Policy.model_validate(make_policy())
    assert p.impact.korea_note is None


def test_pending_requires_stage():
    with pytest.raises(ValidationError, match="stage"):
        Policy.model_validate(make_policy(status="pending"))
    Policy.model_validate(make_policy(status="pending", stage="proposal"))


@pytest.mark.parametrize(
    "url",
    ["", "http://climate.ec.europa.eu/x", "https://example.com/x", "https://europa.eu.evil.com/x"],
)
def test_commission_link_must_be_official(url):
    with pytest.raises(ValidationError, match="commission"):
        Policy.model_validate(make_policy(links={"commission": url}))


def test_commission_link_required():
    with pytest.raises(ValidationError):
        Policy.model_validate(make_policy(links={"eurlex": "https://eur-lex.europa.eu"}))


def test_invalid_enum_rejected():
    with pytest.raises(ValidationError):
        Policy.model_validate(make_policy(steel_relevance="very_high"))


def test_unknown_field_rejected():
    with pytest.raises(ValidationError):
        Policy.model_validate(make_policy(typo_field=1))


def test_korea_note():
    p = Policy.model_validate(
        make_policy(
            impact={
                "eu_producers": {"level": "high"},
                "non_eu_producers": {"level": "low"},
                "korea_note": "열연 수출 영향",
            }
        )
    )
    assert p.impact.korea_note == "열연 수출 영향"


def consultation(start=date(2026, 10, 1), end=date(2026, 10, 31)) -> Consultation:
    return Consultation(type="call_for_evidence", title="t", start=start, end=end)


@pytest.mark.parametrize(
    "today, expected",
    [
        (date(2026, 9, 30), "upcoming"),
        (date(2026, 10, 1), "open"),
        (date(2026, 10, 31), "open"),
        (date(2026, 11, 1), "closed"),
    ],
)
def test_consultation_status(today, expected):
    assert consultation_status(consultation(), today) == expected


def test_days_until_end():
    c = consultation()
    assert days_until_end(c, date(2026, 10, 27)) == 4
    assert days_until_end(c, date(2026, 10, 31)) == 0
    assert days_until_end(c, date(2026, 11, 2)) == -2


def test_consultation_end_before_start_rejected():
    with pytest.raises(ValidationError):
        consultation(start=date(2026, 10, 31), end=date(2026, 10, 1))


@pytest.mark.parametrize("days, stale", [(13, False), (14, False), (15, True)])
def test_is_stale_boundary(days, stale):
    p = Policy.model_validate(make_policy(last_verified=date(2026, 10, 1)))
    assert is_stale(p, date.fromordinal(date(2026, 10, 1).toordinal() + days)) is stale
