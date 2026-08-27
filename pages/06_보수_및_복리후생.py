import streamlit as st
import pandas as pd
import plotly.express as px
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.charts import plot_scatter, plot_rank_bar, plot_group_vs_overall
from utils.level_compare import dept_stats_table
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="보수 및 복리후생", layout="wide")
st.title("⑥ 보수 및 복리후생")
render_intro(
    purpose="직원보수, 임원보수, 복리후생이 서로 어떤 구조를 갖는지 살펴봅니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="보수 구성비 · 대표 관계(평균보수-신입초임 / 근속연수-평균보수) · 총액 vs 1인당 · 순위상관",
    caution="보수 구성비만으로 임금체계가 연공형인지 성과형인지 단정할 수 없습니다. 일반적인 분포(히스토그램·Box plot)는 ① 변수분포 및 기술통계 페이지에서 확인하세요.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p6")
view, caption, mode = year_slice(df, key_prefix="p6")
st.caption(caption)

tab1, tab2, tab3 = st.tabs(["💵 직원 보수", "👔 임원 보수", "🎁 복리후생"])

# ================= TAB 1: 직원 보수 =================
with tab1:
    st.caption("직원 평균보수·신입초임·근속연수·보수 구성(기본급/수당/성과급)의 분포는 → **① 변수분포 및 기술통계** 페이지 [보수] 탭에서 확인할 수 있습니다.")

    st.markdown("#### 보수 구성비 (기관유형 평균, 100% 기준)")
    st.caption("💡 각 기관에서 먼저 구성비를 계산한 뒤, 기관유형별로 그 구성비를 평균했습니다 "
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
    st.markdown("#### 대표 관계 1: 평균보수와 신입초임")
    st.caption("💡 기존 직원 평균보수가 높은 기관은 신규 입사자의 초임도 높은지 확인합니다.")
    if "직원평균보수" in view.columns and "신입사원초임" in view.columns:
        sub = view[["직원평균보수", "신입사원초임"]].dropna()
        fig1 = plot_scatter(view, "직원평균보수", "신입사원초임", x_key="직원평균보수", y_key="신입사원초임")
        st.plotly_chart(fig1, use_container_width=True, key="p6_pay_rel1")
        if sub.shape[0] > 2:
            r, p = stats.pearsonr(sub["직원평균보수"], sub["신입사원초임"])
            st.caption(f"Pearson r = {r:.3f} (N = {sub.shape[0]:,})")

    st.markdown("#### 대표 관계 2: 평균근속연수와 평균보수")
    st.caption("💡 평균보수가 높은 것은 보수체계 자체의 차이일까, 직원들의 평균근속연수가 긴 것과도 관련이 있을까? (인과적으로 해석하지 않습니다.)")
    if "평균근속연수" in view.columns and "직원평균보수" in view.columns:
        sub2 = view[["평균근속연수", "직원평균보수"]].dropna()
        fig2 = plot_scatter(view, "평균근속연수", "직원평균보수", x_key="평균근속연수", y_key="직원평균보수")
        st.plotly_chart(fig2, use_container_width=True, key="p6_pay_rel2")
        if sub2.shape[0] > 2:
            r, p = stats.pearsonr(sub2["평균근속연수"], sub2["직원평균보수"])
            st.caption(f"Pearson r = {r:.3f} (N = {sub2.shape[0]:,})")

    st.divider()
    st.markdown("#### 기관유형별 보수 프리미엄")
    st.caption("💡 어떤 기관유형이 전체 평균보다 보수 수준이 높거나 낮은지 확인합니다.")
    if "직원평균보수" in view.columns:
        st.plotly_chart(plot_group_vs_overall(view, VARIABLES["직원평균보수"]["column"], var_key="직원평균보수"),
                         use_container_width=True, key="p6_pay_premium")

    st.markdown("#### 주무부처별 보수 차이")
    st.caption("💡 소수 기관으로 계산된 부처 평균은 신중하게 해석하세요 (N을 함께 확인).")
    if "직원평균보수" in view.columns:
        dstats = dept_stats_table(view, VARIABLES["직원평균보수"]["column"], min_n=2)
        if not dstats.empty:
            dstats_top = dstats.sort_values("평균", ascending=True).tail(20)
            fig_dept_pay = px.bar(dstats_top, x="평균", y="주무부처", orientation="h",
                                    labels={"평균": "직원평균보수 (천원)"}, hover_data=["N"])
            fig_dept_pay.update_layout(font=dict(size=13), height=max(420, 24 * len(dstats_top)),
                                         title="주무부처별 직원평균보수 (상위 20개 부처, N 순 아님)")
            st.plotly_chart(fig_dept_pay, use_container_width=True)
        else:
            st.info("부처별 비교를 계산할 데이터가 부족합니다.")

    st.markdown("#### 동일유형 내 고보수 기관")
    if "직원평균보수" in view.columns:
        sel_type_pay = st.selectbox("기관유형 선택", sorted(view["기관유형"].dropna().unique()), key="p6_paytype")
        within_type = view[view["기관유형"] == sel_type_pay][["기관명", VARIABLES["직원평균보수"]["column"]]].dropna()
        top5_type = within_type.sort_values(VARIABLES["직원평균보수"]["column"], ascending=False).head(5)
        st.dataframe(top5_type.rename(columns={VARIABLES["직원평균보수"]["column"]: "직원평균보수(천원)"}),
                     use_container_width=True, hide_index=True)

# ================= TAB 2: 임원 보수 =================
with tab2:
    st.caption("기관장연봉·임원평균연봉·보수배율의 분포는 → **① 변수분포 및 기술통계** 페이지 [임원] 탭에서 확인할 수 있습니다.")

    st.markdown("#### 기관장연봉과 직원평균보수")
    if "기관장연봉" in view.columns and "직원평균보수" in view.columns:
        fig_exe = plot_scatter(view, "직원평균보수", "기관장연봉", x_key="직원평균보수", y_key="기관장연봉")
        st.plotly_chart(fig_exe, use_container_width=True)

    st.divider()
    st.markdown("#### 기관장-직원 보수배율 순위")
    if "기관장직원보수배율" in VARIABLES and VARIABLES["기관장직원보수배율"]["column"] in view.columns:
        rank_mode = st.radio("정렬", ["Top 10", "Bottom 10"], horizontal=True, key="p6_exerank")
        st.plotly_chart(
            plot_rank_bar(view, VARIABLES["기관장직원보수배율"]["column"], var_key="기관장직원보수배율",
                           top_n=10, ascending=(rank_mode == "Bottom 10")),
            use_container_width=True,
        )

# ================= TAB 3: 복리후생 =================
with tab3:
    st.caption("복리후생비·1인당복리후생비·업무추진비의 분포는 → **① 변수분포 및 기술통계** 페이지 [복리후생] 탭에서 확인할 수 있습니다.")

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

            st.markdown("#### 두 순위의 순위상관")
            st.caption("💡 복리후생비 총액 순위와 1인당 순위는 얼마나 비슷한가? (기관 규모의 영향을 확인하는 지표입니다.)")
            rank_sub = view[["기관명", total_col, percap_col]].dropna()
            if rank_sub.shape[0] > 3:
                rho, p = stats.spearmanr(rank_sub[total_col], rank_sub[percap_col])
                st.metric("Spearman ρ (총액 순위 vs 1인당 순위)", f"{rho:.3f}")
                if rho > 0.7:
                    st.caption("두 순위가 상당히 비슷합니다 — 기관 규모가 커도 1인당 지출까지 함께 큰 경향이 있습니다.")
                elif rho < 0.3:
                    st.caption("두 순위가 많이 다릅니다 — 총액이 큰 기관과 1인당 지출이 큰 기관이 서로 다른 경우가 많습니다.")
                else:
                    st.caption("두 순위가 어느 정도 겹치지만 완전히 같지는 않습니다.")

    st.divider()
    st.markdown("#### 임직원수와 복리후생")
    st.caption("💡 기관 규모(임직원수)가 복리후생비 총액·1인당 복리후생비와 각각 어떤 관계를 보이는지 확인합니다.")
    if "임직원수" in view.columns:
        emp_col = VARIABLES["임직원수"]["column"]
        wc1, wc2 = st.columns(2)
        with wc1:
            if total_col in view.columns:
                fig_e1 = plot_scatter(view, emp_col, total_col, x_key="임직원수", y_key="복리후생비")
                st.plotly_chart(fig_e1, use_container_width=True, key="p6_emp_total")
        with wc2:
            if percap_col in view.columns:
                fig_e2 = plot_scatter(view, emp_col, percap_col, x_key="임직원수", y_key="1인당복리후생비")
                st.plotly_chart(fig_e2, use_container_width=True, key="p6_emp_percap")

    st.markdown("#### 보수와 복리후생의 관계")
    st.caption("💡 직원 평균보수가 높은 기관은 1인당 복리후생비도 함께 높은지 확인합니다.")
    if "직원평균보수" in view.columns and percap_col in view.columns:
        pay_col = VARIABLES["직원평균보수"]["column"]
        sub_pw = view[[pay_col, percap_col]].dropna()
        fig_pw = plot_scatter(view, pay_col, percap_col, x_key="직원평균보수", y_key="1인당복리후생비")
        st.plotly_chart(fig_pw, use_container_width=True, key="p6_pay_welfare")
        if sub_pw.shape[0] > 2:
            r, p = stats.pearsonr(sub_pw[pay_col], sub_pw[percap_col])
            st.caption(f"Pearson r = {r:.3f} (N = {sub_pw.shape[0]:,})")

st.divider()

# ---------------- 이어보기 ----------------
st.markdown("### ➡️ 이어보기")
st.markdown(
    "- 평균보수와 신규채용률은 어떤 관계인가? → **⑧ 두 변수 관계분석**\n"
    "- 평균근속연수를 통제하면 평균보수와 총수입의 관계는 달라지는가? → **⑧ 두 변수 관계분석**의 부분상관 기능"
)
