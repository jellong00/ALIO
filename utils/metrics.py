"""
metrics.py
----------
기관-연도 패널에 파생변수(비율, 1인당 지표 등)를 계산해 추가한다.
분모가 0이거나 결측이면 NaN으로 처리한다 (임의로 0 대입 금지).
"""

import numpy as np
import pandas as pd


def _safe_div(numer, denom, mult=1.0):
    numer = pd.to_numeric(numer, errors="coerce")
    denom = pd.to_numeric(denom, errors="coerce")
    result = numer / denom.replace(0, np.nan)
    return result * mult


def add_derived_variables(panel: pd.DataFrame) -> pd.DataFrame:
    df = panel.copy()

    # ---------------- 기관 특성 ----------------
    df["여성직원비율"] = _safe_div(df.get("여성현원"), df.get("임직원수"), 100)

    # 기관 규모: 임직원수 기준 3분위(로그 스케일) — 대시보드에서 라벨링
    df["임직원수_log"] = np.log1p(df.get("임직원수"))

    # ---------------- 재정 구조 ----------------
    df["정부지원의존도"] = _safe_div(df.get("정부지원수입"), df.get("총수입"), 100)
    df["1인당총수입"] = _safe_div(df.get("총수입"), df.get("임직원수"))
    df["1인당총지출"] = _safe_div(df.get("총지출"), df.get("임직원수"))
    df["수입지출차이"] = pd.to_numeric(df.get("총수입"), errors="coerce") - pd.to_numeric(df.get("총지출"), errors="coerce")
    df["1인당사업수입"] = _safe_div(df.get("사업수입"), df.get("임직원수"))

    실효세율 = _safe_div(df.get("법인세결정세액"), df.get("과세표준"), 100)
    if "과세표준" in df.columns:
        실효세율 = 실효세율.where(pd.to_numeric(df["과세표준"], errors="coerce") > 0, np.nan)
    df["실효법인세율"] = 실효세율

    # ---------------- 조직 운영 ----------------
    df["1인당복리후생비"] = _safe_div(df.get("복리후생비"), df.get("임직원수"))
    df["기관장직원보수배율"] = _safe_div(df.get("기관장연봉"), df.get("직원평균보수"))
    df["1인당기관장업무추진비"] = _safe_div(df.get("기관장업무추진비"), df.get("임직원수"))

    # ---------------- 인사 결과 ----------------
    df["신규채용률"] = _safe_div(df.get("신규채용자수"), df.get("임직원수"), 100)
    df["여성신규채용비율"] = _safe_div(df.get("여성신규채용자수"), df.get("신규채용자수"), 100)
    df["청년채용비율"] = _safe_div(df.get("청년신규채용자수"), df.get("신규채용자수"), 100)

    return df


def add_growth_variables(panel: pd.DataFrame, vars_to_grow) -> pd.DataFrame:
    """기관별로 정렬한 뒤 전년 대비 증가율(%)을 계산한다 (패널데이터 페이지용)."""
    df = panel.sort_values(["기관명", "연도"]).copy()
    for v in vars_to_grow:
        if v not in df.columns:
            continue
        df[f"{v}_증가율"] = df.groupby("기관명")[v].pct_change() * 100
    return df
