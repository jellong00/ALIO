# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

from utils.data import load_dataset
from utils.stats import descriptive_stats, safe_ratio
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters
from utils.charts import plot_donut

st.set_page_config(page_title="지출 현황", page_icon="💸", layout="wide")
st.title("💸 04. 지출 현황")
st.caption("기관 지출 관련 항목을 먼저 살펴본 뒤, 대표변수인 '총지출'을 심화 분석합니다. (단위: 백만원)")

finance = load_dataset("finance")
panel = load_dataset("panel")
if finance.empty or panel.empty:
    st.stop()

expense_items = [i for i in finance["항목"].unique() if str(i).startswith("지출")]

st.subheader("지출 변수 한눈에 보기")
years_sorted = sorted(finance["연도"].unique(), reverse=True)
year_for_overview = st.selectbox("연도 선택", years_sorted, index=years_sorted.index(2025) if 2025 in years_sorted else 0)

rows = []
for item in expense_items:
    sub = finance[(finance["항목"] == item) & (finance["연도"] == year_for_overview)]["값"]
    st_ = descriptive_stats(sub)
    rows.append({
        "항목": item, "평균": round(st_["mean"], 1) if pd.notna(st_["mean"]) else None,
        "중앙값": round(st_["median"], 1) if pd.notna(st_["median"]) else None,
        "0 비율(%)": st_["zero_pct"], "최대값": st_["max"],
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.header("대표변수 심화분석: 총지출")

filters = render_common_filters(panel, key_prefix="expense")
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(
    filtered,
    variable="총지출",
    year=filters.get("연도", 2025),
    unit="백만원",
)

st.divider()
st.subheader("지출 구성비 (기관 1개 선택 시)")

if filters.get("기관명", "전체") != "전체":
    inst_row = panel[(panel["기관명"] == filters["기관명"]) & (panel["연도"] == filters.get("연도", 2025))]
    if not inst_row.empty:
        row = inst_row.iloc[0]
        total = row.get("총지출", None)
        comp_items = {"인건비": row.get("인건비"), "경상운영비": row.get("경상운영비"), "사업비": row.get("사업비")}
        comp_items = {k: v for k, v in comp_items.items() if pd.notna(v)}
        if comp_items and pd.notna(total) and total != 0:
            fig = plot_donut(list(comp_items.keys()), list(comp_items.values()), title=f"{filters['기관명']} 지출 구성비 ({filters.get('연도',2025)}년)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("구성비를 계산할 데이터가 부족합니다 (분모 0 또는 결측).")
else:
    st.info("상단 필터에서 기관명을 선택하면 지출 구성비를 확인할 수 있습니다.")
