# -*- coding: utf-8 -*-
"""pages/6_수입_지출.py"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years, get_filter_options,
    render_common_filters, apply_common_filters,
    finance_summary, workforce_summary,
    format_number, format_percent, format_amount_krw_million, safe_divide,
    line_trend_chart, bar_ranking_chart, scatter_with_trend, render_or_empty,
)

setup_page("수입·지출")
st.title("💵 수입·지출")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FILTER_OPTIONS = get_filter_options(MASTER)
FSTATE = render_common_filters(YEARS, FILTER_OPTIONS)
st.divider()

fin_all = finance_summary(DATA["finance"])
fin_y = apply_common_filters(fin_all, MASTER, FSTATE, apply_year=True)
wf_y = apply_common_filters(workforce_summary(DATA["workforce"]), MASTER, FSTATE, apply_year=True)

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

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("총수입", format_amount_krw_million(fin_y["total_revenue"].sum()))
    c2.metric("사업수입", format_amount_krw_million(fin_y.get("business_revenue", pd.Series(dtype=float)).sum()))
    c3.metric("자체수입", format_amount_krw_million(fin_y.get(own_col, pd.Series(dtype=float)).sum()))
    c4.metric("총지출", format_amount_krw_million(fin_y["total_expense"].sum()))
    c5.metric("수지", format_amount_krw_million(fin_y["total_revenue"].sum() - fin_y["total_expense"].sum()))
    c6.metric("정부지원 의존도", format_percent(safe_divide(fin_y["gov_support_revenue"].sum(), fin_y["total_revenue"].sum()) * 100
                                             if fin_y["total_revenue"].sum() else np.nan))
    st.caption(f"자체수입 계산식: {own_revenue_def}. 자체수입은 공식 발표 변수가 아니라 분석자가 계산한 파생지표입니다.")
    st.caption("공공기관의 '총수입'은 정부지원수입 등을 포함하므로 일반 기업의 매출액과 동일한 개념이 아닙니다.")

    col_a, col_b = st.columns(2)
    with col_a:
        trend = apply_common_filters(fin_all, MASTER, FSTATE, apply_year=False)
        trend_agg = trend.groupby("year", as_index=False)[["total_revenue", "total_expense"]].sum()
        trend_long = trend_agg.melt(id_vars="year", var_name="구분", value_name="금액")
        trend_long["구분"] = trend_long["구분"].map({"total_revenue": "총수입", "total_expense": "총지출"})
        fig = line_trend_chart(trend_long, "year", "금액", "구분", "총수입·총지출 연도별 추이", "백만원", "백만원")
        render_or_empty(fig)
    with col_b:
        struct_cols = ["gov_support_revenue", "business_revenue", own_col]
        avail_struct = [c for c in struct_cols if c in fin_y.columns]
        if avail_struct:
            struct_long = fin_y[["institution_name_raw"] + avail_struct].melt(
                id_vars="institution_name_raw", var_name="구분", value_name="금액")
            struct_agg = struct_long.groupby("구분", as_index=False)["금액"].sum()
            fig2 = bar_ranking_chart(struct_agg, "구분", "금액", "수입구조 구성 (전체 합계)", "백만원", top_n=10)
        else:
            fig2 = None
        render_or_empty(fig2)

    col_c, col_d = st.columns(2)
    with col_c:
        rank_df = merged6[["institution_name_raw", "gov_dependency_pct"]].dropna()
        fig3 = bar_ranking_chart(rank_df, "institution_name_raw", "gov_dependency_pct",
                                  "정부지원 의존도 상위 10개 기관", "%", top_n=10)
        render_or_empty(fig3)
    with col_d:
        sc = merged6[["institution_name_raw", "business_revenue", "total_workforce"]].dropna() \
            if "business_revenue" in merged6.columns else pd.DataFrame()
        fig4 = scatter_with_trend(sc, "total_workforce", "business_revenue", "institution_name_raw",
                                   "임직원 수 vs 사업수입", "임직원 수(명)", "사업수입(백만원)", log_y=True)
        render_or_empty(fig4)

    csv_bytes = merged6.to_csv(index=False).encode("utf-8-sig")
    st.download_button("수입·지출 데이터 다운로드", data=csv_bytes,
                        file_name=f"finance_{FSTATE.year}_filtered.csv", mime="text/csv")
