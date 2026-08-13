# -*- coding: utf-8 -*-
"""
데이터 로딩 모듈
================
원본 Excel(data/raw/*.xlsx)을 직접 읽어 정제한다. 별도의 전처리 스크립트나
parquet 캐시 파일 없이, Streamlit의 @st.cache_data로 세션 내에서만 캐싱한다.

원자료 시트는 2단 헤더 구조를 가진다.
    행0 : (거의 공백) "(단위: 백만원)" 같은 단위 표기
    행1 : 실제 컬럼명 (기관명, 기관유형, 주무부처, [구분], [항목], 2021년~2026년, 상위기관)
    행2~: 실제 데이터
"""

import os
import re

import numpy as np
import pandas as pd
import streamlit as st

from utils.constants import RAW_DIR

YEAR_RE = re.compile(r"^(20\d{2})년")

# key -> (파일명, 시트명, 연도 외 식별컬럼)
FILES = {
    "finance": ("수입지출현황.xlsx", "수입지출현황(고유사업)", ["항목"]),
    "tax": ("법인세정보.xlsx", "법인세", ["항목"]),
    "employees": ("임직원수현황.xlsx", "1. 임직원 수", ["항목"]),
    "compensation": ("직원평균보수현황.xlsx", "1. 직원평균보수", ["구분", "항목"]),
    "executive_pay": ("임원연봉.xlsx", "임원연봉", ["구분", "항목"]),
    "recruitment": ("신규채용현황.xlsx", "1. 신규채용현황", ["항목"]),
    "welfare": ("복리후생비.xlsx", "1. 예산상 복리후생비", ["구분", "항목"]),
    "business_expense": ("기관장업무추진비.xlsx", "기관장업무추진비", ["항목"]),
    "other_welfare": ("그밖의_복리후생제도_등의_운영현황.xlsx", "1-2. 휴직급여지급현황", ["구분", "항목"]),
}


def normalize_institution_name(name):
    """기관명 표기 차이(공백 등)를 정규화한다."""
    if pd.isna(name):
        return name
    return re.sub(r"\s+", "", str(name)).strip()


def _find_header_row(raw_df, key_col="기관명", search_rows=5):
    for i in range(min(search_rows, len(raw_df))):
        if key_col in raw_df.iloc[i].astype(str).tolist():
            return i
    raise ValueError(f"'{key_col}' 헤더 행을 찾을 수 없습니다.")


def _clean_sheet(raw_df):
    """header=None으로 읽은 raw DataFrame에서 실제 헤더를 찾아 정리한다."""
    hdr_idx = _find_header_row(raw_df)
    header = [c.strip() if isinstance(c, str) else c for c in raw_df.iloc[hdr_idx]]
    df = raw_df.iloc[hdr_idx + 1:].copy()
    df.columns = header
    df = df[df["기관명"].notna()].reset_index(drop=True)

    year_cols = {c for c in df.columns if isinstance(c, str) and YEAR_RE.match(c)}
    for col in df.columns:
        if col in year_cols:
            continue
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].apply(lambda v: v.strip() if isinstance(v, str) else v)
    return df


@st.cache_data(show_spinner="원자료를 읽는 중...")
def _load_long(key: str) -> pd.DataFrame:
    """지정된 데이터셋을 raw Excel에서 읽어 long(연도) 포맷으로 반환한다."""
    fname, sheet, extra_ids = FILES[key]
    path = os.path.join(RAW_DIR, fname)
    if not os.path.exists(path):
        return pd.DataFrame()

    raw = pd.read_excel(path, sheet_name=sheet, header=None)
    df = _clean_sheet(raw)

    year_cols = [c for c in df.columns if isinstance(c, str) and YEAR_RE.match(c)]
    id_cols = [c for c in ["기관명", "기관유형", "주무부처"] if c in df.columns]
    id_cols += [c for c in extra_ids if c in df.columns]

    long_df = df.melt(id_vars=id_cols, value_vars=year_cols, var_name="연도", value_name="값")
    long_df["연도"] = long_df["연도"].str.extract(r"(20\d{2})").astype(int)
    long_df["값"] = pd.to_numeric(long_df["값"], errors="coerce")
    long_df["기관명"] = long_df["기관명"].apply(normalize_institution_name)
    return long_df


def _pivot_items(long_df, item_map, extra_filter=None,
                  id_cols=("기관명", "기관유형", "주무부처", "연도")):
    """long_df에서 특정 항목만 뽑아 wide(item_map 값이 컬럼명)로 변환한다."""
    df = long_df.copy()
    if extra_filter:
        for k, v in extra_filter.items():
            if k in df.columns:
                df = df[df[k] == v]
    df = df[df["항목"].isin(item_map.keys())].copy()
    df["항목"] = df["항목"].map(item_map)
    id_cols = [c for c in id_cols if c in df.columns]
    wide = df.pivot_table(index=id_cols, columns="항목", values="값", aggfunc="first").reset_index()
    wide.columns.name = None
    return wide


def _safe_ratio(numerator, denominator):
    """분모가 0이거나 결측이면 NaN을 반환하는 안전한 비율 계산."""
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    ratio = num / den.replace(0, np.nan)
    return ratio.replace([np.inf, -np.inf], np.nan)


