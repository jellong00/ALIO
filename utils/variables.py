"""
variables.py
------------
대시보드에서 사용하는 모든 분석 변수의 메타데이터.
각 변수는 실제 패널 데이터(utils.data_loader.build_panel + metrics.add_derived_variables)의
컬럼명과 정확히 일치해야 한다.
"""

DOMAINS = ["기관 특성", "재정 구조", "조직 운영", "인사 결과"]

ORG_TYPE_COLORS = {
    "공기업(시장형)": "#1f77b4",
    "공기업(준시장형)": "#ff7f0e",
    "준정부기관(기금관리형)": "#2ca02c",
    "준정부기관(위탁집행형)": "#d62728",
    "기타공공기관": "#9467bd",
}

VARIABLES = {
    # ============ A. 기관 특성 ============
    "임직원수": {
        "column": "임직원수", "label": "임직원 수", "domain": "기관 특성",
        "unit": "명", "description": "임원+정규직+무기계약직을 합한 임직원 총계",
        "log_allowed": True, "percent": False,
    },
    "여성현원": {
        "column": "여성현원", "label": "여성 직원 수", "domain": "기관 특성",
        "unit": "명", "description": "여성 임직원 현원 합계",
        "log_allowed": True, "percent": False,
    },
    "여성직원비율": {
        "column": "여성직원비율", "label": "여성 직원 비율", "domain": "기관 특성",
        "unit": "%", "description": "여성현원 / 임직원수 × 100",
        "log_allowed": False, "percent": True,
    },
    "정규직현원": {
        "column": "정규직현원", "label": "정규직(일반정규직) 현원", "domain": "기관 특성",
        "unit": "명", "description": "일반정규직 현원 계",
        "log_allowed": True, "percent": False,
    },
    "평균근속연수": {
        "column": "평균근속연수", "label": "평균근속연수", "domain": "기관 특성",
        "unit": "년", "description": "정규직(일반정규직) 평균근속연수",
        "log_allowed": False, "percent": False,
    },

    # ============ B. 재정 구조 ============
    "총수입": {
        "column": "총수입", "label": "총수입", "domain": "재정 구조",
        "unit": "백만원", "description": "고유사업+기금계정 수입합계",
        "log_allowed": True, "percent": False,
    },
    "총지출": {
        "column": "총지출", "label": "총지출", "domain": "재정 구조",
        "unit": "백만원", "description": "고유사업+기금계정 지출합계",
        "log_allowed": True, "percent": False,
    },
    "정부지원수입": {
        "column": "정부지원수입", "label": "정부지원수입", "domain": "재정 구조",
        "unit": "백만원", "description": "출연금·보조금 등 정부지원수입 소계",
        "log_allowed": True, "percent": False,
    },
    "정부지원의존도": {
        "column": "정부지원의존도", "label": "정부지원 의존도", "domain": "재정 구조",
        "unit": "%", "description": "정부지원수입 / 총수입 × 100",
        "log_allowed": False, "percent": True,
    },
    "1인당총수입": {
        "column": "1인당총수입", "label": "1인당 총수입", "domain": "재정 구조",
        "unit": "백만원/인", "description": "총수입 / 임직원수",
        "log_allowed": True, "percent": False,
    },
    "1인당총지출": {
        "column": "1인당총지출", "label": "1인당 총지출", "domain": "재정 구조",
        "unit": "백만원/인", "description": "총지출 / 임직원수",
        "log_allowed": True, "percent": False,
    },
    "수입지출차이": {
        "column": "수입지출차이", "label": "수입-지출 차이", "domain": "재정 구조",
        "unit": "백만원", "description": "총수입 - 총지출 (양수면 흑자 성격)",
        "log_allowed": False, "percent": False,
    },
    "과세표준": {
        "column": "과세표준", "label": "법인세 과세표준", "domain": "재정 구조",
        "unit": "천원", "description": "법인세 과세표준액",
        "log_allowed": True, "percent": False,
    },
    "법인세결정세액": {
        "column": "법인세결정세액", "label": "법인세 결정세액", "domain": "재정 구조",
        "unit": "천원", "description": "산출세액-세액공제+가산세 반영 최종 결정세액",
        "log_allowed": True, "percent": False,
    },
    "실효법인세율": {
        "column": "실효법인세율", "label": "실효법인세율", "domain": "재정 구조",
        "unit": "%", "description": "법인세결정세액 / 과세표준 × 100 (과세표준≤0은 결측)",
        "log_allowed": False, "percent": True,
    },

    # ============ C. 조직 운영 ============
    "직원평균보수": {
        "column": "직원평균보수", "label": "직원 평균보수", "domain": "조직 운영",
        "unit": "천원", "description": "정규직(일반정규직) 1인당 평균보수액",
        "log_allowed": True, "percent": False,
    },
    "기본급": {
        "column": "기본급", "label": "기본급", "domain": "조직 운영",
        "unit": "천원", "description": "정규직(일반정규직) 기본급",
        "log_allowed": True, "percent": False,
    },
    "고정수당": {
        "column": "고정수당", "label": "고정수당", "domain": "조직 운영",
        "unit": "천원", "description": "정규직(일반정규직) 고정수당",
        "log_allowed": True, "percent": False,
    },
    "성과상여금": {
        "column": "성과상여금", "label": "성과상여금", "domain": "조직 운영",
        "unit": "천원", "description": "정규직(일반정규직) 성과상여금",
        "log_allowed": True, "percent": False,
    },
    "경영평가성과급": {
        "column": "경영평가성과급", "label": "경영평가 성과급", "domain": "조직 운영",
        "unit": "천원", "description": "정규직(일반정규직) 경영평가 성과급",
        "log_allowed": True, "percent": False,
    },
    "신입사원초임": {
        "column": "신입사원초임", "label": "신입사원 초임", "domain": "조직 운영",
        "unit": "천원", "description": "신입사원 초임 합계",
        "log_allowed": True, "percent": False,
    },
    "기관장연봉": {
        "column": "기관장연봉", "label": "기관장 연봉", "domain": "조직 운영",
        "unit": "천원", "description": "상임기관장 연봉 합계",
        "log_allowed": True, "percent": False,
    },
    "임원평균연봉": {
        "column": "임원평균연봉", "label": "상임임원 평균연봉", "domain": "조직 운영",
        "unit": "천원", "description": "상임임원 평균보수(연봉)",
        "log_allowed": True, "percent": False,
    },
    "기관장직원보수배율": {
        "column": "기관장직원보수배율", "label": "기관장-직원 보수배율", "domain": "조직 운영",
        "unit": "배", "description": "기관장연봉 / 직원평균보수",
        "log_allowed": False, "percent": False,
    },
    "복리후생비": {
        "column": "복리후생비", "label": "복리후생비", "domain": "조직 운영",
        "unit": "천원", "description": "예산상 복리후생비 총계(급여성+비급여성)",
        "log_allowed": True, "percent": False,
    },
    "1인당복리후생비": {
        "column": "1인당복리후생비", "label": "1인당 복리후생비", "domain": "조직 운영",
        "unit": "천원/인", "description": "복리후생비 / 임직원수",
        "log_allowed": True, "percent": False,
    },
    "기관장업무추진비": {
        "column": "기관장업무추진비", "label": "기관장 업무추진비", "domain": "조직 운영",
        "unit": "천원", "description": "기관장 업무추진비 집행금액",
        "log_allowed": True, "percent": False,
    },
    "1인당기관장업무추진비": {
        "column": "1인당기관장업무추진비", "label": "1인당 기관장 업무추진비", "domain": "조직 운영",
        "unit": "천원/인", "description": "기관장업무추진비 / 임직원수",
        "log_allowed": True, "percent": False,
    },

    # ============ D. 인사 결과 ============
    "신규채용자수": {
        "column": "신규채용자수", "label": "신규채용자 수", "domain": "인사 결과",
        "unit": "명", "description": "일반정규직 총 신규채용 인원",
        "log_allowed": True, "percent": False,
    },
    "신규채용률": {
        "column": "신규채용률", "label": "신규채용률", "domain": "인사 결과",
        "unit": "%", "description": "신규채용자수 / 임직원수 × 100",
        "log_allowed": False, "percent": True,
    },
    "여성신규채용자수": {
        "column": "여성신규채용자수", "label": "여성 신규채용자 수", "domain": "인사 결과",
        "unit": "명", "description": "여성 신규채용 인원",
        "log_allowed": True, "percent": False,
    },
    "여성신규채용비율": {
        "column": "여성신규채용비율", "label": "여성 신규채용 비율", "domain": "인사 결과",
        "unit": "%", "description": "여성신규채용자수 / 신규채용자수 × 100",
        "log_allowed": False, "percent": True,
    },
    "청년신규채용자수": {
        "column": "청년신규채용자수", "label": "청년 신규채용자 수", "domain": "인사 결과",
        "unit": "명", "description": "청년 신규채용 인원",
        "log_allowed": True, "percent": False,
    },
    "장애인신규채용자수": {
        "column": "장애인신규채용자수", "label": "장애인 신규채용자 수", "domain": "인사 결과",
        "unit": "명", "description": "장애인 신규채용 인원",
        "log_allowed": True, "percent": False,
    },
    "남성육아휴직사용자수": {
        "column": "남성육아휴직사용자수", "label": "남성 육아휴직 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "남성 육아휴직 사용자 수",
        "log_allowed": True, "percent": False,
    },
    "여성육아휴직사용자수": {
        "column": "여성육아휴직사용자수", "label": "여성 육아휴직 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "여성 육아휴직 사용자 수",
        "log_allowed": True, "percent": False,
    },
    "남성육아휴직사용률": {
        "column": "남성육아휴직사용률", "label": "남성 육아휴직 사용률", "domain": "인사 결과",
        "unit": "%", "description": "남성 육아휴직 사용률",
        "log_allowed": False, "percent": True,
    },
    "여성육아휴직사용률": {
        "column": "여성육아휴직사용률", "label": "여성 육아휴직 사용률", "domain": "인사 결과",
        "unit": "%", "description": "여성 육아휴직 사용률",
        "log_allowed": False, "percent": True,
    },
    "출산휴가사용자수": {
        "column": "출산휴가사용자수", "label": "출산휴가 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "출산휴가 사용자 수",
        "log_allowed": True, "percent": False,
    },
    "배우자출산휴가사용자수": {
        "column": "배우자출산휴가사용자수", "label": "배우자 출산휴가 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "배우자 출산휴가 사용자 수",
        "log_allowed": True, "percent": False,
    },
    "임신기단축근무": {
        "column": "임신기단축근무", "label": "임신기 단축근무 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "임신기 근로시간 단축제도 사용자 수",
        "log_allowed": True, "percent": False,
    },
    "육아기단축근무": {
        "column": "육아기단축근무", "label": "육아기 단축근무 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "육아기 근로시간 단축제도 사용자 수",
        "log_allowed": True, "percent": False,
    },
    "가족돌봄휴가_전체": {
        "column": "가족돌봄휴가_전체", "label": "가족돌봄휴가 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "가족돌봄휴가 사용자 수(전체)",
        "log_allowed": True, "percent": False,
    },
    "가족돌봄휴직_전체": {
        "column": "가족돌봄휴직_전체", "label": "가족돌봄휴직 사용자 수", "domain": "인사 결과",
        "unit": "명", "description": "가족돌봄휴직 사용자 수(전체)",
        "log_allowed": True, "percent": False,
    },
}


def get_vars_by_domain(domain):
    return {k: v for k, v in VARIABLES.items() if v["domain"] == domain}


def get_label(key):
    return VARIABLES.get(key, {}).get("label", key)


def get_unit(key):
    return VARIABLES.get(key, {}).get("unit", "")


def get_column(key):
    return VARIABLES.get(key, {}).get("column", key)


def format_value(key, value):
    import math
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return "N/A"
    meta = VARIABLES.get(key, {})
    unit = meta.get("unit", "")
    if meta.get("percent"):
        return f"{value:,.1f}%"
    if isinstance(value, float):
        return f"{value:,.1f} {unit}".strip()
    return f"{value:,} {unit}".strip()
