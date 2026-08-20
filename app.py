import streamlit as st
from utils.data_cleaner import get_full_panel

st.set_page_config(
    page_title="공공기관 계량분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 공공기관 계량분석 대시보드")
st.markdown(
    "##### 기관 특성 · 재정 구조 · 조직 운영 · 인사 결과를 연결한 공공기관 데이터 분석"
)
st.divider()

with st.spinner("데이터를 불러오는 중입니다..."):
    panel = get_full_panel()

col1, col2 = st.columns([1.1, 1])

with col1:
    st.markdown("### 분석 프레임")
    st.markdown(
        """
<div style="line-height:2.1; font-size:1.05rem;">

<div style="background:#EEF3FB; border:2px solid #4C78A8; border-radius:10px; padding:14px 18px; margin-bottom:6px;">
<b>① 기관 특성</b><br>
<span style="color:#555;">기관유형 · 주무부처 · 기관규모 · 인력구조</span>
</div>

<div style="text-align:center; font-size:1.4rem; color:#4C78A8;">↓</div>

<div style="background:#FBF3EE; border:2px solid #E07B39; border-radius:10px; padding:14px 18px; margin-bottom:6px;">
<b>② 재정 구조</b><br>
<span style="color:#555;">총수입 · 총지출 · 정부지원의존도 · 법인세</span>
</div>

<div style="text-align:center; font-size:1.4rem; color:#E07B39;">↓</div>

<div style="background:#EEFBF1; border:2px solid #2CA02C; border-radius:10px; padding:14px 18px; margin-bottom:6px;">
<b>③ 조직 운영</b><br>
<span style="color:#555;">직원·임원 보수 · 복리후생 · 기관장업무추진비</span>
</div>

<div style="text-align:center; font-size:1.4rem; color:#2CA02C;">↓</div>

<div style="background:#F5EEFB; border:2px solid #9467BD; border-radius:10px; padding:14px 18px;">
<b>④ 인사 결과</b><br>
<span style="color:#555;">신규채용 · 여성채용 · 육아휴직 · 일가정 양립</span>
</div>

</div>
""",
        unsafe_allow_html=True,
    )

with col2:
    st.info(
        "⚠️ **이 흐름은 인과관계를 전제하지 않습니다.**\n\n"
        "데이터에서 관찰되는 차이와 관계를 탐색하고, 계량모형을 이용하여 "
        "어떤 관계가 다른 조건을 통제한 후에도 유지되는지 검토하기 위한 "
        "**분석 가설 프레임**입니다.\n\n"
        "회귀분석 결과의 통계적 유의성은 인과효과를 자동으로 의미하지 않습니다."
    )
    st.markdown("### 데이터 개요")
    m1, m2, m3 = st.columns(3)
    m1.metric("기관 수", f"{panel['기관명'].nunique():,}개")
    m2.metric("연도 범위", f"{panel['연도'].min()}–{panel['연도'].max()}")
    m3.metric("기관-연도 관측치", f"{panel.shape[0]:,}건")

    st.markdown("### 페이지 안내")
    st.markdown(
        """
1. **기관유형 비교** — 4개 영역 전체를 기관유형별로 한눈에 비교
2. **기관특성** — 임직원수·여성비율·근속연수 상세 탐색
3. **재정구조** — 수입·지출·정부지원·법인세 구조 탐색
4. **조직운영** — 보수·임원·복리후생·업무추진비 탐색
5. **인사결과** — 채용·육아휴직·일가정양립 지표 탐색
6. **변수관계 탐색** — 4개 영역을 자유롭게 연결하는 산점도·상관행렬
7. **회귀분석** — 통제변수를 단계적으로 추가하는 다중회귀
8. **패널데이터** — 기관별 시계열 변화와 고정효과 회귀
        """
    )

st.divider()
st.caption(
    "좌측 사이드바 **Pages** 메뉴에서 각 분석 페이지로 이동하세요. "
    "모든 페이지의 필터(연도·기관유형·주무부처·기관명)는 서로 연동됩니다."
)
