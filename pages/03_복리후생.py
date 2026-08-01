# -*- coding: utf-8 -*-
"""pages/5_복리후생.py"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years,
    render_common_filters, apply_common_filters, FilterState,
    welfare_total_summary, welfare_category_breakdown, workforce_summary, employee_avg_pay_summary,
    format_number, format_percent, format_amount_krw_thousand, safe_divide,
    line_trend_chart, bar_ranking_chart, box_plot_chart, scatter_with_trend, render_or_empty, render_scatter_or_empty,
)

setup_page("복리후생")
st.title("🎁 복리후생")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FSTATE = render_common_filters(YEARS, MASTER)
st.divider()

welfare_total_all = welfare_total_summary(DATA["welfare"])
welfare_cat_all = welfare_category_breakdown(DATA["welfare"])
wf_all = workforce_summary(DATA["workforce"])
pay_all = employee_avg_pay_summary(DATA["employee_pay"])

wt_y = apply_common_filters(welfare_total_all, MASTER, FSTATE, apply_year=True)
wc_y = apply_common_filters(welfare_cat_all, MASTER, FSTATE, apply_year=True)
wf_y = apply_common_filters(wf_all, MASTER, FSTATE, apply_year=True)
pay_y = apply_common_filters(pay_all, MASTER, FSTATE, apply_year=True)

merged5 = wt_y.merge(wf_y[["institution_name_raw", "year", "total_workforce"]],
                      on=["institution_name_raw", "year"], how="outer") \
    .merge(pay_y[["institution_name_raw", "year", "employee_avg_pay"]],
           on=["institution_name_raw", "year"], how="outer")

if merged5.empty:
    st.info("선택하신 조건에 해당하는 데이터가 없습니다.")
else:
    merged5["welfare_per_capita"] = merged5.apply(
        lambda r: safe_divide(r.get("total_welfare_expense"), r.get("total_workforce"))
        if pd.notna(safe_divide(r.get("total_welfare_expense"), r.get("total_workforce"))) else np.nan, axis=1)

    prev_year_df = apply_common_filters(
        welfare_total_all, MASTER,
        FilterState(year=FSTATE.year - 1, institution_types=FSTATE.institution_types,
                    ministries=FSTATE.ministries, institution_name=FSTATE.institution_name,
                    comparison_basis=FSTATE.comparison_basis),
        apply_year=True,
    )
    yoy = safe_divide(
        wt_y["total_welfare_expense"].sum() - prev_year_df["total_welfare_expense"].sum(),
        prev_year_df["total_welfare_expense"].sum(),
    ) * 100 if prev_year_df["total_welfare_expense"].sum() else np.nan

    selective_welfare = wc_y[wc_y["welfare_category"] == "선택·문화지원"]["value"].sum()
    family_life_support = wc_y[wc_y["welfare_category"] == "생활지원"]["value"].sum()
    health_support = wc_y[wc_y["welfare_category"] == "건강지원"]["value"].sum()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("총복리후생비", format_amount_krw_thousand(wt_y["total_welfare_expense"].sum()))
    c2.metric("직원 1인당 복리후생비", format_amount_krw_thousand(safe_divide(wt_y["total_welfare_expense"].sum(), wf_y["total_workforce"].sum())))
    c3.metric("전년 대비 증감률", format_percent(yoy))
    c4.metric("선택적 복지비(세부항목 합)", format_amount_krw_thousand(selective_welfare))
    c5.metric("생활지원(세부항목 합)", format_amount_krw_thousand(family_life_support))
    c6.metric("건강지원(세부항목 합)", format_amount_krw_thousand(health_support))
    st.caption("총복리후생비(예산상 복리후생비 시트)와 항목별 세부내역(3-1~3-13 시트)은 서로 다른 산출 기준이므로 이중 합산하지 않습니다.")

    col_a, col_b = st.columns(2)
    with col_a:
        trend = apply_common_filters(welfare_total_all, MASTER, FSTATE, apply_year=False)
        trend_agg = trend.groupby("year", as_index=False)["total_welfare_expense"].sum()
        fig = line_trend_chart(trend_agg.assign(구분="전체"), "year", "total_welfare_expense", "구분",
                                "복리후생비 연도별 추이", "복리후생비(천원)", "천원")
        render_or_empty(fig)
    with col_b:
        cat_agg = wc_y.groupby("welfare_category", as_index=False)["value"].sum()
        fig2 = bar_ranking_chart(cat_agg, "welfare_category", "value", "복리후생 항목 구성(카테고리별 합계)", "천원", top_n=10)
        render_or_empty(fig2)

    col_c, col_d = st.columns(2)
    with col_c:
        box_df = merged5.merge(MASTER[["institution_name", "institution_type"]],
                                left_on="institution_name_raw", right_on="institution_name", how="left")
        fig3 = box_plot_chart(box_df, "institution_type", "welfare_per_capita",
                               "기관유형별 1인당 복리후생비 분포", "1인당 복리후생비(천원)")
        render_or_empty(fig3)
    with col_d:
        sc = merged5[["institution_name_raw", "employee_avg_pay", "welfare_per_capita"]].dropna()
        fig4 = scatter_with_trend(sc, "employee_avg_pay", "welfare_per_capita", "institution_name_raw",
                                   "보수가 높은 기관이 복리후생도 후한가", "평균보수(천원)", "1인당 복리후생비(천원)")
        render_scatter_or_empty(fig4)

    rank_df = merged5[["institution_name_raw", "welfare_per_capita"]].dropna()
    fig5 = bar_ranking_chart(rank_df, "institution_name_raw", "welfare_per_capita",
                              "1인당 복리후생비 상위 10개 기관", "천원", top_n=10)
    render_or_empty(fig5)

    with st.expander("📥 데이터 다운로드 및 원자료 확인"):
        st.dataframe(merged5, use_container_width=True)
        csv_bytes = merged5.to_csv(index=False).encode("utf-8-sig")
        st.download_button("복리후생 데이터 다운로드", data=csv_bytes,
                            file_name=f"welfare_{FSTATE.year}_filtered.csv", mime="text/csv")
