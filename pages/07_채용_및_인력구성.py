import streamlit as st
import pandas as pd

from utils.data_cleaner import get_full_panel, describe_var
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.charts import plot_histogram, plot_boxplot, plot_scatter
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="채용 및 인력구성", layout="wide")
st.title("⑦ 채용 및 인력구성")
render_intro(
    purpose="기관 규모를 고려했을 때, 채용 수준과 인력구성(특히 성별 구성)이 기관별로 어떻게 다른지 살펴봅니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="기술통계 · 히스토그램/Box plot · 총량 vs 비율 비교",
    caution="채용 인원(총량)이 많다고 해서 채용률(비율)도 높은 것은 아닙니다. 기관 규모를 함께 고려해야 합니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p7")
view, caption, mode = year_slice(df, key_prefix="p7")
st.caption(caption)

st.divider()
hire_vars = ["임직원수", "정규직현원", "여성현원", "여성직원비율",
             "신규채용자수", "신규채용률", "여성신규채용자수", "여성신규채용비율",
             "청년신규채용자수", "장애인신규채용자수"]
hire_vars = [v for v in hire_vars if VARIABLES[v]["column"] in view.columns]
var_key = st.selectbox("변수 선택", hire_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p7_var")
col = VARIABLES[var_key]["column"]

desc = describe_var(view, col)
if desc.get("N", 0) > 0:
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("N", f"{desc['N']:,}")
    k2.metric("평균", f"{desc['평균']:,.1f}")
    k3.metric("중앙값", f"{desc['중앙값']:,.1f}")
    k4.metric("표준편차", f"{desc['표준편차']:,.1f}")
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_histogram(view, col, var_key=var_key), use_container_width=True)
    with c2:
        st.plotly_chart(plot_boxplot(view, col, var_key=var_key), use_container_width=True)

st.divider()
st.markdown("### 📐 핵심 개념: 총량 vs 비율")
n_col = VARIABLES["신규채용자수"]["column"]
r_col = VARIABLES["신규채용률"]["column"]
if n_col in view.columns and r_col in view.columns:
    fig6 = plot_scatter(view, n_col, r_col, x_key="신규채용자수", y_key="신규채용률")
    st.plotly_chart(fig6, use_container_width=True)
    st.caption("⚠️ 신규채용자 수가 많아도 임직원 규모가 크면 신규채용률은 낮을 수 있습니다. 두 지표는 서로 다른 정보를 담고 있습니다.")

st.markdown("### 👥 성별 구성: 여성직원비율 ↔ 여성신규채용비율")
if "여성직원비율" in VARIABLES and "여성신규채용비율" in VARIABLES:
    a_col = VARIABLES["여성직원비율"]["column"]
    b_col = VARIABLES["여성신규채용비율"]["column"]
    if a_col in view.columns and b_col in view.columns:
        fig7 = plot_scatter(view, a_col, b_col, x_key="여성직원비율", y_key="여성신규채용비율")
        st.plotly_chart(fig7, use_container_width=True)
        st.caption("💡 기존 여성 직원 비율과 여성 신규채용 비율이 다르다면, 조직의 성별 구성이 변화하는 방향을 짐작할 수 있습니다.")

st.divider()

# ---------------- 🔗 다른 부문과의 관계 ----------------
st.markdown("### 🔗 다른 부문과의 관계")
st.caption("채용 수준이 재정·보수 같은 다른 부문과 어떻게 연결되는지 미리 살펴봅니다. 더 자유로운 조합은 ⑧⑨번 페이지에서 확인할 수 있습니다.")
from scipy import stats as _stats

cross_pairs = [
    ("정부지원의존도", "신규채용률", "재정 → 채용"),
    ("직원평균보수", "신규채용률", "보수 → 채용"),
]
cc1, cc2 = st.columns(2)
for c, (xk, yk, label) in zip([cc1, cc2], cross_pairs):
    xcol, ycol = VARIABLES[xk]["column"], VARIABLES[yk]["column"]
    with c:
        if xcol in view.columns and ycol in view.columns:
            sub = view[[xcol, ycol]].dropna()
            fig_c = plot_scatter(view, xcol, ycol, x_key=xk, y_key=yk)
            st.plotly_chart(fig_c, use_container_width=True, key=f"p7_cross_{xk}_{yk}")
            if sub.shape[0] > 2:
                r, p = _stats.pearsonr(sub[xcol], sub[ycol])
                st.caption(f"**{label}**: r = {r:.3f} (N = {sub.shape[0]:,})")

st.divider()
st.markdown("### 🤔 탐색해볼 질문")
st.info("채용 인원이 많은 기관은 채용률도 높을까? 여성직원 비율과 여성신규채용 비율은 함께 움직일까? "
        "→ 더 자세한 관계 탐색은 ⑧⑨번 페이지에서 이어서 확인할 수 있습니다.")
