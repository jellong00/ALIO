"""
variables.py
------------
대시보드에서 사용하는 모든 분석 변수의 메타데이터.
각 변수는 실제 패널 데이터(utils.data_loader.build_panel + metrics.add_derived_variables)의
컬럼명과 정확히 일치해야 한다.

- domain: 4대 영역(기관특성/재정구조/조직운영/인사결과) — 참고용 대분류
- category: 8개 세부 카테고리(인력/채용/보수/임원/복지/일가정양립/재정/법인세) — 페이지1 변수선택 기준
"""

DOMAINS = ["기관 특성", "재정 구조", "조직 운영", "인사 결과"]
CATEGORIES = ["기관·인력", "재정", "법인세", "보수", "임원", "복리후생", "채용", "일가정양립"]

ORG_TYPE_COLORS = {
    "공기업(시장형)": "#1f77b4",
    "공기업(준시장형)": "#ff7f0e",
    "준정부기관(기금관리형)": "#2ca02c",
    "준정부기관(위탁집행형)": "#d62728",
    "기타공공기관": "#9467bd",
}

VARIABLES = {
    # ============ 인력 ============
    "임직원수": {
        "column": "임직원수", "label": "임직원 수", "domain": "기관 특성", "category": "기관·인력",
        "unit": "명", "description": "임원+정규직+무기계약직을 합한 임직원 총계",
        "log_allowed": True, "percent": False,
        "question": "임직원 수가 100배 이상 차이 나는 두 기관을 '같은 잣대'로 비교해도 될까?",
    },
    "여성현원": {
        "column": "여성현원", "label": "여성 직원 수", "domain": "기관 특성", "category": "기관·인력",
        "unit": "명", "description": "여성 임직원 현원 합계",
        "log_allowed": True, "percent": False,
        "question": "여성 직원 '수'가 많은 기관이 곧 여성 비율도 높은 기관일까?",
    },
    "여성직원비율": {
        "column": "여성직원비율", "label": "여성 직원 비율", "domain": "기관 특성", "category": "기관·인력",
        "unit": "%", "description": "여성현원 / 임직원수 × 100",
        "log_allowed": False, "percent": True,
        "question": "기관유형별로 여성 비율 차이가 크다면, 그 이유는 업종 특성일까 채용 관행일까?",
    },
    "정규직현원": {
        "column": "정규직현원", "label": "정규직(일반정규직) 현원", "domain": "기관 특성", "category": "기관·인력",
        "unit": "명", "description": "일반정규직 현원 계",
        "log_allowed": True, "percent": False,
        "question": "정규직 현원과 임직원 총계의 차이는 무엇을 의미할까? (무기계약직·임원 비중)",
    },
    "평균근속연수": {
        "column": "평균근속연수", "label": "평균근속연수", "domain": "기관 특성", "category": "기관·인력",
        "unit": "년", "description": "정규직(일반정규직) 평균근속연수",
        "log_allowed": False, "percent": False,
        "question": "근속연수가 긴 기관은 안정적인 조직일까, 순환이 적은 폐쇄적 조직일까?",
    },

    # ============ 채용 ============
    "신규채용자수": {
        "column": "신규채용자수", "label": "신규채용자 수", "domain": "인사 결과", "category": "채용",
        "unit": "명", "description": "일반정규직 총 신규채용 인원",
        "log_allowed": True, "percent": False,
        "question": "신규채용자 수가 많은 기관 = 채용에 적극적인 기관일까, 단순히 규모가 큰 기관일까?",
    },
    "신규채용률": {
        "column": "신규채용률", "label": "신규채용률", "domain": "인사 결과", "category": "채용",
        "unit": "%", "description": "신규채용자수 / 임직원수 × 100",
        "log_allowed": False, "percent": True,
        "question": "신규채용률이 매우 높은 기관은 조직이 급성장하는 걸까, 이직률이 높은 걸까?",
    },
    "여성신규채용자수": {
        "column": "여성신규채용자수", "label": "여성 신규채용자 수", "domain": "인사 결과", "category": "채용",
        "unit": "명", "description": "여성 신규채용 인원",
        "log_allowed": True, "percent": False,
        "question": "여성 신규채용자 수만으로 기관의 채용 형평성을 판단할 수 있을까?",
    },
    "여성신규채용비율": {
        "column": "여성신규채용비율", "label": "여성 신규채용 비율", "domain": "인사 결과", "category": "채용",
        "unit": "%", "description": "여성신규채용자수 / 신규채용자수 × 100",
        "log_allowed": False, "percent": True,
        "question": "기존 여성 직원 비율과 여성 신규채용 비율이 다르다면 어떤 변화가 진행 중일까?",
    },
    "청년신규채용자수": {
        "column": "청년신규채용자수", "label": "청년 신규채용자 수", "domain": "인사 결과", "category": "채용",
        "unit": "명", "description": "청년 신규채용 인원",
        "log_allowed": True, "percent": False,
        "question": "청년채용이 많은 기관은 기관 규모, 지역, 업종 중 무엇과 더 관련 있을까?",
    },
    "장애인신규채용자수": {
        "column": "장애인신규채용자수", "label": "장애인 신규채용자 수", "domain": "인사 결과", "category": "채용",
        "unit": "명", "description": "장애인 신규채용 인원",
        "log_allowed": True, "percent": False,
        "question": "장애인 신규채용자 수가 0인 기관이 많다면, 규모의 문제일까 제도 이행의 문제일까?",
    },

    # ============ 보수 ============
    "직원평균보수": {
        "column": "직원평균보수", "label": "직원 평균보수", "domain": "조직 운영", "category": "보수",
        "unit": "천원", "description": "정규직(일반정규직) 1인당 평균보수액",
        "log_allowed": True, "percent": False,
        "question": "평균보수가 높은 기관은 성과가 좋은 걸까, 정부지원의존도가 높은 걸까?",
    },
    "기본급": {
        "column": "기본급", "label": "기본급", "domain": "조직 운영", "category": "보수",
        "unit": "천원", "description": "정규직(일반정규직) 기본급",
        "log_allowed": True, "percent": False,
        "question": "기본급 비중이 큰 기관과 성과급 비중이 큰 기관, 무엇이 다를까?",
    },
    "고정수당": {
        "column": "고정수당", "label": "고정수당", "domain": "조직 운영", "category": "보수",
        "unit": "천원", "description": "정규직(일반정규직) 고정수당",
        "log_allowed": True, "percent": False,
        "question": "고정수당 규모는 기관유형별로 왜 차이가 날까?",
    },
    "실적수당": {
        "column": "실적수당", "label": "실적수당", "domain": "조직 운영", "category": "보수",
        "unit": "천원", "description": "정규직(일반정규직) 실적수당",
        "log_allowed": True, "percent": False,
        "question": "실적수당이 큰 기관은 기본급 비중이 상대적으로 작을까?",
    },
    "성과상여금": {
        "column": "성과상여금", "label": "성과상여금", "domain": "조직 운영", "category": "보수",
        "unit": "천원", "description": "정규직(일반정규직) 성과상여금",
        "log_allowed": True, "percent": False,
        "question": "성과상여금이 0에 가까운 기관은 성과가 낮은 걸까, 성과급 체계가 다른 걸까?",
    },
    "경영평가성과급": {
        "column": "경영평가성과급", "label": "경영평가 성과급", "domain": "조직 운영", "category": "보수",
        "unit": "천원", "description": "정규직(일반정규직) 경영평가 성과급",
        "log_allowed": True, "percent": False,
        "question": "경영평가 성과급의 연도별 변동은 무엇을 반영할까? (평가등급 변화 가능성)",
    },
    "신입사원초임": {
        "column": "신입사원초임", "label": "신입사원 초임", "domain": "조직 운영", "category": "보수",
        "unit": "천원", "description": "신입사원 초임 합계",
        "log_allowed": True, "percent": False,
        "question": "신입 초임과 평균보수의 격차가 큰 기관은 연공서열형 보수체계를 갖고 있을까?",
    },

    # ============ 임원 ============
    "기관장연봉": {
        "column": "기관장연봉", "label": "기관장 연봉", "domain": "조직 운영", "category": "임원",
        "unit": "천원", "description": "상임기관장 연봉 합계",
        "log_allowed": True, "percent": False,
        "question": "기관장 연봉이 높은 기관은 기관 규모가 큰 걸까, 정치적 위상이 높은 자리일까?",
    },
    "임원평균연봉": {
        "column": "임원평균연봉", "label": "상임임원 평균연봉", "domain": "조직 운영", "category": "임원",
        "unit": "천원", "description": "상임임원 평균보수(연봉)",
        "log_allowed": True, "percent": False,
        "question": "기관장 연봉과 임원 평균연봉의 격차는 기관마다 왜 다를까?",
    },
    "기관장직원보수배율": {
        "column": "기관장직원보수배율", "label": "기관장-직원 보수배율", "domain": "조직 운영", "category": "임원",
        "unit": "배", "description": "기관장연봉 / 직원평균보수",
        "log_allowed": False, "percent": False,
        "question": "보수배율이 유독 크거나 작은 기관은 어떤 특징(규모·업종)을 가질까?",
    },

    # ============ 복지 ============
    "복리후생비": {
        "column": "복리후생비", "label": "복리후생비", "domain": "조직 운영", "category": "복리후생",
        "unit": "천원", "description": "예산상 복리후생비 총계(급여성+비급여성)",
        "log_allowed": True, "percent": False,
        "question": "복리후생비 총액이 큰 기관은 1인당으로 봐도 여전히 클까?",
    },
    "1인당복리후생비": {
        "column": "1인당복리후생비", "label": "1인당 복리후생비", "domain": "조직 운영", "category": "복리후생",
        "unit": "천원/인", "description": "복리후생비 / 임직원수",
        "log_allowed": True, "percent": False,
        "question": "1인당 복리후생비가 높은 기관은 직원 만족도도 높을까? (이 데이터로는 확인 불가)",
    },
    "기관장업무추진비": {
        "column": "기관장업무추진비", "label": "기관장 업무추진비", "domain": "조직 운영", "category": "복리후생",
        "unit": "천원", "description": "기관장 업무추진비 집행금액",
        "log_allowed": True, "percent": False,
        "question": "업무추진비가 연도별로 크게 변동한다면 어떤 요인을 의심해볼 수 있을까?",
    },
    "1인당기관장업무추진비": {
        "column": "1인당기관장업무추진비", "label": "1인당 기관장 업무추진비", "domain": "조직 운영", "category": "복리후생",
        "unit": "천원/인", "description": "기관장업무추진비 / 임직원수",
        "log_allowed": True, "percent": False,
        "question": "기관 규모가 작을수록 1인당 업무추진비가 커 보이는 착시는 없을까?",
    },

    # ============ 일가정양립 ============
    "남성육아휴직사용자수": {
        "column": "남성육아휴직사용자수", "label": "남성 육아휴직 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "남성 육아휴직 사용자 수",
        "log_allowed": True, "percent": False,
        "question": "남성 육아휴직 사용자 수가 늘고 있다면, 제도 변화 때문일까 인식 변화 때문일까?",
    },
    "여성육아휴직사용자수": {
        "column": "여성육아휴직사용자수", "label": "여성 육아휴직 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "여성 육아휴직 사용자 수",
        "log_allowed": True, "percent": False,
        "question": "여성 육아휴직 사용자 수는 여성 직원 수와 비례할까, 아니면 다른 패턴을 보일까?",
    },
    "남성육아휴직사용률": {
        "column": "남성육아휴직사용률", "label": "남성 육아휴직 사용률", "domain": "인사 결과", "category": "일가정양립",
        "unit": "%", "description": "남성 육아휴직 사용률",
        "log_allowed": False, "percent": True,
        "question": "남성 육아휴직 사용률이 높은 기관은 조직문화가 다른 걸까, 남성 직원 비율이 다른 걸까?",
    },
    "여성육아휴직사용률": {
        "column": "여성육아휴직사용률", "label": "여성 육아휴직 사용률", "domain": "인사 결과", "category": "일가정양립",
        "unit": "%", "description": "여성 육아휴직 사용률",
        "log_allowed": False, "percent": True,
        "question": "여성 육아휴직 사용률과 여성 신규채용 비율은 서로 관련이 있을까?",
    },
    "출산휴가사용자수": {
        "column": "출산휴가사용자수", "label": "출산휴가 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "출산휴가 사용자 수",
        "log_allowed": True, "percent": False,
        "question": "출산휴가 사용자 수의 연도별 변화는 조직의 연령·성별 구성 변화를 보여줄까?",
    },
    "배우자출산휴가사용자수": {
        "column": "배우자출산휴가사용자수", "label": "배우자 출산휴가 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "배우자 출산휴가 사용자 수",
        "log_allowed": True, "percent": False,
        "question": "배우자 출산휴가 사용자 수는 남성 육아휴직 사용자 수와 비슷한 패턴을 보일까?",
    },
    "임신기단축근무": {
        "column": "임신기단축근무", "label": "임신기 단축근무 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "임신기 근로시간 단축제도 사용자 수",
        "log_allowed": True, "percent": False,
        "question": "임신기 단축근무 제도를 활용하는 정도는 기관유형별로 왜 다를까?",
    },
    "육아기단축근무": {
        "column": "육아기단축근무", "label": "육아기 단축근무 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "육아기 근로시간 단축제도 사용자 수",
        "log_allowed": True, "percent": False,
        "question": "육아기 단축근무 사용자 수와 육아휴직 사용자 수는 서로 대체 관계일까, 보완 관계일까?",
    },
    "가족돌봄휴가_전체": {
        "column": "가족돌봄휴가_전체", "label": "가족돌봄휴가 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "가족돌봄휴가 사용자 수(전체)",
        "log_allowed": True, "percent": False,
        "question": "가족돌봄휴가 사용자 수는 조직의 평균 연령대와 관련이 있을까?",
    },
    "가족돌봄휴직_전체": {
        "column": "가족돌봄휴직_전체", "label": "가족돌봄휴직 사용자 수", "domain": "인사 결과", "category": "일가정양립",
        "unit": "명", "description": "가족돌봄휴직 사용자 수(전체)",
        "log_allowed": True, "percent": False,
        "question": "가족돌봄휴직 사용자 수가 매우 적은 기관은 제도 이용이 어려운 걸까, 수요가 적은 걸까?",
    },

    # ============ 재정 ============
    "총수입": {
        "column": "총수입", "label": "총수입", "domain": "재정 구조", "category": "재정",
        "unit": "백만원", "description": "고유사업+기금계정 수입합계",
        "log_allowed": True, "percent": False,
        "question": "총수입이 큰 기관이 반드시 자립도가 높은 기관일까?",
    },
    "총지출": {
        "column": "총지출", "label": "총지출", "domain": "재정 구조", "category": "재정",
        "unit": "백만원", "description": "고유사업+기금계정 지출합계",
        "log_allowed": True, "percent": False,
        "question": "총지출이 총수입보다 지속적으로 큰 기관은 어떤 재원으로 그 차이를 메울까?",
    },
    "정부지원수입": {
        "column": "정부지원수입", "label": "정부지원수입", "domain": "재정 구조", "category": "재정",
        "unit": "백만원", "description": "출연금·보조금 등 정부지원수입 소계",
        "log_allowed": True, "percent": False,
        "question": "정부지원수입의 절대 규모와 총수입 대비 비중(의존도) 중 어느 쪽이 더 중요한 정보일까?",
    },
    "사업수입": {
        "column": "사업수입", "label": "사업수입(기타사업수입)", "domain": "재정 구조", "category": "재정",
        "unit": "백만원", "description": "정부지원이 아닌 기타사업수입",
        "log_allowed": True, "percent": False,
        "question": "사업수입이 큰 기관은 시장형 공기업에 가까울까?",
    },
    "정부지원의존도": {
        "column": "정부지원의존도", "label": "정부지원 의존도", "domain": "재정 구조", "category": "재정",
        "unit": "%", "description": "정부지원수입 / 총수입 × 100",
        "log_allowed": False, "percent": True,
        "question": "정부지원의존도가 100%에 가까운 기관은 시장 경쟁 없이 운영되는 기관일까?",
    },
    "1인당총수입": {
        "column": "1인당총수입", "label": "1인당 총수입", "domain": "재정 구조", "category": "재정",
        "unit": "백만원/인", "description": "총수입 / 임직원수",
        "log_allowed": True, "percent": False,
        "question": "1인당 총수입이 매우 큰 기관은 자본집약적 사업(에너지·인프라 등)을 하는 기관일까?",
    },
    "1인당총지출": {
        "column": "1인당총지출", "label": "1인당 총지출", "domain": "재정 구조", "category": "재정",
        "unit": "백만원/인", "description": "총지출 / 임직원수",
        "log_allowed": True, "percent": False,
        "question": "1인당 총지출과 1인당 총수입의 차이는 기관의 재무 건전성을 보여줄까?",
    },
    "1인당사업수입": {
        "column": "1인당사업수입", "label": "1인당 사업수입", "domain": "재정 구조", "category": "재정",
        "unit": "백만원/인", "description": "사업수입 / 임직원수",
        "log_allowed": True, "percent": False,
        "question": "1인당 사업수입이 큰 기관은 직원 보수도 함께 높을까?",
    },
    "수입지출차이": {
        "column": "수입지출차이", "label": "수입-지출 차이", "domain": "재정 구조", "category": "재정",
        "unit": "백만원", "description": "총수입 - 총지출 (양수면 흑자 성격)",
        "log_allowed": False, "percent": False,
        "question": "수지가 마이너스인 기관은 매년 적자인 걸까, 특정 연도의 일시적 현상일까?",
    },

    # ============ 법인세 ============
    "과세표준": {
        "column": "과세표준", "label": "법인세 과세표준", "domain": "재정 구조", "category": "법인세",
        "unit": "천원", "description": "법인세 과세표준액",
        "log_allowed": True, "percent": False,
        "question": "과세표준이 0인 기관이 많다면, 이는 이익이 없다는 뜻일까 비과세 사업 구조 때문일까?",
    },
    "법인세결정세액": {
        "column": "법인세결정세액", "label": "법인세 결정세액", "domain": "재정 구조", "category": "법인세",
        "unit": "천원", "description": "산출세액-세액공제+가산세 반영 최종 결정세액",
        "log_allowed": True, "percent": False,
        "question": "법인세를 내는 공공기관과 안 내는 공공기관의 차이는 무엇일까?",
    },
    "실효법인세율": {
        "column": "실효법인세율", "label": "실효법인세율", "domain": "재정 구조", "category": "법인세",
        "unit": "%", "description": "법인세결정세액 / 과세표준 × 100 (과세표준≤0은 결측)",
        "log_allowed": False, "percent": True,
        "question": "실효세율이 기관마다 다르게 나타난다면 세액공제 제도의 영향일까?",
    },
}


def get_vars_by_domain(domain):
    return {k: v for k, v in VARIABLES.items() if v["domain"] == domain}


def get_vars_by_category(category):
    return {k: v for k, v in VARIABLES.items() if v["category"] == category}


def get_label(key):
    return VARIABLES.get(key, {}).get("label", key)


def get_unit(key):
    return VARIABLES.get(key, {}).get("unit", "")


def get_column(key):
    return VARIABLES.get(key, {}).get("column", key)


def get_question(key):
    return VARIABLES.get(key, {}).get(
        "question", "이 변수의 차이는 기관의 어떤 특성과 관련이 있을까?"
    )


def get_allowed_agg(key):
    """비율(%) 변수는 '평균'만, 그 외 변수는 '평균'과 '합계' 모두 허용한다."""
    meta = VARIABLES.get(key, {})
    if meta.get("percent"):
        return ["평균"]
    return ["평균", "합계"]


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
