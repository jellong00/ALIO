# -*- coding: utf-8 -*-
"""pages/2_인력_채용.py"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years,
    render_common_filters, apply_common_filters,
    workforce_summary, recruitment_summary,
    format_number, format_percent, safe_divide,
    line_trend_chart, bar_ranking_chart, scatter_with_trend, grouped_bar_chart, render_or_empty, render_scatter_or_empty,
)

setup_page("인력·채용")
st.title("👥 인력·채용")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FSTATE = render_common_filters(YEARS, MASTER)
st.divider()

wf_all = workforce_summary(DATA["workforce"])
rec_all = recruitment_summary(DATA["recruitment"])

wf_y = apply_common_filters(wf_all, MASTER, FSTATE, apply_year=True)
rec_y = apply_common_filters(rec_all, MASTER, FSTATE, apply_year=True)
merged_y = wf_y.merge(rec_y, on=["institution_name_raw", "year"], how="outer")

if merged_y.empty:
    st.info("선택하신 조건에 해당하는 데이터가 없습니다.")
else:
    merged_y["new_hire_rate_pct"] = merged_y.apply(
        lambda r: safe_divide(r.get("total_new_hires"), r.get("total_workforce")) * 100
        if pd.notna(safe_divide(r.get("total_new_hires"), r.get("total_workforce"))) else np.nan, axis=1)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("임직원 현원", format_number(merged_y["total_workforce"].sum()))
    c2.metric("정원충족률", format_percent(safe_divide(merged_y["total_workforce"].sum(), merged_y["total_authorized"].sum()) * 100
                                          if merged_y["total_authorized"].sum() else np.nan))
    c3.metric("신규채용률", format_percent(safe_divide(merged_y["total_new_hires"].sum(), merged_y["total_workforce"].sum()) * 100
                                          if merged_y["total_workforce"].sum() else np.nan))
    c4.metric("여성인력 비율", format_percent(safe_divide(merged_y["female_workforce"].sum(), merged_y["total_workforce"].sum()) * 100
                                            if merged_y["total_workforce"].sum() else np.nan))
    c5.metric("청년채용 비율", format_percent(safe_divide(merged_y["youth_hires"].sum(), merged_y["total_new_hires"].sum()) * 100
                                            if merged_y["total_new_hires"].sum() else np.nan))
    c6.metric("장애인채용 비율", format_percent(safe_divide(merged_y["disabled_hires"].sum(), merged_y["total_new_hires"].sum()) * 100
                                             if merged_y["total_new_hires"].sum() else np.nan))
    st.caption("청년·여성·장애인 채용은 상호 중복 가능한 집단이므로 합산해 100%로 취급하지 않습니다.")

    col_a, col_b = st.columns(2)
    with col_a:
        wf_trend = apply_common_filters(wf_all, MASTER, FSTATE, apply_year=False)
        trend = wf_trend.groupby("year", as_index=False)["total_workforce"].sum()
        fig = line_trend_chart(trend.assign(구분="전체"), "year", "total_workforce", "구분",
                                "연도별 임직원 현원 추이", "임직원 수", "명")
        render_or_empty(fig)
    with col_b:
        rec_trend = apply_common_filters(rec_all, MASTER, FSTATE, apply_year=False)
        trend_r = rec_trend.groupby("year", as_index=False)[["youth_hires", "female_hires", "disabled_hires"]].sum()
        trend_r_long = trend_r.melt(id_vars="year", var_name="구분", value_name="인원")
        trend_r_long["구분"] = trend_r_long["구분"].map({
            "youth_hires": "청년", "female_hires": "여성", "disabled_hires": "장애인",
        })
        fig2 = grouped_bar_chart(trend_r_long, "year", "인원", "구분", "연도별 신규채용(청년/여성/장애인) 추이", "명")
        render_or_empty(fig2)

    col_c, col_d = st.columns(2)
    with col_c:
        rank_df = merged_y[["institution_name_raw", "new_hire_rate_pct"]].dropna()
        fig3 = bar_ranking_chart(rank_df, "institution_name_raw", "new_hire_rate_pct",
                                  "기관별 신규채용률 상위 10개", "%", top_n=10)
        render_or_empty(fig3)
    with col_d:
        scatter_df = merged_y[["institution_name_raw", "fill_rate_pct", "new_hire_rate_pct"]].dropna()
        fig4 = scatter_with_trend(scatter_df, "fill_rate_pct", "new_hire_rate_pct", "institution_name_raw",
                                   "현재 인력 규모에 비해 신규채용은 활발한가", "정원충족률(%)", "신규채용률(%)")
        render_scatter_or_empty(fig4)

    with st.expander("📥 데이터 다운로드 및 원자료 확인"):
        st.dataframe(merged_y, use_container_width=True)
        csv_bytes = merged_y.to_csv(index=False).encode("utf-8-sig")
        st.download_button("인력·채용 데이터 다운로드", data=csv_bytes,
                            file_name=f"workforce_{FSTATE.year}_filtered.csv", mime="text/csv")
