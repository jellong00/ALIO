# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

from utils.data import load_dataset
from utils.stats import descriptive_stats
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters

st.set_page_config(page_title="수입 현황", page_icon="💰", layout="wide")
st.title("💰 03. 수입 현황")
st.caption("기관 수입 관련 항목을 먼저 살펴본 뒤, 대표변수인 '총수입'을 심화 분석합니다. (단위: 백만원)")

finance = load_dataset("finance")
panel = load_dataset("panel")
if finance.empty or panel.empty:
    st.stop()

income_items = [i for i in finance["항목"].unique() if str(i).startswith("수입")]

st.subheader("수입 변수 한눈에 보기")
year_for_overview = st.selectbox("연도 선택", sorted(finance["연도"].unique(), reverse=True), index=list(sorted(finance["연도"].unique(), reverse=True)).index(2025) if 2025 in finance["연도"].unique() else 0)

rows = []
for item in income_items:
    sub = finance[(finance["항목"] == item) & (finance["연도"] == year_for_overview)]["값"]
    st_ = descriptive_stats(sub)
    rows.append({
        "항목": item, "평균": round(st_["mean"], 1) if pd.notna(st_["mean"]) else None,
        "중앙값": round(st_["median"], 1) if pd.notna(st_["median"]) else None,
        "0 비율(%)": st_["zero_pct"], "최대값": st_["max"],
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.header("대표변수 심화분석: 총수입")

filters = render_common_filters(panel, key_prefix="income")
# 연도는 render_distribution_analysis 내부에서 별도로 처리하므로
# 기관유형/기관명 필터만 미리 적용하고 연도 필터는 제외한다.
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(
    filtered,
    variable="총수입",
    year=filters.get("연도", 2025),
    unit="백만원",
)
