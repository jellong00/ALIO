# -*- coding: utf-8 -*-
"""
홈 - 공공기관을 숫자로 읽다
============================
단순 데이터 소개가 아니라, 이 대시보드를 어떤 방식으로 활용할지 안내하는
수업용 진입 화면.
"""

import streamlit as st

from common_data import load_dataset, raw_files_exist
from utils.style import page_setup
from utils.variables import ALL_VARIABLES
from utils.questions import HOME_QUESTIONS, CORE_CONCEPTS

page_setup("🏛️ 공공기관을 숫자로 읽다")

st.markdown("#### 공공기관 경영정보를 이용한 계량분석 데이터 탐색")
st.write(
    "기관의 규모, 고용, 보수, 복지, 수입·지출, 정부지원, 법인세 정보를 결합하여 "
    "공공기관 간 차이와 변수 간 관계를 살펴봅니다."
)

if not raw_files_exist():
    st.warning("⚠️ `data/` 폴더에 필요한 원본 Excel 파일이 없습니다. README.md를 참고해 파일을 넣어주세요.")
    st.stop()

panel = load_dataset("panel")
if panel.empty:
    st.stop()

# ---------------------------------------------------------------------------
# 데이터 규모 KPI
# ---------------------------------------------------------------------------
k1, k2, k3, k4 = st.columns(4)
k1.metric("분석 기관 수", f"{panel['기관명'].nunique():,}")
k2.metric("분석 연도", f"{int(panel['연도'].min())}–{int(panel['연도'].max())}")
k3.metric("전체 관측치 수(기관×연도)", f"{len(panel):,}")
k4.metric("사용 가능한 핵심 변수 수", f"{len(ALL_VARIABLES)}")

st.divider()

# ---------------------------------------------------------------------------
# 데이터 영역 소개
# ---------------------------------------------------------------------------
st.markdown("###### 이 대시보드가 다루는 데이터 영역")
areas = [
    ("인력·채용", "임직원 수, 정원충족률, 신규채용률, 여성·청년·장애인 채용"),
    ("보수·임원", "직원 평균보수, 신입초임, 근속연수, 기관장 연봉, 보수배율"),
    ("복지·일가정", "1인당 복리후생비, 육아휴직 이용률, 직장어린이집"),
    ("수입·지출", "총수입·총지출 구조, 정부지원수입, 사업수입, 인건비"),
    ("정부지원", "정부지원 의존도, 자체수입(보수적/광의)"),
    ("법인세", "과세표준, 산출세액, 세액공제, 결정세액"),
]
cols = st.columns(6)
for col, (title, desc) in zip(cols, areas):
    with col:
        st.markdown(f"**{title}**")
        st.caption(desc)

st.divider()

# ---------------------------------------------------------------------------
# 수업에서 살펴볼 핵심 개념
# ---------------------------------------------------------------------------
st.markdown("###### 수업에서 살펴볼 핵심 개념")
cc_cols = st.columns(3)
for i, (title, desc) in enumerate(CORE_CONCEPTS):
    with cc_cols[i % 3]:
        with st.container(border=True):
            st.markdown(f"**{title}**")
            st.caption(desc)

st.divider()

# ---------------------------------------------------------------------------
# 흥미로운 질문
# ---------------------------------------------------------------------------
st.markdown("###### 이런 질문들을 함께 탐색해볼 수 있습니다")
st.info("\n\n".join(f"- {q}" for q in HOME_QUESTIONS))

st.caption("왼쪽 메뉴에서 살펴보고 싶은 화면을 선택하세요.")
