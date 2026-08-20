# -*- coding: utf-8 -*-
"""
공통 스타일
============
강의실 대형화면(1920x1080)에서 스크롤 없이 보이도록 하는 CSS와
Plotly 공통 레이아웃 상수를 관리한다.
"""

import streamlit as st

CHART_HEIGHT = 260
CHART_HEIGHT_MAIN = 380

BASE_PLOTLY_LAYOUT = dict(
    template="plotly_white",
    font=dict(size=13),
    title_font_size=18,
    legend_font_size=12,
    margin=dict(l=40, r=20, t=45, b=35),
)


def inject_css():
    st.markdown(
        """
        <style>
        .block-container {padding-top: 1.1rem; padding-bottom: 1rem; max-width: 100%;}
        [data-testid="stMetricValue"] {font-size: 1.3rem;}
        [data-testid="stMetricLabel"] {font-size: 0.8rem; opacity: 0.85;}
        .stTabs [data-baseweb="tab"] {font-size: 1.02rem; padding: 0.45rem 1rem;}
        .stTabs [data-baseweb="tab-list"] {gap: 0.15rem;}
        div[data-testid="stVerticalBlock"] > div {gap: 0.5rem;}
        h1 {font-size: 1.6rem !important;}
        h2 {font-size: 1.25rem !important;}
        h3 {font-size: 1.05rem !important;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_setup(title_icon_label: str):
    """모든 페이지 상단에서 공통으로 호출: 페이지 설정 + CSS + 작은 제목."""
    st.set_page_config(page_title=title_icon_label, layout="wide", initial_sidebar_state="expanded")
    inject_css()
    st.markdown(f"##### {title_icon_label}")
