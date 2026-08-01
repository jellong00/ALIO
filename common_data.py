# -*- coding: utf-8 -*-
"""
common_data.py

공공기관 경영정보 대시보드에서 사용하는 모든 공통 함수를 담은 파일 하나.
(원래 utils/ scripts/ 폴더로 나뉘어 있던 코드를 폴더 구조 없이 쓸 수 있도록 한 파일로 합쳤다)

이 파일과 같은 위치(리포지토리 최상위)에 원본 엑셀 10개를 그대로 두면 된다.
7개의 페이지 파일(종합현황.py, pages/2_인력_채용.py ...)이 전부 이 파일을 불러와 사용한다.

    from common_data import *

전처리를 미리 실행할 필요가 없다. 각 페이지가 열릴 때 이 파일의 load_all_datasets() 가
원본 엑셀을 직접 읽어 정제하고, Streamlit 의 st.cache_data 로 캐싱한다 (최초 1회만 시간이 걸림).
"""

from __future__ import annotations

import re
import logging
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger("common_data")

# 원본 엑셀은 이 파일과 같은 폴더(리포지토리 최상위)에 있다고 가정한다.
RAW_DIR = Path(__file__).resolve().parent


# ============================================================================
# preprocessing.py 내용
# ============================================================================
# ---------------------------------------------------------------------------
# 1. 항목명 매핑 설정 (원자료 항목명 후보 목록)
#    실제 열 이름/항목명이 어느 후보와도 일치하지 않으면 검증 단계에서 경고로 남긴다.
#    주의: 아래 매핑은 KPI 계산 시 "어떤 원문 항목을 찾아야 하는지"를 위한 참고용이며,
#    실제 매칭은 utils/metrics.py 의 find_item() 함수가 부분 일치(포함 여부)로 수행한다.
# ---------------------------------------------------------------------------
ITEM_ALIASES = {
    "total_workforce": ["임직원수", "임직원 총계", "현원 합계", "총 현원", "현원"],
    "authorized_workforce": ["정원"],
    "new_hires": ["신규채용", "일반정규직총신규채용", "총신규채용"],
    "new_hires_youth": ["청년"],
    "new_hires_female": ["여성"],
    "new_hires_disabled": ["장애인"],
    "employee_avg_pay": ["1인당 평균보수액", "직원 평균보수", "평균보수"],
    "starting_pay": ["기본급"],
    "base_pay": ["기본급"],
    "fixed_allowance": ["고정수당"],
    "performance_pay": ["성과상여금"],
    "management_eval_bonus": ["경영평가 성과급", "경영평가성과급"],
    "total_revenue": ["수입합계", "총수입"],
    "total_expense": ["지출합계", "총지출"],
    "executive_expense": ["업무추진비 집행금액", "업무추진비"],
}

# 복리후생 세부 시트명 -> 재분류 카테고리 매핑
# 원본 시트명과 정확히 일치하지 않으면 "기타"로 처리한다 (억지 분류 금지 원칙 준수).
WELFARE_CATEGORY_MAP = {
    "3-2. 항목별-학자금": "생활지원",
    "3-4. 항목별-주택자금": "생활지원",
    "3-5. 항목별-생활안정자금": "생활지원",
    "3-3. 항목별-의료비및건강검진비": "건강지원",
    "3-1. 항목별-보육비": "가족지원",
    "3-6. 항목별-경조비및유족위로금": "가족지원",
    "3-7. 항목별-선택적복지제도": "선택·문화지원",
    "3-11. 항목별-문화여가비": "선택·문화지원",
    "3-8. 항목별-기념품비": "선택·문화지원",
    "3-9. 항목별-행사지원비": "기타지원",
    "3-10. 항목별-경로효친비": "기타지원",
    "3-12. 항목별-재해보상및재해부조": "기타지원",
    "3-13. 항목별-기타": "기타지원",
}

YEAR_COL_PATTERN = re.compile(r"^(20\d{2})년$")
YEAR_GENDER_COL_PATTERN = re.compile(r"^(20\d{2})년\s*(남|여)$")

MISSING_TOKENS = {"-", "–", "—", "해당없음", "없음", "", "NaN", "nan", None}


def clean_institution_name(name) -> Optional[str]:
    """기관명 문자열을 표준화한다 (공백/줄바꿈 정리).

    - 앞뒤 공백 제거
    - 내부 연속 공백을 단일 공백으로 치환
    - 줄바꿈 제거
    - 자동으로 완전히 통일할 수 없는 경우(법인 표기 변형 등)는 그대로 두되,
      추후 validate_data.py 에서 유사 명칭을 별도 목록으로 저장해 사람이 검수하도록 한다.
    """
    if pd.isna(name):
        return None
    s = str(name)
    s = s.replace("\n", " ").replace("\r", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s if s else None


def clean_category_text(val) -> Optional[str]:
    """기관유형/주무부처 등 범주형 텍스트의 공백/줄바꿈만 정리한다."""
    if pd.isna(val):
        return None
    s = str(val).replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s if s else None


def to_numeric_safe(series: pd.Series) -> pd.Series:
    """쉼표, %, 공백, 괄호(음수 표기), '-' 등이 섞인 값을 안전하게 숫자형으로 변환한다.

    변환 규칙:
    - 이미 숫자형(int/float)이면 그대로 반환
    - 문자열의 쉼표(,) 제거
    - '%' 기호 제거
    - 괄호로 감싸진 값 (1,234) 은 음수 -1234 로 처리
    - MISSING_TOKENS 에 해당하는 값은 결측(NaN)으로 처리
    - 그 외 변환 불가능한 값도 결측으로 처리하고 개수를 로그로 남긴다
    """
    if pd.api.types.is_numeric_dtype(series):
        return series

    def _conv(x):
        if x is None:
            return np.nan
        if isinstance(x, (int, float, np.integer, np.floating)):
            return float(x)
        s = str(x).strip()
        if s in MISSING_TOKENS:
            return np.nan
        is_negative = s.startswith("(") and s.endswith(")")
        s = s.strip("()")
        s = s.replace(",", "").replace("%", "").replace(" ", "")
        if s in MISSING_TOKENS:
            return np.nan
        try:
            v = float(s)
            return -v if is_negative else v
        except ValueError:
            return np.nan

    converted = series.map(_conv)
    fail_count = converted.isna().sum() - series.isna().sum()
    if fail_count > 0:
        logger.warning("숫자형 변환 실패 %d건 발생 (결측 처리됨)", fail_count)
    return converted


def find_year_columns(columns) -> list:
    """'2021년' ~ '2026년' 형태의 순수 연도 컬럼명 목록을 반환한다."""
    return [c for c in columns if isinstance(c, str) and YEAR_COL_PATTERN.match(c.strip())]


def find_year_gender_columns(columns) -> list:
    """'2021년 남' 형태의 연도+성별 결합 컬럼명 목록을 반환한다."""
    return [c for c in columns if isinstance(c, str) and YEAR_GENDER_COL_PATTERN.match(c.strip())]


def read_sheet_raw(file_path: str, sheet_name: str) -> Optional[pd.DataFrame]:
    """엑셀 시트를 header=1 규칙으로 읽는다 (1번째 행은 단위 표기용 병합행이므로 건너뜀).

    실패 시 None 을 반환하고 경고 로그를 남긴다 (전체 프로그램 중단 방지).
    """
    try:
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=1)
    except Exception as exc:  # noqa: BLE001
        logger.warning("시트 읽기 실패: %s / %s / 사유: %s", file_path, sheet_name, exc)
        return None

    if df.empty:
        logger.warning("빈 시트로 판단되어 건너뜀: %s / %s", file_path, sheet_name)
        return None

    # Unnamed 열 및 '상위기관' 열 제거 (상위기관은 대부분 비어있는 참고용 열)
    drop_cols = [c for c in df.columns if isinstance(c, str) and
                 (c.startswith("Unnamed") or c.strip() == "상위기관")]
    df = df.drop(columns=drop_cols, errors="ignore")

    # 완전히 빈 행 제거
    df = df.dropna(how="all")

    # 병합셀로 인한 기관 식별 컬럼 결측은 앞 방향으로 채움 (기관명/기관유형/주무부처 등)
    id_like_cols = [c for c in ["기관명", "기관유형", "주무부처", "기금명"] if c in df.columns]
    if id_like_cols:
        df[id_like_cols] = df[id_like_cols].ffill()

    # 기관명이 없는 행(순수 합계/소계 행 등)은 제거
    if "기관명" in df.columns:
        df = df[df["기관명"].notna()]

    return df.reset_index(drop=True)


