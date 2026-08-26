import streamlit as st
import pandas as pd
import plotly.express as px

from utils.data_cleaner import get_full_panel, describe_var, percentile_rank, latest_snapshot
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit, get_question
from utils.charts import plot_histogram, plot_boxplot, plot_rank_bar

st.set_page_config(page_title="기술통계 및 변수분포", layout="wide")
st.title("① 기술통계 및 변수분포")
st.caption("변수 하나를 골라 전체 → 기관유형 → 주무부처 → 개별기관 순으로 자세히 살펴보는 페이지입니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p1")

st.divider()
c1, c2 = st.columns(2)
with c1:
    category = st.selectbox("카테고리", CATEGORIES, key="p1_cat")
cat_vars = get_vars_by_category(category)
with c2:
    var_key = st.selectbox(
        "변수 선택", list(cat_vars.keys()),
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p1_var"
    )

col = VARIABLES[var_key]["column"]
if col not in df.columns:
    st.warning("선택한 변수가 데이터에 없습니다.")
    st.stop()

desc = describe_var(df, col)
if desc.get("N", 0) == 0:
    st.warning("선택한 조건에서 유효한 관측치가 없습니다.")
    st.stop()

st.markdown(f"### 📐 A. 전체 수준 — {get_label(var_key)} 기술통계")
r1 = st.columns(5)
r1[0].metric("N", f"{desc['N']:,}")
r1[1].metric("결측치 수", f"{desc['결측치수']:,}")
r1[2].metric("결측률", f"{desc['결측률']*100:.1f}%")
r1[3].metric("평균", f"{desc['평균']:,.1f}")
r1[4].metric("중앙값", f"{desc['중앙값']:,.1f}")
r2 = st.columns(5)
r2[0].metric("표준편차", f"{desc['표준편차']:,.1f}")
r2[1].metric("Q1", f"{desc['Q1']:,.1f}")
r2[2].metric("Q3", f"{desc['Q3']:,.1f}")
r2[3].metric("최소", f"{desc['최소']:,.1f}")
r2[4].metric("최대", f"{desc['최대']:,.1f}")

nbins = st.slider("히스토그램 구간(bin) 수", 10, 80, 30, key="p1_nbins")
clip = st.checkbox("극단값 영향 줄이기 (상하위 1% 밖은 축 범위에서 제외하고 보기)", value=True, key="p1_clip")
st.plotly_chart(plot_histogram(df, col, var_key=var_key, nbins=nbins, clip_extreme=clip), use_container_width=True)
with st.expander("📌 확인할 것 / 💡 포인트"):
    st.markdown("- 주황 실선은 평균, 초록 점선은 중앙값입니다.\n"
                 "- 두 선이 크게 떨어져 있으면 분포가 한쪽으로 치우쳐 있다는 뜻입니다.\n"
                 "- 극단값이 매우 크면 축이 그쪽으로 눌려서 대부분 데이터가 좁게 뭉쳐 보일 수 있어, 기본적으로 상하위 1%를 축 범위에서 제외해 표시합니다(데이터 자체는 그대로 사용).")

st.divider()

# ---------------- B. 기관유형별 분포 ----------------
st.markdown("### 📦 B. 기관유형 수준 — 분포 비교")
st.plotly_chart(plot_boxplot(df, col, var_key=var_key, clip_extreme=clip), use_container_width=True)
with st.expander("⚠️ 주의할 점"):
    st.markdown("- 점 위에 마우스를 올리면 기관명·연도를 확인할 수 있습니다.\n"
                 "- 기관유형별 상자가 넓게 겹치면 유형 구분만으로는 차이를 설명하기 어렵습니다.")

st.divider()

# ---------------- C. 주무부처별 분포 ----------------
st.markdown("### 🏛️ C. 주무부처 수준 — 분포 비교")
dept_scope = st.radio("표시 범위", ["기관 수 5개 이상 부처만", "전체 부처", "선택 부처만"], horizontal=True, key="p1_deptscope")

dept_stats = df[[col, "주무부처"]].dropna().groupby("주무부처")[col].agg(["count", "mean", "median", "std"]).reset_index()
dept_stats.columns = ["주무부처", "N", "평균", "중앙값", "표준편차"]
dept_stats = dept_stats.sort_values("평균", ascending=False)

if dept_scope == "기관 수 5개 이상 부처만":
    show_depts = dept_stats[dept_stats["N"] >= 5]["주무부처"].tolist()
elif dept_scope == "전체 부처":
    show_depts = dept_stats["주무부처"].tolist()
else:
    show_depts = st.multiselect("부처 선택", dept_stats["주무부처"].tolist(),
                                  default=dept_stats["주무부처"].tolist()[:8], key="p1_deptselect")

