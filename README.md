# 서울시 상권분석서비스 2024 Streamlit MVP

## 사용한 프롬프트 공유 링크

<!-- 여기에 링크 또는 요약을 작성해 주세요. -->





## 데이터 (데이터와 클린징 과정) 및 시각화 결과 (차트 설명 및 인사이트)

<!-- 여기에 데이터 출처, 전처리·클린징 과정, 주요 차트 해석과 인사이트를 작성해 주세요. -->





---

## 프로젝트 개요

서울시 상권분석서비스 2024년 행정동 단위 데이터를 **Supabase**에서 불러와 분석하는 Streamlit 대시보드입니다. 행정동별 매출·점포·유동인구를 결합하고, 규칙 기반 **창업유망점수**를 산출하여 후보 지역을 탐색할 수 있습니다. Gemini API는 포함하지 않습니다.

### 주요 기능

- 분기·업종·최소 점포 수·Top N 등 **사이드바 필터**
- KPI 카드: 총매출, 총 점포 수, 평균 점포당 매출, 평균 폐업률
- 행정동별 **총매출** / **점포당 매출** Top N 막대그래프 (간결한 툴팁)
- 유동인구 대비 매출 **산점도** + 평균선(점선) 및 사분면 해석 안내
- **창업유망지역 Top N** 표·막대그래프, Top 5 **추천 카드**(강점·주의점, 전체 평균 대비 표시)
- **창업 후보지 상세 분석**: 행정동 선택, 핵심 지표, 평균 대비 표, 업종 내 순위, 강점·주의점, 종합 판단 문구
- **시간대별·요일별 매출 비중** 그래프 및 자동 해석 문구(해당 컬럼이 있을 때만 표시)
- 금액·건수·비율·점수에 대한 **일관된 포맷**(억/만 원, 콤마, % 등)

## 기술 스택

