import streamlit as st
import pandas as pd
import plotly.express as px

from utils.page_common import render_domain_page
from utils.data_cleaner import get_full_panel

df, var_key, col = render_domain_page(
    domain="재정 구조",
    question="Q3. 공공기관의 재정구조는 어떻게 다르며 기관 특성과 어떤 관계가 있는가?",
    intro="총수입·총지출·정부지원의존도·법인세 관련 지표를 살펴보고, 기관 특성(임직원수 등)과의 "
          "관계를 함께 탐색한다.",
)

if df is not None:
    st.divider()
    st.markdown("### 💰 수입 구성 (정부지원수입 vs 그 외)")
    comp = df[["기관명", "기관유형", "연도", "총수입", "정부지원수입"]].dropna(subset=["총수입"]).copy()
    comp["기타수입"] = (comp["총수입"] - comp["정부지원수입"].fillna(0)).clip(lower=0)

    view = st.radio("보기 단위", ["기관유형 평균", "개별 기관"], horizontal=True, key="p3_view")
    if view == "기관유형 평균":
        grp = comp.groupby("기관유형")[["정부지원수입", "기타수입"]].mean().reset_index()
        long = grp.melt(id_vars="기관유형", value_vars=["정부지원수입", "기타수입"],
                         var_name="구성", value_name="금액(백만원)")
        fig = px.bar(long, x="기관유형", y="금액(백만원)", color="구성", barmode="stack",
                     color_discrete_map={"정부지원수입": "#E07B39", "기타수입": "#4C78A8"})
    else:
        orgs = sorted(comp["기관명"].unique())
        pick = st.multiselect("기관 선택 (최대 10개 권장)", orgs, default=orgs[:5], key="p3_orgs")
        sub = comp[comp["기관명"].isin(pick)]
        yr = st.selectbox("연도", sorted(sub["연도"].unique(), reverse=True), key="p3_year")
        sub = sub[sub["연도"] == yr]
        long = sub.melt(id_vars="기관명", value_vars=["정부지원수입", "기타수입"],
                         var_name="구성", value_name="금액(백만원)")
        fig = px.bar(long, x="기관명", y="금액(백만원)", color="구성", barmode="stack",
                     color_discrete_map={"정부지원수입": "#E07B39", "기타수입": "#4C78A8"})
    fig.update_layout(font=dict(size=16), height=500)
    st.plotly_chart(fig, use_container_width=True)
    with st.expander("💡 계량분석 포인트"):
        st.markdown("- 정부지원수입 비중이 큰 기관일수록 **정부지원의존도**가 높게 나타난다.\n"
                     "- 이는 다음 '조직 운영' 페이지에서 보수·복리후생과의 관계로 이어진다.")