def melt_wide_year_sheet(
    df: pd.DataFrame,
    id_vars_extra: list,
    dataset: str,
    sheet_name: str,
    unit: str,
) -> pd.DataFrame:
    """'2021년' ~ '20XX년' 형태의 넓은 연도 열을 가진 시트를 표준 긴 형태로 변환한다.

    반환 컬럼: institution_name_raw, institution_type, ministry, dataset, sheet_name,
               <id_vars_extra 원본 열들 그대로 유지>, year, value, unit
    """
    year_cols = find_year_columns(df.columns)
    if not year_cols:
        logger.warning("연도 열을 찾지 못함: dataset=%s sheet=%s", dataset, sheet_name)
        return pd.DataFrame()

    base_cols = ["기관명", "기관유형", "주무부처"]
    base_cols = [c for c in base_cols if c in df.columns]
    keep_extra = [c for c in id_vars_extra if c in df.columns]

    long_df = df.melt(
        id_vars=base_cols + keep_extra,
        value_vars=year_cols,
        var_name="year_raw",
        value_name="value",
    )
    long_df["year"] = long_df["year_raw"].str.extract(r"(20\d{2})").astype("Int64")
    long_df["value"] = to_numeric_safe(long_df["value"])
    long_df = long_df.drop(columns=["year_raw"])

    long_df = long_df.rename(columns={
        "기관명": "institution_name_raw",
        "기관유형": "institution_type",
        "주무부처": "ministry",
    })
    long_df["institution_name_raw"] = long_df["institution_name_raw"].map(clean_institution_name)
    if "institution_type" in long_df.columns:
        long_df["institution_type"] = long_df["institution_type"].map(clean_category_text)
    if "ministry" in long_df.columns:
        long_df["ministry"] = long_df["ministry"].map(clean_category_text)

    long_df["dataset"] = dataset
    long_df["sheet_name"] = sheet_name
    long_df["unit"] = unit

    # 구분/항목 등 추가 열의 앞뒤 공백/줄바꿈 정리 (원본 셀에 불규칙한 공백이 섞여 있는 사례 대응)
    # 주의: pandas 2.x 의 string dtype 은 object 가 아닐 수 있으므로 dtype 검사 없이 항상 적용한다.
    for col in keep_extra:
        long_df[col] = long_df[col].map(clean_category_text)

    # 값과 기관명이 모두 없는 행 제거 (완전 소계용 빈 행 등)
    long_df = long_df[long_df["institution_name_raw"].notna()]
    return long_df.reset_index(drop=True)


def melt_year_gender_sheet(df: pd.DataFrame, dataset: str, sheet_name: str, unit: str) -> pd.DataFrame:
    """'2021년 남' / '2021년 여' 처럼 연도+성별이 결합된 열을 가진 시트를 긴 형태로 변환한다.

    (일가정_양립_지원제도_운영현황.xlsx 의 '4. 일가정-유연근무현황' 시트 전용)
    성별 정보를 gender 열로 분리하여, 남/녀를 합산하지 않고 별도 행으로 유지한다.
    """
    yg_cols = find_year_gender_columns(df.columns)
    if not yg_cols:
        return pd.DataFrame()

    base_cols = [c for c in ["기관명", "기관유형", "주무부처", "항목"] if c in df.columns]
    long_df = df.melt(id_vars=base_cols, value_vars=yg_cols, var_name="year_gender", value_name="value")

    extracted = long_df["year_gender"].str.extract(YEAR_GENDER_COL_PATTERN)
    long_df["year"] = extracted[0].astype("Int64")
    long_df["gender"] = extracted[1].map({"남": "남성", "여": "여성"})
    long_df["value"] = to_numeric_safe(long_df["value"])
    long_df = long_df.drop(columns=["year_gender"])

    long_df = long_df.rename(columns={
        "기관명": "institution_name_raw",
        "기관유형": "institution_type",
        "주무부처": "ministry",
        "항목": "item",
    })
    long_df["institution_name_raw"] = long_df["institution_name_raw"].map(clean_institution_name)
    long_df["institution_type"] = long_df.get("institution_type", pd.Series(dtype=object)).map(clean_category_text)
    long_df["ministry"] = long_df.get("ministry", pd.Series(dtype=object)).map(clean_category_text)
    if "item" in long_df.columns:
        long_df["item"] = long_df["item"].map(clean_category_text)

    long_df["dataset"] = dataset
    long_df["sheet_name"] = sheet_name
    long_df["unit"] = unit
    long_df = long_df[long_df["institution_name_raw"].notna()]
    return long_df.reset_index(drop=True)


def split_hierarchical_item(series: pd.Series, max_levels: int = 4) -> pd.DataFrame:
    """'수입 > 정부지원수입 > 직접지원 > 출연금' 형태의 계층형 항목명을 레벨별로 분리한다.

    반환: level_1 ~ level_(max_levels) 컬럼을 가진 DataFrame. 레벨이 부족한 경우 결측(None).
    """
    split_result = series.fillna("").str.split(">")
    out = pd.DataFrame(index=series.index)
    for i in range(max_levels):
        out[f"level_{i+1}"] = split_result.map(
            lambda parts, i=i: parts[i].strip() if len(parts) > i and parts[i].strip() else None
        )
    return out


# ============================================================================
# pipeline.py 내용
# ============================================================================
# (주의) RAW_DIR 은 파일 맨 위에서 이미 "이 파일과 같은 폴더"로 정의했다.

