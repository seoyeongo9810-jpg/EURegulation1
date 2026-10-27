"""YAML 데이터 로드 및 검증.

검증에 실패한 항목은 앱을 중단시키지 않고 건너뛴 뒤 오류 목록으로 반환한다.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import streamlit as st
import yaml
from pydantic import BaseModel, ValidationError

from src.models import ChangelogEntry, Policy

# EU_POLICY_DATA_DIR: 다른 데이터 폴더로 앱을 띄울 때 사용 (e2e 테스트에서 실제 data/를 건드리지 않기 위함)
DATA_DIR = Path(os.environ.get("EU_POLICY_DATA_DIR") or Path(__file__).resolve().parent.parent / "data")
POLICIES_PATH = DATA_DIR / "policies.yaml"
CHANGELOG_PATH = DATA_DIR / "changelog.yaml"


@dataclass
class LoadResult:
    policies: list[Policy] = field(default_factory=list)
    changelog: list[ChangelogEntry] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


def _format_error(source: str, label: str, exc: ValidationError) -> str:
    details = "; ".join(
        f"{'.'.join(str(p) for p in e['loc']) or '(항목)'}: {e['msg']}" for e in exc.errors()
    )
    return f"[{source}] {label} — {details}"


def _parse_list(raw: Any, model: type[BaseModel], source: str) -> tuple[list, list[str]]:
    if raw is None:
        return [], []
    if not isinstance(raw, list):
        return [], [f"[{source}] 최상위 구조가 목록(list)이 아닙니다"]
    items, errors = [], []
    for i, entry in enumerate(raw):
        label = f"#{i + 1}"
        if isinstance(entry, dict) and entry.get("id"):
            label += f" ({entry['id']})"
        if not isinstance(entry, dict):
            errors.append(f"[{source}] {label} — 항목이 매핑(dict)이 아닙니다")
            continue
        try:
            items.append(model.model_validate(entry))
        except ValidationError as exc:
            errors.append(_format_error(source, label, exc))
    return items, errors


def parse_policies(raw: Any) -> tuple[list[Policy], list[str]]:
    policies, errors = _parse_list(raw, Policy, "policies.yaml")
    seen: set[str] = set()
    unique: list[Policy] = []
    for p in policies:
        if p.id in seen:
            errors.append(f"[policies.yaml] 중복된 id '{p.id}' — 뒤의 항목은 무시합니다")
            continue
        seen.add(p.id)
        unique.append(p)
    # 검증에 실패해 빠진 항목을 가리키는 related는 따로 오류로 세지 않는다
    # (항목 하나가 깨졌을 때 경고 수가 부풀려지지 않도록). 파일 어디에도 없는 id만 보고한다.
    raw_ids = {e.get("id") for e in raw if isinstance(e, dict)} if isinstance(raw, list) else set()
    for p in unique:
        for rel in p.related:
            if rel not in raw_ids:
                errors.append(f"[policies.yaml] '{p.id}'의 related에 없는 id '{rel}'가 있습니다")
    return unique, errors


def parse_changelog(raw: Any) -> tuple[list[ChangelogEntry], list[str]]:
    entries, errors = _parse_list(raw, ChangelogEntry, "changelog.yaml")
    return sorted(entries, key=lambda e: e.date, reverse=True), errors


def _read_yaml(path: Path) -> tuple[Any, list[str]]:
    try:
        with path.open(encoding="utf-8") as f:
            return yaml.safe_load(f), []
    except FileNotFoundError:
        return None, [f"[{path.name}] 파일을 찾을 수 없습니다"]
    except yaml.YAMLError as exc:
        return None, [f"[{path.name}] YAML 문법 오류: {exc}"]


def load_from_paths(policies_path: Path, changelog_path: Path) -> LoadResult:
    raw_p, err_p = _read_yaml(policies_path)
    raw_c, err_c = _read_yaml(changelog_path)
    policies, perr = parse_policies(raw_p)
    changelog, cerr = parse_changelog(raw_c)
    return LoadResult(policies, changelog, err_p + perr + err_c + cerr)


@st.cache_data(show_spinner=False)
def _load_cached(policies_mtime: float, changelog_mtime: float) -> LoadResult:
    return load_from_paths(POLICIES_PATH, CHANGELOG_PATH)


def _mtime(path: Path) -> float:
    return path.stat().st_mtime if path.exists() else 0.0


def load_data() -> LoadResult:
    """앱에서 사용하는 진입점. 파일 수정 시각을 캐시 키로 써서 YAML 수정이 바로 반영된다."""
    return _load_cached(_mtime(POLICIES_PATH), _mtime(CHANGELOG_PATH))
