# PRD: EU 철강 탄소중립 정책 트래커 (EU Steel Decarbonisation Policy Tracker)

| 항목 | 내용 |
|---|---|
| 문서 버전 | v0.1 (초안) |
| 작성일 | 2026-10-27 |
| 작성자 | seoyeongo9810@gmail.com |
| 제품 형태 | Streamlit(Python) 웹 애플리케이션 |
| 배포 대상 | Streamlit Community Cloud (1차), 필요 시 사내 서버/클라우드 (2차) |

---

## 1. 배경 및 문제 정의

EU는 2050 기후중립과 2040 감축 목표(1990년 대비 -90%)를 위해 철강 업계에 영향을 주는 정책을 연달아 제정·개정하고 있습니다. 탄소국경조정제도(CBAM) 본격 시행(2026), EU ETS 무상할당 단계적 폐지(2026~2034), CBAM 적용 대상의 하류(downstream) 제품 확대 제안, 에코디자인 규정(ESPR)의 철강 제품 요건, 산업가속화법(Industrial Accelerator Act)과 저탄소 철강 라벨 등이 그 예입니다.

**문제점**
- 정책이 여러 총국(DG CLIMA, DG TAXUD, DG GROW, DG ENV, DG TRADE, DG ENER)에 흩어져 있어 한곳에서 보기 어렵다.
- 정책마다 "시행 중 / 입법 진행 중 / 의견수렴 중" 단계가 계속 바뀌어 최신 상태를 따라가기 힘들다.
- 정책별 요구사항(탄소발자국 산정, 배출량 보고, 검증, 인증서 구매 등)과 **EU 역내 철강사 / 역외(수출) 철강사** 영향이 정리된 자료가 없다.
- 의견수렴(Call for Evidence, Public Consultation) 마감일을 놓치기 쉽다.

## 2. 목표 (Goals)

1. 철강 관련 EU 탄소중립 정책을 **한 화면에서** 확인할 수 있다.
2. 정책을 **① 시행 중(In force)** 과 **② 제정 중·시행 예정(Pending)** 으로 명확히 나눈다.
3. 정책별 **주요 요구사항**, **목표 일정**, **의견수렴 현황**, **역내/역외 철강사 영향**, **EU Commission 공식 링크**를 제공한다.
4. 비개발자도 데이터 파일(YAML/CSV)만 고쳐 정책 정보를 업데이트할 수 있다.
5. 웹으로 배포해 URL 하나로 팀원과 공유한다.

### 비목표 (Non-goals)
- 법률 자문 또는 법적 해석을 제공하지 않는다. (참고용 정보이며 공식 출처 확인을 안내)
- 회사별 CBAM 비용 정밀 산정 엔진 (v1 범위 밖, 간이 계산기는 선택 기능으로 검토)
- EU 회원국별 국내 이행법 세부 추적 (v1 범위 밖)

## 3. 대상 사용자

| 사용자 | 니즈 |
|---|---|
| 철강사 탄소중립/ESG 담당자 | 규제 요구사항·일정 파악, 대응 계획 수립 |
| 수출/통상 담당자 | CBAM·수입 규제의 역외 수출 영향 파악 |
| 경영진·기획 | 한눈에 보는 요약, 주요 일정 |
| 리서치·컨설팅 | 정책 원문 링크, 의견수렴 현황 |

## 4. 주요 기능 (Functional Requirements)

### F1. 정책 목록 (시행 중 / 제정 중 분리)
- 메인 화면을 **탭 2개**로 구성: `✅ 시행 중인 법·정책` / `🕒 제정 중·시행 예정`
- 각 정책을 카드 또는 표로 표시: 정책명(국문/영문), 법적 형태(Regulation/Directive/Delegated·Implementing Act/Communication), 법령 번호, 담당 총국, 상태, 시행일, 철강 관련도(상/중/하)
- 필터: 상태, 정책 분야(탄소가격·무역, 제품·탄소발자국, 산업배출, 에너지·수소, 공공조달·시장창출, 지원·보조금), 영향 대상(역내/역외), 키워드 검색
- 정렬: 시행일, 최근 업데이트일, 관련도

