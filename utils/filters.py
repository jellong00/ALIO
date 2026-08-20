"""
filters.py
----------
모든 페이지에서 공통으로 사용하는 사이드바 필터.
연도 / 기관유형 / 주무부처 / 기관명 순으로 연동 필터를 제공한다.
"""

import streamlit as st
import pandas as pd


def sidebar_filters(df: pd.DataFrame, key_prefix: str = ""):
    st.sidebar.markdown("### 🔎 필터")

    years = sorted(df["연도"].unique())
    sel_years = st.sidebar.multiselect(
        "연도", years, default=years, key=f"{key_prefix}_years"
    )

    org_types = sorted(df["기관유형"].unique())
    sel_types = st.sidebar.multiselect(
        "기관유형", org_types, default=org_types, key=f"{key_prefix}_types"
    )

    filtered_for_dept = df[df["기관유형"].isin(sel_types)] if sel_types else df
    depts = sorted(filtered_for_dept["주무부처"].unique())
    sel_depts = st.sidebar.multiselect(
        "주무부처", depts, default=depts, key=f"{key_prefix}_depts"
    )

    filtered_for_org = filtered_for_dept[filtered_for_dept["주무부처"].isin(sel_depts)] if sel_depts else filtered_for_dept
    orgs = sorted(filtered_for_org["기관명"].unique())
    sel_orgs = st.sidebar.multiselect(
        "기관명 (미선택 시 전체)", orgs, default=[], key=f"{key_prefix}_orgs"
    )

    out = df.copy()
    if sel_years:
        out = out[out["연도"].isin(sel_years)]
    if sel_types:
        out = out[out["기관유형"].isin(sel_types)]
    if sel_depts:
        out = out[out["주무부처"].isin(sel_depts)]
    if sel_orgs:
        out = out[out["기관명"].isin(sel_orgs)]

    st.sidebar.caption(f"현재 필터: 기관-연도 관측치 {out.shape[0]:,}건 · 기관 {out['기관명'].nunique():,}개")

    return out
