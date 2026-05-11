# 서울시 상권분석서비스 2024 Streamlit MVP

서울시 상권분석서비스 2024년 데이터를 기반으로, 행정동별 상권 현황을 시각화하고 규칙 기반 창업유망점수를 계산해 창업 후보지를 추천하는 대시보드입니다.

## 프로젝트 개요

- 행정동 단위 매출/점포/유동인구 통합 분석
- 필터(분기/업종/최소 점포 수/Top N) 기반 탐색
- 창업유망점수 기반 추천 표 + Top 5 카드
- 로컬 CSV와 Supabase를 모두 지원하며, Supabase 실패 시 로컬 CSV fallback
- Gemini API 기능은 현재 MVP 범위에서 제외

## 사용 데이터

아래 3개 데이터(동일 스키마)를 사용합니다.

- `sales_2024` / `sales_2024.csv`: 추정매출(행정동)
- `stores_2024` / `stores_2024.csv`: 점포(행정동)
- `population_2024` / `population_2024.csv`: 길단위인구(행정동)

## 폴더 구조

```text
publicData-BusinessDistrict/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ data/
│  └─ .gitkeep
└─ .streamlit/
   └─ secrets.toml
```

추후 확장 예상 구조:

```text
seoul-commercial-dashboard/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ data/
│  └─ .gitkeep
├─ src/
│  ├─ data_loader.py
│  ├─ preprocess.py
│  ├─ scoring.py
│  └─ charts.py
└─ .streamlit/
   └─ secrets.toml
```

## 로컬 CSV 방식 실행 방법

1. Python 환경 준비
2. 의존성 설치
3. Streamlit 실행

```bash
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

아래 파일을 `data/` 폴더에 직접 넣어야 합니다.

- `data/sales_2024.csv`
- `data/stores_2024.csv`
- `data/population_2024.csv`

앱은 CSV를 `utf-8-sig`로 먼저 읽고 실패 시 `cp949`로 재시도합니다.

## Supabase 방식 실행 방법

1. 동일하게 의존성 설치 및 앱 실행
2. 사이드바에서 데이터 소스를 `Supabase`로 선택
3. `.streamlit/secrets.toml`에 Supabase 정보 설정

### Supabase 테이블명

- `sales_2024`
- `stores_2024`
- `population_2024`

### Streamlit secrets 설정 예시

`.streamlit/secrets.toml` 파일에 아래 형식으로 작성:

```toml
[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
key = "YOUR_SUPABASE_ANON_KEY"
```

## 데이터 소스 선택 및 fallback 구조

- 사이드바에서 데이터 소스를 `로컬 CSV` / `Supabase` 중 선택
- 기본값은 `로컬 CSV`
- `Supabase` 선택 시 Supabase 조회를 우선 시도
- 연결 실패/권한 오류/테이블 오류/secrets 누락 시 경고를 표시하고 로컬 CSV로 자동 fallback
- fallback 이후에도 CSV가 없으면 필수 파일명을 안내하고 중단

## GitHub에 원본 CSV와 secrets.toml을 올리지 않는 이유

- 대용량 원본 파일은 저장소를 불필요하게 비대화시킴
- 데이터 버전 교체가 잦아 코드와 데이터 분리 관리가 유리
- `secrets.toml`은 접속 정보(민감정보)가 포함될 수 있어 업로드 금지
- `.gitignore`에서 `data/*.csv`, `.streamlit/secrets.toml`, `.env`를 제외하고 `data/.gitkeep`만 추적

## 분석 지표

- 점포당매출 = 당월매출 / 점포수
- 점포당매출건수 = 당월매출건수 / 점포수
- 유동인구당매출 = 당월매출 / 총유동인구
- 유동인구당매출건수 = 당월매출건수 / 총유동인구
- 객단가 = 당월매출 / 당월매출건수
- 프랜차이즈비율 = 프랜차이즈점포수 / 점포수

0으로 나누는 경우는 NaN 처리합니다.

## 창업유망점수 계산식

각 지표를 0~100 min-max 정규화 후 아래 가중합으로 계산합니다.

```text
창업유망점수 =
0.35 * 점포당매출점수
+ 0.25 * 유동인구점수
+ 0.25 * 유동인구당매출점수
+ 0.15 * 폐업률안정성점수
```

- 폐업률안정성점수 = 100 - 폐업률정규화점수

## 툴팁 간소화 기준

- 그래프별 핵심 정보 4~6개만 노출
- `custom_data` + `hovertemplate`로 사용자 친화적인 한글 라벨 적용
- 금액은 억/만/원 단위로 축약
- 비율은 `%`, 점수는 소수점 1자리 기준 표시
- `<extra></extra>`로 불필요 trace 라벨 제거

## 데이터 한계 및 유의사항

- 본 대시보드는 행정동 단위 집계 데이터 기반
- 임대료/권리금/실제 영업이익/개별 점포 입지 조건은 미반영
- 추천 결과는 창업 후보지 탐색을 위한 참고 자료로 사용
