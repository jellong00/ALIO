# -*- coding: utf-8 -*-
import streamlit as st
import plotly.express as px

from utils.data import load_dataset
from utils.stats import group_summary
from utils.charts import plot_group_boxplot

st.set_page_config(page_title="집단별 분포", page_icon="📊", layout="wide")
st.title("📊 14. 집단별 분포")
st.caption("분석 변수를 집단 변수(예: 기관유형)로 나누어 비교합니다. 통계적 검정(t-test, ANOVA 등)은 자동으로 수행하지 않습니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

numeric_cols = [c for c in panel.select_dtypes(include="number").columns if c != "연도"]
cat_cols = [c for c in ["기관유형", "주무부처"] if c in panel.columns]

c1, c2, c3 = st.columns(3)
with c1:
    variable = st.selectbox("분석 변수", numeric_cols)
with c2:
    group_col = st.selectbox("집단 변수", cat_cols)
with c3:
    years = sorted(panel["연도"].dropna().unique(), reverse=True)
    year = st.selectbox("연도", years, index=years.index(2025) if 2025 in years else 0)

data = panel[panel["연도"] == year][[variable, group_col]].dropna()

st.subheader("집단별 요약통계")
summary = group_summary(data, variable, group_col)
st.dataframe(summary, use_container_width=True, hide_index=True)

c4, c5 = st.columns(2)
with c4:
    st.plotly_chart(plot_group_boxplot(data, variable, group_col, title=f"{group_col}별 {variable} 분포 ({year}년)"), use_container_width=True)
with c5:
    fig = px.bar(summary, x=group_col, y="평균", title=f"{group_col}별 {variable} 평균")
    fig.update_layout(template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)
