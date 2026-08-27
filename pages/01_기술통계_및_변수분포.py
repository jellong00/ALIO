import streamlit as st
import pandas as pd

from utils.data_cleaner import get_full_panel, describe_var
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit, get_question
from utils.charts import plot_histogram
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="기술통계 및 변수분포", layout="wide")
st.title("① 기술통계 및 변수분포")
render_intro(
    purpose="선택한 변수 하나의 값이 어떤 범위와 분포를 갖는지 이해합니다.",
    unit="아래에서 선택한 연도의 기관 (기본값: 최신연도, 기관 1개 = 관측치 1개)",
    methods="기술통계량 · 히스토그램 · 전체 Box plot",
    caution="이 페이지는 변수 하나만 봅니다. 기관유형·주무부처에 따른 차이는 ②③번 페이지에서 다룹니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p1")

st.divider()
c1, c2 = st.columns(2)
with c1:
    category = st.selectbox("카테고리", CATEGORIES, key="p1_cat")
cat_vars = get_vars_by_category(category)
with c2:
    var_key = st.selectbox(
        "변수 선택", list(cat_vars.keys()),
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p1_var"
    )
col = VARIABLES[var_key]["column"]
if col not in df.columns:
    st.warning("선택한 변수가 데이터에 없습니다.")
    st.stop()

view, caption, mode = year_slice(df, key_prefix="p1")
st.caption(caption)

desc = describe_var(view, col)
if desc.get("N", 0) == 0:
    st.warning("선택한 조건에서 유효한 관측치가 없습니다.")
    st.stop()

st.divider()
st.markdown(f"### 📐 {get_label(var_key)} 기술통계")
r1 = st.columns(5)
r1[0].metric("N", f"{desc['N']:,}")
r1[1].metric("결측치 수", f"{desc['결측치수']:,}")
r1[2].metric("결측률", f"{desc['결측률']*100:.1f}%")
r1[3].metric("평균", f"{desc['평균']:,.1f}")
r1[4].metric("중앙값", f"{desc['중앙값']:,.1f}")
r2 = st.columns(5)
r2[0].metric("표준편차", f"{desc['표준편차']:,.1f}")
r2[1].metric("Q1", f"{desc['Q1']:,.1f}")
r2[2].metric("Q3", f"{desc['Q3']:,.1f}")
r2[3].metric("최소", f"{desc['최소']:,.1f}")
r2[4].metric("최대", f"{desc['최대']:,.1f}")

nbins = st.slider("히스토그램 구간(bin) 수", 10, 80, 30, key="p1_nbins")
clip = st.checkbox("극단값 영향 줄이기 (상하위 1% 밖은 축 범위에서 제외하고 보기)", value=True, key="p1_clip")
fig = plot_histogram(view, col, var_key=var_key, nbins=nbins, clip_extreme=clip)
st.plotly_chart(fig, use_container_width=True)
st.caption("범례: 주황 실선 = 평균, 초록 점선 = 중앙값 (선 위 숫자는 값입니다)")
with st.expander("📌 확인할 것 / 💡 포인트"):
    st.markdown("- **평균과 중앙값**: 두 값이 크게 다르면 분포가 한쪽으로 치우쳐 있다는 뜻입니다.\n"
                 "- **표준편차**: 값들이 평균에서 얼마나 퍼져 있는지를 나타냅니다.\n"
                 "- **Q1·Q3(사분위수)**: 하위 25%, 상위 25% 지점을 의미하며, Q3-Q1(사분위범위)이 넓을수록 분포가 넓게 퍼져 있습니다.\n"
                 "- 극단값이 매우 크면 축이 그쪽으로 눌려서 대부분 데이터가 좁게 뭉쳐 보일 수 있어, 기본적으로 상하위 1%를 축 범위에서 제외해 표시합니다(데이터 자체는 그대로 사용).")

st.divider()
st.markdown("### 📦 전체 분포 (Box plot)")
import plotly.express as px
import numpy as np
box_data = view[[col]].dropna()
fig_box = px.box(box_data, y=col, points="outliers", labels={col: f"{get_label(var_key)} ({get_unit(var_key)})"})
fig_box.update_layout(font=dict(size=16), height=460)
if clip and not box_data.empty:
    lo, hi = np.percentile(box_data[col], [1, 99])
    if lo != hi:
        pad = (hi - lo) * 0.15
        fig_box.update_yaxes(range=[lo - pad, hi + pad])
    st.caption("극단값 영향 줄이기가 켜져 있어 y축 범위를 상하위 1% 기준으로 조정했습니다 (데이터 자체는 그대로 사용, 점으로 표시된 이상치는 축 범위 밖에 있을 수 있습니다).")
st.plotly_chart(fig_box, use_container_width=True)

st.divider()
st.markdown("### 🔎 이상치 기관 확인")
snap_named = view[["기관명", col]].dropna().sort_values(col)
if not snap_named.empty:
    ec1, ec2 = st.columns(2)
    with ec1:
        st.markdown("**값이 가장 작은 5개 기관**")
        st.dataframe(snap_named.head(5).rename(columns={col: get_label(var_key)}), use_container_width=True, hide_index=True)
    with ec2:
        st.markdown("**값이 가장 큰 5개 기관**")
        st.dataframe(snap_named.tail(5).sort_values(col, ascending=False).rename(columns={col: get_label(var_key)}),
                     use_container_width=True, hide_index=True)
    st.caption("💡 기관유형·주무부처별 비교, 특정 기관의 상세 순위는 ②③⑩번 페이지에서 확인할 수 있습니다.")

st.divider()
st.markdown("### 🤔 생각해볼 질문")
st.info(get_question(var_key))
