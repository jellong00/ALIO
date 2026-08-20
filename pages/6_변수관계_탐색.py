import streamlit as st
import pandas as pd
import numpy as np
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_domain, DOMAINS, get_label, get_unit
from utils.charts import plot_scatter, plot_correlation_heatmap

st.set_page_config(page_title="변수 관계 탐색", layout="wide")
st.title("⑥ 변수 관계 탐색")
st.markdown("#### 오늘의 질문")
st.info("**Q6. 기관 특성·재정·조직 운영·인사 결과는 서로 어떤 관계를 갖는가?**")
st.caption("이 페이지는 대시보드의 핵심입니다. 4개 영역의 모든 변수를 자유롭게 X/Y로 연결할 수 있습니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p6")

PRESETS = {
    "직접 선택": None,
    "기관규모 ↔ 총수입": ("임직원수", "총수입"),
    "기관규모 ↔ 정부지원수입": ("임직원수", "정부지원수입"),
    "기관규모 ↔ 정부지원의존도": ("임직원수", "정부지원의존도"),
    "임직원수 ↔ 직원평균보수": ("임직원수", "직원평균보수"),
    "평균근속연수 ↔ 직원평균보수": ("평균근속연수", "직원평균보수"),
    "기관규모 ↔ 복리후생비": ("임직원수", "복리후생비"),
    "총수입 ↔ 직원평균보수": ("총수입", "직원평균보수"),
    "총수입 ↔ 1인당복리후생비": ("총수입", "1인당복리후생비"),
    "정부지원의존도 ↔ 직원평균보수": ("정부지원의존도", "직원평균보수"),
    "정부지원의존도 ↔ 1인당복리후생비": ("정부지원의존도", "1인당복리후생비"),
    "과세표준 ↔ 직원평균보수": ("과세표준", "직원평균보수"),
    "법인세결정세액 ↔ 직원평균보수": ("법인세결정세액", "직원평균보수"),
    "총수입 ↔ 신규채용률": ("총수입", "신규채용률"),
    "정부지원의존도 ↔ 신규채용률": ("정부지원의존도", "신규채용률"),
    "과세표준 ↔ 신규채용률": ("과세표준", "신규채용률"),
    "직원평균보수 ↔ 신규채용률": ("직원평균보수", "신규채용률"),
    "1인당복리후생비 ↔ 여성육아휴직사용률": ("1인당복리후생비", "여성육아휴직사용률"),
    "여성직원비율 ↔ 여성육아휴직사용률": ("여성직원비율", "여성육아휴직사용률"),
}

preset_choice = st.selectbox("💡 관계 프리셋 (선택 후 자유롭게 수정 가능)", list(PRESETS.keys()), key="p6_preset")

var_keys = list(VARIABLES.keys())

# 프리셋에 따른 기본값 계산
if PRESETS[preset_choice] is not None:
    default_x, default_y = PRESETS[preset_choice]
else:
    default_x, default_y = "임직원수", "직원평균보수"

st.markdown("### Step 1~2. X 변수")
xc1, xc2 = st.columns(2)
with xc1:
    x_domain = st.selectbox("X 영역", DOMAINS, index=DOMAINS.index(VARIABLES[default_x]["domain"]), key="p6_xdomain")
