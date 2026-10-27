"""정책 데이터 스키마 (PRD 6장) 및 날짜 기반 파생값 계산.

의견수렴 상태·D-day·재확인 필요 여부는 YAML에 저장하지 않고,
오늘 날짜(today)를 인자로 받아 계산한다.
"""

from __future__ import annotations

from datetime import date
from typing import Literal, Optional
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# 주 1회 업데이트 기준: 업데이트 2회 누락(14일 초과) 시 재확인 필요 (PRD 13장 결정사항)
STALE_THRESHOLD_DAYS = 14

Status = Literal["in_force", "pending"]
LegislativeStage = Literal[
    "preparation",        # 준비 연구·기술작업반 등
    "call_for_evidence",
    "consultation",
    "proposal",           # Commission 제안
    "trilogue",           # 유럽의회·이사회 협상
    "agreed",             # 정치적 합의
    "adopted",            # 채택·관보 게재
]
LegalForm = Literal[
    "Regulation",
    "Directive",
    "Delegated Act",
    "Implementing Act",
    "Decision",
    "Communication",
    "Other",
]
Category = Literal[
    "carbon_pricing_trade",   # 탄소가격·무역
    "product_footprint",      # 제품·탄소발자국
    "industrial_emissions",   # 산업배출
    "energy_hydrogen",        # 에너지·수소
    "procurement_market",     # 공공조달·시장창출
    "funding_support",        # 지원·보조금
    "climate_framework",      # 기후목표 프레임워크
]
Level = Literal["high", "medium", "low"]
RequirementType = Literal[
    "carbon_footprint",   # 탄소발자국/내재배출량 산정
    "mrv",                # 모니터링·보고·검증
    "certificate",        # 인증서/배출권 구매
    "product_info",       # 제품 성능·정보 요건(DPP 등)
    "labelling",          # 라벨링
    "bat_limits",         # BAT/배출한도
    "procurement",        # 공공조달 기준
    "trade_measure",      # 무역 조치(쿼터·관세)
]
ConsultationType = Literal["call_for_evidence", "public_consultation", "draft_act_feedback"]
ConsultationStatus = Literal["upcoming", "open", "closed"]

# 화면 표시용 한국어 라벨
STATUS_LABELS = {"in_force": "시행 중", "pending": "제정 중·시행 예정"}
STAGE_LABELS = {
    "preparation": "준비·연구",
    "call_for_evidence": "Call for Evidence",
    "consultation": "공개협의",
    "proposal": "Commission 제안",
    "trilogue": "의회·이사회 협상",
    "agreed": "정치적 합의",
    "adopted": "채택·관보 게재",
}
# 입법 단계 진행 바 순서 (마지막 단계는 '시행')
STAGE_ORDER = [
    "preparation",
    "call_for_evidence",
    "consultation",
    "proposal",
    "trilogue",
    "agreed",
    "adopted",
]
CATEGORY_LABELS = {
    "carbon_pricing_trade": "탄소가격·무역",
    "product_footprint": "제품·탄소발자국",
    "industrial_emissions": "산업배출",
    "energy_hydrogen": "에너지·수소",
    "procurement_market": "공공조달·시장창출",
    "funding_support": "지원·보조금",
    "climate_framework": "기후목표",
}
LEVEL_LABELS = {"high": "상", "medium": "중", "low": "하"}
REQUIREMENT_LABELS = {
    "carbon_footprint": "탄소발자국/내재배출량 산정",
    "mrv": "MRV(모니터링·보고·검증)",
    "certificate": "인증서/배출권 구매",
    "product_info": "제품 성능·정보 요건(DPP 등)",
    "labelling": "라벨링",
    "bat_limits": "BAT/배출한도",
    "procurement": "공공조달 기준",
    "trade_measure": "무역 조치(쿼터·관세)",
}
CONSULTATION_TYPE_LABELS = {
    "call_for_evidence": "Call for Evidence",
    "public_consultation": "Public Consultation",
    "draft_act_feedback": "Draft act feedback",
}
CONSULTATION_STATUS_LABELS = {"upcoming": "예정", "open": "진행 중", "closed": "마감"}


