# -*- coding: cp949 -*-
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

try:
    from supabase import create_client
except Exception:  # noqa: BLE001
    create_client = None


st.set_page_config(page_title="Seoul Commercial Dashboard MVP", layout="wide")


# -----------------------------
# Constants
# -----------------------------
DATA_DIR = Path("data")
REQUIRED_FILES = {
    "sales_2024.csv": DATA_DIR / "sales_2024.csv",
    "stores_2024.csv": DATA_DIR / "stores_2024.csv",
    "population_2024.csv": DATA_DIR / "population_2024.csv",
}

SUPABASE_TABLES = {
    "sales_2024": "sales_2024",
    "stores_2024": "stores_2024",
    "population_2024": "population_2024",
}


# -----------------------------
# Formatting helpers
# -----------------------------
def format_currency_krw(value: float) -> str:
    """원화 금액을 억/만/원 단위로 가독성 있게 변환한다."""
    if pd.isna(value):
        return "-"
    abs_v = abs(float(value))
    sign = "-" if value < 0 else ""
    if abs_v >= 100_000_000:
        return f"{sign}{abs_v / 100_000_000:.1f}억 원"
    if abs_v >= 10_000:
        return f"{sign}{abs_v / 10_000:.1f}만 원"
    return f"{sign}{int(round(abs_v)):,}원"


def format_number(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(round(value)):,}"


def format_percent(value: float, digits: int = 1) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.{digits}f}%"


def format_score(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:.1f}점"


# -----------------------------
# Data load helpers
# -----------------------------
def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    """CSV 파일을 utf-8-sig 우선, 실패 시 cp949로 읽는다."""
    last_error = None
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise ValueError(f"`{path.name}` 파일을 utf-8-sig/cp949로 읽지 못했습니다: {last_error}")


