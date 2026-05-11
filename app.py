# -*- coding: utf-8 -*-
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


def format_currency_krw(value: float) -> str:
    if pd.isna(value):
        return "-"
    value = float(value)
    abs_v = abs(value)
    sign = "-" if value < 0 else ""
    if abs_v >= 100_000_000:
        return f"{sign}{abs_v / 100_000_000:.1f} hundred million KRW"
    if abs_v >= 10_000:
        return f"{sign}{abs_v / 10_000:.1f} ten-thousand KRW"
    return f"{sign}{int(round(abs_v)):,} KRW"


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
    return f"{value:.1f}"


def read_csv_with_fallback(path: Path) -> pd.DataFrame:
    last_error = None
    for encoding in ("utf-8-sig", "cp949"):
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except Exception as exc:  # noqa: BLE001
            last_error = exc
    raise ValueError(f"Failed to read `{path.name}` with utf-8-sig/cp949: {last_error}")


def get_supabase_credentials() -> tuple[str, str]:
    """
    Supported secrets formats:
    1) [supabase] url, key
    2) SUPABASE_URL, SUPABASE_KEY
    3) [connections.supabase] SUPABASE_URL/SUPABASE_KEY or url/key
    """
    supa_url = None
    supa_key = None

    if "supabase" in st.secrets:
        supa_url = st.secrets["supabase"].get("url")
        supa_key = st.secrets["supabase"].get("key")

    if not supa_url or not supa_key:
        supa_url = st.secrets.get("SUPABASE_URL")
        supa_key = st.secrets.get("SUPABASE_KEY")

    if (not supa_url or not supa_key) and "connections" in st.secrets:
        connections = st.secrets["connections"]
        if "supabase" in connections:
            conn = connections["supabase"]
            supa_url = supa_url or conn.get("SUPABASE_URL") or conn.get("url")
            supa_key = supa_key or conn.get("SUPABASE_KEY") or conn.get("key")

    if not supa_url or not supa_key:
        top_keys = ", ".join(list(st.secrets.keys()))
        raise KeyError(
            "Supabase URL/KEY not found. "
            "Use [supabase] url/key, SUPABASE_URL/SUPABASE_KEY, "
            "or [connections.supabase] SUPABASE_URL/SUPABASE_KEY. "
            f"(Top-level keys: {top_keys})"
        )

    return supa_url, supa_key


@st.cache_data(show_spinner=False)
def load_data_from_csv() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    missing = [name for name, path in REQUIRED_FILES.items() if not path.exists()]
    if missing:
        raise FileNotFoundError(",".join(missing))

    sales = read_csv_with_fallback(REQUIRED_FILES["sales_2024.csv"])
    stores = read_csv_with_fallback(REQUIRED_FILES["stores_2024.csv"])
    population = read_csv_with_fallback(REQUIRED_FILES["population_2024.csv"])
    return sales, stores, population


def fetch_all_rows(client, table_name: str, page_size: int = 1000) -> list[dict]:
    # For large tables, range pagination is required.
    all_rows: list[dict] = []
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
    if create_client is None:
        raise ImportError("`supabase` package is missing. Install dependencies and retry.")

    supa_url, supa_key = get_supabase_credentials()
    client = create_client(supa_url, supa_key)

    sales_rows = fetch_all_rows(client, SUPABASE_TABLES["sales_2024"])
    stores_rows = fetch_all_rows(client, SUPABASE_TABLES["stores_2024"])
    pop_rows = fetch_all_rows(client, SUPABASE_TABLES["population_2024"])

    sales = pd.DataFrame(sales_rows)
    stores = pd.DataFrame(stores_rows)
    population = pd.DataFrame(pop_rows)

    if sales.empty or stores.empty or population.empty:
        raise ValueError("Supabase table is empty or read access failed.")

    return sales, stores, population


def load_data(source: str) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    if source == "Local CSV":
        sales, stores, population = load_data_from_csv()
        return sales, stores, population, "Local CSV"

    try:
        sales, stores, population = load_data_from_supabase()
        st.success("Loaded data from Supabase.")
        return sales, stores, population, "Supabase"
    except Exception as supa_err:  # noqa: BLE001
        st.warning(
            "Supabase load failed. Falling back to local CSV.\n"
            f"Reason: {supa_err}"
        )
        sales, stores, population = load_data_from_csv()
        return sales, stores, population, "Local CSV (fallback)"


