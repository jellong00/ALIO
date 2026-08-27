import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from utils.data_cleaner import get_full_panel
from utils.filters import sidebar_filters
from utils.variables import VARIABLES, get_label, get_unit, ORG_TYPE_COLORS
from utils.charts import plot_donut, plot_rank_bar
from utils.level_compare import dept_stats_table
from utils.page_header import render_intro, year_slice

st.set_page_config(page_title="수입지출 구조", layout="wide")
st.title("④ 수입·지출 구조")
render_intro(
    purpose="공공기관이 어떤 재원으로 수입을 구성하고, 총수입과 총지출 규모가 어떻게 나타나는지 살펴봅니다.",
    unit="선택 연도의 기관 (기본값: 최신연도)",
    methods="재정 규모 KPI · 수입구성 비교(기관유형/주무부처/개별기관) · 총수입 vs 총지출 산점도",
    caution="결측값은 '수입이 0'이 아니라 '미공시'일 수 있어 0으로 대체하지 않습니다. 구성비 합이 맞지 않는 기관은 별도 표시합니다.",
)

panel = get_full_panel()
df = sidebar_filters(panel, key_prefix="p4")

view, caption, mode = year_slice(df, key_prefix="p4")
st.caption(caption)

st.divider()
st.markdown("### 💰 재정 규모 KPI (평균)")
kpi_vars = ["총수입", "총지출", "사업수입", "정부지원수입"]
r1 = st.columns(4)
for c, vk in zip(r1, kpi_vars):
    col = VARIABLES[vk]["column"]
    if col in view.columns:
        v = pd.to_numeric(view[col], errors="coerce").mean()
        c.metric(get_label(vk), f"{v:,.0f} {get_unit(vk)}" if pd.notna(v) else "N/A")

st.divider()

# ---------------- 수입구조 (결측치 유지, 불일치 플래그) ----------------
comp = view[["기관명", "기관유형", "주무부처", "총수입", "정부지원수입", "사업수입"]].dropna(subset=["총수입"]).copy()
# 결측 유지: 0으로 채우지 않는다. 구성비 계산에는 결측이 아닌 값만 사용하고, 결측이 있으면 '기타'가 아니라 '불명'으로 취급한다.
comp["기타수입_원값"] = comp["총수입"] - comp["정부지원수입"].fillna(0) - comp["사업수입"].fillna(0)
comp["구성불일치"] = comp["기타수입_원값"] < 0
comp["정부지원_결측"] = comp["정부지원수입"].isna()
comp["사업수입_결측"] = comp["사업수입"].isna()

n_flag = int(comp["구성불일치"].sum())
if n_flag > 0:
    st.warning(f"⚠️ {n_flag}개 기관-연도에서 '정부지원수입 + 사업수입'이 총수입보다 커서 기타수입이 음수로 계산됩니다 "
                "(수입구성 불일치). 이 기관들은 아래 구성비 차트에서 제외했습니다. 원자료의 항목 정의·단위 차이일 수 있습니다.")

comp_valid = comp[~comp["구성불일치"]].copy()
comp_valid["기타수입"] = comp_valid["기타수입_원값"].clip(lower=0)

st.markdown("### 📊 수입 구성 비교 (100% 기준)")
level = st.radio("비교 수준", ["기관유형", "주무부처", "개별기관"], horizontal=True, key="p4_level")

if level == "기관유형":
    grp = comp_valid.groupby("기관유형")[["정부지원수입", "사업수입", "기타수입"]].mean()
    grp_pct = grp.div(grp.sum(axis=1), axis=0) * 100
    long = grp_pct.reset_index().melt(id_vars="기관유형", var_name="구성", value_name="비중(%)")
    fig = px.bar(long, x="기관유형", y="비중(%)", color="구성", barmode="stack",
                 color_discrete_map={"정부지원수입": "#E07B39", "사업수입": "#4C78A8", "기타수입": "#B0B0B0"})
    fig.update_layout(font=dict(size=16), height=480)
    st.plotly_chart(fig, use_container_width=True)

elif level == "주무부처":
    min_n = st.slider("최소 기관 수", 1, 10, 3, key="p4_deptminn")
    valid_depts = dept_stats_table(comp_valid, "총수입", min_n=min_n)["주무부처"].tolist()
    grp = comp_valid[comp_valid["주무부처"].isin(valid_depts)].groupby("주무부처")[["정부지원수입", "사업수입", "기타수입"]].mean()
    grp_pct = grp.div(grp.sum(axis=1), axis=0) * 100
    long = grp_pct.reset_index().melt(id_vars="주무부처", var_name="구성", value_name="비중(%)")
    fig = px.bar(long, x="주무부처", y="비중(%)", color="구성", barmode="stack",
                 color_discrete_map={"정부지원수입": "#E07B39", "사업수입": "#4C78A8", "기타수입": "#B0B0B0"})
    fig.update_layout(font=dict(size=16), height=520, xaxis_tickangle=-30)
    st.plotly_chart(fig, use_container_width=True)

