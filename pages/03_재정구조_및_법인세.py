import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit, ORG_TYPE_COLORS
from utils.charts import plot_donut, plot_rank_bar, plot_scatter, plot_boxplot
from utils.level_compare import dept_stats_table, four_level_values

st.set_page_config(page_title="재정구조 및 법인세", layout="wide")
st.title("③ 재정구조 및 법인세")
st.caption("공공기관의 수입·지출 구조와 법인세 흐름을 전체·기관유형·주무부처·개별기관 수준에서 살펴보는 페이지입니다.")

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p3")

st.divider()
st.markdown("### 💰 재정 KPI (전체 평균)")
kpi_vars = ["총수입", "총지출", "사업수입", "정부지원수입"]
r1 = st.columns(4)
for c, vk in zip(r1, kpi_vars):
    col = VARIABLES[vk]["column"]
    if col in df.columns:
        c.metric(get_label(vk), f"{pd.to_numeric(df[col], errors='coerce').mean():,.0f} {get_unit(vk)}")
kpi_vars2 = ["정부지원의존도", "수입지출차이", "과세표준", "법인세결정세액"]
r2 = st.columns(4)
for c, vk in zip(r2, kpi_vars2):
    col = VARIABLES[vk]["column"]
    if col in df.columns:
        v = pd.to_numeric(df[col], errors="coerce").mean()
        unit = "%" if VARIABLES[vk]["percent"] else get_unit(vk)
        c.metric(get_label(vk), f"{v:,.1f} {unit}")

st.divider()

# ---------------- 수입구조 ----------------
comp = df[["기관명", "기관유형", "주무부처", "연도", "총수입", "정부지원수입", "사업수입"]].dropna(subset=["총수입"]).copy()
comp["정부지원수입"] = comp["정부지원수입"].fillna(0)
comp["사업수입"] = comp["사업수입"].fillna(0)
comp["기타수입"] = (comp["총수입"] - comp["정부지원수입"] - comp["사업수입"]).clip(lower=0)

st.markdown("### 📊 수입 구조 비교 (100% 기준)")
level = st.radio("비교 수준", ["기관유형", "주무부처", "개별기관"], horizontal=True, key="p3_level")

if level == "기관유형":
    grp = comp.groupby("기관유형")[["정부지원수입", "사업수입", "기타수입"]].mean()
    grp_pct = grp.div(grp.sum(axis=1), axis=0) * 100
    long = grp_pct.reset_index().melt(id_vars="기관유형", var_name="구성", value_name="비중(%)")
    fig = px.bar(long, x="기관유형", y="비중(%)", color="구성", barmode="stack",
                 color_discrete_map={"정부지원수입": "#E07B39", "사업수입": "#4C78A8", "기타수입": "#B0B0B0"})
    fig.update_layout(font=dict(size=16), height=480)
    st.plotly_chart(fig, use_container_width=True)

