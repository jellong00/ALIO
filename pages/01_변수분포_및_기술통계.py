import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats as scipy_stats

from utils.data_cleaner import get_full_panel, describe_var, percentile_rank, latest_snapshot
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit, get_question
from utils.charts import plot_histogram, plot_boxplot
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="변수분포 및 기술통계", layout="wide")
st.title("① 변수분포 및 기술통계")
render_intro(
    purpose="선택한 변수 하나의 분포, 대표값, 산포, 이상치를 확인합니다. 이 페이지는 모든 변수에 대한 분포 탐색(EDA)의 출발점입니다.",
    unit="아래에서 선택한 연도의 기관 (기본값: 최신연도, 기관 1개 = 관측치 1개)",
    methods="기술통계량 · 히스토그램 · Box plot · 왜도 · 원자료/로그변환 비교 · 이상치 기관 확인",
    caution="이 페이지는 변수 하나만 봅니다. 기관유형·주무부처에 따른 차이는 ②③번 페이지에서, 다른 페이지의 재정·보수·채용 등 각 주제 페이지에서 분포를 보고 싶다면 이 페이지로 돌아와서 확인하세요.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p1")
view, caption, mode = year_slice(df, key_prefix="p1")
st.caption(caption)

st.divider()


def render_variable_eda(view: pd.DataFrame, category: str, key_prefix: str):
    cat_vars = get_vars_by_category(category)
    cat_vars = {k: v for k, v in cat_vars.items() if v["column"] in view.columns}
    if not cat_vars:
        st.info("이 카테고리에는 사용 가능한 변수가 없습니다.")
        return

    var_key = st.selectbox(
        "변수 선택", list(cat_vars.keys()),
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key=f"{key_prefix}_var"
    )
    col = VARIABLES[var_key]["column"]

    # ---------------- 원자료 / 로그변환 ----------------
    log_allowed = VARIABLES[var_key]["log_allowed"]
    use_col = col
    use_label = get_label(var_key)
    use_unit = get_unit(var_key)
    plot_df = view

    if log_allowed:
        view_mode = st.radio("보기 방식", ["원자료", "log 변환"], horizontal=True, key=f"{key_prefix}_logmode")
        if view_mode == "log 변환":
            raw = view[[col]].dropna()
            n_before = raw.shape[0]
            positive = raw[raw[col] > 0].copy()
            n_after = positive.shape[0]
            log_col = f"log_{col}"
            positive[log_col] = np.log(positive[col])
            plot_df = positive
            use_col = log_col
            use_label = f"log({get_label(var_key)})"
            use_unit = "log 스케일"
            st.caption(f"0 이하 값은 로그변환에서 제외됩니다: N {n_before:,} → {n_after:,} "
                        f"(오른쪽으로 심하게 치우친 금액·규모 변수는 로그를 사용하면 분포가 덜 비대칭적으로 보일 수 있습니다. 로그가 정규성을 '만들어주는' 것은 아닙니다.)")

    desc = describe_var(plot_df, use_col)
    if desc.get("N", 0) == 0:
        st.warning("선택한 조건에서 유효한 관측치가 없습니다.")
        return

    st.markdown(f"### 📐 {use_label} 기술통계")
    r1 = st.columns(5)
    r1[0].metric("N", f"{desc['N']:,}")
    r1[1].metric("결측치 수", f"{desc['결측치수']:,}")
    r1[2].metric("결측률", f"{desc['결측률']*100:.1f}%")
    r1[3].metric("평균", f"{desc['평균']:,.2f}")
    r1[4].metric("중앙값", f"{desc['중앙값']:,.2f}")
    r2 = st.columns(5)
    r2[0].metric("표준편차", f"{desc['표준편차']:,.2f}")
    r2[1].metric("Q1", f"{desc['Q1']:,.2f}")
    r2[2].metric("Q3", f"{desc['Q3']:,.2f}")
    r2[3].metric("최소", f"{desc['최소']:,.2f}")
    r2[4].metric("최대", f"{desc['최대']:,.2f}")

    skew_val = scipy_stats.skew(plot_df[use_col].dropna())
    st.metric("왜도 (skewness)", f"{skew_val:,.2f}")
    st.caption("0에 가까울수록 대칭에 가깝고, 양수가 크면 오른쪽 꼬리가 긴 분포입니다 (왜도만으로 정규성을 판정할 수는 없습니다).")

    nbins = st.slider("히스토그램 구간(bin) 수", 10, 80, 30, key=f"{key_prefix}_nbins")
    clip = st.checkbox("극단값 영향 줄이기 (상하위 1% 밖은 축 범위에서 제외하고 보기)", value=True, key=f"{key_prefix}_clip")
    st.caption("💡 평균만으로는 알 수 없는 분포의 비대칭성과 극단값을 확인합니다.")
    fig = plot_histogram(plot_df, use_col, var_key=None, nbins=nbins, clip_extreme=clip)
    fig.update_xaxes(title=f"{use_label} ({use_unit})")
    st.plotly_chart(fig, use_container_width=True, key=f"{key_prefix}_hist")
    st.caption("범례: 주황 실선 = 평균, 초록 점선 = 중앙값 (선 위 숫자는 값입니다)")

    st.divider()
    st.markdown("### 📦 전체 분포 (Box plot)")
    import plotly.express as px
    box_data = plot_df[[use_col]].dropna()
    fig_box = px.box(box_data, y=use_col, points="outliers", labels={use_col: f"{use_label} ({use_unit})"})
    fig_box.update_layout(font=dict(size=16), height=460)
    if clip and not box_data.empty:
        lo, hi = np.percentile(box_data[use_col], [1, 99])
        if lo != hi:
            pad = (hi - lo) * 0.15
            fig_box.update_yaxes(range=[lo - pad, hi + pad])
        st.caption("극단값 영향 줄이기가 켜져 있어 y축 범위를 상하위 1% 기준으로 조정했습니다.")
    st.plotly_chart(fig_box, use_container_width=True, key=f"{key_prefix}_box")

    st.divider()
    st.markdown("### 🔎 Top 5 · Bottom 5 기관")
    snap_named = view[["기관명", "기관유형", "주무부처", col]].dropna().sort_values(col)
    if not snap_named.empty:
        ec1, ec2 = st.columns(2)
        with ec1:
            st.markdown("**Bottom 5 (값이 가장 작은 5개 기관)**")
            st.dataframe(snap_named.head(5).rename(columns={col: get_label(var_key)}), use_container_width=True, hide_index=True)
        with ec2:
            st.markdown("**Top 5 (값이 가장 큰 5개 기관)**")
            st.dataframe(snap_named.tail(5).sort_values(col, ascending=False).rename(columns={col: get_label(var_key)}),
                         use_container_width=True, hide_index=True)
        st.caption("💡 기관유형·주무부처별 비교, 특정 기관의 상세 순위는 ②③⑩번 페이지에서 확인할 수 있습니다.")

    st.divider()
    st.markdown("### 🤔 생각해볼 질문")
    st.info(get_question(var_key))


tabs = st.tabs([f"[{c}]" for c in CATEGORIES])
for cat, tab in zip(CATEGORIES, tabs):
    with tab:
        render_variable_eda(view, cat, key_prefix=f"p1_{cat}")
