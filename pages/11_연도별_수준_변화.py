import streamlit as st
import plotly.graph_objects as go

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit, get_allowed_agg
from utils.page_header import render_intro

st.set_page_config(page_title="연도별 수준 변화", layout="wide")
st.title("⑪ 연도별 수준 변화")
render_intro(
    purpose="공공기관 지표의 평균 또는 총량이 시간에 따라 어떻게 변화했는지 살펴봅니다.",
    unit="연도별 전체 기관-연도 관측치 (이 페이지는 추세만 다루며, 변화율·순위 안정성은 ⑫번 페이지에서 다룹니다)",
    methods="전체·기관유형·주무부처·개별기관 수준을 한 그래프에서 최대 4개 선으로 비교",
    caution="합계 추이는 기관 수 변화(신설·통폐합 등)에도 영향을 받고, 평균 추이는 이상치 기관 하나에도 크게 흔들릴 수 있습니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p12")

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
    var_key = st.selectbox("변수 선택 (13개)", TREND_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p12_var")
allowed = get_allowed_agg(var_key)
with c2:
    agg = st.radio("집계 방식", allowed, horizontal=True, key="p12_agg")
col = VARIABLES[var_key]["column"]
agg_func = "mean" if agg == "평균" else "sum"

st.markdown(f"### 📈 연도별 {agg} 추이 — 비교 수준 선택")
st.caption("전체·기관유형·주무부처·개별기관 중 원하는 선을 골라 한 그래프에서 비교합니다 (최대 4개 권장). "
            "기관유형을 고르면 주무부처 목록이, 주무부처를 고르면 개별기관 목록이 그 안으로 좁혀집니다.")

lc1, lc2, lc3, lc4 = st.columns(4)
with lc1:
    show_overall = st.checkbox("전체 평균/합계", value=True, key="p12_showoverall")
with lc2:
    sel_types = st.multiselect("기관유형", sorted(df["기관유형"].unique()), key="p12_seltypes")

# 기관유형 선택에 따라 주무부처 후보를 좁힌다
dept_pool = df[df["기관유형"].isin(sel_types)] if sel_types else df
dept_options = sorted(dept_pool["주무부처"].unique())
if "p12_seldepts" in st.session_state:
    st.session_state["p12_seldepts"] = [d for d in st.session_state["p12_seldepts"] if d in dept_options]
with lc3:
    sel_depts = st.multiselect("주무부처", dept_options, key="p12_seldepts")

# 주무부처 선택에 따라 개별기관 후보를 좁힌다 (기관유형 선택도 함께 반영)
org_pool = dept_pool[dept_pool["주무부처"].isin(sel_depts)] if sel_depts else dept_pool
org_options = sorted(org_pool["기관명"].unique())
if "p12_selorgs" in st.session_state:
    st.session_state["p12_selorgs"] = [o for o in st.session_state["p12_selorgs"] if o in org_options]
with lc4:
    sel_orgs_trend = st.multiselect("개별기관", org_options, key="p12_selorgs")

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

fig1.update_layout(font=dict(size=16), height=560, yaxis_title=f"{get_label(var_key)} ({get_unit(var_key)})", xaxis_title="연도")
st.plotly_chart(fig1, use_container_width=True)
