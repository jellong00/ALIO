# -*- coding: utf-8 -*-
import streamlit as st

from utils.data import load_dataset
from utils.charts import plot_histogram, plot_boxplot
from utils.constants import NOTE_BOXPLOT, NOTE_HISTOGRAM

st.set_page_config(page_title="분포 실습", page_icon="📈", layout="wide")
st.title("📈 13. 분포 실습")
st.caption("숫자형 변수를 선택하여 히스토그램과 박스플롯을 직접 그려봅니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

numeric_cols = panel.select_dtypes(include="number").columns.tolist()
numeric_cols = [c for c in numeric_cols if c != "연도"]

c1, c2 = st.columns(2)
with c1:
    variable = st.selectbox("변수 선택", numeric_cols)
with c2:
    years = sorted(panel["연도"].dropna().unique(), reverse=True)
    year = st.selectbox("연도", years, index=years.index(2025) if 2025 in years else 0)

data = panel[panel["연도"] == year][variable]

nbins = st.slider("Bin 수", min_value=10, max_value=50, value=30, step=1)
st.caption("bin 수를 바꾸면 분포의 인상이 달라질 수 있습니다. 같은 데이터라도 bin이 너무 적으면 세부 구조가 가려지고, 너무 많으면 잡음이 부각됩니다.")

c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(plot_histogram(data, title=f"{variable} 히스토그램 ({year}년)", nbins=nbins), use_container_width=True)
    st.caption(NOTE_HISTOGRAM)
with c4:
    st.plotly_chart(plot_boxplot(data, title=f"{variable} 박스플롯 ({year}년)"), use_container_width=True)
    st.caption(NOTE_BOXPLOT)
