# -*- coding: cp949 -*-
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Seoul Commercial Dashboard MVP", layout="wide")

DATA_DIR = Path("data")
REQUIRED_FILES = {
    "sales_2024.csv": DATA_DIR / "sales_2024.csv",
    "stores_2024.csv": DATA_DIR / "stores_2024.csv",
    "population_2024.csv": DATA_DIR / "population_2024.csv",
}


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    """Try utf-8-sig first, then cp949."""
    last_error = None
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise ValueError(f"Cannot read {path.name} with utf-8-sig/cp949: {last_error}")


def to_numeric_safe(series: pd.Series) -> pd.Series:
    """Convert comma-separated strings to numeric safely."""
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("%", "", regex=False)
    )
    cleaned = cleaned.replace({"": np.nan, "-": np.nan, "nan": np.nan, "None": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


def safe_div(numer: pd.Series, denom: pd.Series) -> pd.Series:
    """Return NaN where denominator is 0."""
    return numer / denom.replace(0, np.nan)


def minmax_0_100(series: pd.Series) -> pd.Series:
    """Min-max normalize to 0~100, return 50 for constants."""
    s = series.astype(float)
    min_v = s.min(skipna=True)
    max_v = s.max(skipna=True)
    if pd.isna(min_v) or pd.isna(max_v):
        return pd.Series(0.0, index=series.index)
    if np.isclose(min_v, max_v):
        return pd.Series(50.0, index=series.index)
    return ((s - min_v) / (max_v - min_v) * 100).clip(0, 100)


@st.cache_data(show_spinner=False)
def load_local_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Local CSV loader for MVP.
    This function is intentionally isolated for future Supabase migration.
    """
    missing = [name for name, path in REQUIRED_FILES.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(",".join(missing))

    sales = read_csv_with_fallback(REQUIRED_FILES["sales_2024.csv"])
    stores = read_csv_with_fallback(REQUIRED_FILES["stores_2024.csv"])
    population = read_csv_with_fallback(REQUIRED_FILES["population_2024.csv"])
    return sales, stores, population


def validate_columns_shape(df: pd.DataFrame, at_least: int, file_name: str) -> None:
    if df.shape[1] < at_least:
        raise ValueError(
            f"{file_name}: expected at least {at_least} columns, but got {df.shape[1]}"
        )


def standardize_columns_by_position(
    sales_raw: pd.DataFrame, stores_raw: pd.DataFrame, pop_raw: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Standardize columns based on official file order.
    This avoids encoding/display issues in raw Korean column names.
    """
    validate_columns_shape(sales_raw, 7, "sales_2024.csv")
    validate_columns_shape(stores_raw, 10, "stores_2024.csv")
    validate_columns_shape(pop_raw, 4, "population_2024.csv")

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
    """Merge files and build derived metrics + startup potential score."""
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

    # Derived variables
    merged["sales_per_store"] = safe_div(merged["monthly_sales_amount"], merged["store_count"])
    merged["sales_count_per_store"] = safe_div(merged["monthly_sales_count"], merged["store_count"])
    merged["sales_per_floating_pop"] = safe_div(
        merged["monthly_sales_amount"], merged["floating_population"]
    )
    merged["sales_count_per_floating_pop"] = safe_div(
        merged["monthly_sales_count"], merged["floating_population"]
    )
    merged["avg_ticket"] = safe_div(merged["monthly_sales_amount"], merged["monthly_sales_count"])
    if "franchise_store_count" in merged.columns:
        merged["franchise_ratio"] = safe_div(merged["franchise_store_count"], merged["store_count"])
    else:
        merged["franchise_ratio"] = np.nan

    merged = merged.replace([np.inf, -np.inf], np.nan)

    # Scoring
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


def build_reason(row: pd.Series) -> str:
    reasons = []
    if row["score_sales_per_store"] >= 70:
        reasons.append("점포당 매출이 높아 기존 점포의 매출 효율이 좋은 지역입니다.")
    if row["score_floating_pop"] >= 70:
        reasons.append("유동인구 규모가 커 잠재 고객 수요가 풍부한 지역입니다.")
    if row["score_sales_per_floating_pop"] >= 70:
        reasons.append("유동인구 대비 매출이 높아 실제 소비 전환력이 좋은 상권으로 볼 수 있습니다.")
    if row["score_close_stability"] >= 70:
        reasons.append("폐업률이 낮아 상대적으로 안정적인 상권으로 해석됩니다.")
    if row["score_close_stability"] < 40:
        reasons.append("다만 폐업률이 높아 창업 전 경쟁 강도와 입지 조건을 추가 검토할 필요가 있습니다.")
    if not reasons:
        return "핵심 지표가 평균 수준이므로 업종별 경쟁도와 입지 조건을 함께 검토하세요."
    return " ".join(reasons)


def fmt_int(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{int(round(value)):,}"


def fmt_float(value: float) -> str:
    if pd.isna(value):
        return "-"
    return f"{value:,.2f}"


def render_dashboard(df: pd.DataFrame) -> None:
    st.title("서울시 상권분석서비스 2024 창업 추천 MVP")
    st.caption("행정동별 상권 현황 시각화 및 규칙 기반 창업유망지역 추천")

    # Sidebar filters
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
        st.warning("선택 조건에 맞는 데이터가 없습니다. 필터를 완화해주세요.")
        st.stop()

    # KPI cards
    total_sales = filtered["monthly_sales_amount"].sum(skipna=True)
    total_stores = filtered["store_count"].sum(skipna=True)
    avg_sales_per_store = filtered["sales_per_store"].mean(skipna=True)
    avg_close_rate = filtered["close_rate"].mean(skipna=True)

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("총매출", f"{fmt_int(total_sales)} 원")
    k2.metric("총 점포 수", fmt_int(total_stores))
    k3.metric("평균 점포당 매출", f"{fmt_int(avg_sales_per_store)} 원")
    k4.metric("평균 폐업률", f"{fmt_float(avg_close_rate)}%")

    # Aggregate by dong
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

    st.subheader("행정동별 상권 시각화")

    # Top N by total sales
    top_sales = agg.sort_values("total_sales", ascending=False).head(top_n)
    fig_sales = px.bar(
        top_sales.sort_values("total_sales"),
        x="total_sales",
        y="dong_name",
        orientation="h",
        title=f"행정동별 총매출 Top {top_n}",
    )
    fig_sales.update_layout(yaxis_title="", xaxis_title="총매출")
    st.plotly_chart(fig_sales, use_container_width=True)

    # Top N by sales per store
    top_sales_per_store = agg.sort_values("avg_sales_per_store", ascending=False).head(top_n)
    fig_sps = px.bar(
        top_sales_per_store.sort_values("avg_sales_per_store"),
        x="avg_sales_per_store",
        y="dong_name",
        orientation="h",
        title=f"행정동별 점포당 매출 Top {top_n}",
    )
    fig_sps.update_layout(yaxis_title="", xaxis_title="점포당매출")
    st.plotly_chart(fig_sps, use_container_width=True)

    # Scatter plot
    scatter = agg.dropna(subset=["total_floating_pop", "total_sales", "total_stores"]).copy()
    color_col = scatter_color_metric if scatter_color_metric in scatter.columns else "startup_score"
    fig_scatter = px.scatter(
        scatter,
        x="total_floating_pop",
        y="total_sales",
        size="total_stores",
        color=color_col,
        hover_data={
            "dong_name": True,
            "total_sales": ":,.0f",
            "total_stores": ":,.0f",
            "avg_sales_per_store": ":,.0f",
            "avg_close_rate": ":.2f",
        },
        title="유동인구와 매출 관계 산점도",
    )
    fig_scatter.update_layout(xaxis_title="총_유동인구_수", yaxis_title="당월_매출_금액")
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Recommendation section
    st.subheader("창업유망지역 추천")
    reco = agg.sort_values("startup_score", ascending=False).head(top_n).copy()
    reco["reason"] = reco.apply(build_reason, axis=1)

    reco_table = reco.rename(
        columns={
            "dong_name": "행정동_코드_명",
            "startup_score": "창업유망점수",
            "total_sales": "총매출",
            "avg_sales_per_store": "점포당매출",
            "total_floating_pop": "총_유동인구_수",
            "avg_sales_per_floating_pop": "유동인구당매출",
            "total_stores": "점포_수",
            "avg_close_rate": "폐업_률",
            "reason": "추천사유",
        }
    )
    st.dataframe(
        reco_table[
            [
                "행정동_코드_명",
                "창업유망점수",
                "총매출",
                "점포당매출",
                "총_유동인구_수",
                "유동인구당매출",
                "점포_수",
                "폐업_률",
                "추천사유",
            ]
        ],
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
    fig_reco.update_layout(yaxis_title="", xaxis_title="창업유망점수")
    st.plotly_chart(fig_reco, use_container_width=True)

    # Top 5 cards
    st.markdown("### Top 5 행정동 카드")
    top5 = reco.head(5)
    cols = st.columns(5)
    for idx, row in top5.reset_index(drop=True).iterrows():
        with cols[idx]:
            st.markdown(f"#### {idx + 1}. {row['dong_name']}")
            st.markdown(f"- 창업유망점수: **{fmt_float(row['startup_score'])}**")
            st.markdown(f"- 총매출: {fmt_int(row['total_sales'])} 원")
            st.markdown(f"- 점포당매출: {fmt_int(row['avg_sales_per_store'])} 원")
            st.markdown(f"- 총 유동인구: {fmt_int(row['total_floating_pop'])}")
            st.markdown(f"- 유동인구당매출: {fmt_float(row['avg_sales_per_floating_pop'])}")
            st.markdown(f"- 점포 수: {fmt_int(row['total_stores'])}")
            st.markdown(f"- 폐업률: {fmt_float(row['avg_close_rate'])}%")
            st.caption(row["reason"])

    # Notice
    st.markdown("---")
    st.markdown("### 유의사항")
    st.markdown("- 본 대시보드는 서울시 상권분석서비스의 행정동 단위 데이터를 기반으로 함")
    st.markdown("- 임대료, 권리금, 실제 영업이익, 개별 점포 입지 조건은 포함하지 않음")
    st.markdown("- 따라서 추천 결과는 창업 후보지 탐색을 위한 참고 자료로 활용해야 함")


def main() -> None:
    try:
        sales_raw, stores_raw, pop_raw = load_local_data()
    except FileNotFoundError as exc:
        missing = [x for x in str(exc).split(",") if x]
        msg = "\n".join([f"- `{name}`" for name in missing])
        st.error(
            "필수 CSV 파일을 찾지 못했습니다. 아래 파일을 data 폴더에 넣어주세요.\n\n"
            f"{msg}"
        )
        st.stop()
    except Exception as exc:  # noqa: BLE001
        st.error(f"데이터 로딩 중 오류가 발생했습니다: {exc}")
        st.stop()

    try:
        master = build_master_dataframe(sales_raw, stores_raw, pop_raw)
    except Exception as exc:  # noqa: BLE001
        st.error(
            "데이터 결합/전처리/점수계산 중 오류가 발생했습니다.\n"
            f"원인: {exc}\n"
            "CSV 형식 또는 데이터 값을 확인해주세요."
        )
        st.stop()

    render_dashboard(master)


if __name__ == "__main__":
    main()
