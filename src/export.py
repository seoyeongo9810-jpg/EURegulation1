"""필터된 정책 목록 내보내기 (CSV/Excel)."""

from __future__ import annotations

from io import BytesIO

import pandas as pd

from src.models import (
    CATEGORY_LABELS,
    LEVEL_LABELS,
    REQUIREMENT_LABELS,
    STAGE_LABELS,
    STATUS_LABELS,
    Policy,
)


def policies_to_frame(policies: list[Policy]) -> pd.DataFrame:
    rows = []
    for p in policies:
        rows.append(
            {
                "ID": p.id,
                "정책명": p.name_ko,
                "영문명": p.name_en,
                "상태": STATUS_LABELS[p.status],
                "입법 단계": STAGE_LABELS[p.stage] if p.stage else "",
                "법적 형태": p.legal_form,
                "법령": p.legal_ref or "",
                "담당 총국": p.dg,
                "분야": ", ".join(CATEGORY_LABELS[c] for c in p.category),
                "철강 관련도": LEVEL_LABELS[p.steel_relevance],
                "시행일": p.effective_date.isoformat() if p.effective_date else "",
                "요약": p.summary.strip(),
                "주요 요구사항": "\n".join(f"[{REQUIREMENT_LABELS[r.type]}] {r.text}" for r in p.requirements),
                "역내 영향도": LEVEL_LABELS[p.impact.eu_producers.level],
                "역외 영향도": LEVEL_LABELS[p.impact.non_eu_producers.level],
                "한국 영향도": LEVEL_LABELS[p.impact.korea_effective_level],
                "한국 철강사 시사점": p.impact.korea_note or "",
                "Commission 링크": p.links.commission,
                "EUR-Lex 링크": p.links.eurlex or "",
                "확인 필요": "예" if p.verify_needed else "",
                "마지막 확인일": p.last_verified.isoformat(),
            }
        )
    return pd.DataFrame(rows)


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    # utf-8-sig: Excel에서 열어도 한글이 깨지지 않도록 BOM 포함
    return df.to_csv(index=False).encode("utf-8-sig")


def to_excel_bytes(df: pd.DataFrame) -> bytes:
    buf = BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="정책 목록")
    return buf.getvalue()
