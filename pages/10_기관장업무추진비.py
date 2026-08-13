# -*- coding: utf-8 -*-
import streamlit as st

from utils.data import load_dataset
from utils.components import render_distribution_analysis
from utils.filters import render_common_filters, apply_filters

st.set_page_config(page_title="기관장업무추진비", page_icon="🧳", layout="wide")
st.title("🧳 10. 기관장 업무추진비")
st.caption("대표변수인 '업무추진비 집행금액'을 분석합니다. (단위: 천원)")
st.info("과도한 해석(예: 청렴도, 경영효율성 지표화)은 하지 않습니다. 단순 분포와 추이만 확인합니다.")

panel = load_dataset("panel")
if panel.empty:
    st.stop()

filters = render_common_filters(panel, key_prefix="bizexp")
filters_no_year = {k: v for k, v in filters.items() if k != "연도"}
filtered = apply_filters(panel, filters_no_year)

render_distribution_analysis(filtered, variable="기관장업무추진비", year=filters.get("연도", 2025), unit="천원")
