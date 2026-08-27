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

# ---------------- A-2. 결정세액 0 vs 양수 비율 ----------------
st.markdown("### 🔢 법인세 결정세액이 '0'인 기관과 '양수'인 기관")
st.caption("⚠️ 결정세액이 0이라는 사실만으로 해당 기관의 재무상태나 경영성과를 평가할 수 없습니다 (수익사업이 없거나, 공제·감면으로 세액이 0이 된 경우 등 다양한 이유가 있을 수 있습니다).")
if "법인세결정세액" in view.columns:
    tax_amt = pd.to_numeric(view["법인세결정세액"], errors="coerce").dropna()
    n_total_tax = tax_amt.shape[0]
    n_zero = int((tax_amt == 0).sum())
    n_pos = int((tax_amt > 0).sum())
    n_neg = int((tax_amt < 0).sum())
    zc1, zc2, zc3, zc4 = st.columns(4)
    zc1.metric("전체 N", f"{n_total_tax:,}")
    zc2.metric("결정세액 = 0", f"{n_zero:,} ({n_zero/n_total_tax*100:.1f}%)" if n_total_tax else "0")
    zc3.metric("결정세액 > 0", f"{n_pos:,} ({n_pos/n_total_tax*100:.1f}%)" if n_total_tax else "0")
    if n_neg:
        zc4.metric("결정세액 < 0", f"{n_neg:,}")

    st.markdown("#### 기관유형·주무부처별 결정세액 '양수' 기관 비율")
    ratio_level = st.radio("비교 수준", ["기관유형", "주무부처"], horizontal=True, key="p5_ratiolevel")
    tax_flag = view[["기관명", "기관유형", "주무부처", "법인세결정세액"]].dropna(subset=["법인세결정세액"]).copy()
    tax_flag["양수여부"] = pd.to_numeric(tax_flag["법인세결정세액"], errors="coerce") > 0

    if ratio_level == "기관유형":
        grp_ratio = tax_flag.groupby("기관유형").agg(N=("양수여부", "size"), 양수비율=("양수여부", "mean")).reset_index()
        grp_ratio["양수비율(%)"] = grp_ratio["양수비율"] * 100
        fig_ratio = px.bar(grp_ratio, x="기관유형", y="양수비율(%)", hover_data=["N"],
                             labels={"양수비율(%)": "결정세액 > 0 인 기관 비율(%)"})
        fig_ratio.update_layout(font=dict(size=15), height=440)
        st.plotly_chart(fig_ratio, use_container_width=True)
    else:
        ratio_minn = st.slider("최소 기관 수", 1, 10, 3, key="p5_ratiominn")
        grp_ratio = tax_flag.groupby("주무부처").agg(N=("양수여부", "size"), 양수비율=("양수여부", "mean")).reset_index()
        grp_ratio = grp_ratio[grp_ratio["N"] >= ratio_minn].sort_values("양수비율", ascending=False)
        grp_ratio["양수비율(%)"] = grp_ratio["양수비율"] * 100
        fig_ratio = px.bar(grp_ratio, x="양수비율(%)", y="주무부처", orientation="h", hover_data=["N"],
                             labels={"양수비율(%)": "결정세액 > 0 인 기관 비율(%)"})
        fig_ratio.update_layout(font=dict(size=13), height=max(440, 22 * len(grp_ratio)))
        st.plotly_chart(fig_ratio, use_container_width=True)
        st.caption(f"최소 기관 수 {ratio_minn}개 이상인 부처만 표시합니다.")

st.divider()

