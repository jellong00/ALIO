import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit, get_allowed_agg, ORG_TYPE_COLORS
from utils.charts import plot_rank_scatter
from utils.page_header import render_intro

st.set_page_config(page_title="시간 변화", layout="wide")
st.title("⑪ 시간 변화")
render_intro(
    purpose="공공기관 지표가 시간에 따라 수준·변화율·순위·기관 간 격차 측면에서 어떻게 달라졌는지 살펴봅니다.",
    unit="[수준 변화] 탭은 연도별 전체 기관-연도, 나머지 탭은 선택한 두 연도 사이의 변화를 사용합니다.",
    methods="[수준 변화] [변화율] [순위 변화] [기관 간 격차] — 탭으로 분리",
    caution="합계 추이는 기관 수 변화의 영향을, 평균 추이는 이상치 기관 하나의 영향을 크게 받을 수 있습니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p11")

TREND_VARS = [
    "임직원수", "여성직원비율", "신규채용자수", "신규채용률",
    "직원평균보수", "1인당복리후생비", "기관장연봉",
    "총수입", "총지출", "정부지원의존도", "법인세결정세액",
    "여성육아휴직사용자수", "남성육아휴직사용자수",
]
TREND_VARS = [v for v in TREND_VARS if VARIABLES[v]["column"] in df.columns]

st.divider()

tab_level, tab_growth, tab_rank, tab_gap = st.tabs(["📈 수준 변화", "📐 변화율", "🔄 순위 변화", "📊 기관 간 격차"])

