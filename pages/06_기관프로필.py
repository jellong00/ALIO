# -*- coding: utf-8 -*-
"""
기관 랭킹
==========
단순 흥미 요소이면서 동시에 극단값과 분포를 학습하는 장치.
"""

import pandas as pd
import streamlit as st

from common_data import load_dataset, raw_files_exist
from utils.style import page_setup, CHART_HEIGHT
from utils.filters import render_cascading_filters, apply_filters
from utils.variables import VARIABLE_META, ALL_VARIABLES, var_label
from utils.stats import descriptive_stats
from utils.charts import plot_rank_bar_with_ratio, apply_compact_height
from utils.questions import PAGE_QUESTIONS

page_setup("🏆 기관 랭킹")
st.caption("상위·하위 기관을 통해 극단값과 분포를 함께 살펴봅니다.")

if not raw_files_exist():
    st.warning("⚠️ `data/` 폴더에 원본 Excel 파일이 없습니다.")
    st.stop()

panel = load_dataset("panel")
if panel.empty:
    st.stop()

filters = render_cascading_filters(panel)
year = filters["연도"]
year_df = apply_filters(panel, {**filters, "기관명": "전체"})

RANKING_VARS = [
    "total_workforce", "new_hire_rate_pct", "employee_avg_pay", "starting_pay",
    "executive_total_pay", "executive_pay_multiple", "welfare_per_capita",
    "total_revenue", "business_revenue", "business_revenue_per_employee",
    "gov_dependency_pct", "balance", "labor_cost_ratio_pct", "corporate_tax_final",
]
label_to_key = {var_label(k): k for k in RANKING_VARS if k in VARIABLE_META}

c1, c2 = st.columns([2, 1])
with c1:
    chosen_label = st.selectbox("랭킹 변수", list(label_to_key.keys()), key="rank_var")
var_key = label_to_key[chosen_label]
meta = VARIABLE_META[var_key]

rank_df = year_df.dropna(subset=[var_key]) if var_key in year_df.columns else pd.DataFrame()

if rank_df.empty:
    st.caption(f"ℹ️ '{meta['label']}' 지표는 현재 필터 조건에서 자료가 없습니다.")
else:
    stats = descriptive_stats(rank_df[var_key])
    m1, m2, m3 = st.columns(3)
    m1.metric("전체 평균", f"{stats['mean']:,.1f}" if pd.notna(stats["mean"]) else "-")
    m2.metric("중앙값", f"{stats['median']:,.1f}" if pd.notna(stats["median"]) else "-")
    m3.metric("N", f"{stats['n_valid']:,}")

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(
            apply_compact_height(
                plot_rank_bar_with_ratio(rank_df, "기관명", var_key, reference_value=stats["mean"],
                                          top_n=10, title=f"{meta['label']} Top 10 (평균 대비 배수 표시)", unit=meta["unit"]),
                CHART_HEIGHT,
            ),
            use_container_width=True,
        )
    with c2:
        st.plotly_chart(
            apply_compact_height(
                plot_rank_bar_with_ratio(rank_df, "기관명", var_key, reference_value=stats["mean"],
                                          top_n=10, ascending=True, title=f"{meta['label']} Bottom 10 (평균 대비 배수 표시)", unit=meta["unit"]),
                CHART_HEIGHT,
            ),
            use_container_width=True,
        )

    st.caption("💡 막대 옆 '평균×N.N'은 해당 기관 값이 전체 평균의 몇 배인지를 나타냅니다. 1.0에 가까울수록 평균적인 기관입니다.")
    st.caption(f"출처: {meta['source']}")

st.info("💭 수업에서 생각해볼 질문\n\n" + "\n\n".join(f"- {q}" for q in PAGE_QUESTIONS["ranking"]))