def to_numeric_safe(series: pd.Series) -> pd.Series:
    cleaned = (
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace("%", "", regex=False)
    )
    cleaned = cleaned.replace({"": np.nan, "-": np.nan, "nan": np.nan, "None": np.nan})
    return pd.to_numeric(cleaned, errors="coerce")


def safe_divide(numer: pd.Series, denom: pd.Series) -> pd.Series:
    return numer / denom.replace(0, np.nan)


def minmax_0_100(series: pd.Series) -> pd.Series:
    s = series.astype(float)
    min_v = s.min(skipna=True)
    max_v = s.max(skipna=True)
    if pd.isna(min_v) or pd.isna(max_v):
        return pd.Series(0.0, index=series.index)
    if np.isclose(min_v, max_v):
        return pd.Series(50.0, index=series.index)
    return ((s - min_v) / (max_v - min_v) * 100).clip(0, 100)


def validate_columns_shape(df: pd.DataFrame, at_least: int, name: str) -> None:
    if df.shape[1] < at_least:
        raise ValueError(f"{name}: expected at least {at_least} columns, got {df.shape[1]}")


def standardize_columns_by_position(
    sales_raw: pd.DataFrame,
    stores_raw: pd.DataFrame,
    pop_raw: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
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
    sales_raw: pd.DataFrame,
    stores_raw: pd.DataFrame,
    pop_raw: pd.DataFrame,
) -> pd.DataFrame:
    sales, stores, population = standardize_columns_by_position(sales_raw, stores_raw, pop_raw)

    merge_keys_sales_stores = [
        "quarter_code",
        "dong_code",
        "dong_name",
        "service_code",
        "service_name",
    ]
    merge_keys_pop = ["quarter_code", "dong_code", "dong_name"]

    merged = pd.merge(sales, stores, on=merge_keys_sales_stores, how="inner")
    merged = pd.merge(merged, population, on=merge_keys_pop, how="left")

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
    strengths: list[str] = []
    cautions: list[str] = []

    if row["score_sales_per_store"] >= 70:
        strengths.append("High sales-per-store efficiency.")
    if row["score_floating_pop"] >= 70:
        strengths.append("Large floating population supports demand.")
    if row["score_sales_per_floating_pop"] >= 70:
        strengths.append("Strong spending conversion from floating population.")
    if row["score_close_stability"] >= 70:
        strengths.append("Relatively stable district with lower closure risk.")
    if row["score_close_stability"] < 40:
        cautions.append("High closure risk; validate competition and location conditions.")

    if not strengths:
        strengths.append("Core indicators are around average; perform additional local research.")
    if not cautions:
        cautions.append("No strong red flag found, but category-specific checks are still needed.")
    return strengths, cautions


def prepare_display_columns(agg: pd.DataFrame) -> pd.DataFrame:
    disp = agg.copy()
    disp["sales_display"] = disp["total_sales"].apply(format_currency_krw)
    disp["sales_per_store_display"] = disp["avg_sales_per_store"].apply(format_currency_krw)
    disp["sales_per_pop_display"] = disp["avg_sales_per_floating_pop"].apply(format_currency_krw)
    disp["population_display"] = disp["total_floating_pop"].apply(format_number)
    disp["stores_display"] = disp["total_stores"].apply(format_number)
    disp["close_rate_display"] = disp["avg_close_rate"].apply(lambda x: format_percent(x, 2))
    disp["score_display"] = disp["startup_score"].apply(format_score)
    disp["score_sps_display"] = disp["score_sales_per_store"].apply(format_score)
    disp["score_pop_display"] = disp["score_floating_pop"].apply(format_score)
    disp["score_spop_display"] = disp["score_sales_per_floating_pop"].apply(format_score)
    disp["score_close_display"] = disp["score_close_stability"].apply(format_score)
    return disp


