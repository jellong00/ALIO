# -*- coding: utf-8 -*-
import numpy as np
import streamlit as st
import pandas as pd

from utils.data import load_dataset
from utils.stats import descriptive_stats, stats_to_display_df, yearly_summary
from utils.charts import (
    plot_histogram, plot_boxplot, plot_group_boxplot, plot_rank_bar,
    plot_time_series, plot_donut,
)
from utils.constants import NOTE_BOXPLOT, NOTE_HISTOGRAM, NOTE_ZERO_VS_NA

st.set_page_config(page_title="법인세 현황", page_icon="🧾", layout="wide")
st.title("🧾 05. 법인세 현황")
st.caption("법인세 관련 변수를 먼저 간단히 훑어본 뒤, '결정세액'을 대표변수로 심화분석합니다. (단위: 천원)")

tax = load_dataset("tax")
if tax.empty:
    st.stop()

years = sorted(tax["연도"].unique(), reverse=True)
default_idx = years.index(2025) if 2025 in years else 0
year = st.selectbox("연도", years, index=default_idx, key="tax_year")

# ---------------------------------------------------------------------
# 13-1. 법인세 변수 한눈에 보기
# ---------------------------------------------------------------------
st.subheader("법인세 변수 한눈에 보기")
tax_year = tax[tax["연도"] == year]

rows = []
for item in tax["항목"].unique():
    sub = tax_year[tax_year["항목"] == item]["값"]
    st_ = descriptive_stats(sub)
    rows.append({
        "변수": item, "N": st_["n_valid"],
        "평균": round(st_["mean"], 1) if pd.notna(st_["mean"]) else None,
        "중앙값": round(st_["median"], 1) if pd.notna(st_["median"]) else None,
        "0인 기관 비율(%)": st_["zero_pct"],
        "최대값": st_["max"],
    })
st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------------------
# 13-2. 결정세액 집중 분석
# ---------------------------------------------------------------------
st.header("결정세액 집중 분석")

dec_tax = tax_year[tax_year["항목"] == "결정세액"][["기관명", "기관유형", "주무부처", "값"]].rename(columns={"값": "결정세액"})

# A. 요약통계
st.subheader("A. 요약통계")
stats = descriptive_stats(dec_tax["결정세액"])
st.dataframe(stats_to_display_df(stats), hide_index=True, use_container_width=True)
st.caption(NOTE_ZERO_VS_NA)

# B, C. 히스토그램 / 박스플롯
c1, c2 = st.columns(2)
with c1:
    st.subheader("B. Histogram")
    st.plotly_chart(plot_histogram(dec_tax["결정세액"], title=f"결정세액 분포 ({year}년)", unit="천원"), use_container_width=True)
    st.caption(NOTE_HISTOGRAM)
with c2:
    st.subheader("C. Boxplot")
    st.plotly_chart(plot_boxplot(dec_tax["결정세액"], title=f"결정세액 박스플롯 ({year}년)", unit="천원"), use_container_width=True)
    st.caption(NOTE_BOXPLOT)

# D. 0인 기관과 양수 기관
st.subheader("D. 0인 기관과 양수 기관")
zero_n = (dec_tax["결정세액"] == 0).sum()
pos_n = (dec_tax["결정세액"] > 0).sum()
valid_n = dec_tax["결정세액"].notna().sum()
d1, d2 = st.columns([1, 2])
with d1:
    st.metric("결정세액 = 0", f"{zero_n:,}개 ({zero_n/valid_n*100:.1f}%)" if valid_n else "-")
    st.metric("결정세액 > 0", f"{pos_n:,}개 ({pos_n/valid_n*100:.1f}%)" if valid_n else "-")
with d2:
    st.plotly_chart(plot_donut(["0인 기관", "양수 기관"], [zero_n, pos_n], title="결정세액 0/양수 기관 비율"), use_container_width=True)

# E. 양수 기관만 보기
st.subheader("E. 양수 기관만 보기")
positive_only = st.checkbox("결정세액이 0보다 큰 기관만 보기", key="tax_positive_only")
display_df = dec_tax[dec_tax["결정세액"] > 0] if positive_only else dec_tax

# F. 기관유형별 Boxplot
st.subheader("F. 기관유형별 Boxplot")
st.plotly_chart(plot_group_boxplot(display_df, "결정세액", "기관유형", title=f"기관유형별 결정세액 분포 ({year}년)", unit="천원"), use_container_width=True)
st.caption("※ 통계적 검정(t-test, ANOVA 등)은 자동으로 수행하지 않습니다.")

# G. 결정세액 상위 기관
st.subheader("G. 결정세액 상위 기관")
top_n = st.radio("상위 기관 수", [10, 20, 30], index=1, horizontal=True, key="tax_topn")
st.plotly_chart(plot_rank_bar(display_df, "기관명", "결정세액", top_n=top_n, title=f"결정세액 상위 {top_n}개 기관 ({year}년)", unit="천원"), use_container_width=True)

# H. 연도별 변화
st.subheader("H. 연도별 변화")
dec_tax_all = tax[tax["항목"] == "결정세액"][["기관명", "기관유형", "연도", "값"]].rename(columns={"값": "결정세액"})
agg_choice = st.radio("집계 방법", ["평균", "중앙값", "합계"], horizontal=True, key="tax_agg")
yearly = yearly_summary(dec_tax_all, "결정세액", agg=agg_choice)
st.plotly_chart(plot_time_series(yearly, "연도", agg_choice, title=f"결정세액 연도별 {agg_choice}", unit="천원"), use_container_width=True)

st.write("연도별 Boxplot")
fig_yearly_box = plot_group_boxplot(dec_tax_all, "결정세액", "연도", title="연도별 결정세액 분포", unit="천원")
st.plotly_chart(fig_yearly_box, use_container_width=True)

# I. 로그변환 비교
st.subheader("I. 로그변환 비교")
show_log = st.checkbox("log(1+x) 변환 분포 함께 보기", key="tax_log")
if show_log:
    log_series = np.log1p(dec_tax["결정세액"].clip(lower=0))
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_histogram(dec_tax["결정세액"], title="원자료 분포", unit="천원"), use_container_width=True)
    with c2:
        st.plotly_chart(plot_histogram(log_series, title="log(1+결정세액) 분포", unit="log scale"), use_container_width=True)
    st.caption(
        "왜도가 큰 금액 자료는 로그변환을 하면 분포가 더 대칭적으로 보이는 경우가 많습니다. "
        "이는 법인세율이나 조세효과를 의미하는 것이 아니라, 분포의 형태를 보여주기 위한 것입니다."
    )

st.info("※ '결정세액 / 과세표준'을 '실효세율' 또는 '실효세부담률'로 명명하여 계산하지 않습니다.")
