import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit
from utils.charts import plot_group_mean, plot_boxplot, plot_index_comparison

st.set_page_config(page_title="기관유형별 비교", layout="wide")
st.title("② 기관유형별 비교")
st.caption("공기업·준정부기관·기타공공기관의 차이를 살펴보는 페이지입니다.")

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

st.markdown("### 📋 기관유형별 통계표")
rows = []
for org_type, g in df.groupby("기관유형"):
    s = pd.to_numeric(g[col], errors="coerce").dropna()
    if s.empty:
        continue
    rows.append({
        "기관유형": org_type, "N": s.shape[0], "평균": s.mean(), "중앙값": s.median(),
        "표준편차": s.std(), "Q1": s.quantile(0.25), "Q3": s.quantile(0.75),
    })
stat_df = pd.DataFrame(rows).round(1)
st.dataframe(stat_df, use_container_width=True, hide_index=True)

st.divider()
c3, c4 = st.columns(2)
with c3:
    st.plotly_chart(plot_group_mean(df, col, var_key=var_key), use_container_width=True)
    with st.expander("📌 확인할 것"):
        st.markdown("- 오차막대는 95% 신뢰구간입니다. 구간이 겹치면 평균 차이가 통계적으로 뚜렷하지 않을 수 있습니다.")
with c4:
    st.plotly_chart(plot_boxplot(df, col, var_key=var_key), use_container_width=True)

st.markdown("### 📈 상대지수 (전체 평균 = 100)")
st.plotly_chart(plot_index_comparison(df, col, var_key=var_key), use_container_width=True)
with st.expander("💡 계량분석 포인트"):
    st.markdown("- 전체 평균을 100으로 두면 기관유형 간 상대적 격차를 직관적으로 비교할 수 있습니다.")

st.divider()

# ---------------- ANOVA ----------------
st.markdown("### 통계적 검정")
groups = [pd.to_numeric(g[col], errors="coerce").dropna().values
          for _, g in df.groupby("기관유형") if pd.to_numeric(g[col], errors="coerce").dropna().shape[0] > 1]
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

st.warning("⚠️ 기관유형별 평균 차이가 관찰되더라도 기관유형이 해당 변수의 원인이라고 해석할 수는 없습니다.")