elif level == "주무부처":
    min_n = st.slider("최소 기관 수", 1, 10, 3, key="p3_deptminn")
    valid_depts = dept_stats_table(comp, "총수입", min_n=min_n)["주무부처"].tolist()
    grp = comp[comp["주무부처"].isin(valid_depts)].groupby("주무부처")[["정부지원수입", "사업수입", "기타수입"]].mean()
    grp_pct = grp.div(grp.sum(axis=1), axis=0) * 100
    long = grp_pct.reset_index().melt(id_vars="주무부처", var_name="구성", value_name="비중(%)")
    fig = px.bar(long, x="주무부처", y="비중(%)", color="구성", barmode="stack",
                 color_discrete_map={"정부지원수입": "#E07B39", "사업수입": "#4C78A8", "기타수입": "#B0B0B0"})
    fig.update_layout(font=dict(size=16), height=520, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

else:
    c1, c2 = st.columns(2)
    with c1:
        orgs = sorted(comp["기관명"].unique())
        sel_org = st.selectbox("기관 선택", orgs, key="p3_org")
    sub = comp[comp["기관명"] == sel_org]
    with c2:
        yrs = sorted(sub["연도"].unique(), reverse=True)
        sel_year = st.selectbox("연도 선택", yrs, key="p3_year") if yrs else None

    if sel_year is not None:
        row = sub[sub["연도"] == sel_year]
        if not row.empty:
            r = row.iloc[0]
            org_type = r["기관유형"]
            org_dept = r["주무부처"]
            type_avg = comp[comp["기관유형"] == org_type][["정부지원수입", "사업수입", "기타수입"]].mean()
            dept_avg = comp[comp["주무부처"] == org_dept][["정부지원수입", "사업수입", "기타수입"]].mean()

            d1, d2, d3 = st.columns(3)
            with d1:
                st.plotly_chart(plot_donut(["정부지원수입", "사업수입", "기타수입"],
                                             [r["정부지원수입"], r["사업수입"], r["기타수입"]],
                                             title=f"{sel_org} ({sel_year}년)"), use_container_width=True)
            with d2:
                st.plotly_chart(plot_donut(["정부지원수입", "사업수입", "기타수입"],
                                             [type_avg["정부지원수입"], type_avg["사업수입"], type_avg["기타수입"]],
                                             title=f"동일유형({org_type}) 평균"), use_container_width=True)
            with d3:
                st.plotly_chart(plot_donut(["정부지원수입", "사업수입", "기타수입"],
                                             [dept_avg["정부지원수입"], dept_avg["사업수입"], dept_avg["기타수입"]],
                                             title=f"동일부처({org_dept}) 평균"), use_container_width=True)

            total_r = r["정부지원수입"] + r["사업수입"] + r["기타수입"]
            total_t = type_avg.sum()
            total_d = dept_avg.sum()
            lines = []
            for label, total, vals in [("선택기관", total_r, r), ("동일유형 평균", total_t, type_avg), ("동일부처 평균", total_d, dept_avg)]:
                if total:
                    lines.append(f"**{label}**: 정부지원 {vals['정부지원수입']/total*100:.0f}% · "
                                  f"사업수입 {vals['사업수입']/total*100:.0f}% · 기타 {vals['기타수입']/total*100:.0f}%")
            st.markdown("  \n".join(lines))

st.divider()

# ---------------- 총수입 vs 총지출 ----------------
st.markdown("### ⚖️ 총수입 vs 총지출")
sub2 = df[["기관명", "기관유형", "주무부처", "연도", "총수입", "총지출"]].dropna()
fig2 = px.scatter(sub2, x="총수입", y="총지출", color="기관유형", color_discrete_map=ORG_TYPE_COLORS,
                    hover_name="기관명", hover_data=["주무부처", "연도"],
                    labels={"총수입": "총수입 (백만원)", "총지출": "총지출 (백만원)"})
lo = min(sub2["총수입"].min(), sub2["총지출"].min())
hi = max(sub2["총수입"].max(), sub2["총지출"].max())
fig2.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi, line=dict(color="gray", dash="dash"))
fig2.update_layout(font=dict(size=16), height=520)
st.plotly_chart(fig2, use_container_width=True)
st.caption("점선(45도 기준선)보다 위에 있으면 지출이 수입보다 큰 기관(수지 마이너스)입니다.")

st.markdown("### 흑자 / 적자 순위")
rank_mode = st.radio("정렬 기준", ["흑자 상위 10", "적자 상위 10"], horizontal=True, key="p3_rankmode")
st.plotly_chart(
    plot_rank_bar(df, "수입지출차이", var_key="수입지출차이", top_n=10,
                   ascending=(rank_mode == "적자 상위 10")),
    use_container_width=True,
)

st.divider()

