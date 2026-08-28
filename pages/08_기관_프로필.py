import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.data_cleaner import get_full_panel, percentile_rank
from utils.variables import VARIABLES, get_label, get_unit
from utils.page_header import render_intro

st.set_page_config(page_title="기관 프로필", layout="wide")
st.title("⑧ 기관 프로필")
render_intro(
    purpose="하나의 기관을 전체·동일유형·동일부처와 비교합니다.",
    unit="해당 기관의 가장 최근 연도. 비교 대상(전체/동일유형/동일부처 평균)도 같은 연도로 맞춰 계산합니다.",
    methods="4중 비교표 · 백분위 및 실제 순위 · 특징적인 지표(z-score) · 상대 프로파일 · 선택 지표 기준 유사기관",
    caution="유사기관은 선택한 지표와 거리계산 방식에 따라 달라지는 참고용 결과입니다.",
)

panel = get_full_panel()

st.divider()
st.markdown("### 🔍 A. 기관 검색")
search_mode = st.radio("검색 방식", ["기관명 직접 검색", "기관유형 → 주무부처 → 기관명"], horizontal=True, key="p11_searchmode")

if search_mode == "기관명 직접 검색":
    all_orgs = sorted(panel["기관명"].unique())
    org_name = st.selectbox("기관명 검색", all_orgs, key="p11_orgsearch")
else:
    c1, c2, c3 = st.columns(3)
    with c1:
        org_type = st.selectbox("기관유형", sorted(panel["기관유형"].unique()), key="p11_type")
    sub1 = panel[panel["기관유형"] == org_type]
    with c2:
        dept = st.selectbox("주무부처", sorted(sub1["주무부처"].unique()), key="p11_dept")
    sub2 = sub1[sub1["주무부처"] == dept]
    with c3:
        org_name = st.selectbox("기관명", sorted(sub2["기관명"].unique()), key="p11_org")

org_df = panel[panel["기관명"] == org_name].sort_values("연도")
if org_df.empty:
    st.warning("선택한 기관의 데이터가 없습니다.")
    st.stop()

latest_year = org_df["연도"].max()
snap = org_df[org_df["연도"] == latest_year].iloc[0]

st.divider()
st.markdown(f"### 🏢 B. 기관 기본정보")
i1, i2, i3, i4 = st.columns(4)
i1.metric("기관명", org_name)
i2.metric("기관유형", snap["기관유형"])
i3.metric("주무부처", snap["주무부처"])
i4.metric("최신연도", str(latest_year))

st.markdown(f"### 📌 C. 핵심 KPI ({latest_year}년 기준)")
KPI_GROUPS = {
    "기관·인력": ["임직원수", "여성직원비율"],
    "재정": ["총수입", "정부지원의존도"],
    "보수·복지": ["직원평균보수", "1인당복리후생비"],
    "채용": ["신규채용률", "여성신규채용비율"],
}
for grp_name, vks in KPI_GROUPS.items():
    st.markdown(f"**{grp_name}**")
    cols = st.columns(len(vks))
    for c, vk in zip(cols, vks):
        col = VARIABLES[vk]["column"]
        val = snap.get(col)
        c.metric(get_label(vk), f"{val:,.1f} {get_unit(vk)}" if pd.notna(val) else "N/A")

st.divider()

# ---------------- D. 4중 비교표 (동일연도 기준) ----------------
st.markdown(f"### 📊 D. 4중 비교표 — {latest_year}년 기준 (기관 vs 동일유형 vs 동일부처 vs 전체)")
st.caption(f"비교 대상(동일유형/동일부처/전체 평균)도 모두 {latest_year}년 값만 사용합니다 (다른 연도가 섞이지 않습니다).")
ALL_PROFILE_VARS = ["임직원수", "여성직원비율", "평균근속연수", "총수입", "정부지원의존도",
                     "직원평균보수", "1인당복리후생비", "기관장연봉", "신규채용률",
                     "여성신규채용비율", "여성육아휴직사용자수", "남성육아휴직사용자수"]
ALL_PROFILE_VARS = [v for v in ALL_PROFILE_VARS if VARIABLES[v]["column"] in panel.columns]
sel_vars = st.multiselect("비교할 지표 선택 (5~10개 권장)", ALL_PROFILE_VARS, default=ALL_PROFILE_VARS[:7], key="p11_compare_vars")

