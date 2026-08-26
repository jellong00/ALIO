"""
data_loader.py
--------------
공공기관 경영정보 Excel 원자료를 읽어서
기관-연도(institution-year) 패널로 결합하는 모듈.

원칙
----
1. 원본 Excel 파일은 절대 수정하지 않는다 (읽기 전용으로만 사용).
2. 결측값을 임의로 0으로 채우지 않는다.
3. merge는 무조건 inner join하지 않고, 기관-연도 master frame을 만든 뒤
   left join으로 다른 변수를 붙인다.
4. 모든 로더 함수는 @st.cache_data로 캐싱하여 페이지 이동 시
   Excel을 다시 읽지 않도록 한다.
"""

import os
import pandas as pd
import numpy as np
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")

YEARS = [2021, 2022, 2023, 2024, 2025]  # 전 파일 공통 연도 (법인세/복리후생비 등은 2026년 자료가 없음)
YEAR_COLS_5 = [f"{y}년" for y in YEARS]


def _path(fname):
    return os.path.join(DATA_DIR, fname)


def _melt_years(df, id_vars, year_cols=None):
    """연도별 wide 컬럼(2021년~)을 long 포맷으로 변환한다."""
    if year_cols is None:
        year_cols = [c for c in df.columns if c.endswith("년") and c[:-1].isdigit()]
    long_df = df.melt(id_vars=id_vars, value_vars=year_cols, var_name="연도", value_name="값")
    long_df["연도"] = long_df["연도"].str.replace("년", "", regex=False).astype(int)
    long_df["값"] = pd.to_numeric(long_df["값"], errors="coerce")
    return long_df


@st.cache_data(show_spinner=False)
def load_sheet(fname, sheet_name):
    """Excel 파일의 특정 시트를 header=1(두 번째 행)로 읽는다.
    (첫 번째 행은 단위 표기용 행이므로 건너뛴다.)"""
    df = pd.read_excel(_path(fname), sheet_name=sheet_name, header=1)
    df.columns = [str(c).strip() for c in df.columns]
    # 기관명/기관유형/주무부처 공백 정리
    for c in ["기관명", "기관유형", "주무부처", "구분", "항목"]:
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    if "상위기관" in df.columns:
        df = df.drop(columns=["상위기관"])
    return df


# ------------------------------------------------------------------
# 1) 임직원 수 현황  → 기관특성 영역의 근간(기관 마스터 테이블)
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_headcount():
    df = load_sheet("임직원수현황.xlsx", "1. 임직원 수")
    id_vars = ["기관명", "기관유형", "주무부처", "항목"]
    year_cols = [c for c in df.columns if c.endswith("년")]
    long_df = _melt_years(df, id_vars, year_cols)
    long_df = long_df[long_df["연도"].isin(YEARS)]

    wanted = {
        "임직원 총계(A+B+C)": "임직원수",
        "여성 현원-합계": "여성현원",
        "정규직-일반정규직-현원-계": "정규직현원",
        "임원-상임임원정원(A)": "상임임원정원",
    }
    sub = long_df[long_df["항목"].isin(wanted.keys())].copy()
    sub["항목"] = sub["항목"].map(wanted)
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="항목", values="값", aggfunc="sum").reset_index()
    return wide


@st.cache_data(show_spinner=False)
def load_institution_master():
    """기관명-기관유형-주무부처-연도 마스터 테이블 (임직원수 파일 기준)."""
    hc = load_headcount()
    master = hc[["기관명", "기관유형", "주무부처", "연도"]].drop_duplicates()
    return master


# ------------------------------------------------------------------
# 2) 신규채용 현황
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_new_hire():
    df = load_sheet("신규채용현황.xlsx", "1. 신규채용현황")
    id_vars = ["기관명", "기관유형", "주무부처", "항목"]
    long_df = _melt_years(df, id_vars)
    long_df = long_df[long_df["연도"].isin(YEARS)]

    wanted = {
        "일반정규직총신규채용": "신규채용자수",
        "여성": "여성신규채용자수",
        "청년": "청년신규채용자수",
        "장애인": "장애인신규채용자수",
        "정규직(무기계약직)신규채용": "무기계약직신규채용자수",
    }
    sub = long_df[long_df["항목"].isin(wanted.keys())].copy()
    sub["항목"] = sub["항목"].map(wanted)
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="항목", values="값", aggfunc="sum").reset_index()
    return wide


