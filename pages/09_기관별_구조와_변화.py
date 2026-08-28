import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats

from utils.data_cleaner import get_full_panel
from utils.variables import VARIABLES, get_label, get_unit
from utils.charts import plot_donut
from utils.page_header import render_intro

st.set_page_config(page_title="기관별 구조와 변화", layout="wide")
st.title("⑨ 기관별 구조와 변화")
render_intro(
    purpose="선택기관의 재정·인력·보수·법인세 지표가 어떤 내부 구조를 가지며, 시간에 따른 변화가 어느 구성항목에서 나타났는지 확인합니다.",
    unit="선택기관의 기관-연도 자료 (다른 기관과의 평균 비교나 순위는 다루지 않습니다 — 상대적 위치는 ⑧ 기관 프로필을 참고하세요)",
    methods="[재정 구조와 변화] [인력과 채용 흐름] [보수와 복리후생 구조] [법인세와 기관 내 변동성] — 탭으로 분리",
    caution="이 페이지의 설명은 관측된 구성항목의 변화를 기술할 뿐, 변화의 원인을 단정하지 않습니다.",
)


def col_of(key: str) -> str:
    """Return the dataframe column for a VARIABLES key, falling back to the key itself."""
    if key in VARIABLES:
        return VARIABLES[key]["column"]
    return key


panel = get_full_panel()

st.divider()
st.markdown("### 🔍 기관 검색")
search_mode = st.radio("검색 방식", ["기관명 직접 검색", "기관유형 → 주무부처 → 기관명"], horizontal=True, key="p9s_searchmode")
if search_mode == "기관명 직접 검색":
    all_orgs = sorted(panel["기관명"].unique())
    org_name = st.selectbox("기관명 검색", all_orgs, key="p9s_orgsearch")
else:
    c1, c2, c3 = st.columns(3)
    with c1:
        org_type = st.selectbox("기관유형", sorted(panel["기관유형"].unique()), key="p9s_type")
    sub1 = panel[panel["기관유형"] == org_type]
    with c2:
        dept = st.selectbox("주무부처", sorted(sub1["주무부처"].unique()), key="p9s_dept")
    sub2 = sub1[sub1["주무부처"] == dept]
    with c3:
        org_name = st.selectbox("기관명", sorted(sub2["기관명"].unique()), key="p9s_org")

org_df = panel[panel["기관명"] == org_name].sort_values("연도").reset_index(drop=True)
if org_df.empty:
    st.warning("선택한 기관의 데이터가 없습니다.")
    st.stop()

years = sorted(org_df["연도"].unique())
latest_year = years[-1]
snap = org_df[org_df["연도"] == latest_year].iloc[0]
st.caption(f"**{org_name}** ({snap['기관유형']} · {snap['주무부처']}) — 관측 연도: {years[0]}~{years[-1]} (N = {len(years)}개 연도)")
if len(years) < 2:
    st.warning("⚠️ 관측 연도가 1개뿐이라 변화·추이 분석의 일부는 표시되지 않을 수 있습니다.")

st.divider()

tab_fin, tab_hr, tab_pay, tab_tax = st.tabs(
    ["💰 재정 구조와 변화", "🧑‍💼 인력과 채용 흐름", "💵 보수와 복리후생 구조", "🏛️ 법인세와 기관 내 변동성"]
)

