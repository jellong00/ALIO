import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.charts import plot_scatter
from utils.level_compare import dept_stats_table
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="법인세 분석", layout="wide")
st.title("⑤ 법인세 분석")
render_intro(
    purpose="공공기관별 과세표준과 법인세 결정세액이 어떻게 분포하고, 서로 어떤 관계를 갖는지 살펴봅니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="개념 설명 · 분포(히스토그램/Box plot) · 기관유형·주무부처 비교 · 산점도+상관계수",
    caution="과세표준과 세액은 세법상 계산 항목으로 단위·성격이 달라 하나의 막대축으로 나란히 비교하지 않습니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p5")
view, caption, mode = year_slice(df, key_prefix="p5")
st.caption(caption)

st.divider()
st.markdown("### 📖 A. 변수 개념")
st.markdown(
    """
공공기관도 수익사업 부분에 대해 법인세를 낼 수 있습니다. 계산 흐름은 다음과 같습니다.

```
과세표준  →  (세율 적용)  →  산출세액  →  (공제·감면, 가산세 반영)  →  결정세액
```

- **과세표준**: 세율을 적용하는 기준 금액 (익금에서 손금·이월결손금 등을 제외한 금액)
- **산출세액**: 과세표준에 세율을 곱한 금액
- **세액공제**: 산출세액에서 빼주는 금액 (각종 공제·감면)
- **가산세**: 신고 오류 등에 따라 추가되는 금액
- **결정세액**: 최종적으로 확정된 납부세액
"""
)
k1, k2, k3 = st.columns(3)
if "과세표준" in view.columns:
    k1.metric("평균 과세표준", f"{pd.to_numeric(view['과세표준'], errors='coerce').mean():,.0f} 천원")
if "법인세산출세액" in view.columns:
    k2.metric("평균 산출세액", f"{pd.to_numeric(view['법인세산출세액'], errors='coerce').mean():,.0f} 천원")
if "법인세결정세액" in view.columns:
    k3.metric("평균 결정세액", f"{pd.to_numeric(view['법인세결정세액'], errors='coerce').mean():,.0f} 천원")

st.divider()

st.markdown("### 📊 B. 분포 자세히 보기")
tax_var = st.selectbox("변수 선택", ["과세표준", "법인세결정세액", "실효법인세율"],
                         format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p5_taxvar")
tax_col = VARIABLES[tax_var]["column"]
st.info(f"'{get_label(tax_var)}'의 히스토그램·Box plot·기술통계·왜도는 **① 변수분포 및 기술통계** 페이지의 [법인세] 탭에서 확인할 수 있습니다.")

st.divider()

# ---------------- C. 기관유형·주무부처 비교 ----------------
st.markdown("### 🏛️ C. 기관유형·주무부처 비교")
tax_level = st.radio("비교 수준", ["기관유형", "주무부처"], horizontal=True, key="p5_taxlevel")
if tax_col in view.columns:
    if tax_level == "기관유형":
        import plotly.express as px
        fig_c = px.box(view.dropna(subset=[tax_col]), x="기관유형", y=tax_col,
                        labels={tax_col: f"{get_label(tax_var)} ({get_unit(tax_var)})"})
        fig_c.update_layout(font=dict(size=16), height=460)
        st.plotly_chart(fig_c, use_container_width=True, key="p5_typebox")
    else:
        dstats = dept_stats_table(view, tax_col, min_n=3).round(1)
        st.dataframe(dstats, use_container_width=True, hide_index=True)

st.divider()

# ---------------- D. 관계 ----------------
st.markdown("### 🔗 D. 과세표준과 법인세결정세액")
if "과세표준" in view.columns and "법인세결정세액" in view.columns:
    fig4 = plot_scatter(view, "과세표준", "법인세결정세액", x_key="과세표준", y_key="법인세결정세액", trendline="ols")
    st.plotly_chart(fig4, use_container_width=True)
    sub3 = view[["과세표준", "법인세결정세액"]].dropna()
    if sub3.shape[0] > 2:
        r, p = stats.pearsonr(sub3["과세표준"], sub3["법인세결정세액"])
        st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {sub3.shape[0]:,}")

st.divider()

# ---------------- E. 확장 ----------------
st.markdown("### 🔎 E. 확장 — 다른 재정 변수와의 관계")
x_options = ["총수입", "사업수입", "정부지원의존도", "임직원수"]
x_key = st.selectbox("X 변수", x_options, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p5_extx")
x_col = VARIABLES[x_key]["column"]
if x_col in view.columns and "법인세결정세액" in view.columns:
    fig5 = plot_scatter(view, x_col, "법인세결정세액", x_key=x_key, y_key="법인세결정세액", trendline="ols")
    st.plotly_chart(fig5, use_container_width=True)
    sub4 = view[[x_col, "법인세결정세액"]].dropna()
    if sub4.shape[0] > 2:
        r, p = stats.pearsonr(sub4[x_col], sub4["법인세결정세액"])
        st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {sub4.shape[0]:,}")
    st.caption("⚠️ 법인세는 세법상 규정(공제·감면 등)의 영향을 받으므로 단순 상관관계로 인과를 단정할 수 없습니다.")
