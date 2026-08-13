# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

from utils.data import load_dataset

st.set_page_config(page_title="데이터 개요", page_icon="🗂️", layout="wide")
st.title("🗂️ 01. 데이터 개요")
st.caption("이 대시보드에서 사용하는 각 데이터셋의 구조와 범위를 살펴봅니다.")

DATASET_INFO = [
    {
        "key": "finance", "name": "수입지출현황",
        "desc": "기관별 수입(정부지원수입, 사업수입 등)과 지출(인건비, 사업비 등) 항목별 금액(백만원).",
        "rep_var": "총수입, 총지출",
    },
    {
        "key": "tax", "name": "법인세정보",
        "desc": "기관별 법인세 과세표준, 산출세액, 세액공제, 가산세, 결정세액(천원).",
        "rep_var": "결정세액",
    },
    {
        "key": "employees", "name": "임직원수현황",
        "desc": "임원·정규직·비정규직 인원 및 정원/현원 현황(명).",
        "rep_var": "임직원 총계(A+B+C)",
    },
    {
        "key": "compensation", "name": "직원평균보수현황",
        "desc": "정규직 기본급, 수당, 성과상여금 등 보수 구성요소와 1인당 평균보수(천원).",
        "rep_var": "1인당 평균보수액",
    },
    {
        "key": "executive_pay", "name": "임원연봉",
        "desc": "기관장/이사/감사 등 임원 직위별 보수 구성요소(천원).",
        "rep_var": "기관장 연간보수(합계)",
    },
    {
        "key": "recruitment", "name": "신규채용현황",
        "desc": "일반정규직, 청년, 여성, 장애인 등 유형별 신규채용 인원(명).",
        "rep_var": "일반정규직총신규채용",
    },
    {
        "key": "welfare", "name": "복리후생비",
        "desc": "임원·정규직·비정규직 대상 급여성/비급여성 복리후생비 항목(천원).",
        "rep_var": "총계(A+B)",
    },
    {
        "key": "business_expense", "name": "기관장업무추진비",
        "desc": "기관장 업무추진비 집행금액(천원).",
        "rep_var": "업무추진비 집행금액",
    },
    {
        "key": "other_welfare", "name": "그밖의 복리후생제도(휴직급여)",
        "desc": "정규직/비정규직/임원의 휴직 유형별 급여 지급현황(천원). 데이터 품질을 고려해 제한적으로 사용.",
        "rep_var": "기관 고유지급금액",
    },
]

for info in DATASET_INFO:
    df = load_dataset(info["key"])
    if df.empty:
        continue

    with st.container(border=True):
        c1, c2 = st.columns([2, 3])
        with c1:
            st.subheader(info["name"])
            st.write(info["desc"])
            st.markdown(f"**대표변수:** {info['rep_var']}")
        with c2:
            n_inst = df["기관명"].nunique() if "기관명" in df.columns else "-"
            year_min = int(df["연도"].min()) if "연도" in df.columns else "-"
            year_max = int(df["연도"].max()) if "연도" in df.columns else "-"
            n_vars = df["항목"].nunique() if "항목" in df.columns else "-"

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("기관 수", f"{n_inst:,}" if isinstance(n_inst, int) else n_inst)
            m2.metric("기간", f"{year_min}–{year_max}")
            m3.metric("변수 수", n_vars)

            if "값" in df.columns:
                missing_pct = round(df["값"].isna().mean() * 100, 1)
                zero_pct = round((df["값"] == 0).mean() * 100, 1)
                m4.metric("결측률", f"{missing_pct}%")
                st.caption(f"0 비율: {zero_pct}%")

st.divider()
st.subheader("기관 패널 데이터 (institution_panel)")
panel = load_dataset("panel")
if not panel.empty:
    st.write(
        f"모든 데이터셋을 기관-연도 단위로 병합한 패널 데이터입니다. "
        f"총 {panel['기관명'].nunique():,}개 기관, {int(panel['연도'].min())}–{int(panel['연도'].max())}년, "
        f"{panel.shape[1]}개 변수로 구성되어 있습니다."
    )
    st.dataframe(panel.head(20), use_container_width=True)