# ---------------- 법인세 구조 ----------------
st.markdown("### 🧾 법인세 흐름: 과세표준 → 산출세액 → 세액공제 → 가산세 → 결정세액")
tax_stages = ["과세표준", "법인세산출세액", "세액공제", "가산세", "법인세결정세액"]
tax_stages = [t for t in tax_stages if t in df.columns]
if tax_stages:
    stage_means = df[tax_stages].apply(pd.to_numeric, errors="coerce").mean()
    fig3 = go.Figure(go.Bar(x=stage_means.index, y=stage_means.values, marker_color="#4C78A8",
                              text=stage_means.round(0), textposition="outside"))
    fig3.update_layout(font=dict(size=16), height=460, yaxis_title="금액(천원, 전체 평균)")
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("### 법인세 지표 분포")
tax_var = st.selectbox("변수 선택", ["과세표준", "법인세결정세액", "실효법인세율"],
                         format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p3_taxdist")
tax_col = VARIABLES[tax_var]["column"]
tax_level = st.radio("비교 수준", ["기관유형", "주무부처"], horizontal=True, key="p3_taxlevel")
if tax_col in df.columns:
    if tax_level == "기관유형":
        st.plotly_chart(plot_boxplot(df, tax_col, var_key=tax_var), use_container_width=True)
    else:
        dstats = dept_stats_table(df, tax_col, min_n=3).round(1)
        st.dataframe(dstats, use_container_width=True, hide_index=True)
        fig_d = px.bar(dstats.sort_values("평균", ascending=True), x="평균", y="주무부처", orientation="h",
                        labels={"평균": f"{get_label(tax_var)} 평균"})
        fig_d.update_layout(font=dict(size=14), height=max(420, 26 * len(dstats)))
        st.plotly_chart(fig_d, use_container_width=True)

st.markdown("#### 선택기관 법인세 4중 비교")
tax_orgs = sorted(df["기관명"].unique())
sel_tax_org = st.selectbox("기관 선택", ["(선택 안 함)"] + tax_orgs, key="p3_taxorg")
if sel_tax_org != "(선택 안 함)":
    tc1, tc2 = st.columns(2)
    for c, vk in zip([tc1, tc2], ["과세표준", "법인세결정세액"]):
        vals = four_level_values(df, VARIABLES[vk]["column"], sel_tax_org)
        with c:
            if vals:
                st.markdown(f"**{get_label(vk)}**")
                st.write(f"- 기관값: {vals['기관값']:,.0f}")
                st.write(f"- 동일유형 평균: {vals['동일유형평균']:,.0f}" if pd.notna(vals['동일유형평균']) else "- 동일유형 평균: N/A")
                st.write(f"- 동일부처 평균: {vals['동일부처평균']:,.0f}" if pd.notna(vals['동일부처평균']) else "- 동일부처 평균: N/A")
            else:
                st.info("데이터가 없습니다.")

st.divider()

# ---------------- 법인세 관계 탐색 ----------------
st.markdown("### 🔗 법인세 관계 탐색")
x_options = ["과세표준", "총수입", "사업수입", "정부지원의존도", "임직원수"]
x_key = st.selectbox("X 변수", x_options, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p3_taxx")
x_col = VARIABLES[x_key]["column"]
y_col = VARIABLES["법인세결정세액"]["column"]

if x_col in df.columns and y_col in df.columns:
    fig4 = plot_scatter(df, x_col, y_col, x_key=x_key, y_key="법인세결정세액", trendline="ols")
    st.plotly_chart(fig4, use_container_width=True)
    sub3 = df[[x_col, y_col]].dropna()
    if sub3.shape[0] > 2:
        r, p = stats.pearsonr(sub3[x_col], sub3[y_col])
        slope, intercept, r_value, p_value, se = stats.linregress(sub3[x_col], sub3[y_col])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Pearson r", f"{r:.3f}")
        m2.metric("기울기 b", f"{slope:,.4f}")
        m3.metric("R²", f"{r_value**2:.3f}")
        m4.metric("N", f"{sub3.shape[0]:,}")
    st.caption("⚠️ 법인세는 세법상 규정(공제·감면 등)의 영향을 받으므로 단순 상관관계로 인과를 단정할 수 없습니다.")
