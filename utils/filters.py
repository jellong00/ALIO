# -*- coding: utf-8 -*-
"""
종속형 공통 필터
================
연도 | 기관유형 | 주무부처 | 기관명 순서로 종속되는 필터.
모든 페이지에서 동일한 session_state 키("filt_*")를 사용하므로,
페이지를 이동해도(멀티페이지 앱) 선택한 필터가 그대로 유지된다.
상위 필터가 바뀌면 하위 선택은 자동으로 "전체"로 초기화된다.
"""

import streamlit as st

from utils.constants import DEFAULT_YEAR, YEAR_2026_WARNING

YEAR_KEY = "filt_year"
TYPE_KEY = "filt_type"
DEPT_KEY = "filt_dept"
INST_KEY = "filt_inst"


def render_cascading_filters(df, show_year=True):
    def _reset_dept_and_inst():
        st.session_state[DEPT_KEY] = "전체"
        st.session_state[INST_KEY] = "전체"

    def _reset_inst():
        st.session_state[INST_KEY] = "전체"

    n_cols = 4 if show_year else 3
    cols = st.columns(n_cols)
    result = {}
    idx = 0

    if show_year and "연도" in df.columns:
        years = sorted(df["연도"].dropna().unique().astype(int), reverse=True)
        default_year = DEFAULT_YEAR if DEFAULT_YEAR in years else years[0]
        if st.session_state.get(YEAR_KEY) not in years:
            st.session_state[YEAR_KEY] = default_year
        with cols[idx]:
            year = st.selectbox("연도", years, key=YEAR_KEY)
        result["연도"] = year
        if year == 2026:
            st.caption(f"⚠️ {YEAR_2026_WARNING}")
        idx += 1

    type_options = ["전체"] + sorted(df["기관유형"].dropna().unique().tolist())
    if st.session_state.get(TYPE_KEY, "전체") not in type_options:
        st.session_state[TYPE_KEY] = "전체"
    with cols[idx]:
        inst_type = st.selectbox("기관유형", type_options, key=TYPE_KEY, on_change=_reset_dept_and_inst)
    result["기관유형"] = inst_type
    idx += 1

    df_by_type = df if inst_type == "전체" else df[df["기관유형"] == inst_type]
    dept_options = ["전체"] + sorted(df_by_type["주무부처"].dropna().unique().tolist())
    if st.session_state.get(DEPT_KEY, "전체") not in dept_options:
        st.session_state[DEPT_KEY] = "전체"
    with cols[idx]:
        dept = st.selectbox("주무부처", dept_options, key=DEPT_KEY, on_change=_reset_inst)
    result["주무부처"] = dept
    idx += 1

    df_by_dept = df_by_type if dept == "전체" else df_by_type[df_by_type["주무부처"] == dept]
    inst_options = ["전체"] + sorted(df_by_dept["기관명"].dropna().unique().tolist())
    if st.session_state.get(INST_KEY, "전체") not in inst_options:
        st.session_state[INST_KEY] = "전체"
    with cols[idx]:
        inst = st.selectbox("기관명", inst_options, key=INST_KEY)
    result["기관명"] = inst

    return result


def apply_filters(df, filters: dict):
    out = df.copy()
    if filters.get("연도") is not None and "연도" in out.columns:
        out = out[out["연도"] == filters["연도"]]
    if filters.get("기관유형") not in (None, "전체") and "기관유형" in out.columns:
        out = out[out["기관유형"] == filters["기관유형"]]
    if filters.get("주무부처") not in (None, "전체") and "주무부처" in out.columns:
        out = out[out["주무부처"] == filters["주무부처"]]
    if filters.get("기관명") not in (None, "전체") and "기관명" in out.columns:
        out = out[out["기관명"] == filters["기관명"]]
    return out
