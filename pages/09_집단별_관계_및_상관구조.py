import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit
from utils.charts import plot_correlation_heatmap
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="집단별 관계 및 상관구조", layout="wide")
st.title("⑨ 집단별 관계 및 상관구조")
render_intro(
    purpose="전체에서 관찰된 두 변수의 관계가 기관유형이나 주무부처 내부에서도 동일하게 나타나는지 확인하고, 8개 부문(인력·재정·법인세·보수·임원·복리후생·채용·일가정양립)이 서로 어떻게 얽혀 있는지 한눈에 살펴봅니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="부문간 관계 지도(대표변수 상관행렬) · 전체/기관유형별/주무부처별 상관계수 비교 · Correlation matrix · 상관관계 순위",
    caution="전체 관계와 집단별 관계가 다를 수 있으므로 집단 구성을 함께 확인해야 합니다. 방향이 반대로 나타나는 특수한 경우에는 Simpson's paradox 가능성을 검토할 수 있습니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p10")
view, caption, mode = year_slice(df, key_prefix="p10")
st.caption(caption)

st.divider()

# ---------------- 부문간 관계 지도 ----------------
st.markdown("### 🗺️ 부문간 관계 지도")
st.caption("각 부문(카테고리)을 대표하는 변수 하나씩을 뽑아 상관행렬을 보여줍니다. "
            "재정 페이지, 보수 페이지처럼 부문별로 따로 보던 지표들이 서로 얼마나 함께 움직이는지 한 화면에서 확인할 수 있습니다. "
            "대표변수는 아래에서 부문별로 바꿀 수 있고, 더 세밀한 변수 조합은 아래 'Correlation Matrix'에서 직접 고를 수 있습니다.")

REP_DEFAULTS = {
    "기관·인력": "임직원수", "재정": "총수입", "법인세": "법인세결정세액",
    "보수": "직원평균보수", "임원": "기관장연봉", "복리후생": "1인당복리후생비",
    "채용": "신규채용률", "일가정양립": "여성육아휴직사용자수",
}
rep_selection = {}
rep_cols_ui = st.columns(4)
for i, cat in enumerate(CATEGORIES):
    cat_vars = {k: v for k, v in get_vars_by_category(cat).items() if v["column"] in view.columns}
    if not cat_vars:
        continue
    default_key = REP_DEFAULTS.get(cat)
    default_idx = list(cat_vars.keys()).index(default_key) if default_key in cat_vars else 0
    with rep_cols_ui[i % 4]:
        rep_selection[cat] = st.selectbox(
            f"[{cat}] 대표변수", list(cat_vars.keys()), index=default_idx,
            format_func=lambda k: get_label(k), key=f"p10_rep_{cat}"
        )

rep_keys = list(rep_selection.values())
if len(rep_keys) >= 2:
    rep_cols = [VARIABLES[k]["column"] for k in rep_keys]
    rep_labels = [f"[{cat}] {get_label(k)}" for cat, k in rep_selection.items()]
    rep_corr = view[rep_cols].apply(pd.to_numeric, errors="coerce").corr(method="pearson")
    st.plotly_chart(plot_correlation_heatmap(rep_corr, labels=rep_labels), use_container_width=True)
    st.caption("💡 부문 간 상관이 예상보다 강하거나 약한 조합이 있다면, 아래에서 변수 A/B로 직접 골라 산점도까지 살펴보세요.")
else:
    st.info("대표변수를 계산할 데이터가 부족합니다.")