# =========================================================================
# TAB 1: 재정 구조와 변화
# =========================================================================
with tab_fin:
    has_income_parts = all(c in org_df.columns for c in ["총수입", "정부지원수입", "사업수입"])
    if has_income_parts:
        inc = org_df[["연도", "총수입", "정부지원수입", "사업수입"]].copy()
        inc["기타수입_원값"] = inc["총수입"] - inc["정부지원수입"].fillna(0) - inc["사업수입"].fillna(0)
        inc["구성불일치"] = inc["기타수입_원값"] < 0
        inc["기타수입"] = inc["기타수입_원값"].clip(lower=0)

        st.markdown(f"### 🍩 최근연도({latest_year}년) 수입 구성")
        latest_inc = inc[inc["연도"] == latest_year]
        if not latest_inc.empty and not latest_inc["구성불일치"].iloc[0]:
            r = latest_inc.iloc[0]
            st.plotly_chart(
                plot_donut(["정부지원수입", "사업수입", "기타수입"],
                            [r["정부지원수입"], r["사업수입"], r["기타수입"]],
                            title=f"{org_name} 수입 구성 ({latest_year}년)"),
                use_container_width=True,
            )
        else:
            st.info("최근연도 수입구성이 불일치(정부지원수입+사업수입 > 총수입)하거나 결측이 있어 도넛 차트를 표시할 수 없습니다.")

        st.divider()
        st.markdown("### 📊 연도별 수입 구성 (금액)")
        valid_inc = inc[~inc["구성불일치"]]
        if not valid_inc.empty:
            long_amt = valid_inc.melt(id_vars="연도", value_vars=["정부지원수입", "사업수입", "기타수입"],
                                        var_name="구성", value_name="금액")
            fig_amt = px.bar(long_amt, x="연도", y="금액", color="구성", barmode="stack",
                               color_discrete_map={"정부지원수입": "#E07B39", "사업수입": "#4C78A8", "기타수입": "#B0B0B0"})
            fig_amt.update_layout(font=dict(size=15), height=440)
            st.plotly_chart(fig_amt, use_container_width=True)

            st.markdown("### 📈 연도별 수입 구성비 (100% 기준)")
            pct_df = valid_inc.set_index("연도")[["정부지원수입", "사업수입", "기타수입"]]
            pct_df = pct_df.div(pct_df.sum(axis=1), axis=0) * 100
            long_pct = pct_df.reset_index().melt(id_vars="연도", var_name="구성", value_name="비중(%)")
            fig_pct = px.bar(long_pct, x="연도", y="비중(%)", color="구성", barmode="stack",
                               color_discrete_map={"정부지원수입": "#E07B39", "사업수입": "#4C78A8", "기타수입": "#B0B0B0"})
            fig_pct.update_layout(font=dict(size=15), height=440)
            st.plotly_chart(fig_pct, use_container_width=True)

            n_incomplete = inc["구성불일치"].sum()
            if n_incomplete:
                st.caption(f"⚠️ {int(n_incomplete)}개 연도는 수입구성이 불일치하여 위 두 차트에서 제외했습니다.")
        else:
            st.info("수입구성을 계산할 수 있는 연도가 없습니다.")

        st.divider()
        st.markdown("### 🌊 두 연도 간 총수입 증감분해")
        if len(years) >= 2:
            wc1, wc2 = st.columns(2)
            with wc1:
                w_from = st.selectbox("기준 연도(이전)", years[:-1], index=len(years) - 2, key="p9_wfrom")
            with wc2:
                w_to_options = [y for y in years if y > w_from]
                w_to = st.selectbox("비교 연도(이후)", w_to_options, index=0, key="p9_wto")

            row_from = inc[inc["연도"] == w_from]
            row_to = inc[inc["연도"] == w_to]
            can_decompose = (
                not row_from.empty and not row_to.empty
                and not row_from["구성불일치"].iloc[0] and not row_to["구성불일치"].iloc[0]
                and row_from[["정부지원수입", "사업수입", "총수입"]].notna().all(axis=1).iloc[0]
                and row_to[["정부지원수입", "사업수입", "총수입"]].notna().all(axis=1).iloc[0]
            )
            if can_decompose:
                rf, rt = row_from.iloc[0], row_to.iloc[0]
                d_gov = rt["정부지원수입"] - rf["정부지원수입"]
                d_biz = rt["사업수입"] - rf["사업수입"]
                d_etc = rt["기타수입"] - rf["기타수입"]
                total_change = rt["총수입"] - rf["총수입"]
                # 구성요소 변화의 합이 총수입 변화와 일치하는 경우에만 표시
                if abs((d_gov + d_biz + d_etc) - total_change) < 1e-6 * max(abs(total_change), 1):
                    fig_wf = go.Figure(go.Waterfall(
                        orientation="v",
                        measure=["absolute", "relative", "relative", "relative", "total"],
                        x=[f"{w_from}년 총수입", "정부지원수입 변화", "사업수입 변화", "기타수입 변화", f"{w_to}년 총수입"],
                        y=[rf["총수입"], d_gov, d_biz, d_etc, rt["총수입"]],
                        connector={"line": {"color": "gray"}},
                    ))
                    fig_wf.update_layout(font=dict(size=15), height=460, yaxis_title="백만원")
                    st.plotly_chart(fig_wf, use_container_width=True)
                    st.caption("💡 각 구성요소의 변화가 총수입 변화에 얼마나 기여했는지 보여줍니다 (구성요소 변화의 합 = 총수입 변화인 경우에만 표시됩니다).")
                else:
                    st.info("구성요소 변화의 합이 총수입 변화와 일치하지 않아 증감분해를 표시하지 않습니다.")
            else:
                st.info("선택한 두 연도 중 하나 이상에서 수입구성이 불일치하거나 결측이 있어 증감분해를 표시할 수 없습니다.")
        else:
            st.info("증감분해를 계산하려면 관측 연도가 2개 이상이어야 합니다.")
    else:
        st.info("정부지원수입·사업수입 변수가 데이터에 없어 수입구성 분석을 표시할 수 없습니다.")

    st.divider()
    st.markdown("### 📉 총수입 · 총지출 · 수입지출차이 시계열")
    fin_cols_present = [c for c in ["총수입", "총지출", "수입지출차이"] if c in org_df.columns]
    if fin_cols_present:
        fig_fin = go.Figure()
        colors = {"총수입": "#4C78A8", "총지출": "#E07B39", "수입지출차이": "#2CA02C"}
        for c in fin_cols_present:
            d = org_df[["연도", c]].dropna()
            fig_fin.add_trace(go.Scatter(x=d["연도"], y=d[c], mode="lines+markers", name=c,
                                           line=dict(width=3, color=colors.get(c))))
        fig_fin.update_layout(font=dict(size=15), height=440, yaxis_title="백만원")
        st.plotly_chart(fig_fin, use_container_width=True)
    else:
        st.info("총수입·총지출 관련 변수가 없습니다.")

