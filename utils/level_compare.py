"""
level_compare.py
-----------------
'전체 기관 → 기관유형 → 주무부처 → 개별 기관' 4단계 비교체계를 위한 공통 함수 모음.
여러 페이지에서 동일한 로직을 재사용하기 위해 분리했다.
"""

import pandas as pd
import numpy as np

from utils.data_cleaner import percentile_rank


def dept_stats_table(df: pd.DataFrame, col: str, min_n: int = 1) -> pd.DataFrame:
    """주무부처별 N·평균·중앙값·표준편차 테이블. 기관 수가 적은 부처를 걸러낼 수 있다."""
    s = df[[col, "주무부처"]].dropna()
    grp = s.groupby("주무부처")[col].agg(["count", "mean", "median", "std"]).reset_index()
    grp.columns = ["주무부처", "N", "평균", "중앙값", "표준편차"]
    grp = grp[grp["N"] >= min_n].sort_values("평균", ascending=False)
    return grp


def four_level_values(df: pd.DataFrame, col: str, org_name: str) -> dict:
    """선택 기관의 값과, 전체/동일유형/동일부처 평균·백분위를 반환한다.
    기관값은 필터링된 범위 내 해당 기관의 가장 최근 연도 값을 사용한다."""
    org_rows = df[df["기관명"] == org_name].dropna(subset=[col])
    if org_rows.empty:
        return None
    org_row = org_rows.sort_values("연도").iloc[-1]
    org_val = org_row[col]
    org_type = org_row["기관유형"]
    org_dept = org_row["주무부처"]

    same_type = df[df["기관유형"] == org_type][col]
    same_dept = df[df["주무부처"] == org_dept][col]

    return {
        "기관명": org_name, "기관유형": org_type, "주무부처": org_dept,
        "기관값": org_val,
        "전체평균": pd.to_numeric(df[col], errors="coerce").mean(),
        "동일유형평균": pd.to_numeric(same_type, errors="coerce").mean(),
        "동일부처평균": pd.to_numeric(same_dept, errors="coerce").mean(),
        "전체백분위": percentile_rank(df[col], org_val),
        "동일유형백분위": percentile_rank(same_type, org_val),
        "동일부처백분위": percentile_rank(same_dept, org_val),
    }


def cross_table(df: pd.DataFrame, col: str, row_col: str = "주무부처", col_col: str = "기관유형",
                 agg: str = "mean", min_n: int = 1) -> tuple:
    """주무부처 × 기관유형 교차 평균표와, 각 셀의 관측치 수(N) 표를 함께 반환한다."""
    s = df[[col, row_col, col_col]].dropna()
    pivot_val = s.pivot_table(index=row_col, columns=col_col, values=col, aggfunc=agg)
    pivot_n = s.pivot_table(index=row_col, columns=col_col, values=col, aggfunc="count")
    row_totals = s.groupby(row_col)[col].count()
    keep_rows = row_totals[row_totals >= min_n].index
    return pivot_val.loc[pivot_val.index.intersection(keep_rows)], pivot_n.loc[pivot_n.index.intersection(keep_rows)]


def render_four_level_panel(st, df: pd.DataFrame, col: str, label: str, unit: str, org_name: str):
    """선택 기관의 값 · 동일유형 평균 · 동일부처 평균 · 전체 평균과 각 수준 백분위를 함께 표시한다.
    streamlit 모듈(st)을 인자로 받아 utils 모듈이 streamlit에 직접 의존하지 않도록 한다."""
    vals = four_level_values(df, col, org_name)
    if not vals:
        st.info("선택한 기관에 유효한 값이 없습니다.")
        return
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("전체 평균", f"{vals['전체평균']:,.1f} {unit}" if pd.notna(vals['전체평균']) else "N/A")
    m2.metric(f"동일유형 평균", f"{vals['동일유형평균']:,.1f} {unit}" if pd.notna(vals['동일유형평균']) else "N/A")
    m3.metric(f"동일부처 평균", f"{vals['동일부처평균']:,.1f} {unit}" if pd.notna(vals['동일부처평균']) else "N/A")
    m4.metric(f"{org_name}", f"{vals['기관값']:,.1f} {unit}" if pd.notna(vals['기관값']) else "N/A")
    p1, p2, p3 = st.columns(3)
    p1.metric("전체 백분위", f"상위 {vals['전체백분위']:.0f}%" if vals['전체백분위'] is not None else "N/A")
    p2.metric("동일유형 내 백분위", f"상위 {vals['동일유형백분위']:.0f}%" if vals['동일유형백분위'] is not None else "N/A")
    p3.metric("동일부처 내 백분위", f"상위 {vals['동일부처백분위']:.0f}%" if vals['동일부처백분위'] is not None else "N/A")
