# -*- coding: utf-8 -*-
"""
변수 메타데이터
================
build_analysis_panel()이 만드는 모든 분석변수의 표시명·단위·범주·유형·출처·설명을
한 곳에서 관리한다. 분포·랭킹·기관프로필·트렌드 등 모든 화면이 이 사전을 공유한다.
코드 곳곳에 변수명을 직접 반복하지 않는다.

type:
    "count"  절대량 (명, 원 단위 등 총액/인원)
    "amount" 금액 총액
    "ratio"  비율(%) 또는 배율
"""

VARIABLE_META = {
    # --- 인력 ---
    "total_workforce": {"label": "임직원 수", "unit": "명", "category": "인력", "type": "count",
                          "source": "임직원수현황.xlsx", "description": "기관의 전체 임직원 현원(임직원 총계 A+B+C)."},
    "total_authorized": {"label": "정원(일반정규직+무기계약직)", "unit": "명", "category": "인력", "type": "count",
                          "source": "임직원수현황.xlsx", "description": "일반정규직·무기계약직 정원의 합."},
    "fill_rate_pct": {"label": "정원충족률", "unit": "%", "category": "인력", "type": "ratio",
                       "source": "임직원수현황.xlsx", "description": "현원(일반정규직+무기계약직) ÷ 정원 × 100."},
    "female_workforce": {"label": "여성 임직원 수", "unit": "명", "category": "인력", "type": "count",
                          "source": "임직원수현황.xlsx", "description": "여성 현원 합계."},
    "female_ratio_pct": {"label": "여성인력 비율", "unit": "%", "category": "인력", "type": "ratio",
                          "source": "임직원수현황.xlsx", "description": "여성 임직원 수 ÷ 전체 임직원 수 × 100."},
    "nonregular_workforce": {"label": "비정규직 수", "unit": "명", "category": "인력", "type": "count",
                             "source": "임직원수현황.xlsx", "description": "기간제·기타·소속외 인력의 합."},

    # --- 채용 ---
    "total_new_hires": {"label": "신규채용 인원", "unit": "명", "category": "채용", "type": "count",
                         "source": "신규채용현황.xlsx", "description": "일반정규직 총 신규채용 인원."},
    "new_hire_rate_pct": {"label": "신규채용률", "unit": "%", "category": "채용", "type": "ratio",
                           "source": "신규채용현황.xlsx + 임직원수현황.xlsx", "description": "신규채용 인원 ÷ 임직원 현원 × 100."},
    "youth_hires": {"label": "청년 신규채용", "unit": "명", "category": "채용", "type": "count",
                    "source": "신규채용현황.xlsx", "description": "청년 신규채용 인원."},
    "youth_hire_ratio_pct": {"label": "청년채용 비율", "unit": "%", "category": "채용", "type": "ratio",
                              "source": "신규채용현황.xlsx", "description": "청년 신규채용 ÷ 전체 신규채용 × 100."},
    "female_hires": {"label": "여성 신규채용", "unit": "명", "category": "채용", "type": "count",
                     "source": "신규채용현황.xlsx", "description": "여성 신규채용 인원."},
    "female_hire_ratio_pct": {"label": "여성채용 비율", "unit": "%", "category": "채용", "type": "ratio",
                               "source": "신규채용현황.xlsx", "description": "여성 신규채용 ÷ 전체 신규채용 × 100."},
    "disabled_hires": {"label": "장애인 신규채용", "unit": "명", "category": "채용", "type": "count",
                        "source": "신규채용현황.xlsx", "description": "장애인 신규채용 인원."},
    "disabled_hire_ratio_pct": {"label": "장애인채용 비율", "unit": "%", "category": "채용", "type": "ratio",
                                 "source": "신규채용현황.xlsx", "description": "장애인 신규채용 ÷ 전체 신규채용 × 100."},

    # --- 직원 보수 ---
    "employee_avg_pay": {"label": "직원 평균보수", "unit": "천원", "category": "보수", "type": "amount",
                          "source": "직원평균보수현황.xlsx", "description": "정규직(일반정규직) 1인당 평균보수액."},
    "starting_pay": {"label": "신입사원 초임", "unit": "천원", "category": "보수", "type": "amount",
                      "source": "직원평균보수현황.xlsx (신입사원초임)", "description": "신입사원 초임 합계."},
    "avg_tenure_months": {"label": "평균근속연수", "unit": "개월", "category": "보수", "type": "amount",
                           "source": "직원평균보수현황.xlsx", "description": "정규직(일반정규직) 평균근속연수."},
    "base_pay": {"label": "기본급", "unit": "천원", "category": "보수", "type": "amount",
                 "source": "직원평균보수현황.xlsx", "description": "정규직(일반정규직) 1인당 기본급."},
    "fixed_allowance": {"label": "고정수당", "unit": "천원", "category": "보수", "type": "amount",
                         "source": "직원평균보수현황.xlsx", "description": "정규직(일반정규직) 1인당 고정수당."},
    "performance_pay": {"label": "성과상여금", "unit": "천원", "category": "보수", "type": "amount",
                        "source": "직원평균보수현황.xlsx", "description": "정규직(일반정규직) 1인당 성과상여금."},
    "management_eval_bonus": {"label": "경영평가 성과급", "unit": "천원", "category": "보수", "type": "amount",
                               "source": "직원평균보수현황.xlsx", "description": "정규직(일반정규직) 1인당 경영평가 성과급."},

    # --- 임원 ---
    "executive_total_pay": {"label": "기관장 연봉", "unit": "천원", "category": "임원", "type": "amount",
                             "source": "임원연봉.xlsx", "description": "상임기관장 보수 합계(연간)."},
    "executive_pay_multiple": {"label": "기관장-직원 보수배율", "unit": "배", "category": "임원", "type": "ratio",
                                "source": "임원연봉.xlsx ÷ 직원평균보수현황.xlsx", "description": "기관장 연봉 ÷ 직원 평균보수."},
    "executive_expense": {"label": "기관장 업무추진비", "unit": "천원", "category": "임원", "type": "amount",
                           "source": "기관장업무추진비.xlsx", "description": "기관장 업무추진비 집행금액."},
    "executive_expense_per_capita": {"label": "직원 1인당 업무추진비", "unit": "천원", "category": "임원", "type": "ratio",
                                      "source": "기관장업무추진비.xlsx ÷ 임직원수현황.xlsx", "description": "기관장 업무추진비 ÷ 임직원 수."},

    # --- 복리후생 ---
    "total_welfare_expense": {"label": "총 복리후생비", "unit": "천원", "category": "복지", "type": "amount",
                               "source": "복리후생비.xlsx", "description": "예산상 복리후생비 총계(A+B)."},
    "welfare_per_capita": {"label": "1인당 복리후생비", "unit": "천원", "category": "복지", "type": "ratio",
                            "source": "복리후생비.xlsx ÷ 임직원수현황.xlsx", "description": "총 복리후생비 ÷ 임직원 수."},

    # --- 일·가정 양립 ---
    "parental_leave_total": {"label": "육아휴직 사용자 수", "unit": "명", "category": "일가정양립", "type": "count",
                              "source": "일가정_양립.xlsx", "description": "전체 육아휴직 사용자 수."},
    "parental_leave_rate_pct": {"label": "육아휴직 이용률", "unit": "%", "category": "일가정양립", "type": "ratio",
                                 "source": "일가정_양립.xlsx ÷ 여성직원수", "description": "육아휴직 사용자 수 ÷ 여성 임직원 수 × 100 (근사 추정치)."},
    "male_parental_leave_ratio_pct": {"label": "남성 육아휴직 비율", "unit": "%", "category": "일가정양립", "type": "ratio",
                                       "source": "일가정_양립.xlsx", "description": "원자료에 보고된 남성 육아휴직 사용률."},
    "daycare_expense": {"label": "직장어린이집 운영비", "unit": "천원", "category": "일가정양립", "type": "amount",
                         "source": "일가정_양립.xlsx (직장어린이집운영비)",
                         "description": "지원항목별 금액 합계 (세부항목 간 일부 중복 집계 가능성 있음)."},
    "daycare_beneficiaries": {"label": "직장어린이집 수혜인원", "unit": "명", "category": "일가정양립", "type": "count",
                               "source": "일가정_양립.xlsx (직장어린이집운영비)", "description": "지원항목별 수혜인원 합계."},

    # --- 재정 ---
    "total_revenue": {"label": "총수입", "unit": "백만원", "category": "재정", "type": "amount",
                       "source": "수입지출현황.xlsx", "description": "수입 합계(정부지원수입·사업수입·출자금·차입금 등 포함)."},
    "total_expense": {"label": "총지출", "unit": "백만원", "category": "재정", "type": "amount",
                       "source": "수입지출현황.xlsx", "description": "지출 합계."},
    "balance": {"label": "수지", "unit": "백만원", "category": "재정", "type": "amount",
                "source": "수입지출현황.xlsx", "description": "총수입 - 총지출."},
    "gov_support_revenue": {"label": "정부지원수입", "unit": "백만원", "category": "재정", "type": "amount",
                             "source": "수입지출현황.xlsx", "description": "정부지원수입 소계(직접지원+간접지원)."},
    "gov_dependency_pct": {"label": "정부지원 의존도", "unit": "%", "category": "재정", "type": "ratio",
                            "source": "수입지출현황.xlsx", "description": "정부지원수입 ÷ 총수입 × 100."},
    "business_revenue": {"label": "사업수입(기타사업수입)", "unit": "백만원", "category": "재정", "type": "amount",
                          "source": "수입지출현황.xlsx",
                          "description": "원자료에 별도 '사업수입' 소계가 없어 '기타사업수입' 항목을 사용."},
    "own_revenue_conservative": {"label": "자체수입(보수적 정의)", "unit": "백만원", "category": "재정", "type": "amount",
                                  "source": "수입지출현황.xlsx", "description": "기타사업수입만 반영한 보수적 자체수입."},
    "own_revenue_broad": {"label": "자체수입(광의)", "unit": "백만원", "category": "재정", "type": "amount",
                           "source": "수입지출현황.xlsx", "description": "총수입 - 정부지원수입."},
    "revenue_per_employee": {"label": "직원 1인당 총수입", "unit": "백만원", "category": "재정", "type": "ratio",
                              "source": "수입지출현황.xlsx ÷ 임직원수현황.xlsx", "description": "총수입 ÷ 임직원 수."},
    "business_revenue_per_employee": {"label": "직원 1인당 사업수입", "unit": "백만원", "category": "재정", "type": "ratio",
                                       "source": "수입지출현황.xlsx ÷ 임직원수현황.xlsx", "description": "사업수입 ÷ 임직원 수."},
    "labor_cost": {"label": "인건비", "unit": "백만원", "category": "재정", "type": "amount",
                   "source": "수입지출현황.xlsx", "description": "지출 중 인건비."},
    "labor_cost_ratio_pct": {"label": "인건비 비중", "unit": "%", "category": "재정", "type": "ratio",
                              "source": "수입지출현황.xlsx", "description": "인건비 ÷ 총지출 × 100."},

    # --- 법인세 ---
    "taxable_income": {"label": "과세표준", "unit": "천원", "category": "법인세", "type": "amount",
                        "source": "법인세정보.xlsx", "description": "법인세 과세표준."},
    "corporate_tax_calculated": {"label": "법인세 산출세액", "unit": "천원", "category": "법인세", "type": "amount",
                                  "source": "법인세정보.xlsx", "description": "과세표준에 세율을 적용한 산출세액."},
    "tax_credit": {"label": "세액공제", "unit": "천원", "category": "법인세", "type": "amount",
                   "source": "법인세정보.xlsx", "description": "법인세 세액공제 금액."},
    "additional_tax": {"label": "가산세", "unit": "천원", "category": "법인세", "type": "amount",
                        "source": "법인세정보.xlsx", "description": "법인세 가산세."},
    "corporate_tax_final": {"label": "법인세 결정세액", "unit": "천원", "category": "법인세", "type": "amount",
                             "source": "법인세정보.xlsx", "description": "최종 결정세액."},
    "tax_credit_ratio": {"label": "세액공제 비율", "unit": "%", "category": "법인세", "type": "ratio",
                          "source": "법인세정보.xlsx", "description": "세액공제 ÷ 법인세 산출세액 × 100."},
    "tax_burden_ratio": {"label": "세부담 비율(참고용)", "unit": "%", "category": "법인세", "type": "ratio",
                          "source": "법인세정보.xlsx",
                          "description": "결정세액 ÷ 과세표준 × 100. 세법상 '실효세율'과 동일한 개념이 아닌 참고 지표."},
}

# 분포/랭킹/관계 selectbox에 노출할 기본 순서
ALL_VARIABLES = list(VARIABLE_META.keys())

# 카테고리별 그룹 (selectbox를 카테고리로 묶어 보여줄 때 사용)
CATEGORY_ORDER = ["인력", "채용", "보수", "임원", "복지", "일가정양립", "재정", "법인세"]


def var_label(key: str) -> str:
    meta = VARIABLE_META.get(key)
    return f"{meta['label']} ({meta['unit']})" if meta else key


def variables_by_category(keys=None):
    """카테고리 -> [(라벨, key), ...] 형태로 묶어 반환."""
    keys = keys or ALL_VARIABLES
    grouped = {c: [] for c in CATEGORY_ORDER}
    for k in keys:
        meta = VARIABLE_META.get(k)
        if not meta:
            continue
        grouped.setdefault(meta["category"], []).append((var_label(k), k))
    return {c: v for c, v in grouped.items() if v}


def var_options(keys=None):
    keys = keys or ALL_VARIABLES
    return [(var_label(k), k) for k in keys]