### F2. 정책 상세 – 주요 요구사항
정책 하나를 선택하면 상세 페이지/확장 패널에 다음을 표시:
- 개요 (3~5줄 요약)
- **주요 요구사항** 목록. 요구사항마다 유형 태그 부여:
  - `탄소발자국/내재배출량 산정` · `MRV(모니터링·보고·검증)` · `인증서/배출권 구매` · `제품 성능·정보 요건(DPP 등)` · `라벨링` · `BAT/배출한도` · `공공조달 기준` · `무역 조치(쿼터·관세)`
- 적용 대상 (제품 CN 코드 범위, 사업장 규모 기준 등)
- 주요 일정 타임라인 (과거 마일스톤 + 향후 마일스톤)
- 관련 하위 법령 (위임·이행법령) 목록
- 마지막 확인일(`last_verified`) 및 출처

### F3. 제정 중 법안 – 일정 및 의견수렴 현황
제정 중인 법안은 추가로 다음을 표시:
- **입법 단계**: 로드맵/Call for Evidence → 공개협의 → Commission 제안 → 유럽의회·이사회 협상(트릴로그) → 합의 → 채택·관보 게재 → 시행
- 현재 단계를 진행 바(progress)로 시각화
- **목표 일정**: Commission 채택 예정 시점, 적용 예정일
- **의견수렴(Have Your Say)**:
  - 유형: Call for Evidence / Public Consultation / Draft Act feedback
  - 기간(시작~마감), 상태(진행 중 / 마감 / 예정), D-day
  - 의견수렴 주요 질문·내용 요약
  - Have Your Say 페이지 링크
- 사이드바/홈 상단에 **"마감 임박 의견수렴"** 알림 박스 (마감 30일 이내)

### F4. 역내/역외 철강사 영향 분석
- 정책별로 **EU 역내 철강사** / **EU 역외 철강사(EU 수출기업)** 영향을 나란히 비교하는 2열 레이아웃
- 항목: 직접 의무 / 비용 영향 / 준비해야 할 데이터·시스템 / 기회 요인 / 영향도(상·중·하)
- 전체 정책을 모아 보는 **영향 매트릭스** (행: 정책, 열: 역내·역외, 셀: 영향도 색상) 히트맵
- (선택) 한국 등 수출국 관점 메모 필드

### F5. 공식 링크
- 정책마다 다음 링크 제공 (없는 항목은 생략):
  - EU Commission 정책 페이지
  - EUR-Lex 법령 원문
  - Have Your Say(의견수렴) 페이지
  - 유럽의회 Legislative Observatory(OEIL) 절차 페이지 (제정 중 법안)
  - 가이던스·FAQ 문서
- 링크 유효성 점검 스크립트(`scripts/check_links.py`) 제공: HTTP 상태 확인, 깨진 링크 목록 출력

### F6. 대시보드(홈)
- KPI: 시행 중 정책 수 / 제정 중 정책 수 / 진행 중 의견수렴 수 / 90일 이내 주요 마일스톤 수
- **통합 타임라인** (Plotly Gantt/Timeline): 2023~2035 주요 일정 (예: CBAM 전환기간 종료, 무상할당 감축 일정)
- 최근 업데이트된 정책 5건

### F7. 데이터 관리 및 업데이트
- 정책 데이터는 코드와 분리된 `data/policies.yaml` 하나로 관리
- 각 항목에 `last_verified`(마지막 확인일) 필드 필수. 90일 넘게 확인하지 않은 항목은 UI에 "⚠ 재확인 필요" 배지 표시
- 업데이트 이력 `data/changelog.yaml` → "변경 이력" 페이지에 표시
- (v2) EUR-Lex / Have Your Say RSS 또는 API를 이용한 변경 감지 알림

### F8. 내보내기
- 필터된 정책 목록 CSV/Excel 다운로드 (`st.download_button`)
- (v2) 정책 요약 PDF 리포트

### F9. 언어
- v1: 한국어 UI + 영문 정책 원어명 병기
- v2: 영어 UI 전환 토글

## 5. 초기 정책 데이터 (Seed List)

> ⚠ 아래 내용은 PRD 작성 시점 기준 초안입니다. 정책 상태가 빠르게 바뀌므로 **개발 단계에서 각 항목을 EUR-Lex·Commission 공식 페이지로 반드시 재확인**한 뒤 `last_verified`를 기록합니다. 특히 `[확인 필요]` 표시 항목은 최신 입법 상황을 우선 확인합니다.

