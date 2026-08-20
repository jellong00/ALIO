# -*- coding: utf-8 -*-
"""
정부지원과 기관의 자립
========================
기관의 재정은 정부지원과 자체적인 수입 사이에서 어떻게 구성되는가?
"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import load_dataset, raw_files_exist
from utils.style import page_setup, CHART_HEIGHT, CHART_HEIGHT_MAIN
from utils.filters import render_cascading_filters, apply_filters
from utils.variables import VARIABLE_META, ALL_VARIABLES, var_label
from utils.questions import RELATIONSHIP_PRESETS, PAGE_QUESTIONS
from utils.charts import plot_histogram, plot_relationship_scatter, apply_compact_height
from utils.constants import NOTE_CORR

page_setup("🏛 정부지원과 기관의 자립")
st.caption("기관의 재정은 정부지원과 자체적인 수입 사이에서 어떻게 구성되는가?")

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

k1, k2, k3, k4 = st.columns(4)
k1.metric("정부지원수입 평균", f"{year_df['gov_support_revenue'].mean():,.0f} 백만원" if year_df["gov_support_revenue"].notna().any() else "자료없음")
k2.metric("정부지원 의존도 평균", f"{year_df['gov_dependency_pct'].mean():.1f} %" if year_df["gov_dependency_pct"].notna().any() else "자료없음")
k3.metric("자체수입(광의) 평균", f"{year_df['own_revenue_broad'].mean():,.0f} 백만원" if year_df["own_revenue_broad"].notna().any() else "자료없음")
k4.metric("직원 1인당 사업수입", f"{year_df['business_revenue_per_employee'].mean():,.1f} 백만원" if year_df["business_revenue_per_employee"].notna().any() else "자료없음")

st.divider()

gdf = year_df.dropna(subset=["gov_dependency_pct"])
c1, c2 = st.columns(2)
with c1:
    if not gdf.empty:
        st.plotly_chart(apply_compact_height(plot_histogram(gdf["gov_dependency_pct"], "정부지원 의존도 분포", "%"), CHART_HEIGHT), use_container_width=True)
    else:
        st.caption("ℹ️ 정부지원 의존도 자료가 없습니다.")
with c2:
    from utils.charts import plot_group_boxplot
    if not gdf.dropna(subset=["기관유형"]).empty:
        st.plotly_chart(apply_compact_height(plot_group_boxplot(gdf, "gov_dependency_pct", "기관유형", "기관유형별 정부지원 의존도", "%"), CHART_HEIGHT), use_container_width=True)
    else:
        st.caption("ℹ️ 기관유형별 비교 자료가 없습니다.")

st.divider()

# ---------------------------------------------------------------------------
# 정부지원 의존도와 다른 변수의 관계 (추천 조합)
# ---------------------------------------------------------------------------
GOV_PRESET_LABELS = [
    "정부지원 의존도 → 직원 평균보수", "정부지원 의존도 → 1인당 복리후생비",
    "정부지원 의존도 → 신규채용률", "정부지원 의존도 → 법인세 결정세액",
    "직원 1인당 사업수입 → 직원 평균보수", "직원 1인당 사업수입 → 1인당 복리후생비",
]
gov_presets = [p for p in RELATIONSHIP_PRESETS if p["label"] in GOV_PRESET_LABELS]

label_to_key = {var_label(k): k for k in ALL_VARIABLES}
key_to_label = {v: k for k, v in label_to_key.items()}


def _apply_preset():
    chosen = st.session_state.get("gov_preset")
    preset = next((p for p in gov_presets if p["label"] == chosen), None)
    if preset:
        st.session_state["gov_x"] = key_to_label[preset["x"]]
        st.session_state["gov_y"] = key_to_label[preset["y"]]


preset_labels = [p["label"] for p in gov_presets]
c1, c2, c3 = st.columns([1.8, 1.2, 1.2])
with c1:
    st.selectbox("추천 관계", preset_labels, key="gov_preset", on_change=_apply_preset, index=0)
with c2:
    if "gov_x" not in st.session_state:
        st.session_state["gov_x"] = key_to_label["gov_dependency_pct"]
    x_label = st.selectbox("X 변수", list(label_to_key.keys()), key="gov_x")
with c3:
    if "gov_y" not in st.session_state:
        st.session_state["gov_y"] = key_to_label["employee_avg_pay"]
    y_label = st.selectbox("Y 변수", list(label_to_key.keys()), key="gov_y")

color_choice = st.selectbox("색상 구분", ["기관유형", "주무부처", "없음"], key="gov_color")
trendline = st.checkbox("추세선 표시 (단순 선형)", key="gov_trend")
x_key, y_key = label_to_key[x_label], label_to_key[y_label]
color_col = None if color_choice == "없음" else color_choice

subset = year_df.dropna(subset=[c for c in [x_key, y_key, color_col] if c and c in year_df.columns])
if subset.empty:
    st.caption("ℹ️ 선택한 두 변수를 동시에 가진 기관이 없습니다.")
else:
    fig, plotted = plot_relationship_scatter(subset, x_key, y_key, title=f"{x_label} vs {y_label} ({year}년)",
                                              color_col=color_col, trendline=trendline, height=CHART_HEIGHT_MAIN)
    cc1, cc2 = st.columns([3, 1])
    with cc1:
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        n = len(plotted)
        r = plotted[x_key].corr(plotted[y_key]) if n >= 3 else np.nan
        st.metric("N", f"{n:,}")
        st.metric("Pearson r", f"{r:.3f}" if pd.notna(r) else "-")
        if trendline and n >= 3:
            from scipy import stats as scipy_stats
            slope, intercept, _, _, _ = scipy_stats.linregress(plotted[x_key], plotted[y_key])
            st.caption(f"추세선 기울기: {slope:,.3f} · R²: {r**2:.3f}")
    st.info(NOTE_CORR)
    if trendline:
        st.caption("추세선은 단순 선형 참고선일 뿐, 회귀모형의 추정 결과를 의미하지 않습니다.")

st.info("💭 수업에서 생각해볼 질문\n\n" + "\n\n".join(f"- {q}" for q in PAGE_QUESTIONS["gov_dependency"]))
