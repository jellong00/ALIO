import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="주무부처별 비교", layout="wide")
st.title("③ 주무부처별 비교")
render_intro(
    purpose="동일한 지표가 주무부처별 산하기관 사이에서 얼마나 다른지 확인합니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="산하기관 수(N) 확인 → 부처별 평균 dot plot → 표본 수와 평균의 안정성(CI폭) → 선택 부처 2~5개 분포 비교 → 기관유형×주무부처 교차분석",
    caution="주무부처마다 산하기관 수가 크게 다릅니다. 기관 수가 적은 부처의 평균은 소수 기관에 크게 좌우될 수 있으므로, N을 항상 함께 확인하세요.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p3")

st.divider()
c1, c2 = st.columns(2)
with c1:
    category = st.selectbox("카테고리", CATEGORIES, key="p3_cat")
cat_vars = get_vars_by_category(category)
with c2:
    var_key = st.selectbox(
        "변수 선택", list(cat_vars.keys()),
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p3_var"
    )
col = VARIABLES[var_key]["column"]
if col not in df.columns:
    st.warning("선택한 변수가 데이터에 없습니다.")
    st.stop()

view, caption, mode = year_slice(df, key_prefix="p3")
st.caption(caption)

st.divider()

# ---------------- A. 주무부처별 산하기관 수 ----------------
st.markdown("### A. 주무부처별 산하기관 수")
st.caption("ℹ️ 이 차트는 '부처별로 등록된 기관 개수'를 세는 것이라, 기관유형·주무부처는 이 데이터에서 연도에 따라 바뀌지 않는 고정 속성이므로 연도를 바꿔도 값이 거의 동일합니다. "
            "선택한 변수의 실제 값이 연도별로 달라지는 것은 아래 B섹션부터 확인할 수 있습니다.")
dept_n = view.groupby("주무부처")["기관명"].nunique().reset_index(name="기관 수").sort_values("기관 수", ascending=False)
fig_n = px.bar(dept_n.head(20), x="기관 수", y="주무부처", orientation="h")
fig_n.update_layout(font=dict(size=14), height=520, title="산하기관 수 상위 20개 부처")
st.plotly_chart(fig_n, use_container_width=True)

# ---------------- B. 부처별 평균·중앙값 ----------------
st.markdown("### B. 부처별 평균·중앙값 (dot plot)")
dept_stats = view.groupby("주무부처").agg(
    기관수=("기관명", "nunique"),
    평균=(col, lambda s: pd.to_numeric(s, errors="coerce").mean()),
    중앙값=(col, lambda s: pd.to_numeric(s, errors="coerce").median()),
).reset_index()
dept_stats = dept_stats.dropna(subset=["평균"]).sort_values("평균", ascending=True)

fig_dot = go.Figure()
fig_dot.add_trace(go.Scatter(x=dept_stats["평균"], y=dept_stats["주무부처"], mode="markers",
                               marker=dict(size=dept_stats["기관수"].clip(upper=20) + 4, color="#4C78A8"),
                               customdata=dept_stats["기관수"],
                               hovertemplate="%{y}<br>평균: %{x:,.1f}<br>기관 수: %{customdata}<extra></extra>",
                               name="평균"))
fig_dot.update_layout(font=dict(size=13), height=max(500, 22 * len(dept_stats)),
                        xaxis_title=f"{get_label(var_key)} ({get_unit(var_key)})",
                        title="부처별 평균 (점 크기 = 산하기관 수)")
st.plotly_chart(fig_dot, use_container_width=True)
st.caption("💡 점 크기가 작을수록(산하기관 수가 적을수록) 해당 부처의 평균은 소수 기관의 값에 더 크게 좌우됩니다.")

with st.expander("📋 부처별 통계표 전체 보기"):
    st.dataframe(dept_stats.round(1).sort_values("평균", ascending=False), use_container_width=True, hide_index=True)

st.divider()

# ---------------- C. 선택 부처 2~5개 분포 비교 ----------------
st.markdown("### C. 선택 부처 분포 비교 (2~5개 권장)")
depts_sorted = dept_stats.sort_values("기관수", ascending=False)["주무부처"].tolist()
sel_depts = st.multiselect("주무부처 선택", depts_sorted, default=depts_sorted[:4], key="p3_seldepts")
if sel_depts:
    sub = view[view["주무부처"].isin(sel_depts)].dropna(subset=[col])
    fig_box = px.box(sub, x="주무부처", y=col, points="all",
                       labels={col: f"{get_label(var_key)} ({get_unit(var_key)})"})
    fig_box.update_layout(font=dict(size=15), height=500)
    st.plotly_chart(fig_box, use_container_width=True)
else:
    st.info("비교할 부처를 1개 이상 선택하세요.")

st.divider()

# ---------------- D. 표본 수와 부처 평균의 안정성 ----------------
st.markdown("### D. 소수 기관으로 계산된 부처 평균은 얼마나 안정적인가?")
st.caption("산하기관이 2개뿐인 부처의 평균과 30개인 부처의 평균을 같은 확신으로 비교해도 될까요?")
fig_scatter = px.scatter(dept_stats, x="기관수", y="평균", hover_name="주무부처",
                           labels={"기관수": "산하기관 수", "평균": f"{get_label(var_key)} 평균"})
fig_scatter.update_layout(font=dict(size=15), height=460)
st.plotly_chart(fig_scatter, use_container_width=True)
st.caption("💡 왼쪽(기관 수 적음)에 위치한 부처일수록 평균값의 변동성이 클 수 있습니다. 소수 기관으로 결정된 평균은 신중하게 해석하세요.")

