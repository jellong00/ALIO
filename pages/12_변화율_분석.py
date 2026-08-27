import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit, ORG_TYPE_COLORS
from utils.charts import plot_rank_scatter
from utils.page_header import render_intro

st.set_page_config(page_title="변화율 분석", layout="wide")
st.title("⑫ 변화율 분석")
render_intro(
    purpose="수준이 아니라 변화의 크기와 기관 간 순위의 안정성을 살펴봅니다.",
    unit="선택한 두 연도 사이의 변화 (기관-연도 pooled가 아니라 특정 변화기간 하나를 기본으로 봅니다)",
    methods="전년 대비 변화 · 변화 분포 · 증가/감소 Top · Rank-Rank(Spearman)",
    caution="금액·인원 변수는 '증가율(%)', 이미 비율인 변수(예: 정부지원의존도)는 '증감(%p, 퍼센트포인트)'로 봐야 혼동이 없습니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p13")

TREND_VARS = [
    "임직원수", "여성직원비율", "신규채용자수", "신규채용률",
    "직원평균보수", "1인당복리후생비", "기관장연봉",
    "총수입", "총지출", "정부지원의존도", "법인세결정세액",
    "여성육아휴직사용자수", "남성육아휴직사용자수",
]
TREND_VARS = [v for v in TREND_VARS if VARIABLES[v]["column"] in df.columns]

st.divider()
var_key = st.selectbox("변수 선택 (13개)", TREND_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p13_var")
col = VARIABLES[var_key]["column"]
is_ratio = VARIABLES[var_key]["percent"]
change_label = "증감 (%p)" if is_ratio else "증가율 (%)"

years = sorted(df["연도"].unique())
if len(years) < 2:
    st.warning("비교할 연도가 2개 이상 있어야 합니다.")
    st.stop()

st.markdown("### 변화기간 선택")
c1, c2 = st.columns(2)
with c1:
    y_from = st.selectbox("기준 연도(이전)", years[:-1], index=len(years) - 2, key="p13_yfrom")
with c2:
    y_to_options = [y for y in years if y > y_from]
    y_to = st.selectbox("비교 연도(이후)", y_to_options, index=0, key="p13_yto")

d_from = df[df["연도"] == y_from][["기관명", "기관유형", col]].dropna().rename(columns={col: "이전값"})
d_to = df[df["연도"] == y_to][["기관명", "기관유형", col]].dropna().rename(columns={col: "이후값"})
merged = pd.merge(d_from, d_to, on=["기관명", "기관유형"])

if is_ratio:
    merged["변화"] = merged["이후값"] - merged["이전값"]
else:
    merged = merged[merged["이전값"] != 0]
    merged["변화"] = (merged["이후값"] - merged["이전값"]) / merged["이전값"] * 100

merged = merged.replace([float("inf"), float("-inf")], pd.NA).dropna(subset=["변화"])

if merged.empty:
    st.info("선택한 기간에 비교 가능한 관측치가 부족합니다.")
    st.stop()

st.markdown(f"### 📐 {y_from}년 → {y_to}년 {change_label} 분포")
m1, m2, m3 = st.columns(3)
m1.metric(f"평균 {change_label}", f"{merged['변화'].mean():,.1f}")
m2.metric("중앙값", f"{merged['변화'].median():,.1f}")
m3.metric("N", f"{merged.shape[0]:,}")
fig3 = px.histogram(merged, x="변화", nbins=40, labels={"변화": f"{get_label(var_key)} {change_label}"})
fig3.update_layout(font=dict(size=16), height=450, showlegend=False)
st.plotly_chart(fig3, use_container_width=True)

st.markdown("### 🏆 증가/감소 Top 10")
rank_mode = st.radio("정렬", ["증가 Top 10", "감소 Top 10"], horizontal=True, key="p13_growrank")
ranked = merged.sort_values("변화", ascending=(rank_mode == "감소 Top 10")).head(10)
fig4 = px.bar(ranked, x="변화", y="기관명", orientation="h", color="기관유형",
               color_discrete_map=ORG_TYPE_COLORS, labels={"변화": f"{get_label(var_key)} {change_label}"})
fig4.update_layout(font=dict(size=16), height=420)
st.plotly_chart(fig4, use_container_width=True)

st.divider()

# ---------------- 순위 안정성 ----------------
st.markdown(f"### 🔄 순위 안정성 (Rank-Rank): {y_from}년 vs {y_to}년")
merged["순위_이전"] = merged["이전값"].rank(ascending=False)
merged["순위_이후"] = merged["이후값"].rank(ascending=False)
if merged.shape[0] > 3:
    rho, p = stats.spearmanr(merged["순위_이전"], merged["순위_이후"])
    st.write(f"**Spearman 순위상관계수** = {rho:.3f} (p = {p:.4f}, N = {merged.shape[0]:,})")
    fig5 = plot_rank_scatter(merged, "순위_이전", "순위_이후", f"{y_from}년 순위", f"{y_to}년 순위")
    st.plotly_chart(fig5, use_container_width=True)
    st.caption("💡 대각선(점선)에 가까울수록 두 연도의 순위가 유지된다는 뜻입니다. "
                "수준이 높은 기관과 변화율이 높은 기관이 반드시 같지는 않습니다.")
else:
    st.info("순위상관을 계산할 만큼 관측치가 부족합니다.")

st.divider()

# ---------------- 변화량 관계 ----------------
st.markdown(f"### 🔗 다른 변수의 {y_from}→{y_to} 변화와의 관계")
other_vars = [v for v in TREND_VARS if v != var_key]
other_key = st.selectbox("비교할 변수", other_vars, format_func=lambda k: get_label(k), key="p13_otherg")
other_col = VARIABLES[other_key]["column"]
other_is_ratio = VARIABLES[other_key]["percent"]
other_label = "증감(%p)" if other_is_ratio else "증가율(%)"

od_from = df[df["연도"] == y_from][["기관명", other_col]].dropna().rename(columns={other_col: "이전값2"})
od_to = df[df["연도"] == y_to][["기관명", other_col]].dropna().rename(columns={other_col: "이후값2"})
omerged = pd.merge(od_from, od_to, on="기관명")
if other_is_ratio:
    omerged["변화2"] = omerged["이후값2"] - omerged["이전값2"]
else:
    omerged = omerged[omerged["이전값2"] != 0]
    omerged["변화2"] = (omerged["이후값2"] - omerged["이전값2"]) / omerged["이전값2"] * 100
omerged = omerged.replace([float("inf"), float("-inf")], pd.NA).dropna(subset=["변화2"])

joint = pd.merge(merged[["기관명", "변화"]], omerged[["기관명", "변화2"]], on="기관명")
if joint.shape[0] > 3:
    fig6 = px.scatter(joint, x="변화", y="변화2", trendline="ols",
                        labels={"변화": f"{get_label(var_key)} {change_label}", "변화2": f"{get_label(other_key)} {other_label}"})
    fig6.update_layout(font=dict(size=16), height=480)
    st.plotly_chart(fig6, use_container_width=True)
    r, p = stats.pearsonr(joint["변화"], joint["변화2"])
    st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {joint.shape[0]:,}")
else:
    st.info("관계를 계산할 만큼 관측치가 부족합니다.")

st.caption(f"※ 이 페이지의 모든 분석은 {y_from}년 → {y_to}년, 단 하나의 변화기간만 사용합니다 "
            "(여러 기간의 변화를 한꺼번에 섞지 않습니다). 다른 기간을 보려면 위에서 연도를 다시 선택하세요.")