# =========================================================================
# TAB 2: 인력과 채용 흐름
# =========================================================================
with tab_hr:
    st.markdown("### 👥 임직원 수 · 신규채용자 수 · 신규채용률 시계열")
    hr_keys = ["임직원수", "신규채용자수", "신규채용률"]
    hr_present = [(k, col_of(k)) for k in hr_keys if col_of(k) in org_df.columns]
    if hr_present:
        fig_hr = make_subplots(specs=[[{"secondary_y": True}]])
        colors_hr = ["#4C78A8", "#E07B39", "#2CA02C"]
        for i, (k, c) in enumerate(hr_present):
            d = org_df[["연도", c]].dropna()
            secondary = VARIABLES.get(k, {}).get("percent", False)
            fig_hr.add_trace(go.Scatter(x=d["연도"], y=d[c], mode="lines+markers", name=get_label(k),
                                          line=dict(width=3, color=colors_hr[i % len(colors_hr)])),
                               secondary_y=secondary)
        fig_hr.update_layout(font=dict(size=15), height=460)
        fig_hr.update_yaxes(title_text="인원(명)", secondary_y=False)
        fig_hr.update_yaxes(title_text="비율(%)", secondary_y=True)
        st.plotly_chart(fig_hr, use_container_width=True)
    else:
        st.info("인력·채용 관련 변수가 없습니다.")

    st.divider()
    st.markdown("### 👩 여성직원비율 · 여성신규채용비율 시계열")
    w_keys = ["여성직원비율", "여성신규채용비율"]
    w_present = [(k, col_of(k)) for k in w_keys if col_of(k) in org_df.columns]
    if w_present:
        fig_w = go.Figure()
        colors_w = ["#9467BD", "#D62728"]
        for i, (k, c) in enumerate(w_present):
            d = org_df[["연도", c]].dropna()
            fig_w.add_trace(go.Scatter(x=d["연도"], y=d[c], mode="lines+markers", name=get_label(k),
                                         line=dict(width=3, color=colors_w[i % len(colors_w)])))
        fig_w.update_layout(font=dict(size=15), height=420, yaxis_title="비율(%)")
        st.plotly_chart(fig_w, use_container_width=True)
    else:
        st.info("여성 인력 관련 변수가 없습니다.")

    st.divider()
    st.markdown("### 📋 두 시점 간 주요 인력지표 변화")
    if len(years) >= 2:
        hc1, hc2 = st.columns(2)
        with hc1:
            h_from = st.selectbox("기준 연도", years[:-1], index=len(years) - 2, key="p9_hfrom")
        with hc2:
            h_to = st.selectbox("비교 연도", [y for y in years if y > h_from], index=0, key="p9_hto")
        table_keys = ["임직원수", "신규채용자수", "신규채용률", "여성직원비율", "여성신규채용비율",
                      "여성육아휴직사용자수", "남성육아휴직사용자수"]
        rows = []
        for k in table_keys:
            c = col_of(k)
            if c not in org_df.columns:
                continue
            v_from = org_df.loc[org_df["연도"] == h_from, c]
            v_to = org_df.loc[org_df["연도"] == h_to, c]
            v_from = v_from.iloc[0] if not v_from.empty else None
            v_to = v_to.iloc[0] if not v_to.empty else None
            diff = (v_to - v_from) if (v_from is not None and v_to is not None and pd.notna(v_from) and pd.notna(v_to)) else None
            rows.append({"지표": get_label(k), f"{h_from}년": v_from, f"{h_to}년": v_to, "변화": diff})
        if rows:
            st.dataframe(pd.DataFrame(rows).round(1), use_container_width=True, hide_index=True)
    else:
        st.info("비교하려면 관측 연도가 2개 이상이어야 합니다.")

