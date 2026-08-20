import streamlit as st
from scipy import stats

from utils.page_common import render_domain_page
from utils.variables import VARIABLES
from utils.charts import plot_scatter

df, var_key, col = render_domain_page(
    domain="인사 결과",
    question="Q5. 기관의 특성과 운영 방식은 채용과 일·가정 양립 지표와 어떤 관계를 보이는가?",
    intro="신규채용, 육아휴직·출산휴가 등 일·가정 양립 지표를 살펴보고, 앞선 세 영역(기관특성·재정·조직운영)"
          "과의 관계를 프리셋으로 빠르게 탐색한다.",
)

if df is not None:
    st.divider()
    st.markdown("### 🔗 앞 단계 변수와 연결 (프리셋)")
    presets = {
        "임직원수 ↔ 신규채용자수": ("임직원수", "신규채용자수"),
        "임직원수 ↔ 신규채용률": ("임직원수", "신규채용률"),
        "총수입 ↔ 신규채용률": ("총수입", "신규채용률"),
        "정부지원의존도 ↔ 신규채용률": ("정부지원의존도", "신규채용률"),
        "직원평균보수 ↔ 신규채용률": ("직원평균보수", "신규채용률"),
        "여성직원비율 ↔ 여성신규채용비율": ("여성직원비율", "여성신규채용비율"),
        "1인당복리후생비 ↔ 여성육아휴직사용률": ("1인당복리후생비", "여성육아휴직사용률"),
        "여성직원비율 ↔ 여성육아휴직사용률": ("여성직원비율", "여성육아휴직사용률"),
        "여성직원비율 ↔ 남성육아휴직사용률": ("여성직원비율", "남성육아휴직사용률"),
        "직원평균보수 ↔ 남성육아휴직사용률": ("직원평균보수", "남성육아휴직사용률"),
    }
    choice = st.selectbox("프리셋 선택", list(presets.keys()), key="p5_preset")
    xk, yk = presets[choice]
    xc, yc = VARIABLES[xk]["column"], VARIABLES[yk]["column"]
    if xc in df.columns and yc in df.columns:
        fig = plot_scatter(df, xc, yc, x_key=xk, y_key=yk)
        st.plotly_chart(fig, use_container_width=True)
        sub = df[[xc, yc]].dropna()
        if sub.shape[0] > 2:
            r, p = stats.pearsonr(sub[xc], sub[yc])
            st.write(f"Pearson r = **{r:.3f}**, p = {p:.4f}, N = {sub.shape[0]:,}")
        st.caption("⚠️ 관찰된 상관관계이며 인과관계를 의미하지 않습니다. "
                    "특히 육아휴직 사용률은 제도 여건뿐 아니라 인력 구성(연령·성별 분포)의 영향도 받습니다.")
    else:
        st.warning("선택한 변수 조합이 데이터에 없습니다.")