same_type = panel[(panel["기관유형"] == snap["기관유형"]) & (panel["연도"] == latest_year)]
same_dept = panel[(panel["주무부처"] == snap["주무부처"]) & (panel["연도"] == latest_year)]
overall = panel[panel["연도"] == latest_year]

rows = []
for vk in sel_vars:
    col = VARIABLES[vk]["column"]
    org_val = snap.get(col)
    type_mean = pd.to_numeric(same_type[col], errors="coerce").mean()
    dept_mean = pd.to_numeric(same_dept[col], errors="coerce").mean()
    overall_mean = pd.to_numeric(overall[col], errors="coerce").mean()
    rows.append({
        "변수": get_label(vk), "기관값": org_val, "동일유형 평균": type_mean,
        "동일부처 평균": dept_mean, "전체 평균": overall_mean,
    })
comp_df = pd.DataFrame(rows).round(1)
st.dataframe(comp_df, use_container_width=True, hide_index=True)

st.markdown(f"### 📍 E. 백분위 및 실제 순위 ({latest_year}년 기준)")


def _rank_of(series, val):
    s = pd.to_numeric(series, errors="coerce").dropna()
    if val is None or pd.isna(val) or s.empty:
        return None, None
    rank = int((s > val).sum() + 1)
    return rank, s.shape[0]


pct_rows = []
for vk in sel_vars:
    col = VARIABLES[vk]["column"]
    org_val = snap.get(col)
    pct_overall = percentile_rank(overall[col], org_val)
    pct_type = percentile_rank(same_type[col], org_val)
    pct_dept = percentile_rank(same_dept[col], org_val)
    rank_overall, n_overall = _rank_of(overall[col], org_val)
    rank_type, n_type = _rank_of(same_type[col], org_val)
    rank_dept, n_dept = _rank_of(same_dept[col], org_val)
    pct_rows.append({
        "변수": get_label(vk),
        "전체 순위": f"{rank_overall} / {n_overall}" if rank_overall is not None else "N/A",
        "전체 백분위": f"상위 {pct_overall:.0f}%" if pct_overall is not None else "N/A",
        "동일유형 순위": f"{rank_type} / {n_type}" if rank_type is not None else "N/A",
        "동일유형 백분위": f"상위 {pct_type:.0f}%" if pct_type is not None else "N/A",
        "동일부처 순위": f"{rank_dept} / {n_dept}" if rank_dept is not None else "N/A",
        "동일부처 백분위": f"상위 {pct_dept:.0f}%" if pct_dept is not None else "N/A",
    })
st.dataframe(pd.DataFrame(pct_rows), use_container_width=True, hide_index=True)

st.divider()

# ---------------- E-2. 특징적인 지표 (z-score) ----------------
st.markdown(f"### 🌟 이 기관에서 상대적으로 두드러진 지표 ({latest_year}년, 전체 기관 기준)")
st.caption("선택 지표들을 동일연도 전체기관 기준으로 표준화(z-score)한 뒤, 절댓값이 큰 상위 3개를 보여줍니다. "
            "전체기관 평균에서 상대적으로 얼마나 떨어져 있는지를 보여주는 값이며, 좋고 나쁨을 의미하지 않습니다.")
z_rows = []
for vk in sel_vars:
    col = VARIABLES[vk]["column"]
    org_val = snap.get(col)
    s = pd.to_numeric(overall[col], errors="coerce").dropna()
    if org_val is not None and pd.notna(org_val) and s.std() > 0:
        z = (org_val - s.mean()) / s.std()
        z_rows.append({"변수": get_label(vk), "z": z})
if z_rows:
    z_df = pd.DataFrame(z_rows)
    z_df["abs_z"] = z_df["z"].abs()
    top_z = z_df.sort_values("abs_z", ascending=False).head(3)
    zc = st.columns(len(top_z)) if len(top_z) > 0 else []
    for c, (_, row) in zip(zc, top_z.iterrows()):
        c.metric(row["변수"], f"{'+' if row['z'] >= 0 else ''}{row['z']:.1f} SD")
else:
    st.info("z-score를 계산할 데이터가 부족합니다.")

st.divider()