def render_dashboard(
    df: pd.DataFrame,
    source_label: str,
    sales_rows: int,
    stores_rows: int,
    pop_rows: int,
) -> None:
    st.title("Seoul Commercial Analysis Dashboard")
    st.caption("District-level visualization and rule-based startup recommendation")

    st.sidebar.header("Data Status")
    st.sidebar.info(f"Current source: {source_label}")

    st.sidebar.header("Filters")
    quarter_options = ["All"] + sorted(df["quarter_code"].dropna().astype(str).unique().tolist())
    service_options = ["All"] + sorted(df["service_name"].dropna().astype(str).unique().tolist())
    selected_quarter = st.sidebar.selectbox("Quarter", quarter_options, index=0)
    selected_service = st.sidebar.selectbox("Service category", service_options, index=0)
    min_store = st.sidebar.number_input("Minimum store count", min_value=0, value=3, step=1)
    top_n = st.sidebar.slider("Top N", min_value=5, max_value=30, value=10, step=1)
    scatter_color_metric = st.sidebar.selectbox(
        "Scatter color metric", ["close_rate", "startup_score"], index=0
    )

    filtered = df.copy()
    if selected_quarter != "All":
        filtered = filtered[filtered["quarter_code"].astype(str) == selected_quarter]
    if selected_service != "All":
        filtered = filtered[filtered["service_name"].astype(str) == selected_service]
    filtered = filtered[filtered["store_count"].fillna(0) >= min_store]

    if filtered.empty:
        st.warning("No rows match current filters. Please relax filter conditions.")
        st.stop()

    total_sales = filtered["monthly_sales_amount"].sum(skipna=True)
    total_stores = filtered["store_count"].sum(skipna=True)
    avg_sales_per_store = filtered["sales_per_store"].mean(skipna=True)
    avg_close_rate = filtered["close_rate"].mean(skipna=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total sales", format_currency_krw(total_sales))
    c2.metric("Total stores", format_number(total_stores))
    c3.metric("Avg sales per store", format_currency_krw(avg_sales_per_store))
    c4.metric("Avg closure rate", format_percent(avg_close_rate, 2))

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
        st.warning("Aggregated dataset is empty; charts cannot be rendered.")
        st.stop()

    agg_disp = prepare_display_columns(agg)
    overall_avg = {
        "avg_sales_per_store": agg["avg_sales_per_store"].mean(skipna=True),
        "total_floating_pop": agg["total_floating_pop"].mean(skipna=True),
        "avg_sales_per_floating_pop": agg["avg_sales_per_floating_pop"].mean(skipna=True),
        "avg_close_rate": agg["avg_close_rate"].mean(skipna=True),
    }

    st.subheader("District Charts")

    # Sales Top N
    top_sales = agg_disp.sort_values("total_sales", ascending=False).head(top_n)
    top_sales_sorted = top_sales.sort_values("total_sales")
    fig_sales = px.bar(
        top_sales_sorted,
        x="total_sales",
        y="dong_name",
        orientation="h",
        title=f"Top {top_n} Districts by Total Sales",
    )
    fig_sales.update_traces(
        customdata=np.stack(
            [
                top_sales_sorted["dong_name"],
                top_sales_sorted["sales_display"],
                top_sales_sorted["stores_display"],
                top_sales_sorted["sales_per_store_display"],
                top_sales_sorted["close_rate_display"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>District</b>: %{customdata[0]}<br>"
            "<b>Total Sales</b>: %{customdata[1]}<br>"
            "<b>Store Count</b>: %{customdata[2]}<br>"
            "<b>Sales per Store</b>: %{customdata[3]}<br>"
            "<b>Closure Rate</b>: %{customdata[4]}<extra></extra>"
        ),
    )
    fig_sales.update_layout(yaxis_title="", xaxis_title="Total Sales")
    st.plotly_chart(fig_sales, width="stretch")
    st.caption(f"Interpretation: Highest total-sales district is `{top_sales.iloc[0]['dong_name']}`.")

    # Sales per store Top N
    top_sps = agg_disp.sort_values("avg_sales_per_store", ascending=False).head(top_n)
    top_sps_sorted = top_sps.sort_values("avg_sales_per_store")
    fig_sps = px.bar(
        top_sps_sorted,
        x="avg_sales_per_store",
        y="dong_name",
        orientation="h",
        title=f"Top {top_n} Districts by Sales per Store",
    )
    fig_sps.update_traces(
        customdata=np.stack(
            [
                top_sps_sorted["dong_name"],
                top_sps_sorted["sales_per_store_display"],
                top_sps_sorted["sales_display"],
                top_sps_sorted["stores_display"],
                top_sps_sorted["population_display"],
                top_sps_sorted["close_rate_display"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>District</b>: %{customdata[0]}<br>"
            "<b>Sales per Store</b>: %{customdata[1]}<br>"
            "<b>Total Sales</b>: %{customdata[2]}<br>"
            "<b>Store Count</b>: %{customdata[3]}<br>"
            "<b>Floating Population</b>: %{customdata[4]}<br>"
            "<b>Closure Rate</b>: %{customdata[5]}<extra></extra>"
        ),
    )
    fig_sps.update_layout(yaxis_title="", xaxis_title="Sales per Store")
    st.plotly_chart(fig_sps, width="stretch")
    st.caption(
        f"Interpretation: Highest sales-per-store district is `{top_sps.iloc[0]['dong_name']}`. "
        "Sales-per-store is a store efficiency metric."
    )

    # Scatter with average lines
    scatter = agg_disp.dropna(subset=["total_floating_pop", "total_sales", "total_stores"]).copy()
    if scatter.empty:
        st.warning("No data available for scatter plot.")
    else:
        color_col = scatter_color_metric if scatter_color_metric in scatter.columns else "startup_score"
        fig_scatter = px.scatter(
            scatter,
            x="total_floating_pop",
            y="total_sales",
            size="total_stores",
            color=color_col,
            title="Floating Population vs Total Sales",
        )
        fig_scatter.update_traces(
            customdata=np.stack(
                [
                    scatter["dong_name"],
                    scatter["population_display"],
                    scatter["sales_display"],
                    scatter["stores_display"],
                    scatter["sales_per_store_display"],
                    scatter["score_display"],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>District</b>: %{customdata[0]}<br>"
                "<b>Floating Population</b>: %{customdata[1]}<br>"
                "<b>Total Sales</b>: %{customdata[2]}<br>"
                "<b>Store Count</b>: %{customdata[3]}<br>"
                "<b>Sales per Store</b>: %{customdata[4]}<br>"
                "<b>Startup Score</b>: %{customdata[5]}<extra></extra>"
            ),
        )
        fig_scatter.add_vline(
            x=scatter["total_floating_pop"].mean(skipna=True),
            line_dash="dot",
            line_color="gray",
        )
        fig_scatter.add_hline(
            y=scatter["total_sales"].mean(skipna=True),
            line_dash="dot",
            line_color="gray",
        )
        fig_scatter.update_layout(xaxis_title="Floating Population", yaxis_title="Total Sales")
        st.plotly_chart(fig_scatter, width="stretch")
        st.markdown(
            "- High population + high sales: highly active district  \n"
            "- High population + low sales: weak conversion  \n"
            "- Low population + high sales: destination-driven demand  \n"
            "- Low population + low sales: low-activity district"
        )

    # Recommendation
    st.subheader("Startup Recommendation")
    reco = agg_disp.sort_values("startup_score", ascending=False).head(top_n).copy()
    reco["strengths"] = reco.apply(lambda r: split_strengths_and_cautions(r)[0], axis=1)
    reco["cautions"] = reco.apply(lambda r: split_strengths_and_cautions(r)[1], axis=1)
    reco["reason"] = reco["strengths"].apply(lambda xs: " ".join(xs))

    reco_table = reco.rename(
        columns={
            "dong_name": "district",
            "startup_score": "startup_score",
            "score_sales_per_store": "score_sales_per_store",
            "score_floating_pop": "score_floating_pop",
            "score_sales_per_floating_pop": "score_sales_per_floating_pop",
            "score_close_stability": "score_close_stability",
            "total_sales": "total_sales",
            "avg_sales_per_store": "sales_per_store",
            "total_floating_pop": "floating_population",
            "avg_sales_per_floating_pop": "sales_per_floating_pop",
            "total_stores": "store_count",
            "avg_close_rate": "close_rate",
        }
    )
    st.dataframe(
        reco_table[
            [
                "district",
                "startup_score",
                "score_sales_per_store",
                "score_floating_pop",
                "score_sales_per_floating_pop",
                "score_close_stability",
                "total_sales",
                "sales_per_store",
                "floating_population",
                "sales_per_floating_pop",
                "store_count",
                "close_rate",
                "reason",
            ]
        ],
        width="stretch",
    )

    reco_sorted = reco.sort_values("startup_score")
    fig_reco = px.bar(
        reco_sorted,
        x="startup_score",
        y="dong_name",
        orientation="h",
        title=f"Top {top_n} Startup Score Districts",
        color="startup_score",
        color_continuous_scale="Blues",
    )
    fig_reco.update_traces(
        customdata=np.stack(
            [
                reco_sorted["dong_name"],
                reco_sorted["score_display"],
                reco_sorted["score_sps_display"],
                reco_sorted["score_pop_display"],
                reco_sorted["score_spop_display"],
                reco_sorted["score_close_display"],
            ],
            axis=-1,
        ),
        hovertemplate=(
            "<b>District</b>: %{customdata[0]}<br>"
            "<b>Startup Score</b>: %{customdata[1]}<br>"
            "<b>Sales/Store Score</b>: %{customdata[2]}<br>"
            "<b>Population Score</b>: %{customdata[3]}<br>"
            "<b>Sales/Population Score</b>: %{customdata[4]}<br>"
            "<b>Closure Stability Score</b>: %{customdata[5]}<extra></extra>"
        ),
    )
    fig_reco.update_layout(yaxis_title="", xaxis_title="Startup Score")
    st.plotly_chart(fig_reco, width="stretch")
    st.caption(
        f"Interpretation: Top startup district is `{reco.iloc[0]['dong_name']}`. "
        "The score combines sales efficiency, population, conversion, and closure stability."
    )

    st.markdown("### Top 5 District Cards")
    top5 = reco.head(5)
    cols = st.columns(5)
    for idx, row in top5.reset_index(drop=True).iterrows():
        strengths, cautions = split_strengths_and_cautions(row)
        with cols[idx]:
            st.markdown(f"#### {idx + 1}. {row['dong_name']}")
            st.markdown(f"- Startup score: **{format_score(row['startup_score'])}**")
            st.markdown(
                f"- Sales/store: {format_currency_krw(row['avg_sales_per_store'])} / "
                f"overall avg {format_currency_krw(overall_avg['avg_sales_per_store'])}"
            )
            st.markdown(
                f"- Floating pop: {format_number(row['total_floating_pop'])} / "
                f"overall avg {format_number(overall_avg['total_floating_pop'])}"
            )
            st.markdown(
                f"- Sales/pop: {format_currency_krw(row['avg_sales_per_floating_pop'])} / "
                f"overall avg {format_currency_krw(overall_avg['avg_sales_per_floating_pop'])}"
            )
            st.markdown(
                f"- Close rate: {format_percent(row['avg_close_rate'], 2)} / "
                f"overall avg {format_percent(overall_avg['avg_close_rate'], 2)}"
            )
            st.markdown("**Strengths**")
            for s in strengths:
                st.caption(f"- {s}")
            st.markdown("**Cautions**")
            for c in cautions:
                st.caption(f"- {c}")

    st.markdown("---")
    st.markdown("### Notes")
    st.markdown("- This dashboard uses district-level aggregated public data.")
    st.markdown("- Rent, key money, actual profit, and micro-location factors are not included.")
    st.markdown("- Use the recommendation as a shortlist reference, not a final decision.")

    with st.expander("Data QA Snapshot"):
        st.write(f"- Current source: `{source_label}`")
        st.write(f"- Sales rows: {format_number(sales_rows)}")
        st.write(f"- Stores rows: {format_number(stores_rows)}")
        st.write(f"- Population rows: {format_number(pop_rows)}")
        st.write(f"- Merged rows: {format_number(len(df))}")
        st.write(f"- Missing values (total): {format_number(df.isna().sum().sum())}")
        st.write(f"- Rows with store_count == 0: {format_number((df['store_count'] == 0).sum())}")
        st.write(
            "- Rows with floating_population == 0: "
            f"{format_number((df['floating_population'] == 0).sum())}"
        )


def main() -> None:
    st.sidebar.header("Data Source")
    source = st.sidebar.radio("Load from", ["Local CSV", "Supabase"], index=0)

    try:
        sales_raw, stores_raw, pop_raw, source_label = load_data(source)
    except FileNotFoundError as exc:
        missing = [x for x in str(exc).split(",") if x]
        msg = "\n".join([f"- `{name}`" for name in missing])
        st.error(f"Required CSV files are missing:\n\n{msg}")
        st.stop()
    except Exception as exc:  # noqa: BLE001
        st.error(f"Data loading failed: {exc}")
        st.stop()

    try:
        master = build_master_dataframe(sales_raw, stores_raw, pop_raw)
    except Exception as exc:  # noqa: BLE001
        st.error(f"Preprocess/merge/scoring failed: {exc}")
        st.stop()

    if master.empty:
        st.warning("Merged dataset is empty.")
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