# =========================================================================
# TAB 3: 보수와 복리후생 구조
# =========================================================================
with tab_pay:
    st.markdown(f"### 🥧 최근연도({latest_year}년) 보수 구성비 (기본급·수당·성과급)")
    comp_vars = ["기본급", "고정수당", "실적수당", "성과상여금", "경영평가성과급"]
    comp_cols = [c for c in comp_vars if c in org_df.columns]
    if comp_cols:
        latest_row = org_df[org_df["연도"] == latest_year]
        if not latest_row.empty:
            vals = latest_row.iloc[0][comp_cols]
            if vals.notna().any() and vals.sum() > 0:
                st.plotly_chart(plot_donut(comp_cols, vals.fillna(0).tolist(),
                                             title=f"{org_name} 보수 구성 ({latest_year}년)"),
                                  use_container_width=True)
            else:
                st.info("최근연도 보수 구성요소 데이터가 없습니다.")
    else:
        st.info("기본급·수당·성과급 변수가 없습니다.")

    st.divider()
    st.markdown("### 💰 직원평균보수 · 신입사원초임 시계열")
    pay_keys = ["직원평균보수", "신입사원초임"]
    pay_present = [(k, col_of(k)) for k in pay_keys if col_of(k) in org_df.columns]
    if pay_present:
        fig_pay = go.Figure()
        colors_pay = ["#4C78A8", "#E07B39"]
        for i, (k, c) in enumerate(pay_present):
            d = org_df[["연도", c]].dropna()
            fig_pay.add_trace(go.Scatter(x=d["연도"], y=d[c], mode="lines+markers", name=get_label(k),
                                           line=dict(width=3, color=colors_pay[i % len(colors_pay)])))
        fig_pay.update_layout(font=dict(size=15), height=420, yaxis_title="천원")
        st.plotly_chart(fig_pay, use_container_width=True)

    st.markdown("### 📆 평균근속연수 시계열")
    tenure_col = col_of("평균근속연수")
    if tenure_col in org_df.columns:
        d = org_df[["연도", tenure_col]].dropna()
        fig_ten = px.line(d, x="연도", y=tenure_col, markers=True, labels={tenure_col: "평균근속연수(년)"})
        fig_ten.update_layout(font=dict(size=15), height=380)
        st.plotly_chart(fig_ten, use_container_width=True)
    else:
        st.info("평균근속연수 변수가 없습니다.")

    st.divider()
    st.markdown("### 🎁 복리후생비 총액 · 1인당 복리후생비 · 임직원 수 동시 추이")
    ben_total_col = col_of("복리후생비")
    ben_percap_col = col_of("1인당복리후생비")
    emp_col = col_of("임직원수")
    if ben_total_col in org_df.columns and ben_percap_col in org_df.columns:
        fig_ben = make_subplots(specs=[[{"secondary_y": True}]])
        d1 = org_df[["연도", ben_total_col]].dropna()
        d2 = org_df[["연도", ben_percap_col]].dropna()
        fig_ben.add_trace(go.Scatter(x=d1["연도"], y=d1[ben_total_col], mode="lines+markers",
                                       name="복리후생비 총액", line=dict(width=3, color="#4C78A8")), secondary_y=False)
        fig_ben.add_trace(go.Scatter(x=d2["연도"], y=d2[ben_percap_col], mode="lines+markers",
                                       name="1인당 복리후생비", line=dict(width=3, color="#E07B39", dash="dash")), secondary_y=True)
        if emp_col in org_df.columns:
            d3 = org_df[["연도", emp_col]].dropna()
            fig_ben.add_trace(go.Scatter(x=d3["연도"], y=d3[emp_col], mode="lines+markers",
                                           name="임직원 수", line=dict(width=2, color="#2CA02C", dash="dot")), secondary_y=True)
        fig_ben.update_layout(font=dict(size=15), height=460)
        fig_ben.update_yaxes(title_text="복리후생비 총액(천원)", secondary_y=False)
        fig_ben.update_yaxes(title_text="1인당 복리후생비(천원) / 임직원 수(명)", secondary_y=True)
        st.plotly_chart(fig_ben, use_container_width=True)
        st.caption("💡 총액이 늘어도 임직원 수가 함께 늘면 1인당 금액은 정체되거나 줄어들 수 있습니다.")
    else:
        st.info("복리후생비 총액·1인당 변수가 없습니다.")

