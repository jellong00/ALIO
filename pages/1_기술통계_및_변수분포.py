import streamlit as st
import pandas as pd

from utils.data_cleaner import get_full_panel, describe_var, percentile_rank
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_vars_by_category, CATEGORIES, get_label, get_unit, get_question
from utils.charts import plot_histogram, plot_boxplot, plot_rank_bar

st.set_page_config(page_title="기술통계 및 변수분포", layout="wide")
st.title("① 기술통계 및 변수분포")
st.caption("변수 하나를 골라 충분히 자세히 살펴보는 페이지입니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p1")

st.divider()
c1, c2 = st.columns(2)
with c1:
    category = st.selectbox("카테고리", CATEGORIES, key="p1_cat")
cat_vars = get_vars_by_category(category)
with c2:
    var_key = st.selectbox(
        "변수 선택", list(cat_vars.keys()),
        format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p1_var"
    )

col = VARIABLES[var_key]["column"]
if col not in df.columns:
    st.warning("선택한 변수가 데이터에 없습니다.")
    st.stop()

desc = describe_var(df, col)
if desc.get("N", 0) == 0:
    st.warning("선택한 조건에서 유효한 관측치가 없습니다.")
    st.stop()

st.markdown(f"### 📐 {get_label(var_key)} 기술통계")
r1 = st.columns(5)
r1[0].metric("N", f"{desc['N']:,}")
r1[1].metric("결측치 수", f"{desc['결측치수']:,}")
r1[2].metric("결측률", f"{desc['결측률']*100:.1f}%")
r1[3].metric("평균", f"{desc['평균']:,.1f}")
r1[4].metric("중앙값", f"{desc['중앙값']:,.1f}")
r2 = st.columns(5)
r2[0].metric("표준편차", f"{desc['표준편차']:,.1f}")
r2[1].metric("Q1", f"{desc['Q1']:,.1f}")
r2[2].metric("Q3", f"{desc['Q3']:,.1f}")
r2[3].metric("최소", f"{desc['최소']:,.1f}")
r2[4].metric("최대", f"{desc['최대']:,.1f}")

st.divider()
c3, c4 = st.columns(2)
with c3:
    nbins = st.slider("히스토그램 구간(bin) 수", 10, 60, 30, key="p1_nbins")
    st.plotly_chart(plot_histogram(df, col, var_key=var_key, nbins=nbins), use_container_width=True)
    with st.expander("📌 확인할 것 / 💡 포인트"):
        st.markdown("- 주황 실선은 평균, 초록 점선은 중앙값입니다.\n"
                     "- 두 선이 크게 떨어져 있으면 분포가 한쪽으로 치우쳐 있다는 뜻입니다.")
with c4:
    st.plotly_chart(plot_boxplot(df, col, var_key=var_key), use_container_width=True)
    with st.expander("⚠️ 주의할 점"):
        st.markdown("- 점 위에 마우스를 올리면 기관명·연도를 확인할 수 있습니다.\n"
                     "- 기관유형별 상자가 넓게 겹치면 유형 구분만으로는 차이를 설명하기 어렵습니다.")

st.divider()

# ---------------- Top / Bottom ----------------
st.markdown("### 🏆 Top / Bottom 기관")
c5, c6 = st.columns([1, 1])
with c5:
    rank_mode = st.radio("정렬", ["Top", "Bottom"], horizontal=True, key="p1_rankmode")
with c6:
    top_n = st.slider("표시 개수", 5, 20, 10, key="p1_topn")

ascending = (rank_mode == "Bottom")
overall_mean = pd.to_numeric(df[col], errors="coerce").mean()

rank_rows = []
ranked = df[["기관명", "기관유형", col]].dropna().sort_values(col, ascending=ascending).head(top_n)
for _, row in ranked.iterrows():
    val = row[col]
    same_type_vals = df[df["기관유형"] == row["기관유형"]][col]
    same_type_mean = pd.to_numeric(same_type_vals, errors="coerce").mean()
    pct = percentile_rank(df[col], val)
    rank_rows.append({
        "기관명": row["기관명"],
        "기관유형": row["기관유형"],
        get_label(var_key): round(val, 1),
        "전체 평균 대비": f"{val/overall_mean:,.2f}배" if overall_mean else "N/A",
        "동일유형 평균 대비": f"{val/same_type_mean*100:,.0f}%" if same_type_mean else "N/A",
        "전체 백분위": f"상위 {pct:.1f}%" if pct is not None else "N/A",
    })
st.dataframe(pd.DataFrame(rank_rows), use_container_width=True, hide_index=True)
st.plotly_chart(plot_rank_bar(df, col, var_key=var_key, top_n=top_n, ascending=ascending, show_multiple=True),
                 use_container_width=True)

st.divider()
st.markdown("### 🤔 생각해볼 질문")
st.info(get_question(var_key))
