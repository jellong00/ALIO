import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit, get_allowed_agg, ORG_TYPE_COLORS
from utils.metrics import add_growth_variables
from utils.charts import plot_rank_bar, plot_rank_scatter

st.set_page_config(page_title="연도별 변화분석", layout="wide")
st.title("⑦ 연도별 변화분석")
st.caption("수준(level)과 변화율(growth)을 구분해서 살펴보는 페이지입니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p7")

TREND_VARS = [
    "임직원수", "여성직원비율", "신규채용자수", "신규채용률",
    "직원평균보수", "1인당복리후생비", "기관장연봉",
    "총수입", "총지출", "정부지원의존도", "법인세결정세액",
    "여성육아휴직사용자수", "남성육아휴직사용자수",
]
TREND_VARS = [v for v in TREND_VARS if VARIABLES[v]["column"] in df.columns]

st.divider()
c1, c2 = st.columns(2)
with c1:
    var_key = st.selectbox("변수 선택 (13개)", TREND_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p7_var")
allowed = get_allowed_agg(var_key)
with c2:
    agg = st.radio("집계 방식", allowed, horizontal=True, key="p7_agg")
col = VARIABLES[var_key]["column"]
agg_func = "mean" if agg == "평균" else "sum"

st.markdown(f"### 📈 연도별 {agg} 추이 — 비교 수준 선택")
st.caption("전체·기관유형·주무부처·개별기관 중 원하는 선을 골라 한 그래프에서 비교합니다 (최대 4개 권장).")

lc1, lc2, lc3, lc4 = st.columns(4)
with lc1:
    show_overall = st.checkbox("전체 평균/합계", value=True, key="p7_showoverall")
with lc2:
    sel_types = st.multiselect("기관유형", sorted(df["기관유형"].unique()), key="p7_seltypes")
with lc3:
    sel_depts = st.multiselect("주무부처", sorted(df["주무부처"].unique()), key="p7_seldepts")
with lc4:
    sel_orgs_trend = st.multiselect("개별기관", sorted(df["기관명"].unique()), key="p7_selorgs")

n_lines = int(show_overall) + len(sel_types) + len(sel_depts) + len(sel_orgs_trend)
if n_lines > 4:
    st.warning(f"⚠️ 현재 {n_lines}개 선이 선택되었습니다. 4개 이하로 선택하면 더 읽기 쉽습니다.")

fig1 = go.Figure()
if show_overall:
    overall = df.groupby("연도")[col].agg(agg_func).reset_index()
    fig1.add_trace(go.Scatter(x=overall["연도"], y=overall[col], mode="lines+markers", name="전체",
                                line=dict(width=3, color="#333333")))
palette = ["#4C78A8", "#E07B39", "#2CA02C", "#D62728", "#9467BD", "#8C564B"]
pi = 0
for t in sel_types:
    d = df[df["기관유형"] == t].groupby("연도")[col].agg(agg_func).reset_index()
    fig1.add_trace(go.Scatter(x=d["연도"], y=d[col], mode="lines+markers", name=f"{t} 평균" if agg == "평균" else f"{t} 합계",
                                line=dict(width=2, color=palette[pi % len(palette)], dash="dash")))
    pi += 1
for dpt in sel_depts:
    d = df[df["주무부처"] == dpt].groupby("연도")[col].agg(agg_func).reset_index()
    fig1.add_trace(go.Scatter(x=d["연도"], y=d[col], mode="lines+markers", name=f"{dpt} 평균" if agg == "평균" else f"{dpt} 합계",
                                line=dict(width=2, color=palette[pi % len(palette)], dash="dot")))
    pi += 1
for org in sel_orgs_trend:
    d = df[df["기관명"] == org][["연도", col]].dropna()
    fig1.add_trace(go.Scatter(x=d["연도"], y=d[col], mode="lines+markers", name=org,
                                line=dict(width=2, color=palette[pi % len(palette)])))
    pi += 1

fig1.update_layout(font=dict(size=16), height=520, yaxis_title=f"{get_label(var_key)} ({get_unit(var_key)})", xaxis_title="연도")
st.plotly_chart(fig1, use_container_width=True)

st.divider()

# ---------------- 증가율 분석 ----------------
st.markdown("### 📐 전년 대비 증가율 분석")
grown = add_growth_variables(df, [col])
g_col = f"{col}_증가율"

yrs = sorted(grown["연도"].unique())
sel_year = st.selectbox("증가율 확인 연도", yrs[1:] if len(yrs) > 1 else yrs, index=len(yrs)-2 if len(yrs) > 1 else 0, key="p7_gyear")
g_year_df = grown[grown["연도"] == sel_year][[g_col, "기관명", "기관유형"]].copy()
g_year_df[g_col] = pd.to_numeric(g_year_df[g_col], errors="coerce")
g_year_df = g_year_df[~g_year_df[g_col].isin([float("inf"), float("-inf")])].dropna()

if not g_year_df.empty:
    m1, m2, m3 = st.columns(3)
    m1.metric("평균 증가율", f"{g_year_df[g_col].mean():,.1f}%")
    m2.metric("중앙값", f"{g_year_df[g_col].median():,.1f}%")
    m3.metric("N", f"{g_year_df.shape[0]:,}")
    fig3 = px.histogram(g_year_df, x=g_col, nbins=40, labels={g_col: f"{get_label(var_key)} 전년대비 증가율(%)"})
    fig3.update_layout(font=dict(size=16), height=450, showlegend=False)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("### 🏆 증가율 순위")
    rank_mode = st.radio("정렬", ["Top 10", "Bottom 10"], horizontal=True, key="p7_growrank")
    g_year_df2 = g_year_df.rename(columns={g_col: "증가율(%)"})
    ranked = g_year_df2.sort_values("증가율(%)", ascending=(rank_mode == "Bottom 10")).head(10)
    fig4 = px.bar(ranked, x="증가율(%)", y="기관명", orientation="h", color="기관유형",
                   color_discrete_map=ORG_TYPE_COLORS)
    fig4.update_layout(font=dict(size=16), height=420)
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("선택한 연도의 증가율을 계산할 관측치가 부족합니다.")

st.divider()

# ---------------- 순위 안정성 ----------------
st.markdown("### 🔄 순위 안정성 (Rank-Rank)")
if len(yrs) >= 2:
    c3, c4 = st.columns(2)
    with c3:
        y1 = st.selectbox("기준 연도", yrs, index=0, key="p7_y1")
    with c4:
        y2 = st.selectbox("비교 연도", yrs, index=len(yrs) - 1, key="p7_y2")

    d1 = df[df["연도"] == y1][["기관명", col]].dropna().rename(columns={col: "값1"})
    d2 = df[df["연도"] == y2][["기관명", col]].dropna().rename(columns={col: "값2"})
    merged = pd.merge(d1, d2, on="기관명")
    if merged.shape[0] > 3:
        merged["순위_기준연도"] = merged["값1"].rank(ascending=False)
        merged["순위_비교연도"] = merged["값2"].rank(ascending=False)
        rho, p = stats.spearmanr(merged["순위_기준연도"], merged["순위_비교연도"])
        st.write(f"**Spearman 순위상관계수** = {rho:.3f} (p = {p:.4f}, N = {merged.shape[0]:,})")
        fig5 = plot_rank_scatter(merged, "순위_기준연도", "순위_비교연도",
                                   f"{y1}년 순위", f"{y2}년 순위")
        st.plotly_chart(fig5, use_container_width=True)
        st.caption("💡 대각선(점선)에 가까울수록 두 연도의 순위가 유지된다는 뜻입니다.")
    else:
        st.info("두 연도 모두 관측치가 있는 기관이 부족합니다.")

st.divider()

# ---------------- 변화량 관계 ----------------
st.markdown("### 🔗 변화량(증가율) 간 관계")
other_vars = [v for v in TREND_VARS if v != var_key]
other_key = st.selectbox("비교할 변수의 증가율", other_vars, format_func=lambda k: get_label(k), key="p7_otherg")
other_col = VARIABLES[other_key]["column"]
grown2 = add_growth_variables(df, [col, other_col])
gc1, gc2 = f"{col}_증가율", f"{other_col}_증가율"
sub = grown2[[gc1, gc2]].apply(pd.to_numeric, errors="coerce")
sub = sub[~sub[gc1].isin([float("inf"), float("-inf")]) & ~sub[gc2].isin([float("inf"), float("-inf")])].dropna()
if sub.shape[0] > 3:
    fig6 = px.scatter(sub, x=gc1, y=gc2, trendline="ols",
                        labels={gc1: f"{get_label(var_key)} 증가율(%)", gc2: f"{get_label(other_key)} 증가율(%)"})
    fig6.update_layout(font=dict(size=16), height=480)
    st.plotly_chart(fig6, use_container_width=True)
    r, p = stats.pearsonr(sub[gc1], sub[gc2])
    st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {sub.shape[0]:,}")
else:
    st.info("증가율 관계를 계산할 관측치가 부족합니다.")

with st.expander("⚠️ 해석 시 주의할 점"):
    st.markdown(
        "- 합계 추이는 '기관 수'의 변화(신설·통폐합 등)에도 영향을 받을 수 있습니다.\n"
        "- 평균 추이는 특정 연도에 이상치 기관이 있으면 크게 흔들릴 수 있습니다.\n"
        "- 증가율은 분모(전년도 값)가 0에 가까우면 매우 불안정해질 수 있습니다."
    )