# ---------------- F. 기관 상대 프로파일 ----------------
st.markdown("### 🎯 F. 기관 상대 프로파일")
baseline = st.radio("비교 기준", ["전체 평균=100", "동일유형 평균=100", "동일부처 평균=100"],
                      horizontal=True, key="p11_baseline")
baseline_col = {"전체 평균=100": "전체 평균", "동일유형 평균=100": "동일유형 평균", "동일부처 평균=100": "동일부처 평균"}[baseline]

prof_df = comp_df.copy()
prof_df["지수"] = prof_df["기관값"] / prof_df[baseline_col] * 100
prof_df = prof_df.dropna(subset=["지수"])
if not prof_df.empty:
    fig_prof = go.Figure(go.Bar(x=prof_df["지수"], y=prof_df["변수"], orientation="h", marker_color="#4C78A8",
                                  text=prof_df["지수"].round(0), textposition="outside"))
    fig_prof.add_vline(x=100, line_dash="dash", line_color="gray", annotation_text=baseline)
    fig_prof.update_layout(font=dict(size=16), height=max(400, 60 * len(prof_df)))
    st.plotly_chart(fig_prof, use_container_width=True)
else:
    st.info("표시할 데이터가 없습니다.")

st.divider()

st.divider()

st.info("💡 이 기관의 장기 시계열, 수입·인력·보수 구성 변화, 증감분해는 **⑨ 기관별 구조와 변화** 페이지에서 확인할 수 있습니다.")

st.divider()

# ---------------- H. 선택 지표 기준 유사기관 ----------------
st.markdown("### 🧭 H. 선택 지표 기준 유사기관")
st.caption("아래에서 고른 지표들을 표준화한 뒤 유클리드 거리로 계산한 '참고용' 결과입니다. "
            "변수 간 상관, 동일 가중치 가정, 기관의 설립목적·산업 특성 미반영 등의 한계가 있습니다.")
sim_scope = st.radio("검색 범위", ["전체 기관", "동일 기관유형", "동일 주무부처"], horizontal=True, key="p11_simscope")
sim_vars = ["임직원수", "직원평균보수", "평균근속연수", "정부지원의존도", "신규채용률", "1인당복리후생비"]
sim_vars = [v for v in sim_vars if VARIABLES[v]["column"] in panel.columns]
sim_cols = [VARIABLES[v]["column"] for v in sim_vars]

scope_df = panel[panel["연도"] == latest_year]
if sim_scope == "동일 기관유형":
    scope_df = scope_df[scope_df["기관유형"] == snap["기관유형"]]
elif sim_scope == "동일 주무부처":
    scope_df = scope_df[scope_df["주무부처"] == snap["주무부처"]]

snap_all = scope_df[["기관명"] + sim_cols].dropna()
if org_name in snap_all["기관명"].values and snap_all.shape[0] > 5:
    z = snap_all.copy()
    for c in sim_cols:
        std = z[c].std()
        z[c] = (z[c] - z[c].mean()) / std if std else 0
    target = z[z["기관명"] == org_name][sim_cols].values[0]
    z["거리"] = np.sqrt(((z[sim_cols].values - target) ** 2).sum(axis=1))
    similar = z[z["기관명"] != org_name].sort_values("거리").head(5)
    st.dataframe(similar[["기관명", "거리"]].round(2).rename(columns={"거리": "유사도 거리(작을수록 유사)"}),
                 use_container_width=True, hide_index=True)

    st.markdown("#### 유사기관과 나란히 비교")
    compare_target = st.selectbox("비교할 유사기관 선택", similar["기관명"].tolist(), key="p11_simcompare")
    if compare_target:
        target_row = scope_df[scope_df["기관명"] == compare_target]
        if not target_row.empty:
            t = target_row.iloc[0]
            comp_rows = []
            for c, vname in zip(sim_cols, sim_vars):
                org_v = snap.get(c)
                sim_v = t.get(c)
                diff = (org_v - sim_v) if pd.notna(org_v) and pd.notna(sim_v) else None
                comp_rows.append({
                    "지표": get_label(vname),
                    org_name: org_v,
                    compare_target: sim_v,
                    "차이": diff,
                })
            st.dataframe(pd.DataFrame(comp_rows).round(1), use_container_width=True, hide_index=True)
else:
    st.info("선택한 검색 범위에서 유사기관을 계산할 만큼 데이터가 충분하지 않습니다.")