else:
    orgs = sorted(comp_valid["기관명"].unique())
    sel_org = st.selectbox("기관 선택", orgs, key="p4_org")
    row = comp_valid[comp_valid["기관명"] == sel_org]
    if not row.empty:
        r = row.iloc[-1]
        st.plotly_chart(plot_donut(["정부지원수입", "사업수입", "기타수입"],
                                     [r["정부지원수입"], r["사업수입"], r["기타수입"]],
                                     title=f"{sel_org} 수입 구성"), use_container_width=True)
    else:
        st.info("선택한 기관은 수입구성 불일치로 제외되었거나 데이터가 없습니다.")

st.markdown(
    "**💡 생각해볼 질문**: 정부지원수입의 '금액'이 큰 기관과 총수입 대비 '비중'이 높은 기관은 같은 기관일까요? "
    "(정부지원의존도는 ⑧⑨번 페이지의 관계분석에서 더 다룹니다.)"
)

st.divider()

# ---------------- 규모와 의존도의 구분 ----------------
st.markdown("### 🧭 규모와 의존도의 구분 — 정부지원 '금액'이 큰 기관 vs '비중'이 높은 기관")
st.caption("💡 정부지원수입의 절대 금액이 큰 기관과, 총수입 대비 정부지원 비중(정부지원의존도)이 높은 기관은 서로 다를 수 있습니다. "
            "아래 사분면으로 두 기관 집단이 실제로 어떻게 갈리는지 확인합니다.")
dep_col = VARIABLES["정부지원의존도"]["column"] if "정부지원의존도" in VARIABLES else None
if dep_col and dep_col in view.columns and "총수입" in view.columns:
    base_cols = ["기관명", "기관유형", "주무부처", "총수입", dep_col]
    has_gov_income_col = "정부지원수입" in view.columns
    if has_gov_income_col:
        base_cols.append("정부지원수입")
    sub_dep = view[base_cols].dropna(subset=["기관명", "기관유형", "주무부처", "총수입", dep_col])

    exclude_zero = st.checkbox("정부지원수입이 없는(0원) 기관 제외", value=True, key="p4_excl_zero_gov")
    if exclude_zero and not sub_dep.empty:
        n_before = sub_dep.shape[0]
        if has_gov_income_col:
            sub_dep = sub_dep[pd.to_numeric(sub_dep["정부지원수입"], errors="coerce") > 0]
        else:
            sub_dep = sub_dep[sub_dep[dep_col] > 0]
        n_excluded = n_before - sub_dep.shape[0]
        if n_excluded > 0:
            st.caption(f"정부지원수입이 0원(또는 정부지원의존도 0%)인 기관 {n_excluded:,}개를 제외했습니다.")

    if not sub_dep.empty:
        threshold_mode = st.radio("사분면 기준선", ["중앙값 기준", "직접 입력"], horizontal=True, key="p4_qmode")
        if threshold_mode == "중앙값 기준":
            x_thresh = float(sub_dep["총수입"].median())
            y_thresh = float(sub_dep[dep_col].median())
        else:
            qc1, qc2 = st.columns(2)
            with qc1:
                x_thresh = st.number_input("총수입 기준값 (백만원)", value=float(sub_dep["총수입"].median()), key="p4_xthresh")
            with qc2:
                y_thresh = st.number_input("정부지원의존도 기준값 (%)", value=float(sub_dep[dep_col].median()), key="p4_ythresh")

        fig_dep = px.scatter(sub_dep, x="총수입", y=dep_col, color="기관유형", color_discrete_map=ORG_TYPE_COLORS,
                               hover_name="기관명", hover_data=["주무부처"],
                               labels={"총수입": "총수입 (백만원)", dep_col: "정부지원의존도 (%)"})
        fig_dep.add_vline(x=x_thresh, line_dash="dash", line_color="gray")
        fig_dep.add_hline(y=y_thresh, line_dash="dash", line_color="gray")
        fig_dep.update_layout(font=dict(size=16), height=520)

        xc1, xc2 = st.columns([1, 2])
        with xc1:
            zoom_x = st.checkbox("x축 범위 좁혀서 보기 (극단값은 그대로 유지, 축 범위만 조정)", value=True, key="p4_zoomx")
        if zoom_x:
            with xc2:
                x_pct = st.slider("x축 상한 기준 (총수입 백분위수)", 70, 99, 95, key="p4_xpct")
            x_hi = float(np.percentile(sub_dep["총수입"], x_pct))
            n_over = int((sub_dep["총수입"] > x_hi).sum())
            fig_dep.update_xaxes(range=[sub_dep["총수입"].min() * 1.0, x_hi])
            st.caption(f"💡 x축 범위를 상위 {100 - x_pct}% 지점({x_hi:,.0f} 백만원)까지만 표시합니다. "
                        f"이보다 큰 기관 {n_over:,}개는 화면 오른쪽 밖에 위치하지만, 데이터·기준선·사분면 기관 수 계산에서는 제외되지 않습니다.")

        st.plotly_chart(fig_dep, use_container_width=True)
        st.caption("오른쪽 위: 총수입도 크고 정부지원 비중도 높은 기관 · 오른쪽 아래: 총수입은 크지만 정부지원 비중은 낮은 기관 · "
                    "왼쪽 위: 총수입은 작지만 정부지원 비중이 높은 기관 · 왼쪽 아래: 둘 다 낮은 기관.")

        q_counts = pd.DataFrame([
            {"구분": "총수입↑ · 의존도↑", "기관 수": int(((sub_dep["총수입"] >= x_thresh) & (sub_dep[dep_col] >= y_thresh)).sum())},
            {"구분": "총수입↑ · 의존도↓", "기관 수": int(((sub_dep["총수입"] >= x_thresh) & (sub_dep[dep_col] < y_thresh)).sum())},
            {"구분": "총수입↓ · 의존도↑", "기관 수": int(((sub_dep["총수입"] < x_thresh) & (sub_dep[dep_col] >= y_thresh)).sum())},
            {"구분": "총수입↓ · 의존도↓", "기관 수": int(((sub_dep["총수입"] < x_thresh) & (sub_dep[dep_col] < y_thresh)).sum())},
        ])
        st.dataframe(q_counts, use_container_width=True, hide_index=True)
    else:
        st.info("정부지원의존도와 총수입을 함께 가진 관측치가 없습니다.")
