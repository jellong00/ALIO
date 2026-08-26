import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit
from utils.charts import plot_scatter, plot_correlation_heatmap

st.set_page_config(page_title="변수간 관계분석", layout="wide")
st.title("⑤ 변수 간 관계분석")
st.caption("서로 다른 공공기관 지표가 어떻게 함께 움직이는지 탐색하는, 이 대시보드의 핵심 페이지입니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p5")

# ---------------- 추천 관계 Preset ----------------
PRESETS = {
    "[보수] 평균보수 ↔ 신입초임": ("직원평균보수", "신입사원초임"),
    "[보수] 평균보수 ↔ 평균근속연수": ("평균근속연수", "직원평균보수"),
    "[보수] 직원평균보수 ↔ 기관장연봉": ("직원평균보수", "기관장연봉"),
    "[보수] 기관유형 ↔ 보수배율": ("기관장직원보수배율", "직원평균보수"),
    "[규모] 임직원수 ↔ 직원평균보수": ("임직원수", "직원평균보수"),
    "[규모] 임직원수 ↔ 복리후생비": ("임직원수", "복리후생비"),
    "[규모] 임직원수 ↔ 1인당복리후생비": ("임직원수", "1인당복리후생비"),
    "[재정] 총수입 ↔ 직원평균보수": ("총수입", "직원평균보수"),
    "[재정] 사업수입 ↔ 직원평균보수": ("사업수입", "직원평균보수"),
    "[재정] 정부지원수입 ↔ 정부지원의존도": ("정부지원수입", "정부지원의존도"),
    "[재정] 정부지원의존도 ↔ 직원평균보수": ("정부지원의존도", "직원평균보수"),
    "[재정] 정부지원의존도 ↔ 신규채용률": ("정부지원의존도", "신규채용률"),
    "[채용] 평균보수 ↔ 신규채용률": ("직원평균보수", "신규채용률"),
    "[채용] 평균근속연수 ↔ 신규채용률": ("평균근속연수", "신규채용률"),
    "[채용] 임직원수 ↔ 신규채용자수": ("임직원수", "신규채용자수"),
    "[채용] 신규채용자수 ↔ 신규채용률": ("신규채용자수", "신규채용률"),
    "[성별·일가정양립] 여성직원수 ↔ 여성신규채용자수": ("여성현원", "여성신규채용자수"),
    "[성별·일가정양립] 여성직원비율 ↔ 남성육아휴직사용자수": ("여성직원비율", "남성육아휴직사용자수"),
    "[성별·일가정양립] 1인당복리후생비 ↔ 여성육아휴직사용자수": ("1인당복리후생비", "여성육아휴직사용자수"),
    "[법인세] 과세표준 ↔ 법인세결정세액": ("과세표준", "법인세결정세액"),
    "[법인세] 총수입 ↔ 법인세결정세액": ("총수입", "법인세결정세액"),
    "[법인세] 사업수입 ↔ 법인세결정세액": ("사업수입", "법인세결정세액"),
}

st.divider()
preset_choice = st.selectbox("💡 추천 관계 (선택하면 아래 변수 A/B가 바뀝니다 — 이후 자유롭게 수정 가능)",
                               ["직접 선택"] + list(PRESETS.keys()), key="p5_preset")
if preset_choice != "직접 선택":
    default_a, default_b = PRESETS[preset_choice]
else:
    default_a, default_b = "임직원수", "직원평균보수"