def _process_generic_file(file_name: str, dataset: str, unit: str, id_vars_extra: list) -> pd.DataFrame:
    """단일 파일 내 모든 시트가 동일한 '연도-와이드' 구조를 따르는 표준 파일을 처리한다.

    각 시트를 자동으로 발견하여(pd.ExcelFile) melt_wide_year_sheet 로 변환한 뒤
    pd.concat 으로 결합한다 (동일 열 구조를 가진 시트 결합 원칙).
    """
    file_path = RAW_DIR / file_name
    if not file_path.exists():
        logger.warning("파일이 존재하지 않아 건너뜀: %s", file_path)
        return pd.DataFrame()

    try:
        sheet_names = pd.ExcelFile(file_path).sheet_names
    except Exception as exc:  # noqa: BLE001
        logger.error("엑셀 파일 손상 또는 열기 실패: %s (%s)", file_name, exc)
        return pd.DataFrame()

    frames = []
    for sheet_name in sheet_names:
        df = read_sheet_raw(str(file_path), sheet_name)
        if df is None:
            continue
        long_df = melt_wide_year_sheet(df, id_vars_extra, dataset, sheet_name, unit)
        if not long_df.empty:
            frames.append(long_df)
        else:
            logger.warning("변환 결과가 비어 있음: %s / %s", file_name, sheet_name)

    if not frames:
        logger.error("%s 파일에서 유효한 데이터를 하나도 얻지 못함", file_name)
        return pd.DataFrame()

    result = pd.concat(frames, ignore_index=True)
    # 동일 기관·연도·항목·시트 완전 중복행 제거 (원자료 중복 방지)
    dedup_cols = [c for c in ["institution_name_raw", "year", "sheet_name"] + id_vars_extra
                  if c in result.columns]
    before = len(result)
    result = result.drop_duplicates(subset=dedup_cols + ["value"], keep="first")
    if len(result) < before:
        logger.info("%s: 완전 중복행 %d건 제거", file_name, before - len(result))
    return result


# ---------------------------------------------------------------------------
# 파일별 전처리 함수
# ---------------------------------------------------------------------------

def process_workforce() -> pd.DataFrame:
    """임직원수현황.xlsx -> workforce.parquet

    시트: '1. 임직원 수' (단일 시트, 항목이 '임원-기관장-상임정원' 처럼 '-'로 계층 구분됨)
    단위: 명, %
    """
    df = _process_generic_file("임직원수현황.xlsx", "workforce", "명", ["항목"])
    if df.empty:
        return df
    df = df.rename(columns={"항목": "item"})
    # '-' 기준 계층 분리 (최대 4단계) - 항목 구조가 시트마다 깊이가 달라 일부만 채워질 수 있음
    parts = df["item"].fillna("").str.split("-", n=3, expand=True)
    for i in range(4):
        col = f"item_level_{i+1}"
        df[col] = parts[i].str.strip() if i in parts.columns else None
        df[col] = df[col].replace("", None)
    # 정원/현원 구분 플래그 (정원충족률 계산에 사용)
    df["count_type"] = df["item"].apply(
        lambda x: "정원" if isinstance(x, str) and "정원" in x
        else ("현원" if isinstance(x, str) and "현원" in x else None)
    )
    return df


def process_recruitment() -> pd.DataFrame:
    """신규채용현황.xlsx -> recruitment.parquet

    시트: '1. 신규채용현황', '2. 청년인턴채용현황' (열 구조 동일: 기관명/기관유형/주무부처/항목/연도열)
    단위: 명
    주의: 청년/여성/장애인 신규채용은 상호배타적 집단이 아니므로(중복 가능),
          단순 합산해 100% 로 취급하지 않는다 (§26 원칙).
    """
    return _process_generic_file("신규채용현황.xlsx", "recruitment", "명", ["항목"]).rename(
        columns={"항목": "item"}
    )


