# -*- coding: utf-8 -*-
import streamlit as st

from utils.data import load_dataset
from utils.stats import run_multiple_ols
from utils.constants import NOTE_REGRESSION

st.set_page_config(page_title="다중회귀", page_icon="📊", layout="wide")
st.title("📊 18. 다중회귀분석")
st.caption("종속변수 Y, 연속형 독립변수 여러 개, 범주형 변수를 선택하여 다중회귀(OLS)를 실습합니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

numeric_cols = [c for c in panel.select_dtypes(include="number").columns if c != "연도"]
cat_cols = [c for c in ["기관유형", "주무부처"] if c in panel.columns]

c1, c2 = st.columns(2)
with c1:
    y_col = st.selectbox("종속변수 (Y)", numeric_cols, index=0)
with c2:
    years = sorted(panel["연도"].dropna().unique(), reverse=True)
    year = st.selectbox("연도", years, index=years.index(2025) if 2025 in years else 0)

x_cols = st.multiselect("연속형 독립변수 (여러 개 선택)", [c for c in numeric_cols if c != y_col])
cat_selected = st.multiselect("범주형 변수 (더미변수로 처리, 1개 이상 권장)", cat_cols)

if not x_cols:
    st.info("독립변수를 1개 이상 선택해주세요.")
    st.stop()

data = panel[panel["연도"] == year]
use_cols = [y_col] + x_cols + cat_selected
valid_n = data[use_cols].dropna().shape[0]

if valid_n < len(x_cols) + len(cat_selected) + 5:
    st.warning("회귀분석을 수행하기에 유효한 관측치가 부족합니다.")
    st.stop()

result = run_multiple_ols(data, y_col, x_cols, cat_cols=cat_selected)

st.subheader("회귀분석 결과")
st.dataframe(result["table"], hide_index=True, use_container_width=True)

m1, m2, m3 = st.columns(3)
m1.metric("R²", f"{result['r2']:.3f}")
m2.metric("Adjusted R²", f"{result['adj_r2']:.3f}")
m3.metric("N", f"{result['n']:,}")

st.info(NOTE_REGRESSION)
st.caption("범주형 변수는 첫 번째 범주를 기준(reference)으로 하는 더미변수로 변환되어 포함됩니다.")
