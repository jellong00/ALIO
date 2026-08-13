# -*- coding: utf-8 -*-
import streamlit as st

from utils.data import load_dataset
from utils.stats import yearly_summary
from utils.charts import plot_time_series

st.set_page_config(page_title="시계열 실습", page_icon="📉", layout="wide")
st.title("📉 15. 시계열 실습")
st.caption("변수 하나를 선택하고 연도에 따른 변화를 확인합니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

numeric_cols = [c for c in panel.select_dtypes(include="number").columns if c != "연도"]

c1, c2 = st.columns(2)
with c1:
    variable = st.selectbox("변수 선택", numeric_cols)
with c2:
    agg_choice = st.radio("집계 방법", ["평균", "중앙값", "합계"], horizontal=True)

use_panel = panel[panel["연도"] <= 2025]

st.subheader(f"전체 기관 {agg_choice} 추이")
yearly = yearly_summary(use_panel, variable, agg=agg_choice)
st.plotly_chart(plot_time_series(yearly, "연도", agg_choice, title=f"{variable} 연도별 {agg_choice}"), use_container_width=True)

st.divider()
st.subheader("특정 기관 추이")
institutions = ["선택 안 함"] + sorted(panel["기관명"].dropna().unique().tolist())
selected_inst = st.selectbox("기관 선택 (선택 시 해당 기관의 원자료 추이를 보여줍니다)", institutions)

if selected_inst != "선택 안 함":
    inst_df = panel[(panel["기관명"] == selected_inst) & (panel["연도"] <= 2025)].sort_values("연도")
    if inst_df[variable].notna().any():
        st.plotly_chart(plot_time_series(inst_df, "연도", variable, title=f"{selected_inst} - {variable} 추이"), use_container_width=True)
    else:
        st.info("해당 기관은 이 변수에 대한 자료가 없습니다.")
