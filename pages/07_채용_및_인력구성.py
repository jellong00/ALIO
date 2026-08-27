import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, get_label, get_unit
from utils.charts import plot_scatter, plot_boxplot, plot_rank_bar
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="채용 및 인력구성", layout="wide")
st.title("⑦ 채용 및 인력구성")
render_intro(
    purpose="채용의 총량과 비율, 기존 인력구성과 신규채용 구성을 비교합니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="총량 vs 비율 · 성별 구성 관계 · 여성 채용구성 격차 · [일·가정양립] 탭",
    caution="채용 인원(총량)이 많다고 해서 채용률(비율)도 높은 것은 아닙니다. 일반적인 분포(히스토그램·Box plot)는 ① 변수분포 및 기술통계 페이지에서 확인하세요.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p7")
view, caption, mode = year_slice(df, key_prefix="p7")
st.caption(caption)

tab1, tab2 = st.tabs(["🧑‍💼 채용·인력", "👶 일·가정양립"])

# ================= TAB 1: 채용·인력 =================
with tab1:
    st.markdown("### 규모효과 — 임직원수와 신규채용자 수")
    st.caption("💡 임직원이 많은 기관은 신규채용 인원도 많은가? (기관 규모가 클수록 채용 인원도 자연스럽게 커질 수 있습니다.)")
    emp_col = VARIABLES["임직원수"]["column"]
    hire_col = VARIABLES["신규채용자수"]["column"]
    if emp_col in view.columns and hire_col in view.columns:
        fig_scale = plot_scatter(view, emp_col, hire_col, x_key="임직원수", y_key="신규채용자수")
        st.plotly_chart(fig_scale, use_container_width=True, key="p7_scale")
        sub_scale = view[[emp_col, hire_col]].dropna()
        if sub_scale.shape[0] > 2:
            r, p = stats.pearsonr(sub_scale[emp_col], sub_scale[hire_col])
            st.caption(f"Pearson r = {r:.3f} (N = {sub_scale.shape[0]:,})")

    st.divider()
    st.markdown("### 핵심 분석 1 — 신규채용자 수와 신규채용률")
    st.caption("💡 채용 인원이 많은 기관이 실제로도 적극적으로 채용하는 기관인가? 기관 규모에 따라 해석이 달라질 수 있습니다.")
    n_col = VARIABLES["신규채용자수"]["column"]
    r_col = VARIABLES["신규채용률"]["column"]
    if n_col in view.columns and r_col in view.columns:
        fig6 = plot_scatter(view, n_col, r_col, x_key="신규채용자수", y_key="신규채용률")
        st.plotly_chart(fig6, use_container_width=True)
        sub = view[[n_col, r_col]].dropna()
        if sub.shape[0] > 2:
            r, p = stats.pearsonr(sub[n_col], sub[r_col])
            st.caption(f"Pearson r = {r:.3f} (N = {sub.shape[0]:,})")

    st.divider()
    st.markdown("### 핵심 분석 2 — 여성직원비율과 여성신규채용비율")
    a_col = VARIABLES["여성직원비율"]["column"]
    b_col = VARIABLES["여성신규채용비율"]["column"]
    if a_col in view.columns and b_col in view.columns:
        fig7 = plot_scatter(view, a_col, b_col, x_key="여성직원비율", y_key="여성신규채용비율")
        st.plotly_chart(fig7, use_container_width=True)
        st.caption("💡 기존 여성 직원 비율과 여성 신규채용 비율이 다르다면, 조직의 성별 구성이 변화하는 방향을 짐작할 수 있습니다.")

    st.divider()
    st.markdown("### 여성 채용구성 격차")
    st.caption("여성채용구성격차 = 여성신규채용비율 − 여성직원비율 (%p). 양수면 신규채용에서 여성 비중이 기존 인력구성보다 높다는 뜻이고, "
                "음수면 그 반대입니다. 이 값이 앞으로도 계속 같은 방향일 것이라고 예측하지는 않습니다.")
    gap_col = VARIABLES["여성채용구성격차"]["column"]
    if gap_col in view.columns:
        gap_by_type = view[["기관유형", gap_col]].dropna().groupby("기관유형")[gap_col].mean().reset_index()
        import plotly.express as px
        fig_gap = px.bar(gap_by_type, x="기관유형", y=gap_col, labels={gap_col: "여성 채용구성 격차 (%p, 평균)"})
        fig_gap.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_gap.update_layout(font=dict(size=15), height=440)
        st.plotly_chart(fig_gap, use_container_width=True)

        rank_mode = st.radio("기관 순위", ["격차 큰 기관 Top 10", "격차 작은(음수) 기관 Top 10"], horizontal=True, key="p7_gaprank")
        st.plotly_chart(
            plot_rank_bar(view, gap_col, var_key="여성채용구성격차", top_n=10,
                           ascending=(rank_mode.startswith("격차 작은"))),
            use_container_width=True,
        )

# ================= TAB 2: 일·가정양립 =================
with tab2:
    wf_vars = get_vars_by_category("일가정양립")
    wf_vars = {k: v for k, v in wf_vars.items() if v["column"] in view.columns}
    st.caption("아래 변수들의 히스토그램·Box plot·기술통계는 → **① 변수분포 및 기술통계** 페이지 [일가정양립] 탭에서 확인할 수 있습니다. "
                "이 탭에서는 기관유형별 비교와 성별 구성과의 관계에 집중합니다.")
    wf_var = st.selectbox("변수 선택", list(wf_vars.keys()), format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p7_wfvar")
    wf_col = VARIABLES[wf_var]["column"]

    st.markdown(f"#### 기관유형별 {get_label(wf_var)}")
    st.plotly_chart(plot_boxplot(view, wf_col, var_key=wf_var), use_container_width=True)

    st.divider()
    st.markdown("#### 여성직원비율과의 관계")
    st.caption("💡 여성직원 비율이 높은 기관에서 남성 육아휴직 이용도 높은가?")
    if "여성직원비율" in view.columns:
        fig_wf = plot_scatter(view, VARIABLES["여성직원비율"]["column"], wf_col, x_key="여성직원비율", y_key=wf_var)
        st.plotly_chart(fig_wf, use_container_width=True)
        sub_wf = view[[VARIABLES["여성직원비율"]["column"], wf_col]].dropna()
        if sub_wf.shape[0] > 2:
            r, p = stats.pearsonr(sub_wf[VARIABLES["여성직원비율"]["column"]], sub_wf[wf_col])
            st.caption(f"Pearson r = {r:.3f} (N = {sub_wf.shape[0]:,})")

    st.divider()
    st.markdown("#### 🤔 탐색해볼 질문")
    st.info("남성 육아휴직 이용은 기관유형별로 얼마나 다른가? 여성직원 비율이 높은 기관에서 남성 육아휴직 이용도 높은가?")

st.divider()

# ---------------- 이어보기 ----------------
st.markdown("### ➡️ 이어보기")
st.markdown(
    "- 정부지원의존도와 신규채용률의 관계가 궁금하다면 → **⑧ 두 변수 관계분석**\n"
    "- 직원평균보수와 신규채용률의 관계가 궁금하다면 → **⑧ 두 변수 관계분석**"
)
