# -*- coding: utf-8 -*-
"""
변수 메타데이터 / 질문은행 / 추천 관계 프리셋
================================================
분포 탐색·변수 관계 탭에서 selectbox와 안내 문구를 이 사전 하나로 관리한다.
코드 곳곳에 변수명을 직접 반복하지 않기 위한 단일 출처(single source of truth).
"""

# key: build_analysis_panel()이 만드는 컬럼명
VARIABLE_META = {
    "total_workforce": {"label": "임직원 수", "unit": "명", "category": "인력", "source": "임직원수현황.xlsx"},
    "fill_rate_pct": {"label": "정원충족률", "unit": "%", "category": "인력", "source": "임직원수현황.xlsx (정원/현원)"},
    "female_ratio_pct": {"label": "여성인력 비율", "unit": "%", "category": "인력", "source": "임직원수현황.xlsx"},
    "new_hire_rate_pct": {"label": "신규채용률", "unit": "%", "category": "채용", "source": "신규채용현황.xlsx ÷ 임직원수현황.xlsx"},
    "youth_hire_ratio_pct": {"label": "청년채용 비율", "unit": "%", "category": "채용", "source": "신규채용현황.xlsx"},
    "female_hire_ratio_pct": {"label": "여성채용 비율", "unit": "%", "category": "채용", "source": "신규채용현황.xlsx"},
    "disabled_hire_ratio_pct": {"label": "장애인채용 비율", "unit": "%", "category": "채용", "source": "신규채용현황.xlsx"},
    "employee_avg_pay": {"label": "직원 평균보수", "unit": "천원", "category": "보수", "source": "직원평균보수현황.xlsx"},
    "starting_pay": {"label": "신입사원 초임", "unit": "천원", "category": "보수", "source": "직원평균보수현황.xlsx (신입사원초임)"},
    "avg_tenure_months": {"label": "평균근속연수", "unit": "개월", "category": "보수", "source": "직원평균보수현황.xlsx"},
    "executive_pay_multiple": {"label": "기관장-직원 보수배율", "unit": "배", "category": "보수", "source": "임원연봉.xlsx ÷ 직원평균보수현황.xlsx"},
    "welfare_per_capita": {"label": "1인당 복리후생비", "unit": "천원", "category": "복지", "source": "복리후생비.xlsx ÷ 임직원수현황.xlsx"},
    "parental_leave_rate_pct": {"label": "육아휴직 이용률", "unit": "%", "category": "일가정양립", "source": "일가정_양립.xlsx ÷ 여성직원수"},
    "male_parental_leave_ratio_pct": {"label": "남성 육아휴직 비율", "unit": "%", "category": "일가정양립", "source": "일가정_양립.xlsx"},
    "total_revenue": {"label": "총수입", "unit": "백만원", "category": "재정", "source": "수입지출현황.xlsx"},
    "business_revenue": {"label": "사업수입(기타사업수입)", "unit": "백만원", "category": "재정", "source": "수입지출현황.xlsx"},
    "revenue_per_employee": {"label": "직원 1인당 총수입", "unit": "백만원", "category": "재정", "source": "수입지출현황.xlsx ÷ 임직원수현황.xlsx"},
    "business_revenue_per_employee": {"label": "직원 1인당 사업수입", "unit": "백만원", "category": "재정", "source": "수입지출현황.xlsx ÷ 임직원수현황.xlsx"},
    "gov_dependency_pct": {"label": "정부지원 의존도", "unit": "%", "category": "재정", "source": "수입지출현황.xlsx"},
    "labor_cost_ratio_pct": {"label": "인건비 비중", "unit": "%", "category": "재정", "source": "수입지출현황.xlsx"},
}

# 분포 탐색 selectbox에 노출할 순서
DISTRIBUTION_VARIABLES = list(VARIABLE_META.keys())

