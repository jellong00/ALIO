# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st

from utils.data import load_dataset
from utils.stats import descriptive_stats
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters
from utils.charts import plot_rank_bar
from utils.constants import NOTE_ZERO_VS_NA

st.set_page_config(page_title="복리후생비", page_icon="🎁", layout="wide")
st.title("🎁 11. 복리후생비")
st.caption("복리후생비는 항목이 많고 0값 비율이 높을 수 있어, 모든 항목을 깊게 분석하지 않습니다. (단위: 천원)")
st.info(NOTE_ZERO_VS_NA)

welfare = load_dataset("welfare")
panel = load_dataset("panel")
if welfare.empty or panel.empty:
    st.stop()

years_sorted = sorted(welfare["연도"].unique(), reverse=True)
year_for_overview = st.selectbox("연도 선택", years_sorted, index=years_sorted.index(2025) if 2025 in years_sorted else 0)

st.subheader("주요 항목별 한눈에 보기")
welfare_year = welfare[welfare["연도"] == year_for_overview]
main_items = [i for i in welfare["항목"].unique() if "소계" in str(i) or "총계" in str(i)]

rows = []
for item in main_items:
    sub = welfare_year[welfare_year["항목"] == item]["값"]
    st_ = descriptive_stats(sub)
    rows.append({
        "항목": item, "N": st_["n_valid"],
        "0 비율(%)": st_["zero_pct"],
        "평균": round(st_["mean"], 1) if pd.notna(st_["mean"]) else None,
        "중앙값": round(st_["median"], 1) if pd.notna(st_["median"]) else None,
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.subheader("항목별 0 비율")
zero_rows = []
for item in welfare["항목"].unique():
    sub = welfare_year[welfare_year["항목"] == item]["값"]
    st_ = descriptive_stats(sub)
    zero_rows.append({"항목": item, "0 비율(%)": st_["zero_pct"] if pd.notna(st_["zero_pct"]) else 0})
zero_df = pd.DataFrame(zero_rows).sort_values("0 비율(%)", ascending=True)
st.plotly_chart(
    plot_rank_bar(zero_df.assign(**{"0 비율(%)": zero_df["0 비율(%)"]}), "항목", "0 비율(%)", top_n=len(zero_df), title=f"항목별 0 비율 ({year_for_overview}년)", ascending=False),
    use_container_width=True,
)

st.divider()
st.header("대표변수 심화분석: 총 복리후생비")

filters = render_common_filters(panel, key_prefix="welfare")
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(filtered, variable="총복리후생비", year=filters.get("연도", 2025), unit="천원")