else:
    st.info("정부지원의존도 변수가 데이터에 없어 이 분석을 표시할 수 없습니다.")

st.divider()

# ---------------- 총수입 vs 총지출 ----------------
st.markdown("### ⚖️ 총수입 vs 총지출")
sub2 = view[["기관명", "기관유형", "주무부처", "총수입", "총지출"]].dropna()
fig2 = px.scatter(sub2, x="총수입", y="총지출", color="기관유형", color_discrete_map=ORG_TYPE_COLORS,
                    hover_name="기관명", hover_data=["주무부처"],
                    labels={"총수입": "총수입 (백만원)", "총지출": "총지출 (백만원)"})
lo = min(sub2["총수입"].min(), sub2["총지출"].min())
hi = max(sub2["총수입"].max(), sub2["총지출"].max())
fig2.add_shape(type="line", x0=lo, y0=lo, x1=hi, y1=hi, line=dict(color="gray", dash="dash"))
fig2.update_layout(font=dict(size=16), height=520)
st.plotly_chart(fig2, use_container_width=True)
st.caption("점선(45도 기준선)보다 위에 있으면 총지출이 총수입보다 큰 기관입니다.")

st.markdown("### 수입-지출 차이 상위/하위")
st.caption("※ 총수입-총지출 차이가 회계상 당기순이익이나 사업성과를 의미하는지는 이 자료만으로 확인할 수 없어 '흑자/적자' 대신 '수입-지출 차이'로 표기합니다.")
rank_mode = st.radio("정렬 기준", ["차이 상위 10 (수입>지출)", "차이 하위 10 (지출>수입)"], horizontal=True, key="p4_rankmode")
st.plotly_chart(
    plot_rank_bar(view, "수입지출차이", var_key="수입지출차이", top_n=10,
                   ascending=(rank_mode.startswith("차이 하위"))),
    use_container_width=True,
)

st.divider()

# ---------------- 이어보기 ----------------
st.markdown("### ➡️ 이어보기")
st.markdown(
    "- 총수입이 큰 기관은 직원 평균보수도 높은지 궁금하다면 → **⑧ 두 변수 관계분석**\n"
    "- 정부지원의존도와 신규채용률의 관계가 궁금하다면 → **⑧ 두 변수 관계분석**"
)