def process_employee_pay() -> pd.DataFrame:
    """직원평균보수현황.xlsx -> employee_pay.parquet

    시트: '1. 직원평균보수' (구분: 정규직/무기계약직 등, 항목: 기본급/고정수당/성과상여금 등)
          '2. 신입사원초임' (항목만 존재, 구분 없음)
    단위: 천원, 명, 월
    두 시트는 열 구조가 달라(구분 유무) sheet_name 으로 구분해 결합하고,
    pay_type 열로 '평균보수'/'신입초임' 을 구분한다.
    """
    file_path = RAW_DIR / "직원평균보수현황.xlsx"
    if not file_path.exists():
        logger.warning("파일이 존재하지 않아 건너뜀: %s", file_path)
        return pd.DataFrame()

    frames = []
    for sheet_name in pd.ExcelFile(file_path).sheet_names:
        df = read_sheet_raw(str(file_path), sheet_name)
        if df is None:
            continue
        id_vars_extra = [c for c in ["구분", "항목"] if c in df.columns]
        long_df = melt_wide_year_sheet(df, id_vars_extra, "employee_pay", sheet_name, "천원")
        if long_df.empty:
            continue
        long_df = long_df.rename(columns={"구분": "employment_type", "항목": "item"})
        long_df["pay_type"] = "신입초임" if "신입" in sheet_name else "평균보수"
        frames.append(long_df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def process_executive_pay() -> pd.DataFrame:
    """임원연봉.xlsx -> executive_pay.parquet

    시트: '임원연봉' (구분: 상임기관장/상임감사/상임이사 등 - 임원 유형, 항목: 기본급 등 보수 구성)
    단위: 천원
    """
    return _process_generic_file("임원연봉.xlsx", "executive_pay", "천원", ["구분", "항목"]).rename(
        columns={"구분": "executive_type", "항목": "item"}
    )


def process_executive_expense() -> pd.DataFrame:
    """기관장업무추진비.xlsx -> executive_expense.parquet

    시트: '기관장업무추진비' (항목: '업무추진비 집행금액' 단일 항목)
    단위: 천원
    """
    return _process_generic_file("기관장업무추진비.xlsx", "executive_expense", "천원", ["항목"]).rename(
        columns={"항목": "item"}
    )


def process_corporate_tax() -> pd.DataFrame:
    """법인세정보.xlsx -> corporate_tax.parquet

    시트: '법인세' (항목: 과세표준/법인세 산출세액/세액공제/가산세/결정세액)
    단위: 천원
    """
    return _process_generic_file("법인세정보.xlsx", "corporate_tax", "천원", ["항목"]).rename(
        columns={"항목": "item"}
    )


def process_welfare() -> pd.DataFrame:
    """복리후생비.xlsx -> welfare.parquet

    시트 구성:
        '1. 예산상 복리후생비'        : 구분(임원/정규직 등), 항목('급여성 > 보육비' 등 계층형)
        '2. 사내복지기금 조성현황'    : 구분, 항목 (기금 관련 세부 항목)
        '3-1'~'3-13' 항목별 세부시트 : 구분(무상/유상), 항목(대부분 '소계' 단일값)
    단위: 천원 (일부 시트는 천원, 명 혼용 - unit 열에 원문 그대로 기록)
    §14 원칙에 따라 총복리후생비(1번 시트 합계성 항목)와 세부 항목(3-1~3-13)을 자동으로 재합산하지
    않도록, dataset 을 sheet_group 으로 세분화해 이중 합산을 방지한다.
    복지항목 재분류는 WELFARE_CATEGORY_MAP 을 사용하며, 매핑에 없는 시트는 '기타'로 분류한다
    (원자료 항목명과 정확히 일치하지 않으면 억지로 분류하지 않는다는 원칙 준수).
    """
    file_path = RAW_DIR / "복리후생비.xlsx"
    if not file_path.exists():
        logger.warning("파일이 존재하지 않아 건너뜀: %s", file_path)
        return pd.DataFrame()

    frames = []
    for sheet_name in pd.ExcelFile(file_path).sheet_names:
        df = read_sheet_raw(str(file_path), sheet_name)
        if df is None:
            continue
        id_vars_extra = [c for c in ["구분", "항목"] if c in df.columns]
        long_df = melt_wide_year_sheet(df, id_vars_extra, "welfare", sheet_name, "천원")
        if long_df.empty:
            continue
        long_df = long_df.rename(columns={"구분": "category", "항목": "item"})

        if sheet_name.startswith("1."):
            long_df["sheet_group"] = "예산상_복리후생비_총괄"
            if "item" in long_df.columns:
                hier = split_hierarchical_item(long_df["item"], max_levels=2)
                long_df["welfare_level_1"] = hier["level_1"]
                long_df["welfare_level_2"] = hier["level_2"]
            long_df["welfare_category"] = "총괄"
        elif sheet_name.startswith("2."):
            long_df["sheet_group"] = "사내복지기금"
            long_df["welfare_category"] = "기타"
        else:
            long_df["sheet_group"] = "항목별_세부내역"
            long_df["welfare_category"] = WELFARE_CATEGORY_MAP.get(sheet_name, "기타")
            if long_df["welfare_category"].iloc[0] == "기타" and sheet_name not in WELFARE_CATEGORY_MAP:
                logger.warning("복리후생 세부 시트 재분류 매핑 없음 -> 기타로 처리: %s", sheet_name)

        frames.append(long_df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def process_other_welfare() -> pd.DataFrame:
    """그밖의_복리후생제도_등의_운영현황.xlsx -> other_welfare.parquet

    시트: '1-2. 휴직급여지급현황' (구분: 정규직/임원 등, 항목: 업무상 공상/업무외 질병 등)
          '2-3. 퇴직금가산지급현황' (구분, 항목: 직무상 부상.사망 등)
    단위: 명, 천원 (혼용)
    """
    return _process_generic_file(
        "그밖의_복리후생제도_등의_운영현황.xlsx", "other_welfare", "명 또는 천원", ["구분", "항목"]
    ).rename(columns={"구분": "employment_type", "항목": "item"})


def process_work_family() -> pd.DataFrame:
    """일가정_양립_지원제도_운영현황.xlsx -> work_family.parquet

    시트 1~3, 5, 6 : 표준 연도-와이드 구조 (구분 열 존재)
    시트 4 (유연근무현황) : '2021년 남' 처럼 연도+성별 결합 컬럼 -> melt_year_gender_sheet 로 별도 처리
    시트 7 (직장어린이집운영비) : '연도' 가 이미 하나의 열로 존재하는 예외 구조 -> 별도 처리
    남녀 인원은 성별 그대로 유지하고(합산 금지), 인원수/전일제환산 값도 구분하여 별도 지표로 취급한다.
    """
    file_path = RAW_DIR / "일가정_양립_지원제도_운영현황.xlsx"
    if not file_path.exists():
        logger.warning("파일이 존재하지 않아 건너뜀: %s", file_path)
        return pd.DataFrame()

    frames = []
    for sheet_name in pd.ExcelFile(file_path).sheet_names:
        df = read_sheet_raw(str(file_path), sheet_name)
        if df is None:
            continue

        if "유연근무" in sheet_name:
            long_df = melt_year_gender_sheet(df, "work_family", sheet_name, "명")
            if long_df.empty:
                continue
            # 항목 접미사로 인원수 vs 전일제환산 구분 (합산하지 않고 별도 지표로 유지 - §11 원칙)
            long_df["metric_type"] = long_df["item"].apply(
                lambda x: "전일제환산" if isinstance(x, str) and "전일제환산" in x
                else ("인원수" if isinstance(x, str) and "인원수" in x else None)
            )
            frames.append(long_df)
            continue

        if "직장어린이집" in sheet_name:
            # 이미 '연도' 열이 존재하는 예외 구조: 연도별로 여러 행이 있으며
            # '금액' 과 '수혜인원' 이 각각 하나의 지표 열로 존재한다.
            keep_cols = [c for c in ["기관명", "기관유형", "주무부처", "연도", "금액", "수혜인원"]
                         if c in df.columns]
            sub = df[keep_cols].copy()
            sub["연도"] = sub["연도"].astype(str).str.extract(r"(20\d{2})").astype("Int64")
            metric_frames = []
            for metric_col, unit in [("금액", "천원"), ("수혜인원", "명")]:
                if metric_col not in sub.columns:
                    continue
                m = sub[["기관명", "기관유형", "주무부처", "연도"]].copy()
                m["item"] = f"직장어린이집_{metric_col}"
                m["value"] = to_numeric_safe(sub[metric_col])
                m["unit"] = unit
                metric_frames.append(m)
            if not metric_frames:
                continue
            long_df = pd.concat(metric_frames, ignore_index=True)
            long_df = long_df.rename(columns={
                "기관명": "institution_name_raw", "기관유형": "institution_type",
                "주무부처": "ministry", "연도": "year",
            })
            long_df["institution_name_raw"] = long_df["institution_name_raw"].map(clean_institution_name)
            long_df["institution_type"] = long_df["institution_type"].map(clean_category_text)
            long_df["ministry"] = long_df["ministry"].map(clean_category_text)
            long_df["dataset"] = "work_family"
            long_df["sheet_name"] = sheet_name
            long_df = long_df[long_df["institution_name_raw"].notna()]
            frames.append(long_df)
            continue

        # 표준 구조 시트 (1,2,3,5,6번)
        id_vars_extra = [c for c in ["구분", "항목"] if c in df.columns]
        long_df = melt_wide_year_sheet(df, id_vars_extra, "work_family", sheet_name, "명")
        if long_df.empty:
            continue
        long_df = long_df.rename(columns={"구분": "item"})
        frames.append(long_df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def process_finance() -> pd.DataFrame:
    """수입지출현황.xlsx -> finance.parquet

    시트: '수입지출현황(고유사업)', '정부순지원수입(고유사업)',
          '수입지출현황(기금계정)'(기금명 열 추가), '정부순지원수입(기금계정)'(기금명 열 추가)
    단위: 백만원
    항목이 '수입 > 정부지원수입 > 직접지원 > 출연금' 형태의 계층형 문자열이므로
    split_hierarchical_item 으로 level_1~level_4 로 분리한다.
    '고유사업'과 '기금계정'은 서로 다른 회계 단위이므로 account_type 열로 구분하여
    합산 시 이중 계산되지 않도록 한다.
    """
    file_path = RAW_DIR / "수입지출현황.xlsx"
    if not file_path.exists():
        logger.warning("파일이 존재하지 않아 건너뜀: %s", file_path)
        return pd.DataFrame()

    frames = []
    for sheet_name in pd.ExcelFile(file_path).sheet_names:
        df = read_sheet_raw(str(file_path), sheet_name)
        if df is None:
            continue
        id_vars_extra = [c for c in ["기금명", "항목"] if c in df.columns]
        long_df = melt_wide_year_sheet(df, id_vars_extra, "finance", sheet_name, "백만원")
        if long_df.empty:
            continue
        long_df = long_df.rename(columns={"기금명": "fund_name", "항목": "item"})

        long_df["account_type"] = "기금계정" if "기금계정" in sheet_name else "고유사업"
        long_df["statement_type"] = "정부순지원수입" if "정부순지원수입" in sheet_name else "수입지출현황"

        if "item" in long_df.columns:
            hier = split_hierarchical_item(long_df["item"], max_levels=4)
            long_df = pd.concat([long_df, hier], axis=1)

        frames.append(long_df)

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


# ---------------------------------------------------------------------------
# 기관 마스터 테이블
# ---------------------------------------------------------------------------

def build_institution_master(all_long_frames: dict) -> pd.DataFrame:
    """모든 도메인 데이터에 등장하는 (institution_name_raw, institution_type, ministry) 조합을 모아
    기관 마스터 테이블을 생성한다.

    [한계] 완전한 기관코드가 원자료에 없으므로, 정제된 기관명(institution_name)을 결합 키로 사용한다.
    기관유형/주무부처가 파일마다 다르게 기록된 경우, 가장 빈도가 높은 값을 대표값으로 채택하고
    그 외 조합은 institution_name_raw 원본 그대로 보존한다.
    """
    records = []
    for dataset_name, df in all_long_frames.items():
        if df.empty or "institution_name_raw" not in df.columns:
            continue
        cols = [c for c in ["institution_name_raw", "institution_type", "ministry"] if c in df.columns]
        sub = df[cols].drop_duplicates().copy()
        sub["source_dataset"] = dataset_name
        records.append(sub)

    if not records:
        return pd.DataFrame()

    combined = pd.concat(records, ignore_index=True)
    combined["institution_name"] = combined["institution_name_raw"]  # 표준 기관명 = 정제된 원명 (한계 사항)

    # 기관명별 기관유형/주무부처 최빈값을 대표값으로 채택
    def _mode_or_first(s: pd.Series):
        s = s.dropna()
        if s.empty:
            return None
        return s.mode().iloc[0]

    agg_cols = {}
    if "institution_type" in combined.columns:
        agg_cols["institution_type"] = _mode_or_first
    if "ministry" in combined.columns:
        agg_cols["ministry"] = _mode_or_first

    master = combined.groupby("institution_name", as_index=False).agg(agg_cols) if agg_cols else \
        combined[["institution_name"]].drop_duplicates()

    master["institution_id"] = master["institution_name"]
    master["institution_name_raw"] = master["institution_name"]
    master["parent_institution"] = None  # 원자료에 상위기관 정보가 사실상 비어있어 채우지 못함 (한계)

    master = master[[
        "institution_id", "institution_name", "institution_name_raw",
        "institution_type", "ministry", "parent_institution",
    ]]
    return master.sort_values("institution_name").reset_index(drop=True)


# ============================================================================
# metrics.py 내용
# ============================================================================
GROUP_KEYS = ["institution_name_raw", "year"]


def _pivot_sum(df: pd.DataFrame, item_filter, value_col_name: str) -> pd.DataFrame:
    """item 필터에 해당하는 행을 institution×year 기준으로 합산한다."""
    if df.empty or "item" not in df.columns:
        return pd.DataFrame(columns=GROUP_KEYS + [value_col_name])
    sub = df[df["item"].isin(item_filter)] if isinstance(item_filter, (list, set)) else df[df["item"] == item_filter]
    if sub.empty:
        return pd.DataFrame(columns=GROUP_KEYS + [value_col_name])
    agg = sub.groupby(GROUP_KEYS, as_index=False)["value"].sum()
    return agg.rename(columns={"value": value_col_name})


def workforce_summary(df_workforce: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 총 현원, 총 정원, 여성 현원, 정원충족률을 계산한다."""
    total = _pivot_sum(df_workforce, "임직원 총계(A+B+C)", "total_workforce")
    authorized = _pivot_sum(
        df_workforce,
        ["임원-상임임원정원(A)", "정규직-일반정규직-정원-계(B)", "정규직-무기계약직-정원-계(C)"],
        "total_authorized",
    )
    female = _pivot_sum(df_workforce, "여성 현원-합계", "female_workforce")

    result = total.merge(authorized, on=GROUP_KEYS, how="outer").merge(female, on=GROUP_KEYS, how="outer")
    result["fill_rate_pct"] = result.apply(
        lambda r: safe_divide(r.get("total_workforce"), r.get("total_authorized")) * 100
        if pd.notna(safe_divide(r.get("total_workforce"), r.get("total_authorized"))) else np.nan,
        axis=1,
    )
    result["female_ratio_pct"] = result.apply(
        lambda r: safe_divide(r.get("female_workforce"), r.get("total_workforce")) * 100
        if pd.notna(safe_divide(r.get("female_workforce"), r.get("total_workforce"))) else np.nan,
        axis=1,
    )
    return result


def recruitment_summary(df_recruitment: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 총 신규채용, 청년/여성/장애인 채용(중복 가능 집단, 별도 유지)을 계산한다."""
    total_new = _pivot_sum(df_recruitment, ["일반정규직총신규채용", "정규직(무기계약직)신규채용"], "total_new_hires")
    youth = _pivot_sum(df_recruitment, "청년", "youth_hires")
    female = _pivot_sum(df_recruitment, "여성", "female_hires")
    disabled = _pivot_sum(df_recruitment, "장애인", "disabled_hires")

    result = total_new
    for other in (youth, female, disabled):
        result = result.merge(other, on=GROUP_KEYS, how="outer")
    return result


def employee_avg_pay_summary(df_employee_pay: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 직원 평균보수(1인당 평균보수액), 상시종업원수, 보수 구성요소를 계산한다."""
    avg = df_employee_pay[
        (df_employee_pay["pay_type"] == "평균보수") & (df_employee_pay["item"] == "1인당 평균보수액")
    ]
    avg_pivot = avg.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "employee_avg_pay"}
    )

    headcount = df_employee_pay[
        (df_employee_pay["pay_type"] == "평균보수") & (df_employee_pay["item"] == "상시 종업원수")
    ]
    headcount_pivot = headcount.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "avg_headcount_for_weighting"}
    )

    components = ["기본급", "고정수당", "실적수당", "급여성 복리후생비", "성과상여금", "(경영평가 성과급)"]
    comp_df = df_employee_pay[
        (df_employee_pay["pay_type"] == "평균보수") & (df_employee_pay["item"].isin(components))
    ]
    comp_pivot = comp_df.pivot_table(
        index=GROUP_KEYS, columns="item", values="value", aggfunc="sum"
    ).reset_index()

    tenure = df_employee_pay[
        (df_employee_pay["pay_type"] == "평균보수") & (df_employee_pay["item"] == "평균근속연수(개월)")
    ]
    tenure_pivot = tenure.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "avg_tenure_months"}
    )

    result = avg_pivot.merge(headcount_pivot, on=GROUP_KEYS, how="outer")
    result = result.merge(comp_pivot, on=GROUP_KEYS, how="left")
    result = result.merge(tenure_pivot, on=GROUP_KEYS, how="left")
    return result


def starting_pay_summary(df_employee_pay: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 신입사원 초임(합계)을 계산한다."""
    starting = df_employee_pay[(df_employee_pay["pay_type"] == "신입초임") & (df_employee_pay["item"] == "합계")]
    return starting.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "starting_pay"}
    )


def executive_pay_summary(df_executive_pay: pd.DataFrame, executive_type: str = "상임기관장") -> pd.DataFrame:
    """기관×연도별 특정 임원 유형(기본값: 상임기관장)의 총연봉을 계산한다."""
    sub = df_executive_pay[df_executive_pay["executive_type"] == executive_type]
    total = sub[sub["item"] == "합계"]
    if not total.empty:
        return total.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
            columns={"value": "executive_total_pay"}
        )
    # '합계' 항목이 없는 기관 대비: 보수 구성요소 합으로 보완
    components = ["기본급", "고정수당", "실적수당", "급여성 복리후생비", "성과상여금", "(경영평가 성과급)"]
    comp = sub[sub["item"].isin(components)]
    return comp.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "executive_total_pay"}
    )


