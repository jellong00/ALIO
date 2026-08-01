# -*- coding: utf-8 -*-
"""pages/4_일가정_양립.py

핵심 질문: 일·가정 양립 제도는 실제로 얼마나 활용되는가?
(제도의 존재 여부가 아니라 '이용률'을 중심으로 본다)
"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years,
    render_common_filters, apply_common_filters,
    work_family_leave_summary, work_family_daycare_summary,
    work_family_flexwork_summary, work_family_care_summary, workforce_summary,
    format_number, format_percent, format_amount_krw_thousand, safe_divide,
    grouped_bar_chart, scatter_with_trend, bar_ranking_chart, box_plot_chart,
    line_trend_chart, render_or_empty, render_scatter_or_empty,
)

setup_page("일·가정 양립")
st.title("👨‍👩‍👧 일·가정 양립 제도, 실제로 얼마나 쓰이고 있는가")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FSTATE = render_common_filters(YEARS, MASTER)

with st.expander("이 탭에서 사용하는 자료 · 지표 정의"):
    st.caption(
        "자료: 일가정_양립_지원제도_운영현황.xlsx(육아휴직·유연근무·가족돌봄·직장어린이집 시트) "
        "+ 임직원수현황.xlsx(분모)\n\n"
        "· 육아휴직 이용률 = 육아휴직 사용자 수 / 임직원 현원 × 100\n"
        "· 유연근무 이용률 = 5개 유연근무 제도(시간선택제 채용·전환, 탄력근무제, 재량근무제, 원격근무제) "
        "이용 인원(제도별 '계' 항목만 사용해 중복합산 방지) / 임직원 현원 × 100\n"
        "· 가족돌봄 이용률 = 가족돌봄휴가+휴직 이용자 수 / 임직원 현원 × 100\n"
        "· 분모가 0이거나 결측이면 '자료 없음'으로 표시하며 0으로 대체하지 않습니다."
    )
st.divider()

wf_all = workforce_summary(DATA["workforce"])
leave_all = work_family_leave_summary(DATA["work_family"])
daycare_all = work_family_daycare_summary(DATA["work_family"])
flex_total_all, flex_detail_all = work_family_flexwork_summary(DATA["work_family"])
care_all = work_family_care_summary(DATA["work_family"])

wf_y = apply_common_filters(wf_all, MASTER, FSTATE, apply_year=True)
leave_y = apply_common_filters(leave_all, MASTER, FSTATE, apply_year=True)
daycare_y = apply_common_filters(daycare_all, MASTER, FSTATE, apply_year=True)
flex_y = apply_common_filters(flex_total_all, MASTER, FSTATE, apply_year=True)
care_y = apply_common_filters(care_all, MASTER, FSTATE, apply_year=True)

merged4 = wf_y[["institution_name_raw", "year", "total_workforce", "female_ratio_pct"]] \
    .merge(leave_y, on=["institution_name_raw", "year"], how="outer") \
    .merge(flex_y, on=["institution_name_raw", "year"], how="outer") \
    .merge(care_y, on=["institution_name_raw", "year"], how="outer") \
    .merge(daycare_y, on=["institution_name_raw", "year"], how="outer")

if merged4.empty or not merged4["total_workforce"].sum():
    st.info("선택하신 조건에 해당하는 데이터가 없습니다.")
else:
    merged4["leave_use_rate_pct"] = merged4.apply(
        lambda r: safe_divide(r.get("parental_leave_total"), r.get("total_workforce")) * 100
        if pd.notna(safe_divide(r.get("parental_leave_total"), r.get("total_workforce"))) else np.nan, axis=1)
    merged4["male_leave_ratio_pct"] = merged4.apply(
        lambda r: safe_divide(r.get("parental_leave_male"), r.get("parental_leave_total")) * 100
        if pd.notna(safe_divide(r.get("parental_leave_male"), r.get("parental_leave_total"))) else np.nan, axis=1)
    merged4["flexwork_rate_pct"] = merged4.apply(
        lambda r: safe_divide(r.get("flexwork_total_users"), r.get("total_workforce")) * 100
        if pd.notna(safe_divide(r.get("flexwork_total_users"), r.get("total_workforce"))) else np.nan, axis=1)
    merged4["care_rate_pct"] = merged4.apply(
        lambda r: safe_divide(r.get("family_care_total"), r.get("total_workforce")) * 100
        if pd.notna(safe_divide(r.get("family_care_total"), r.get("total_workforce"))) else np.nan, axis=1)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("육아휴직 이용률", format_percent(safe_divide(merged4["parental_leave_total"].sum(), merged4["total_workforce"].sum()) * 100
                                            if merged4["total_workforce"].sum() else np.nan))
    c2.metric("남성 육아휴직 비율", format_percent(safe_divide(merged4["parental_leave_male"].sum(), merged4["parental_leave_total"].sum()) * 100
                                               if merged4["parental_leave_total"].sum() else np.nan))
    c3.metric("유연근무 이용률", format_percent(safe_divide(merged4["flexwork_total_users"].sum(), merged4["total_workforce"].sum()) * 100
                                            if merged4["total_workforce"].sum() else np.nan))
    c4.metric("가족돌봄 이용률", format_percent(safe_divide(merged4["family_care_total"].sum(), merged4["total_workforce"].sum()) * 100
                                            if merged4["total_workforce"].sum() else np.nan))
    c5.metric("직장어린이집 수혜인원", format_number(merged4["daycare_beneficiaries"].sum()))
    c6.metric("어린이집 1인당 운영비", format_amount_krw_thousand(safe_divide(merged4["daycare_expense"].sum(), merged4["daycare_beneficiaries"].sum())))

    st.divider()
    sub_tabs = st.tabs(["육아휴직", "유연근무 · 가족돌봄", "직장어린이집"])

    with sub_tabs[0]:
        col_a, col_b = st.columns(2)
        with col_a:
            leave_trend = apply_common_filters(leave_all, MASTER, FSTATE, apply_year=False)
            trend = leave_trend.groupby("year", as_index=False)[["parental_leave_male", "parental_leave_female"]].sum()
            trend_long = trend.melt(id_vars="year", var_name="성별", value_name="이용자수")
            trend_long["성별"] = trend_long["성별"].map({"parental_leave_male": "남성", "parental_leave_female": "여성"})
            fig = grouped_bar_chart(trend_long, "year", "이용자수", "성별", "남녀 육아휴직 이용자는 최근 어떻게 변했는가", "명")
            render_or_empty(fig)
        with col_b:
            sc = merged4[["institution_name_raw", "female_ratio_pct", "leave_use_rate_pct"]].dropna()
            fig2 = scatter_with_trend(sc, "female_ratio_pct", "leave_use_rate_pct", "institution_name_raw",
                                       "여성인력이 많은 기관일수록 육아휴직을 더 쓰는가", "여성인력 비율(%)", "육아휴직 이용률(%)")
            render_scatter_or_empty(fig2)

        col_c, col_d = st.columns(2)
        with col_c:
            type_df = merged4.merge(MASTER[["institution_name", "institution_type"]],
                                     left_on="institution_name_raw", right_on="institution_name", how="left")
            fig3 = box_plot_chart(type_df, "institution_type", "leave_use_rate_pct",
                                   "기관유형에 따라 육아휴직 이용률 차이가 있는가", "육아휴직 이용률(%)")
            render_or_empty(fig3)
        with col_d:
            rank_df = merged4[["institution_name_raw", "male_leave_ratio_pct"]].dropna()
            fig4 = bar_ranking_chart(rank_df, "institution_name_raw", "male_leave_ratio_pct",
                                      "남성 육아휴직 비율이 가장 높은 기관은 어디인가", "%", top_n=10)
            render_or_empty(fig4)

    with sub_tabs[1]:
        col_a, col_b = st.columns(2)
        with col_a:
            flex_detail_y = apply_common_filters(flex_detail_all, MASTER, FSTATE, apply_year=True)
            flex_agg = flex_detail_y.groupby("flex_type", as_index=False)["value"].sum()
            fig5 = bar_ranking_chart(flex_agg, "flex_type", "value", "어떤 유연근무 제도가 가장 많이 쓰이는가", "명", top_n=10)
            render_or_empty(fig5)
        with col_b:
            care_trend = apply_common_filters(care_all, MASTER, FSTATE, apply_year=False)
            care_trend_agg = care_trend.groupby("year", as_index=False)[["family_care_male", "family_care_female"]].sum()
            care_trend_long = care_trend_agg.melt(id_vars="year", var_name="성별", value_name="이용자수")
            care_trend_long["성별"] = care_trend_long["성별"].map({"family_care_male": "남성", "family_care_female": "여성"})
            fig6 = grouped_bar_chart(care_trend_long, "year", "이용자수", "성별", "가족돌봄휴가·휴직은 늘고 있는가", "명")
            render_or_empty(fig6)

        col_c, col_d = st.columns(2)
        with col_c:
            rank_df = merged4[["institution_name_raw", "flexwork_rate_pct"]].dropna()
            fig7 = bar_ranking_chart(rank_df, "institution_name_raw", "flexwork_rate_pct",
                                      "유연근무 이용률이 가장 높은 기관은 어디인가", "%", top_n=10)
            render_or_empty(fig7)
        with col_d:
            rank_df2 = merged4[["institution_name_raw", "care_rate_pct"]].dropna()
            fig8 = bar_ranking_chart(rank_df2, "institution_name_raw", "care_rate_pct",
                                      "가족돌봄제도 이용률이 가장 높은 기관은 어디인가", "%", top_n=10)
            render_or_empty(fig8)

    with sub_tabs[2]:
        col_a, col_b = st.columns(2)
        with col_a:
            daycare_trend = apply_common_filters(daycare_all, MASTER, FSTATE, apply_year=False)
            trend_dc = daycare_trend.groupby("year", as_index=False)["daycare_beneficiaries"].sum()
            fig9 = line_trend_chart(trend_dc.assign(구분="전체"), "year", "daycare_beneficiaries", "구분",
                                     "직장어린이집 수혜인원은 늘고 있는가", "수혜인원", "명")
            render_or_empty(fig9)
        with col_b:
            rank_df3 = merged4[["institution_name_raw", "daycare_expense"]].dropna()
            fig10 = bar_ranking_chart(rank_df3, "institution_name_raw", "daycare_expense",
                                       "직장어린이집 운영비 지출이 큰 기관은 어디인가", "천원", top_n=10)
            render_or_empty(fig10)
        st.caption("직장어린이집을 운영하지 않는 기관은 원자료에 값이 없어 그래프에서 제외됩니다(0으로 대체하지 않음).")

    st.divider()
    with st.expander("📥 데이터 다운로드 및 원자료 확인"):
        st.dataframe(merged4, use_container_width=True)
        csv_bytes = merged4.to_csv(index=False).encode("utf-8-sig")
        st.download_button("일·가정 양립 데이터 다운로드", data=csv_bytes,
                            file_name=f"work_family_{FSTATE.year}_filtered.csv", mime="text/csv")
