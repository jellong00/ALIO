# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd

from utils.data import load_dataset
from utils.charts import plot_time_series

st.set_page_config(page_title="기관 종합현황", page_icon="🏢", layout="wide")
st.title("🏢 02. 기관 종합현황")
st.caption("기관을 하나 선택하면 재무·인력·보수 등 주요 지표를 한 화면에서 확인할 수 있습니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

institutions = sorted(panel["기관명"].dropna().unique())
selected = st.selectbox("기관명 검색", institutions, key="inst02")

inst_df = panel[panel["기관명"] == selected].sort_values("연도")
if inst_df.empty:
    st.warning("선택한 기관의 데이터가 없습니다.")
    st.stop()

latest_year = int(inst_df["연도"].max())
latest = inst_df[inst_df["연도"] == latest_year].iloc[0]

st.markdown(f"### {selected} — 기관유형: {latest['기관유형']} / 주무부처: {latest['주무부처']}")
st.caption(f"최근 자료 연도: {latest_year}년")

KPI_GROUPS = {
    "재무 (백만원)": [
        ("총수입", "총수입"), ("총지출", "총지출"), ("수지차", "수지차"),
        ("정부지원수입", "정부지원수입"), ("인건비", "인건비"), ("사업비", "사업비"),
    ],
    "법인세 (천원)": [
        ("과세표준", "과세표준"), ("법인세결정세액", "결정세액"),
    ],
    "인력 (명)": [
        ("임직원수", "임직원수"), ("정규직수", "정규직수"),
        ("비정규직수", "비정규직수"), ("여성직원수", "여성직원수"),
        ("신규채용", "신규채용"),
    ],
    "보수 (천원)": [
        ("직원평균보수", "1인당 평균보수"), ("남성평균보수", "남성 평균보수"),
        ("여성평균보수", "여성 평균보수"), ("기관장보수", "기관장 보수"),
        ("임원평균보수", "임원 평균보수"),
    ],
    "기타 (천원)": [
        ("기관장업무추진비", "업무추진비"), ("총복리후생비", "복리후생비"),
    ],
}

for group_title, items in KPI_GROUPS.items():
    st.subheader(group_title)
    cols = st.columns(len(items))
    for col, (var, label) in zip(cols, items):
        val = latest.get(var, None)
        if pd.isna(val):
            col.metric(label, "자료없음")
        else:
            col.metric(label, f"{val:,.0f}")

st.divider()
st.subheader("연도별 추이 (2021~2025)")
st.caption("복잡한 종합점수나 지수는 계산하지 않으며, 단순 추이만 확인합니다.")

trend_options = ["총수입", "총지출", "임직원수", "직원평균보수", "기관장보수", "총복리후생비"]
trend_var = st.selectbox("확인할 변수", [v for v in trend_options if v in inst_df.columns])

trend_df = inst_df[inst_df["연도"] <= 2025]
if trend_var in trend_df.columns and trend_df[trend_var].notna().any():
    fig = plot_time_series(trend_df, "연도", trend_var, title=f"{selected} - {trend_var} 추이")
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("해당 변수에 대한 시계열 자료가 부족합니다.")

st.caption("※ 이 데이터는 기관 단위 집계자료이며, 개인 수준의 결과로 해석할 수 없습니다.")
