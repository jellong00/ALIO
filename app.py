import streamlit as st
import pandas as pd

from utils.data_cleaner import get_full_panel
from utils.variables import VARIABLES

st.set_page_config(
    page_title="공공기관 계량분석 대시보드",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("📊 공공기관 계량분석 대시보드")
st.markdown("##### 실제 공공기관 데이터로 질문을 만들고, 분포를 확인하고, 관계를 탐색하는 기초계량분석 실습 대시보드")
st.divider()

with st.spinner("데이터를 불러오는 중입니다..."):
    panel = get_full_panel()

used_cols = {v["column"] for v in VARIABLES.values() if v["column"] in panel.columns}

m1, m2, m3, m4 = st.columns(4)
m1.metric("분석기관 수", f"{panel['기관명'].nunique():,}개")
m2.metric("연도 범위", f"{panel['연도'].min()}–{panel['연도'].max()}")
m3.metric("기관-연도 관측치", f"{panel.shape[0]:,}건")
m4.metric("결합된 변수 수", f"{len(used_cols):,}개")

st.divider()

# ---------------- 실데이터 기반 흥미유도 질문 ----------------
st.markdown("### 🤔 이 데이터로 답할 수 있는 질문들")

latest_year = panel["연도"].max()
earliest_year = panel["연도"].min()
snap = panel[panel["연도"] == latest_year]


def safe_ratio_top():
    if "기관장직원보수배율" in snap.columns:
        s = snap[["기관명", "기관장직원보수배율"]].dropna()
        if not s.empty:
            row = s.loc[s["기관장직원보수배율"].idxmax()]
            return row["기관명"], row["기관장직원보수배율"]
    return None, None


def safe_gov_compare():
    if "정부지원수입" in snap.columns and "정부지원의존도" in snap.columns:
        s1 = snap[["기관명", "정부지원수입"]].dropna()
        s2 = snap[["기관명", "정부지원의존도"]].dropna()
        if not s1.empty and not s2.empty:
            top_amt = s1.loc[s1["정부지원수입"].idxmax(), "기관명"]
            top_ratio = s2.loc[s2["정부지원의존도"].idxmax(), "기관명"]
            return top_amt, top_ratio
    return None, None


def safe_female_leave_by_type():
    if "여성육아휴직사용자수" in panel.columns:
        s = panel.groupby("기관유형")["여성육아휴직사용자수"].mean().dropna()
        if not s.empty:
            return s.idxmax(), s.max()
    return None, None


def safe_salary_growth_top():
    col = "직원평균보수"
    if col in panel.columns:
        first = panel[panel["연도"] == earliest_year][["기관명", col]].dropna().rename(columns={col: "초기값"})
        last = panel[panel["연도"] == latest_year][["기관명", col]].dropna().rename(columns={col: "최근값"})
        merged = pd.merge(first, last, on="기관명")
        merged = merged[merged["초기값"] > 0]
        if not merged.empty:
            merged["증가율"] = (merged["최근값"] - merged["초기값"]) / merged["초기값"] * 100
            row = merged.loc[merged["증가율"].idxmax()]
            return row["기관명"], row["증가율"]
    return None, None


q_org, q_ratio = safe_ratio_top()
q_amt_org, q_ratio_org = safe_gov_compare()
q_type, q_type_rate = safe_female_leave_by_type()
q_growth_org, q_growth_rate = safe_salary_growth_top()

qc1, qc2 = st.columns(2)
qc3, qc4 = st.columns(2)

with qc1:
    if q_org:
        st.info(f"💰 **기관장 연봉이 직원 평균보수의 몇 배?** — {latest_year}년 기준 **{q_org}**이(가) "
                f"**{q_ratio:.1f}배**로 가장 높습니다.")
    else:
        st.info("💰 기관장 연봉은 직원 평균보수의 몇 배일까요? — [보수·복리후생·채용] 페이지에서 확인해보세요.")
with qc2:
    if q_amt_org and q_ratio_org:
        same = "같습니다" if q_amt_org == q_ratio_org else "다릅니다"
        st.info(f"🏛️ **정부지원수입 최다 기관과 정부지원의존도 최고 기관은 같을까?** — {same}. "
                f"(수입 최다: {q_amt_org} / 의존도 최고: {q_ratio_org})")
    else:
        st.info("🏛️ 정부지원수입이 많은 기관과 정부지원의존도가 높은 기관은 같을까요?")
with qc3:
    if q_type:
        st.info(f"👶 **여성 육아휴직 사용자 수가 가장 많은 기관유형은?** — **{q_type}** (평균 {q_type_rate:.1f}명)")
    else:
        st.info("👶 육아휴직 사용자 수가 많은 기관유형은 어디일까요?")
with qc4:
    if q_growth_org:
        st.info(f"📈 **{earliest_year}~{latest_year}년, 평균보수가 가장 많이 오른 기관은?** — "
                f"**{q_growth_org}** (+{q_growth_rate:.1f}%)")
    else:
        st.info("📈 최근 기간 평균보수가 가장 많이 상승한 기관은 어디일까요?")

st.caption("💡 더 자세한 답은 좌측 사이드바의 각 분석 페이지에서 직접 탐색해보세요.")

st.divider()

# ---------------- 계량분석 핵심개념 ----------------
st.markdown("### 📚 이 대시보드를 보기 전에: 계량분석 핵심개념")
c1, c2, c3, c4 = st.columns(4)
c5, c6, c7 = st.columns(3)

with c1:
    st.markdown("#### ① 평균과 중앙값")
    st.caption("평균만으로 전체 분포를 설명할 수 있을까요? 극단값이 있으면 평균과 중앙값이 크게 달라집니다.")
with c2:
    st.markdown("#### ② 분포와 이상치")
    st.caption("극단값(이상치)은 평균뿐 아니라 회귀분석 결과에도 큰 영향을 줄 수 있습니다.")
with c3:
    st.markdown("#### ③ 총액과 비율")
    st.caption("기관 규모가 다른데 총액을 그대로 비교해도 될까요? '1인당' 지표가 필요한 이유입니다.")
with c4:
    st.markdown("#### ④ 집단 차이")
    st.caption("기관유형별 평균 차이가 통계적으로 유의하다고 해서 그것이 곧 원인은 아닙니다.")
with c5:
    st.markdown("#### ⑤ 상관관계")
    st.caption("두 변수가 함께 움직인다고 해서 인과관계라고 할 수 있을까요?")
with c6:
    st.markdown("#### ⑥ 통제변수")
    st.caption("다른 조건(기관유형, 규모 등)을 고려하면 관계가 어떻게 달라질까요?")
with c7:
    st.markdown("#### ⑦ 시간 변화")
    st.caption("기관 간의 차이와 동일 기관의 시간에 따른 변화는 같은 정보를 담고 있을까요?")

st.divider()

st.markdown("### 페이지 안내")
st.markdown(
    """
1. **기술통계 및 변수분포** — 변수 하나를 골라 전체·유형·부처·기관 위치를 확인
2. **기관유형 및 주무부처 비교** — 두 기준으로 비교 + 부처×유형 교차분석
3. **재정구조 및 법인세** — 수입·지출 구조와 법인세 흐름 (유형/부처/개별기관)
4. **보수·복리후생·채용** — 탭으로 지표 탐색 + 선택기관 4중 비교
5. **변수간 관계분석** — 자유 변수 선택 + 관계 비교기준(전체/유형/부처) (핵심 페이지)
6. **기관별 비교 및 프로필** — 내 기관을 4단계로 비교, 상대 프로파일, 유사기관
7. **연도별 변화분석** — 전체·유형·부처·기관 4단계 추세 비교, 증가율, 순위 안정성
8. **다중회귀분석** (심화) — 기관유형·주무부처·연도를 단계적으로 통제
9. **패널데이터 분석** (심화) — Between/Within, 기관·부처 고정효과
10. **주무부처별 분석** — 부처 하나를 골라 산하기관 전체를 살펴보는 페이지
    """
)

st.divider()
st.caption(
    "좌측 사이드바 **Pages** 메뉴에서 각 분석 페이지로 이동하세요. "
    "모든 페이지의 필터(연도·기관유형·주무부처·기관명)는 종속적으로 연동됩니다."
)