### 5.1 시행 중 (In force)

| # | 정책 | 법령 | 철강 관련 핵심 요구사항 | 역내 철강사 | 역외 철강사 |
|---|---|---|---|---|---|
| 1 | **CBAM** (탄소국경조정제도) | Reg. (EU) 2023/956, 간소화 개정 Reg. (EU) 2025/2083 및 이행·위임법령 | 2026.1.1 확정기간 시작. 연간 50톤 미만 수입자 면제, 허가 신고인(Authorised CBAM declarant) 제도, 내재배출량(직접+일부 간접) 산정·검증, CBAM 인증서 구매(2027.2 판매 개시), 2026년분 연간 신고 2027.9.30까지 | 무상할당 감축과 연동, 수입재와의 가격 경쟁 조건 변화 | **직접 영향 최대**: 설비 단위 배출량 데이터 제공, 검증기관 검증, 기본값(default value) 대비 실측 우위 확보, 원산지 탄소가격 공제 |
| 2 | **EU ETS** (배출권거래제) | Dir. 2003/87/EC (2023/959 개정) | 고로·전기로 등 설비 배출량 MRV, 배출권 제출. CBAM 대상 부문 **무상할당 2026~2034 단계적 폐지**(2026 -2.5% → 2034 -100%), 벤치마크 갱신, 탈탄소 계획 미이행 시 무상할당 감액 | **직접 영향 최대**: 탄소비용 증가, 탈탄소화 투자 압박 | 간접 영향(CBAM 가격이 ETS 가격과 연동) |
| 3 | **산업배출지침 개정 (IED 2.0)** | Dir. (EU) 2024/1785 | BAT 기반 허가, 환경관리시스템(EMS)에 2030년까지 **전환계획(Transformation plan)** 포함, 철강 BREF 개정 진행 | 사업장 허가 조건·투자 계획 수립 | 영향 적음 |
| 4 | **에코디자인 규정 (ESPR)** | Reg. (EU) 2024/1781 | 철강을 우선 중간재로 지정(2025 작업계획). 향후 위임법령으로 탄소·환경발자국, 재활용 함량, 디지털 제품여권(DPP) 요건 도입 예정 | 제품 단위 탄소발자국 산정·공개 체계 구축 | EU 시장 출시 제품에 동일 적용 → 제품 단위 데이터 필요 |
| 5 | **건설제품규정 (CPR) 개정** | Reg. (EU) 2024/3110 | 철근·형강 등 건설용 강재에 환경지속가능성 정보(GWP 등) 단계적 신고, DPP | EPD·GWP 데이터 대응 | EU 건설시장 수출 시 동일 요건 |
| 6 | **넷제로산업법 (NZIA)** | Reg. (EU) 2024/1735 | 공공조달·경매 시 지속가능성·회복력 기준 | 저탄소 철강 수요 확대 기회 | 조달 시장 접근 조건 강화 가능 |
| 7 | **재생에너지지침 개정 (RED III)** | Dir. (EU) 2023/2413 | 산업용 수소 중 RFNBO(재생 수소) 비중 2030 42% | 수소환원제철(H2-DRI) 연료 조달 계획 | 영향 적음 |
| 8 | **유럽기후법 개정 (2040 목표)** `[확인 필요]` | Reg. (EU) 2021/1119 개정 | 2040 순배출 -90%(국제 크레딧 일부 허용) → ETS·CBAM 후속 개정의 근거 | 장기 감축 경로 | 간접 |
| 9 | **철강 무역조치 (세이프가드 후속 조치)** `[확인 필요]` | 2025.10 제안, 2026.7 세이프가드 만료 대체 | 수입 쿼터 대폭 축소, 쿼터 초과분 50% 관세, 용해·주조(melt and pour) 원산지 기준 | 역내 공급 보호 | **직접 영향**: 수출 물량·가격 |

### 5.2 제정 중·시행 예정 (Pending)