def executive_expense_summary(df_executive_expense: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 기관장 업무추진비 집행금액을 계산한다."""
    sub = df_executive_expense[df_executive_expense["item"] == "업무추진비 집행금액"]
    return sub.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "executive_expense"}
    )


def welfare_total_summary(df_welfare: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 총복리후생비(예산상 복리후생비 총괄 시트 기준)를 계산한다."""
    sub = df_welfare[df_welfare["sheet_group"] == "예산상_복리후생비_총괄"]
    return sub.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "total_welfare_expense"}
    )


def welfare_category_breakdown(df_welfare: pd.DataFrame) -> pd.DataFrame:
    """기관×연도×복지 재분류 카테고리별 금액을 계산한다 (항목별 세부내역 시트 기준, 무상+유상 합산)."""
    sub = df_welfare[df_welfare["sheet_group"] == "항목별_세부내역"]
    return sub.groupby(GROUP_KEYS + ["welfare_category"], as_index=False)["value"].sum()


def finance_summary(df_finance: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 총수입/총지출/정부지원수입/자체수입 관련 값을 계산한다 (수입지출현황 시트 기준)."""
    base = df_finance[df_finance["statement_type"] == "수입지출현황"]
    if base.empty:
        return pd.DataFrame(columns=GROUP_KEYS)

    def _sum_level2(level2_values):
        sub = base[base["level_2"].isin(level2_values)]
        return sub.groupby(GROUP_KEYS, as_index=False)["value"].sum()

    total_revenue = _sum_level2(["수입합계"]).rename(columns={"value": "total_revenue"})
    total_expense = _sum_level2(["지출합계"]).rename(columns={"value": "total_expense"})
    gov_support = _sum_level2(["정부지원수입"]).rename(columns={"value": "gov_support_revenue"})
    conservative_own = _sum_level2(["기타사업수입", "부대수입", "기타"]).rename(
        columns={"value": "own_revenue_conservative"}
    )
    equity_capital = _sum_level2(["출자금"]).rename(columns={"value": "equity_capital"})
    borrowings = _sum_level2(["차입금"]).rename(columns={"value": "borrowings"})
    labor_cost = _sum_level2(["인건비"]).rename(columns={"value": "labor_cost"})
    business_revenue = _sum_level2(["기타사업수입"]).rename(columns={"value": "business_revenue"})

    result = total_revenue
    for other in (total_expense, gov_support, conservative_own, equity_capital, borrowings, labor_cost, business_revenue):
        result = result.merge(other, on=GROUP_KEYS, how="outer")

    result["balance"] = result.get("total_revenue", np.nan) - result.get("total_expense", np.nan)
    result["own_revenue_broad"] = (
        result.get("total_revenue", np.nan)
        - result.get("gov_support_revenue", 0).fillna(0)
        - result.get("equity_capital", 0).fillna(0)
        - result.get("borrowings", 0).fillna(0)
    )
    return result


def work_family_leave_summary(df_work_family: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 육아휴직 이용자 수(전체/남성/여성)를 계산한다."""
    sub = df_work_family[df_work_family["sheet_name"].str.contains("육아휴직사용자수", na=False)]
    total = sub[sub["item"] == "전체 사용자 수"].groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "parental_leave_total"}
    )
    male = sub[sub["item"] == "남성 사용자 수"].groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "parental_leave_male"}
    )
    female = sub[sub["item"] == "여성 사용자 수"].groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "parental_leave_female"}
    )
    result = total.merge(male, on=GROUP_KEYS, how="outer").merge(female, on=GROUP_KEYS, how="outer")
    return result


