# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

from utils.data import load_dataset
from utils.stats import descriptive_stats
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters

st.set_page_config(page_title="임직원 현황", page_icon="👥", layout="wide")
st.title("👥 06. 임직원 현황")
st.caption("주요 임직원 변수를 먼저 살펴본 뒤, 대표변수인 '총 임직원수'를 심화 분석합니다. (단위: 명)")

employees = load_dataset("employees")
panel = load_dataset("panel")
if employees.empty or panel.empty:
    st.stop()

st.subheader("임직원 변수 한눈에 보기")
years_sorted = sorted(employees["연도"].unique(), reverse=True)
year_for_overview = st.selectbox("연도 선택", years_sorted, index=years_sorted.index(2025) if 2025 in years_sorted else 0)

key_items = [
    "임직원 총계(A+B+C)", "정규직-일반정규직-현원-계", "정규직-무기계약직-현원-계",
    "여성 현원-합계", "비정규직-기간제-계", "임원-상임임원정원(A)",
]
rows = []
for item in key_items:
    sub = employees[(employees["항목"] == item) & (employees["연도"] == year_for_overview)]["값"]
    if sub.empty:
        continue
    st_ = descriptive_stats(sub)
    rows.append({
        "항목": item,
        "평균": round(st_["mean"], 1) if pd.notna(st_["mean"]) else None,
        "중앙값": round(st_["median"], 1) if pd.notna(st_["median"]) else None,
        "0 비율(%)": st_["zero_pct"], "최대값": st_["max"],
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()
st.header("대표변수 심화분석: 총 임직원수")

filters = render_common_filters(panel, key_prefix="emp")
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(filtered, variable="임직원수", year=filters.get("연도", 2025), unit="명")

st.caption("파생변수: 여성직원비율 = 여성직원수 / 임직원수, 비정규직비율 = 비정규직수 / 임직원수 (분모 0은 결측 처리)")
