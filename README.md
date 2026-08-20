# 공공기관 데이터 탐색 대시보드

공기업정책학과 석사과정 계량분석 수업용 대시보드입니다.
파일별·주제별 열람 구조가 아니라, **기관×연도 통합 분석 패널**을 기반으로
분포 → 변수 관계 → 기관 비교를 탐색하는 구조로 설계했습니다.
강의실 대형화면(1920×1080)에서 세로 스크롤 없이 한 화면에 보이도록 구성했습니다.

원본 Excel 파일을 그대로 사용하며 별도의 전처리·parquet 변환 과정이 없습니다.
`@st.cache_data`로 세션 중에만 메모리에 캐싱합니다.

## 1. 환경 설치

```bash
pip install -r requirements.txt
```

## 2. 원본 Excel 위치

`data/` 폴더에 다음 원본 Excel 파일을 그대로 넣어주세요. (파일명 동일하게 유지)

```
수입지출현황.xlsx
법인세정보.xlsx
임직원수현황.xlsx
직원평균보수현황.xlsx
임원연봉.xlsx
신규채용현황.xlsx
복리후생비.xlsx
기관장업무추진비.xlsx
그밖의_복리후생제도_등의_운영현황.xlsx
일가정_양립_지원제도_운영현황.xlsx
```

## 3. 실행

```bash
streamlit run app.py
```

## 화면 구조 (탭)

```text
1. 종합현황     전체 규모·구조를 KPI 6개 + 그래프 6개로 한 화면에 요약
2. 분포 탐색    변수 하나를 선택해 히스토그램·박스플롯·상하위 10개 기관 확인
3. 변수 관계    서로 다른 데이터셋의 두 변수를 산점도로 연결 (추천 관계 15개 제공)
4. 기관 비교    기관 하나를 선택해 전체/동일유형/동일부처 평균과 비교
5. 주제별 상세  원자료 세부 구조를 보고 싶을 때 사용하는 보조 영역 (서브탭 5개)
```

모든 탭은 화면 상단의 **종속형 필터**(연도 → 기관유형 → 주무부처 → 기관명)를 공유합니다.
상위 필터를 바꾸면 하위 필터는 자동으로 "전체"로 초기화됩니다.

## 프로젝트 구조

```
app.py                 메인 앱 (st.tabs 기반 단일 페이지)
requirements.txt
data/                  원본 Excel (그대로 두고 수정하지 않음)
utils/
  data.py              원본 Excel 로딩·정제·통합 분석 패널 생성 (build_analysis_panel)
  metadata.py          VARIABLE_META / QUESTION_BANK / RELATIONSHIP_PRESETS
  filters.py           종속형 공통 필터 (기관유형 → 주무부처 → 기관명)
  stats.py             기술통계 함수
  charts.py             Plotly 재사용 차트 함수 (관계 산점도 포함)
  constants.py         공통 상수, 안내 문구, 차트 높이
```

## 통합 분석 패널 (`build_analysis_panel`)

기관명+연도를 key로 여러 데이터셋을 outer merge하여 만듭니다.
**값이 없으면 절대 0으로 대체하지 않고 NaN을 유지**합니다. 주요 변수:

- 인력: `total_workforce`, `fill_rate_pct`, `female_ratio_pct`
- 채용: `new_hire_rate_pct`, `youth_hire_ratio_pct`, `female_hire_ratio_pct`, `disabled_hire_ratio_pct`
- 보수: `employee_avg_pay`, `starting_pay`, `avg_tenure_months`, `executive_pay_multiple`
- 복지: `welfare_per_capita`
- 일가정양립: `parental_leave_rate_pct`, `male_parental_leave_ratio_pct`
- 재정: `total_revenue`, `business_revenue`, `gov_dependency_pct`, `revenue_per_employee`, `labor_cost_ratio_pct`

**참고**: 원자료에 "사업수입" 소계 항목이 별도로 없어 `business_revenue`는
`기타사업수입` 항목으로 대체했습니다 (`utils/metadata.py`의 `source`에 명시).
직장어린이집 운영비(`daycare_expense` 등)는 원자료 구조가 연도별 wide 포맷이 아닌
레코드형 구조라 이번 버전에서는 패널에 포함하지 않았습니다.

## 사용하지 않는 기능 (의도적 제외)

OLS/로짓 회귀 결과표, p-value 자동 해석, 통계적 유의성 자동 판정은 제공하지 않습니다.
산점도의 추세선은 단순 선형 참고선이며 회귀모형 추정 결과가 아닙니다.

## 데이터 해석상 주의사항

1. 모든 데이터는 **기관 단위 집계자료**이며 개인 수준 결과로 해석할 수 없습니다.
2. 상관관계·추세선은 통계적 연관성을 보여줄 뿐 **인과관계를 의미하지 않습니다.**
3. 청년·여성·장애인 채용은 중복 가능하므로 합산하여 100%로 표현하지 않습니다.
4. 총액과 1인당 지표는 기관 규모 차이를 고려해 구분해서 봐야 합니다.
5. 2026년 자료는 연중 공시자료 또는 잠정값일 수 있습니다.