# ------------------------------------------------------------------
# 3) 직원 평균보수 / 신입사원 초임
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_salary():
    df = load_sheet("직원평균보수현황.xlsx", "1. 직원평균보수")
    id_vars = ["기관명", "기관유형", "주무부처", "구분", "항목"]
    long_df = _melt_years(df, id_vars)
    long_df = long_df[long_df["연도"].isin(YEARS)]
    long_df = long_df[long_df["구분"] == "정규직(일반정규직)"]

    wanted = {
        "1인당 평균보수액": "직원평균보수",
        "기본급": "기본급",
        "고정수당": "고정수당",
        "실적수당": "실적수당",
        "성과상여금": "성과상여금",
        "(경영평가 성과급)": "경영평가성과급",
        "평균근속연수(개월)": "평균근속연수_개월",
        "상시 종업원수": "상시종업원수",
    }
    sub = long_df[long_df["항목"].isin(wanted.keys())].copy()
    sub["항목"] = sub["항목"].map(wanted)
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="항목", values="값", aggfunc="sum").reset_index()
    if "평균근속연수_개월" in wide.columns:
        wide["평균근속연수"] = wide["평균근속연수_개월"] / 12.0
    return wide


@st.cache_data(show_spinner=False)
def load_starting_salary():
    df = load_sheet("직원평균보수현황.xlsx", "2. 신입사원초임")
    id_vars = ["기관명", "기관유형", "주무부처", "항목"]
    long_df = _melt_years(df, id_vars)
    long_df = long_df[long_df["연도"].isin(YEARS)]
    sub = long_df[long_df["항목"] == "합계"].copy()
    sub["항목"] = "신입사원초임"
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="항목", values="값", aggfunc="sum").reset_index()
    return wide


# ------------------------------------------------------------------
# 4) 임원연봉
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_executive_salary():
    df = load_sheet("임원연봉.xlsx", "임원연봉")
    id_vars = ["기관명", "기관유형", "주무부처", "구분", "항목"]
    long_df = _melt_years(df, id_vars)
    long_df = long_df[long_df["연도"].isin(YEARS)]

    ceo = long_df[(long_df["구분"] == "상임기관장") & (long_df["항목"] == "합계")].copy()
    ceo = ceo.rename(columns={"값": "기관장연봉"})[["기관명", "기관유형", "주무부처", "연도", "기관장연봉"]]

    exe = long_df[(long_df["구분"] == "상임임원 평균보수(연봉)") & (long_df["항목"] == "상임임원평균연봉")].copy()
    exe = exe.rename(columns={"값": "임원평균연봉"})[["기관명", "기관유형", "주무부처", "연도", "임원평균연봉"]]

    wide = pd.merge(ceo, exe, on=["기관명", "기관유형", "주무부처", "연도"], how="outer")
    return wide


# ------------------------------------------------------------------
# 5) 복리후생비
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_welfare_cost():
    df = load_sheet("복리후생비.xlsx", "1. 예산상 복리후생비")
    id_vars = ["기관명", "기관유형", "주무부처", "구분", "항목"]
    long_df = _melt_years(df, id_vars, [c for c in df.columns if c.endswith("년")])
    long_df = long_df[long_df["연도"].isin(YEARS)]

    total = long_df[long_df["항목"].str.strip() == "총계(A+B)"].copy()
    if total.empty:
        total = long_df[long_df["항목"].str.contains("총계", na=False)].copy()
    grp = total.groupby(["기관명", "기관유형", "주무부처", "연도"], as_index=False)["값"].sum()
    grp = grp.rename(columns={"값": "복리후생비"})
    return grp


