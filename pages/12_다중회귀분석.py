import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.regression import run_ols, run_ols_clustered, coef_table, model_summary_stats, compute_vif
from utils.charts import plot_coefficient
from utils.page_header import render_intro

st.set_page_config(page_title="다중회귀분석", layout="wide")
st.title("⑫ 다중회귀분석")
render_intro(
    purpose="다른 변수들을 통제한 이후에도 관심변수와 종속변수의 관계가 유지되는지 확인합니다.",
    unit="기관-연도 pooled 자료 (아래에서 기관 단위 cluster-robust 표준오차를 선택할 수 있습니다)",
    methods="STEP1 분석질문 설정 → STEP2 통제변수 선택 → STEP3 모형비교(Model 1~5, 고정) → STEP4 계수해석 → STEP5 진단",
    caution="통계적으로 유의한 회귀계수도 인과효과를 자동으로 의미하지 않습니다 (누락변수·역인과성·측정오차 등을 고려해야 합니다).",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p14")

st.divider()
st.markdown("### STEP 1 — 분석질문 설정 (Y / X)")
DV_OPTIONS = ["직원평균보수", "신규채용률", "1인당복리후생비", "여성신규채용비율", "여성육아휴직사용자수"]
c1, c2 = st.columns(2)
with c1:
    dv_key = st.selectbox("종속변수 (Y)", DV_OPTIONS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p14_dv")
with c2:
    exp_candidates = [k for k in VARIABLES.keys() if VARIABLES[k]["column"] in df.columns and k != dv_key]
    iv_keys = st.multiselect(
        "핵심 설명변수 (X, 자유롭게 선택)", exp_candidates,
        default=["총수입"] if "총수입" in exp_candidates else exp_candidates[:1],
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p14_iv"
    )
if not iv_keys:
    st.warning("핵심 설명변수를 1개 이상 선택하세요.")
    st.stop()
dv_col = VARIABLES[dv_key]["column"]
iv_cols = [VARIABLES[k]["column"] for k in iv_keys]

st.divider()
st.markdown("### STEP 2 — 통제변수 선택")
numeric_control_options = {"임직원수": "임직원수", "평균근속연수": "평균근속연수", "여성직원비율": "여성직원비율"}
cc1, cc2 = st.columns(2)
with cc1:
    numeric_controls_label = st.multiselect("기관 규모·인력 통제변수 (Model 2 이상에 적용)", list(numeric_control_options.keys()),
                                              default=[list(numeric_control_options.keys())[0]], key="p14_num_controls")
numeric_controls = [numeric_control_options[l] for l in numeric_controls_label
                    if numeric_control_options[l] not in iv_cols and numeric_control_options[l] != dv_col]
with cc2:
    use_cluster = st.checkbox("표준오차: 기관 단위 cluster-robust 사용", value=False, key="p14_cluster")
    st.caption("동일 기관이 여러 연도로 반복 관측되면 오차항이 기관 내부에서 상관될 수 있습니다. "
                "체크하면 기관 단위로 표준오차를 보정합니다 (일반적으로 표준오차가 더 커집니다).")

coef_mode = st.radio("계수 표시", ["비표준화 b", "표준화 β"], horizontal=True, key="p14_coefmode")
st.caption("표준화계수는 변수 간 단위 차이를 줄여 비교하기 위한 값이며, 계수가 크다고 해당 변수가 더 중요한 원인이라는 뜻은 아닙니다. "
            "표준화는 연속형 변수(X, 통제변수, Y)에만 적용되고, 기관유형·주무부처·연도 더미는 그대로 둡니다.")

reg_df = df
if coef_mode == "표준화 β":
    reg_df = df.copy()
    continuous_cols = list(dict.fromkeys(iv_cols + numeric_controls + [dv_col]))
    for c in continuous_cols:
        if c in reg_df.columns:
            s = pd.to_numeric(reg_df[c], errors="coerce")
            std = s.std()
            reg_df[c] = (s - s.mean()) / std if std else s

st.divider()
st.markdown("### STEP 3 — 모형 비교")
st.caption("아래 5개 모형은 항상 동일한 구성으로 고정됩니다 (사용자가 켜고 끌 수 없습니다).")
st.markdown(
    "| 모형 | 구성 |\n|---|---|\n| Model 1 | 핵심 설명변수(X)만 |\n| Model 2 | + 기관 규모·인력(수치형 통제변수) |\n"
    "| Model 3 | + 기관유형 |\n| Model 4 | + 주무부처 |\n| Model 5 | + 연도 |"
)

models_spec = [
    ("Model 1", iv_cols, []),
    ("Model 2", iv_cols + numeric_controls, []),
    ("Model 3", iv_cols + numeric_controls, ["기관유형"]),
    ("Model 4", iv_cols + numeric_controls, ["기관유형", "주무부처"]),
    ("Model 5", iv_cols + numeric_controls, ["기관유형", "주무부처", "연도"]),
]

def _run(xcols, cat_controls):
    xcols = list(dict.fromkeys([c for c in xcols if c in reg_df.columns]))
    # '연도'는 범주형 통제변수로 취급 (문자열 더미), 나머지는 cat_controls 그대로
    year_as_cat = "연도" in cat_controls
    real_cat = [c for c in cat_controls if c != "연도"]
    if use_cluster:
        return run_ols_clustered(reg_df, dv_col, xcols, cat_controls=real_cat + (["연도"] if year_as_cat else []),
                                   cluster_col="기관명")
    return run_ols(reg_df, dv_col, xcols, cat_controls=real_cat + (["연도"] if year_as_cat else []))

results = {}
for name, xcols, cat_controls in models_spec:
    res, data, X = _run(xcols, cat_controls)
    results[name] = (res, X)

st.divider()
st.markdown("### STEP 4 — 계수 해석")
focus_col = iv_cols[0]
coef_rows = []
tabs = st.tabs(list(results.keys()))
for (name, (res, X)), tab in zip(results.items(), tabs):
    with tab:
        if res is None:
            st.warning("관측치가 부족하여 이 모형을 추정할 수 없습니다.")
            continue
        ct = coef_table(res)
        stats_ = model_summary_stats(res)
        s1, s2, s3 = st.columns(3)
        s1.metric("N", stats_["N"])
        s2.metric("R²", f"{stats_['R²']:.3f}")
        s3.metric("adj. R²", f"{stats_['adj. R²']:.3f}")

        show = ct.copy()
        label_map = {v["column"]: get_label(k) for k, v in VARIABLES.items()}
        show["변수"] = show["variable"].replace(label_map)
        coef_header = "계수 β (SE)" if coef_mode == "표준화 β" else "계수 b (SE)"
        show[coef_header] = show.apply(lambda r: f"{r['coef']:,.3f} ({r['std_err']:,.3f})", axis=1)
        show_display = show[["변수", coef_header, "t", "p_value", "ci_low", "ci_high"]].round(4)
        st.dataframe(show_display, use_container_width=True, hide_index=True)

        focus_row = ct[ct["variable"] == focus_col]
        if not focus_row.empty:
            coef_rows.append({"model": name, "coef": focus_row["coef"].values[0],
                              "ci_low": focus_row["ci_low"].values[0], "ci_high": focus_row["ci_high"].values[0]})

if coef_rows:
    st.markdown(f"#### 📈 핵심 변수 계수 변화: {get_label(iv_keys[0])}")
    coef_df = pd.DataFrame(coef_rows).rename(columns={"model": "variable"})
    st.plotly_chart(plot_coefficient(coef_df, title="모형별 핵심 변수 계수 (95% CI)"), use_container_width=True)

    if len(coef_rows) >= 2:
        first_b = coef_rows[0]["coef"]
        last_b = coef_rows[-1]["coef"]
        first_name = coef_rows[0]["model"]
        last_name = coef_rows[-1]["model"]
        if first_b != 0:
            change_pct = (last_b - first_b) / abs(first_b) * 100
            cc1, cc2, cc3 = st.columns(3)
            cc1.metric(f"{first_name} 계수", f"{first_b:,.3f}")
            cc2.metric(f"{last_name} 계수", f"{last_b:,.3f}")
            cc3.metric("계수 변화", f"{'+' if change_pct >= 0 else ''}{change_pct:,.1f}%")
            st.caption("💡 통제변수를 추가하면서 초기 관계가 얼마나 달라지는지 보여주는 참고값입니다. "
                        "이를 인과적 '편향 제거율'이라고 표현하지 않습니다.")

    with st.expander("💡 계량분석 포인트"):
        st.markdown("- 통제변수를 추가했을 때 계수의 크기·부호·유의성이 어떻게 바뀌는지 확인하세요.\n"
                     "- 크게 바뀐다면, 처음 모형에 누락된 변수가 있었을 가능성을 의심할 수 있습니다.\n"
                     "- **기관유형 더미**는 '공기업(시장형)/준정부기관' 같은 범주 간 차이를 통제하고, "
                     "**주무부처 더미**는 주무부처별로 공통적으로 나타나는 평균적 수준 차이를 통제합니다.")

st.divider()

# ---------------- STEP 5: 진단 ----------------
st.markdown("### STEP 5 — 진단")
with st.expander("🔬 회귀진단 (VIF · 잔차)"):
    diag_model = st.selectbox("진단할 모형", list(results.keys()), index=len(results) - 1, key="p14_diagmodel")
    res_d, X_d = results[diag_model]
    if res_d is not None:
        st.markdown("**VIF (분산팽창계수)**")
        st.caption("VIF가 클수록 다른 설명변수와의 선형 중복성이 크다는 뜻입니다. 5 또는 10이 실무적 참고기준으로 쓰이지만, 절대적인 판정기준은 아닙니다.")
        vif_df = compute_vif(X_d)
        if not vif_df.empty:
            vif_df["variable"] = vif_df["variable"].replace({v["column"]: get_label(k) for k, v in VARIABLES.items()})
            st.dataframe(vif_df.round(2), use_container_width=True, hide_index=True)

        c1, c2 = st.columns(2)
        with c1:
            fig_r = px.histogram(res_d.resid, nbins=30, labels={"value": "잔차"})
            fig_r.update_layout(font=dict(size=14), height=380, showlegend=False, title="잔차 히스토그램")
            st.plotly_chart(fig_r, use_container_width=True)
        with c2:
            fig_rf = go.Figure(go.Scatter(x=res_d.fittedvalues, y=res_d.resid, mode="markers",
                                            marker=dict(color="#4C78A8", size=6, opacity=0.6)))
            fig_rf.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_rf.update_layout(font=dict(size=14), height=380, title="잔차 vs 적합값",
                                   xaxis_title="적합값", yaxis_title="잔차")
            st.plotly_chart(fig_rf, use_container_width=True)
    else:
        st.info("선택한 모형을 추정할 수 없습니다.")

st.divider()
st.warning(
    "**관찰자료의 회귀계수가 통계적으로 유의하더라도 이를 인과효과로 바로 해석할 수 없습니다.**\n\n"
    "누락변수, 역인과성, 측정오차 등을 고려해야 합니다."
)
