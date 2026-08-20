import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel, describe_var
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_domain, DOMAINS, get_label, get_unit
from utils.charts import plot_group_bar, plot_group_box, plot_scatter

st.set_page_config(page_title="기관유형 비교", layout="wide")
st.title("① 기관유형 비교")
st.markdown("#### 오늘의 질문")
st.info("**Q1. 공공기관 유형에 따라 기관 특성·재정·조직 운영·인사 결과는 어떻게 다른가?**")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p1")

# ---------------- 영역 선택 ----------------
domain = st.radio("영역 선택", DOMAINS, horizontal=True, key="p1_domain")
domain_vars = get_vars_by_domain(domain)
var_key = st.selectbox(
    "변수 선택", list(domain_vars.keys()),
    format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p1_var"
)
col = VARIABLES[var_key]["column"]

if col not in df.columns:
    st.warning("선택한 변수가 데이터에 없습니다.")
    st.stop()

st.divider()

# ---------------- KPI ----------------
desc = describe_var(df, col)
if desc.get("N", 0) == 0:
    st.warning("선택한 조건에서 유효한 관측치가 없습니다.")
    st.stop()

k1, k2, k3, k4 = st.columns(4)
k1.metric("전체 평균", f"{desc['평균']:,.1f}")
k2.metric("중앙값", f"{desc['중앙값']:,.1f}")
k3.metric("표준편차", f"{desc['표준편차']:,.1f}")
k4.metric("N", f"{desc['N']:,}")

# ---------------- Chart A / B ----------------
c1, c2 = st.columns(2)
with c1:
    st.plotly_chart(plot_group_bar(df, col, var_key=var_key), use_container_width=True)
with c1.expander("📌 이 그래프에서 확인할 것 / 💡 포인트"):
    st.markdown("- 기관유형별 **평균 수준**의 차이를 확인한다.\n- 막대 높이 차이가 곧 인과효과는 아니다 (⚠️ 기관유형 내부 이질성은 아래 box plot에서 확인).")
with c2:
    st.plotly_chart(plot_group_box(df, col, var_key=var_key), use_container_width=True)
with c2.expander("📌 이 그래프에서 확인할 것 / ⚠️ 주의할 점"):
    st.markdown("- 중앙값·사분위 범위·이상치를 함께 본다.\n- 상자가 넓게 겹치면 평균 차이가 통계적으로 유의해도 실질적 구분력은 약할 수 있다.")

# ---------------- Table ----------------
st.markdown("#### 기관유형별 기술통계표")
table_rows = []
for org_type, sub in df.groupby("기관유형"):
    d = describe_var(sub, col)
    if d.get("N", 0) == 0:
        continue
    table_rows.append({"기관유형": org_type, **{k: v for k, v in d.items() if k != "결측률"}})
table_df = pd.DataFrame(table_rows).round(1)
st.dataframe(table_df, use_container_width=True, hide_index=True)

# ---------------- 통계적 비교 ----------------
st.markdown("#### 통계적 비교")
groups = [g[col].dropna().values for _, g in df.groupby("기관유형") if g[col].dropna().shape[0] > 1]
n_groups = len([g for g in groups if len(g) > 0])
if n_groups == 2:
    stat, p = stats.ttest_ind(*groups, equal_var=False)
    st.write(f"**독립표본 t-검정**: t = {stat:.3f}, p = {p:.4f}")
elif n_groups > 2:
    stat, p = stats.f_oneway(*groups)
    st.write(f"**일원분산분석(one-way ANOVA)**: F = {stat:.3f}, p = {p:.4f}")
else:
    st.write("비교 가능한 집단 수가 부족합니다.")
st.caption("⚠️ 통계적으로 유의한 차이가 있다고 해서 기관유형이 해당 변수의 **원인**이라고 단정할 수 없습니다.")

st.divider()

# ---------------- 관계 탐색 ----------------
st.markdown(f"### 🔗 '{get_label(var_key)}'와 다른 변수의 관계 보기")
other_domain = st.selectbox("관계 변수 영역", DOMAINS, key="p1_rel_domain")
other_vars = {k: v for k, v in get_vars_by_domain(other_domain).items() if k != var_key}
rel_key = st.selectbox(
    "관계 변수 선택", list(other_vars.keys()),
    format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p1_rel_var"
)
rel_col = VARIABLES[rel_key]["column"]

if rel_col in df.columns:
    fig = plot_scatter(df, col, rel_col, x_key=var_key, y_key=rel_key)
    st.plotly_chart(fig, use_container_width=True)
    sub = df[[col, rel_col]].dropna()
    if sub.shape[0] > 2:
        r, p = stats.pearsonr(sub[col], sub[rel_col])
        st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {sub.shape[0]:,}")
    st.caption("⚠️ 산점도의 상관관계는 두 변수 사이의 '관계'를 보여줄 뿐, '영향'이나 '원인'을 의미하지 않습니다.")
else:
    st.warning("선택한 관계 변수가 데이터에 없습니다.")