- Python 3.x  
- [Streamlit](https://streamlit.io/) — UI  
- [Pandas](https://pandas.pydata.org/), NumPy — 전처리·집계  
- [Plotly Express](https://plotly.com/python/plotly-express/) — 시각화  
- [Supabase Python 클라이언트](https://supabase.com/docs/reference/python/introduction) — 데이터 로딩(테이블 `range` 기반 페이지네이션)

## 폴더 구조

```text
publicData-BusinessDistrict/
├─ app.py                 # 대시보드 단일 진입점(로딩·전처리·점수·차트·UI)
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ data/
│  └─ .gitkeep            # 원본 CSV는 Git에 포함하지 않음(선택·분석용)
└─ .streamlit/
   └─ secrets.toml        # 로컬 실행 시 Supabase 설정(저장소에 커밋하지 않음)
```

추후 모듈 분리 예시:

```text
seoul-commercial-dashboard/
├─ app.py
├─ requirements.txt
├─ README.md
├─ .gitignore
├─ src/
│  ├─ data_loader.py
│  ├─ preprocess.py
│  ├─ scoring.py
│  └─ charts.py
└─ .streamlit/
   └─ secrets.toml
```

## 사용 데이터 (스키마 요약)

Supabase에는 아래 **세 테이블**이 있으며, 컬럼 구조는 서울시 상권분석서비스 CSV와 동일하다고 가정합니다.

| 테이블명 | 설명 |
|---------|------|
| `sales_2024` | 추정매출(행정동) — 시간대·요일별 매출 금액 컬럼 포함 가능 |
| `stores_2024` | 점포(행정동) |
| `population_2024` | 길단위인구·행정동 단위 유동인구 |

앱은 위 원본 컬럼 순서를 기준으로 내부 표준 이름으로 매핑한 뒤 키로 결합합니다.

## 실행 방법 (로컬)

1. **저장소 클론** 후 프로젝트 루트로 이동합니다.

2. 가상환경을 권장합니다.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
```

3. 의존성 설치:

```bash
python -m pip install -r requirements.txt
```

4. Supabase 접속 정보를 Streamlit secrets에 둡니다.

**파일 위치:** `.streamlit/secrets.toml` (Git에는 올리지 마세요.)

```toml
[supabase]
url = "https://YOUR_PROJECT_ID.supabase.co"
key = "YOUR_SUPABASE_ANON_KEY"
```

아래처럼 **최상위 키**만 두어도 `app.py`에서 인식합니다.

```toml
SUPABASE_URL = "https://YOUR_PROJECT_ID.supabase.co"
SUPABASE_KEY = "YOUR_SUPABASE_ANON_KEY"
```

또는 `connections.supabase` 블록의 `url`/`key` 또는 `SUPABASE_URL`/`SUPABASE_KEY` 조합도 지원합니다.

5. 앱 실행:

```bash
python -m streamlit run app.py
```

브라우저에서 표시되는 주소(기본 `http://localhost:8501`)로 접속합니다.

> Supabase 조회 실패 시 로컬 CSV로 넘어가지 않습니다. secrets·네트워크·테이블 권한·RLS 설정을 확인하세요.

## Streamlit Cloud 배포

1. GitHub에 코드를 푸시합니다 (`secrets.toml`·원본 CSV는 커밋하지 않음).

2. [Streamlit Community Cloud](https://streamlit.io/cloud)에서 저장소와 브랜치를 연결하고, **앱 설정 → Secrets**에 동일한 Supabase URL·키를 TOML 형식으로 입력합니다.

3. 메인 파일을 `app.py`로 지정합니다.

4. 첫 실행 시 세 테이블 전량을 페이지 단위로 가져오므로 데이터 크기에 따라 로딩이 길어질 수 있습니다. `@st.cache_data(ttl=300)`으로 짧은 기간 캐시됩니다.

## 파생 지표

결합된 행 단위에서 다음과 같이 계산합니다(0으로 나누는 경우 NaN 처리).

- **점포당매출** = 당월 매출 금액 ÷ 점포 수  
- **점포당매출건수** = 당월 매출 건수 ÷ 점포 수  
- **유동인구당매출** = 당월 매출 금액 ÷ 총 유동인구 수  
- **유동인구당매출건수** = 당월 매출 건수 ÷ 총 유동인구 수  
- **객단가** = 당월 매출 금액 ÷ 당월 매출 건수  
- **프랜차이즈비율** = 프랜차이즈 점포 수 ÷ 점포 수 (해당 컬럼이 있을 때)

집계 화면에서는 행정동별 합계·평균 등으로 요약해 KPI·차트에 사용합니다.

## 창업유망점수 계산식

각 구성 지표를 해당 필터 구간 전체에 대해 **0~100 min-max 정규화**한 뒤 가중합합니다.

```text
창업유망점수 =
  0.35 × 점포당매출점수
+ 0.25 × 유동인구점수
+ 0.25 × 유동인구당매출점수
+ 0.15 × 폐업률안정성점수
```

- **폐업률안정성점수** = 100 − (폐업률에 대한 min-max 점수)  
- 규칙 기반 추천 문장은 위 세부 점수·평균 대비 등과 연동되어 카드·상세 분석에 표시됩니다.

## 툴팁·표시 규칙 (요약)

- Plotly 그래프는 `custom_data`와 `hovertemplate`으로 항목 수를 줄이고 한글 라벨을 사용합니다.  
- 금액은 **억 원 / 만 원 / 원** 단위로 읽기 쉽게 표시합니다.  
- 비율은 **%**, 점수는 소수 **한 자리** 정도로 통일합니다.  
- `<extra></extra>`로 트레이스 이름 등 불필요한 hover 줄을 숨깁니다.

## GitHub에 원본 CSV와 secrets를 올리지 않는 이유

- 원본 CSV 용량이 크고 버전 교체가 잦을 수 있어 저장소와 분리하는 편이 관리에 유리합니다.  
- Supabase URL·API 키는 공개 저장소에 포함하면 안 됩니다.  
- `.gitignore`에서 `data/*.csv`, `.streamlit/secrets.toml`, `.env` 등을 제외하고 `data/.gitkeep`만 추적할 수 있습니다.

## 데이터 한계 및 유의사항

- 행정동·업종·분기 단위 **공개 통계** 기준이며, 실제 매장 단위 매출이 아닙니다.  
- **임대료, 권리금, 실제 영업이익, 입지 세부 조건**은 반영하지 않습니다.  
- 창업유망점수와 추천 문구는 **참고용 탐색 도구**이며, 최종 의사결정 전 현장 조사·추가 분석이 필요합니다.
