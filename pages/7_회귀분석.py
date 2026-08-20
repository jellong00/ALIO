import streamlit as st
import pandas as pd

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit
from utils.regression import run_ols, coef_table, model_summary_stats
from utils.charts import plot_coefficient

st.set_page_config(page_title="회귀분석", layout="wide")
st.title("⑦ 회귀분석")
st.markdown("#### 오늘의 질문")
st.info("**Q7. 다른 조건을 통제한 이후에도 관찰된 관계가 유지되는가?**")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p7")

DV_OPTIONS = ["직원평균보수", "신규채용률", "여성신규채용비율", "1인당복리후생비", "여성육아휴직사용률"]
IV_OPTIONS = ["총수입", "정부지원의존도", "과세표준", "법인세결정세액", "임직원수",
              "여성직원비율", "평균근속연수", "직원평균보수"]

c1, c2 = st.columns(2)
with c1:
    dv_key = st.selectbox("종속변수", DV_OPTIONS, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p7_dv")
with c2:
    iv_keys = st.multiselect(
        "핵심 설명변수 (1개 이상)", [v for v in IV_OPTIONS if v != dv_key],
        default=[[v for v in IV_OPTIONS if v != dv_key][0]],
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p7_iv"
    )

if not iv_keys:
    st.warning("핵심 설명변수를 1개 이상 선택하세요.")
    st.stop()

dv_col = VARIABLES[dv_key]["column"]
iv_cols = [VARIABLES[k]["column"] for k in iv_keys]

missing = [c for c in [dv_col] + iv_cols if c not in df.columns]
if missing:
    st.warning(f"데이터에 없는 변수가 있습니다: {missing}")
    st.stop()

st.divider()
st.markdown("### 통제변수 선택")
numeric_control_options = {"기관규모(임직원수)": "임직원수", "평균근속연수": "평균근속연수", "여성직원비율": "여성직원비율"}
cc1, cc2 = st.columns(2)
with cc1:
    numeric_controls_label = st.multiselect(
        "기관 특성 통제 (수치형)", list(numeric_control_options.keys()),
        default=list(numeric_control_options.keys())[:1], key="p7_num_controls"
    )
numeric_controls = [numeric_control_options[l] for l in numeric_controls_label if numeric_control_options[l] not in iv_cols and numeric_control_options[l] != dv_col]

with cc2:
    use_org_type = st.checkbox("기관유형 통제 (더미)", value=True, key="p7_orgtype")
    use_year = st.checkbox("연도 통제 (더미)", value=False, key="p7_year")

st.caption("범주형 통제변수(기관유형·연도)는 더미변수로 자동 처리됩니다.")

st.divider()
st.markdown("### 단계별 회귀모형 비교")
st.markdown(
    """
| 모형 | 구성 |
|---|---|
| Model 1 | 핵심 설명변수만 |
| Model 2 | + 기관 특성 (수치형 통제변수) |
| Model 3 | + 기관유형 (더미) |
| Model 4 | + 연도 (더미) |
"""
)

models_spec = [
    ("Model 1", iv_cols, [], False, False),
    ("Model 2", iv_cols + numeric_controls, [], False, False),
    ("Model 3", iv_cols + numeric_controls, ["기관유형"] if use_org_type else [], False, False),
    ("Model 4", iv_cols + numeric_controls, ["기관유형"] if use_org_type else [], False, use_year),
]

results = {}
for name, xcols, cat_controls, efe, yfe in models_spec:
    xcols = list(dict.fromkeys([c for c in xcols if c in df.columns]))
    res, data = run_ols(df, dv_col, xcols, cat_controls=cat_controls, entity_fe=efe, year_fe=yfe)
    results[name] = (res, xcols)

focus_col = iv_cols[0]
rows = []
tabs = st.tabs(list(results.keys()))
for (name, (res, xcols)), tab in zip(results.items(), tabs):
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
        show["variable"] = show["variable"].replace(
            {v["column"]: f"{get_label(k)}" for k, v in VARIABLES.items()}
        )
        st.dataframe(show.round(4), use_container_width=True, hide_index=True)

        focus_row = ct[ct["variable"] == focus_col]
        if not focus_row.empty:
            rows.append({"model": name, "coef": focus_row["coef"].values[0],
                         "ci_low": focus_row["ci_low"].values[0], "ci_high": focus_row["ci_high"].values[0]})

if rows:
    st.divider()
    st.markdown(f"### 📈 핵심 변수 계수 변화: {get_label(next(k for k in iv_keys if VARIABLES[k]['column']==focus_col))}")
    coef_df = pd.DataFrame(rows).rename(columns={"model": "variable"})
    st.plotly_chart(plot_coefficient(coef_df, title="모형별 핵심 변수 계수 (95% CI)"), use_container_width=True)

st.divider()
st.warning(
    "**통계적으로 유의한 회귀계수는 인과효과를 자동으로 의미하지 않습니다.**\n\n"
    "다음을 함께 고려하세요:\n"
    "- 누락변수가 있는가? (관측되지 않은 기관 특성이 X와 Y 모두에 영향을 줄 수 있는가)\n"
    "- 역인과성이 가능한가? (Y가 X에 영향을 주는 경로는 없는가)\n"
    "- 기관유형을 통제해야 하는 이유는 무엇인가?\n"
    "- 기관규모를 추가했을 때 계수가 왜 변하는가?\n"
    "- 동일 기관의 고유한 특성(시간 불변)이 결과에 영향을 미치지는 않는가? → 패널데이터 페이지에서 확인"
)
