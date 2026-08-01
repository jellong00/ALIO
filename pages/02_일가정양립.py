# -*- coding: utf-8 -*-
"""pages/4_일가정_양립.py"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years, get_filter_options,
    render_common_filters, apply_common_filters,
    work_family_leave_summary, work_family_daycare_summary, workforce_summary,
    format_number, format_percent, format_amount_krw_thousand, safe_divide,
    grouped_bar_chart, scatter_with_trend, bar_ranking_chart, render_or_empty,
)

setup_page("일·가정 양립")
st.title("👨‍👩‍👧 일·가정 양립")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FILTER_OPTIONS = get_filter_options(MASTER)
FSTATE = render_common_filters(YEARS, FILTER_OPTIONS)
st.divider()

leave_all = work_family_leave_summary(DATA["work_family"])
daycare_all = work_family_daycare_summary(DATA["work_family"])
wf_all = workforce_summary(DATA["workforce"])

leave_y = apply_common_filters(leave_all, MASTER, FSTATE, apply_year=True)
daycare_y = apply_common_filters(daycare_all, MASTER, FSTATE, apply_year=True)
wf_y = apply_common_filters(wf_all, MASTER, FSTATE, apply_year=True)

merged4 = leave_y.merge(wf_y[["institution_name_raw", "year", "total_workforce", "female_ratio_pct"]],
                         on=["institution_name_raw", "year"], how="outer") \
    .merge(daycare_y, on=["institution_name_raw", "year"], how="outer")

if merged4.empty:
    st.info("선택하신 조건에 해당하는 데이터가 없습니다.")
else:
    merged4["leave_use_rate_pct"] = merged4.apply(
        lambda r: safe_divide(r.get("parental_leave_total"), r.get("total_workforce")) * 100
        if pd.notna(safe_divide(r.get("parental_leave_total"), r.get("total_workforce"))) else np.nan, axis=1)
    merged4["male_leave_ratio_pct"] = merged4.apply(
        lambda r: safe_divide(r.get("parental_leave_male"), r.get("parental_leave_total")) * 100
        if pd.notna(safe_divide(r.get("parental_leave_male"), r.get("parental_leave_total"))) else np.nan, axis=1)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("육아휴직 이용률", format_percent(safe_divide(merged4["parental_leave_total"].sum(), merged4["total_workforce"].sum()) * 100
                                            if merged4["total_workforce"].sum() else np.nan))
    c2.metric("남성 육아휴직 비율", format_percent(safe_divide(merged4["parental_leave_male"].sum(), merged4["parental_leave_total"].sum()) * 100
                                               if merged4["parental_leave_total"].sum() else np.nan))
    c3.metric("유연근무", "하단 탭에서 상세 데이터 다운로드 참고")
    c4.metric("가족돌봄제도", "하단 탭에서 상세 데이터 다운로드 참고")
    c5.metric("직장어린이집 수혜인원", format_number(merged4["daycare_beneficiaries"].sum()))
    c6.metric("어린이집 1인당 운영비", format_amount_krw_thousand(safe_divide(merged4["daycare_expense"].sum(), merged4["daycare_beneficiaries"].sum())))

    col_a, col_b = st.columns(2)
    with col_a:
        leave_trend = apply_common_filters(leave_all, MASTER, FSTATE, apply_year=False)
        trend = leave_trend.groupby("year", as_index=False)[["parental_leave_male", "parental_leave_female"]].sum()
        trend_long = trend.melt(id_vars="year", var_name="성별", value_name="이용자수")
        trend_long["성별"] = trend_long["성별"].map({"parental_leave_male": "남성", "parental_leave_female": "여성"})
        fig = grouped_bar_chart(trend_long, "year", "이용자수", "성별", "남녀 육아휴직자 연도별 추이", "명")
        render_or_empty(fig)
    with col_b:
        sc = merged4[["institution_name_raw", "female_ratio_pct", "leave_use_rate_pct"]].dropna()
        fig2 = scatter_with_trend(sc, "female_ratio_pct", "leave_use_rate_pct", "institution_name_raw",
                                   "여성인력 비율 vs 육아휴직 이용률", "여성인력 비율(%)", "육아휴직 이용률(%)")
        render_or_empty(fig2)

    col_c, col_d = st.columns(2)
    with col_c:
        type_df = merged4.merge(MASTER[["institution_name", "institution_type"]],
                                 left_on="institution_name_raw", right_on="institution_name", how="left")
        by_type = type_df.groupby("institution_type", as_index=False)["leave_use_rate_pct"].mean().dropna()
        fig3 = bar_ranking_chart(by_type, "institution_type", "leave_use_rate_pct",
                                  "기관유형별 육아휴직 이용률", "%", top_n=15)
        render_or_empty(fig3)
    with col_d:
        rank_df = merged4[["institution_name_raw", "male_leave_ratio_pct"]].dropna()
        fig4 = bar_ranking_chart(rank_df, "institution_name_raw", "male_leave_ratio_pct",
                                  "남성 육아휴직 비율 상위 10개", "%", top_n=10)
        render_or_empty(fig4)

    csv_bytes = merged4.to_csv(index=False).encode("utf-8-sig")
    st.download_button("일·가정 양립 데이터 다운로드", data=csv_bytes,
                        file_name=f"work_family_{FSTATE.year}_filtered.csv", mime="text/csv")
