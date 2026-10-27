# EU 철강 탄소중립 정책 트래커

EU에서 시행 중이거나 제정 중인 철강 관련 탄소중립 정책을 한 화면에서 확인하는 **사내용** Streamlit 앱입니다.
요구사항은 상위 폴더의 `PRD.md`를 참고하세요. 13장 아래에 적힌 결정사항이 PRD 본문보다 우선합니다.

## 로컬 실행

Python 3.11 이상이 필요합니다.

```bash
pip install -r requirements.txt
streamlit run app.py
```

브라우저에서 http://localhost:8501 로 접속합니다.
정책 상세는 `http://localhost:8501/detail?policy=<정책 id>` 형식으로 바로 열 수 있습니다.

## 테스트

```bash
pytest                                                # 전체
pytest tests/test_filters.py                          # 파일 단위
pytest tests/test_models.py::test_is_stale_boundary   # 단일 테스트
python scripts/check_links.py                         # 정책 링크 점검 (깨진 링크가 있으면 종료 코드 1)
```

`tests/test_app.py`는 Streamlit `AppTest`로 실제 라우터를 띄워 페이지별로 렌더링을 확인합니다.

### 브라우저 E2E 테스트 (Playwright)

```bash
pip install -r requirements-dev.txt
python -m playwright install chromium
pytest -m e2e tests/e2e                       # 약 5분, 테스트용 Streamlit 서버를 직접 띄움
pytest -m "e2e and not network" tests/e2e     # 외부 링크 점검 제외
```

- PRD 수용 기준(A), 기능·버그 탐색(B), 반응형·테마(C), 데이터 정합성(D)을 검증합니다. 결과는 `QA_REPORT.md`를 참고하세요.
- 데이터를 바꿔야 하는 테스트는 임시 폴더에 복사한 데이터(`EU_POLICY_DATA_DIR`)로 별도 서버를 띄우므로 `data/`는 바뀌지 않습니다.
- 스크린샷은 `tests/e2e/screenshots/`, 측정값은 `tests/e2e/results/`에 생성됩니다(저장소에는 올리지 않음).

## 구조

| 경로 | 역할 |
|---|---|
| `app.py` | 진입점. `src/navigation.py`의 `run_app()` 호출 |
| `src/navigation.py` | 페이지 등록(`st.navigation`), 공통 사이드바·데이터 오류 경고 |
| `views/` | 대시보드, 정책 목록, 정책 상세, 의견수렴, 영향 매트릭스, 변경 이력 |
| `src/models.py` | pydantic 스키마, 한국어 라벨, 날짜 기반 계산(의견수렴 상태, D-day, 재확인 필요, 입법 단계) |
| `src/filters.py` | 사이드바 필터·정렬 (순수 함수) |
| `src/components.py` | 공통 UI (사이드바, 배지, 카드, 영향 비교, 타임라인·히트맵) |
| `src/export.py` | CSV(utf-8-sig)·Excel 내보내기 |
| `src/loader.py` | YAML 로드·검증. 잘못된 항목은 건너뛰고 오류 목록으로 반환 |
| `data/policies.yaml` | 정책 데이터 |
| `data/changelog.yaml` | 데이터 변경 이력 |
| `scripts/check_links.py` | 링크 유효성 점검 |

> 페이지 폴더가 `pages/`가 아니라 `views/`인 이유: `pages/` 폴더가 있으면 Streamlit이 자동 페이지 탐색을 함께 수행해서,
> `/dashboard` 같은 주소로 바로 들어올 때 사이드바 필터 없이 페이지 파일만 실행됩니다.

## 주 1회 데이터 업데이트 절차

정책 데이터는 **매주 1회** 업데이트합니다. `last_verified`가 14일을 넘은 정책에는 화면에 "⚠ 재확인 필요" 배지가 표시됩니다.

1. **확인 순서** (정책마다)
   1. 앱의 **의견수렴 현황**과 사이드바 **마감 임박 의견수렴**을 먼저 봅니다. 진행 중인 의견수렴의 마감일이 바뀌지 않았는지 확인합니다.
   2. 제정 중 법안: [유럽의회 OEIL](https://oeil.secure.europarl.europa.eu) 절차 페이지에서 입법 단계(제안 → 협상 → 합의 → 채택)가 바뀌었는지 확인합니다.
   3. 새 의견수렴: [Have Your Say](https://ec.europa.eu/info/law/better-regulation/have-your-say_en)에서 CBAM, ETS, steel, ecodesign 등으로 검색합니다.
   4. 채택된 법령: [EUR-Lex](https://eur-lex.europa.eu)에서 관보 게재 여부와 법령 번호를 확인합니다.
   5. 각 정책의 Commission 페이지에서 가이던스·FAQ 변경을 확인합니다.
2. **YAML 수정** (`data/policies.yaml`)
   - 바뀐 내용을 반영하고, 확인한 정책은 `last_verified`를 확인한 날짜로 바꿉니다. 내용이 그대로여도 확인했다면 날짜를 갱신합니다.
   - 채택·시행된 법안은 `status: in_force`로 옮기고 `stage`를 지웁니다.
   - 확인하지 못한 사항은 `verify_needed: true`와 `note`(사유)를 남깁니다. 추측으로 날짜나 번호를 채우지 않습니다.
   - 필드와 허용값은 `src/models.py`를 참고합니다. 의견수렴 상태와 D-day는 앱이 계산하므로 적지 않습니다.
3. **변경 이력 기록** (`data/changelog.yaml`): 날짜, `policy_id`, 변경 요약을 추가합니다.
4. **점검**
   ```bash
   pytest tests/test_loader.py          # 데이터 검증 (정책 수가 바뀌면 테스트의 기대값도 수정)
   python scripts/check_links.py        # 깨짐 0건 확인, 리다이렉트되는 링크는 최종 주소로 갱신
   ```
   앱을 열어 화면 상단에 "데이터 검증 오류"가 없는지 확인합니다.
5. 배포 환경에 반영합니다 (아래 배포 방법 참고).

## 사내 한정 배포

공개 URL로 배포하지 않습니다. 둘 중 하나를 선택합니다.

### 방법 1. Streamlit Community Cloud 비공개 앱

1. 코드를 **비공개(private)** GitHub 저장소에 push합니다.
2. https://share.streamlit.io 에서 New app → 저장소, 브랜치, `app.py`를 선택해 배포합니다.
3. 앱 설정의 **Sharing**에서 공개(public) 공유를 끄고, 열람자(viewer)로 사내 인원의 이메일만 초대합니다.
4. 이후 `data/policies.yaml`을 수정해 push하면 자동으로 다시 배포됩니다.

> Streamlit Community Cloud는 외부 서버입니다. 사내 보안 정책상 외부 호스팅이 허용되는지 먼저 확인하세요.
> 비공개 앱 개수 제한 등 요금제 조건은 Streamlit 공식 문서에서 최신 내용을 확인하세요.

### 방법 2. 사내 서버 (Docker)

```bash
docker build -t eu-steel-policy-tracker .
docker run -d --name eu-steel-policy-tracker -p 8501:8501 --restart unless-stopped eu-steel-policy-tracker
```

- 사내망에서만 접근할 수 있는 서버에 띄우고, 필요하면 사내 SSO·리버스 프록시 뒤에 둡니다.
- 데이터를 수정하면 이미지를 다시 빌드하거나, `-v $(pwd)/data:/app/data`로 `data/` 폴더를 마운트해서 YAML만 교체합니다.
  앱이 파일 수정 시각을 확인하므로 재시작 없이 반영됩니다.