st.divider()
c1, c2 = st.columns(2)
with c1:
    st.markdown("**변수 A**")
    a_cat = st.selectbox("카테고리", CATEGORIES, key="p10_acat")
    a_vars = get_vars_by_category(a_cat)
    a_key = st.selectbox("변수", list(a_vars.keys()), format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p10_avar")
with c2:
    st.markdown("**변수 B**")
    b_cat = st.selectbox("카테고리", CATEGORIES, index=min(1, len(CATEGORIES) - 1), key="p10_bcat")
    b_vars = get_vars_by_category(b_cat)
    b_key = st.selectbox("변수", list(b_vars.keys()), format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p10_bvar")

a_col, b_col = VARIABLES[a_key]["column"], VARIABLES[b_key]["column"]
if a_col not in view.columns or b_col not in view.columns:
    st.warning("선택한 변수 조합이 데이터에 없습니다.")
    st.stop()

sub_all = view[[a_col, b_col]].dropna()
if sub_all.shape[0] > 2:
    r_all, p_all = stats.pearsonr(sub_all[a_col], sub_all[b_col])
    st.markdown(f"### 전체 상관관계: r = **{r_all:.3f}** (p = {p_all:.4f}, N = {sub_all.shape[0]:,})")

st.divider()
st.markdown("### 관계 비교 기준")
relation_basis = st.radio("비교 기준", ["기관유형별", "주무부처별"], horizontal=True, key="p10_relbasis")

rows = []
if relation_basis == "기관유형별":
    for org_type, g in view.groupby("기관유형"):
        gs = g[[a_col, b_col]].dropna()
        if gs.shape[0] > 2:
            r_g, _ = stats.pearsonr(gs[a_col], gs[b_col])
            slope_g, intercept_g, rv_g, p_g, se_g = stats.linregress(gs[a_col], gs[b_col])
            rows.append({"그룹": org_type, "N": gs.shape[0], "Pearson r": round(r_g, 3),
                          "기울기 b": round(slope_g, 4), "R²": round(rv_g**2, 3)})
else:
    dept_counts = view[[a_col, b_col, "주무부처"]].dropna().groupby("주무부처").size().sort_values(ascending=False)
    top_depts = dept_counts.head(15).index.tolist()
    sel_depts = st.multiselect("주무부처 선택 (최대 3~5개 권장)", top_depts, default=top_depts[:3], key="p10_reldepts")
    for dept in sel_depts:
        gs = view[view["주무부처"] == dept][[a_col, b_col]].dropna()
        if gs.shape[0] > 2:
            r_g, _ = stats.pearsonr(gs[a_col], gs[b_col])
            slope_g, intercept_g, rv_g, p_g, se_g = stats.linregress(gs[a_col], gs[b_col])
            rows.append({"그룹": dept, "N": gs.shape[0], "Pearson r": round(r_g, 3),
                          "기울기 b": round(slope_g, 4), "R²": round(rv_g**2, 3)})

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("표시할 관측치가 부족합니다.")

st.divider()

# ---------------- Correlation Matrix ----------------
st.markdown("### 🧮 Correlation Matrix")
sel_cats = st.multiselect("카테고리 선택", CATEGORIES, default=CATEGORIES[:4], key="p10_corr_cats")
candidate_vars = {}
for cat in sel_cats:
    candidate_vars.update(get_vars_by_category(cat))
candidate_vars = {k: v for k, v in candidate_vars.items() if v["column"] in view.columns}
default_corr = list(candidate_vars.keys())[:8]
corr_keys = st.multiselect("변수 선택 (5~12개 권장)", list(candidate_vars.keys()), default=default_corr,
                             format_func=lambda k: get_label(k), key="p10_corr_vars")
if len(corr_keys) >= 2:
    cols = [VARIABLES[k]["column"] for k in corr_keys]
    labels = [get_label(k) for k in corr_keys]
    corr_df = view[cols].apply(pd.to_numeric, errors="coerce").corr(method="pearson")
    st.plotly_chart(plot_correlation_heatmap(corr_df, labels=labels), use_container_width=True)
else:
    st.info("2개 이상의 변수를 선택하세요.")

st.divider()

# ---------------- 상관관계 순위 ----------------
st.markdown("### 📌 상관관계 순위")
st.caption("기준 변수 하나를 고르면, 다른 변수들과의 상관관계를 절댓값 기준으로 정렬해 보여줍니다. (※ '영향요인'이 아니라 '상관관계 순위'입니다)")
all_numeric_keys = [k for k in VARIABLES.keys() if VARIABLES[k]["column"] in view.columns]
base_key = st.selectbox("기준 변수", all_numeric_keys, format_func=lambda k: get_label(k), key="p10_basevar")
base_col = VARIABLES[base_key]["column"]

corr_rows = []
for k in all_numeric_keys:
    if k == base_key:
        continue
    other_col = VARIABLES[k]["column"]
    pair = view[[base_col, other_col]].dropna()
    if pair.shape[0] > 2:
        r_k, p_k = stats.pearsonr(pair[base_col], pair[other_col])
        corr_rows.append({"변수": get_label(k), "Pearson r": round(r_k, 3), "|r|": abs(r_k), "N": pair.shape[0]})
if corr_rows:
    rank_df = pd.DataFrame(corr_rows).sort_values("|r|", ascending=False).drop(columns="|r|").head(15)
    st.dataframe(rank_df, use_container_width=True, hide_index=True)
