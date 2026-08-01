# -*- coding: utf-8 -*-
"""pages/7_기관_상세.py"""

import numpy as np
import pandas as pd
import streamlit as st

from common_data import (
    setup_page, load_data_or_stop, get_available_years, get_filter_options,
    render_common_filters, apply_common_filters,
    workforce_summary, recruitment_summary, employee_avg_pay_summary, starting_pay_summary,
    executive_pay_summary, welfare_total_summary, finance_summary, compute_comparison_index,
    format_number, format_percent, format_amount_krw_thousand, safe_divide,
    line_trend_chart, comparison_bullet_chart, render_or_empty,
)

setup_page("기관 상세")
st.title("🏢 기관 상세")

DATA = load_data_or_stop()
MASTER = DATA["institution_master"]
YEARS = get_available_years(DATA)
FILTER_OPTIONS = get_filter_options(MASTER)
FSTATE = render_common_filters(YEARS, FILTER_OPTIONS)
st.divider()

if FSTATE.institution_name == "전체":
    st.info("상단 공통 필터의 '기관명'에서 분석할 기관을 하나 선택해주세요.")
else:
    sel = FSTATE.institution_name
    wf_all = workforce_summary(DATA["workforce"])
    rec_all = recruitment_summary(DATA["recruitment"])
    pay_all = employee_avg_pay_summary(DATA["employee_pay"])
    exec_pay_all = executive_pay_summary(DATA["executive_pay"])
    welfare_total_all = welfare_total_summary(DATA["welfare"])
    fin_all = finance_summary(DATA["finance"])

    wf_y = apply_common_filters(wf_all, MASTER, FSTATE, apply_year=True, apply_institution=True)
    rec_y = apply_common_filters(rec_all, MASTER, FSTATE, apply_year=True, apply_institution=True)
    pay_y = apply_common_filters(pay_all, MASTER, FSTATE, apply_year=True, apply_institution=True)
    exec_pay_y = apply_common_filters(exec_pay_all, MASTER, FSTATE, apply_year=True, apply_institution=True)
    welfare_y = apply_common_filters(welfare_total_all, MASTER, FSTATE, apply_year=True, apply_institution=True)
    fin_y = apply_common_filters(fin_all, MASTER, FSTATE, apply_year=True, apply_institution=True)

    if wf_y.empty and fin_y.empty:
        st.info(f"선택하신 조건({sel} - {FSTATE.year}년)에 해당하는 데이터가 없습니다.")
    else:
        new_hire_rate = safe_divide(rec_y["total_new_hires"].sum(), wf_y["total_workforce"].sum()) * 100 \
            if wf_y["total_workforce"].sum() else np.nan
        welfare_per_capita = safe_divide(welfare_y["total_welfare_expense"].sum(), wf_y["total_workforce"].sum())
        gov_dep = safe_divide(fin_y["gov_support_revenue"].sum(), fin_y["total_revenue"].sum()) * 100 \
            if fin_y["total_revenue"].sum() else np.nan

        st.subheader(f"{sel} ({FSTATE.year}년 기준)")
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("임직원 수", format_number(wf_y["total_workforce"].sum()))
        c2.metric("신규채용률", format_percent(new_hire_rate))
        c3.metric("직원 평균보수", format_amount_krw_thousand(pay_y["employee_avg_pay"].sum()))
        c4.metric("기관장 연봉", format_amount_krw_thousand(exec_pay_y["executive_total_pay"].sum()))
        c5.metric("1인당 복리후생비", format_amount_krw_thousand(welfare_per_capita))
        c6.metric("정부지원 의존도", format_percent(gov_dep))

        col_a, col_b = st.columns(2)
        with col_a:
            wf_trend = wf_all[wf_all["institution_name_raw"] == sel]
            fig = line_trend_chart(wf_trend.assign(구분="임직원 수"), "year", "total_workforce", "구분",
                                    f"{sel} 임직원 수 추이", "임직원 수", "명")
            render_or_empty(fig)
        with col_b:
            fin_trend = fin_all[fin_all["institution_name_raw"] == sel]
            fin_trend_long = fin_trend.melt(id_vars=["institution_name_raw", "year"],
                                             value_vars=["total_revenue", "total_expense"],
                                             var_name="구분", value_name="금액")
            fin_trend_long["구분"] = fin_trend_long["구분"].map({"total_revenue": "총수입", "total_expense": "총지출"})
            fig2 = line_trend_chart(fin_trend_long, "year", "금액", "구분", f"{sel} 총수입·총지출 추이", "백만원", "백만원")
            render_or_empty(fig2)

        st.markdown("#### 비교집단 대비 지수 (비교집단 평균 = 100)")
        comparison_master = MASTER[MASTER["institution_name"] == sel]
        inst_type = comparison_master["institution_type"].iloc[0] if not comparison_master.empty else None
        ministry = comparison_master["ministry"].iloc[0] if not comparison_master.empty else None

        if FSTATE.comparison_basis == "동일 기관유형" and inst_type:
            peer_names = set(MASTER[MASTER["institution_type"] == inst_type]["institution_name"])
            comp_label = f"동일 기관유형({inst_type}) 평균"
        elif FSTATE.comparison_basis == "동일 주무부처" and ministry:
            peer_names = set(MASTER[MASTER["ministry"] == ministry]["institution_name"])
            comp_label = f"동일 주무부처({ministry}) 평균"
        else:
            peer_names = set(MASTER["institution_name"])
            comp_label = "전체 기관 평균"

        wf_peer = wf_all[(wf_all["year"] == FSTATE.year) & (wf_all["institution_name_raw"].isin(peer_names))]
        pay_peer = pay_all[(pay_all["year"] == FSTATE.year) & (pay_all["institution_name_raw"].isin(peer_names))]
        fin_peer = fin_all[(fin_all["year"] == FSTATE.year) & (fin_all["institution_name_raw"].isin(peer_names))]

        compare_items = {
            "임직원 수": (wf_y["total_workforce"].sum(), wf_peer["total_workforce"].mean()),
            "직원 평균보수": (pay_y["employee_avg_pay"].sum(), pay_peer["employee_avg_pay"].mean()),
            "총수입": (fin_y["total_revenue"].sum(), fin_peer["total_revenue"].mean()),
            "정부지원 의존도": (
                gov_dep,
                safe_divide(fin_peer["gov_support_revenue"].mean(), fin_peer["total_revenue"].mean()) * 100
                if fin_peer["total_revenue"].mean() else np.nan,
            ),
        }
        labels, indices = [], []
        for label, (val, peer_val) in compare_items.items():
            idx = compute_comparison_index(val, peer_val)
            labels.append(f"{label} (vs {comp_label})")
            indices.append(idx if pd.notna(idx) else None)

        fig3 = comparison_bullet_chart(labels, indices, f"{sel} 비교지수 (100 = {comp_label})", "지수")
        render_or_empty(fig3)

        csv_bytes = wf_y.to_csv(index=False).encode("utf-8-sig")
        st.download_button("기관 상세 데이터 다운로드", data=csv_bytes,
                            file_name=f"institution_detail_{sel}.csv", mime="text/csv")