if show_depts:
    dept_df = df[df["주무부처"].isin(show_depts)]
    fig_dept = px.box(dept_df.dropna(subset=[col]), x="주무부처", y=col, points=False,
                        labels={col: f"{get_label(var_key)} ({get_unit(var_key)})"})
    fig_dept.update_layout(font=dict(size=15), height=520, xaxis_tickangle=-30)
    if clip:
        import numpy as np
        s = dept_df[col].dropna()
        if not s.empty:
            lo, hi = np.percentile(s, [1, 99])
            if lo != hi:
                pad = (hi - lo) * 0.15
                fig_dept.update_yaxes(range=[lo - pad, hi + pad])
    st.plotly_chart(fig_dept, use_container_width=True)

    st.markdown("**주무부처별 통계표** (기관 수 3개 미만인 부처는 평균이 소수 기관에 크게 좌우될 수 있습니다 ⚠️)")
    display_stats = dept_stats[dept_stats["주무부처"].isin(show_depts)].round(1)
    st.dataframe(display_stats, use_container_width=True, hide_index=True)
else:
    st.info("표시할 부처를 선택하세요.")

st.divider()

# ---------------- D. 선택기관 위치 ----------------
st.markdown("### 🏢 D. 개별기관 수준 — 선택기관 위치")
orgs = sorted(df["기관명"].unique())
sel_org = st.selectbox("기관 선택", ["(선택 안 함)"] + orgs, key="p1_selorg")

if sel_org != "(선택 안 함)":
    org_rows = df[df["기관명"] == sel_org].dropna(subset=[col])
    if not org_rows.empty:
        org_row = org_rows.sort_values("연도").iloc[-1]
        org_val = org_row[col]
        org_type = org_row["기관유형"]
        org_dept = org_row["주무부처"]

        overall_mean = pd.to_numeric(df[col], errors="coerce").mean()
        type_mean = pd.to_numeric(df[df["기관유형"] == org_type][col], errors="coerce").mean()
        dept_mean = pd.to_numeric(df[df["주무부처"] == org_dept][col], errors="coerce").mean()

        fig_pos = plot_histogram(df, col, var_key=var_key, nbins=nbins, clip_extreme=clip)
        fig_pos.add_vline(x=org_val, line_color="red", line_width=3,
                            annotation_text=f"{sel_org} {org_val:,.1f}", annotation_position="top left")
        st.plotly_chart(fig_pos, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("전체 평균", f"{overall_mean:,.1f}")
        m2.metric(f"동일유형({org_type}) 평균", f"{type_mean:,.1f}" if pd.notna(type_mean) else "N/A")
        m3.metric(f"동일부처({org_dept}) 평균", f"{dept_mean:,.1f}" if pd.notna(dept_mean) else "N/A")
        m4.metric(f"{sel_org}", f"{org_val:,.1f}")

        pct_overall = percentile_rank(df[col], org_val)
        pct_type = percentile_rank(df[df["기관유형"] == org_type][col], org_val)
        pct_dept = percentile_rank(df[df["주무부처"] == org_dept][col], org_val)
        p1, p2, p3 = st.columns(3)
        p1.metric("전체 백분위", f"상위 {pct_overall:.0f}%" if pct_overall is not None else "N/A")
        p2.metric("동일유형 내 백분위", f"상위 {pct_type:.0f}%" if pct_type is not None else "N/A")
        p3.metric("동일부처 내 백분위", f"상위 {pct_dept:.0f}%" if pct_dept is not None else "N/A")
    else:
        st.info("선택한 기관에 유효한 값이 없습니다.")

st.divider()

# ---------------- Top / Bottom ----------------
st.markdown("### 🏆 Top / Bottom 기관")
st.caption("기관마다 필터링된 범위 내 가장 최근 연도 값 1개만 사용해 순위를 매깁니다 (같은 기관이 여러 연도로 중복 표시되지 않습니다).")
c5, c6 = st.columns([1, 1])
with c5:
    rank_mode = st.radio("정렬", ["Top", "Bottom"], horizontal=True, key="p1_rankmode")
with c6:
    top_n = st.slider("표시 개수", 5, 20, 10, key="p1_topn")

ascending = (rank_mode == "Bottom")
snap = latest_snapshot(df)
overall_mean = pd.to_numeric(snap[col], errors="coerce").mean()

rank_rows = []
ranked = snap[["기관명", "기관유형", "주무부처", col]].dropna().sort_values(col, ascending=ascending).head(top_n)
for _, row in ranked.iterrows():
    val = row[col]
    same_type_mean = pd.to_numeric(snap[snap["기관유형"] == row["기관유형"]][col], errors="coerce").mean()
    pct = percentile_rank(snap[col], val)
    rank_rows.append({
        "기관명": row["기관명"],
        "기관유형": row["기관유형"],
        "주무부처": row["주무부처"],
        get_label(var_key): round(val, 1),
        "전체 평균 대비": f"{val/overall_mean:,.2f}배" if overall_mean else "N/A",
        "동일유형 평균 대비": f"{val/same_type_mean*100:,.0f}%" if same_type_mean else "N/A",
        "전체 백분위": f"상위 {pct:.1f}%" if pct is not None else "N/A",
    })
st.dataframe(pd.DataFrame(rank_rows), use_container_width=True, hide_index=True)
st.plotly_chart(plot_rank_bar(df, col, var_key=var_key, top_n=top_n, ascending=ascending, show_multiple=True),
                 use_container_width=True)

st.divider()
st.markdown("### 🤔 생각해볼 질문")
st.info(get_question(var_key))
