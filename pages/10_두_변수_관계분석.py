import streamlit as st
import pandas as pd
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit
from utils.charts import plot_scatter
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="두 변수 관계분석", layout="wide")
st.title("⑩ 두 변수 관계분석")
render_intro(
    purpose="두 연속형 변수의 관계 방향과 강도를 확인합니다.",
    unit="선택 연도의 기관 (기본값: 최신연도) — '전체 기간'을 선택하면 기관-연도가 함께 pooled됩니다",
    methods="산점도 · Pearson r · Spearman ρ · 단순회귀선 · R² · 선택기관 강조",
    caution="두 변수가 함께 움직인다고 해서 하나가 다른 하나의 원인이라는 뜻은 아닙니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p9")

# 수정된 preset (변수명 오류 수정 + 비율 변수 위주로 조정)
PRESETS = {
    "직접 선택": None,
    "평균보수 ↔ 신입초임": ("직원평균보수", "신입사원초임"),
    "평균근속연수 ↔ 평균보수": ("평균근속연수", "직원평균보수"),
    "기관장-직원 보수배율 ↔ 직원평균보수": ("기관장직원보수배율", "직원평균보수"),
    "총수입 ↔ 직원평균보수": ("총수입", "직원평균보수"),
    "정부지원의존도 ↔ 직원평균보수": ("정부지원의존도", "직원평균보수"),
    "정부지원의존도 ↔ 신규채용률": ("정부지원의존도", "신규채용률"),
    "여성직원비율 ↔ 여성신규채용비율": ("여성직원비율", "여성신규채용비율"),
    "여성직원비율 ↔ 남성육아휴직사용자수": ("여성직원비율", "남성육아휴직사용자수"),
    "과세표준 ↔ 법인세결정세액": ("과세표준", "법인세결정세액"),
}

st.divider()
preset_choice = st.selectbox("💡 추천 관계 (선택하면 아래 A/B가 바뀝니다 — 이후 자유롭게 수정 가능)",
                               list(PRESETS.keys()), key="p9_preset")
default_a, default_b = PRESETS[preset_choice] if PRESETS[preset_choice] else ("임직원수", "직원평균보수")