# ================= TAB 1: 수준 변화 =================
with tab_level:
    c1, c2 = st.columns(2)
    with c1:
        var_key = st.selectbox("변수 선택 (13개)", TREND_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p11_var")
    allowed = get_allowed_agg(var_key)
    with c2:
        agg = st.radio("집계 방식", allowed, horizontal=True, key="p11_agg")
    col = VARIABLES[var_key]["column"]
    agg_func = "mean" if agg == "평균" else "sum"

    st.markdown(f"### 연도별 {agg} 추이 — 비교 수준 선택")
    st.caption("전체·기관유형·주무부처·개별기관 중 원하는 선을 골라 한 그래프에서 비교합니다 (최대 4개 권장). "
                "기관유형을 고르면 주무부처 목록이, 주무부처를 고르면 개별기관 목록이 그 안으로 좁혀집니다.")

    lc1, lc2, lc3, lc4 = st.columns(4)
    with lc1:
        show_overall = st.checkbox("전체 평균/합계", value=True, key="p11_showoverall")
    with lc2:
        sel_types = st.multiselect("기관유형", sorted(df["기관유형"].unique()), key="p11_seltypes")

    dept_pool = df[df["기관유형"].isin(sel_types)] if sel_types else df
    dept_options = sorted(dept_pool["주무부처"].unique())
    if "p11_seldepts" in st.session_state:
        st.session_state["p11_seldepts"] = [d for d in st.session_state["p11_seldepts"] if d in dept_options]
    with lc3:
        sel_depts = st.multiselect("주무부처", dept_options, key="p11_seldepts")

    org_pool = dept_pool[dept_pool["주무부처"].isin(sel_depts)] if sel_depts else dept_pool
    org_options = sorted(org_pool["기관명"].unique())
    if "p11_selorgs" in st.session_state:
        st.session_state["p11_selorgs"] = [o for o in st.session_state["p11_selorgs"] if o in org_options]
    with lc4:
        sel_orgs_trend = st.multiselect("개별기관", org_options, key="p11_selorgs")

    n_lines = int(show_overall) + len(sel_types) + len(sel_depts) + len(sel_orgs_trend)
    if n_lines > 4:
        st.warning(f"⚠️ 현재 {n_lines}개 선이 선택되었습니다. 4개 이하로 선택하면 더 읽기 쉽습니다.")

    fig1 = go.Figure()
    if show_overall:
        overall = df.groupby("연도")[col].agg(agg_func).reset_index()
        fig1.add_trace(go.Scatter(x=overall["연도"], y=overall[col], mode="lines+markers", name="전체",
                                    line=dict(width=3, color="#333333")))
    palette = ["#4C78A8", "#E07B39", "#2CA02C", "#D62728", "#9467BD", "#8C564B"]
    pi = 0
    for t in sel_types:
        d = df[df["기관유형"] == t].groupby("연도")[col].agg(agg_func).reset_index()
        fig1.add_trace(go.Scatter(x=d["연도"], y=d[col], mode="lines+markers", name=f"{t} 평균" if agg == "평균" else f"{t} 합계",
                                    line=dict(width=2, color=palette[pi % len(palette)], dash="dash")))
        pi += 1
    for dpt in sel_depts:
        d = df[df["주무부처"] == dpt].groupby("연도")[col].agg(agg_func).reset_index()
        fig1.add_trace(go.Scatter(x=d["연도"], y=d[col], mode="lines+markers", name=f"{dpt} 평균" if agg == "평균" else f"{dpt} 합계",
                                    line=dict(width=2, color=palette[pi % len(palette)], dash="dot")))
        pi += 1
    for org in sel_orgs_trend:
        d = df[df["기관명"] == org][["연도", col]].dropna()
        fig1.add_trace(go.Scatter(x=d["연도"], y=d[col], mode="lines+markers", name=org,
                                    line=dict(width=2, color=palette[pi % len(palette)])))
        pi += 1

    fig1.update_layout(font=dict(size=16), height=560, yaxis_title=f"{get_label(var_key)} ({get_unit(var_key)})", xaxis_title="연도")
    st.plotly_chart(fig1, use_container_width=True)

    st.divider()
    st.markdown("#### 평균과 중앙값 추이")
    st.caption("💡 특정 연도에 극단값이 평균을 끌어올리는지 확인할 수 있습니다.")
    show_mm = st.multiselect("표시할 선", ["평균", "중앙값"], default=["평균", "중앙값"], key="p11_mmlines")
    if show_mm:
        fig_mm = go.Figure()
        if "평균" in show_mm:
            mm_mean = df.groupby("연도")[col].mean().reset_index()
            fig_mm.add_trace(go.Scatter(x=mm_mean["연도"], y=mm_mean[col], mode="lines+markers", name="평균",
                                          line=dict(width=3, color="#E07B39")))
        if "중앙값" in show_mm:
            mm_med = df.groupby("연도")[col].median().reset_index()
            fig_mm.add_trace(go.Scatter(x=mm_med["연도"], y=mm_med[col], mode="lines+markers", name="중앙값",
                                          line=dict(width=3, color="#2CA02C", dash="dash")))
        fig_mm.update_layout(font=dict(size=16), height=440, yaxis_title=f"{get_label(var_key)} ({get_unit(var_key)})")
        st.plotly_chart(fig_mm, use_container_width=True)

# ================= TAB 2 & 3: 변화율 / 순위 변화 (공통 기간 선택) =================
years = sorted(df["연도"].unique())
if len(years) >= 2:
    with tab_growth:
        st.caption("이 탭과 [순위 변화] 탭은 아래에서 고른 두 연도 사이의 변화만 사용합니다 (여러 기간을 한꺼번에 섞지 않습니다).")
        gvar_key = st.selectbox("변수 선택 (13개)", TREND_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p11_gvar")
        gcol = VARIABLES[gvar_key]["column"]
        is_ratio = VARIABLES[gvar_key]["percent"]
        change_label = "증감 (%p)" if is_ratio else "증가율 (%)"

        c1, c2 = st.columns(2)
        with c1:
            y_from = st.selectbox("기준 연도(이전)", years[:-1], index=len(years) - 2, key="p11_yfrom")
        with c2:
            y_to_options = [y for y in years if y > y_from]
            y_to = st.selectbox("비교 연도(이후)", y_to_options, index=0, key="p11_yto")

        d_from = df[df["연도"] == y_from][["기관명", "기관유형", gcol]].dropna().rename(columns={gcol: "이전값"})
        d_to = df[df["연도"] == y_to][["기관명", "기관유형", gcol]].dropna().rename(columns={gcol: "이후값"})
        merged = pd.merge(d_from, d_to, on=["기관명", "기관유형"])

        if is_ratio:
            merged["변화"] = merged["이후값"] - merged["이전값"]
        else:
            n_before_zero = merged.shape[0]
            merged = merged[merged["이전값"] != 0]
            n_excluded_zero = n_before_zero - merged.shape[0]
            merged["변화"] = (merged["이후값"] - merged["이전값"]) / merged["이전값"] * 100
            if n_excluded_zero > 0:
                st.caption(f"⚠️ 기준연도({y_from}년) 값이 0인 기관 {n_excluded_zero:,}개는 증가율 계산에서 제외되었습니다.")
        merged = merged.replace([float("inf"), float("-inf")], pd.NA).dropna(subset=["변화"])

        if merged.empty:
            st.info("선택한 기간에 비교 가능한 관측치가 부족합니다.")
        else:
            st.markdown(f"### {y_from}년 → {y_to}년 {change_label} 분포")
            m1, m2, m3 = st.columns(3)
            m1.metric(f"평균 {change_label}", f"{merged['변화'].mean():,.1f}")
            m2.metric("중앙값", f"{merged['변화'].median():,.1f}")
            m3.metric("N", f"{merged.shape[0]:,}")
            fig3 = px.histogram(merged, x="변화", nbins=40, labels={"변화": f"{get_label(gvar_key)} {change_label}"})
            fig3.update_layout(font=dict(size=16), height=450, showlegend=False)
            st.plotly_chart(fig3, use_container_width=True)

            st.markdown("### 증가/감소 Top 10")
            rank_mode = st.radio("정렬", ["증가 Top 10", "감소 Top 10"], horizontal=True, key="p11_growrank")
            ranked = merged.sort_values("변화", ascending=(rank_mode == "감소 Top 10")).head(10)
            fig4 = px.bar(ranked, x="변화", y="기관명", orientation="h", color="기관유형",
                           color_discrete_map=ORG_TYPE_COLORS, labels={"변화": f"{get_label(gvar_key)} {change_label}"})
            fig4.update_layout(font=dict(size=16), height=420)
            st.plotly_chart(fig4, use_container_width=True)

            st.divider()
            st.markdown(f"### 다른 변수의 {y_from}→{y_to} 변화와의 관계")
            other_vars = [v for v in TREND_VARS if v != gvar_key]
            other_key = st.selectbox("비교할 변수", other_vars, format_func=lambda k: get_label(k), key="p11_otherg")
            other_col = VARIABLES[other_key]["column"]
            other_is_ratio = VARIABLES[other_key]["percent"]
            other_label = "증감(%p)" if other_is_ratio else "증가율(%)"

            od_from = df[df["연도"] == y_from][["기관명", other_col]].dropna().rename(columns={other_col: "이전값2"})
            od_to = df[df["연도"] == y_to][["기관명", other_col]].dropna().rename(columns={other_col: "이후값2"})
            omerged = pd.merge(od_from, od_to, on="기관명")
            if other_is_ratio:
                omerged["변화2"] = omerged["이후값2"] - omerged["이전값2"]
            else:
                omerged = omerged[omerged["이전값2"] != 0]
                omerged["변화2"] = (omerged["이후값2"] - omerged["이전값2"]) / omerged["이전값2"] * 100
            omerged = omerged.replace([float("inf"), float("-inf")], pd.NA).dropna(subset=["변화2"])

            joint = pd.merge(merged[["기관명", "변화"]], omerged[["기관명", "변화2"]], on="기관명")
            if joint.shape[0] > 3:
                fig6 = px.scatter(joint, x="변화", y="변화2", trendline="ols",
                                    labels={"변화": f"{get_label(gvar_key)} {change_label}", "변화2": f"{get_label(other_key)} {other_label}"})
                fig6.update_layout(font=dict(size=16), height=480)
                st.plotly_chart(fig6, use_container_width=True)
                r, p = stats.pearsonr(joint["변화"], joint["변화2"])
                st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {joint.shape[0]:,}")
            else:
                st.info("관계를 계산할 만큼 관측치가 부족합니다.")

    with tab_rank:
        st.caption(f"[변화율] 탭에서 고른 변수({get_label(gvar_key)})와 기간({y_from}년→{y_to}년)을 그대로 사용합니다.")
        if not merged.empty:
            merged["순위_이전"] = merged["이전값"].rank(ascending=False)
            merged["순위_이후"] = merged["이후값"].rank(ascending=False)
            if merged.shape[0] > 3:
                rho, p = stats.spearmanr(merged["순위_이전"], merged["순위_이후"])
                st.write(f"**Spearman 순위상관계수** = {rho:.3f} (p = {p:.4f}, N = {merged.shape[0]:,})")
                fig5 = plot_rank_scatter(merged, "순위_이전", "순위_이후", f"{y_from}년 순위", f"{y_to}년 순위")
                st.plotly_chart(fig5, use_container_width=True)
                st.caption("💡 대각선(점선)에 가까울수록 두 연도의 순위가 유지된다는 뜻입니다. "
                            "수준이 높은 기관과 변화율이 높은 기관이 반드시 같지는 않습니다.")
            else:
                st.info("순위상관을 계산할 만큼 관측치가 부족합니다.")
        else:
            st.info("[변화율] 탭에서 먼저 비교 가능한 기간을 선택하세요.")
else:
    with tab_growth:
        st.warning("비교할 연도가 2개 이상 있어야 합니다.")
    with tab_rank:
        st.warning("비교할 연도가 2개 이상 있어야 합니다.")

# ================= TAB 4: 기관 간 격차 =================
with tab_gap:
    st.caption("평균 수준의 변화뿐 아니라, 기관 간 상대적 격차가 시간에 따라 커졌는지 줄었는지 변동계수(CV = 표준편차 / 평균)로 살펴봅니다.")
    NON_NEGATIVE_SAFE = [v for v in TREND_VARS if not VARIABLES[v]["percent"]]
    if not NON_NEGATIVE_SAFE:
        st.info("변동계수를 계산하기 적합한 변수가 없습니다.")
    else:
        cv_var = st.selectbox("변수 선택", NON_NEGATIVE_SAFE, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p11_cvvar")
        cv_col = VARIABLES[cv_var]["column"]
        cv_rows = []
        for y, g in df.groupby("연도"):
            s = pd.to_numeric(g[cv_col], errors="coerce").dropna()
            if s.shape[0] > 1 and s.mean() > 0 and (s >= 0).all():
                cv_rows.append({"연도": y, "평균": s.mean(), "표준편차": s.std(), "CV": s.std() / s.mean()})
        if cv_rows:
            cv_df = pd.DataFrame(cv_rows)
            fig_cv = px.line(cv_df, x="연도", y="CV", markers=True, labels={"CV": "변동계수 (CV = SD/평균)"})
            fig_cv.update_traces(line=dict(width=3, color="#4C78A8"), marker=dict(size=9))
            fig_cv.update_layout(font=dict(size=16), height=460, title=f"{get_label(cv_var)} 연도별 CV 추이")
            st.plotly_chart(fig_cv, use_container_width=True)
            st.caption("💡 CV가 커지면 기관 간 격차(상대적 흩어짐)가 커졌다는 뜻이고, 작아지면 격차가 줄었다는 뜻입니다. "
                        "평균이 0에 가깝거나 음수가 가능한 변수에는 CV를 사용하지 않습니다.")
            with st.expander("연도별 평균·표준편차·CV 표"):
                st.dataframe(cv_df.round(3), use_container_width=True, hide_index=True)
        else:
            st.info("변동계수를 계산할 만큼 데이터가 충분하지 않거나, 이 변수는 음수 값이 있어 CV를 사용할 수 없습니다.")
