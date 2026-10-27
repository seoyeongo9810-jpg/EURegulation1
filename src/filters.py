"""정책 목록 필터·정렬 (UI와 분리된 순수 함수)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

from src.models import Policy

Target = Literal["eu", "non_eu", "korea"]
SortKey = Literal["effective_date", "last_verified", "relevance"]

TARGET_LABELS = {"eu": "EU 역내 철강사", "non_eu": "EU 역외 철강사", "korea": "한국 철강사"}
SORT_LABELS = {
    "relevance": "관련도 높은 순",
    "effective_date": "시행일 최신순",
    "last_verified": "최근 확인일 순",
}
_LEVEL_RANK = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Filters:
    statuses: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
    targets: list[Target] = field(default_factory=list)
    relevance: list[str] = field(default_factory=list)
    keyword: str = ""
    sort: SortKey = "relevance"

    @property
    def active(self) -> bool:
        return bool(self.statuses or self.categories or self.targets or self.relevance or self.keyword.strip())


def target_level(p: Policy, target: Target) -> str:
    if target == "eu":
        return p.impact.eu_producers.level
    if target == "non_eu":
        return p.impact.non_eu_producers.level
    return p.impact.korea_effective_level


def _searchable_text(p: Policy) -> str:
    parts = [p.id, p.name_ko, p.name_en, p.legal_ref or "", p.dg, p.summary, p.scope, p.impact.korea_note or ""]
    parts += [r.text for r in p.requirements]
    return " ".join(parts).lower()


def matches(p: Policy, f: Filters) -> bool:
    if f.statuses and p.status not in f.statuses:
        return False
    if f.categories and not set(p.category) & set(f.categories):
        return False
    # 영향 대상: 선택한 대상 중 하나라도 영향도가 '중' 이상이면 포함
    if f.targets and not any(target_level(p, t) in ("high", "medium") for t in f.targets):
        return False
    if f.relevance and p.steel_relevance not in f.relevance:
        return False
    keywords = f.keyword.lower().split()
    if keywords:
        text = _searchable_text(p)
        if not all(k in text for k in keywords):
            return False
    return True


def sort_policies(policies: list[Policy], key: SortKey) -> list[Policy]:
    if key == "effective_date":
        # 시행일 없는 항목(제정 중 등)은 뒤로
        return sorted(policies, key=lambda p: (p.effective_date is None, -(p.effective_date or date.min).toordinal()))
    if key == "last_verified":
        return sorted(policies, key=lambda p: p.last_verified, reverse=True)
    return sorted(policies, key=lambda p: (-_LEVEL_RANK[p.steel_relevance], p.name_ko))


def apply_filters(policies: list[Policy], f: Filters) -> list[Policy]:
    return sort_policies([p for p in policies if matches(p, f)], f.sort)
