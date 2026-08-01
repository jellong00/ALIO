# -*- coding: utf-8 -*-
"""pages/6_수입_지출.py

핵심 질문: 기관의 재정구조와 자체수입 능력은 어떠한가? 법인세는 재정성과와 어떤 관계가 있는가?
"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years,
    render_common_filters, apply_common_filters,
    finance_summary, workforce_summary, corporate_tax_summary,
    format_number, format_percent, format_amount_krw_million, format_amount_krw_thousand, safe_divide,
    line_trend_chart, bar_ranking_chart, scatter_with_trend, render_or_empty, render_scatter_or_empty,
)

setup_page("수입·지출")
st.title("💵 기관의 재정구조와 정부지원 의존도")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FSTATE = render_common_filters(YEARS, MASTER)

with st.expander("이 탭에서 사용하는 자료 · 지표 정의 · 주의사항"):
    st.caption(
        "자료: 수입지출현황.xlsx(고유사업+기금계정 합산), 법인세정보.xlsx\n\n"
        "· 공공기관의 '총수입'에는 정부지원수입·출자금·차입금 등이 포함될 수 있어 "
        "일반 기업의 매출액과 동일한 개념이 아닙니다. 원자료에 공식 매출액이 없으므로 이 용어는 쓰지 않습니다.\n"
        "· 정부지원 의존도 = 정부지원수입(소계) / 총수입 × 100\n"
        "· 자체수입은 원자료의 공식 변수가 아니라 분석자가 계산한 파생지표이며, 두 가지 정의 중 선택할 수 있습니다.\n"
        "· 금액 단위는 백만원입니다."
    )
st.divider()

fin_all = finance_summary(DATA["finance"])
fin_y = apply_common_filters(fin_all, MASTER, FSTATE, apply_year=True)
wf_y = apply_common_filters(workforce_summary(DATA["workforce"]), MASTER, FSTATE, apply_year=True)
tax_all = corporate_tax_summary(DATA["corporate_tax"])
tax_y = apply_common_filters(tax_all, MASTER, FSTATE, apply_year=True)

if fin_y.empty:
    st.info("선택하신 조건에 해당하는 데이터가 없습니다.")
else:
    own_revenue_def = st.selectbox(
        "자체수입 정의 선택",
        ["보수적 자체수입 (기타사업수입+부대수입+기타)", "광의 자체수입 (총수입-정부지원수입-출자금-차입금)"],
        key="own_revenue_def",
    )
    own_col = "own_revenue_conservative" if "보수적" in own_revenue_def else "own_revenue_broad"

    merged6 = fin_y.merge(wf_y[["institution_name_raw", "year", "total_workforce"]],
                           on=["institution_name_raw", "year"], how="left")
    merged6["gov_dependency_pct"] = merged6.apply(
        lambda r: safe_divide(r.get("gov_support_revenue"), r.get("total_revenue")) * 100
        if pd.notna(safe_divide(r.get("gov_support_revenue"), r.get("total_revenue"))) else np.nan, axis=1)
    merged6["revenue_per_capita"] = merged6.apply(
        lambda r: safe_divide(r.get("total_revenue"), r.get("total_workforce"))
        if pd.notna(safe_divide(r.get("total_revenue"), r.get("total_workforce"))) else np.nan, axis=1)
    merged6["labor_cost_ratio_pct"] = merged6.apply(
        lambda r: safe_divide(r.get("labor_cost"), r.get("total_expense")) * 100
        if pd.notna(safe_divide(r.get("labor_cost"), r.get("total_expense"))) else np.nan, axis=1)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("총수입", format_amount_krw_million(fin_y["total_revenue"].sum()))
    c2.metric("사업수입", format_amount_krw_million(fin_y.get("business_revenue", pd.Series(dtype=float)).sum()))
    c3.metric("자체수입", format_amount_krw_million(fin_y.get(own_col, pd.Series(dtype=float)).sum()))
    c4.metric("총지출", format_amount_krw_million(fin_y["total_expense"].sum()))
    c5.metric("수지", format_amount_krw_million(fin_y["total_revenue"].sum() - fin_y["total_expense"].sum()))
    c6.metric("정부지원 의존도", format_percent(safe_divide(fin_y["gov_support_revenue"].sum(), fin_y["total_revenue"].sum()) * 100
                                             if fin_y["total_revenue"].sum() else np.nan))
    st.caption(f"자체수입 계산식: {own_revenue_def}")

    st.divider()
    sub_tabs = st.tabs(["수입·지출 추이", "수입구조", "정부지원 의존도", "법인세"])

    with sub_tabs[0]:
        col_a, col_b = st.columns(2)
        with col_a:
            trend = apply_common_filters(fin_all, MASTER, FSTATE, apply_year=False)
            trend_agg = trend.groupby("year", as_index=False)[["total_revenue", "total_expense"]].sum()
            trend_long = trend_agg.melt(id_vars="year", var_name="구분", value_name="금액")
            trend_long["구분"] = trend_long["구분"].map({"total_revenue": "총수입", "total_expense": "총지출"})
            fig = line_trend_chart(trend_long, "year", "금액", "구분", "총수입과 총지출은 함께 늘어나고 있는가", "백만원", "백만원")
            render_or_empty(fig)
        with col_b:
            sc = merged6[["institution_name_raw", "total_workforce", "business_revenue"]].dropna() \
                if "business_revenue" in merged6.columns else pd.DataFrame()
            fig2 = scatter_with_trend(sc, "total_workforce", "business_revenue", "institution_name_raw",
                                       "인력이 많은 기관일수록 사업수입도 큰가", "임직원 수(명)", "사업수입(백만원)", log_y=True)
            render_scatter_or_empty(fig2)

        col_c, col_d = st.columns(2)
        with col_c:
            rank_df = merged6[["institution_name_raw", "revenue_per_capita"]].dropna()
            fig3 = bar_ranking_chart(rank_df, "institution_name_raw", "revenue_per_capita",
                                      "직원 1인당 총수입이 가장 큰 기관은 어디인가", "백만원", top_n=10)
            render_or_empty(fig3)
        with col_d:
            rank_df2 = merged6[["institution_name_raw", "labor_cost_ratio_pct"]].dropna()
            fig4 = bar_ranking_chart(rank_df2, "institution_name_raw", "labor_cost_ratio_pct",
                                      "총지출 중 인건비 비중이 가장 큰 기관은 어디인가", "%", top_n=10)
            render_or_empty(fig4)

    with sub_tabs[1]:
        col_a, col_b = st.columns(2)
        with col_a:
            struct_cols = ["gov_support_revenue", "business_revenue", own_col]
            avail_struct = [c for c in struct_cols if c in fin_y.columns]
            if avail_struct:
                struct_long = fin_y[["institution_name_raw"] + avail_struct].melt(
                    id_vars="institution_name_raw", var_name="구분", value_name="금액")
                struct_agg = struct_long.groupby("구분", as_index=False)["금액"].sum()
                struct_agg["구분"] = struct_agg["구분"].map({
                    "gov_support_revenue": "정부지원수입", "business_revenue": "사업수입",
                    "own_revenue_conservative": "자체수입(보수적)", "own_revenue_broad": "자체수입(광의)",
                })
                fig5 = bar_ranking_chart(struct_agg, "구분", "금액", "수입은 어떤 항목으로 구성되어 있는가", "백만원", top_n=10)
            else:
                fig5 = None
            render_or_empty(fig5)
        with col_b:
            sc2 = merged6[["institution_name_raw", "gov_dependency_pct"]].dropna()
            fig6 = bar_ranking_chart(sc2, "institution_name_raw", "gov_dependency_pct",
                                      "정부지원 의존도가 가장 낮은(자체수입 능력이 큰) 기관은 어디인가", "%", top_n=10)
            render_or_empty(fig6)
        st.caption("자체수입은 공식 발표 변수가 아니라 분석자가 계산한 파생지표입니다.")

    with sub_tabs[2]:
        col_a, col_b = st.columns(2)
        with col_a:
            rank_df3 = merged6[["institution_name_raw", "gov_dependency_pct"]].dropna()
            fig7 = bar_ranking_chart(rank_df3, "institution_name_raw", "gov_dependency_pct",
                                      "정부지원 의존도가 가장 높은 기관은 어디인가", "%", top_n=10)
            render_or_empty(fig7)
        with col_b:
            from common_data import employee_avg_pay_summary
            pay_all = employee_avg_pay_summary(DATA["employee_pay"])
            pay_y = apply_common_filters(pay_all, MASTER, FSTATE, apply_year=True)
            merged_pay = merged6.merge(pay_y[["institution_name_raw", "employee_avg_pay"]],
                                        on="institution_name_raw", how="left")
            sc3 = merged_pay[["institution_name_raw", "gov_dependency_pct", "employee_avg_pay"]].dropna()
            fig8 = scatter_with_trend(sc3, "gov_dependency_pct", "employee_avg_pay", "institution_name_raw",
                                       "정부지원 의존도가 높은 기관은 보수 수준도 다른가", "정부지원 의존도(%)", "직원 평균보수(천원)")
            render_scatter_or_empty(fig8)

    with sub_tabs[3]:
        if tax_y.empty or tax_y["tax_final"].dropna().empty:
            st.info("선택한 연도에 법인세 자료가 없습니다.")
        else:
            col_a, col_b = st.columns(2)
            with col_a:
                tax_trend = apply_common_filters(tax_all, MASTER, FSTATE, apply_year=False)
                trend_tax = tax_trend.groupby("year", as_index=False)["tax_final"].sum()
                fig9 = line_trend_chart(trend_tax.assign(구분="전체"), "year", "tax_final", "구분",
                                         "법인세 결정세액은 연도별로 어떻게 변했는가", "결정세액(천원)", "천원")
                render_or_empty(fig9)
            with col_b:
                rank_df4 = tax_y[["institution_name_raw", "tax_final"]].dropna()
                fig10 = bar_ranking_chart(rank_df4, "institution_name_raw", "tax_final",
                                          "법인세 결정세액이 가장 큰 기관은 어디인가", "천원", top_n=10)
                render_or_empty(fig10)

            merged_tax = tax_y.merge(fin_y[["institution_name_raw", "total_revenue"]], on="institution_name_raw", how="left")
            merged_tax["tax_burden_pct"] = merged_tax.apply(
                lambda r: safe_divide(r.get("tax_final"), r.get("total_revenue")) * 100
                if pd.notna(safe_divide(r.get("tax_final"), r.get("total_revenue"))) else np.nan, axis=1)
            rank_df5 = merged_tax[["institution_name_raw", "tax_burden_pct"]].dropna()
            fig11 = bar_ranking_chart(rank_df5, "institution_name_raw", "tax_burden_pct",
                                      "총수입 대비 법인세 부담이 가장 큰 기관은 어디인가", "%", top_n=10)
            render_or_empty(fig11)
            st.caption(
                "과세표준·세액 항목의 산정 기준이 기관별로 동일하게 적용되는지는 원자료만으로 확인할 수 없어, "
                "결정세액과 총수입 대비 비중만 참고용으로 제시합니다."
            )

    st.divider()
    with st.expander("📥 데이터 다운로드 및 원자료 확인"):
        st.dataframe(merged6, use_container_width=True)
        csv_bytes = merged6.to_csv(index=False).encode("utf-8-sig")
        st.download_button("수입·지출 데이터 다운로드", data=csv_bytes,
                            file_name=f"finance_{FSTATE.year}_filtered.csv", mime="text/csv")
