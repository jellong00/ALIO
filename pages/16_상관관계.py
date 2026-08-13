# -*- coding: utf-8 -*-
import streamlit as st

from utils.data import load_dataset
from utils.charts import plot_scatter, plot_correlation_heatmap
from utils.constants import NOTE_CORR

st.set_page_config(page_title="상관관계", page_icon="🔗", layout="wide")
st.title("🔗 16. 상관관계")
st.caption("두 숫자형 변수 간 상관관계를 살펴봅니다. 이 페이지부터는 별도의 관계분석 실습 영역입니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

numeric_cols = [c for c in panel.select_dtypes(include="number").columns if c != "연도"]

c1, c2, c3, c4 = st.columns(4)
with c1:
    x_col = st.selectbox("X 변수", numeric_cols, index=0)
with c2:
    y_col = st.selectbox("Y 변수", numeric_cols, index=min(1, len(numeric_cols) - 1))
with c3:
    years = sorted(panel["연도"].dropna().unique(), reverse=True)
    year = st.selectbox("연도", years, index=years.index(2025) if 2025 in years else 0)
with c4:
    type_options = ["전체"] + sorted(panel["기관유형"].dropna().unique().tolist())
    inst_type = st.selectbox("기관유형", type_options)

data = panel[panel["연도"] == year].copy()
if inst_type != "전체":
    data = data[data["기관유형"] == inst_type]

data = data[[x_col, y_col]].dropna()

st.subheader("Scatter Plot")
st.plotly_chart(plot_scatter(data, x_col, y_col, title=f"{x_col} vs {y_col} ({year}년)"), use_container_width=True)

if len(data) >= 3:
    corr = data[x_col].corr(data[y_col])
    m1, m2 = st.columns(2)
    m1.metric("Pearson 상관계수 (r)", f"{corr:.3f}")
    m2.metric("N", f"{len(data):,}")
else:
    st.warning("상관계수를 계산하기에 유효한 관측치가 부족합니다.")

st.info(NOTE_CORR)

st.divider()
st.subheader("여러 변수 상관행렬 (선택)")
multi_vars = st.multiselect("변수 선택 (2개 이상)", numeric_cols, default=numeric_cols[:5] if len(numeric_cols) >= 5 else numeric_cols)
if len(multi_vars) >= 2:
    multi_data = panel[panel["연도"] == year][multi_vars].dropna()
    if len(multi_data) >= 3:
        corr_matrix = multi_data.corr()
        st.plotly_chart(plot_correlation_heatmap(corr_matrix, title=f"상관행렬 ({year}년)"), use_container_width=True)
    else:
        st.warning("상관행렬을 계산하기에 유효한 관측치가 부족합니다.")
