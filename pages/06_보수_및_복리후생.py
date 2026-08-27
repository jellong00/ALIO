import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_cleaner import get_full_panel, describe_var
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.charts import plot_histogram, plot_boxplot, plot_scatter
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="보수 및 복리후생", layout="wide")
st.title("⑥ 보수 및 복리후생")
render_intro(
    purpose="직원 보수 수준·구성, 임원보수, 복리후생 지출 수준이 기관별로 어떻게 다른지 살펴봅니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="기술통계 · 히스토그램/Box plot · 보수 구성비 · 총액 vs 1인당 비교",
    caution="보수 구성비만으로 임금체계가 연공형인지 성과형인지 단정할 수 없습니다 (호봉·직무급 구조 등 추가 정보가 필요합니다).",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p6")
view, caption, mode = year_slice(df, key_prefix="p6")
st.caption(caption)

tab1, tab2, tab3 = st.tabs(["💵 직원 보수", "👔 임원 보수", "🎁 복리후생"])

# ================= TAB 1: 직원 보수 =================
with tab1:
    pay_vars = ["직원평균보수", "기본급", "고정수당", "실적수당", "성과상여금", "경영평가성과급", "신입사원초임", "평균근속연수"]
    pay_vars = [v for v in pay_vars if VARIABLES[v]["column"] in view.columns]
    var_key = st.selectbox("변수 선택", pay_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p6_payvar")
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

    st.markdown("#### 보수 구성비 (기관유형 평균, 100% 기준)")
    st.caption("각 기관에서 먼저 구성비를 계산한 뒤, 기관유형별로 그 구성비를 평균했습니다 "
                "(항목별 평균을 먼저 구해 나누는 방식과 달리, '평균적인 기관의 보수구성'에 더 가깝습니다).")
    comp_vars = ["기본급", "고정수당", "실적수당", "성과상여금", "경영평가성과급"]
    comp_cols = [VARIABLES[v]["column"] for v in comp_vars if VARIABLES[v]["column"] in view.columns]
    if comp_cols:
        comp_df = view[["기관유형"] + comp_cols].dropna(subset=comp_cols, how="all").copy()
        row_total = comp_df[comp_cols].sum(axis=1)
        valid = row_total > 0
        comp_ratio = comp_df.loc[valid, comp_cols].div(row_total[valid], axis=0) * 100
        comp_ratio["기관유형"] = comp_df.loc[valid, "기관유형"]
        grp_pct = comp_ratio.groupby("기관유형")[comp_cols].mean()
        long = grp_pct.reset_index().melt(id_vars="기관유형", var_name="구성", value_name="비중(%)")
        fig = px.bar(long, x="기관유형", y="비중(%)", color="구성", barmode="stack")
        fig.update_layout(font=dict(size=16), height=460)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("보수 총액에서 기본급·수당·성과급이 차지하는 상대적 비중을 비교한 결과이며, "
                    "이 구성비만으로 임금체계가 연공형인지 성과형인지 판단할 수는 없습니다.")

    st.divider()
    st.markdown("#### 🤔 탐색해볼 질문")
    st.info("평균보수가 높은 기관은 신입초임도 높을까? 평균보수가 높은 것은 근속연수가 길어서일까? "
            "→ 자세한 관계 탐색은 ⑧번 페이지에서 이어서 확인할 수 있습니다.")

# ================= TAB 2: 임원 보수 =================
with tab2:
    exe_vars = ["기관장연봉", "임원평균연봉", "직원평균보수", "기관장직원보수배율"]
    exe_vars = [v for v in exe_vars if VARIABLES[v]["column"] in view.columns]
    var_key2 = st.selectbox("변수 선택", exe_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p6_exevar")
    col2 = VARIABLES[var_key2]["column"]
    desc2 = describe_var(view, col2)
    if desc2.get("N", 0) > 0:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("N", f"{desc2['N']:,}")
        k2.metric("평균", f"{desc2['평균']:,.2f}")
        k3.metric("중앙값", f"{desc2['중앙값']:,.2f}")
        k4.metric("표준편차", f"{desc2['표준편차']:,.2f}")
        st.plotly_chart(plot_boxplot(view, col2, var_key=var_key2), use_container_width=True)

    st.markdown("#### 기관장연봉 ↔ 직원평균보수")
    if "기관장연봉" in view.columns and "직원평균보수" in view.columns:
        fig_exe = plot_scatter(view, "직원평균보수", "기관장연봉", x_key="직원평균보수", y_key="기관장연봉")
        st.plotly_chart(fig_exe, use_container_width=True)

# ================= TAB 3: 복리후생 =================
with tab3:
    wel_vars = ["복리후생비", "1인당복리후생비", "기관장업무추진비", "1인당기관장업무추진비"]
    wel_vars = [v for v in wel_vars if VARIABLES[v]["column"] in view.columns]
    var_key3 = st.selectbox("변수 선택", wel_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p6_welvar")
    col3 = VARIABLES[var_key3]["column"]
    desc3 = describe_var(view, col3)
    if desc3.get("N", 0) > 0:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("N", f"{desc3['N']:,}")
        k2.metric("평균", f"{desc3['평균']:,.1f}")
        k3.metric("중앙값", f"{desc3['중앙값']:,.1f}")
        k4.metric("표준편차", f"{desc3['표준편차']:,.1f}")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_histogram(view, col3, var_key=var_key3), use_container_width=True)
        with c2:
            st.plotly_chart(plot_boxplot(view, col3, var_key=var_key3), use_container_width=True)

    st.markdown("#### 💡 핵심 개념: 총액 vs 1인당")
    if "복리후생비" in VARIABLES and "1인당복리후생비" in VARIABLES:
        total_col = VARIABLES["복리후생비"]["column"]
        percap_col = VARIABLES["1인당복리후생비"]["column"]
        if total_col in view.columns and percap_col in view.columns:
            fig5 = plot_scatter(view, total_col, percap_col, x_key="복리후생비", y_key="1인당복리후생비")
            st.plotly_chart(fig5, use_container_width=True)
            st.caption("⚠️ 총액이 큰 기관이 반드시 1인당 금액도 큰 것은 아닙니다. 기관 규모(임직원수)를 함께 고려해야 합니다.")

            rank_col1, rank_col2 = st.columns(2)
            with rank_col1:
                top_total = view[["기관명", total_col]].dropna().sort_values(total_col, ascending=False).head(5)
                st.markdown("**복리후생비 총액 Top 5**")
                st.dataframe(top_total.rename(columns={total_col: "총액(천원)"}), use_container_width=True, hide_index=True)
            with rank_col2:
                top_percap = view[["기관명", percap_col]].dropna().sort_values(percap_col, ascending=False).head(5)
                st.markdown("**1인당 복리후생비 Top 5**")
                st.dataframe(top_percap.rename(columns={percap_col: "1인당(천원/인)"}), use_container_width=True, hide_index=True)
            st.caption("💡 두 순위표에 같은 기관이 얼마나 겹치는지 확인해보세요. 총액 순위와 1인당 순위는 서로 다른 이야기를 들려줄 수 있습니다.")

st.divider()

# ---------------- 🔗 다른 부문과의 관계 ----------------
st.markdown("### 🔗 다른 부문과의 관계")
st.caption("보수·복리후생 수준이 재정·인력 같은 다른 부문과 어떻게 연결되는지 미리 살펴봅니다. 더 자유로운 조합은 ⑧⑨번 페이지에서 확인할 수 있습니다.")
from scipy import stats as _stats

cross_pairs = [
    ("총수입", "직원평균보수", "재정 → 보수"),
    ("임직원수", "1인당복리후생비", "인력 규모 → 복리후생"),
]
cc1, cc2 = st.columns(2)
for c, (xk, yk, label) in zip([cc1, cc2], cross_pairs):
    xcol, ycol = VARIABLES[xk]["column"], VARIABLES[yk]["column"]
    with c:
        if xcol in view.columns and ycol in view.columns:
            sub = view[[xcol, ycol]].dropna()
            fig_c = plot_scatter(view, xcol, ycol, x_key=xk, y_key=yk)
            st.plotly_chart(fig_c, use_container_width=True, key=f"p6_cross_{xk}_{yk}")
            if sub.shape[0] > 2:
                r, p = _stats.pearsonr(sub[xcol], sub[ycol])
                st.caption(f"**{label}**: r = {r:.3f} (N = {sub.shape[0]:,})")