def work_family_daycare_summary(df_work_family: pd.DataFrame) -> pd.DataFrame:
    """기관×연도별 직장어린이집 운영비, 수혜인원을 계산한다."""
    amount = df_work_family[df_work_family["item"] == "직장어린이집_금액"]
    benefit = df_work_family[df_work_family["item"] == "직장어린이집_수혜인원"]
    amount_pivot = amount.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "daycare_expense"}
    )
    benefit_pivot = benefit.groupby(GROUP_KEYS, as_index=False)["value"].sum().rename(
        columns={"value": "daycare_beneficiaries"}
    )
    return amount_pivot.merge(benefit_pivot, on=GROUP_KEYS, how="outer")


def compute_comparison_index(value: float, comparison_mean: float) -> float:
    """비교집단 평균을 100으로 한 지수를 계산한다 (선택기관 값 / 비교집단 평균 × 100)."""
    ratio = safe_divide(value, comparison_mean)
    if pd.isna(ratio):
        return np.nan
    return ratio * 100


# ============================================================================
# formatting.py 내용
# ============================================================================
def format_number(value, decimals: int = 0) -> str:
    """결측이면 '자료 없음', 아니면 천 단위 구분기호가 포함된 문자열을 반환한다."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "자료 없음"
    return f"{value:,.{decimals}f}"


def format_percent(value, decimals: int = 1) -> str:
    """비율 값을 소수점 첫째 자리까지 '%' 와 함께 표시한다. 결측이면 '자료 없음'."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "자료 없음"
    return f"{value:,.{decimals}f}%"


