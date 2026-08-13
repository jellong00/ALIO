# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st

from utils.data import load_dataset
from utils.stats import descriptive_stats, stats_to_display_df

st.set_page_config(page_title="요약통계 실습", page_icon="🧮", layout="wide")
st.title("🧮 12. 요약통계 실습")
st.caption("데이터셋과 변수를 직접 선택하여 요약통계를 계산해봅니다.")

DATASETS = {
    "수입지출현황": "finance",
    "법인세정보": "tax",
    "임직원수현황": "employees",
    "직원평균보수현황": "compensation",
    "임원연봉": "executive_pay",
    "신규채용현황": "recruitment",
    "복리후생비": "welfare",
    "기관장업무추진비": "business_expense",
}

c1, c2 = st.columns(2)
with c1:
    dataset_label = st.selectbox("데이터셋", list(DATASETS.keys()))
df = load_dataset(DATASETS[dataset_label])
if df.empty:
    st.stop()

with c2:
    variable = st.selectbox("변수 (항목)", sorted(df["항목"].unique()))

sub_df = df[df["항목"] == variable]

c3, c4, c5 = st.columns(3)
with c3:
    if "구분" in sub_df.columns and sub_df["구분"].nunique() > 1:
        gubun_options = ["전체"] + sorted(sub_df["구분"].dropna().unique().tolist())
        gubun = st.selectbox("구분", gubun_options)
        if gubun != "전체":
            sub_df = sub_df[sub_df["구분"] == gubun]
with c4:
    years = sorted(sub_df["연도"].unique(), reverse=True)
    year = st.selectbox("연도", years, index=years.index(2025) if 2025 in years else 0)
    sub_df = sub_df[sub_df["연도"] == year]
with c5:
    type_options = ["전체"] + sorted(sub_df["기관유형"].dropna().unique().tolist())
    inst_type = st.selectbox("기관유형", type_options)
    if inst_type != "전체":
        sub_df = sub_df[sub_df["기관유형"] == inst_type]

st.divider()
st.subheader(f"결과: {dataset_label} - {variable} ({year}년)")

stats = descriptive_stats(sub_df["값"])
st.dataframe(stats_to_display_df(stats), hide_index=True, use_container_width=True)

with st.expander("통계량 설명 보기"):
    st.markdown(
        """
- **N**: 전체 관측치(기관) 수
- **결측**: 값이 존재하지 않는 기관 수
- **평균(Mean)**: 모든 값의 합을 개수로 나눈 값. 극단값(이상치)에 민감합니다.
- **중앙값(Median)**: 값을 크기순으로 나열했을 때 정확히 가운데에 위치한 값. 이상치에 덜 민감합니다.
- **표준편차(SD)**: 평균으로부터 값들이 평균적으로 얼마나 떨어져 있는지를 나타내는 산포 지표.
- **최소값/최대값(Min/Max)**: 관측된 값의 범위.
- **Q1/Q3**: 값을 4등분했을 때 25%, 75% 지점의 값.
"""
    )
