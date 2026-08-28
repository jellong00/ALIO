import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.charts import plot_time_series, plot_coefficient
from utils.regression import run_ols, coef_table, model_summary_stats
from utils.page_header import render_intro

st.set_page_config(page_title="패널데이터 분석", layout="wide")
st.title("⑭ 패널데이터 분석")
render_intro(
    purpose="기관 간 차이(between)와 동일 기관의 시간적 변화(within)를 구분하고, 이를 반영한 회귀모형을 비교합니다.",
    unit="기관-연도 패널 전체 (동일 기관의 여러 연도 값을 함께 사용하는 것이 이 페이지의 목적입니다)",
    methods="기관/유형/부처별 시계열 · Between-Within 분해 · Pooled OLS vs 고정효과/더미통제 비교",
    caution="고정효과·더미변수를 많이 추가하면 R²가 기계적으로 높아질 수 있어, 'R²가 높으니 더 좋은 모형'이라고 단순 비교하면 안 됩니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p15")

st.markdown("### 📋 패널 구성 요약")
st.caption("이 페이지는 기관-연도 패널 전체를 사용합니다 (동일 기관이 여러 연도로 반복 관측됩니다).")
_n_orgs = df["기관명"].nunique()
_n_obs = df.shape[0]
_years = sorted(df["연도"].unique())
_year_range = f"{_years[0]}–{_years[-1]}" if _years else "N/A"
_avg_years = df.groupby("기관명")["연도"].nunique().mean() if _n_orgs else 0
pc1, pc2, pc3, pc4 = st.columns(4)
pc1.metric("기관 수", f"{_n_orgs:,}")
pc2.metric("전체 관측치 수 (기관-연도)", f"{_n_obs:,}")
pc3.metric("연도 범위", _year_range)
pc4.metric("기관별 평균 관측 연도 수", f"{_avg_years:.1f}")
st.divider()

PANEL_VARS = ["임직원수", "총수입", "정부지원의존도", "직원평균보수", "신규채용률",
              "복리후생비", "여성육아휴직사용자수", "남성육아휴직사용자수"]
PANEL_VARS = [v for v in PANEL_VARS if VARIABLES[v]["column"] in df.columns]

