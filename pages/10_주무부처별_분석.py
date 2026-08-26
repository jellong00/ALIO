import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from scipy import stats

from utils.data_cleaner import get_full_panel, latest_snapshot
from utils.variables import VARIABLES, get_label, get_unit, get_vars_by_category, CATEGORIES, ORG_TYPE_COLORS
from utils.charts import plot_rank_bar, plot_scatter

st.set_page_config(page_title="주무부처별 분석", layout="wide")
st.title("⑩ 주무부처별 분석")
st.caption("주무부처를 선택해 산하기관 전체를 하나의 그룹으로 살펴보는 페이지입니다.")

panel = get_full_panel()

st.divider()
depts = sorted(panel["주무부처"].unique())
sel_dept = st.selectbox("주무부처 선택", depts, key="p10_dept")

dept_df = panel[panel["주무부처"] == sel_dept]
dept_snap = latest_snapshot(dept_df)
latest_year = dept_snap["연도"].max() if not dept_snap.empty else None

if dept_snap.empty:
    st.warning("선택한 부처의 데이터가 없습니다.")
    st.stop()

st.divider()
st.markdown(f"### 🏛️ {sel_dept} 산하기관 개요 ({latest_year}년 기준)")
m1, m2, m3, m4, m5 = st.columns(5)
m1.metric("산하기관 수", f"{dept_snap['기관명'].nunique():,}개")
m2.metric("총 임직원수", f"{pd.to_numeric(dept_snap['임직원수'], errors='coerce').sum():,.0f}명")
m3.metric("총수입 합계", f"{pd.to_numeric(dept_snap['총수입'], errors='coerce').sum():,.0f}백만원")
m4.metric("평균보수 평균", f"{pd.to_numeric(dept_snap['직원평균보수'], errors='coerce').mean():,.0f}천원")
m5.metric("평균 정부지원의존도", f"{pd.to_numeric(dept_snap['정부지원의존도'], errors='coerce').mean():,.1f}%")

m6, m7 = st.columns(2)
m6.metric("평균 신규채용률", f"{pd.to_numeric(dept_snap['신규채용률'], errors='coerce').mean():,.1f}%")
m7.metric("1인당 복리후생비 평균", f"{pd.to_numeric(dept_snap['1인당복리후생비'], errors='coerce').mean():,.0f}천원/인")

st.divider()

# ---------------- 산하기관 분포 ----------------
st.markdown("### 📊 산하기관 분포")
c1, c2 = st.columns(2)
with c1:
    type_counts = dept_snap["기관유형"].value_counts().reset_index()
    type_counts.columns = ["기관유형", "기관 수"]
    fig_pie = px.pie(type_counts, names="기관유형", values="기관 수", color="기관유형",
                       color_discrete_map=ORG_TYPE_COLORS, title="기관유형 구성")
    fig_pie.update_layout(font=dict(size=15), height=440)
    st.plotly_chart(fig_pie, use_container_width=True)
with c2:
    fig_hist = px.histogram(dept_snap.dropna(subset=["임직원수"]), x="임직원수", nbins=20,
                              labels={"임직원수": "임직원수 (명)"}, title="임직원 규모 분포")
    fig_hist.update_layout(font=dict(size=15), height=440, showlegend=False)
    st.plotly_chart(fig_hist, use_container_width=True)

st.divider()

# ---------------- 주요 변수: 부처 평균 vs 전체 평균 ----------------
st.markdown("### ⚖️ 부처 평균 vs 전체 평균")
compare_vars = ["임직원수", "총수입", "정부지원의존도", "직원평균보수", "1인당복리후생비", "신규채용률"]
compare_vars = [v for v in compare_vars if VARIABLES[v]["column"] in panel.columns]
overall_snap = latest_snapshot(panel[panel["연도"] == latest_year]) if latest_year else latest_snapshot(panel)
rows = []
for vk in compare_vars:
    col = VARIABLES[vk]["column"]
    dept_mean = pd.to_numeric(dept_snap[col], errors="coerce").mean()
    overall_mean = pd.to_numeric(overall_snap[col], errors="coerce").mean()
    diff_pct = (dept_mean - overall_mean) / overall_mean * 100 if overall_mean else None
    rows.append({"변수": get_label(vk), f"{sel_dept} 평균": dept_mean, "전체 평균": overall_mean,
                  "차이(%)": diff_pct})