x_vars = get_vars_by_domain(x_domain)
x_default_idx = list(x_vars.keys()).index(default_x) if default_x in x_vars else 0
with xc2:
    x_key = st.selectbox("X 변수", list(x_vars.keys()), index=x_default_idx,
                           format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p6_xvar")

st.markdown("### Step 3~4. Y 변수")
yc1, yc2 = st.columns(2)
with yc1:
    y_domain = st.selectbox("Y 영역", DOMAINS, index=DOMAINS.index(VARIABLES[default_y]["domain"]), key="p6_ydomain")
y_vars = {k: v for k, v in get_vars_by_domain(y_domain).items()}
y_default_idx = list(y_vars.keys()).index(default_y) if default_y in y_vars else 0
with yc2:
    y_key = st.selectbox("Y 변수", list(y_vars.keys()), index=y_default_idx,
                           format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p6_yvar")

x_col, y_col = VARIABLES[x_key]["column"], VARIABLES[y_key]["column"]

if x_col not in df.columns or y_col not in df.columns:
    st.warning("선택한 변수 조합이 데이터에 없습니다.")
    st.stop()

st.divider()

# ---------------- 옵션 ----------------
o1, o2, o3, o4, o5 = st.columns(5)
with o1:
    trendline = st.checkbox("회귀선 표시", value=True, key="p6_trend")
with o2:
    log_x = st.checkbox("X 로그", value=VARIABLES[x_key]["log_allowed"], key="p6_logx")
with o3:
    log_y = st.checkbox("Y 로그", value=VARIABLES[y_key]["log_allowed"], key="p6_logy")
with o4:
    show_labels = st.checkbox("기관명 라벨", value=False, key="p6_labels")
with o5:
    orgs = sorted(df["기관명"].unique())
    highlight = st.selectbox("특정 기관 강조", ["(없음)"] + orgs, key="p6_highlight")

fig = plot_scatter(
    df, x_col, y_col, x_key=x_key, y_key=y_key,
    trendline="ols" if trendline else None,
    log_x=log_x, log_y=log_y,
    highlight_org=None if highlight == "(없음)" else highlight,
)
if show_labels:
    fig.update_traces(mode="markers+text", selector=dict(mode="markers"))
    fig.update_traces(text=df["기관명"], textposition="top center", selector=dict(mode="markers+text"))
st.plotly_chart(fig, use_container_width=True)

# ---------------- 관계 통계 ----------------
st.markdown("### 관계 통계")
sub = df[[x_col, y_col]].dropna()
if sub.shape[0] > 2:
    r, p_pearson = stats.pearsonr(sub[x_col], sub[y_col])
    rho, p_spearman = stats.spearmanr(sub[x_col], sub[y_col])
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pearson r", f"{r:.3f}")
    m2.metric("Spearman ρ", f"{rho:.3f}")
    m3.metric("p-value", f"{p_pearson:.4f}")
    m4.metric("N", f"{sub.shape[0]:,}")
else:
    st.warning("상관계수를 계산할 만큼 관측치가 충분하지 않습니다.")

# ---------------- 기관유형별 상관 ----------------
st.markdown("### 기관유형별 상관계수")
rows = []
for org_type, g in df.groupby("기관유형"):
    gs = g[[x_col, y_col]].dropna()
    if gs.shape[0] > 2:
        r_g, p_g = stats.pearsonr(gs[x_col], gs[y_col])
        rows.append({"기관유형": org_type, "r": round(r_g, 3), "p-value": round(p_g, 4), "N": gs.shape[0]})
if rows:
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    st.caption("💡 전체 상관관계와 기관유형 내부 상관관계가 다르다면, 이는 '심슨의 역설(Simpson's paradox)' 가능성을 시사합니다. "
               "기관유형을 통제하지 않은 전체 상관관계 해석에 주의하세요.")
else:
    st.info("기관유형별로 계산할 관측치가 부족합니다.")

st.divider()

# ---------------- Correlation Matrix ----------------
st.markdown("### 🧮 Correlation Matrix")
sel_domains = st.multiselect("영역 선택", DOMAINS, default=DOMAINS, key="p6_corr_domains")
candidate_vars = {}
for d in sel_domains:
    candidate_vars.update(get_vars_by_domain(d))
candidate_vars = {k: v for k, v in candidate_vars.items() if v["column"] in df.columns}

default_corr_vars = list(candidate_vars.keys())[:8]
corr_var_keys = st.multiselect(
    "변수 선택 (5~12개 권장)", list(candidate_vars.keys()), default=default_corr_vars,
    format_func=lambda k: get_label(k), key="p6_corr_vars"
)

if len(corr_var_keys) >= 2:
    cols = [VARIABLES[k]["column"] for k in corr_var_keys]
    labels = [get_label(k) for k in corr_var_keys]
    corr_df = df[cols].apply(pd.to_numeric, errors="coerce").corr(method="pearson")
    fig2 = plot_correlation_heatmap(corr_df, labels=labels)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("모든 값을 표시합니다 (강한 상관만 강조하지 않음). 대각선은 항상 1입니다.")
else:
    st.info("2개 이상의 변수를 선택하세요.")