@st.cache_data(show_spinner="기관-연도 패널 데이터를 구성하는 중...")
def _build_panel() -> pd.DataFrame:
    """여러 데이터셋의 대표 항목을 뽑아 기관-연도 단위 패널로 병합한다."""
    finance = _load_long("finance")
    tax = _load_long("tax")
    employees = _load_long("employees")
    compensation = _load_long("compensation")
    exec_pay = _load_long("executive_pay")
    recruitment = _load_long("recruitment")
    welfare = _load_long("welfare")
    biz_expense = _load_long("business_expense")

    if finance.empty:
        return pd.DataFrame()

    panel = _pivot_items(finance, {
        "수입 > 수입합계": "총수입",
        "수입 > 정부지원수입 > 소계": "정부지원수입",
        "지출 > 지출합계": "총지출",
        "지출 > 인건비": "인건비",
        "지출 > 경상운영비": "경상운영비",
        "지출 > 사업비": "사업비",
    })

    tax_wide = _pivot_items(tax, {
        "과세표준": "과세표준", "법인세 산출세액": "법인세산출세액",
        "세액공제": "세액공제", "가산세": "가산세", "결정세액": "법인세결정세액",
    })

    employees_wide = _pivot_items(employees, {
        "임직원 총계(A+B+C)": "임직원수",
        "정규직-일반정규직-현원-계": "정규직수",
        "여성 현원-합계": "여성직원수",
    })

    nonreg_items = ["비정규직-기간제-계", "비정규직-기타", "비정규직-소속외 인력-계"]
    nonreg = employees[employees["항목"].isin(nonreg_items)]
    nonreg_wide = nonreg.pivot_table(
        index=["기관명", "기관유형", "주무부처", "연도"], columns="항목", values="값", aggfunc="first"
    ).reset_index()
    nonreg_wide.columns.name = None
    present = [c for c in nonreg_items if c in nonreg_wide.columns]
    nonreg_wide["비정규직수"] = nonreg_wide[present].sum(axis=1, skipna=True) if present else np.nan
    nonreg_wide = nonreg_wide[["기관명", "기관유형", "주무부처", "연도", "비정규직수"]]

    recruitment_wide = _pivot_items(recruitment, {
        "일반정규직총신규채용": "신규채용", "여성": "여성신규채용",
        "청년": "청년신규채용", "장애인": "장애인신규채용",
    })

    compensation_wide = _pivot_items(
        compensation,
        {
            "1인당 평균보수액": "직원평균보수", "1인당 평균보수액 - 남성": "남성평균보수",
            "1인당 평균보수액 - 여성": "여성평균보수", "평균근속연수(개월)": "평균근속연수_개월",
        },
        extra_filter={"구분": "정규직(일반정규직)"},
    )

    exec_pay_head = _pivot_items(exec_pay, {"합계": "기관장보수"}, extra_filter={"구분": "상임기관장"})
    exec_pay_avg = _pivot_items(exec_pay, {"상임임원평균연봉": "임원평균보수"}, extra_filter={"구분": "상임임원 평균보수(연봉)"})

    biz_expense_wide = _pivot_items(biz_expense, {"업무추진비 집행금액": "기관장업무추진비"})

    welfare_total = welfare[welfare["항목"].astype(str).str.contains("총계", na=False)]
    welfare_item_name = welfare_total["항목"].iloc[0] if not welfare_total.empty else None
    welfare_wide = (
        _pivot_items(welfare, {welfare_item_name: "총복리후생비"}) if welfare_item_name else pd.DataFrame()
    )

    for wide_df in [tax_wide, employees_wide, nonreg_wide, recruitment_wide,
                    compensation_wide, exec_pay_head, exec_pay_avg, biz_expense_wide, welfare_wide]:
        if wide_df.empty:
            continue
        merge_cols = [c for c in ["기관명", "기관유형", "주무부처", "연도"] if c in wide_df.columns]
        panel = panel.merge(wide_df, on=merge_cols, how="outer")

    # 파생변수 (분모 0/결측은 NaN 처리)
    if {"총수입", "총지출"}.issubset(panel.columns):
        panel["수지차"] = panel["총수입"] - panel["총지출"]
    if {"정부지원수입", "총수입"}.issubset(panel.columns):
        panel["정부지원수입비중"] = _safe_ratio(panel["정부지원수입"], panel["총수입"])
    if {"인건비", "총지출"}.issubset(panel.columns):
        panel["인건비비중"] = _safe_ratio(panel["인건비"], panel["총지출"])
    if {"사업비", "총지출"}.issubset(panel.columns):
        panel["사업비비중"] = _safe_ratio(panel["사업비"], panel["총지출"])
    if {"총수입", "임직원수"}.issubset(panel.columns):
        panel["1인당수입"] = _safe_ratio(panel["총수입"], panel["임직원수"])
    if {"총지출", "임직원수"}.issubset(panel.columns):
        panel["1인당지출"] = _safe_ratio(panel["총지출"], panel["임직원수"])
    if {"여성직원수", "임직원수"}.issubset(panel.columns):
        panel["여성직원비율"] = _safe_ratio(panel["여성직원수"], panel["임직원수"])
    if {"비정규직수", "임직원수"}.issubset(panel.columns):
        panel["비정규직비율"] = _safe_ratio(panel["비정규직수"], panel["임직원수"])

    return panel


def load_dataset(key: str) -> pd.DataFrame:
    """
    데이터셋을 불러온다.
    key가 'panel'이면 기관-연도 병합 패널을, 그 외에는 해당 데이터셋의
    long(연도) 포맷을 반환한다. 원본 파일이 없으면 안내 메시지를 표시한다.
    """
    if key == "panel":
        df = _build_panel()
    elif key in FILES:
        df = _load_long(key)
    else:
        raise ValueError(f"알 수 없는 데이터셋: {key}")

    if df.empty:
        st.error(
            "원본 데이터를 찾을 수 없습니다. `data/raw/` 폴더에 필요한 Excel 파일이 있는지 확인해주세요."
        )
    return df


def raw_files_exist() -> bool:
    return all(os.path.exists(os.path.join(RAW_DIR, fname)) for fname, _, _ in FILES.values())