compare_df = pd.DataFrame(rows).round(1)
st.dataframe(compare_df, use_container_width=True, hide_index=True)

st.divider()

# ---------------- 산하기관 내부 비교: 선택 변수 순위 ----------------
st.markdown("### 🏆 산하기관 내부 순위")
cat = st.selectbox("카테고리", CATEGORIES, key="p10_cat")
cat_vars = get_vars_by_category(cat)
var_key = st.selectbox("변수 선택", list(cat_vars.keys()), format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p10_var")
col = VARIABLES[var_key]["column"]
if col in dept_df.columns:
    rank_mode = st.radio("정렬", ["Top", "Bottom"], horizontal=True, key="p10_rankmode")
    st.plotly_chart(plot_rank_bar(dept_df, col, var_key=var_key, top_n=min(15, dept_snap["기관명"].nunique()),
                                    ascending=(rank_mode == "Bottom")), use_container_width=True)
else:
    st.warning("선택한 변수가 데이터에 없습니다.")

st.divider()

# ---------------- 산하기관 관계 ----------------
st.markdown("### 🔗 산하기관 내 변수 관계")
st.caption("예: 총수입 ↔ 평균보수 — 같은 부처 산하기관들 사이에서도 이 관계가 성립하는지 확인합니다.")
rel_a = st.selectbox("변수 A", list(VARIABLES.keys()), index=list(VARIABLES.keys()).index("총수입") if "총수입" in VARIABLES else 0,
                       format_func=lambda k: get_label(k), key="p10_rela")
rel_b = st.selectbox("변수 B", list(VARIABLES.keys()), index=list(VARIABLES.keys()).index("직원평균보수") if "직원평균보수" in VARIABLES else 1,
                       format_func=lambda k: get_label(k), key="p10_relb")
rel_a_col, rel_b_col = VARIABLES[rel_a]["column"], VARIABLES[rel_b]["column"]
if rel_a_col in dept_df.columns and rel_b_col in dept_df.columns:
    sub = dept_df[[rel_a_col, rel_b_col]].dropna()
    if sub.shape[0] > 2:
        fig_rel = plot_scatter(dept_df, rel_a_col, rel_b_col, x_key=rel_a, y_key=rel_b, color_col="기관유형", trendline="ols")
        st.plotly_chart(fig_rel, use_container_width=True)
        r, p = stats.pearsonr(sub[rel_a_col], sub[rel_b_col])
        st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {sub.shape[0]:,}")
    else:
        st.info("관계를 계산할 만큼 관측치가 충분하지 않습니다.")

st.divider()

# ---------------- 시계열 ----------------
st.markdown("### 📈 부처 산하기관 평균 추이 vs 전체")
ts_var = st.selectbox("변수 선택", compare_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p10_tsvar")
ts_col = VARIABLES[ts_var]["column"]
dept_ts = dept_df.groupby("연도")[ts_col].mean().reset_index()
overall_ts = panel.groupby("연도")[ts_col].mean().reset_index()

import plotly.graph_objects as go
fig_ts = go.Figure()
fig_ts.add_trace(go.Scatter(x=dept_ts["연도"], y=dept_ts[ts_col], mode="lines+markers", name=f"{sel_dept} 평균",
                              line=dict(width=3, color="#E07B39")))
fig_ts.add_trace(go.Scatter(x=overall_ts["연도"], y=overall_ts[ts_col], mode="lines+markers", name="전체 평균",
                              line=dict(width=2, dash="dash", color="#4C78A8")))
fig_ts.update_layout(font=dict(size=16), height=460, yaxis_title=f"{get_label(ts_var)} ({get_unit(ts_var)})")
st.plotly_chart(fig_ts, use_container_width=True)

st.caption("⚠️ 부처 산하기관 수가 적으면 평균이 소수 기관의 값에 크게 좌우될 수 있습니다.")