| # | 정책 | 단계(작성 시점) | 목표 일정 | 핵심 요구사항(안) | 의견수렴 |
|---|---|---|---|---|---|
| 1 | **CBAM 적용범위 확대 – 하류제품 및 우회방지** `[확인 필요]` | 2025.12 Commission 제안 → 의회·이사회 심의 | 2028 적용 목표 | 철강·알루미늄 집약 하류제품(약 180개 CN) 추가, 우회방지 조항 | 제안 단계 피드백 (Have Your Say) |
| 2 | **CBAM 수출 관련 조치 / 탈탄소 기금** `[확인 필요]` | 2025.12 제안 패키지 | 미정 | EU 수출품 탄소유출 대응 | 확인 필요 |
| 3 | **EU ETS 2026 검토 개정안** `[확인 필요]` | Call for evidence/공개협의 이후 Commission 제안 예정·진행 | 2026~2027 제안 | 2030 이후 상한(cap), 무상할당·벤치마크, 탄소제거 편입 등 | Call for Evidence / Public Consultation |
| 4 | **산업가속화법 (Industrial Accelerator Act)** `[확인 필요]` | 2026 Commission 제안 → 입법 심의 | 미정 | 공공조달 저탄소·역내산(Made in Europe) 기준, **저탄소 철강 라벨/정의** | 확인 필요 |
| 5 | **ESPR 철강 위임법령** | 준비 연구·이해관계자 협의(Ecodesign Forum) | 2027 전후 채택 예상 | 탄소발자국 성능 등급, 정보 공개, DPP | 초안 피드백 예정 |
| 6 | **철강 BREF 개정 (IED)** | 기술작업반(TWG) 검토 | 미정 | BAT-AEL(배출한도) 강화 | 기술작업반 절차 |
| 7 | **폐차규정 (ELV Regulation)** `[확인 필요]` | 트릴로그/채택 단계 | 미정 | 차량 재활용 함량, 철 스크랩 회수 | – |
| 8 | **CBAM 간접배출·기본값 관련 이행/위임법령 개정** | 상시 | 수시 | 기본값, 검증, 벤치마크 등 기술 세부 | Draft act feedback |

**비입법 정책(참고 섹션):** Clean Industrial Deal(2025.2), 철강·금속 행동계획(Steel and Metals Action Plan, 2025.3), Clean Industrial Deal 국가보조 프레임워크(CISAF, 2025.6), Industrial Decarbonisation Bank, Innovation Fund — "지원·보조금" 분야로 분리해 표시.

### 5.3 기본 링크 (개발 시 유효성 재확인)

| 정책 | URL |
|---|---|
| CBAM | https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en |
| EU ETS | https://climate.ec.europa.eu/eu-action/eu-emissions-trading-system-eu-ets_en |
| 산업배출 (IED) | https://environment.ec.europa.eu/topics/industrial-emissions-and-safety_en |
| ESPR | https://commission.europa.eu/energy-climate-change-environment/standards-tools-and-labels/products-labelling-rules-and-requirements/ecodesign-sustainable-products-regulation_en |
| CPR | https://single-market-economy.ec.europa.eu/sectors/construction/construction-products-regulation-cpr_en |
| NZIA | https://single-market-economy.ec.europa.eu/industry/sustainability/net-zero-industry-act_en |
| 재생에너지지침 | https://energy.ec.europa.eu/topics/renewable-energy/renewable-energy-directive-targets-and-rules/renewable-energy-directive_en |
| 유럽기후법 | https://climate.ec.europa.eu/eu-action/european-climate-law_en |
| 철강 산업 정책 | https://single-market-economy.ec.europa.eu/sectors/raw-materials/related-industries/metal-industries/steel_en |
| 의견수렴 (Have Your Say) | https://ec.europa.eu/info/law/better-regulation/have-your-say_en |
| 법령 원문 | https://eur-lex.europa.eu |
| 유럽의회 입법 절차 | https://oeil.secure.europarl.europa.eu |

## 6. 데이터 모델

`data/policies.yaml` 항목 스키마 예시:

```yaml
- id: cbam
  name_ko: 탄소국경조정제도
  name_en: Carbon Border Adjustment Mechanism (CBAM)
  status: in_force            # in_force | pending
  stage: definitive_period    # pending일 경우: call_for_evidence | consultation | proposal | trilogue | agreed | adopted
  legal_form: Regulation
  legal_ref: "Regulation (EU) 2023/956"
  dg: TAXUD
  category: [carbon_pricing_trade]
  steel_relevance: high       # high | medium | low
  summary: >
    EU로 수입되는 철강 등 탄소집약 제품의 내재배출량에 탄소가격을 부과...
  requirements:
    - type: carbon_footprint
      text: 설비별 내재배출량(직접·간접) 산정 및 제3자 검증
    - type: certificate
      text: 2027년 2월부터 CBAM 인증서 구매, 연간 신고
  scope: "CN 72, 73 일부 (철강)"
  milestones:
    - date: 2026-01-01
      label: 확정기간 시작
    - date: 2027-09-30
      label: 2026년분 첫 연간 신고 마감
  consultations:
    - type: call_for_evidence # call_for_evidence | public_consultation | draft_act_feedback
      title: "..."
      start: 2025-12-17
      end: 2026-02-11
      summary: "..."
      url: "https://ec.europa.eu/info/law/better-regulation/have-your-say/..."
  impact:
    eu_producers:
      level: medium
      obligations: "..."
      costs: "..."
      preparation: "..."
      opportunities: "..."
    non_eu_producers:
      level: high
      obligations: "..."
      costs: "..."
      preparation: "..."
      opportunities: "..."
  links:
    commission: "https://taxation-customs.ec.europa.eu/carbon-border-adjustment-mechanism_en"
    eurlex: "https://eur-lex.europa.eu/eli/reg/2023/956/oj"
    have_your_say: null
    oeil: null
  related: [eu_ets, cbam_downstream]
  last_verified: 2026-10-27
```

- 스키마 검증: `pydantic` 모델로 앱 실행 시 로드·검증, 오류 항목은 경고 표시
- 의견수렴 상태(진행 중/마감/예정)와 D-day는 저장하지 않고 오늘 날짜 기준으로 계산

## 7. 화면 구성 (IA)

```
사이드바
 ├─ 필터 (분야 / 영향 대상 / 관련도 / 검색)
 ├─ ⏰ 마감 임박 의견수렴
 └─ 데이터 기준일 · 면책 문구

페이지
 1. 🏠 대시보드      : KPI, 통합 타임라인, 최근 업데이트
 2. 📋 정책 목록      : [시행 중] [제정 중] 탭 → 카드/표 → 상세 펼치기
 3. 🔍 정책 상세      : 요구사항, 일정, 의견수렴, 역내/역외 영향, 링크
 4. 🗣 의견수렴 현황  : 진행 중·예정·마감 목록, 캘린더 뷰
 5. 🌍 영향 매트릭스  : 정책 × 역내/역외 히트맵, 비교표
 6. 📝 변경 이력      : changelog
```

Streamlit 멀티페이지(`pages/` 디렉터리 또는 `st.navigation`) 구조 사용.

## 8. 기술 설계

| 구분 | 선택 |
|---|---|
| 언어/프레임워크 | Python 3.11+, Streamlit (최신 안정 버전) |
| 데이터 | YAML (`PyYAML`) + `pydantic` 스키마 검증, `pandas` |
| 시각화 | Plotly (타임라인, 히트맵) |
| 캐싱 | `@st.cache_data` (데이터 파일 변경 시 갱신) |
| 링크 점검 | `requests` 기반 스크립트, (v2) GitHub Actions 주간 실행 |
| 배포 | GitHub 저장소 → Streamlit Community Cloud |
| 내보내기 | `pandas` → CSV, `openpyxl` → Excel |

### 디렉터리 구조

```
eu-steel-policy-tracker/
├─ app.py                  # 진입점, 대시보드
├─ pages/
│  ├─ 1_정책_목록.py
│  ├─ 2_정책_상세.py
│  ├─ 3_의견수렴.py
│  ├─ 4_영향_매트릭스.py
│  └─ 5_변경_이력.py
├─ src/
│  ├─ models.py            # pydantic 스키마
│  ├─ loader.py            # YAML 로드·검증
│  └─ components.py        # 카드, 배지, 타임라인 등 UI 컴포넌트
├─ data/
│  ├─ policies.yaml
│  └─ changelog.yaml
├─ scripts/
│  └─ check_links.py
├─ .streamlit/config.toml  # 테마
├─ requirements.txt
└─ README.md               # 실행·배포·데이터 업데이트 방법
```

