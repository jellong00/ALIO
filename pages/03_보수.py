# -*- coding: utf-8 -*-
"""
직원에게 얼마나 쓸까?
======================
기관은 사람에게 얼마나, 어떤 방식으로 지출하는가?
보수·복지·임원연봉·업무추진비·채용을 하나의 페이지에서 연결한다.

[중요] 추천 관계 selectbox와 X/Y 변수 selectbox는 서로 "별개"로 동작해야 한다.
       - 추천 관계를 바꾸면: 그 순간에만 X/Y 값을 해당 조합으로 갱신한다 (on_change 콜백).
       - 이후 사용자가 X/Y를 직접 바꾸면: 추천 관계 선택과 무관하게 자유롭게 바뀐다.
       Streamlit selectbox는 key가 이미 session_state에 있으면 index 인자를 무시하므로,
       "매 렌더링마다 index로 강제 동기화"하는 방식은 동작하지 않는다.
       따라서 on_change 콜백 안에서 session_state를 직접 갱신하는 방식을 사용한다.
"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import load_dataset, raw_files_exist
from utils.style import page_setup, CHART_HEIGHT, CHART_HEIGHT_MAIN
from utils.filters import render_cascading_filters, apply_filters
from utils.variables import VARIABLE_META, ALL_VARIABLES, var_label
from utils.questions import RELATIONSHIP_PRESETS, PAGE_QUESTIONS
from utils.charts import plot_relationship_scatter
from utils.constants import NOTE_CORR

page_setup("👥 직원에게 얼마나 쓸까?")
st.caption("기관은 사람에게 얼마나, 어떤 방식으로 지출하는가?")

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
k1.metric("직원 평균보수", f"{year_df['employee_avg_pay'].mean():,.0f} 천원" if year_df["employee_avg_pay"].notna().any() else "자료없음")
k2.metric("신입초임", f"{year_df['starting_pay'].mean():,.0f} 천원" if year_df["starting_pay"].notna().any() else "자료없음")
k3.metric("1인당 복리후생비", f"{year_df['welfare_per_capita'].mean():,.0f} 천원" if year_df["welfare_per_capita"].notna().any() else "자료없음")
k4.metric("기관장 연봉", f"{year_df['executive_total_pay'].mean():,.0f} 천원" if year_df["executive_total_pay"].notna().any() else "자료없음")
k5.metric("기관장-직원 보수배율", f"{year_df['executive_pay_multiple'].mean():.1f} 배" if year_df["executive_pay_multiple"].notna().any() else "자료없음")
k6.metric("신규채용률", f"{year_df['new_hire_rate_pct'].mean():.1f} %" if year_df["new_hire_rate_pct"].notna().any() else "자료없음")

st.divider()

# ---------------------------------------------------------------------------
# 변수 관계 (추천 관계 + 직접 선택 - 독립적으로 동작)
# ---------------------------------------------------------------------------
PEOPLE_PRESET_LABELS = [
    "평균근속연수 → 직원 평균보수", "직원 평균보수 → 1인당 복리후생비",
    "직원 평균보수 → 신규채용률", "직원 평균보수 → 기관장 연봉",
]
people_presets = [p for p in RELATIONSHIP_PRESETS if p["label"] in PEOPLE_PRESET_LABELS]

label_to_key = {var_label(k): k for k in ALL_VARIABLES}
key_to_label = {v: k for k, v in label_to_key.items()}
all_labels = list(label_to_key.keys())


def _apply_preset():
    """추천 관계 selectbox의 on_change 콜백: 선택 순간에만 X/Y를 갱신한다."""
    chosen = st.session_state.get("people_preset")
    preset = next((p for p in people_presets if p["label"] == chosen), None)
    if preset:
        st.session_state["people_x"] = key_to_label[preset["x"]]
        st.session_state["people_y"] = key_to_label[preset["y"]]


preset_labels = ["직접 선택"] + [p["label"] for p in people_presets]
c1, c2, c3 = st.columns([1.6, 1.2, 1.2])
with c1:
    st.selectbox("추천 관계", preset_labels, key="people_preset", on_change=_apply_preset)
with c2:
    if "people_x" not in st.session_state:
        st.session_state["people_x"] = key_to_label["avg_tenure_months"]
    x_label = st.selectbox("X 변수", all_labels, key="people_x")
with c3:
    if "people_y" not in st.session_state:
        st.session_state["people_y"] = key_to_label["employee_avg_pay"]
    y_label = st.selectbox("Y 변수", all_labels, key="people_y")

o1, o2, o3 = st.columns(3)
with o1:
    color_choice = st.selectbox("색상 구분", ["없음", "기관유형", "주무부처"], key="people_color")
with o2:
    trendline = st.checkbox("추세선 표시 (단순 선형)", key="people_trend")
with o3:
    st.write("")

x_key = label_to_key[x_label]
y_key = label_to_key[y_label]
color_col = None if color_choice == "없음" else color_choice

subset_cols = [x_key, y_key] + ([color_col] if color_col else [])
rel_df = year_df.dropna(subset=[c for c in subset_cols if c in year_df.columns])

if rel_df.empty:
    st.caption("ℹ️ 선택한 두 변수를 동시에 가진 기관이 없습니다.")
else:
    fig, plotted = plot_relationship_scatter(
        rel_df, x_key, y_key, title=f"{x_label} vs {y_label} ({year}년)",
        color_col=color_col, trendline=trendline, height=CHART_HEIGHT_MAIN,
    )
    cc1, cc2 = st.columns([3, 1])
    with cc1:
        st.plotly_chart(fig, use_container_width=True)
    with cc2:
        n = len(plotted)
        r = plotted[x_key].corr(plotted[y_key]) if n >= 3 else np.nan
        st.metric("N", f"{n:,}")
        st.metric("Pearson r", f"{r:.3f}" if pd.notna(r) else "-")
        st.metric(f"{x_label} 평균", f"{plotted[x_key].mean():,.1f}")
        st.metric(f"{y_label} 평균", f"{plotted[y_key].mean():,.1f}")
        if trendline and n >= 3:
            from scipy import stats as scipy_stats
            slope, intercept, _, _, _ = scipy_stats.linregress(plotted[x_key], plotted[y_key])
            st.caption(f"추세선 기울기: {slope:,.3f} · R²: {r**2:.3f}")

    st.info(NOTE_CORR)
    if trendline:
        st.caption("추세선은 단순 선형 참고선일 뿐, 회귀모형의 추정 결과를 의미하지 않습니다.")
    active_preset = next((p for p in people_presets if key_to_label[p["x"]] == x_label and key_to_label[p["y"]] == y_label), None)
    if active_preset:
        st.info(f"💭 생각해보기: {active_preset['question']}")

st.info("💭 수업에서 생각해볼 질문\n\n" + "\n\n".join(f"- {q}" for q in PAGE_QUESTIONS["people_spending"]))