st.divider()
var_key = st.selectbox("변수 선택", PANEL_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p15_var")
col = VARIABLES[var_key]["column"]

st.markdown("### 기관별 시계열")
orgs = sorted(df["기관명"].unique())
sel_orgs = st.multiselect("기관 선택 (여러 개 비교 가능)", orgs, default=orgs[:5], key="p15_ts_orgs")
if sel_orgs:
    st.plotly_chart(plot_time_series(df, col, entities=sel_orgs, var_key=var_key), use_container_width=True)
else:
    st.info("기관을 1개 이상 선택하세요.")

st.markdown("### 기관유형별 시계열 (평균)")
st.plotly_chart(plot_time_series(df, col, var_key=var_key, agg="기관유형평균"), use_container_width=True)

st.markdown("### 주무부처별 시계열 (평균)")
depts = sorted(df["주무부처"].unique())
sel_depts_ts = st.multiselect("주무부처 선택 (최대 5개 권장)", depts, default=depts[:3], key="p15_seldepts")
if sel_depts_ts:
    dept_ts = df[df["주무부처"].isin(sel_depts_ts)].groupby(["주무부처", "연도"])[col].mean().reset_index()
    fig_dept_ts = px.line(dept_ts, x="연도", y=col, color="주무부처", markers=True,
                            labels={col: f"{get_label(var_key)} ({get_unit(var_key)})"})
    fig_dept_ts.update_layout(font=dict(size=16), height=460)
    st.plotly_chart(fig_dept_ts, use_container_width=True)
else:
    st.info("주무부처를 1개 이상 선택하세요.")

st.divider()

# ---------------- Between / Within ----------------
st.markdown("### 🔍 Between-Within 분해")
st.caption("같은 변수를 '기관 간 평균 차이(between)'와, 기관평균에서 벗어난 '기관 내부 편차(within variation)'로 나누어 봅니다. "
            "within 값은 전년 대비 변화량이 아니라, 각 연도 값에서 그 기관의 전체 평균을 뺀 편차입니다.")
d = df[["기관명", col]].dropna().copy()
if not d.empty:
    inst_mean = d.groupby("기관명")[col].transform("mean")
    d["between"] = inst_mean
    d["within"] = d[col] - inst_mean + d[col].mean()

    c1, c2 = st.columns(2)
    with c1:
        between_by_org = d.groupby("기관명")["between"].first()
        fig_b = px.histogram(between_by_org, nbins=30, labels={"value": f"{get_label(var_key)} (기관별 평균)"})
        fig_b.update_layout(font=dict(size=15), height=420, showlegend=False, title="기관 간 평균 차이 (Between)")
        st.plotly_chart(fig_b, use_container_width=True)
    with c2:
        fig_w = px.histogram(d["within"], nbins=30, labels={"value": f"{get_label(var_key)} (평균 중심화)"})
        fig_w.update_layout(font=dict(size=15), height=420, showlegend=False,
                              title="기관평균에서 벗어난 기관 내부 편차 (Within variation)")
        st.plotly_chart(fig_w, use_container_width=True)
    st.caption("💡 Between 분포가 넓게 퍼져 있으면 '기관 간 차이'가 크다는 뜻이고, "
                "Within 분포가 넓으면 같은 기관 안에서도 연도에 따라 값의 편차가 크다는 뜻입니다.")
else:
    st.info("선택한 변수에 유효한 관측치가 없습니다.")

st.divider()

# ---------------- 패널 회귀 ----------------
st.markdown("### 패널 회귀: Pooled OLS vs 고정효과/더미통제")
DV_OPTIONS = ["직원평균보수", "신규채용률", "1인당복리후생비"]
IV_OPTIONS = ["총수입", "정부지원의존도", "임직원수", "여성직원비율"]

c1, c2 = st.columns(2)
with c1:
    dv_key = st.selectbox("종속변수", DV_OPTIONS, format_func=lambda k: get_label(k), key="p15_dv")
with c2:
    iv_key = st.selectbox("핵심 설명변수", [v for v in IV_OPTIONS if v != dv_key], format_func=lambda k: get_label(k), key="p15_iv")

dv_col = VARIABLES[dv_key]["column"]
iv_col = VARIABLES[iv_key]["column"]

if dv_col in df.columns and iv_col in df.columns:
    use_dept_dummy = st.checkbox("주무부처 더미 통제도 비교에 포함", value=False, key="p15_deptdummy")
    specs = [("Pooled OLS", False, False, False), ("기관 고정효과", True, False, False),
             ("연도 고정효과", False, True, False), ("기관+연도 고정효과", True, True, False)]
    if use_dept_dummy:
        specs.append(("주무부처 더미 통제", False, False, True))
    rows = []
    tabs = st.tabs([s[0] for s in specs])
    for (name, efe, yfe, ddummy), tab in zip(specs, tabs):
        with tab:
            cat_controls = ["주무부처"] if ddummy else []
            res, data, X = run_ols(df, dv_col, [iv_col], cat_controls=cat_controls, entity_fe=efe, year_fe=yfe)
            if res is None:
                st.warning("관측치가 부족하여 이 모형을 추정할 수 없습니다.")
                continue
            ct = coef_table(res)
            stats_ = model_summary_stats(res)
            s1, s2, s3 = st.columns(3)
            s1.metric("N", stats_["N"])
            s2.metric("R²", f"{stats_['R²']:.3f}")
            s3.metric("adj. R²", f"{stats_['adj. R²']:.3f}")
            focus = ct[ct["variable"] == iv_col]
            if not focus.empty:
                st.write(f"**{get_label(iv_key)} 계수** = {focus['coef'].values[0]:,.4f} "
                         f"(SE = {focus['std_err'].values[0]:,.4f}, p = {focus['p_value'].values[0]:.4f})")
                rows.append({"variable": name, "coef": focus["coef"].values[0],
                              "ci_low": focus["ci_low"].values[0], "ci_high": focus["ci_high"].values[0]})
            st.dataframe(ct.round(4), use_container_width=True, hide_index=True)

    st.caption("⚠️ 기관 더미를 수백 개 추가하면 R²가 기계적으로 크게 올라갈 수 있습니다. "
                "'R²가 더 높은 모형이 더 좋다'고 단순 비교하지 말고, 핵심 설명변수의 계수가 모형마다 어떻게 달라지는지를 중심으로 보세요.")

    if rows:
        coef_df = pd.DataFrame(rows)
        st.plotly_chart(plot_coefficient(coef_df, title=f"{get_label(iv_key)} 계수: 모형별 비교"), use_container_width=True)

    st.info(
        "**Pooled OLS**는 기관 간 차이와 기관 내부의 시간 변화를 함께 사용해 계수를 추정합니다.\n\n"
        "**기관 고정효과**는 시간에 따라 변하지 않는 기관 고유 특성(업종, 설립 목적 등)을 통제하고, "
        "동일 기관 내부의 변화(within)에만 초점을 둡니다.\n\n"
        "**주무부처 더미 통제**는 같은 부처 산하 기관들 사이의 평균적 수준 차이를 통제합니다. "
        "기관 고정효과와는 다른 수준(부처 vs 기관)의 통제라는 점에 유의하세요.\n\n"
        "두 모형의 계수가 크게 다르다면, 관측되지 않은 고유 특성이 Pooled OLS 결과에 영향을 주고 있었을 가능성이 있습니다."
    )
else:
    st.warning("선택한 변수 조합이 데이터에 없습니다.")
