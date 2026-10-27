"""policies.yaml의 모든 링크(정책 링크 + 의견수렴 링크)를 점검한다.

사용법:
    python scripts/check_links.py [--timeout 20]

종료 코드: 깨진 링크가 있으면 1, 없으면 0.
202(봇 확인 페이지)와 403/429/5xx는 서버가 자동 요청을 막거나 일시 장애일 수 있어 '경고'로 분류한다
(종료 코드에 영향 없음, 브라우저로 직접 확인). 리다이렉트되는 링크는 최종 주소로 YAML을 갱신하는 것을 권장한다.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.loader import CHANGELOG_PATH, POLICIES_PATH, load_from_paths  # noqa: E402

HEADERS = {"User-Agent": "Mozilla/5.0 (EU steel policy tracker link checker)"}


@dataclass
class LinkResult:
    source: str
    url: str
    status: int | None
    final_url: str
    error: str = ""

    @property
    def verdict(self) -> str:
        if self.status is None:
            return "broken"
        if self.status == 202:
            # EUR-Lex 등은 자동 요청에 봇 확인 페이지(202)를 돌려줘 실제 내용 확인이 불가
            return "warn"
        if self.status < 400:
            return "ok"
        if self.status in (403, 429) or self.status >= 500:
            return "warn"
        return "broken"


def collect_links() -> list[tuple[str, str]]:
    result = load_from_paths(POLICIES_PATH, CHANGELOG_PATH)
    if result.errors:
        print("⚠ 데이터 검증 오류가 있어 일부 항목을 건너뜁니다:")
        for e in result.errors:
            print(f"  - {e}")
    links: list[tuple[str, str]] = []
    for p in result.policies:
        for field, url in p.links.model_dump().items():
            if url:
                links.append((f"{p.id}.links.{field}", url))
        for i, c in enumerate(p.consultations):
            if c.url:
                links.append((f"{p.id}.consultations[{i}]", c.url))
    return links


def check(source: str, url: str, timeout: float) -> LinkResult:
    try:
        # 일부 EU 사이트는 HEAD를 지원하지 않으므로 GET(stream)으로 확인
        with requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True, stream=True) as r:
            return LinkResult(source, url, r.status_code, r.url)
    except requests.RequestException as exc:
        return LinkResult(source, url, None, "", f"{type(exc).__name__}: {exc}")


def main() -> int:
    # Windows 콘솔(cp949)에서도 이모지·한글이 출력되도록
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--timeout", type=float, default=20)
    args = parser.parse_args()

    links = collect_links()
    print(f"링크 {len(links)}개 점검 중...\n")
    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda sl: check(*sl, args.timeout), links))

    icons = {"ok": "✅", "warn": "⚠️", "broken": "❌"}
    for r in sorted(results, key=lambda r: ("broken", "warn", "ok").index(r.verdict)):
        line = f"{icons[r.verdict]} [{r.status or '-'}] {r.source}  {r.url}"
        if r.final_url and r.final_url.rstrip("/") != r.url.rstrip("/"):
            line += f"\n      → 리다이렉트: {r.final_url}"
        if r.error:
            line += f"\n      → {r.error}"
        print(line)

    counts = {v: sum(r.verdict == v for r in results) for v in icons}
    print(f"\n정상 {counts['ok']} · 경고 {counts['warn']} · 깨짐 {counts['broken']} (총 {len(results)})")
    return 1 if counts["broken"] else 0


if __name__ == "__main__":
    sys.exit(main())