### 배포 절차 (Streamlit Community Cloud)
1. GitHub 저장소 생성 후 코드 push
2. share.streamlit.io 로그인 → New app → 저장소/브랜치/`app.py` 선택
3. `requirements.txt` 기반 자동 빌드 → 공개 URL 발급
4. `data/policies.yaml` 수정 후 push하면 자동 재배포

## 9. 비기능 요구사항

- **정확성/신뢰성**: 모든 정책 항목에 공식 출처 링크와 `last_verified` 필수. 화면 하단에 "본 정보는 참고용이며 법적 효력이 없습니다. 공식 출처를 확인하세요." 면책 문구 표시
- **성능**: 첫 로딩 3초 이내 (정책 ~50건 기준)
- **유지보수성**: 정책 추가·수정은 YAML 수정만으로 가능, 코드 변경 불필요
- **반응형**: 데스크톱 우선, 모바일에서도 표·카드가 깨지지 않을 것
- **보안**: 외부 API 키 불필요(v1). 비공개 배포가 필요하면 Streamlit Cloud의 viewer 제한 또는 사내 배포

## 10. 마일스톤

| 단계 | 내용 | 산출물 |
|---|---|---|
| M1 | 데이터 조사·검증 (5장 seed list 공식 출처 확인) | `policies.yaml` v1 |
| M2 | 핵심 화면: 정책 목록(시행/제정 분리) + 상세 | 로컬 실행 앱 |
| M3 | 의견수렴 현황, 영향 매트릭스, 대시보드 타임라인 | 기능 완성 앱 |
| M4 | 링크 점검 스크립트, 내보내기, README | 배포 가능한 저장소 |
| M5 | Streamlit Cloud 배포 및 사용자 피드백 | 공개 URL |
| v2 | EUR-Lex/Have Your Say 변경 감지, 영어 UI, PDF 리포트, CBAM 비용 간이 계산기 | – |

## 11. 수용 기준 (Acceptance Criteria)

- [ ] 정책 목록이 "시행 중" / "제정 중·시행 예정" 탭으로 분리되어 표시된다.
- [ ] 각 정책에 주요 요구사항이 유형 태그(탄소발자국, MRV 등)와 함께 표시된다.
- [ ] 제정 중 법안은 현재 입법 단계, 목표 일정, 의견수렴(유형·기간·내용·링크)을 표시한다.
- [ ] 진행 중 의견수렴은 D-day와 함께 사이드바에 노출된다.
- [ ] 정책마다 역내/역외 철강사 영향이 비교 형태로 표시되고, 영향 매트릭스 페이지가 있다.
- [ ] 정책마다 최소 1개 이상의 EU Commission 공식 링크가 있고, 링크 점검 스크립트 결과 깨진 링크가 0건이다.
- [ ] `last_verified`가 90일을 넘은 항목에 "재확인 필요" 배지가 표시된다.
- [ ] 필터된 목록을 CSV/Excel로 내려받을 수 있다.
- [ ] Streamlit Community Cloud에 배포되어 공개 URL로 접속된다.

## 12. 리스크 및 대응

| 리스크 | 대응 |
|---|---|
| 정책 변경 속도가 빨라 정보가 낡음 | `last_verified` 배지, 변경 이력, 월 1회 정기 점검, (v2) 자동 변경 감지 |
| 잘못된 해석으로 의사결정 오류 | 원문 링크 병기, 면책 문구, 요약에 출처 조항 표기 |
| Commission 웹페이지 URL 변경 | 링크 점검 스크립트, EUR-Lex ELI 영구 링크 우선 사용 |
| 무료 호스팅 제약(슬립 모드 등) | 사용량 증가 시 사내 서버/클라우드(Docker) 이전 |

## 13. 열린 질문 (Open Questions)

1. 앱 공개 범위: 누구나 접근 가능한 공개 URL인지, 사내 한정인지?
2. 데이터 업데이트 담당자와 주기 (월 1회 제안)
3. 한국 철강사 관점(예: 국내 수출 품목 CN 코드별 영향) 메모를 v1에 포함할지?
4. CBAM 비용 간이 계산기를 v1에 넣을지, v2로 미룰지?


앱 공개 범위는 사내 한정
데이터 업데이트 주기 : 주 1회
한국 철강사 관점 포함
정책 동향만 필요한 관계로 CFP 및 CBAM 산정, 인증서 비용 계산 관련 사항은 불필요