st.markdown("#### 산하기관 수와 95% 신뢰구간 폭")
st.caption("부처마다 변수 값의 스케일 자체가 크게 다르면(예: 초대형 기관 1곳이 낀 부처) 절대 CI폭 비교가 스케일 차이에 묻힐 수 있습니다. "
            "기본값은 평균 대비 상대적인 CI폭(%)이며, 절대값으로도 바꿔볼 수 있습니다.")
ci_rows = []
for dept, g in view.groupby("주무부처"):
    s = pd.to_numeric(g[col], errors="coerce").dropna()
    n = s.shape[0]
    if n >= 2 and s.std() > 0 and s.mean() != 0:
        se = s.std() / (n ** 0.5)
        ci_width = 2 * 1.96 * se
        ci_rel = ci_width / abs(s.mean()) * 100
        ci_rows.append({"주무부처": dept, "기관수": n, "CI폭": ci_width, "CI폭(%)": ci_rel})
ci_df = pd.DataFrame(ci_rows)
if not ci_df.empty:
    ci_c1, ci_c2 = st.columns(2)
    with ci_c1:
        ci_metric = st.radio("표시 방식", ["상대값 (%, 평균 대비)", "절대값"], horizontal=True, key="p3_cimetric")
    with ci_c2:
        ci_logy = st.checkbox("y축 로그 스케일", value=(ci_metric == "절대값"), key="p3_cilogy")
    y_field = "CI폭(%)" if ci_metric.startswith("상대값") else "CI폭"
    y_label = "평균 대비 95% 신뢰구간 폭 (%)" if ci_metric.startswith("상대값") else "95% 신뢰구간 폭"

    trendline_opts = dict(log_y=True) if ci_logy else None
    fig_ci = px.scatter(ci_df, x="기관수", y=y_field, hover_name="주무부처", trendline="ols",
                          trendline_options=trendline_opts,
                          log_y=ci_logy, labels={"기관수": "산하기관 수 (N)", y_field: y_label})
    fig_ci.update_traces(marker=dict(size=10, opacity=0.75), selector=dict(mode="markers"))
    fig_ci.update_layout(font=dict(size=15), height=480)
    st.plotly_chart(fig_ci, use_container_width=True)
    st.caption("💡 산하기관 수가 적은 부처에서는 표본평균의 불확실성(신뢰구간 폭)이 커질 수 있음을 실제 데이터에서 확인합니다. "
                "다만 신뢰구간 폭은 표본 수뿐 아니라 그 부처 내 값들의 분산에도 영향을 받으므로, 'N이 커지면 CI가 반드시 좁아진다'고 단정할 수는 없습니다. "
                "점선(추세선)의 기울기가 완만하거나 뒤섞여 보인다면, 그 자체가 '표본 수만으로는 불확실성이 깔끔하게 설명되지 않는다'는 것을 보여주는 실제 사례입니다.")

    with st.expander("📋 부처별 CI폭 표 보기"):
        st.dataframe(ci_df.round(2).sort_values("기관수"), use_container_width=True, hide_index=True)
else:
    st.info("신뢰구간을 계산할 만큼 데이터가 충분한 부처가 없습니다.")

st.divider()

# ---------------- E. 기관유형 × 주무부처 교차분석 ----------------
st.markdown("### E. 기관유형 × 주무부처 교차분석")
st.caption("동일 기관유형 안에서도 주무부처에 따라 평균이 다른지, 또는 동일 주무부처 안에서도 기관유형별 차이가 나타나는지 탐색합니다.")
cross_min_n = st.slider("교차표에 포함할 부처의 최소 기관 수", 1, 10, 3, key="p3_crossminn")

s = view[[col, "주무부처", "기관유형"]].dropna()
row_totals = s.groupby("주무부처")["기관명"].transform("count") if "기관명" in s.columns else None
valid_depts = s.groupby("주무부처").size()
valid_depts = valid_depts[valid_depts >= cross_min_n].index
s = s[s["주무부처"].isin(valid_depts)]

if not s.empty:
    pivot_val = s.pivot_table(index="주무부처", columns="기관유형", values=col, aggfunc="mean")
    pivot_n = s.pivot_table(index="주무부처", columns="기관유형", values=col, aggfunc="count")
    z = pivot_val.values
    n_arr = pivot_n.reindex(index=pivot_val.index, columns=pivot_val.columns).values
    fig_cross = go.Figure(data=go.Heatmap(
        z=z, x=pivot_val.columns.tolist(), y=pivot_val.index.tolist(),
        colorscale="Blues", customdata=n_arr,
        hovertemplate="%{y} × %{x}<br>평균: %{z:,.1f}<br>N=%{customdata}<extra></extra>",
        colorbar=dict(title=get_label(var_key)),
    ))
    fig_cross.update_layout(font=dict(size=13), height=max(500, 24 * len(pivot_val.index)),
                              title=f"{get_label(var_key)} 평균 (주무부처 × 기관유형)")
    st.plotly_chart(fig_cross, use_container_width=True)
    st.caption("셀에 마우스를 올리면 관측치 수(N)를 확인할 수 있습니다. 빈 칸은 해당 조합의 데이터가 없다는 뜻입니다. "
                "이 표는 단순 평균 교차표이므로, 이것만으로 '기관유형 효과가 부처 구성 때문'이라고 단정할 수는 없습니다.")
else:
    st.info("교차표를 만들 만큼 데이터가 충분하지 않습니다.")
