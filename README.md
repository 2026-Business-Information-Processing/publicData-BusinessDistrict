# 서울시 상권분석서비스 2024 Streamlit MVP

서울시 상권분석서비스 2024년 데이터를 활용해, 행정동별 상권 현황을 시각화하고 규칙 기반 창업유망점수를 계산하여 창업 후보지를 추천하는 Streamlit 대시보드 MVP입니다.

## 프로젝트 개요

- 행정동 단위로 매출, 점포, 유동인구 지표를 통합 분석
- 필터(분기/업종/최소 점포 수) 기반으로 상권 현황 탐색
- 규칙 기반 창업유망점수 산출 및 Top 지역 추천
- MVP 범위: 그래프 시각화 + 추천 기능 (Gemini API 미포함)

## 사용 데이터 설명

`data/` 폴더에 아래 CSV 파일이 있어야 합니다.

- `sales_2024.csv`  
  서울시 상권분석서비스(추정매출-행정동)_2024년 데이터
- `stores_2024.csv`  
  서울시 상권분석서비스(점포-행정동)_2024년 데이터
- `population_2024.csv`  
  서울시 상권분석서비스(길단위인구-행정동) 데이터

## 폴더 구조

현재 MVP 구조:

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
publicData-BusinessDistrict/
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

## 로컬 실행 방법

1. 가상환경 생성 및 활성화
2. 패키지 설치
3. Streamlit 실행

```bash
pip install -r requirements.txt
streamlit run app.py
```

## data 폴더에 직접 넣어야 하는 CSV 파일명

- `data/sales_2024.csv`
- `data/stores_2024.csv`
- `data/population_2024.csv`

앱은 `utf-8-sig` 인코딩으로 먼저 시도하고, 실패하면 `cp949`로 자동 재시도합니다.

## GitHub에 원본 CSV를 올리지 않는 이유

- 원본 공공데이터 파일 용량이 커서 저장소가 불필요하게 비대해질 수 있음
- 데이터 버전 교체/갱신 주기가 있어 코드와 원본 데이터를 분리 관리하는 것이 효율적임
- `.gitignore`로 `data/*.csv`를 제외하고, 폴더 유지를 위해 `data/.gitkeep`만 추적함

## 추후 Supabase 연동 계획

- 현재는 `app.py` 내 `load_local_data()` 함수에서 로컬 CSV를 로딩
- 이후 Supabase 도입 시, 해당 함수 내부를 API/쿼리 방식으로 교체해도 앱 흐름 유지 가능
- 확장 시 `src/data_loader.py`로 분리하여 데이터 소스 전환을 단순화할 예정

## 분석 지표 설명

앱에서 계산하는 주요 파생지표:

- 점포당매출 = 당월_매출_금액 / 점포_수
- 점포당매출건수 = 당월_매출_건수 / 점포_수
- 유동인구당매출 = 당월_매출_금액 / 총_유동인구_수
- 유동인구당매출건수 = 당월_매출_건수 / 총_유동인구_수
- 객단가 = 당월_매출_금액 / 당월_매출_건수
- 프랜차이즈비율 = 프랜차이즈_점포_수 / 점포_수

0으로 나누는 경우는 NaN 처리 후 집계 시 자동 제외되도록 구성했습니다.

## 창업유망점수 계산식

각 지표를 0~100 min-max 정규화한 뒤 아래 가중합으로 점수를 계산합니다.

- 점포당매출점수
- 유동인구점수
- 유동인구당매출점수
- 폐업률안정성점수 = 100 - 폐업률정규화점수

최종식:

```text
창업유망점수 =
0.35 * 점포당매출점수
+ 0.25 * 유동인구점수
+ 0.25 * 유동인구당매출점수
+ 0.15 * 폐업률안정성점수
```

## 데이터 한계 및 유의사항

- 본 대시보드는 서울시 상권분석서비스의 행정동 단위 데이터를 기반으로 함
- 임대료, 권리금, 실제 영업이익, 개별 점포 입지 조건은 포함하지 않음
- 추천 결과는 창업 후보지 탐색을 위한 참고 자료로 활용해야 함