class _Base(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Requirement(_Base):
    type: RequirementType
    text: str


class Milestone(_Base):
    date: date
    label: str


class Consultation(_Base):
    type: ConsultationType
    title: str
    start: date
    end: date
    summary: str = ""
    url: Optional[str] = None

    @model_validator(mode="after")
    def _check_period(self) -> "Consultation":
        if self.end < self.start:
            raise ValueError(f"의견수렴 마감일({self.end})이 시작일({self.start})보다 빠릅니다")
        return self


class ImpactDetail(_Base):
    level: Level
    obligations: str = ""
    costs: str = ""
    preparation: str = ""
    opportunities: str = ""


class Impact(_Base):
    eu_producers: ImpactDetail
    non_eu_producers: ImpactDetail
    korea_note: Optional[str] = None  # 한국 철강사 시사점 (PRD 13장 결정사항)
    korea_level: Optional[Level] = None  # 없으면 역외 철강사 영향도를 따른다

    @property
    def korea_effective_level(self) -> Level:
        return self.korea_level or self.non_eu_producers.level


def _is_europa_url(url: str) -> bool:
    host = urlparse(url).hostname or ""
    return urlparse(url).scheme == "https" and (host == "europa.eu" or host.endswith(".europa.eu"))


class Links(_Base):
    commission: str
    eurlex: Optional[str] = None
    have_your_say: Optional[str] = None
    oeil: Optional[str] = None
    guidance: Optional[str] = None

    @field_validator("commission")
    @classmethod
    def _check_commission(cls, v: str) -> str:
        if not v or not _is_europa_url(v):
            raise ValueError("commission 링크는 https://*.europa.eu 공식 페이지여야 합니다")
        return v


class Policy(_Base):
    id: str = Field(pattern=r"^[a-z0-9_]+$")
    name_ko: str
    name_en: str
    status: Status
    stage: Optional[LegislativeStage] = None
    legal_form: LegalForm
    legal_ref: Optional[str] = None
    dg: str
    category: list[Category] = Field(min_length=1)
    steel_relevance: Level
    effective_date: Optional[date] = None  # 시행(적용)일
    summary: str
    requirements: list[Requirement] = Field(default_factory=list)
    scope: str = ""
    sub_acts: list[str] = Field(default_factory=list)  # 관련 위임·이행법령
    milestones: list[Milestone] = Field(default_factory=list)
    consultations: list[Consultation] = Field(default_factory=list)
    impact: Impact
    links: Links
    related: list[str] = Field(default_factory=list)
    verify_needed: bool = False
    note: Optional[str] = None
    last_verified: date

    @model_validator(mode="after")
    def _check_stage(self) -> "Policy":
        if self.status == "pending" and self.stage is None:
            raise ValueError("제정 중(pending) 정책은 stage(입법 단계)가 필요합니다")
        return self


class ChangelogEntry(_Base):
    date: date
    summary: str
    policy_id: Optional[str] = None
    author: Optional[str] = None


# ---- 날짜 기반 파생값 ----

def consultation_status(c: Consultation, today: date) -> ConsultationStatus:
    if today < c.start:
        return "upcoming"
    if today <= c.end:
        return "open"
    return "closed"


def days_until_end(c: Consultation, today: date) -> int:
    """마감까지 남은 일수 (D-day). 마감 당일은 0, 마감 후는 음수."""
    return (c.end - today).days


def stage_progress(p: Policy) -> tuple[int, int]:
    """(현재 단계 번호, 전체 단계 수). 시행 중이면 마지막 단계(시행)로 본다."""
    total = len(STAGE_ORDER) + 1
    if p.status == "in_force":
        return total, total
    return STAGE_ORDER.index(p.stage) + 1, total


def is_stale(p: Policy, today: date, threshold_days: int = STALE_THRESHOLD_DAYS) -> bool:
    """last_verified 후 threshold_days를 초과하면 재확인 필요."""
    return (today - p.last_verified).days > threshold_days
