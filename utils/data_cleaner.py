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


def describe_var(df: pd.DataFrame, col: str) -> dict:
    """변수 하나에 대한 기술통계 딕셔너리."""
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if s.empty:
        return {"N": 0}
    return {
        "N": int(s.shape[0]),
        "평균": s.mean(),
        "중앙값": s.median(),
        "표준편차": s.std(),
        "최소": s.min(),
        "최대": s.max(),
        "Q1": s.quantile(0.25),
        "Q3": s.quantile(0.75),
        "결측률": 1 - s.shape[0] / df.shape[0] if df.shape[0] else 0,
    }
