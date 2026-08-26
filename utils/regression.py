"""
regression.py
-------------
학생들이 종속변수-설명변수-통제변수를 선택하여 OLS 회귀를 직접 실행할 수 있도록
지원하는 헬퍼 함수. statsmodels 기반이며, 범주형 통제변수는 더미 처리한다.
패널 고정효과는 기관/연도 더미를 추가하는 방식(LSDV)으로 구현한다.
"""

import numpy as np
import pandas as pd
import statsmodels.api as sm


def build_design_matrix(df, y_col, x_cols, cat_controls=None, entity_fe=False, year_fe=False,
                         entity_col="기관명", year_col="연도"):
    """회귀에 사용할 X, y를 구성한다. 결측치는 listwise로 제거한다."""
    cat_controls = cat_controls or []
    use_cols = [y_col] + x_cols + cat_controls
    if entity_fe:
        use_cols.append(entity_col)
    if year_fe:
        use_cols.append(year_col)
    data = df[list(dict.fromkeys(use_cols))].dropna().copy()

    X_parts = [data[x_cols].apply(pd.to_numeric, errors="coerce")]

    for c in cat_controls:
        dummies = pd.get_dummies(data[c], prefix=c, drop_first=True)
        X_parts.append(dummies.astype(float))

    if entity_fe:
        dummies = pd.get_dummies(data[entity_col], prefix="기관", drop_first=True)
        X_parts.append(dummies.astype(float))
    if year_fe:
        dummies = pd.get_dummies(data[year_col].astype(str), prefix="연도", drop_first=True)
        X_parts.append(dummies.astype(float))

    X = pd.concat(X_parts, axis=1)
    X = sm.add_constant(X)
    y = pd.to_numeric(data[y_col], errors="coerce")
    return y, X, data


def run_ols(df, y_col, x_cols, cat_controls=None, entity_fe=False, year_fe=False, robust=True):
    y, X, data = build_design_matrix(df, y_col, x_cols, cat_controls, entity_fe, year_fe)
    if X.shape[0] < X.shape[1] + 5 or X.shape[0] == 0:
        return None, None, None
    model = sm.OLS(y, X.astype(float))
    if robust:
        result = model.fit(cov_type="HC1")
    else:
        result = model.fit()
    return result, data, X


def coef_table(result, exclude_prefixes=("기관_", "연도_")):
    """회귀결과에서 주요 변수(고정효과 더미 제외)만 뽑아 표로 만든다."""
    params = result.params
    conf = result.conf_int()
    rows = []
    for name in params.index:
        if any(name.startswith(p) for p in exclude_prefixes):
            continue
        rows.append({
            "variable": name,
            "coef": params[name],
            "std_err": result.bse[name],
            "t": result.tvalues[name],
            "p_value": result.pvalues[name],
            "ci_low": conf.loc[name, 0],
            "ci_high": conf.loc[name, 1],
        })
    return pd.DataFrame(rows)


def model_summary_stats(result):
    return {
        "N": int(result.nobs),
        "R²": result.rsquared,
        "adj. R²": result.rsquared_adj,
    }


def compute_vif(X, exclude_prefixes=("기관_", "연도_", "const")):
    """수치형 설명변수들의 VIF(분산팽창계수)를 계산한다. 더미변수·상수항은 제외한다."""
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    cols = [c for c in X.columns if not any(c.startswith(p) for p in exclude_prefixes)]
    if len(cols) < 2:
        return pd.DataFrame(columns=["variable", "VIF"])
    Xn = X[cols].astype(float)
    rows = []
    for i, c in enumerate(cols):
        try:
            vif = variance_inflation_factor(Xn.values, i)
        except Exception:
            vif = float("nan")
        rows.append({"variable": c, "VIF": vif})
    return pd.DataFrame(rows)
