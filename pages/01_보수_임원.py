# -*- coding: utf-8 -*-
"""pages/3_보수_임원.py"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years,
    render_common_filters, apply_common_filters,
    employee_avg_pay_summary, starting_pay_summary, executive_pay_summary,
    executive_expense_summary, workforce_summary,
    format_number, format_percent, format_amount_krw_thousand, safe_divide,
    line_trend_chart, stacked_bar_chart, scatter_with_trend, bar_ranking_chart, render_or_empty, render_scatter_or_empty,
)

setup_page("보수·임원")
st.title("💰 보수·임원")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FSTATE = render_common_filters(YEARS, MASTER)
st.divider()


def weighted_or_simple_avg(pay_df: pd.DataFrame, weighted: bool = True):
    """직원 평균보수를 가중평균(기본) 또는 단순평균으로 계산한다."""
    sub = pay_df.dropna(subset=["employee_avg_pay"])
    if sub.empty:
        return np.nan, "계산 불가"
    if weighted and "avg_headcount_for_weighting" in sub.columns and sub["avg_headcount_for_weighting"].notna().any():
        w = sub["avg_headcount_for_weighting"].fillna(0)
        if w.sum() > 0:
            return float((sub["employee_avg_pay"] * w).sum() / w.sum()), "가중평균 (상시종업원수 기준)"
    return float(sub["employee_avg_pay"].mean()), "단순평균 (인원 가중치 없음)"


pay_all = employee_avg_pay_summary(DATA["employee_pay"])
start_all = starting_pay_summary(DATA["employee_pay"])
exec_pay_all = executive_pay_summary(DATA["executive_pay"], executive_type="상임기관장")
exec_exp_all = executive_expense_summary(DATA["executive_expense"])
wf_all = workforce_summary(DATA["workforce"])

pay_y = apply_common_filters(pay_all, MASTER, FSTATE, apply_year=True)
start_y = apply_common_filters(start_all, MASTER, FSTATE, apply_year=True)
exec_pay_y = apply_common_filters(exec_pay_all, MASTER, FSTATE, apply_year=True)
exec_exp_y = apply_common_filters(exec_exp_all, MASTER, FSTATE, apply_year=True)
wf_y = apply_common_filters(wf_all, MASTER, FSTATE, apply_year=True)

merged3 = pay_y.merge(start_y, on=["institution_name_raw", "year"], how="outer") \
    .merge(exec_pay_y, on=["institution_name_raw", "year"], how="outer") \
    .merge(exec_exp_y, on=["institution_name_raw", "year"], how="outer") \
    .merge(wf_y[["institution_name_raw", "year", "total_workforce"]], on=["institution_name_raw", "year"], how="outer")

if merged3.empty:
    st.info("선택하신 조건에 해당하는 데이터가 없습니다.")
else:
    merged3["pay_multiple"] = merged3.apply(
        lambda r: safe_divide(r.get("executive_total_pay"), r.get("employee_avg_pay"))
        if pd.notna(safe_divide(r.get("executive_total_pay"), r.get("employee_avg_pay"))) else np.nan, axis=1)
    merged3["expense_per_capita"] = merged3.apply(
        lambda r: safe_divide(r.get("executive_expense"), r.get("total_workforce"))
        if pd.notna(safe_divide(r.get("executive_expense"), r.get("total_workforce"))) else np.nan, axis=1)

    avg_pay_value, avg_pay_method = weighted_or_simple_avg(pay_y, weighted=True)

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("직원 평균보수", format_amount_krw_thousand(avg_pay_value))
    c2.metric("신입사원 초임", format_amount_krw_thousand(start_y["starting_pay"].mean() if not start_y.empty else np.nan))
    c3.metric("기관장 총연봉(평균)", format_amount_krw_thousand(exec_pay_y["executive_total_pay"].mean() if not exec_pay_y.empty else np.nan))
    c4.metric("기관장-직원 보수배율(평균)", format_number(merged3["pay_multiple"].mean(), 2) + " 배"
              if pd.notna(merged3["pay_multiple"].mean()) else "자료 없음")
    c5.metric("기관장 업무추진비(평균)", format_amount_krw_thousand(exec_exp_y["executive_expense"].mean() if not exec_exp_y.empty else np.nan))
    c6.metric("직원 1인당 업무추진비(평균)", format_number(merged3["expense_per_capita"].mean(), 1) + " 천원"
              if pd.notna(merged3["expense_per_capita"].mean()) else "자료 없음")
    st.caption(f"직원 평균보수 계산 방식: {avg_pay_method}")

    col_a, col_b = st.columns(2)
    with col_a:
        pay_trend = apply_common_filters(pay_all, MASTER, FSTATE, apply_year=False)
        trend = pay_trend.groupby("year", as_index=False)["employee_avg_pay"].mean()
        fig = line_trend_chart(trend.assign(구분="전체 평균"), "year", "employee_avg_pay", "구분",
                                "직원 평균보수 연도별 추이 (단순평균)", "평균보수(천원)", "천원")
        render_or_empty(fig)
    with col_b:
        comp_cols = ["기본급", "고정수당", "실적수당", "급여성 복리후생비", "성과상여금", "(경영평가 성과급)"]
        avail = [c for c in comp_cols if c in pay_y.columns]
        if avail:
            comp_long = pay_y[["institution_name_raw", "year"] + avail].melt(
                id_vars=["institution_name_raw", "year"], var_name="구성항목", value_name="금액")
            comp_agg = comp_long.groupby(["year", "구성항목"], as_index=False)["금액"].mean()
            fig2 = stacked_bar_chart(comp_agg, "year", "금액", "구성항목", "직원 평균보수 구성 (평균, 누적막대)", "천원")
        else:
            fig2 = None
        render_or_empty(fig2)

    col_c, col_d = st.columns(2)
    with col_c:
        sc1 = merged3[["institution_name_raw", "avg_tenure_months", "employee_avg_pay"]].dropna() \
            if "avg_tenure_months" in merged3.columns else pd.DataFrame()
        fig3 = scatter_with_trend(sc1, "avg_tenure_months", "employee_avg_pay", "institution_name_raw",
                                   "근속연수가 길수록 평균보수도 높은가", "평균근속연수(개월)", "평균보수(천원)")
        render_scatter_or_empty(fig3)
    with col_d:
        rank_df = merged3[["institution_name_raw", "pay_multiple"]].dropna().sort_values("pay_multiple", ascending=False)
        fig4 = bar_ranking_chart(rank_df, "institution_name_raw", "pay_multiple",
                                  "기관장-직원 보수배율 상위 10개", "배", top_n=10)
        render_or_empty(fig4)

    with st.expander("📥 데이터 다운로드 및 원자료 확인"):
        st.dataframe(merged3, use_container_width=True)
        csv_bytes = merged3.to_csv(index=False).encode("utf-8-sig")
        st.download_button("보수·임원 데이터 다운로드", data=csv_bytes,
                            file_name=f"pay_{FSTATE.year}_filtered.csv", mime="text/csv")