st.markdown("### 변수 선택")
c1, c2 = st.columns(2)
with c1:
    st.markdown("**변수 A**")
    a_cat = st.selectbox("카테고리", CATEGORIES, index=CATEGORIES.index(VARIABLES[default_a]["category"]), key="p5_acat")
    a_vars = get_vars_by_category(a_cat)
    a_default_idx = list(a_vars.keys()).index(default_a) if default_a in a_vars else 0
    a_key = st.selectbox("변수", list(a_vars.keys()), index=a_default_idx,
                           format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p5_avar")
with c2:
    st.markdown("**변수 B**")
    b_cat = st.selectbox("카테고리", CATEGORIES, index=CATEGORIES.index(VARIABLES[default_b]["category"]), key="p5_bcat")
    b_vars = get_vars_by_category(b_cat)
    b_default_idx = list(b_vars.keys()).index(default_b) if default_b in b_vars else 0
    b_key = st.selectbox("변수", list(b_vars.keys()), index=b_default_idx,
                           format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p5_bvar")

a_col, b_col = VARIABLES[a_key]["column"], VARIABLES[b_key]["column"]
if a_col not in df.columns or b_col not in df.columns:
    st.warning("선택한 변수 조합이 데이터에 없습니다.")
    st.stop()

st.divider()

# ---------------- 옵션 ----------------
o1, o2, o3, o4, o5, o6 = st.columns(6)
with o1:
    color_by = st.radio("색상", ["기관유형", "주무부처"], key="p5_color")
with o2:
    log_a = st.checkbox("A 로그", value=VARIABLES[a_key]["log_allowed"], key="p5_loga")
with o3:
    log_b = st.checkbox("B 로그", value=VARIABLES[b_key]["log_allowed"], key="p5_logb")
with o4:
    trendline = st.checkbox("추세선", value=True, key="p5_trend")
with o5:
    show_labels = st.checkbox("기관명 라벨", value=False, key="p5_labels")
with o6:
    years = sorted(df["연도"].unique())
    year_choice = st.selectbox("연도", ["전체"] + [str(y) for y in years], key="p5_year")

orgs = sorted(df["기관명"].unique())
highlight = st.selectbox("특정 기관 강조", ["(없음)"] + orgs, key="p5_highlight")

plot_df = df if year_choice == "전체" else df[df["연도"] == int(year_choice)]

fig = plot_scatter(
    plot_df, a_col, b_col, x_key=a_key, y_key=b_key, color_col=color_by,
    trendline="ols" if trendline else None, log_x=log_a, log_y=log_b,
    highlight_org=None if highlight == "(없음)" else highlight,
)
if show_labels:
    fig.update_traces(text=plot_df["기관명"], textposition="top center")
    fig.update_traces(mode="markers+text")
st.plotly_chart(fig, use_container_width=True)

# ---------------- 관계 통계 ----------------
st.markdown("### 관계 통계")
sub = plot_df[[a_col, b_col]].dropna()
if sub.shape[0] > 2:
    r, p_r = stats.pearsonr(sub[a_col], sub[b_col])
    rho, p_rho = stats.spearmanr(sub[a_col], sub[b_col])
    slope, intercept, r_value, p_slope, se = stats.linregress(sub[a_col], sub[b_col])
    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Pearson r", f"{r:.3f}")
    k2.metric("Spearman ρ", f"{rho:.3f}")
    k3.metric("N", f"{sub.shape[0]:,}")
    k4.metric("기울기 b", f"{slope:,.4f}")
    k5.metric("p-value", f"{p_r:.4f}")
    k6.metric("R²", f"{r_value**2:.3f}")
else:
    st.warning("상관계수를 계산할 만큼 관측치가 충분하지 않습니다.")

# ---------------- 회귀선 이탈 (선택기관) ----------------
if highlight != "(없음)" and sub.shape[0] > 2:
    st.markdown(f"### 📍 {highlight}, 회귀선에서 얼마나 벗어났나?")
    hi_row = plot_df[plot_df["기관명"] == highlight][[a_col, b_col]].dropna()
    if not hi_row.empty:
        x_val = hi_row[a_col].iloc[-1]
        y_actual = hi_row[b_col].iloc[-1]
        y_pred = slope * x_val + intercept
        residual = y_actual - y_pred
        rc1, rc2, rc3 = st.columns(3)
        rc1.metric(f"실제 {get_label(b_key)}", f"{y_actual:,.1f}")
        rc2.metric("회귀모형 예측값", f"{y_pred:,.1f}")
        rc3.metric("차이 (잔차)", f"{'+' if residual >= 0 else ''}{residual:,.1f}")
        direction = "높습니다" if residual > 0 else ("낮습니다" if residual < 0 else "같습니다")
        st.caption(f"💡 {get_label(a_key)}만으로 예상한 값보다 {highlight}의 {get_label(b_key)}이(가) {direction}. "
                    "이 차이(잔차)는 X 변수 하나로는 설명되지 않는, 그 기관만의 고유한 특성일 수 있습니다.")
    else:
        st.info("선택한 기관에 유효한 값이 없습니다.")

st.divider()

# ---------------- 관계 비교 기준 ----------------
st.markdown("### 관계 비교 기준")
relation_basis = st.radio("비교 기준", ["전체", "기관유형별", "주무부처별"], horizontal=True, key="p5_relbasis", label_visibility="collapsed")

rows = []
if relation_basis == "전체":
    if sub.shape[0] > 2:
        rows.append({"그룹": "전체", "N": sub.shape[0], "Pearson r": round(r, 3),
                      "기울기 b": round(slope, 4), "R²": round(r_value**2, 3)})
elif relation_basis == "기관유형별":
    for org_type, g in plot_df.groupby("기관유형"):
        gs = g[[a_col, b_col]].dropna()
        if gs.shape[0] > 2:
            r_g, _ = stats.pearsonr(gs[a_col], gs[b_col])
            slope_g, intercept_g, rv_g, p_g, se_g = stats.linregress(gs[a_col], gs[b_col])
            rows.append({"그룹": org_type, "N": gs.shape[0], "Pearson r": round(r_g, 3),
                          "기울기 b": round(slope_g, 4), "R²": round(rv_g**2, 3)})
else:
    dept_counts = plot_df[[a_col, b_col, "주무부처"]].dropna().groupby("주무부처").size().sort_values(ascending=False)
    top_depts = dept_counts.head(15).index.tolist()
    sel_depts = st.multiselect("주무부처 선택 (최대 3~5개 권장)", top_depts, default=top_depts[:3], key="p5_reldepts")
    for dept in sel_depts:
        gs = plot_df[plot_df["주무부처"] == dept][[a_col, b_col]].dropna()
        if gs.shape[0] > 2:
            r_g, _ = stats.pearsonr(gs[a_col], gs[b_col])
            slope_g, intercept_g, rv_g, p_g, se_g = stats.linregress(gs[a_col], gs[b_col])
            rows.append({"그룹": dept, "N": gs.shape[0], "Pearson r": round(r_g, 3),
                          "기울기 b": round(slope_g, 4), "R²": round(rv_g**2, 3)})

if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    if relation_basis != "전체":
        st.caption("💡 전체 상관관계와 집단별 상관관계가 다르게 나타난다면, 심슨의 역설(Simpson's paradox) 가능성을 의심해볼 수 있습니다.")
else:
    st.info("표시할 관측치가 부족합니다.")

st.caption("⚠️ 두 변수가 함께 움직인다고 해서 인과관계를 의미하지는 않습니다.")

st.divider()

# ---------------- Correlation Matrix ----------------
st.markdown("### 🧮 Correlation Matrix")
sel_cats = st.multiselect("카테고리 선택", CATEGORIES, default=CATEGORIES, key="p5_corr_cats")
candidate_vars = {}
for cat in sel_cats:
    candidate_vars.update(get_vars_by_category(cat))
candidate_vars = {k: v for k, v in candidate_vars.items() if v["column"] in df.columns}
default_corr = list(candidate_vars.keys())[:8]
corr_keys = st.multiselect("변수 선택 (5~12개 권장)", list(candidate_vars.keys()), default=default_corr,
                             format_func=lambda k: get_label(k), key="p5_corr_vars")
if len(corr_keys) >= 2:
    cols = [VARIABLES[k]["column"] for k in corr_keys]
    labels = [get_label(k) for k in corr_keys]
    corr_df = df[cols].apply(pd.to_numeric, errors="coerce").corr(method="pearson")
    st.plotly_chart(plot_correlation_heatmap(corr_df, labels=labels), use_container_width=True)
else:
    st.info("2개 이상의 변수를 선택하세요.")

st.divider()

# ---------------- 상관관계 순위 ----------------
st.markdown("### 📌 상관관계 순위")
st.caption("기준 변수 하나를 고르면, 다른 변수들과의 상관관계를 절댓값 기준으로 정렬해 보여줍니다. (※ '영향요인'이 아니라 '상관관계 순위'입니다)")
all_numeric_keys = [k for k in VARIABLES.keys() if VARIABLES[k]["column"] in df.columns]
base_key = st.selectbox("기준 변수", all_numeric_keys, format_func=lambda k: get_label(k), key="p5_basevar")
base_col = VARIABLES[base_key]["column"]

corr_rows = []
for k in all_numeric_keys:
    if k == base_key:
        continue
    other_col = VARIABLES[k]["column"]
    pair = df[[base_col, other_col]].dropna()
    if pair.shape[0] > 2:
        r_k, p_k = stats.pearsonr(pair[base_col], pair[other_col])
        corr_rows.append({"변수": get_label(k), "Pearson r": round(r_k, 3), "|r|": abs(r_k), "N": pair.shape[0]})
if corr_rows:
    rank_df = pd.DataFrame(corr_rows).sort_values("|r|", ascending=False).drop(columns="|r|").head(15)
    st.dataframe(rank_df, use_container_width=True, hide_index=True)