c1, c2 = st.columns(2)
with c1:
    st.markdown("**변수 A**")
    a_cat = st.selectbox("카테고리", CATEGORIES, index=CATEGORIES.index(VARIABLES[default_a]["category"]), key="p9_acat")
    a_vars = get_vars_by_category(a_cat)
    a_default_idx = list(a_vars.keys()).index(default_a) if default_a in a_vars else 0
    a_key = st.selectbox("변수", list(a_vars.keys()), index=a_default_idx,
                           format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p9_avar")
with c2:
    st.markdown("**변수 B**")
    b_cat = st.selectbox("카테고리", CATEGORIES, index=CATEGORIES.index(VARIABLES[default_b]["category"]), key="p9_bcat")
    b_vars = get_vars_by_category(b_cat)
    b_default_idx = list(b_vars.keys()).index(default_b) if default_b in b_vars else 0
    b_key = st.selectbox("변수", list(b_vars.keys()), index=b_default_idx,
                           format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p9_bvar")

a_col, b_col = VARIABLES[a_key]["column"], VARIABLES[b_key]["column"]
if a_col not in df.columns or b_col not in df.columns:
    st.warning("선택한 변수 조합이 데이터에 없습니다.")
    st.stop()

view, caption, mode = year_slice(df, key_prefix="p9")
st.caption(caption)

st.divider()
c3, c4 = st.columns(2)
with c3:
    color_by = st.radio("색상 구분", ["기관유형", "주무부처"], horizontal=True, key="p9_color")
with c4:
    orgs = sorted(view["기관명"].unique())
    highlight = st.selectbox("특정 기관 강조", ["(없음)"] + orgs, key="p9_highlight")

fig = plot_scatter(view, a_col, b_col, x_key=a_key, y_key=b_key, color_col=color_by,
                     trendline="ols", highlight_org=None if highlight == "(없음)" else highlight)
st.plotly_chart(fig, use_container_width=True)

st.markdown("### 관계 통계")
sub = view[[a_col, b_col]].dropna()
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

    if highlight != "(없음)":
        hi_row = view[view["기관명"] == highlight][[a_col, b_col]].dropna()
        if not hi_row.empty:
            st.markdown(f"#### 📍 {highlight}, 회귀선에서 얼마나 벗어났나?")
            x_val = hi_row[a_col].iloc[-1]
            y_actual = hi_row[b_col].iloc[-1]
            y_pred = slope * x_val + intercept
            residual = y_actual - y_pred
            rc1, rc2, rc3 = st.columns(3)
            rc1.metric(f"실제 {get_label(b_key)}", f"{y_actual:,.1f}")
            rc2.metric("회귀모형 예측값", f"{y_pred:,.1f}")
            rc3.metric("차이 (잔차)", f"{'+' if residual >= 0 else ''}{residual:,.1f}")
            st.caption("💡 잔차는 변수 A만으로 설명되지 않은 차이입니다. 그 기관만의 고유한 특성일 수도 있지만, "
                        "측정오차·일시적 요인·다른 누락된 변수 등도 함께 포함될 수 있습니다.")

    st.divider()

    # ---------------- 추가 1: 이상치 민감도 ----------------
    st.markdown("### 추가 분석 1 — 이상치 민감도")
    check_outlier = st.checkbox("상하위 1% 극단값 제외 후 관계 다시 계산", key="p9_outliercheck")
    st.caption("💡 극단값 몇 개가 전체 관계를 크게 좌우하는지 확인합니다 (이상치를 '나쁜 데이터'라고 단정하는 것이 아니라, 관계의 민감도를 확인하는 것입니다).")
    if check_outlier:
        lo_a, hi_a = sub[a_col].quantile([0.01, 0.99])
        lo_b, hi_b = sub[b_col].quantile([0.01, 0.99])
        trimmed = sub[(sub[a_col].between(lo_a, hi_a)) & (sub[b_col].between(lo_b, hi_b))]
        if trimmed.shape[0] > 2:
            r_t, _ = stats.pearsonr(trimmed[a_col], trimmed[b_col])
            slope_t, intercept_t, rv_t, p_t, se_t = stats.linregress(trimmed[a_col], trimmed[b_col])
            comp_df = pd.DataFrame([
                {"구분": "전체 표본", "N": sub.shape[0], "Pearson r": round(r, 3), "기울기 b": round(slope, 4), "R²": round(r_value**2, 3)},
                {"구분": "극단값 제외", "N": trimmed.shape[0], "Pearson r": round(r_t, 3), "기울기 b": round(slope_t, 4), "R²": round(rv_t**2, 3)},
            ])
            st.dataframe(comp_df, use_container_width=True, hide_index=True)
        else:
            st.info("극단값을 제외하면 관측치가 너무 적어 다시 계산할 수 없습니다.")

    # ---------------- 추가 2: 부분상관 ----------------
    st.markdown("### 추가 분석 2 — 통제변수 하나를 사용한 부분상관")
    control_options = {"없음": None, "임직원수": "임직원수", "평균근속연수": "평균근속연수", "여성직원비율": "여성직원비율"}
    control_choice = st.selectbox("통제변수", list(control_options.keys()), key="p9_control")
    control_key = control_options[control_choice]
    if control_key and control_key not in (a_key, b_key):
        control_col = VARIABLES[control_key]["column"]
        if control_col in view.columns:
            sub3 = view[[a_col, b_col, control_col]].dropna()
            if sub3.shape[0] > 3:
                r_az, _ = stats.pearsonr(sub3[a_col], sub3[control_col])
                r_bz, _ = stats.pearsonr(sub3[b_col], sub3[control_col])
                r_ab, _ = stats.pearsonr(sub3[a_col], sub3[b_col])
                denom = ((1 - r_az**2) * (1 - r_bz**2)) ** 0.5
                if denom > 0:
                    partial_r = (r_ab - r_az * r_bz) / denom
                    m1, m2 = st.columns(2)
                    m1.metric("단순 Pearson r", f"{r_ab:.3f}")
                    m2.metric(f"{control_choice} 통제 후 partial r", f"{partial_r:.3f}")
                    st.caption(f"💡 두 변수의 관계 중 '{control_choice}'와 함께 움직이는 부분을 제거한 뒤 남은 선형관계입니다. "
                                "부분상관 역시 인과관계를 의미하지 않습니다.")
                else:
                    st.info("부분상관을 계산할 수 없습니다 (통제변수와 완전한 상관관계).")
            else:
                st.info("부분상관을 계산할 만큼 관측치가 충분하지 않습니다.")
        else:
            st.info("선택한 통제변수가 데이터에 없습니다.")
else:
    st.warning("상관계수를 계산할 만큼 관측치가 충분하지 않습니다.")

st.caption("⚠️ 두 변수가 함께 움직인다고 해서 인과관계를 의미하지는 않습니다. "
            "이 관계가 기관유형·주무부처 내부에서도 유지되는지는 ⑪번 페이지에서 확인할 수 있습니다.")