def format_amount_krw_thousand(value_in_thousand_won) -> str:
    """단위가 '천원' 인 금액을 사람이 읽기 쉬운 억원/조원 단위 문자열로 변환한다.

    입력: 천원 단위 숫자 (예: 1,234,567 천원)
    - 1조 원 이상: X.XX조원
    - 1억 원 이상: X.X억원
    - 그 미만: 천원 단위 그대로 표시
    """
    if value_in_thousand_won is None or (isinstance(value_in_thousand_won, float) and np.isnan(value_in_thousand_won)):
        return "자료 없음"
    won = value_in_thousand_won * 1000
    trillion = 1_000_000_000_000
    hundred_million = 100_000_000
    if abs(won) >= trillion:
        return f"{won / trillion:,.2f}조원"
    if abs(won) >= hundred_million:
        return f"{won / hundred_million:,.1f}억원"
    return f"{value_in_thousand_won:,.0f}천원"


def format_amount_krw_million(value_in_million_won) -> str:
    """단위가 '백만원' 인 금액을 억원/조원 단위 문자열로 변환한다 (수입·지출 탭 전용)."""
    if value_in_million_won is None or (isinstance(value_in_million_won, float) and np.isnan(value_in_million_won)):
        return "자료 없음"
    won = value_in_million_won * 1_000_000
    trillion = 1_000_000_000_000
    hundred_million = 100_000_000
    if abs(won) >= trillion:
        return f"{won / trillion:,.2f}조원"
    if abs(won) >= hundred_million:
        return f"{won / hundred_million:,.1f}억원"
    return f"{value_in_million_won:,.0f}백만원"


def truncate_institution_name(name: str, max_len: int = 10) -> str:
    """긴 기관명을 그래프 축 표시용으로 축약한다 (뒤에 … 추가)."""
    if name is None:
        return "자료 없음"
    s = str(name)
    return s if len(s) <= max_len else s[:max_len] + "…"


def safe_divide(numerator, denominator):
    """분모가 0이거나 결측이면 NaN을 반환하는 안전한 나눗셈 (분모 0 예외처리 원칙)."""
    if numerator is None or denominator is None:
        return np.nan
    if isinstance(denominator, (int, float)) and denominator == 0:
        return np.nan
    if isinstance(denominator, float) and np.isnan(denominator):
        return np.nan
    try:
        result = numerator / denominator
    except ZeroDivisionError:
        return np.nan
    if isinstance(result, float) and np.isinf(result):
        return np.nan
    return result


# ============================================================================
# charts.py 내용
# ============================================================================
CHART_HEIGHT = 340
FONT_SIZE_AXIS = 13
FONT_SIZE_TITLE = 18

COMMON_LAYOUT = dict(
    height=CHART_HEIGHT,
    margin=dict(l=10, r=10, t=45, b=10),
    font=dict(size=FONT_SIZE_AXIS),
    title_font=dict(size=FONT_SIZE_TITLE),
    legend=dict(font=dict(size=FONT_SIZE_AXIS)),
)


def render_or_empty(fig, container=st, empty_message: str = "표시할 데이터가 없습니다.") -> None:
    """차트가 None(데이터 없음)이면 안내 메시지를, 있으면 차트를 렌더링한다."""
    if fig is None:
        container.info(empty_message)
        return
    fig.update_layout(**COMMON_LAYOUT)
    container.plotly_chart(fig, use_container_width=True)


def line_trend_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str, y_title: str, unit: str):
    """연도별 추이 선그래프를 생성한다."""
    if df.empty or df[y].dropna().empty:
        return None
    fig = px.line(
        df, x=x, y=y, color=color, markers=True, title=title,
        labels={x: "연도", y: y_title, color: "기관"},
    )
    fig.update_traces(hovertemplate=f"%{{fullData.name}}<br>연도: %{{x}}<br>{y_title}: %{{y:,.0f}} {unit}<extra></extra>")
    return fig


def bar_ranking_chart(df: pd.DataFrame, name_col: str, value_col: str, title: str, unit: str, top_n: int = 10):
    """기관별 순위 가로 막대그래프 (내림차순, 최댓값이 위로 오도록 정렬). 기본 상위 10개만 표시."""
    if df.empty or df[value_col].dropna().empty:
        return None
    ranked = df.dropna(subset=[value_col]).sort_values(value_col, ascending=False).head(top_n).copy()
    ranked["display_name"] = ranked[name_col].map(lambda s: truncate_institution_name(s, 12))
    fig = px.bar(
        ranked.iloc[::-1], x=value_col, y="display_name", orientation="h", title=title,
        labels={value_col: unit, "display_name": "기관명"},
        text=ranked.iloc[::-1][value_col].map(lambda v: f"{v:,.0f}"),
    )
    fig.update_traces(
        hovertemplate="기관명: %{customdata[0]}<br>값: %{x:,.1f} " + unit + "<extra></extra>",
        customdata=ranked.iloc[::-1][[name_col]].values,
    )
    return fig


def scatter_with_trend(df: pd.DataFrame, x: str, y: str, name_col: str, title: str,
                        x_title: str, y_title: str, log_x: bool = False, log_y: bool = False):
    """산점도 (필요시 단순 추세선 포함, 통계모형 아님을 명시)."""
    if df.empty or df[[x, y]].dropna().empty:
        return None
    fig = px.scatter(
        df, x=x, y=y, hover_name=name_col, title=title, log_x=log_x, log_y=log_y,
        trendline="ols" if len(df.dropna(subset=[x, y])) >= 3 else None,
        labels={x: x_title, y: y_title},
    )
    for trace in fig.data:
        if trace.mode == "lines":
            trace.name = "단순 추세선"
            trace.hovertemplate = "단순 추세선<extra></extra>"
    return fig


def stacked_bar_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str, y_title: str):
    """구성 누적막대그래프 (예: 복리후생 항목 구성, 수입구조 100% 누적)."""
    if df.empty or df[y].dropna().empty:
        return None
    fig = px.bar(df, x=x, y=y, color=color, title=title, labels={x: "연도", y: y_title, color: "항목"})
    fig.update_layout(barmode="stack")
    return fig


def box_plot_chart(df: pd.DataFrame, x: str, y: str, title: str, y_title: str):
    """기관유형별 분포 박스플롯."""
    if df.empty or df[y].dropna().empty:
        return None
    fig = px.box(df, x=x, y=y, title=title, labels={x: "기관유형", y: y_title})
    return fig


def comparison_bullet_chart(labels: list, values: list, title: str, unit: str):
    """레이더 차트 대신 사용하는 수평 막대(불릿형) 비교 차트."""
    if not labels:
        return None
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        text=[f"{v:,.1f}" if v is not None else "자료 없음" for v in values],
        hovertemplate="%{y}: %{x:,.1f} " + unit + "<extra></extra>",
    ))
    fig.update_layout(title=title, xaxis_title=unit)
    return fig


def grouped_bar_chart(df: pd.DataFrame, x: str, y: str, color: str, title: str, y_title: str):
    """청년/여성/장애인 채용처럼 중복 가능한 집단을 그룹 막대로 표시 (100% 누적 금지)."""
    if df.empty or df[y].dropna().empty:
        return None
    fig = px.bar(df, x=x, y=y, color=color, barmode="group", title=title,
                 labels={x: "연도", y: y_title, color: "구분"})
    return fig


# ============================================================================
# filters.py 내용
# ============================================================================
COMPARISON_OPTIONS = ["전체 기관", "동일 기관유형", "동일 주무부처"]


