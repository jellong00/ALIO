# -*- coding: utf-8 -*-
"""
공공기관 데이터 탐색형 대시보드
================================
공기업정책학과 석사과정 계량분석 수업용.
파일별·주제별 열람이 아니라, 기관×연도 통합 패널을 기반으로
분포 → 관계 → 비교를 탐색하는 구조로 설계했다.
"""

import numpy as np
import pandas as pd
import streamlit as st
from scipy import stats as scipy_stats

from utils.data import load_dataset, raw_files_exist
from utils.filters import render_cascading_filters, apply_filters
from utils.stats import descriptive_stats, stats_to_display_df
from utils.charts import (
    plot_histogram, plot_boxplot, plot_group_boxplot, plot_rank_bar,
    plot_relationship_scatter, apply_compact_height,
)
from utils.metadata import (
    VARIABLE_META, DISTRIBUTION_VARIABLES, QUESTION_BANK, DEFAULT_QUESTIONS,
    RELATIONSHIP_PRESETS, var_label,
)
from utils.constants import CHART_HEIGHT_COMPACT, CHART_HEIGHT_MAIN, NOTE_CORR, NOTE_AGGREGATE

# ---------------------------------------------------------------------------
# 페이지 설정 / 강의실용 CSS
# ---------------------------------------------------------------------------
st.set_page_config(page_title="공공기관 데이터 탐색 대시보드", page_icon="🏛️", layout="wide", initial_sidebar_state="collapsed")

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.2rem; padding-bottom: 1rem; max-width: 100%;}
    [data-testid="stMetricValue"] {font-size: 1.35rem;}
    [data-testid="stMetricLabel"] {font-size: 0.82rem; opacity: 0.8;}
    .stTabs [data-baseweb="tab"] {font-size: 1.05rem; padding: 0.5rem 1.1rem;}
    .stTabs [data-baseweb="tab-list"] {gap: 0.2rem;}
    div[data-testid="stVerticalBlock"] > div {gap: 0.5rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown("### 🏛️ 공공기관 데이터 탐색 대시보드")

if not raw_files_exist():
    st.warning("⚠️ `data/` 폴더에 필요한 원본 Excel 파일이 없습니다. README.md를 참고해 파일을 넣어주세요.")
    st.stop()

panel = load_dataset("panel")
if panel.empty:
    st.stop()

# ---------------------------------------------------------------------------
# 공통(전역) 종속형 필터 - 모든 탭에서 공유
# ---------------------------------------------------------------------------
filters = render_cascading_filters(panel, key_prefix="global")
year = filters["연도"]
year_df = apply_filters(panel, {**filters, "기관명": "전체"})  # 연도/유형/부처만 반영 (탭별로 기관명은 별도 처리)

tab_names = ["1. 종합현황", "2. 분포 탐색", "3. 변수 관계", "4. 기관 비교", "5. 주제별 상세"]
tab1, tab2, tab3, tab4, tab5 = st.tabs(tab_names)


# ---------------------------------------------------------------------------
# 공통 유틸
# ---------------------------------------------------------------------------
def _fmt(v, decimals=1):
    if pd.isna(v):
        return "자료없음"
    return f"{v:,.{decimals}f}"


def _empty_note(df, msg="선택한 조건을 만족하는 자료가 없습니다."):
    st.caption(f"ℹ️ {msg}")


# ===========================================================================
# 탭 1. 종합현황
# ===========================================================================
with tab1:
    if year_df.empty:
        _empty_note(year_df, "현재 필터 조건을 만족하는 기관이 없습니다.")
    else:
        k1, k2, k3, k4, k5, k6 = st.columns(6)
        k1.metric("분석기관 수", f"{year_df['기관명'].nunique():,}")
        k2.metric("전체 임직원 수", _fmt(year_df["total_workforce"].sum(), 0) + "명" if year_df["total_workforce"].notna().any() else "자료없음")
        k3.metric("평균 신규채용률", _fmt(year_df["new_hire_rate_pct"].mean()) + "%" if year_df["new_hire_rate_pct"].notna().any() else "자료없음")
        k4.metric("직원 평균보수", _fmt(year_df["employee_avg_pay"].mean(), 0) + "천원" if year_df["employee_avg_pay"].notna().any() else "자료없음")
        k5.metric("1인당 복리후생비", _fmt(year_df["welfare_per_capita"].mean(), 0) + "천원" if year_df["welfare_per_capita"].notna().any() else "자료없음")
        k6.metric("정부지원 의존도", _fmt(year_df["gov_dependency_pct"].mean()) + "%" if year_df["gov_dependency_pct"].notna().any() else "자료없음")

        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            if year_df["total_workforce"].notna().any():
                st.plotly_chart(apply_compact_height(plot_histogram(year_df["total_workforce"], "임직원 수 분포", "명"), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(year_df, "임직원 수 자료가 없습니다.")
        with r1c2:
            if year_df["employee_avg_pay"].notna().any():
                st.plotly_chart(apply_compact_height(plot_histogram(year_df["employee_avg_pay"], "평균보수 분포", "천원"), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(year_df, "평균보수 자료가 없습니다.")
        with r1c3:
            if year_df["gov_dependency_pct"].notna().any():
                st.plotly_chart(apply_compact_height(plot_histogram(year_df["gov_dependency_pct"], "정부의존도 분포", "%"), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(year_df, "정부의존도 자료가 없습니다.")

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            gdf = year_df.dropna(subset=["employee_avg_pay", "기관유형"])
            if not gdf.empty:
                st.plotly_chart(apply_compact_height(plot_group_boxplot(gdf, "employee_avg_pay", "기관유형", "기관유형별 평균보수", "천원"), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(gdf)
        with r2c2:
            gdf2 = year_df.dropna(subset=["new_hire_rate_pct", "기관유형"])
            if not gdf2.empty:
                st.plotly_chart(apply_compact_height(plot_group_boxplot(gdf2, "new_hire_rate_pct", "기관유형", "기관유형별 신규채용률", "%"), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(gdf2)
        with r2c3:
            rdf = year_df.dropna(subset=["employee_avg_pay", "기관명"])
            if not rdf.empty:
                st.plotly_chart(apply_compact_height(plot_rank_bar(rdf, "기관명", "employee_avg_pay", top_n=10, title="평균보수 상위 10개 기관", unit="천원"), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(rdf)

        st.caption(NOTE_AGGREGATE)


# ===========================================================================
# 탭 2. 분포 탐색
# ===========================================================================
with tab2:
    label_to_key = {var_label(k): k for k in DISTRIBUTION_VARIABLES}
    c1, c2 = st.columns([2, 1])
    with c1:
        chosen_label = st.selectbox("변수 선택", list(label_to_key.keys()), key="dist_var")
    var_key = label_to_key[chosen_label]
    meta = VARIABLE_META[var_key]

    dist_df = year_df.dropna(subset=[var_key]) if var_key in year_df.columns else pd.DataFrame()

    if dist_df.empty:
        _empty_note(dist_df, f"'{meta['label']}' 지표는 현재 필터 조건에서 자료가 없습니다.")
    else:
        stats = descriptive_stats(dist_df[var_key])
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("N", f"{stats['n_valid']:,}")
        m2.metric("평균", _fmt(stats["mean"]))
        m3.metric("중앙값", _fmt(stats["median"]))
        m4.metric("표준편차", _fmt(stats["std"]))
        m5.metric("최솟값", _fmt(stats["min"]))
        m6.metric("최댓값", _fmt(stats["max"]))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.plotly_chart(apply_compact_height(plot_histogram(dist_df[var_key], f"{meta['label']} 히스토그램", meta["unit"]), CHART_HEIGHT_COMPACT), use_container_width=True)
        with c2:
            gdf = dist_df.dropna(subset=["기관유형"])
            if not gdf.empty:
                st.plotly_chart(apply_compact_height(plot_group_boxplot(gdf, var_key, "기관유형", f"기관유형별 {meta['label']}", meta["unit"]), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(gdf)
        with c3:
            st.plotly_chart(apply_compact_height(plot_rank_bar(dist_df, "기관명", var_key, top_n=10, title="상위 10개 기관", unit=meta["unit"]), CHART_HEIGHT_COMPACT), use_container_width=True)
        with c4:
            if len(dist_df) >= 5:
                st.plotly_chart(apply_compact_height(plot_rank_bar(dist_df, "기관명", var_key, top_n=10, title="하위 10개 기관", unit=meta["unit"], ascending=True), CHART_HEIGHT_COMPACT), use_container_width=True)
            else:
                _empty_note(dist_df, "하위 기관을 구분하기에 관측치가 부족합니다.")

        questions = QUESTION_BANK.get(var_key, DEFAULT_QUESTIONS)
        st.info("💭 생각해보기\n\n" + "\n\n".join(f"- {q}" for q in questions))
        st.caption(f"출처: {meta['source']}")


# ===========================================================================
# 탭 3. 변수 관계
# ===========================================================================
with tab3:
    preset_labels = ["직접 선택"] + [p["label"] for p in RELATIONSHIP_PRESETS]
    c1, c2, c3, c4, c5 = st.columns([2, 1.4, 1.4, 1, 1])
    with c1:
        preset_label = st.selectbox("추천 관계", preset_labels, key="rel_preset")

    preset = next((p for p in RELATIONSHIP_PRESETS if p["label"] == preset_label), None)
    default_x = preset["x"] if preset else DISTRIBUTION_VARIABLES[0]
    default_y = preset["y"] if preset else DISTRIBUTION_VARIABLES[1]

    label_to_key = {var_label(k): k for k in DISTRIBUTION_VARIABLES}
    key_to_label = {v: k for k, v in label_to_key.items()}

    with c2:
        x_label = st.selectbox("X 변수", list(label_to_key.keys()),
                                index=list(label_to_key.keys()).index(key_to_label[default_x]), key="rel_x")
    with c3:
        y_label = st.selectbox("Y 변수", list(label_to_key.keys()),
                                index=list(label_to_key.keys()).index(key_to_label[default_y]), key="rel_y")
    with c4:
        color_choice = st.selectbox("색상 구분", ["기관유형", "주무부처", "없음"], key="rel_color")
    with c5:
        size_choice = st.selectbox("버블 크기", ["없음", "임직원 수"], key="rel_size")

    x_key = label_to_key[x_label]
    y_key = label_to_key[y_label]
    color_col = None if color_choice == "없음" else color_choice
    size_col = "total_workforce" if size_choice == "임직원 수" else None

    o1, o2, o3 = st.columns(3)
    with o1:
        log_x = st.checkbox("X축 로그", key="rel_logx")
    with o2:
        log_y = st.checkbox("Y축 로그", key="rel_logy")
    with o3:
        trendline = st.checkbox("추세선 표시 (단순 선형)", key="rel_trend")

    subset_cols = [x_key, y_key] + [c for c in [color_col, size_col] if c]
    rel_df = year_df.dropna(subset=[c for c in subset_cols if c in year_df.columns])

    if rel_df.empty or x_key not in year_df.columns or y_key not in year_df.columns:
        _empty_note(rel_df, "선택한 두 변수를 동시에 가진 기관이 없습니다.")
    else:
        fig, plotted_df = plot_relationship_scatter(
            rel_df, x_key, y_key,
            title=f"{var_label(x_key)} vs {var_label(y_key)} ({year}년)",
            color_col=color_col, size_col=size_col, log_x=log_x, log_y=log_y,
            trendline=trendline, height=CHART_HEIGHT_MAIN,
        )
        cchart, cstat = st.columns([3, 1])
        with cchart:
            st.plotly_chart(fig, use_container_width=True)
        with cstat:
            n = len(plotted_df)
            r = plotted_df[x_key].corr(plotted_df[y_key]) if n >= 3 else np.nan
            st.metric("N", f"{n:,}")
            st.metric("Pearson r", f"{r:.3f}" if pd.notna(r) else "-")
            st.metric(f"{var_label(x_key)} 평균", _fmt(plotted_df[x_key].mean()))
            st.metric(f"{var_label(y_key)} 평균", _fmt(plotted_df[y_key].mean()))
            with st.expander("Spearman 상관계수 (선택)"):
                if n >= 3:
                    rho, _ = scipy_stats.spearmanr(plotted_df[x_key], plotted_df[y_key])
                    st.write(f"ρ = {rho:.3f}")
                else:
                    st.write("관측치 부족")

        st.info(NOTE_CORR)
        if preset:
            st.info(f"💭 생각해보기: {preset['question']}")
        st.caption("추세선은 단순 선형 참고선일 뿐, 회귀모형의 추정 결과를 의미하지 않습니다.")


# ===========================================================================
# 탭 4. 기관 비교
# ===========================================================================
with tab4:
    if filters["기관명"] != "전체":
        selected_inst = filters["기관명"]
    else:
        inst_options = sorted(year_df["기관명"].dropna().unique().tolist())
        selected_inst = st.selectbox("비교할 기관 선택", inst_options, key="compare_inst") if inst_options else None

    if not selected_inst:
        _empty_note(year_df, "비교할 기관을 선택해주세요.")
    else:
        inst_row_df = year_df[year_df["기관명"] == selected_inst]
        if inst_row_df.empty:
            _empty_note(inst_row_df, f"{selected_inst}의 {year}년 자료가 없습니다.")
        else:
            inst_row = inst_row_df.iloc[0]
            inst_type = inst_row["기관유형"]
            inst_dept = inst_row["주무부처"]

            st.markdown(f"**{selected_inst}** · {inst_type} · {inst_dept} · {year}년 기준")

            compare_vars = [
                ("employee_avg_pay", "직원 평균보수"), ("new_hire_rate_pct", "신규채용률"),
                ("welfare_per_capita", "1인당 복리후생비"), ("gov_dependency_pct", "정부지원 의존도"),
                ("fill_rate_pct", "정원충족률"), ("executive_pay_multiple", "기관장 보수배율"),
            ]

            k_cols = st.columns(6)
            for col, (vkey, vlabel) in zip(k_cols, compare_vars):
                val = inst_row.get(vkey)
                col.metric(vlabel, _fmt(val) if pd.notna(val) else "자료없음")

            type_df = year_df[year_df["기관유형"] == inst_type]
            dept_df = year_df[year_df["주무부처"] == inst_dept]

            rows = []
            for vkey, vlabel in compare_vars:
                sel_val = inst_row.get(vkey)
                all_avg = year_df[vkey].mean() if vkey in year_df.columns else np.nan
                type_avg = type_df[vkey].mean() if vkey in type_df.columns else np.nan
                dept_avg = dept_df[vkey].mean() if vkey in dept_df.columns else np.nan
                rows.append({
                    "지표": vlabel, f"{selected_inst}": sel_val,
                    "전체기관 평균": all_avg, "동일 기관유형 평균": type_avg, "동일 주무부처 평균": dept_avg,
                })
            compare_table = pd.DataFrame(rows).round(1)
            st.dataframe(compare_table, hide_index=True, use_container_width=True)

            st.subheader("비교지수 (동일 기관유형 평균 = 100)")
            index_rows = []
            for vkey, vlabel in compare_vars:
                sel_val = inst_row.get(vkey)
                type_avg = type_df[vkey].mean() if vkey in type_df.columns else np.nan
                if pd.notna(sel_val) and pd.notna(type_avg) and type_avg != 0:
                    index_rows.append({"지표": vlabel, "비교지수": round(sel_val / type_avg * 100, 1)})
            if index_rows:
                import plotly.express as px
                idx_df = pd.DataFrame(index_rows)
                fig = px.bar(idx_df, x="비교지수", y="지표", orientation="h")
                fig.add_vline(x=100, line_dash="dash", line_color="gray")
                fig.update_layout(template="plotly_white", height=CHART_HEIGHT_COMPACT, title="")
                st.plotly_chart(fig, use_container_width=True)
            else:
                _empty_note(pd.DataFrame(), "비교지수를 계산할 자료가 부족합니다.")

            st.caption(NOTE_AGGREGATE)


# ===========================================================================
# 탭 5. 주제별 상세 (보조 영역)
# ===========================================================================
with tab5:
    sub_names = ["인력·채용", "보수·임원", "복리후생", "일·가정 양립", "수입·지출"]
    sub_tabs = st.tabs(sub_names)

    def render_topic_overview(dataset_key, item_col="항목", extra_filter=None, note=""):
        long_df = load_dataset(dataset_key)
        if long_df.empty:
            _empty_note(long_df, "해당 지표의 원자료를 찾지 못했습니다.")
            return
        ldf = long_df[long_df["연도"] == year]
        if extra_filter:
            for k, v in extra_filter.items():
                if k in ldf.columns:
                    ldf = ldf[ldf[k] == v]
        if filters["기관유형"] != "전체" and "기관유형" in ldf.columns:
            ldf = ldf[ldf["기관유형"] == filters["기관유형"]]
        if filters["주무부처"] != "전체" and "주무부처" in ldf.columns:
            ldf = ldf[ldf["주무부처"] == filters["주무부처"]]

        if ldf.empty:
            _empty_note(ldf, f"{year}년에는 이 지표가 공시되지 않았거나, 현재 필터 조건을 만족하는 기관이 없습니다.")
            return

        rows = []
        for item in sorted(ldf[item_col].dropna().unique()):
            sub = ldf[ldf[item_col] == item]["값"]
            s = descriptive_stats(sub)
            rows.append({
                "항목": item, "N": s["n_valid"],
                "평균": round(s["mean"], 1) if pd.notna(s["mean"]) else None,
                "중앙값": round(s["median"], 1) if pd.notna(s["median"]) else None,
                "0 비율(%)": s["zero_pct"],
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if note:
            st.caption(note)

    with sub_tabs[0]:
        st.markdown("**임직원 현황**")
        render_topic_overview("employees")
        st.markdown("**신규채용 현황**")
        render_topic_overview("recruitment")

    with sub_tabs[1]:
        st.markdown("**직원 평균보수** (정규직·일반정규직 기준)")
        render_topic_overview("compensation", extra_filter={"구분": "정규직(일반정규직)"})
        st.markdown("**임원연봉** (상임기관장 기준)")
        render_topic_overview("executive_pay", extra_filter={"구분": "상임기관장"})

    with sub_tabs[2]:
        st.markdown("**복리후생비** (0값과 결측은 다릅니다 — 0은 값이 0, 결측은 자료 없음)")
        render_topic_overview("welfare")
        st.markdown("**기관장 업무추진비**")
        render_topic_overview("business_expense")

    with sub_tabs[3]:
        st.markdown("**육아휴직 사용자 수**")
        render_topic_overview("parental_leave", item_col="구분")

    with sub_tabs[4]:
        st.markdown("**수입·지출 현황**")
        render_topic_overview("finance")
        st.markdown("**법인세**")
        render_topic_overview("tax")