QUESTION_BANK = {
    "total_workforce": [
        "기관 규모의 분포는 대칭적인가?",
        "일부 초대형 기관이 평균을 왜곡하고 있는가?",
        "로그 변환을 고려할 필요가 있어 보이는가?",
    ],
    "fill_rate_pct": [
        "정원충족률이 100%를 넘는 기관이 있는가? 있다면 왜일까?",
        "기관유형별로 정원충족률 분포가 다른가?",
    ],
    "new_hire_rate_pct": [
        "신규채용률이 0에 가까운 기관이 많은가?",
        "대형기관과 소형기관의 채용률은 다른가?",
    ],
    "employee_avg_pay": [
        "평균과 중앙값은 얼마나 차이가 나는가?",
        "직원 평균보수 분포에 이상치가 존재하는가?",
        "기관유형을 나누면 분포가 달라지는가?",
    ],
    "executive_pay_multiple": [
        "보수배율이 유독 높은 기관이 있는가?",
        "기관유형별로 보수배율 분포가 다른가?",
    ],
    "welfare_per_capita": [
        "1인당 복리후생비가 유독 높거나 낮은 기관이 있는가?",
        "복리후생비 총액과 1인당 지표의 순위가 달라지는가?",
    ],
    "parental_leave_rate_pct": [
        "육아휴직 이용률이 0인 기관은 실제로 이용자가 없는 것인가, 자료가 없는 것인가?",
        "기관유형별로 이용률 분포가 다른가?",
    ],
    "gov_dependency_pct": [
        "정부지원 의존도가 100%에 가까운 기관은 어떤 유형인가?",
        "의존도가 낮은 기관은 재정적으로 더 안정적인가?",
    ],
}
DEFAULT_QUESTIONS = [
    "평균과 중앙값의 차이가 큰가? 일부 극단값이 평균을 끌어올리고 있지는 않은가?",
    "기관유형별로 분포가 달라지는가?",
    "이상치로 보이는 기관이 있는가?",
]

# 변수 관계 탭 - 추천 조합 (label, x, y)
RELATIONSHIP_PRESETS = [
    {"label": "임직원 수 → 직원 평균보수", "x": "total_workforce", "y": "employee_avg_pay",
     "question": "규모가 큰 기관일수록 평균보수가 높은가?"},
    {"label": "평균근속연수 → 직원 평균보수", "x": "avg_tenure_months", "y": "employee_avg_pay",
     "question": "평균근속연수가 긴 기관일수록 평균보수가 높은가?"},
    {"label": "신입사원 초임 → 직원 평균보수", "x": "starting_pay", "y": "employee_avg_pay",
     "question": "신입초임이 높은 기관은 전체 평균보수도 높은가?"},
    {"label": "정원충족률 → 신규채용률", "x": "fill_rate_pct", "y": "new_hire_rate_pct",
     "question": "정원충족률이 낮은 기관이 신규채용을 더 많이 하는가?"},
    {"label": "임직원 수 → 신규채용률", "x": "total_workforce", "y": "new_hire_rate_pct",
     "question": "대형기관과 소형기관의 채용률은 다른가?"},
    {"label": "여성인력 비율 → 여성채용 비율", "x": "female_ratio_pct", "y": "female_hire_ratio_pct",
     "question": "기존 여성인력 비율이 높은 기관은 여성 신규채용 비율도 높은가?"},
    {"label": "직원 평균보수 → 1인당 복리후생비", "x": "employee_avg_pay", "y": "welfare_per_capita",
     "question": "보수가 높은 기관은 복리후생비도 높은가?"},
    {"label": "평균근속연수 → 1인당 복리후생비", "x": "avg_tenure_months", "y": "welfare_per_capita",
     "question": "근속연수가 긴 기관에서 복리후생비가 높은가?"},
    {"label": "여성인력 비율 → 육아휴직 이용률", "x": "female_ratio_pct", "y": "parental_leave_rate_pct",
     "question": "여성인력 비율이 높은 기관일수록 육아휴직 이용률도 높은가?"},
    {"label": "여성인력 비율 → 남성 육아휴직 비율", "x": "female_ratio_pct", "y": "male_parental_leave_ratio_pct",
     "question": "여성인력 비율과 남성 육아휴직 활용 사이에도 관계가 있는가?"},
    {"label": "정부지원 의존도 → 직원 평균보수", "x": "gov_dependency_pct", "y": "employee_avg_pay",
     "question": "정부지원 의존도가 높은 기관은 보수 수준이 다른가?"},
    {"label": "직원 1인당 사업수입 → 직원 평균보수", "x": "business_revenue_per_employee", "y": "employee_avg_pay",
     "question": "1인당 사업수입이 높은 기관은 직원 보수도 높은가?"},
    {"label": "총수입 → 임직원 수", "x": "total_revenue", "y": "total_workforce",
     "question": "기관 규모가 클수록 총수입은 반드시 증가하는가?"},
    {"label": "정부지원 의존도 → 1인당 복리후생비", "x": "gov_dependency_pct", "y": "welfare_per_capita",
     "question": "정부지원 의존도와 복리후생 수준은 어떤 관계를 보이는가?"},
    {"label": "직원 1인당 사업수입 → 1인당 복리후생비", "x": "business_revenue_per_employee", "y": "welfare_per_capita",
     "question": "재정적으로 자체수입이 높은 기관에서 복지 수준도 높은가?"},
]


def var_label(key: str) -> str:
    meta = VARIABLE_META.get(key)
    return f"{meta['label']} ({meta['unit']})" if meta else key


def var_options():
    """selectbox용 (표시 라벨, key) 튜플 리스트."""
    return [(var_label(k), k) for k in DISTRIBUTION_VARIABLES]
