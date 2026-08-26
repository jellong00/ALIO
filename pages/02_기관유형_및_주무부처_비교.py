import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit
from utils.charts import plot_group_mean, plot_boxplot, plot_group_vs_overall
from utils.level_compare import dept_stats_table, cross_table

st.set_page_config(page_title="기관유형 및 주무부처 비교", layout="wide")
st.title("② 기관유형 및 주무부처 비교")
st.caption("동일 변수를 기관유형 기준과 주무부처 기준, 두 가지 잣대로 비교해보는 페이지입니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p2")

st.divider()
c1, c2 = st.columns(2)
with c1:
    category = st.selectbox("카테고리", CATEGORIES, key="p2_cat")
cat_vars = get_vars_by_category(category)
with c2:
    var_key = st.selectbox(
        "변수 선택", list(cat_vars.keys()),
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p2_var"
    )
col = VARIABLES[var_key]["column"]
if col not in df.columns:
    st.warning("선택한 변수가 데이터에 없습니다.")
    st.stop()

st.markdown("### 비교 기준")
compare_basis = st.radio("비교 기준", ["기관유형", "주무부처"], horizontal=True, key="p2_basis", label_visibility="collapsed")

if compare_basis == "기관유형":
    group_col = "기관유형"
    plot_df = df
else:
    group_col = "주무부처"
    min_n = st.slider("최소 기관 수 (이보다 적은 부처는 제외)", 1, 10, 3, key="p2_mindept")
    valid_depts = dept_stats_table(df, col, min_n=min_n)["주무부처"].tolist()
    plot_df = df[df["주무부처"].isin(valid_depts)]
    if plot_df.empty:
        st.info("조건을 만족하는 주무부처가 없습니다. 최소 기관 수를 낮춰보세요.")
        st.stop()

st.markdown(f"### 📋 {group_col}별 통계표")
rows = []
for grp_name, g in plot_df.groupby(group_col):
    s = pd.to_numeric(g[col], errors="coerce").dropna()
    if s.empty:
        continue
    rows.append({
        group_col: grp_name, "N": s.shape[0], "평균": s.mean(), "중앙값": s.median(),
        "표준편차": s.std(), "Q1": s.quantile(0.25), "Q3": s.quantile(0.75),
    })
stat_df = pd.DataFrame(rows).round(1).sort_values("평균", ascending=False)
st.dataframe(stat_df, use_container_width=True, hide_index=True)
if compare_basis == "주무부처":
    st.caption("⚠️ 기관 수가 적은 부처의 평균은 소수 기관에 크게 좌우될 수 있으니 N을 함께 확인하세요.")

st.divider()
c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(plot_group_mean(plot_df, col, group_col=group_col, var_key=var_key), use_container_width=True)
    with st.expander("📌 확인할 것"):
        st.markdown("- 오차막대는 95% 신뢰구간입니다. 두 집단의 구간이 겹치면 그 차이는 통계적으로 유의하지 않을 수 있습니다.")
with c4:
    st.plotly_chart(plot_boxplot(plot_df, col, group_col=group_col, var_key=var_key), use_container_width=True)

st.markdown(f"### 📈 {group_col}별 평균 (전체 평균과 비교)")
st.plotly_chart(plot_group_vs_overall(plot_df, col, group_col=group_col, var_key=var_key), use_container_width=True)
with st.expander("💡 계량분석 포인트"):
    st.markdown("- 막대 끝의 괄호 값은 전체 평균 대비 증감률(%)입니다. 점선은 전체 평균 위치입니다.")

st.divider()

# ---------------- 통계적 검정 ----------------
st.markdown("### 통계적 검정")
groups = [pd.to_numeric(g[col], errors="coerce").dropna().values
          for _, g in plot_df.groupby(group_col) if pd.to_numeric(g[col], errors="coerce").dropna().shape[0] > 1]
n_groups = len(groups)
if n_groups >= 3:
    f_stat, p = stats.f_oneway(*groups)
    total_n = sum(len(g) for g in groups)
    m1, m2, m3 = st.columns(3)
    m1.metric("F statistic", f"{f_stat:.3f}")
    m2.metric("p-value", f"{p:.4f}")
    m3.metric("N", f"{total_n:,}")
elif n_groups == 2:
    t_stat, p = stats.ttest_ind(*groups, equal_var=False)
    st.write(f"**독립표본 t-검정**: t = {t_stat:.3f}, p = {p:.4f}")
else:
    st.info("비교 가능한 집단 수가 부족합니다.")

st.warning(f"⚠️ {group_col}별 평균 차이가 관찰되더라도 {group_col}이(가) 해당 변수의 원인이라고 해석할 수는 없습니다.")

st.divider()

# ---------------- 교차분석 ----------------
st.markdown("### 🔲 교차분석: 주무부처 × 기관유형")
st.caption("기관유형 효과처럼 보였던 차이가 사실 특정 부처 구성 때문일 수도 있는지 확인해봅니다.")
cross_min_n = st.slider("교차표에 포함할 부처의 최소 기관 수", 1, 10, 3, key="p2_crossminn")
pivot_val, pivot_n = cross_table(df, col, min_n=cross_min_n)

if not pivot_val.empty:
    z = pivot_val.values
    n_arr = pivot_n.reindex(index=pivot_val.index, columns=pivot_val.columns).values
    fig_cross = go.Figure(data=go.Heatmap(
        z=z, x=pivot_val.columns.tolist(), y=pivot_val.index.tolist(),
        colorscale="Blues", customdata=n_arr,
        hovertemplate="%{y} × %{x}<br>평균: %{z:,.1f}<br>N=%{customdata}<extra></extra>",
        colorbar=dict(title=get_label(var_key)),
    ))
    fig_cross.update_layout(font=dict(size=14), height=max(500, 26 * len(pivot_val.index)),
                              title=f"{get_label(var_key)} 평균 (주무부처 × 기관유형)")
    st.plotly_chart(fig_cross, use_container_width=True)
    st.caption("셀에 마우스를 올리면 해당 조합의 관측치 수(N)를 확인할 수 있습니다. 빈 칸은 해당 조합의 데이터가 없다는 뜻입니다.")
else:
    st.info("교차표를 만들 만큼 데이터가 충분하지 않습니다.")
