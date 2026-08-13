# -*- coding: utf-8 -*-
"""
통계 함수 모음 (기술통계 + 기초 계량분석)
==========================================
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm


# ---------------------------------------------------------------------
# 기술통계
# ---------------------------------------------------------------------

def descriptive_stats(series: pd.Series) -> dict:
    """숫자형 Series에 대한 표준 요약통계를 반환한다."""
    s = pd.to_numeric(series, errors="coerce")
    n_total = len(s)
    missing = int(s.isna().sum())
    valid = s.dropna()
    n_valid = len(valid)

    if n_valid == 0:
        return {
            "n": n_total, "n_valid": 0, "missing": missing,
            "missing_pct": round(missing / n_total * 100, 1) if n_total else np.nan,
            "zero_count": 0, "zero_pct": np.nan, "mean": np.nan, "median": np.nan,
            "std": np.nan, "min": np.nan, "q1": np.nan, "q3": np.nan, "max": np.nan,
        }

    zero_count = int((valid == 0).sum())
    return {
        "n": n_total, "n_valid": n_valid, "missing": missing,
        "missing_pct": round(missing / n_total * 100, 1) if n_total else np.nan,
        "zero_count": zero_count,
        "zero_pct": round(zero_count / n_valid * 100, 1),
        "mean": float(valid.mean()), "median": float(valid.median()),
        "std": float(valid.std()), "min": float(valid.min()),
        "q1": float(valid.quantile(0.25)), "q3": float(valid.quantile(0.75)),
        "max": float(valid.max()),
    }


def stats_to_display_df(stats: dict, decimals=1) -> pd.DataFrame:
    label_map = {
        "n": "N (전체)", "n_valid": "N (결측 제외)", "missing": "결측 수",
        "missing_pct": "결측 비율(%)", "zero_count": "0인 기관 수",
        "zero_pct": "0 비율(%, 유효값 중)", "mean": "평균", "median": "중앙값",
        "std": "표준편차", "min": "최소값", "q1": "Q1 (25%)", "q3": "Q3 (75%)", "max": "최대값",
    }
    rows = []
    for k, label in label_map.items():
        v = stats.get(k, np.nan)
        if isinstance(v, float) and not np.isnan(v):
            v = round(v, decimals)
        rows.append({"항목": label, "값": v})
    return pd.DataFrame(rows)


def group_summary(df: pd.DataFrame, value_col: str, group_col: str) -> pd.DataFrame:
    def _agg(s):
        st_ = descriptive_stats(s)
        return pd.Series({"N": st_["n_valid"], "평균": st_["mean"], "중앙값": st_["median"], "표준편차": st_["std"]})
    return df.groupby(group_col)[value_col].apply(_agg).unstack().reset_index()


def yearly_summary(df: pd.DataFrame, value_col: str, year_col="연도", agg="평균") -> pd.DataFrame:
    agg_map = {"평균": "mean", "중앙값": "median", "합계": "sum"}
    result = df.groupby(year_col)[value_col].agg(agg_map.get(agg, "mean")).reset_index()
    return result.rename(columns={value_col: agg})


def safe_ratio(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    ratio = num / den.replace(0, np.nan)
    return ratio.replace([np.inf, -np.inf], np.nan)


# ---------------------------------------------------------------------
# 기초 계량분석 (OLS / Logit)
# ---------------------------------------------------------------------

def run_simple_ols(df: pd.DataFrame, x_col: str, y_col: str, log_x=False, log_y=False):
    data = df[[x_col, y_col]].copy()
    data[x_col] = pd.to_numeric(data[x_col], errors="coerce")
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    data = data.dropna()

    x_used = data[x_col]
    y_used = data[y_col]
    if log_x:
        x_used = np.log1p(x_used.clip(lower=0))
    if log_y:
        y_used = np.log1p(y_used.clip(lower=0))

    X = sm.add_constant(x_used)
    model = sm.OLS(y_used, X).fit()

    table = pd.DataFrame({
        "변수": ["상수항", x_col],
        "계수(Coefficient)": model.params.values,
        "표준오차(SE)": model.bse.values,
        "t값": model.tvalues.values,
        "p값": model.pvalues.values,
    })

    return {
        "model": model, "table": table, "r2": model.rsquared, "n": int(model.nobs),
        "x_used": x_used, "y_used": y_used, "fitted": model.fittedvalues, "resid": model.resid,
    }


def run_multiple_ols(df: pd.DataFrame, y_col: str, x_cols: list, cat_cols: list = None):
    cat_cols = cat_cols or []
    data = df[[y_col] + x_cols + cat_cols].copy()
    for c in [y_col] + x_cols:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    data = data.dropna()

    X_num = data[x_cols]
    if cat_cols:
        X_cat = pd.get_dummies(data[cat_cols], drop_first=True)
        X = pd.concat([X_num, X_cat], axis=1)
    else:
        X = X_num
    X = sm.add_constant(X.astype(float))
    y = data[y_col].astype(float)

    model = sm.OLS(y, X).fit()
    table = pd.DataFrame({
        "변수": model.params.index, "계수(Coefficient)": model.params.values,
        "표준오차(SE)": model.bse.values, "t값": model.tvalues.values, "p값": model.pvalues.values,
    })
    return {"model": model, "table": table, "r2": model.rsquared, "adj_r2": model.rsquared_adj, "n": int(model.nobs)}


def run_logit(df: pd.DataFrame, y_binary_col: str, x_cols: list):
    data = df[[y_binary_col] + x_cols].copy()
    for c in [y_binary_col] + x_cols:
        data[c] = pd.to_numeric(data[c], errors="coerce")
    data = data.dropna()

    X = sm.add_constant(data[x_cols].astype(float))
    y = data[y_binary_col].astype(float)
    model = sm.Logit(y, X).fit(disp=0)

    table = pd.DataFrame({
        "변수": model.params.index, "계수(Coefficient)": model.params.values,
        "표준오차(SE)": model.bse.values, "p값": model.pvalues.values,
    })
    return {"model": model, "table": table, "n": int(model.nobs), "data": data}


def predicted_probability_curve(model, x_col: str, data: pd.DataFrame, n_points=100):
    x_range = np.linspace(data[x_col].min(), data[x_col].max(), n_points)
    X_pred = pd.DataFrame({"const": 1.0, x_col: x_range})
    for col in model.params.index:
        if col not in ("const", x_col):
            X_pred[col] = data[col].mean()
    X_pred = X_pred[model.params.index]
    return x_range, model.predict(X_pred)