def to_numeric_safe(series: pd.Series) -> pd.Series:
    """쉼표/공백/%가 포함된 숫자 문자열을 안전하게 숫자로 변환한다."""
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("%", "", regex=False)
    )
    cleaned = cleaned.replace({"": np.nan, "-": np.nan, "nan": np.nan, "None": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


def safe_divide(numer: pd.Series, denom: pd.Series) -> pd.Series:
    """0으로 나누는 경우를 NaN 처리한다."""
    return numer / denom.replace(0, np.nan)


def minmax_0_100(series: pd.Series) -> pd.Series:
    """0~100 min-max 정규화 (상수열은 50점)."""
    s = series.astype(float)
    min_v = s.min(skipna=True)
    max_v = s.max(skipna=True)
    if pd.isna(min_v) or pd.isna(max_v):
        return pd.Series(0.0, index=series.index)
    if np.isclose(min_v, max_v):
        return pd.Series(50.0, index=series.index)
    return ((s - min_v) / (max_v - min_v) * 100).clip(0, 100)


@st.cache_data(show_spinner=False)
def load_data_from_csv() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """로컬 CSV에서 원본 3개 데이터프레임을 읽는다."""
    missing = [name for name, path in REQUIRED_FILES.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(",".join(missing))

    sales = read_csv_with_fallback(REQUIRED_FILES["sales_2024.csv"])
    stores = read_csv_with_fallback(REQUIRED_FILES["stores_2024.csv"])
    population = read_csv_with_fallback(REQUIRED_FILES["population_2024.csv"])
    return sales, stores, population


def fetch_all_rows(client, table_name: str, page_size: int = 1000) -> list[dict]:
    """
    Supabase에서 range 기반 페이지네이션으로 전체 행을 가져온다.
    대용량 데이터의 경우 pagination/range 처리가 필요할 수 있음.
    """
    all_rows = []
    start = 0
    while True:
        end = start + page_size - 1
        response = client.table(table_name).select("*").range(start, end).execute()
        rows = response.data or []
        all_rows.extend(rows)
        if len(rows) < page_size:
            break
        start += page_size
    return all_rows


@st.cache_data(show_spinner=False, ttl=300)
def load_data_from_supabase() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Supabase에서 sales/stores/population 데이터를 읽는다."""
    if create_client is None:
        raise ImportError(
            "`supabase` 패키지를 찾지 못했습니다. `pip install supabase` 후 다시 실행하세요."
        )

    if "supabase" not in st.secrets:
        raise KeyError("`st.secrets['supabase']` 설정이 없습니다.")

    supa_url = st.secrets["supabase"].get("url")
    supa_key = st.secrets["supabase"].get("key")

    if not supa_url or not supa_key:
        raise KeyError("Supabase URL 또는 KEY가 비어 있습니다.")

    client = create_client(supa_url, supa_key)

    # MVP 기본은 select("*"), 내부적으로 range 기반 전체 조회를 사용
    sales_rows = fetch_all_rows(client, SUPABASE_TABLES["sales_2024"])
    stores_rows = fetch_all_rows(client, SUPABASE_TABLES["stores_2024"])
    pop_rows = fetch_all_rows(client, SUPABASE_TABLES["population_2024"])

    sales = pd.DataFrame(sales_rows)
    stores = pd.DataFrame(stores_rows)
    population = pd.DataFrame(pop_rows)

    if sales.empty or stores.empty or population.empty:
        raise ValueError("Supabase 테이블 데이터가 비어 있거나 조회되지 않았습니다.")

    return sales, stores, population


def load_data(source: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """
    source에 따라 CSV/Supabase를 로드한다.
    Supabase 실패 시 자동으로 로컬 CSV로 fallback한다.
    """
    if source == "로컬 CSV":
        sales, stores, population = load_data_from_csv()
        return sales, stores, population, "로컬 CSV"

    # source == "Supabase"
    try:
        sales, stores, population = load_data_from_supabase()
        st.success("Supabase 데이터를 성공적으로 불러왔습니다.")
        return sales, stores, population, "Supabase"
    except Exception as supa_err:  # noqa: BLE001
        st.warning(
            "Supabase 연결/조회에 실패하여 로컬 CSV로 자동 전환합니다.\n"
            f"원인: {supa_err}"
        )
        sales, stores, population = load_data_from_csv()
        return sales, stores, population, "로컬 CSV (fallback)"


# -----------------------------
# Preprocess / score helpers
# -----------------------------
def validate_columns_shape(df: pd.DataFrame, at_least: int, file_name: str) -> None:
    if df.shape[1] < at_least:
        raise ValueError(
            f"{file_name}: 필요한 컬럼 수가 부족합니다. 최소 {at_least}개 이상 필요합니다."
        )


def standardize_columns_by_position(
    sales_raw: pd.DataFrame, stores_raw: pd.DataFrame, pop_raw: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    공식 파일 컬럼 순서를 기준으로 표준 컬럼명을 부여한다.
    (원본 한글 컬럼명 인코딩 이슈를 피하기 위함)
    """
    validate_columns_shape(sales_raw, 7, "sales_2024")
    validate_columns_shape(stores_raw, 10, "stores_2024")
    validate_columns_shape(pop_raw, 4, "population_2024")

    sales = sales_raw.rename(
        columns={
            sales_raw.columns[0]: "quarter_code",
            sales_raw.columns[1]: "dong_code",
            sales_raw.columns[2]: "dong_name",
            sales_raw.columns[3]: "service_code",
            sales_raw.columns[4]: "service_name",
            sales_raw.columns[5]: "monthly_sales_amount",
            sales_raw.columns[6]: "monthly_sales_count",
        }
    ).copy()

    stores_map = {
        stores_raw.columns[0]: "quarter_code",
        stores_raw.columns[1]: "dong_code",
        stores_raw.columns[2]: "dong_name",
        stores_raw.columns[3]: "service_code",
        stores_raw.columns[4]: "service_name",
        stores_raw.columns[5]: "store_count",
        stores_raw.columns[9]: "close_rate",
    }
    if stores_raw.shape[1] > 11:
        stores_map[stores_raw.columns[11]] = "franchise_store_count"
    stores = stores_raw.rename(columns=stores_map).copy()

    population = pop_raw.rename(
        columns={
            pop_raw.columns[0]: "quarter_code",
            pop_raw.columns[1]: "dong_code",
            pop_raw.columns[2]: "dong_name",
            pop_raw.columns[3]: "floating_population",
        }
    ).copy()

    return sales, stores, population


def build_master_dataframe(
    sales_raw: pd.DataFrame, stores_raw: pd.DataFrame, pop_raw: pd.DataFrame
) -> pd.DataFrame:
    """데이터 결합 + 파생변수 + 창업유망점수 계산."""
    sales, stores, population = standardize_columns_by_position(sales_raw, stores_raw, pop_raw)

    sales_store_keys = ["quarter_code", "dong_code", "dong_name", "service_code", "service_name"]
    pop_keys = ["quarter_code", "dong_code", "dong_name"]

    merged = pd.merge(sales, stores, on=sales_store_keys, how="inner")
    merged = pd.merge(merged, population, on=pop_keys, how="left")

    for col in [
        "monthly_sales_amount",
        "monthly_sales_count",
        "store_count",
        "close_rate",
        "floating_population",
        "franchise_store_count",
    ]:
        if col in merged.columns:
            merged[col] = to_numeric_safe(merged[col])

    # 파생변수
    merged["sales_per_store"] = safe_divide(merged["monthly_sales_amount"], merged["store_count"])
    merged["sales_count_per_store"] = safe_divide(merged["monthly_sales_count"], merged["store_count"])
    merged["sales_per_floating_pop"] = safe_divide(
        merged["monthly_sales_amount"], merged["floating_population"]
    )
    merged["sales_count_per_floating_pop"] = safe_divide(
        merged["monthly_sales_count"], merged["floating_population"]
    )
    merged["avg_ticket"] = safe_divide(merged["monthly_sales_amount"], merged["monthly_sales_count"])
    if "franchise_store_count" in merged.columns:
        merged["franchise_ratio"] = safe_divide(merged["franchise_store_count"], merged["store_count"])
    else:
        merged["franchise_ratio"] = np.nan

    merged = merged.replace([np.inf, -np.inf], np.nan)

    # 점수화
    merged["score_sales_per_store"] = minmax_0_100(merged["sales_per_store"])
    merged["score_floating_pop"] = minmax_0_100(merged["floating_population"])
    merged["score_sales_per_floating_pop"] = minmax_0_100(merged["sales_per_floating_pop"])
    merged["score_close_stability"] = (100 - minmax_0_100(merged["close_rate"])).clip(0, 100)

    merged["startup_score"] = (
        0.35 * merged["score_sales_per_store"]
        + 0.25 * merged["score_floating_pop"]
        + 0.25 * merged["score_sales_per_floating_pop"]
        + 0.15 * merged["score_close_stability"]
    )
    return merged


def split_strengths_and_cautions(row: pd.Series) -> tuple[list[str], list[str]]:
    """규칙 기반 문장을 강점/주의점으로 분리한다."""
    strengths = []
    cautions = []

    if row["score_sales_per_store"] >= 70:
        strengths.append("점포당 매출이 높아 기존 점포의 매출 효율이 좋은 지역입니다.")
    if row["score_floating_pop"] >= 70:
        strengths.append("유동인구 규모가 커 잠재 고객 수요가 풍부한 지역입니다.")
    if row["score_sales_per_floating_pop"] >= 70:
        strengths.append("유동인구 대비 매출이 높아 실제 소비 전환력이 좋은 상권으로 볼 수 있습니다.")
    if row["score_close_stability"] >= 70:
        strengths.append("폐업률이 낮아 상대적으로 안정적인 상권으로 해석됩니다.")
    if row["score_close_stability"] < 40:
        cautions.append("폐업률이 높아 창업 전 경쟁 강도와 입지 조건을 추가 검토할 필요가 있습니다.")

    if not strengths:
        strengths.append("핵심 지표가 평균 수준이므로 세부 상권 조사와 현장 검토가 필요합니다.")
    if not cautions:
        cautions.append("특별한 위험 신호는 크지 않지만 업종 특성별 검토는 필요합니다.")
    return strengths, cautions


def prepare_display_columns(agg: pd.DataFrame) -> pd.DataFrame:
    """표/툴팁 표시용 포맷 컬럼을 추가한다."""
    disp = agg.copy()
    disp["총매출_표시"] = disp["total_sales"].apply(format_currency_krw)
    disp["점포당매출_표시"] = disp["avg_sales_per_store"].apply(format_currency_krw)
    disp["유동인구당매출_표시"] = disp["avg_sales_per_floating_pop"].apply(format_currency_krw)
    disp["유동인구_표시"] = disp["total_floating_pop"].apply(format_number)
    disp["점포수_표시"] = disp["total_stores"].apply(format_number)
    disp["폐업률_표시"] = disp["avg_close_rate"].apply(lambda x: format_percent(x, 2))
    disp["창업유망점수_표시"] = disp["startup_score"].apply(format_score)
    disp["점포당매출점수_표시"] = disp["score_sales_per_store"].apply(format_score)
    disp["유동인구점수_표시"] = disp["score_floating_pop"].apply(format_score)
    disp["유동인구당매출점수_표시"] = disp["score_sales_per_floating_pop"].apply(format_score)
    disp["폐업률안정성점수_표시"] = disp["score_close_stability"].apply(format_score)
    return disp


# -----------------------------
# UI render
# -----------------------------
def render_dashboard(
    df: pd.DataFrame,
    source_label: str,
    sales_rows: int,
    stores_rows: int,
    pop_rows: int,
) -> None:
    st.title("서울시 상권분석서비스 2024 창업 추천 MVP")
    st.caption("행정동별 상권 현황 시각화 + 규칙 기반 창업유망지역 추천")

    st.sidebar.header("데이터 설정")
    st.sidebar.info(f"현재 로딩 소스: {source_label}")

    # 필터
    st.sidebar.header("필터")
    quarter_options = ["전체"] + sorted(df["quarter_code"].dropna().astype(str).unique().tolist())
    service_options = ["전체"] + sorted(df["service_name"].dropna().astype(str).unique().tolist())

    selected_quarter = st.sidebar.selectbox("기준_년분기_코드", quarter_options, index=0)
    selected_service = st.sidebar.selectbox("서비스_업종_코드_명", service_options, index=0)
    min_store = st.sidebar.number_input("최소 점포 수", min_value=0, value=3, step=1)
    top_n = st.sidebar.slider("Top N", min_value=5, max_value=30, value=10, step=1)
    scatter_color_metric = st.sidebar.selectbox(
        "산점도 색상 기준", ["close_rate", "startup_score"], index=0
    )

    filtered = df.copy()
    if selected_quarter != "전체":
        filtered = filtered[filtered["quarter_code"].astype(str) == selected_quarter]
    if selected_service != "전체":
        filtered = filtered[filtered["service_name"].astype(str) == selected_service]
    filtered = filtered[filtered["store_count"].fillna(0) >= min_store]

    if filtered.empty:
        st.warning("선택한 업종/분기/점포 조건에 맞는 데이터가 없습니다. 필터를 조정해주세요.")
        st.stop()

    # KPI
    total_sales = filtered["monthly_sales_amount"].sum(skipna=True)
    total_stores = filtered["store_count"].sum(skipna=True)
    avg_sales_per_store = filtered["sales_per_store"].mean(skipna=True)
    avg_close_rate = filtered["close_rate"].mean(skipna=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("총매출", format_currency_krw(total_sales))
    k2.metric("총 점포 수", format_number(total_stores))
    k3.metric("평균 점포당 매출", format_currency_krw(avg_sales_per_store))
    k4.metric("평균 폐업률", format_percent(avg_close_rate, 2))

    # 집계
    agg = (
        filtered.groupby("dong_name", as_index=False)
        .agg(
            total_sales=("monthly_sales_amount", "sum"),
            total_stores=("store_count", "sum"),
            total_floating_pop=("floating_population", "sum"),
            avg_close_rate=("close_rate", "mean"),
            avg_sales_per_store=("sales_per_store", "mean"),
            avg_sales_per_floating_pop=("sales_per_floating_pop", "mean"),
            score_sales_per_store=("score_sales_per_store", "mean"),
            score_floating_pop=("score_floating_pop", "mean"),
            score_sales_per_floating_pop=("score_sales_per_floating_pop", "mean"),
            score_close_stability=("score_close_stability", "mean"),
            startup_score=("startup_score", "mean"),
        )
        .replace([np.inf, -np.inf], np.nan)
    )

    if agg.empty:
        st.warning("집계 결과가 비어 있어 시각화를 그릴 수 없습니다.")
        st.stop()

    agg_disp = prepare_display_columns(agg)
    overall_avg = {
        "avg_sales_per_store": agg["avg_sales_per_store"].mean(skipna=True),
        "total_floating_pop": agg["total_floating_pop"].mean(skipna=True),
        "avg_sales_per_floating_pop": agg["avg_sales_per_floating_pop"].mean(skipna=True),
        "avg_close_rate": agg["avg_close_rate"].mean(skipna=True),
    }

    st.subheader("행정동별 상권 시각화")

    # -------------------------
    # 1) 총매출 Top N
    # -------------------------
    top_sales = agg_disp.sort_values("total_sales", ascending=False).head(top_n)
    fig_sales = px.bar(
        top_sales.sort_values("total_sales"),
        x="total_sales",
        y="dong_name",
        orientation="h",
        title=f"행정동별 총매출 Top {top_n}",
    )
    fig_sales.update_traces(
        customdata=np.stack(
            [
                top_sales.sort_values("total_sales")["dong_name"],
                top_sales.sort_values("total_sales")["총매출_표시"],
                top_sales.sort_values("total_sales")["점포수_표시"],
                top_sales.sort_values("total_sales")["점포당매출_표시"],
                top_sales.sort_values("total_sales")["폐업률_표시"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>행정동</b>: %{customdata[0]}<br>"
            "<b>총매출</b>: %{customdata[1]}<br>"
            "<b>점포 수</b>: %{customdata[2]}<br>"
            "<b>점포당 매출</b>: %{customdata[3]}<br>"
            "<b>폐업률</b>: %{customdata[4]}<extra></extra>"
        ),
    )
    fig_sales.update_layout(yaxis_title="", xaxis_title="총매출")
    st.plotly_chart(fig_sales, use_container_width=True)
    top_sales_name = top_sales.iloc[0]["dong_name"]
    st.caption(f"해석: 선택 조건에서 총매출 1위 행정동은 `{top_sales_name}`입니다.")

    # -------------------------
    # 2) 점포당매출 Top N
    # -------------------------
    top_sps = agg_disp.sort_values("avg_sales_per_store", ascending=False).head(top_n)
    fig_sps = px.bar(
        top_sps.sort_values("avg_sales_per_store"),
        x="avg_sales_per_store",
        y="dong_name",
        orientation="h",
        title=f"행정동별 점포당 매출 Top {top_n}",
    )
    fig_sps.update_traces(
        customdata=np.stack(
            [
                top_sps.sort_values("avg_sales_per_store")["dong_name"],
                top_sps.sort_values("avg_sales_per_store")["점포당매출_표시"],
                top_sps.sort_values("avg_sales_per_store")["총매출_표시"],
                top_sps.sort_values("avg_sales_per_store")["점포수_표시"],
                top_sps.sort_values("avg_sales_per_store")["유동인구_표시"],
                top_sps.sort_values("avg_sales_per_store")["폐업률_표시"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>행정동</b>: %{customdata[0]}<br>"
            "<b>점포당 매출</b>: %{customdata[1]}<br>"
            "<b>총매출</b>: %{customdata[2]}<br>"
            "<b>점포 수</b>: %{customdata[3]}<br>"
            "<b>유동인구</b>: %{customdata[4]}<br>"
            "<b>폐업률</b>: %{customdata[5]}<extra></extra>"
        ),
    )
    fig_sps.update_layout(yaxis_title="", xaxis_title="점포당매출")
    st.plotly_chart(fig_sps, use_container_width=True)
    top_sps_name = top_sps.iloc[0]["dong_name"]
    st.caption(
        f"해석: 점포당 매출 1위는 `{top_sps_name}`이며, 점포당 매출은 점포 운영 효율을 보여주는 지표입니다."
    )

    # -------------------------
    # 3) 산점도 + 평균 기준선
    # -------------------------
    scatter = agg_disp.dropna(subset=["total_floating_pop", "total_sales", "total_stores"]).copy()
    if scatter.empty:
        st.warning("산점도에 표시할 데이터가 없어 그래프를 생략합니다.")
    else:
        color_col = scatter_color_metric if scatter_color_metric in scatter.columns else "startup_score"
        fig_scatter = px.scatter(
            scatter,
            x="total_floating_pop",
            y="total_sales",
            size="total_stores",
            color=color_col,
            title="유동인구와 매출 관계 산점도",
        )
        fig_scatter.update_traces(
            customdata=np.stack(
                [
                    scatter["dong_name"],
                    scatter["유동인구_표시"],
                    scatter["총매출_표시"],
                    scatter["점포수_표시"],
                    scatter["점포당매출_표시"],
                    scatter["창업유망점수_표시"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>행정동</b>: %{customdata[0]}<br>"
                "<b>총 유동인구</b>: %{customdata[1]}<br>"
                "<b>총매출</b>: %{customdata[2]}<br>"
                "<b>점포 수</b>: %{customdata[3]}<br>"
                "<b>점포당 매출</b>: %{customdata[4]}<br>"
                "<b>창업유망점수</b>: %{customdata[5]}<extra></extra>"
            ),
        )

        mean_pop = scatter["total_floating_pop"].mean(skipna=True)
        mean_sales = scatter["total_sales"].mean(skipna=True)
        fig_scatter.add_vline(x=mean_pop, line_dash="dot", line_color="gray")
        fig_scatter.add_hline(y=mean_sales, line_dash="dot", line_color="gray")
        fig_scatter.update_layout(xaxis_title="총_유동인구_수", yaxis_title="당월_매출_금액")
        st.plotly_chart(fig_scatter, use_container_width=True)

        st.markdown(
            "- 유동인구 높음 + 매출 높음: 대형 활성 상권  \n"
            "- 유동인구 높음 + 매출 낮음: 유동은 많지만 매출 전환 약함  \n"
            "- 유동인구 낮음 + 매출 높음: 목적형 소비 상권 가능성  \n"
            "- 유동인구 낮음 + 매출 낮음: 저활성 상권"
        )

    # -------------------------
    # 추천 섹션
    # -------------------------
    st.subheader("창업유망지역 추천")
    reco = agg_disp.sort_values("startup_score", ascending=False).head(top_n).copy()
    reco["강점"] = reco.apply(lambda r: split_strengths_and_cautions(r)[0], axis=1)
    reco["주의점"] = reco.apply(lambda r: split_strengths_and_cautions(r)[1], axis=1)
    reco["추천사유"] = reco.apply(lambda r: " ".join(split_strengths_and_cautions(r)[0]), axis=1)

    reco_table = reco.rename(
        columns={
            "dong_name": "행정동_코드_명",
            "startup_score": "창업유망점수",
            "score_sales_per_store": "점포당매출점수",
            "score_floating_pop": "유동인구점수",
            "score_sales_per_floating_pop": "유동인구당매출점수",
            "score_close_stability": "폐업률안정성점수",
            "total_sales": "총매출",
            "avg_sales_per_store": "점포당매출",
            "total_floating_pop": "총_유동인구_수",
            "avg_sales_per_floating_pop": "유동인구당매출",
            "total_stores": "점포_수",
            "avg_close_rate": "폐업_률",
        }
    )

    st.dataframe(
        reco_table[
            [
                "행정동_코드_명",
                "창업유망점수",
                "점포당매출점수",
                "유동인구점수",
                "유동인구당매출점수",
                "폐업률안정성점수",
                "총매출",
                "점포당매출",
                "총_유동인구_수",
                "유동인구당매출",
                "점포_수",
                "폐업_률",
                "추천사유",
            ]
        ].style.format(
            {
                "창업유망점수": "{:.1f}",
                "점포당매출점수": "{:.1f}",
                "유동인구점수": "{:.1f}",
                "유동인구당매출점수": "{:.1f}",
                "폐업률안정성점수": "{:.1f}",
                "총매출": "{:,.0f}",
                "점포당매출": "{:,.0f}",
                "총_유동인구_수": "{:,.0f}",
                "유동인구당매출": "{:,.0f}",
                "점포_수": "{:,.0f}",
                "폐업_률": "{:.2f}",
            }
        ),
        use_container_width=True,
    )

    fig_reco = px.bar(
        reco.sort_values("startup_score"),
        x="startup_score",
        y="dong_name",
        orientation="h",
        title=f"창업유망점수 Top {top_n}",
        color="startup_score",
        color_continuous_scale="Blues",
    )
    sorted_reco = reco.sort_values("startup_score")
    fig_reco.update_traces(
        customdata=np.stack(
            [
                sorted_reco["dong_name"],
                sorted_reco["창업유망점수_표시"],
                sorted_reco["점포당매출점수_표시"],
                sorted_reco["유동인구점수_표시"],
                sorted_reco["유동인구당매출점수_표시"],
                sorted_reco["폐업률안정성점수_표시"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>행정동</b>: %{customdata[0]}<br>"
            "<b>창업유망점수</b>: %{customdata[1]}<br>"
            "<b>점포당매출점수</b>: %{customdata[2]}<br>"
            "<b>유동인구점수</b>: %{customdata[3]}<br>"
            "<b>유동인구당매출점수</b>: %{customdata[4]}<br>"
            "<b>폐업률안정성점수</b>: %{customdata[5]}<extra></extra>"
        ),
    )
    fig_reco.update_layout(yaxis_title="", xaxis_title="창업유망점수")
    st.plotly_chart(fig_reco, use_container_width=True)

    top_reco_name = reco.iloc[0]["dong_name"]
    st.caption(
        f"해석: 창업유망점수 1위는 `{top_reco_name}`이며, "
        "이 점수는 매출 효율·유동인구·매출 전환력·폐업률 안정성을 종합한 값입니다."
    )

    # Top 5 카드 (강점/주의점 분리 + 전체 평균 비교)
    st.markdown("### Top 5 행정동 카드")
    top5 = reco.head(5)
    card_cols = st.columns(5)
    for idx, row in top5.reset_index(drop=True).iterrows():
        strengths, cautions = split_strengths_and_cautions(row)
        with card_cols[idx]:
            st.markdown(f"#### {idx + 1}. {row['dong_name']}")
            st.markdown(f"- 창업유망점수: **{format_score(row['startup_score'])}**")
            st.markdown(
                f"- 점포당매출: {format_currency_krw(row['avg_sales_per_store'])} / "
                f"전체 평균 {format_currency_krw(overall_avg['avg_sales_per_store'])}"
            )
            st.markdown(
                f"- 총 유동인구: {format_number(row['total_floating_pop'])} / "
                f"전체 평균 {format_number(overall_avg['total_floating_pop'])}"
            )
            st.markdown(
                f"- 유동인구당매출: {format_currency_krw(row['avg_sales_per_floating_pop'])} / "
                f"전체 평균 {format_currency_krw(overall_avg['avg_sales_per_floating_pop'])}"
            )
            st.markdown(
                f"- 폐업률: {format_percent(row['avg_close_rate'], 2)} / "
                f"전체 평균 {format_percent(overall_avg['avg_close_rate'], 2)}"
            )
            st.markdown("**강점**")
            for s in strengths:
                st.caption(f"- {s}")
            st.markdown("**주의점**")
            for c in cautions:
                st.caption(f"- {c}")

    # 하단 안내
    st.markdown("---")
    st.markdown("### 유의사항")
    st.markdown("- 본 대시보드는 서울시 상권분석서비스의 행정동 단위 데이터를 기반으로 함")
    st.markdown("- 임대료, 권리금, 실제 영업이익, 개별 점포 입지 조건은 포함하지 않음")
    st.markdown("- 따라서 추천 결과는 창업 후보지 탐색을 위한 참고 자료로 활용해야 함")

    # 데이터 점검 섹션
    with st.expander("데이터 점검 보기"):
        st.write(f"- 현재 데이터 소스: `{source_label}`")
        st.write(f"- 매출 데이터 행 수: {format_number(sales_rows)}")
        st.write(f"- 점포 데이터 행 수: {format_number(stores_rows)}")
        st.write(f"- 유동인구 데이터 행 수: {format_number(pop_rows)}")
        st.write(f"- 결합 후 최종 데이터 행 수: {format_number(len(df))}")
        st.write(f"- 결측치 수(전체): {format_number(df.isna().sum().sum())}")
        st.write(f"- 점포 수가 0인 행 수: {format_number((df['store_count'] == 0).sum())}")
        st.write(f"- 유동인구가 0인 행 수: {format_number((df['floating_population'] == 0).sum())}")


def main() -> None:
    st.sidebar.header("데이터 소스")
    source = st.sidebar.radio("데이터 로딩 방식", ["로컬 CSV", "Supabase"], index=0)

    # 로딩
    try:
        sales_raw, stores_raw, pop_raw, source_label = load_data(source)
    except FileNotFoundError as exc:
        missing = [x for x in str(exc).split(",") if x]
        msg = "\n".join([f"- `{name}`" for name in missing])
        st.error(
            "필수 CSV 파일을 찾지 못했습니다. 아래 파일을 `data/` 폴더에 넣어주세요.\n\n"
            f"{msg}"
        )
        st.stop()
    except Exception as exc:  # noqa: BLE001
        st.error(
            "데이터 로딩 중 오류가 발생했습니다.\n"
            f"원인: {exc}\n"
            "Supabase 설정 또는 로컬 CSV 파일 상태를 확인해주세요."
        )
        st.stop()

    # 전처리/결합
    try:
        master = build_master_dataframe(sales_raw, stores_raw, pop_raw)
    except Exception as exc:  # noqa: BLE001
        st.error(
            "데이터 결합/전처리/점수 계산 중 오류가 발생했습니다.\n"
            f"원인: {exc}\n"
            "CSV 컬럼 구조 또는 Supabase 테이블 스키마를 확인해주세요."
        )
        st.stop()

    if master.empty:
        st.warning("결합된 데이터가 비어 있어 대시보드를 표시할 수 없습니다.")
        st.stop()

    render_dashboard(
        master,
        source_label=source_label,
        sales_rows=len(sales_raw),
        stores_rows=len(stores_raw),
        pop_rows=len(pop_raw),
    )


if __name__ == "__main__":
    main()
