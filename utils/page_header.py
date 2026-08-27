"""
page_header.py
--------------
모든 페이지에서 공통으로 사용하는:
1) 표준 안내 박스 (분석목적 / 분석단위 / 주요 분석방법 / 해석 시 주의)
2) 분석단위(연도) 선택기 — 기관-연도 패널을 횡단면처럼 다루는 문제를 방지하기 위해
   기술통계·집단비교·상관분석 페이지에서는 기본적으로 '단일 연도' 단면을 사용하도록 강제한다.
"""

import streamlit as st
import pandas as pd


def render_intro(purpose: str, unit: str, methods: str, caution: str):
    st.markdown(
        f"""
<div style="background:#F3F6FA; border:1px solid #D8E0EA; border-radius:10px; padding:14px 18px; margin-bottom:8px; font-size:0.95rem; line-height:1.7;">
<b>🎯 분석목적</b> · {purpose}<br>
<b>📏 분석단위</b> · {unit}<br>
<b>🔧 주요 분석방법</b> · {methods}<br>
<b>⚠️ 해석 시 주의</b> · {caution}
</div>
""",
        unsafe_allow_html=True,
    )


def year_slice(df: pd.DataFrame, key_prefix: str, default_mode: str = "최신연도"):
    """분석단위(연도)를 선택하게 하고, 그에 맞게 잘라낸 df와 설명 캡션을 반환한다.

    반환: (view_df, caption_text, mode)
    - '최신연도' / '특정연도' 선택 시: 기관-연도 패널을 진짜 횡단면(기관당 1행)으로 축소한다.
      이때 N은 '기관 수'와 정확히 같다.
    - '전체 기간(모든 연도 pooled)' 선택 시: 여러 연도의 동일 기관 관측치가 모두 포함되므로
      N은 '기관-연도 관측치 수'이지 기관 수가 아니라는 경고를 함께 표시한다.
    """
    years = sorted(df["연도"].unique())
    mode = st.radio(
        "분석단위(연도) 선택",
        ["최신연도", "특정연도", "전체 기간(기관-연도 pooled)"],
        horizontal=True, key=f"{key_prefix}_yearmode",
        index=["최신연도", "특정연도", "전체 기간(기관-연도 pooled)"].index(default_mode),
    )

    if mode == "최신연도":
        idx = df.groupby("기관명")["연도"].idxmax()
        view = df.loc[idx].reset_index(drop=True)
        n_org = view["기관명"].nunique()
        caption = f"📏 기관마다 필터링된 범위 내 가장 최근 연도 값 1개를 사용합니다. N = 기관 수 = {n_org:,}개"
        return view, caption, mode

    if mode == "특정연도":
        sel_year = st.selectbox("연도 선택", years, index=len(years) - 1, key=f"{key_prefix}_year")
        view = df[df["연도"] == sel_year].drop_duplicates(subset=["기관명"])
        n_org = view["기관명"].nunique()
        caption = f"📏 {sel_year}년 횡단면입니다. N = 기관 수 = {n_org:,}개"
        return view, caption, mode

    # 전체 기간 pooled
    view = df
    n_row = view.shape[0]
    n_org = view["기관명"].nunique()
    caption = (f"⚠️ 여러 연도의 동일 기관이 반복 포함됩니다(pooled 기관-연도 자료). "
               f"N = 기관-연도 관측치 수 = {n_row:,}건 (기관 수는 {n_org:,}개)이며, 이는 독립표본이 아닙니다.")
    return view, caption, mode
