import streamlit as st
from utils.page_common import render_domain_page

df, var_key, col = render_domain_page(
    domain="조직 운영",
    question="Q4. 공공기관은 확보한 재정과 인력을 어떻게 운영하고 있는가?",
    intro="직원·임원 보수, 복리후생비, 기관장업무추진비 등 조직 운영 지표를 살펴보고, "
          "재정 구조(총수입·정부지원의존도 등)와의 관계를 탐색한다.",
)

if df is not None:
    st.divider()
    st.markdown("### 🔗 재정-조직운영 연결 프리셋")
    presets = {
        "총수입 → 직원평균보수": ("총수입", "직원평균보수"),
        "총수입 → 복리후생비": ("총수입", "복리후생비"),
        "정부지원의존도 → 직원평균보수": ("정부지원의존도", "직원평균보수"),
        "정부지원의존도 → 1인당복리후생비": ("정부지원의존도", "1인당복리후생비"),
        "과세표준 → 직원평균보수": ("과세표준", "직원평균보수"),
        "임직원수 → 직원평균보수": ("임직원수", "직원평균보수"),
        "평균근속연수 → 직원평균보수": ("평균근속연수", "직원평균보수"),
    }
    choice = st.selectbox("프리셋 선택", list(presets.keys()), key="p4_preset")
    from utils.variables import VARIABLES, get_label
    from utils.charts import plot_scatter
    from scipy import stats

    xk, yk = presets[choice]
    xc, yc = VARIABLES[xk]["column"], VARIABLES[yk]["column"]
    if xc in df.columns and yc in df.columns:
        fig = plot_scatter(df, xc, yc, x_key=xk, y_key=yk)
        st.plotly_chart(fig, use_container_width=True)
        sub = df[[xc, yc]].dropna()
        if sub.shape[0] > 2:
            r, p = stats.pearsonr(sub[xc], sub[yc])
            st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {sub.shape[0]:,}")
        st.caption("⚠️ 통계적으로는 '영향'이 아니라 '관계' 또는 '연관성'으로 해석합니다. "
                    "다른 조건을 통제한 관계는 회귀분석 페이지에서 확인하세요.")
