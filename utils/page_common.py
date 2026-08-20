"""
page_common.py
--------------
Page 2~5 (기관특성/재정구조/조직운영/인사결과)가 공유하는 공통 UI 구조.

레이아웃:
[영역 설명] → [변수 선택] → [KPI] → [Histogram | 기관유형별 Box Plot]
→ [연도별 추세 | 기관 Top/Bottom] → [이 변수와 다른 변수의 관계 보기]
"""

import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel, describe_var
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_domain, DOMAINS, get_label, get_unit
from utils.charts import (
    plot_histogram, plot_group_box, plot_time_series, plot_rank_chart, plot_scatter
)


def render_domain_page(domain: str, question: str, intro: str):
    st.set_page_config(page_title=domain, layout="wide")
    st.title(domain)
    st.markdown("#### 오늘의 질문")
    st.info(question)
    st.caption(intro)

    panel = get_full_panel()
    df = sidebar_filters(panel, key_prefix=f"pg_{domain}")

    domain_vars = get_vars_by_domain(domain)
    var_key = st.selectbox(
        "변수 선택", list(domain_vars.keys()),
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)}) — {VARIABLES[k]['description']}",
        key=f"{domain}_var",
    )
    col = VARIABLES[var_key]["column"]
    if col not in df.columns:
        st.warning("선택한 변수가 데이터에 없습니다.")
        return None, None, None

    st.divider()

    # ---- 기술통계 (KPI) ----
    desc = describe_var(df, col)
    if desc.get("N", 0) == 0:
        st.warning("선택한 조건에서 유효한 관측치가 없습니다.")
        return None, None, None

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("N", f"{desc['N']:,}")
    k2.metric("평균", f"{desc['평균']:,.1f}")
    k3.metric("중앙값", f"{desc['중앙값']:,.1f}")
    k4.metric("표준편차", f"{desc['표준편차']:,.1f}")
    k5.metric("최소", f"{desc['최소']:,.1f}")
    k6.metric("최대", f"{desc['최대']:,.1f}")
    st.caption(f"결측률: {desc['결측률']*100:.1f}%")

    # ---- Histogram / Box plot ----
    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(plot_histogram(df, col, var_key=var_key), use_container_width=True)
        with st.expander("📌 확인할 것 / 💡 포인트"):
            st.markdown("- 분포의 형태(치우침, 이상치)를 확인한다.\n- 평균과 중앙값이 크게 다르면 분포가 비대칭일 가능성이 높다.")
    with c2:
        st.plotly_chart(plot_group_box(df, col, var_key=var_key), use_container_width=True)
        with st.expander("📌 확인할 것 / ⚠️ 주의할 점"):
            st.markdown("- 기관유형 간 분포 차이는 '차이'이지 '원인'이 아니다.")

    # ---- 연도별 추세 / Top-Bottom ----
    c3, c4 = st.columns(2)
    with c3:
        st.plotly_chart(plot_time_series(df, col, var_key=var_key, agg="기관유형평균"), use_container_width=True)
    with c4:
        rank_mode = st.radio("순위", ["Top 10", "Bottom 10"], horizontal=True, key=f"{domain}_rankmode")
        st.plotly_chart(
            plot_rank_chart(df, col, var_key=var_key, top_n=10, ascending=(rank_mode == "Bottom 10")),
            use_container_width=True,
        )

    st.divider()

    # ---- 다른 변수와의 관계 ----
    st.markdown(f"### 🔗 '{get_label(var_key)}'와(과) 다른 변수의 관계 보기")
    rc1, rc2 = st.columns(2)
    with rc1:
        rel_domain = st.selectbox("관계 변수 영역", DOMAINS, key=f"{domain}_reldomain")
    other_vars = {k: v for k, v in get_vars_by_domain(rel_domain).items() if k != var_key}
    with rc2:
        rel_key = st.selectbox(
            "관계 변수", list(other_vars.keys()),
            format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key=f"{domain}_relvar"
        )
    rel_col = VARIABLES[rel_key]["column"]

    sc1, sc2 = st.columns([2, 1])
    if rel_col in df.columns:
        with sc1:
            fig = plot_scatter(df, col, rel_col, x_key=var_key, y_key=rel_key)
            st.plotly_chart(fig, use_container_width=True)
        with sc2:
            sub = df[[col, rel_col]].dropna()
            if sub.shape[0] > 2:
                r, p = stats.pearsonr(sub[col], sub[rel_col])
                st.metric("Pearson r", f"{r:.3f}")
                st.metric("p-value", f"{p:.4f}")
                st.metric("N", f"{sub.shape[0]:,}")
            st.caption("⚠️ 상관관계는 '관계'이지 '영향'이 아닙니다.")
    else:
        st.warning("선택한 관계 변수가 데이터에 없습니다.")

    return df, var_key, col
