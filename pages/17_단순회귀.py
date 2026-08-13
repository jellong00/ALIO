# -*- coding: utf-8 -*-
import streamlit as st
import plotly.graph_objects as go
import numpy as np

from utils.data import load_dataset
from utils.stats import run_simple_ols
from utils.charts import plot_scatter_ols
from utils.constants import NOTE_REGRESSION, PRIMARY_COLOR

st.set_page_config(page_title="단순회귀", page_icon="📐", layout="wide")
st.title("📐 17. 단순회귀분석")
st.caption("숫자형 X, Y 변수를 선택하여 단순선형회귀(OLS)를 직접 실습합니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

numeric_cols = [c for c in panel.select_dtypes(include="number").columns if c != "연도"]

c1, c2, c3 = st.columns(3)
with c1:
    x_col = st.selectbox("X (독립변수)", numeric_cols, index=0)
with c2:
    y_col = st.selectbox("Y (종속변수)", numeric_cols, index=min(1, len(numeric_cols) - 1))
with c3:
    years = sorted(panel["연도"].dropna().unique(), reverse=True)
    year = st.selectbox("연도", years, index=years.index(2025) if 2025 in years else 0)

c4, c5 = st.columns(2)
with c4:
    log_x = st.checkbox("X 로그변환 (log1p)")
with c5:
    log_y = st.checkbox("Y 로그변환 (log1p)")

data = panel[panel["연도"] == year]

if len(data[[x_col, y_col]].dropna()) < 5:
    st.warning("회귀분석을 수행하기에 유효한 관측치가 부족합니다.")
    st.stop()

result = run_simple_ols(data, x_col, y_col, log_x=log_x, log_y=log_y)

st.subheader("회귀분석 결과")
st.dataframe(result["table"], hide_index=True, use_container_width=True)

m1, m2 = st.columns(2)
m1.metric("R²", f"{result['r2']:.3f}")
m2.metric("N", f"{result['n']:,}")

st.info(NOTE_REGRESSION)

st.subheader("Scatter + 회귀선")
plot_df = data.copy()
x_label = f"log(1+{x_col})" if log_x else x_col
y_label = f"log(1+{y_col})" if log_y else y_col

fig = go.Figure()
fig.add_trace(go.Scatter(x=result["x_used"], y=result["y_used"], mode="markers", marker=dict(color=PRIMARY_COLOR, opacity=0.6), name="관측치"))
order = np.argsort(result["x_used"].values)
fig.add_trace(go.Scatter(
    x=result["x_used"].values[order],
    y=result["fitted"].values[order],
    mode="lines", line=dict(color="#DC2626"), name="OLS 회귀선",
))
fig.update_layout(template="plotly_white", title=f"{x_label} vs {y_label} ({year}년)", xaxis_title=x_label, yaxis_title=y_label)
st.plotly_chart(fig, use_container_width=True)

st.subheader("잔차 플롯 (선택)")
if st.checkbox("잔차 플롯 보기"):
    fig_resid = go.Figure()
    fig_resid.add_trace(go.Scatter(x=result["fitted"], y=result["resid"], mode="markers", marker=dict(color=PRIMARY_COLOR, opacity=0.6)))
    fig_resid.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_resid.update_layout(template="plotly_white", title="잔차 플롯", xaxis_title="예측값", yaxis_title="잔차")
    st.plotly_chart(fig_resid, use_container_width=True)
