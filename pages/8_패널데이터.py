import streamlit as st
import pandas as pd

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.metrics import add_growth_variables
from utils.charts import plot_time_series
from utils.regression import run_ols, coef_table, model_summary_stats

st.set_page_config(page_title="패널데이터", layout="wide")
st.title("⑧ 패널데이터")
st.markdown("#### 오늘의 질문")
st.info("**Q8. 기관 간 차이와 동일 기관 내부의 시간 변화는 서로 다른가?**")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p8")

PANEL_VARS = ["임직원수", "총수입", "정부지원의존도", "직원평균보수", "신규채용률",
              "복리후생비", "여성육아휴직사용률", "남성육아휴직사용률"]

st.markdown("### 기관별 시계열")
var_key = st.selectbox("변수 선택", PANEL_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p8_var")
col = VARIABLES[var_key]["column"]

orgs = sorted(df["기관명"].unique())
default_orgs = orgs[:5]
sel_orgs = st.multiselect("기관 선택 (여러 개 비교 가능)", orgs, default=default_orgs, key="p8_orgs_ts")

if col in df.columns and sel_orgs:
    st.plotly_chart(plot_time_series(df, col, entities=sel_orgs, var_key=var_key), use_container_width=True)
else:
    st.info("기관을 1개 이상 선택하세요.")

st.markdown("### 기관유형별 시계열 (평균)")
if col in df.columns:
    st.plotly_chart(plot_time_series(df, col, var_key=var_key, agg="기관유형평균"), use_container_width=True)

st.divider()

# ---------------- 변화량 분석 ----------------
st.markdown("### 변화량(전년 대비 증가율) 분석")
growth_targets = ["총수입", "임직원수", "직원평균보수", "복리후생비", "신규채용률", "정부지원의존도"]
growth_cols = [VARIABLES[v]["column"] for v in growth_targets if VARIABLES[v]["column"] in df.columns]
grown = add_growth_variables(df, growth_cols)

g_choice = st.selectbox("증가율을 확인할 변수", growth_targets, format_func=lambda k: get_label(k), key="p8_growth")
g_col = f"{VARIABLES[g_choice]['column']}_증가율"
if g_col in grown.columns:
    gdesc = grown[g_col].replace([float("inf"), float("-inf")], pd.NA).dropna()
    if not gdesc.empty:
        m1, m2, m3 = st.columns(3)
        m1.metric("평균 증가율", f"{gdesc.mean():,.1f}%")
        m2.metric("중앙값", f"{gdesc.median():,.1f}%")
        m3.metric("N", f"{gdesc.shape[0]:,}")
        import plotly.express as px
        fig = px.histogram(gdesc, nbins=40, labels={"value": f"{get_label(g_choice)} 전년대비 증가율(%)"})
        fig.update_layout(font=dict(size=16), height=450, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("증가율을 계산할 관측치가 부족합니다.")

st.divider()

# ---------------- 패널 회귀 ----------------
st.markdown("### 패널 회귀: Pooled OLS vs 고정효과")
st.caption("동일한 모형에서 기관 고정효과·연도 고정효과를 추가했을 때 핵심 변수의 계수가 어떻게 달라지는지 비교합니다.")

DV_OPTIONS = ["직원평균보수", "신규채용률", "1인당복리후생비"]
IV_OPTIONS = ["총수입", "정부지원의존도", "임직원수", "여성직원비율"]

c1, c2 = st.columns(2)
with c1:
    dv_key = st.selectbox("종속변수", DV_OPTIONS, format_func=lambda k: get_label(k), key="p8_dv")
with c2:
    iv_key = st.selectbox("핵심 설명변수", [v for v in IV_OPTIONS if v != dv_key], format_func=lambda k: get_label(k), key="p8_iv")

dv_col = VARIABLES[dv_key]["column"]
iv_col = VARIABLES[iv_key]["column"]

if dv_col in df.columns and iv_col in df.columns:
    specs = [
        ("Pooled OLS", False, False),
        ("기관 고정효과", True, False),
        ("연도 고정효과", False, True),
        ("기관+연도 고정효과", True, True),
    ]
    rows = []
    tabs = st.tabs([s[0] for s in specs])
    for (name, efe, yfe), tab in zip(specs, tabs):
        with tab:
            res, data = run_ols(df, dv_col, [iv_col], entity_fe=efe, year_fe=yfe)
            if res is None:
                st.warning("관측치가 부족하여 이 모형을 추정할 수 없습니다. (고정효과 더미가 많아 표본 대비 변수가 과다할 수 있습니다)")
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
                         f"(p = {focus['p_value'].values[0]:.4f})")
                rows.append({"variable": name, "coef": focus["coef"].values[0],
                             "ci_low": focus["ci_low"].values[0], "ci_high": focus["ci_high"].values[0]})
            st.dataframe(ct.round(4), use_container_width=True, hide_index=True)

    if rows:
        from utils.charts import plot_coefficient
        coef_df = pd.DataFrame(rows)
        st.plotly_chart(plot_coefficient(coef_df, title=f"{get_label(iv_key)} 계수: 모형별 비교"), use_container_width=True)
        st.caption("💡 기관 고정효과를 추가하면 '동일 기관의 시간에 따른 변화'만으로 계수를 추정합니다. "
                   "Pooled OLS와 계수가 크게 다르다면, 관측되지 않은 기관 고유 특성이 원래 회귀식에 영향을 주고 있었을 가능성이 있습니다.")
else:
    st.warning("선택한 변수 조합이 데이터에 없습니다.")
