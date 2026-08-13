# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st

from utils.data import load_dataset
from utils.stats import descriptive_stats
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters
from utils.constants import NOTE_AGGREGATE

st.set_page_config(page_title="직원보수 현황", page_icon="💵", layout="wide")
st.title("💵 08. 직원보수 현황")
st.caption("직원 평균보수의 구성요소를 먼저 살펴본 뒤, 대표변수인 '1인당 평균보수액'을 심화 분석합니다. (단위: 천원, 정규직(일반정규직) 기준)")
st.info(NOTE_AGGREGATE)

compensation = load_dataset("compensation")
panel = load_dataset("panel")
if compensation.empty or panel.empty:
    st.stop()

comp_main = compensation[compensation["구분"] == "정규직(일반정규직)"]

st.subheader("보수 구성요소 한눈에 보기")
years_sorted = sorted(comp_main["연도"].unique(), reverse=True)
year_for_overview = st.selectbox("연도 선택", years_sorted, index=years_sorted.index(2025) if 2025 in years_sorted else 0)

component_items = ["기본급", "고정수당", "실적수당", "급여성 복리후생비", "성과상여금", "(경영평가 성과급)", "기타", "1인당 평균보수액"]
rows = []
for item in component_items:
    sub = comp_main[(comp_main["항목"] == item) & (comp_main["연도"] == year_for_overview)]["값"]
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
st.header("대표변수 심화분석: 1인당 평균보수액")

filters = render_common_filters(panel, key_prefix="comp")
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(filtered, variable="직원평균보수", year=filters.get("연도", 2025), unit="천원")

st.divider()
st.subheader("남성·여성 평균보수 비교 (참고)")
st.caption("※ 기관 수준 집계자료이므로 개인 수준의 성별 임금격차로 해석하지 않습니다.")

year_cmp = filters.get("연도", 2025)
cmp_df = filtered[filtered["연도"] == year_cmp][["남성평균보수", "여성평균보수"]].mean()
if cmp_df.notna().any():
    import plotly.express as px
    fig = px.bar(x=["남성", "여성"], y=[cmp_df.get("남성평균보수"), cmp_df.get("여성평균보수")],
                 labels={"x": "", "y": "평균보수(천원)"})
    fig.update_layout(template="plotly_white", title=f"성별 평균보수 비교 ({year_cmp}년, 기관 평균)")
    st.plotly_chart(fig, use_container_width=True)
