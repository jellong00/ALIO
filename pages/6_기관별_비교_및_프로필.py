import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

from utils.data_cleaner import get_full_panel, percentile_rank
from utils.variables import VARIABLES, get_label, get_unit

st.set_page_config(page_title="기관별 비교 및 프로필", layout="wide")
st.title("⑥ 기관별 비교 및 프로필")
st.caption("내가 근무하는 기관, 혹은 관심 있는 기관을 직접 찾아 비교해보는 페이지입니다.")

panel = get_full_panel()

st.divider()
st.markdown("### 🔍 기관 검색 (기관유형 → 주무부처 → 기관명)")
c1, c2, c3 = st.columns(3)
with c1:
    org_type = st.selectbox("기관유형", sorted(panel["기관유형"].unique()), key="p6_type")
sub1 = panel[panel["기관유형"] == org_type]
with c2:
    dept = st.selectbox("주무부처", sorted(sub1["주무부처"].unique()), key="p6_dept")
sub2 = sub1[sub1["주무부처"] == dept]
with c3:
    org_name = st.selectbox("기관명", sorted(sub2["기관명"].unique()), key="p6_org")

org_df = panel[panel["기관명"] == org_name].sort_values("연도")
if org_df.empty:
    st.warning("선택한 기관의 데이터가 없습니다.")
    st.stop()

latest_year = org_df["연도"].max()
snap = org_df[org_df["연도"] == latest_year].iloc[0]

st.divider()
st.markdown(f"### 🏢 {org_name} ({latest_year}년 기준)")
st.caption(f"기관유형: {snap['기관유형']} · 주무부처: {snap['주무부처']}")

KPI_GROUPS = {
    "기관·인력": ["임직원수", "여성직원비율"],
    "재정": ["총수입", "정부지원의존도"],
    "보수·복지": ["직원평균보수", "1인당복리후생비"],
    "채용·일가정": ["신규채용률", "여성육아휴직사용률"],
}
for grp_name, vks in KPI_GROUPS.items():
    st.markdown(f"**{grp_name}**")
    cols = st.columns(len(vks))
    for c, vk in zip(cols, vks):
        col = VARIABLES[vk]["column"]
        val = snap.get(col)
        c.metric(get_label(vk), f"{val:,.1f} {get_unit(vk)}" if pd.notna(val) else "N/A")

st.divider()

# ---------------- 비교표 ----------------
st.markdown("### 📊 비교표")
ALL_PROFILE_VARS = ["임직원수", "여성직원비율", "평균근속연수", "총수입", "정부지원의존도",
                     "직원평균보수", "1인당복리후생비", "기관장연봉", "신규채용률",
                     "여성신규채용비율", "여성육아휴직사용률", "남성육아휴직사용률"]
ALL_PROFILE_VARS = [v for v in ALL_PROFILE_VARS if VARIABLES[v]["column"] in panel.columns]
sel_vars = st.multiselect("비교할 지표 선택 (5~10개 권장)", ALL_PROFILE_VARS, default=ALL_PROFILE_VARS[:7], key="p6_compare_vars")

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
    index_vs_type = (org_val / type_mean * 100) if type_mean not in (0, None) and pd.notna(type_mean) and pd.notna(org_val) else None
    rows.append({
        "변수": get_label(vk), "기관값": org_val, "동일유형 평균": type_mean,
        "동일부처 평균": dept_mean, "전체 평균": overall_mean, "유형대비지수": index_vs_type,
    })
comp_df = pd.DataFrame(rows).round(1)
st.dataframe(comp_df, use_container_width=True, hide_index=True)

idx_df = comp_df.dropna(subset=["유형대비지수"])
if not idx_df.empty:
    fig2 = go.Figure(go.Bar(x=idx_df["유형대비지수"], y=idx_df["변수"], orientation="h", marker_color="#4C78A8"))
    fig2.add_vline(x=100, line_dash="dash", line_color="gray", annotation_text="동일유형 평균=100")
    fig2.update_layout(font=dict(size=16), height=max(400, 60 * len(idx_df)))
    st.plotly_chart(fig2, use_container_width=True)

# ---------------- 백분위 ----------------
st.markdown("### 📍 백분위")
pct_rows = []
for vk in sel_vars:
    col = VARIABLES[vk]["column"]
    org_val = snap.get(col)
    pct_overall = percentile_rank(overall[col], org_val)
    pct_type = percentile_rank(same_type[col], org_val)
    pct_rows.append({
        "변수": get_label(vk),
        "전체 백분위": f"상위 {pct_overall:.0f}%" if pct_overall is not None else "N/A",
        "동일유형 내 백분위": f"상위 {pct_type:.0f}%" if pct_type is not None else "N/A",
    })
st.dataframe(pd.DataFrame(pct_rows), use_container_width=True, hide_index=True)

st.divider()

# ---------------- 시계열 ----------------
st.markdown("### 📈 연도별 추세")
ts_var = st.selectbox("변수 선택", ALL_PROFILE_VARS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p6_tsvar")
ts_col = VARIABLES[ts_var]["column"]
type_avg = panel[panel["기관유형"] == snap["기관유형"]].groupby("연도")[ts_col].mean().reset_index()
org_ts = org_df[["연도", ts_col]].dropna()

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=org_ts["연도"], y=org_ts[ts_col], mode="lines+markers", name=org_name,
                            line=dict(width=3, color="#E07B39")))
fig3.add_trace(go.Scatter(x=type_avg["연도"], y=type_avg[ts_col], mode="lines+markers",
                            name=f"{snap['기관유형']} 평균", line=dict(width=2, dash="dash", color="#4C78A8")))
fig3.update_layout(font=dict(size=16), height=460, yaxis_title=f"{get_label(ts_var)} ({get_unit(ts_var)})")
st.plotly_chart(fig3, use_container_width=True)

st.divider()

# ---------------- 유사기관 ----------------
st.markdown("### 🧭 유사기관 찾기 (선택 기능)")
sim_vars = ["임직원수", "직원평균보수", "평균근속연수", "정부지원의존도", "신규채용률", "1인당복리후생비"]
sim_vars = [v for v in sim_vars if VARIABLES[v]["column"] in panel.columns]
sim_cols = [VARIABLES[v]["column"] for v in sim_vars]

snap_all = panel[panel["연도"] == latest_year][["기관명"] + sim_cols].dropna()
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
    st.caption("⚠️ 유사기관 결과는 선택된 변수와 거리계산 방식(표준화 유클리드 거리)에 따라 달라질 수 있습니다.")
else:
    st.info("유사기관을 계산할 만큼 데이터가 충분하지 않습니다.")
