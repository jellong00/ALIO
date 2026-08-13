# -*- coding: utf-8 -*-
import pandas as pd
import streamlit as st

from utils.data import load_dataset
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters
from utils.charts import plot_group_boxplot

st.set_page_config(page_title="임원보수 현황", page_icon="🎩", layout="wide")
st.title("🎩 09. 임원보수 현황")
st.caption("대표변수인 '기관장 연간보수(합계)'를 중심으로 심화 분석합니다. (단위: 천원)")

exec_pay = load_dataset("executive_pay")
panel = load_dataset("panel")
if exec_pay.empty or panel.empty:
    st.stop()

st.subheader("직위별 비교")
years_sorted = sorted(exec_pay["연도"].unique(), reverse=True)
year_for_overview = st.selectbox("연도 선택", years_sorted, index=years_sorted.index(2025) if 2025 in years_sorted else 0)

position_total = exec_pay[(exec_pay["항목"] == "합계") & (exec_pay["연도"] == year_for_overview)]
positions = [p for p in ["상임기관장", "상임이사", "상임감사", "비상임이사", "비상임감사"] if p in position_total["구분"].unique()]
pos_df = position_total[position_total["구분"].isin(positions)]

if not pos_df.empty:
    st.plotly_chart(
        plot_group_boxplot(pos_df, "값", "구분", title=f"직위별 보수(합계) 분포 ({year_for_overview}년)", unit="천원"),
        use_container_width=True,
    )

st.divider()
st.header("대표변수 심화분석: 기관장 연간보수")

filters = render_common_filters(panel, key_prefix="execpay")
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(filtered, variable="기관장보수", year=filters.get("연도", 2025), unit="천원")
