import streamlit as st
import pandas as pd
from pathlib import Path

# TODO: set actual Parquet path from config
DEFAULT_PARQUET = Path(__file__).resolve().parents[1] / "data" / "processed" / "listings.parquet"


def load_data(path: Path = DEFAULT_PARQUET) -> pd.DataFrame:
    """Load processed listings for admin view (TODO: error handling, caching)."""
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def main():
    st.set_page_config(page_title="Listing Admin", layout="wide")
    st.title("Listing Admin Dashboard")

    df = load_data()
    if df.empty:
        st.warning("No data found. Please run preprocessing pipeline first.")
        return

    with st.sidebar:
        st.header("Filters")
        cities = st.multiselect("城市", sorted(df["city"].dropna().unique()))
        districts = st.multiselect("城区", sorted(df["district"].dropna().unique()))
        min_price, max_price = st.slider("总价区间(万)", 0, int(df["total_price"].max() or 1000), (0, int(df["total_price"].max() or 1000)))

    mask = pd.Series(True, index=df.index)
    if cities:
        mask &= df["city"].isin(cities)
    if districts:
        mask &= df["district"].isin(districts)
    mask &= df["total_price"].between(min_price, max_price)
    filtered = df.loc[mask]

    st.subheader(f"数据概览（{len(filtered)} 条）")
    st.dataframe(filtered.head(200))

    st.subheader("价格分布")
    st.bar_chart(filtered["total_price"].dropna())

    st.subheader("面积 vs 单价")
    st.scatter_chart(filtered, x="area", y="unit_price")


if __name__ == "__main__":
    main()
