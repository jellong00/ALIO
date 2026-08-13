# -*- coding: utf-8 -*-
"""
공통 필터 UI 컴포넌트
======================
연도 / 기관유형 / 기관명 / 주무부처 필터를 표준화된 형태로 제공한다.
데이터에 존재하지 않는 필터는 표시하지 않는다.
"""

import streamlit as st
from utils.constants import DEFAULT_YEAR, YEAR_2026_WARNING


def render_common_filters(df, key_prefix="", show_institution=True, show_dept=False, container=None):
    """
    연도 / 기관유형 / (선택)기관명 / (선택)주무부처 필터를 렌더링하고
    선택된 값을 dict로 반환한다.

    df에 해당 컬럼이 없으면 그 필터는 표시하지 않는다.
    """
    c = container if container is not None else st
    result = {}

    cols = c.columns(4 if show_dept else 3)
    idx = 0

    # 연도
    if "연도" in df.columns:
        years = sorted(df["연도"].dropna().unique().astype(int), reverse=True)
        default_year = DEFAULT_YEAR if DEFAULT_YEAR in years else (years[0] if years else None)
        with cols[idx]:
            year = st.selectbox("연도", years, index=years.index(default_year) if default_year in years else 0, key=f"{key_prefix}_year")
        result["연도"] = year
        if year == 2026:
            c.caption(f"⚠️ {YEAR_2026_WARNING}")
        idx += 1

    # 기관유형
    if "기관유형" in df.columns:
        types = ["전체"] + sorted(df["기관유형"].dropna().unique().tolist())
        with cols[idx]:
            inst_type = st.selectbox("기관유형", types, index=0, key=f"{key_prefix}_type")
        result["기관유형"] = inst_type
        idx += 1

    # 주무부처
    if show_dept and "주무부처" in df.columns:
        depts = ["전체"] + sorted(df["주무부처"].dropna().unique().tolist())
        with cols[idx]:
            dept = st.selectbox("주무부처", depts, index=0, key=f"{key_prefix}_dept")
        result["주무부처"] = dept
        idx += 1

    # 기관명 (검색 가능한 selectbox)
    if show_institution and "기관명" in df.columns:
        names = ["전체"] + sorted(df["기관명"].dropna().unique().tolist())
        with cols[idx]:
            name = st.selectbox("기관명", names, index=0, key=f"{key_prefix}_name")
        result["기관명"] = name

    return result


def apply_filters(df, filters: dict):
    """render_common_filters 결과를 받아 DataFrame에 실제로 필터를 적용한다."""
    out = df.copy()
    if filters.get("연도") is not None and "연도" in out.columns:
        out = out[out["연도"] == filters["연도"]]
    if filters.get("기관유형") and filters["기관유형"] != "전체" and "기관유형" in out.columns:
        out = out[out["기관유형"] == filters["기관유형"]]
    if filters.get("주무부처") and filters["주무부처"] != "전체" and "주무부처" in out.columns:
        out = out[out["주무부처"] == filters["주무부처"]]
    if filters.get("기관명") and filters["기관명"] != "전체" and "기관명" in out.columns:
        out = out[out["기관명"] == filters["기관명"]]
    return out