# =========================================================================
# TAB 4: 법인세와 기관 내 변동성
# =========================================================================
with tab_tax:
    st.markdown("### 🏛️ 과세표준 · 산출세액 · 결정세액 시계열")
    tax_keys_cols = [c for c in ["과세표준", "법인세산출세액", "법인세결정세액"] if c in org_df.columns]
    if tax_keys_cols:
        fig_tax = go.Figure()
        colors_tax = ["#4C78A8", "#E07B39", "#2CA02C"]
        for i, c in enumerate(tax_keys_cols):
            d = org_df[["연도", c]].dropna()
            fig_tax.add_trace(go.Scatter(x=d["연도"], y=d[c], mode="lines+markers", name=c,
                                           line=dict(width=3, color=colors_tax[i % len(colors_tax)])))
        fig_tax.update_layout(font=dict(size=15), height=440, yaxis_title="천원")
        st.plotly_chart(fig_tax, use_container_width=True)
    else:
        st.info("법인세 관련 변수가 없습니다.")

    st.divider()
    st.markdown("### 📐 선택 변수의 기관 내 변동성")
    numeric_keys = [k for k in VARIABLES.keys() if col_of(k) in org_df.columns]
    if numeric_keys:
        var_key = st.selectbox("변수 선택", numeric_keys, format_func=lambda k: f"{get_label(k)} ({get_unit(k)})", key="p9_volvar")
        vcol = col_of(var_key)
        s = pd.to_numeric(org_df.set_index("연도")[vcol], errors="coerce").dropna()
        if s.shape[0] >= 1:
            vm1, vm2, vm3, vm4, vm5 = st.columns(5)
            vm1.metric("평균", f"{s.mean():,.1f}")
            vm2.metric("중앙값", f"{s.median():,.1f}")
            vm3.metric("표준편차", f"{s.std():,.1f}" if s.shape[0] > 1 else "N/A")
            vm4.metric(f"최솟값 ({s.idxmin()}년)", f"{s.min():,.1f}")
            vm5.metric(f"최댓값 ({s.idxmax()}년)", f"{s.max():,.1f}")

            is_ratio = VARIABLES.get(var_key, {}).get("percent", False)
            if not is_ratio and s.mean() > 0 and (s >= 0).all() and s.shape[0] > 1:
                cv = s.std() / s.mean()
                st.metric("변동계수 CV (= SD/평균)", f"{cv:.3f}")
                st.caption("💡 CV가 클수록 이 기관 내부에서 연도에 따른 상대적 변동이 크다는 뜻입니다.")
            else:
                st.caption("비율 변수이거나 평균이 0 이하·음수 포함 가능성이 있어 CV를 계산하지 않습니다.")

            st.markdown("#### 연도별 변화율(또는 증감)")
            change_df = pd.DataFrame({"값": s}).sort_index()
            if is_ratio:
                change_df["변화"] = change_df["값"].diff()
                change_label = "전년 대비 증감(%p)"
            else:
                change_df["변화"] = change_df["값"].pct_change() * 100
                change_label = "전년 대비 증가율(%)"
            fig_chg = px.bar(change_df.reset_index(), x="연도", y="변화", labels={"변화": change_label})
            fig_chg.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_chg.update_layout(font=dict(size=15), height=380)
            st.plotly_chart(fig_chg, use_container_width=True)

            st.markdown("#### 🎯 기관의 과거 평균에서 가장 크게 벗어난 연도 Top 3")
            if s.shape[0] > 1 and s.std() > 0:
                z = ((s - s.mean()) / s.std()).abs().sort_values(ascending=False).head(3)
                dev_df = pd.DataFrame({"연도": z.index, "값": s.loc[z.index].values, "|z-score|": z.values.round(2)})
                st.dataframe(dev_df, use_container_width=True, hide_index=True)
                st.caption("💡 이 기관 자신의 평균·표준편차를 기준으로 계산한 값이며, 다른 기관과 비교한 순위가 아닙니다. 원인은 이 표만으로 단정할 수 없습니다.")
            else:
                st.info("표준편차를 계산할 만큼 관측 연도가 충분하지 않습니다.")
        else:
            st.info("선택한 변수에 유효한 관측치가 없습니다.")
    else:
        st.info("표시할 수 있는 변수가 없습니다.")
