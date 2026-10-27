"""Plotly 차트. 모든 차트는 apply_layout()으로 폰트·여백·범례를 통일한다."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from src.filters import TARGET_LABELS, target_level
from src.models import CATEGORY_LABELS, CONSULTATION_TYPE_LABELS, LEVEL_LABELS, STATUS_LABELS, Policy
from src.theme import CHART, FONT_FAMILY, LEVEL_HEX

TIMELINE_RANGE = (date(2023, 1, 1), date(2035, 12, 31))
CHART_CONFIG = {"displayModeBar": False, "responsive": True}
LEVEL_SCORE = {"high": 3, "medium": 2, "low": 1}


def short(text: str, limit: int = 22) -> str:
    """축 라벨용 줄임. 원문은 hover로 보여준다."""
    return text if len(text) <= limit else text[: limit - 1] + "…"


def apply_layout(fig: go.Figure, height: int) -> go.Figure:
    fig.update_layout(
        height=height,
        font=dict(family=FONT_FAMILY, size=12),
        margin=dict(l=8, r=8, t=36, b=8),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None),
        hoverlabel=dict(font_family=FONT_FAMILY),
    )
    fig.update_yaxes(title=None, automargin=True)
    fig.update_xaxes(title=None, automargin=True)
    return fig


def _dt(d: date) -> datetime:
    return datetime.combine(d, datetime.min.time())


def _add_today(fig: go.Figure, now: date) -> None:
    fig.add_shape(type="line", x0=_dt(now), x1=_dt(now), y0=0, y1=1, yref="paper",
                  line=dict(color=CHART["today"], dash="dot", width=1.5))
    # 범례와 겹치지 않도록 그래프 영역 안쪽(선 오른쪽 위)에 표시
    fig.add_annotation(x=_dt(now), y=1, yref="paper", text="오늘", showarrow=False, yanchor="top", xanchor="left",
                       xshift=3, font=dict(color=CHART["today"], size=11))


def milestone_figure(
    policies: list[Policy], now: date, group_by: str = "policy", fit: bool = False
) -> go.Figure | None:
    """마일스톤 타임라인. group_by='category'면 분야별로 묶어 행 수를 줄인다.

    fit=True(단일 정책 상세용)면 x축을 해당 일정 범위(+오늘)에 맞추고 행 라벨을 숨긴다.
    """
    rows = []
    for p in policies:
        row_label = CATEGORY_LABELS[p.category[0]] if group_by == "category" else short(p.name_ko)
        for m in p.milestones:
            if TIMELINE_RANGE[0] <= m.date <= TIMELINE_RANGE[1]:
                rows.append({"행": row_label, "정책": p.name_ko, "날짜": m.date, "내용": m.label, "상태": p.status})
    if not rows:
        return None
    df = pd.DataFrame(rows)
    fig = go.Figure()
    for status in ("in_force", "pending"):
        part = df[df["상태"] == status]
        if part.empty:
            continue
        fig.add_trace(
            go.Scatter(
                x=part["날짜"],
                y=part["행"],
                mode="markers",
                name=STATUS_LABELS[status],
                marker=dict(size=10, color=CHART[status], line=dict(width=1, color="rgba(255,255,255,0.6)")),
                customdata=part[["정책", "내용"]],
                hovertemplate="<b>%{customdata[0]}</b><br>%{x|%Y-%m-%d}<br>%{customdata[1]}<extra></extra>",
            )
        )
    _add_today(fig, now)
    if fit:
        start, end = min(df["날짜"].min(), now), max(df["날짜"].max(), now)
        pad = max((end - start).days * 0.06, 45)
        fig.update_xaxes(range=[_dt(start) - timedelta(days=pad), _dt(end) + timedelta(days=pad)], tickformat="%Y.%m")
        fig.update_yaxes(showticklabels=False)
        fig.update_traces(marker_size=13)
        return apply_layout(fig, 170)
    fig.update_xaxes(range=[_dt(TIMELINE_RANGE[0]), _dt(TIMELINE_RANGE[1])], dtick="M24", tickformat="%Y")
    fig.update_yaxes(autorange="reversed")
    return apply_layout(fig, max(220, 30 * df["행"].nunique() + 90))


HEATMAP_COLUMNS = {"eu": "EU 역내", "non_eu": "EU 역외", "korea": "한국"}  # 모바일에서 회전되지 않게 짧게


def impact_heatmap(policies: list[Policy]) -> go.Figure:
    targets = list(TARGET_LABELS)
    levels = [[target_level(p, t) for t in targets] for p in policies]
    fig = go.Figure(
        go.Heatmap(
            z=[[LEVEL_SCORE[lv] for lv in row] for row in levels],
            x=[HEATMAP_COLUMNS[t] for t in targets],
            y=[short(p.name_ko, 24) for p in policies],
            text=[[LEVEL_LABELS[lv] for lv in row] for row in levels],
            customdata=[[p.name_ko] * len(targets) for p in policies],
            texttemplate="%{text}",
            textfont=dict(color="#1C2430", size=13),
            colorscale=[[0, LEVEL_HEX["low"]], [0.5, LEVEL_HEX["medium"]], [1, LEVEL_HEX["high"]]],
            zmin=1,
            zmax=3,
            showscale=False,
            hovertemplate="<b>%{customdata}</b><br>%{x}: 영향도 %{text}<extra></extra>",
            xgap=3,
            ygap=3,
        )
    )
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(side="top", tickangle=0)
    return apply_layout(fig, max(260, 32 * len(policies) + 70))


def consultation_timeline(items: list[tuple[Policy, object, str]], now: date) -> go.Figure:
    """의견수렴 기간 막대. 축 라벨은 '정책명 · 유형'으로 짧게, 원문 제목은 hover."""
    status_label = {"open": "진행 중", "upcoming": "예정", "closed": "마감"}
    df = pd.DataFrame(
        [
            {
                "의견수렴": f"{short(p.name_ko, 20)} · {CONSULTATION_TYPE_LABELS[c.type]}",
                "제목": c.title,
                "정책": p.name_ko,
                "시작": c.start,
                "마감": c.end,
                "상태": status_label[s],
            }
            for p, c, s in items
        ]
    )
    fig = px.timeline(
        df, x_start="시작", x_end="마감", y="의견수렴", color="상태",
        hover_name="제목", hover_data={"정책": True, "의견수렴": False, "상태": False},
        color_discrete_map={"진행 중": CHART["open"], "예정": CHART["upcoming"], "마감": CHART["closed"]},
        category_orders={"상태": ["진행 중", "예정", "마감"]},
    )
    _add_today(fig, now)
    fig.update_yaxes(autorange="reversed")
    return apply_layout(fig, max(240, 26 * df["의견수렴"].nunique() + 90))
