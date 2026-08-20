# -*- coding: utf-8 -*-
"""
어디서 벌고 어디에 쓸까?
=========================
공공기관은 어떤 방식으로 자금을 조달하고 어디에 지출하는가?
법인세 데이터도 재정정보와 연결하여 활용한다.
"""

import pandas as pd
import numpy as np
import plotly.express as px
import streamlit as st

from common_data import load_dataset, raw_files_exist
from utils.style import page_setup, CHART_HEIGHT, CHART_HEIGHT_MAIN
from utils.filters import render_cascading_filters, apply_filters
from utils.stats import descriptive_stats
from utils.charts import plot_rank_bar, plot_relationship_scatter, apply_compact_height
from utils.questions import PAGE_QUESTIONS
from utils.constants import NOTE_CORR

page_setup("💰 어디서 벌고 어디에 쓸까?")
st.caption("공공기관은 어떤 방식으로 자금을 조달하고 어디에 지출하는가?")

if not raw_files_exist():
    st.warning("⚠️ `data/` 폴더에 원본 Excel 파일이 없습니다.")
    st.stop()

panel = load_dataset("panel")
if panel.empty:
    st.stop()

filters = render_cascading_filters(panel)
year = filters["연도"]
year_df = apply_filters(panel, {**filters, "기관명": "전체"})

if year_df.empty:
    st.caption("ℹ️ 현재 필터 조건을 만족하는 기관이 없습니다.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------------
k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("총수입 합계", f"{year_df['total_revenue'].sum():,.0f} 백만원" if year_df["total_revenue"].notna().any() else "자료없음")
k2.metric("총지출 합계", f"{year_df['total_expense'].sum():,.0f} 백만원" if year_df["total_expense"].notna().any() else "자료없음")
k3.metric("사업수입 평균", f"{year_df['business_revenue'].mean():,.0f} 백만원" if year_df["business_revenue"].notna().any() else "자료없음")
k4.metric("정부지원수입 평균", f"{year_df['gov_support_revenue'].mean():,.0f} 백만원" if year_df["gov_support_revenue"].notna().any() else "자료없음")
k5.metric("인건비 평균", f"{year_df['labor_cost'].mean():,.0f} 백만원" if year_df["labor_cost"].notna().any() else "자료없음")
k6.metric("수지 평균", f"{year_df['balance'].mean():,.0f} 백만원" if year_df["balance"].notna().any() else "자료없음")

st.divider()

# ---------------------------------------------------------------------------
# 수입 구조: 기관유형별 구성비
# ---------------------------------------------------------------------------
st.markdown("###### 수입 구조")
c1, c2 = st.columns(2)
with c1:
    comp_vars = ["gov_support_revenue", "business_revenue"]
    comp_labels = {"gov_support_revenue": "정부지원수입", "business_revenue": "기타사업수입"}
    grouped = year_df.groupby("기관유형")[comp_vars].mean(numeric_only=True).reset_index()
    if not grouped.empty and grouped[comp_vars].notna().any().any():
        melted = grouped.melt(id_vars="기관유형", value_vars=comp_vars, var_name="구분", value_name="금액")
        melted["구분"] = melted["구분"].map(comp_labels)
        fig = px.bar(melted, x="기관유형", y="금액", color="구분", barmode="stack",
                     title="기관유형별 평균 수입 구성 (백만원)")
        fig.update_layout(template="plotly_white", height=CHART_HEIGHT)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("ℹ️ 기관유형별 수입 구성 자료가 없습니다.")

with c2:
    inst_options = sorted(year_df["기관명"].dropna().unique().tolist())
    sel = st.selectbox("기관 선택 (수입구성 확인)", ["선택 안 함"] + inst_options, key="rev_inst")
    if sel != "선택 안 함":
        row = year_df[year_df["기관명"] == sel]
        if not row.empty:
            row = row.iloc[0]
            vals = {comp_labels[v]: row.get(v) for v in comp_vars if pd.notna(row.get(v))}
            if vals:
                fig2 = px.pie(names=list(vals.keys()), values=list(vals.values()), hole=0.5,
                              title=f"{sel} 수입 구성 ({year}년)")
                fig2.update_layout(template="plotly_white", height=CHART_HEIGHT)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.caption("ℹ️ 선택한 기관의 수입 구성 자료가 없습니다.")
    else:
        st.caption("기관을 선택하면 수입 구성을 확인할 수 있습니다.")

# ---------------------------------------------------------------------------
# 재정 균형 및 상위/하위 기관
# ---------------------------------------------------------------------------
st.markdown("###### 재정 균형 (수지 = 총수입 - 총지출)")
c3, c4 = st.columns(2)
with c3:
    bdf = year_df.dropna(subset=["balance"])
    if not bdf.empty:
        st.plotly_chart(apply_compact_height(plot_rank_bar(bdf, "기관명", "balance", top_n=10, title="수지 상위 10개 기관", unit="백만원"), CHART_HEIGHT), use_container_width=True)
    else:
        st.caption("ℹ️ 수지 자료가 없습니다.")
with c4:
    if not bdf.empty:
        st.plotly_chart(apply_compact_height(plot_rank_bar(bdf, "기관명", "balance", top_n=10, title="수지 하위 10개 기관", unit="백만원", ascending=True), CHART_HEIGHT), use_container_width=True)
    else:
        st.caption("ℹ️ 수지 자료가 없습니다.")

st.divider()

# ---------------------------------------------------------------------------
# 법인세 연결 분석
# ---------------------------------------------------------------------------
st.markdown("###### 법인세와 재정정보의 관계")
tax_presets = {
    "과세표준 vs 법인세 결정세액": ("taxable_income", "corporate_tax_final"),
    "총수입 vs 법인세 결정세액": ("total_revenue", "corporate_tax_final"),
    "사업수입 vs 법인세 결정세액": ("business_revenue", "corporate_tax_final"),
    "정부지원 의존도 vs 법인세 결정세액": ("gov_dependency_pct", "corporate_tax_final"),
}
tax_choice = st.selectbox("확인할 관계", list(tax_presets.keys()), key="tax_rel")
x_key, y_key = tax_presets[tax_choice]

subset = year_df.dropna(subset=[x_key, y_key])
if subset.empty:
    st.caption("ℹ️ 선택한 두 변수를 동시에 가진 기관이 없습니다.")
else:
    fig, plotted = plot_relationship_scatter(subset, x_key, y_key, title=tax_choice, height=CHART_HEIGHT_MAIN)
    cc1, cc2 = st.columns([3, 1])
    with cc1:
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        n = len(plotted)
        r = plotted[x_key].corr(plotted[y_key]) if n >= 3 else np.nan
        st.metric("N", f"{n:,}")
        st.metric("Pearson r", f"{r:.3f}" if pd.notna(r) else "-")
    st.info(NOTE_CORR)

questions = PAGE_QUESTIONS["revenue_expense"] + PAGE_QUESTIONS["tax"]
st.info("💭 수업에서 생각해볼 질문\n\n" + "\n\n".join(f"- {q}" for q in questions[:6]))