@dataclass
class FilterState:
    """선택된 공통 필터 값을 담는 데이터 클래스."""

    year: int | None = None
    institution_types: list = field(default_factory=list)
    ministries: list = field(default_factory=list)
    institution_name: str = "전체"
    comparison_basis: str = "전체 기관"


def render_common_filters(years: list, options: dict) -> FilterState:
    """상단 공통 필터를 한 줄로 배치하고 선택 결과를 FilterState 로 반환한다."""
    col1, col2, col3, col4, col5 = st.columns([1, 1.4, 1.4, 1.6, 1.2])

    with col1:
        year = st.selectbox("기준연도", years, index=0 if years else None, key="flt_year")

    with col2:
        institution_types = st.multiselect(
            "기관유형", options["institution_types"], default=[], key="flt_type",
            placeholder="전체 (선택 안 함 = 전체)",
        )

    with col3:
        ministries = st.multiselect(
            "주무부처", options["ministries"], default=[], key="flt_ministry",
            placeholder="전체 (선택 안 함 = 전체)",
        )

    with col4:
        institution_name = st.selectbox(
            "기관명", ["전체"] + options["institution_names"], index=0, key="flt_institution",
        )

    with col5:
        comparison_basis = st.selectbox("비교 기준", COMPARISON_OPTIONS, index=0, key="flt_comparison")

    return FilterState(
        year=year,
        institution_types=institution_types,
        ministries=ministries,
        institution_name=institution_name,
        comparison_basis=comparison_basis,
    )


def apply_common_filters(
    df: pd.DataFrame,
    master: pd.DataFrame,
    state: FilterState,
    apply_year: bool = True,
    apply_institution: bool = False,
) -> pd.DataFrame:
    """공통 필터 조건을 데이터프레임에 적용한다.

    기관유형/주무부처 필터는 기관 마스터를 통해 institution_name_raw 기준으로 적용한다.
    (각 도메인 데이터에도 institution_type/ministry 열이 있지만, 파일 간 표기가 다를 수 있어
    기관 마스터의 대표값을 우선 사용해 일관성을 확보한다.)
    """
    if df.empty:
        return df

    result = df.copy()

    if apply_year and "year" in result.columns and state.year is not None:
        result = result[result["year"] == state.year]

    if state.institution_types or state.ministries:
        allowed = master.copy()
        if state.institution_types:
            allowed = allowed[allowed["institution_type"].isin(state.institution_types)]
        if state.ministries:
            allowed = allowed[allowed["ministry"].isin(state.ministries)]
        allowed_names = set(allowed["institution_name"].dropna().tolist())
        result = result[result["institution_name_raw"].isin(allowed_names)]

    if apply_institution and state.institution_name != "전체":
        result = result[result["institution_name_raw"] == state.institution_name]

    return result


def show_no_data_message(context: str = "") -> None:
    """선택한 필터 조건에 해당하는 데이터가 없을 때 안내 메시지를 표시한다."""
    msg = "선택하신 조건에 해당하는 데이터가 없습니다."
    if context:
        msg += f" ({context})"
    st.info(msg)

# ============================================================================
# 데이터 로딩 (원본 엑셀을 직접 읽어서 정제 + 캐싱)
# ============================================================================

DATASET_NAMES = [
    "institution_master", "workforce", "recruitment", "employee_pay",
    "executive_pay", "executive_expense", "corporate_tax", "welfare",
    "other_welfare", "work_family", "finance",
]

_BUILDERS = {
    "workforce": process_workforce,
    "recruitment": process_recruitment,
    "employee_pay": process_employee_pay,
    "executive_pay": process_executive_pay,
    "executive_expense": process_executive_expense,
    "corporate_tax": process_corporate_tax,
    "welfare": process_welfare,
    "other_welfare": process_other_welfare,
    "work_family": process_work_family,
    "finance": process_finance,
}


def raw_files_exist() -> bool:
    """이 파일과 같은 폴더에 원본 엑셀이 있는지 확인한다."""
    return any(RAW_DIR.glob("*.xlsx"))


def show_missing_data_guide() -> None:
    """원본 엑셀을 찾을 수 없을 때 안내 메시지를 표시한다."""
    st.error("원본 엑셀 파일을 찾을 수 없습니다. 이 파일(common_data.py)과 같은 폴더에 엑셀 10개를 넣어주세요.")
    st.code(
        "그밖의_복리후생제도_등의_운영현황.xlsx\n기관장업무추진비.xlsx\n법인세정보.xlsx\n복리후생비.xlsx\n"
        "수입지출현황.xlsx\n신규채용현황.xlsx\n일가정_양립_지원제도_운영현황.xlsx\n임원연봉.xlsx\n"
        "임직원수현황.xlsx\n직원평균보수현황.xlsx",
        language="text",
    )


@st.cache_data(show_spinner="원본 엑셀에서 데이터를 정제하는 중입니다 (최초 1회만 수행)...")
def load_all_datasets() -> dict:
    """원본 엑셀 10개를 직접 읽어 정제한 뒤 딕셔너리로 반환한다 (Streamlit 캐시 적용)."""
    results = {}
    for name, func in _BUILDERS.items():
        try:
            results[name] = func()
        except Exception as exc:  # noqa: BLE001
            logger.error("전처리 실패 (건너뜀): %s / 사유: %s", name, exc)
            results[name] = pd.DataFrame()
    results["institution_master"] = build_institution_master(results)
    return results


def get_available_years(datasets: dict) -> list:
    """모든 데이터셋에 실제 존재하는 연도 목록(내림차순)을 반환한다."""
    years = set()
    for df in datasets.values():
        if "year" in df.columns:
            years.update(df["year"].dropna().unique().tolist())
    return sorted((int(y) for y in years), reverse=True)


def get_filter_options(master: pd.DataFrame) -> dict:
    """기관유형/주무부처/기관명 필터 선택지를 기관 마스터 테이블에서 추출한다."""
    if master.empty:
        return {"institution_types": [], "ministries": [], "institution_names": []}
    return {
        "institution_types": sorted(master["institution_type"].dropna().unique().tolist()),
        "ministries": sorted(master["ministry"].dropna().unique().tolist()),
        "institution_names": sorted(master["institution_name"].dropna().unique().tolist()),
    }


def setup_page(title_suffix: str = "") -> None:
    """모든 페이지 파일 상단에서 공통으로 호출하는 페이지 설정 + 강의실용 CSS."""
    st.set_page_config(
        page_title="공공기관 경영정보 대시보드" + (f" - {title_suffix}" if title_suffix else ""),
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
            .block-container {padding-top: 1rem; padding-bottom: 1rem; max-width: 100% !important;}
            h1 {font-size: 2.1rem !important;}
            div[data-testid="stMetricLabel"] {font-size: 1.05rem !important;}
            div[data-testid="stMetricValue"] {font-size: 1.7rem !important;}
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_data_or_stop() -> dict:
    """데이터를 로드한다. 원본 엑셀이 없으면 안내 메시지를 띄우고 페이지 실행을 멈춘다."""
    if not raw_files_exist():
        show_missing_data_guide()
        st.stop()
    return load_all_datasets()
