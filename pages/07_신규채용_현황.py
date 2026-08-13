# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st

from utils.data import load_dataset
from utils.stats import descriptive_stats
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters
from utils.charts import plot_rank_bar

st.set_page_config(page_title="신규채용 현황", page_icon="🧑‍💼", layout="wide")
st.title("🧑‍💼 07. 신규채용 현황")
st.caption("채용 유형별 현황을 먼저 살펴본 뒤, 대표변수인 '일반정규직 총 신규채용'을 심화 분석합니다. (단위: 명)")

recruitment = load_dataset("recruitment")
panel = load_dataset("panel")
if recruitment.empty or panel.empty:
    st.stop()

st.subheader("채용 유형 한눈에 보기")
years_sorted = sorted(recruitment["연도"].unique(), reverse=True)
year_for_overview = st.selectbox("연도 선택", years_sorted, index=years_sorted.index(2025) if 2025 in years_sorted else 0)

rows = []
for item in recruitment["항목"].unique():
    sub = recruitment[(recruitment["항목"] == item) & (recruitment["연도"] == year_for_overview)]["값"]
    st_ = descriptive_stats(sub)
    rows.append({
        "채용 유형": item,
        "평균": round(st_["mean"], 1) if pd.notna(st_["mean"]) else None,
        "중앙값": st_["median"],
        "0명 비율(%)": st_["zero_pct"], "최대값": st_["max"],
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.header("대표변수 심화분석: 일반정규직 총 신규채용")

filters = render_common_filters(panel, key_prefix="recruit")
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(filtered, variable="신규채용", year=filters.get("연도", 2025), unit="명")

st.divider()
st.subheader("채용 인원 구간별 분포")
year_cat = filters.get("연도", 2025)
cat_df = filtered[filtered["연도"] == year_cat].copy()

def categorize(v):
    if pd.isna(v):
        return None
    if v == 0:
        return "0명"
    if v <= 2:
        return "1-2명"
    if v <= 5:
        return "3-5명"
    if v <= 10:
        return "6-10명"
    return "11명 이상"

cat_df["구간"] = cat_df["신규채용"].apply(categorize)
order = ["0명", "1-2명", "3-5명", "6-10명", "11명 이상"]
counts = cat_df["구간"].value_counts().reindex(order).fillna(0).astype(int)

import plotly.express as px
fig = px.bar(x=counts.index, y=counts.values, labels={"x": "채용 인원 구간", "y": "기관 수"})
fig.update_layout(template="plotly_white", title=f"신규채용 인원 구간별 기관 수 ({year_cat}년)")
st.plotly_chart(fig, use_container_width=True)
