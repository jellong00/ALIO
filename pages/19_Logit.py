# -*- coding: utf-8 -*-
import streamlit as st
import plotly.graph_objects as go

from utils.data import load_dataset
from utils.stats import run_logit, predicted_probability_curve
from utils.constants import PRIMARY_COLOR

st.set_page_config(page_title="Logit", page_icon="🎯", layout="wide")
st.title("🎯 19. 로짓(Logit) 분석 실습")
st.caption("기초 실습용으로만 제공됩니다. 정책 효과나 인과효과 분석으로 해석하지 않습니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

BINARY_CANDIDATES = {
    "법인세 결정세액 > 0": ("법인세결정세액", 0),
    "세액공제 > 0": ("세액공제", 0),
    "신규채용 > 0": ("신규채용", 0),
    "장애인 신규채용 > 0": ("장애인신규채용", 0),
}
available = {k: v for k, v in BINARY_CANDIDATES.items() if v[0] in panel.columns}

numeric_cols = [c for c in panel.select_dtypes(include="number").columns if c != "연도"]

c1, c2 = st.columns(2)
with c1:
    y_label = st.selectbox("종속변수 (이항)", list(available.keys()))
with c2:
    years = sorted(panel["연도"].dropna().unique(), reverse=True)
    year = st.selectbox("연도", years, index=years.index(2025) if 2025 in years else 0)

y_var, threshold = available[y_label]
x_cols = st.multiselect("독립변수 선택 (연속형)", [c for c in numeric_cols if c != y_var])

if not x_cols:
    st.info("독립변수를 1개 이상 선택해주세요.")
    st.stop()

data = panel[panel["연도"] == year].copy()
data["y_binary"] = (data[y_var] > threshold).astype(float)
data.loc[data[y_var].isna(), "y_binary"] = None

use_cols = ["y_binary"] + x_cols
valid_n = data[use_cols].dropna().shape[0]

if valid_n < len(x_cols) + 10:
    st.warning("로짓 분석을 수행하기에 유효한 관측치가 부족합니다.")
    st.stop()

result = run_logit(data, "y_binary", x_cols)

st.subheader("로짓 분석 결과")
st.dataframe(result["table"], hide_index=True, use_container_width=True)
st.metric("N", f"{result['n']:,}")

st.info("로짓 계수는 종속변수가 1이 될 로그오즈(log-odds)에 대한 연관성을 나타낼 뿐이며, 정책 효과나 인과효과를 의미하지 않습니다.")

if len(x_cols) >= 1:
    st.divider()
    st.subheader("예측확률 플롯 (주요 연속형 변수 1개)")
    main_x = st.selectbox("플롯에 사용할 변수", x_cols)
    x_range, probs = predicted_probability_curve(result["model"], main_x, result["data"])

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_range, y=probs, mode="lines", line=dict(color=PRIMARY_COLOR)))
    fig.update_layout(
        template="plotly_white",
        title=f"{main_x}에 따른 예측확률 ({y_label})",
        xaxis_title=main_x, yaxis_title="예측확률",
        yaxis=dict(range=[0, 1]),
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("다른 독립변수는 평균값으로 고정한 상태에서의 예측확률입니다.")
