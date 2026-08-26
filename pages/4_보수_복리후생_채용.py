import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_cleaner import get_full_panel, describe_var
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.charts import plot_histogram, plot_boxplot, plot_rank_bar, plot_scatter

st.set_page_config(page_title="보수·복리후생·채용", layout="wide")
st.title("④ 보수 · 복리후생 · 채용")
st.caption("탭을 이동하며 보수, 임원, 복리후생, 채용 지표를 살펴보는 페이지입니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p4")

tab1, tab2, tab3, tab4 = st.tabs(["💵 보수", "👔 임원", "🎁 복리후생", "🧑‍💼 채용"])

# ================= TAB 1: 보수 =================
with tab1:
    pay_vars = ["직원평균보수", "기본급", "고정수당", "실적수당", "성과상여금", "경영평가성과급", "신입사원초임", "평균근속연수"]
    pay_vars = [v for v in pay_vars if VARIABLES[v]["column"] in df.columns]
    var_key = st.selectbox("변수 선택", pay_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p4_payvar")
    col = VARIABLES[var_key]["column"]
    desc = describe_var(df, col)
    if desc.get("N", 0) > 0:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("N", f"{desc['N']:,}")
        k2.metric("평균", f"{desc['평균']:,.1f}")
        k3.metric("중앙값", f"{desc['중앙값']:,.1f}")
        k4.metric("표준편차", f"{desc['표준편차']:,.1f}")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_histogram(df, col, var_key=var_key), use_container_width=True)
        with c2:
            st.plotly_chart(plot_boxplot(df, col, var_key=var_key), use_container_width=True)

    st.markdown("#### 보수 구성비 (기관유형 평균, 100% 기준)")
    comp_vars = ["기본급", "고정수당", "실적수당", "성과상여금", "경영평가성과급"]
    comp_cols = [VARIABLES[v]["column"] for v in comp_vars if VARIABLES[v]["column"] in df.columns]
    if comp_cols:
        grp = df.groupby("기관유형")[comp_cols].mean()
        grp_pct = grp.div(grp.sum(axis=1), axis=0) * 100
        long = grp_pct.reset_index().melt(id_vars="기관유형", var_name="구성", value_name="비중(%)")
        fig = px.bar(long, x="기관유형", y="비중(%)", color="구성", barmode="stack")
        fig.update_layout(font=dict(size=16), height=460)
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 기본급 비중이 큰 기관은 연공서열형, 성과상여금·경영평가성과급 비중이 큰 기관은 성과중심형 보수체계에 가깝습니다.")

# ================= TAB 2: 임원 =================
with tab2:
    exe_vars = ["기관장연봉", "임원평균연봉", "직원평균보수", "기관장직원보수배율"]
    exe_vars = [v for v in exe_vars if VARIABLES[v]["column"] in df.columns]
    var_key2 = st.selectbox("변수 선택", exe_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p4_exevar")
    col2 = VARIABLES[var_key2]["column"]
    desc2 = describe_var(df, col2)
    if desc2.get("N", 0) > 0:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("N", f"{desc2['N']:,}")
        k2.metric("평균", f"{desc2['평균']:,.2f}")
        k3.metric("중앙값", f"{desc2['중앙값']:,.2f}")
        k4.metric("표준편차", f"{desc2['표준편차']:,.2f}")
        st.plotly_chart(plot_boxplot(df, col2, var_key=var_key2), use_container_width=True)

    st.markdown("#### 기관장-직원 보수배율 Top / Bottom")
    if "기관장직원보수배율" in VARIABLES and VARIABLES["기관장직원보수배율"]["column"] in df.columns:
        rank_mode = st.radio("정렬", ["Top 10", "Bottom 10"], horizontal=True, key="p4_exerank")
        st.plotly_chart(
            plot_rank_bar(df, VARIABLES["기관장직원보수배율"]["column"], var_key="기관장직원보수배율",
                           top_n=10, ascending=(rank_mode == "Bottom 10")),
            use_container_width=True,
        )

# ================= TAB 3: 복리후생 =================
with tab3:
    wel_vars = ["복리후생비", "1인당복리후생비", "기관장업무추진비", "1인당기관장업무추진비"]
    wel_vars = [v for v in wel_vars if VARIABLES[v]["column"] in df.columns]
    var_key3 = st.selectbox("변수 선택", wel_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p4_welvar")
    col3 = VARIABLES[var_key3]["column"]
    desc3 = describe_var(df, col3)
    if desc3.get("N", 0) > 0:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("N", f"{desc3['N']:,}")
        k2.metric("평균", f"{desc3['평균']:,.1f}")
        k3.metric("중앙값", f"{desc3['중앙값']:,.1f}")
        k4.metric("표준편차", f"{desc3['표준편차']:,.1f}")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_histogram(df, col3, var_key=var_key3), use_container_width=True)
        with c2:
            st.plotly_chart(plot_boxplot(df, col3, var_key=var_key3), use_container_width=True)

    st.markdown("#### 총액 vs 1인당: 같은 순위일까?")
    if "복리후생비" in VARIABLES and "1인당복리후생비" in VARIABLES:
        total_col = VARIABLES["복리후생비"]["column"]
        percap_col = VARIABLES["1인당복리후생비"]["column"]
        if total_col in df.columns and percap_col in df.columns:
            fig5 = plot_scatter(df, total_col, percap_col, x_key="복리후생비", y_key="1인당복리후생비")
            st.plotly_chart(fig5, use_container_width=True)
            st.caption("⚠️ 총액이 큰 기관이 반드시 1인당 금액도 큰 것은 아닙니다. 기관 규모(임직원수)를 함께 고려해야 합니다.")

# ================= TAB 4: 채용 =================
with tab4:
    hire_vars = ["신규채용자수", "신규채용률", "여성신규채용자수", "여성신규채용비율"]
    hire_vars = [v for v in hire_vars if VARIABLES[v]["column"] in df.columns]
    var_key4 = st.selectbox("변수 선택", hire_vars, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p4_hirevar")
    col4 = VARIABLES[var_key4]["column"]
    desc4 = describe_var(df, col4)
    if desc4.get("N", 0) > 0:
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("N", f"{desc4['N']:,}")
        k2.metric("평균", f"{desc4['평균']:,.1f}")
        k3.metric("중앙값", f"{desc4['중앙값']:,.1f}")
        k4.metric("표준편차", f"{desc4['표준편차']:,.1f}")
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(plot_histogram(df, col4, var_key=var_key4), use_container_width=True)
        with c2:
            st.plotly_chart(plot_boxplot(df, col4, var_key=var_key4), use_container_width=True)

    st.markdown("#### 명수 vs 비율: 신규채용자수와 신규채용률은 같은 정보일까?")
    n_col = VARIABLES["신규채용자수"]["column"]
    r_col = VARIABLES["신규채용률"]["column"]
    if n_col in df.columns and r_col in df.columns:
        fig6 = plot_scatter(df, n_col, r_col, x_key="신규채용자수", y_key="신규채용률")
        st.plotly_chart(fig6, use_container_width=True)
        st.caption("⚠️ 신규채용자 수가 많아도 임직원 규모가 크면 신규채용률은 낮을 수 있습니다. 두 지표는 서로 다른 정보를 담고 있습니다.")