st.markdown("### 📊 B. 분포 자세히 보기")
tax_var = st.selectbox("변수 선택", ["과세표준", "법인세결정세액", "실효법인세율"],
                         format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p5_taxvar")
tax_col = VARIABLES[tax_var]["column"]
st.info(f"'{get_label(tax_var)}'의 히스토그램·Box plot·기술통계·왜도는 **① 변수분포 및 기술통계** 페이지의 [법인세] 탭에서 확인할 수 있습니다.")
st.caption("⚠️ 과세표준·결정세액 모두 0값이 상당수 포함되어 있을 수 있습니다. 위 [A] 항목의 0/양수 비율을 함께 참고하세요.")

st.markdown("#### 실효법인세율 (양수 과세표준 기관 한정)")
st.caption("실효법인세율 = 결정세액 / 과세표준. 과세표준이 0 이하이거나 결측인 기관은 정의상 계산에서 제외합니다.")
if "과세표준" in view.columns and "법인세결정세액" in view.columns:
    etr_base = view[["기관명", "과세표준", "법인세결정세액"]].copy()
    etr_base["과세표준_num"] = pd.to_numeric(etr_base["과세표준"], errors="coerce")
    etr_base["결정세액_num"] = pd.to_numeric(etr_base["법인세결정세액"], errors="coerce")
    n_before_etr = etr_base.shape[0]
    etr_valid = etr_base[(etr_base["과세표준_num"] > 0) & etr_base["결정세액_num"].notna()].copy()
    n_after_etr = etr_valid.shape[0]
    etr_valid["실효세율"] = etr_valid["결정세액_num"] / etr_base.loc[etr_valid.index, "과세표준_num"] * 100
    st.caption(f"제외된 관측치: {n_before_etr - n_after_etr:,}건 (과세표준 ≤ 0 또는 결측) · 분석에 사용된 N = {n_after_etr:,}")
    if not etr_valid.empty:
        import plotly.express as _px
        fig_etr = _px.histogram(etr_valid, x="실효세율", nbins=30, labels={"실효세율": "실효법인세율 (%)"})
        fig_etr.update_layout(font=dict(size=15), height=420, showlegend=False)
        st.plotly_chart(fig_etr, use_container_width=True)
    else:
        st.info("양수 과세표준을 가진 기관이 없어 실효법인세율을 계산할 수 없습니다.")

st.divider()

# ---------------- C. 기관유형·주무부처 비교 ----------------
st.markdown("### 🏛️ C. 기관유형·주무부처 비교")
compare_var = st.radio("비교할 지표", ["법인세결정세액", "실효법인세율(양수 과세표준)"], horizontal=True, key="p5_comparevar")
tax_level = st.radio("비교 수준", ["기관유형", "주무부처"], horizontal=True, key="p5_taxlevel")

if compare_var == "법인세결정세액":
    plot_col = "법인세결정세액"
    plot_df = view.dropna(subset=[plot_col]).copy() if plot_col in view.columns else pd.DataFrame()
    plot_label = f"{get_label('법인세결정세액')} ({get_unit('법인세결정세액')})"
else:
    plot_col = "실효세율"
    base = view[["기관명", "기관유형", "주무부처", "과세표준", "법인세결정세액"]].copy()
    base["과세표준_num"] = pd.to_numeric(base["과세표준"], errors="coerce")
    base["결정세액_num"] = pd.to_numeric(base["법인세결정세액"], errors="coerce")
    plot_df = base[(base["과세표준_num"] > 0) & base["결정세액_num"].notna()].copy()
    plot_df["실효세율"] = plot_df["결정세액_num"] / plot_df["과세표준_num"] * 100
    plot_label = "실효법인세율 (%)"

if not plot_df.empty:
    import plotly.express as px
    if tax_level == "기관유형":
        fig_c = px.box(plot_df, x="기관유형", y=plot_col, points="outliers", labels={plot_col: plot_label})
        fig_c.update_layout(font=dict(size=16), height=460)
        st.plotly_chart(fig_c, use_container_width=True, key="p5_typebox")
        n_by_type = plot_df.groupby("기관유형").size().reset_index(name="N")
        st.dataframe(n_by_type, use_container_width=True, hide_index=True)
    else:
        min_n_dept = st.slider("최소 기관 수", 1, 10, 3, key="p5_deptminn2")
        dept_n = plot_df.groupby("주무부처").size()
        valid_depts = dept_n[dept_n >= min_n_dept].index
        dsub = plot_df[plot_df["주무부처"].isin(valid_depts)]
        if not dsub.empty:
            fig_c = px.box(dsub, x="주무부처", y=plot_col, points="outliers", labels={plot_col: plot_label})
            fig_c.update_layout(font=dict(size=14), height=500, xaxis_tickangle=-30)
            st.plotly_chart(fig_c, use_container_width=True, key="p5_deptbox")
            st.caption(f"최소 기관 수 {min_n_dept}개 이상인 부처만 표시합니다.")
        else:
            st.info("조건을 만족하는 부처가 없습니다.")
else:
    st.info("표시할 데이터가 없습니다.")

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