# ------------------------------------------------------------------
# 6) 기관장업무추진비
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_ceo_expense():
    df = load_sheet("기관장업무추진비.xlsx", "기관장업무추진비")
    id_vars = ["기관명", "기관유형", "주무부처", "항목"]
    long_df = _melt_years(df, id_vars, [c for c in df.columns if c.endswith("년")])
    long_df = long_df[long_df["연도"].isin(YEARS)]
    sub = long_df[long_df["항목"] == "업무추진비 집행금액"].copy()
    sub = sub.rename(columns={"값": "기관장업무추진비"})[["기관명", "기관유형", "주무부처", "연도", "기관장업무추진비"]]
    return sub


# ------------------------------------------------------------------
# 7) 수입지출현황 (고유사업 + 기금계정 합산)
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_finance():
    df1 = load_sheet("수입지출현황.xlsx", "수입지출현황(고유사업)")
    df1["재원"] = "고유사업"
    df2 = load_sheet("수입지출현황.xlsx", "수입지출현황(기금계정)")
    df2["재원"] = "기금계정"
    if "기금명" in df2.columns:
        df2 = df2.drop(columns=["기금명"])

    id_vars = ["기관명", "기관유형", "주무부처", "항목", "재원"]
    year_cols = [c for c in df1.columns if c.endswith("년")]
    long1 = _melt_years(df1, id_vars, year_cols)
    long2 = _melt_years(df2, id_vars, [c for c in df2.columns if c.endswith("년")])
    long_df = pd.concat([long1, long2], ignore_index=True)
    long_df = long_df[long_df["연도"].isin(YEARS)]

    wanted = {
        "수입 > 수입합계": "총수입",
        "지출 > 지출합계": "총지출",
        "수입 > 정부지원수입 > 소계": "정부지원수입",
        "수입 > 기타사업수입": "사업수입",
        "지출 > 인건비": "인건비지출",
        "지출 > 사업비": "사업비지출",
    }
    sub = long_df[long_df["항목"].isin(wanted.keys())].copy()
    sub["항목"] = sub["항목"].map(wanted)
    # 고유사업 + 기금계정 합산 (기관 전체 재정규모)
    grp = sub.groupby(["기관명", "기관유형", "주무부처", "연도", "항목"], as_index=False)["값"].sum()
    wide = grp.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="항목", values="값", aggfunc="sum").reset_index()
    return wide


# ------------------------------------------------------------------
# 8) 법인세정보
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_corporate_tax():
    df = load_sheet("법인세정보.xlsx", "법인세")
    id_vars = ["기관명", "기관유형", "주무부처", "항목"]
    year_cols = [c for c in df.columns if c.endswith("년")]
    long_df = _melt_years(df, id_vars, year_cols)
    long_df = long_df[long_df["연도"].isin(YEARS)]

    wanted = {
        "과세표준": "과세표준",
        "법인세 산출세액": "법인세산출세액",
        "세액공제": "세액공제",
        "가산세": "가산세",
        "결정세액": "법인세결정세액",
    }
    sub = long_df[long_df["항목"].isin(wanted.keys())].copy()
    sub["항목"] = sub["항목"].map(wanted)
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="항목", values="값", aggfunc="sum").reset_index()
    return wide


# ------------------------------------------------------------------
# 9) 일·가정 양립 지표
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_parental_leave():
    df = load_sheet("일가정_양립_지원제도_운영현황.xlsx", "1. 일가정-육아휴직사용자수")
    id_vars = ["기관명", "기관유형", "주무부처", "구분"]
    long_df = _melt_years(df, id_vars, [c for c in df.columns if c.endswith("년")])
    long_df = long_df[long_df["연도"].isin(YEARS)]

    wanted = {
        "남성 사용자 수": "남성육아휴직사용자수",
        "남성 육아휴직 사용률": "남성육아휴직사용률",
        "여성 사용자 수": "여성육아휴직사용자수",
        "여성 육아휴직 사용률": "여성육아휴직사용률",
        "전체 사용자 수": "육아휴직사용자수_전체",
    }
    long_df["구분"] = long_df["구분"].str.strip()
    sub = long_df[long_df["구분"].isin(wanted.keys())].copy()
    sub["구분"] = sub["구분"].map(wanted)
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="구분", values="값", aggfunc="sum").reset_index()
    return wide


