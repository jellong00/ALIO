"""
data_cleaner.py
----------------
data_loader의 원자료 결합 결과에 파생변수를 추가하고,
분석에 바로 사용할 수 있는 최종 패널을 캐싱하여 제공한다.
"""

import streamlit as st
import pandas as pd

from utils.data_loader import build_panel
from utils.metrics import add_derived_variables


@st.cache_data(show_spinner="데이터를 불러오는 중입니다...")
def get_full_panel() -> pd.DataFrame:
    panel = build_panel()
    panel = add_derived_variables(panel)
    return panel


def n_obs(series: pd.Series) -> int:
    """결측치를 제외한 관측치 수."""
    return int(series.dropna().shape[0])


def latest_snapshot(df: pd.DataFrame, entity_col: str = "기관명", year_col: str = "연도") -> pd.DataFrame:
    """기관별로 (현재 필터링된 범위 내) 가장 최근 연도의 행 1개만 남긴 스냅샷을 반환한다.
    Top/Bottom 순위처럼 '기관' 단위 비교가 필요한 곳에서 동일 기관이 여러 연도로 중복 표시되는 것을 방지한다."""
    if df.empty:
        return df
    idx = df.groupby(entity_col)[year_col].idxmax()
    return df.loc[idx].reset_index(drop=True)


def percentile_rank(series: pd.Series, value) -> float:
    """value가 series 내에서 상위 몇 %에 해당하는지 반환 (낮을수록 상위)."""
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty or pd.isna(value):
        return None
    pct_below_or_equal = (s <= value).mean()
    return round((1 - pct_below_or_equal) * 100, 1)


def describe_var(df: pd.DataFrame, col: str) -> dict:
    """변수 하나에 대한 기술통계 딕셔너리."""
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    n_missing = df.shape[0] - s.shape[0]
    if s.empty:
        return {"N": 0}
    return {
        "N": int(s.shape[0]),
        "결측치수": int(n_missing),
        "평균": s.mean(),
        "중앙값": s.median(),
        "표준편차": s.std(),
        "최소": s.min(),
        "최대": s.max(),
        "Q1": s.quantile(0.25),
        "Q3": s.quantile(0.75),
        "결측률": n_missing / df.shape[0] if df.shape[0] else 0,
    }
