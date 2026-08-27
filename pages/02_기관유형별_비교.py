import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit
from utils.charts import plot_group_mean, plot_boxplot
from utils.regression import tukey_hsd
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="기관유형별 비교", layout="wide")
st.title("② 기관유형별 비교")
render_intro(
    purpose="선택한 변수가 기관유형(공기업·준정부기관·기타공공기관)에 따라 평균과 분포에서 차이를 보이는지 확인합니다.",
    unit="선택 연도의 기관 (기본값: 최신연도, 독립표본으로 취급하기 위해 연도를 하나로 고정합니다)",
    methods="기술통계표 · 평균+95%CI · Box plot · 일원분산분석(ANOVA)",
    caution="기관유형별 평균 차이가 통계적으로 유의해도, 이는 '기관유형이 원인'임을 의미하지 않습니다.",
)

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

view, caption, mode = year_slice(df, key_prefix="p2")
st.caption(caption)
if mode == "전체 기간(기관-연도 pooled)":
    st.warning("⚠️ 전체 기간을 선택하면 동일 기관의 여러 연도 값이 서로 독립적인 관측치처럼 검정에 포함됩니다. "
                "기초통계 학습 목적이라면 '최신연도' 또는 '특정연도'를 권장합니다.")

st.markdown("### ① 기관유형별 통계표")
rows = []
for org_type, g in view.groupby("기관유형"):
    s = pd.to_numeric(g[col], errors="coerce").dropna()
    if s.empty:
        continue
    rows.append({
        "기관유형": org_type, "기관 수": s.shape[0], "평균": s.mean(), "중앙값": s.median(),
        "표준편차": s.std(), "Q1": s.quantile(0.25), "Q3": s.quantile(0.75),
    })
stat_df = pd.DataFrame(rows).round(1).sort_values("평균", ascending=False)
st.dataframe(stat_df, use_container_width=True, hide_index=True)

st.divider()
st.markdown("### ② 평균 + 95% 신뢰구간")
st.plotly_chart(plot_group_mean(view, col, var_key=var_key), use_container_width=True)
st.caption("오차막대는 각 집단 평균의 95% 신뢰구간입니다. 집단 간 평균 차이의 통계적 유의성은 아래 검정 결과를 확인해야 합니다 "
           "(신뢰구간이 겹치는지 여부만으로 유의성을 판단할 수 없습니다).")

st.markdown("### ③ Box plot")
st.plotly_chart(plot_boxplot(view, col, var_key=var_key), use_container_width=True)

st.divider()

# ---------------- ANOVA ----------------
st.markdown("### ④ 통계적 검정: 일원분산분석 (One-way ANOVA)")
st.markdown(
    f"**검정 질문**: {category} 카테고리의 '{get_label(var_key)}'는 기관유형에 따라 평균이 모두 같다고 볼 수 있는가?\n\n"
    f"- H₀ (귀무가설): 모든 기관유형의 '{get_label(var_key)}' 평균은 같다.\n"
    f"- H₁ (대립가설): 적어도 하나의 기관유형 평균은 다르다."
)

groups_dict = {name: pd.to_numeric(g[col], errors="coerce").dropna().values
               for name, g in view.groupby("기관유형") if pd.to_numeric(g[col], errors="coerce").dropna().shape[0] > 1}
groups = list(groups_dict.values())
n_groups = len(groups)

if n_groups >= 3:
    f_stat, p = stats.f_oneway(*groups)
    total_n = sum(len(g) for g in groups)
    m1, m2, m3 = st.columns(3)
    m1.metric("F statistic", f"{f_stat:.3f}")
    m2.metric("p-value", f"{p:.4f}")
    m3.metric("N", f"{total_n:,}")
    if p < 0.05:
        st.success(f"p = {p:.4f} < .05 → 모든 기관유형의 평균이 같다는 귀무가설을 기각합니다. "
                    "**적어도 하나의** 기관유형 평균이 다릅니다 (모든 쌍이 서로 다르다는 뜻은 아닙니다).")
    else:
        st.info(f"p = {p:.4f} ≥ .05 → 기관유형별 평균이 같다는 귀무가설을 기각할 근거가 부족합니다.")

    with st.expander("🔬 사후검정(Tukey HSD) — 어느 유형과 어느 유형이 다른가?"):
        tukey_df = tukey_hsd(view, col, group_col="기관유형")
        if tukey_df is not None:
            st.dataframe(tukey_df, use_container_width=True, hide_index=True)
            st.caption("'reject' 열이 True이면 해당 두 기관유형의 평균 차이가 통계적으로 유의합니다 (다중비교 보정 적용).")
        else:
            st.info("사후검정을 수행할 만큼 데이터가 충분하지 않습니다.")
elif n_groups == 2:
    t_stat, p = stats.ttest_ind(*groups, equal_var=False)
    st.write(f"**독립표본 t-검정**: t = {t_stat:.3f}, p = {p:.4f}")
    st.caption("H₀: 두 기관유형의 평균이 같다 / H₁: 두 기관유형의 평균이 다르다.")
else:
    st.info("비교 가능한 집단 수가 부족합니다.")

st.warning("⚠️ 기관유형별 평균 차이가 관찰되더라도 기관유형이 해당 변수의 원인이라고 해석할 수는 없습니다. "
            "관측되지 않은 다른 요인(규모, 업종 등)이 함께 작용했을 수 있습니다.")