@st.cache_data(show_spinner=False)
def load_maternity_leave():
    df = load_sheet("일가정_양립_지원제도_운영현황.xlsx", "2. 일가정-출산휴가사용자수")
    id_vars = ["기관명", "기관유형", "주무부처", "구분"]
    long_df = _melt_years(df, id_vars, [c for c in df.columns if c.endswith("년")])
    long_df = long_df[long_df["연도"].isin(YEARS)]
    wanted = {
        "출산휴가 사용자 수": "출산휴가사용자수",
        "배우자 출산휴가 사용자 수": "배우자출산휴가사용자수",
        "배우자 출산휴가 법정일수 사용률": "배우자출산휴가법정일수사용률",
    }
    long_df["구분"] = long_df["구분"].str.strip()
    sub = long_df[long_df["구분"].isin(wanted.keys())].copy()
    sub["구분"] = sub["구분"].map(wanted)
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="구분", values="값", aggfunc="sum").reset_index()
    return wide


@st.cache_data(show_spinner=False)
def load_shortened_work():
    df = load_sheet("일가정_양립_지원제도_운영현황.xlsx", "3. 일가정-임신기육아기단축근무제사용자수")
    id_vars = ["기관명", "기관유형", "주무부처", "구분"]
    long_df = _melt_years(df, id_vars, [c for c in df.columns if c.endswith("년")])
    long_df = long_df[long_df["연도"].isin(YEARS)]
    wanted = {
        "임신기 단축 근무제": "임신기단축근무",
        "육아기 단축 근무제": "육아기단축근무",
    }
    long_df["구분"] = long_df["구분"].str.strip()
    sub = long_df[long_df["구분"].isin(wanted.keys())].copy()
    sub["구분"] = sub["구분"].map(wanted)
    wide = sub.pivot_table(index=["기관명", "기관유형", "주무부처", "연도"],
                            columns="구분", values="값", aggfunc="sum").reset_index()
    return wide


@st.cache_data(show_spinner=False)
def load_family_care():
    leave = load_sheet("일가정_양립_지원제도_운영현황.xlsx", "5. 일가정-가족돌봄휴가사용자수")
    off = load_sheet("일가정_양립_지원제도_운영현황.xlsx", "6. 일가정-가족돌봄휴직사용자수")
    id_vars = ["기관명", "기관유형", "주무부처", "구분"]

    l1 = _melt_years(leave, id_vars, [c for c in leave.columns if c.endswith("년")])
    l1 = l1[(l1["연도"].isin(YEARS)) & (l1["구분"].str.strip() == "전체")]
    l1 = l1.groupby(["기관명", "기관유형", "주무부처", "연도"], as_index=False)["값"].sum()
    l1 = l1.rename(columns={"값": "가족돌봄휴가_전체"})

    l2 = _melt_years(off, id_vars, [c for c in off.columns if c.endswith("년")])
    l2 = l2[(l2["연도"].isin(YEARS)) & (l2["구분"].str.strip() == "전체")]
    l2 = l2.groupby(["기관명", "기관유형", "주무부처", "연도"], as_index=False)["값"].sum()
    l2 = l2.rename(columns={"값": "가족돌봄휴직_전체"})

    wide = pd.merge(l1, l2, on=["기관명", "기관유형", "주무부처", "연도"], how="outer")
    return wide


# ------------------------------------------------------------------
# 전체 패널 결합
# ------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def build_panel():
    """기관-연도 단위의 통합 패널 데이터를 생성한다.
    임직원수 파일을 마스터로 하여 나머지 지표를 left join으로 결합한다."""
    master = load_institution_master()

    pieces = [
        load_headcount(),
        load_new_hire(),
        load_salary(),
        load_starting_salary(),
        load_executive_salary(),
        load_welfare_cost(),
        load_ceo_expense(),
        load_finance(),
        load_corporate_tax(),
        load_parental_leave(),
        load_maternity_leave(),
        load_shortened_work(),
        load_family_care(),
    ]

    panel = master.copy()
    for piece in pieces:
        cols = [c for c in piece.columns if c not in ["기관명", "기관유형", "주무부처", "연도"]]
        panel = panel.merge(piece[["기관명", "연도"] + cols], on=["기관명", "연도"], how="left")

    return panel
