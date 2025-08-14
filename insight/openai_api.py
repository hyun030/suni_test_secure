# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import config

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

class OpenAIInsightGenerator:
    """OpenAI GPT-4o를 사용하여 분석 인사이트를 생성하는 클래스"""
    def __init__(self, api_key):
        if OPENAI_AVAILABLE and api_key:
            try:
                self.client = OpenAI(api_key=api_key)
                self.model = "gpt-4o"
            except Exception as e:
                st.error(f"OpenAI 모델 초기화 실패: {e}")
                self.client = None
        else:
            self.client = None

    def generate_financial_insight(self, financial_data):
        """재무데이터 → 경쟁사 분석 인사이트"""
        if not self.client:
            return "OpenAI API를 사용할 수 없습니다. API 키를 확인해주세요."
        
        try:
            # 재무데이터를 텍스트로 변환
            data_str = financial_data.to_string() if hasattr(financial_data, 'to_string') else str(financial_data)
            
            prompt = f"""
다음은 SK에너지 중심의 재무데이터입니다:
숫자 표기: 소수점 둘째 자리까지, 단위 명시(%, 원/배럴, 원/톤 등)
데이터 결측 시: "데이터 없음" 명시

{data_str}

당신은 SK에너지 전략기획팀 수석 분석가입니다.
아래 1~6번 항목에 따라 **정확한 수치근거**와 **실행 가능한 제안**을 제시하세요.
각 섹션 마지막에는 반드시 구분선(---)을 넣으세요.

## 1. 📊 SK에너지 현재 재무 상황 분석
- 최근 12개 분기 수익성(영업이익률, 순이익률) 변화와 원인(매출/원가/판관비/고정비/변동비 기여도) 분해
- 경쟁사 대비 수익구조의 강·약점 요약(핵심 지표 3~5개: 영업이익률, 매출원가율, 판관비율, 공헌이익률 등)
- 생산량 변화, 설비가동률 추정, 단위당 영업이익(원/배럴 또는 원/톤) 비교
---

## 2. 🔍 경쟁사 대비 사업 경쟁력 분석(더 깊게)
- **원가 구조 분해:** 인건비·감가상각비(고정비), 동력비·원재료비(변동비) 지표를 각 사별로 비교하고, 항목별 격차 원인을 설명
- **포트폴리오/스케일:** 정유(정제), 석유화학, 트레이딩/마케팅 등 사업 포트폴리오와 생산능력(용량)·규모의 경제 효과 비교
- **가격/마진 요인:** 정제마진, 제품 믹스(경질/중질·수송/석화), 스프레드 변동이 각 사 마진에 미친 영향
- **CAPEX·효율화 동향:** 최근 1~2년 설비 투자·에너지 효율화·디지털/자동화 투자 사례가 마진·원가에 미친 효과 추정
- **경쟁우위/약점 도출:** 각 항목별로 SK의 우위/약점을 "지표·수치·원인" 3요소로 정리(불릿 5개 내)
---

## 3. 🧩 전략적 시사점 및 내부 개선 방향(실행 초점)
- **기간 구분:** 단기(3~6개월)·중기(6~18개월)·장기(18개월+)로 나눠 전략 제시
- **전략별 구성:** (i) 실행 과제, (ii) 필요 자원(인력/투자), (iii) 예상 정량효과(매출/원가/EBITDA 변화 범위), (iv) 리스크·가정
- **우선순위 기준:** 효과(High/Mid/Low) × 난이도(High/Mid/Low) × 리드타임(개월) 3축 평가로 우선순위 도출
- **운영 레버:** 에너지 사용 최적화, 유지보수 주기/정비 전략, 원료 스위칭, 제품 믹스 전환, 상각기간/비용 재배치 등 구체 과제 명시
---

## 4. 📌 리스크 요인 및 감시 항목(리스크 레지스터)
- **분류:** 재무·운영·시장·정책/규제·공급망/안전·기술 6개 범주로 리스크 도출
- **정량화:** 각 리스크별 발생 가능성(낮음/중간/높음)·영향도(낮음/중간/높음)·노출 지표(정제마진, 유가, 환율 등) 기입
- **선행지표/트리거:** 어떤 수치가 어떤 임계값을 넘으면 경보로 볼지(예: 정제마진 X$/bbl 이하 2분기 지속 시)
- **즉시 대응책:** 회피/완화/전가/수용 중 선택과 구체 액션(원료/재고/헤지/정비 스케줄 조정 등)
---

## 5. DART 공시 기반 갭 분석 및 추세 전략(표 + 템플릿 둘 다 필수)
[입력 데이터]
대상: SK에너지, HD현대오일뱅크, GS칼텍스, S-Oil
기간: 최근 12개 분기
항목: 매출액, 매출원가, 영업이익, 고정비(인건비/감가상각비), 변동비(동력비/원재료비), 생산량

[분석 지표]
영업이익률, 매출원가율
고정비율(인건비율, 감가상각비율)
변동비율(동력비율, 원재료비율)
공헌이익률(매출-변동비)/매출
단위당 영업이익(원/배럴, 원/톤)

[갭 계산]
현재 갭 = SK지표 - 경쟁사평균
추세 = 최근 4분기 갭 변화율
위험도 = 우위→축소(高) / 열위→확대(中) / 열위→축소(기회)

### 5-1) 📋 갭 분석 표(반드시 표로 출력, 행/열 합치지 말 것)
| 지표 | SK 값 | 경쟁사 평균 | 격차(SK-평균) | 최근 4분기 추세(%) | 위험도 | 해석 |
|---|---:|---:|---:|---:|---|---|
| 예: 영업이익률(%) |  |  |  |  |  |  |
| 예: 매출원가율(%) |  |  |  |  |  |  |
| 예: 인건비율(%) |  |  |  |  |  |  |
| 예: 감가상각비율(%) |  |  |  |  |  |  |
| 예: 동력비율(%) |  |  |  |  |  |  |
| 예: 원재료비율(%) |  |  |  |  |  |  |
| 예: 공헌이익률(%) |  |  |  |  |  |  |
| 예: 단위당 영업이익(원/배럴 또는 원/톤) |  |  |  |  |  |  |

### 5-2) 📊 경쟁사 비교 분석(불릿 템플릿, 반드시 그대로 — 각 항목은 **반드시 새 줄**에서 시작하고 **항목 사이에 빈 줄 1개**를 넣을 것)
-🟢 우위지표: [지표] SK[값] vs 경쟁사[값] (격차+[차이], 추세[%])
-🔴 열위지표: [지표] SK[값] vs 경쟁사[값] (격차-[차이], 추세[%])

### 5-3) ⚠️ 위험신호(불릿 템플릿, 반드시 그대로)
-긴급: [우위→급속축소 지표]
-취약: [열위→지속확대 지표]

### 5-4) 📈 전략방안(지표별 미니 액션플랜)
[지표명]
-상황: "SK에너지는 ○○하므로"
-조치: "○○가 필요하다"
-목표: [시점]까지 격차 [현재]→[목표]

### 5-5) 🎯 우선순위(불릿 템플릿, 반드시 그대로)
1. [긴급지표] - [목표] - [방안]
2. [기회지표] - [목표] - [방안]
---

## 6. 🚀 향후 6개월 내 실질적 액션 플랜
- 실행 과제 3~5개: 담당/일정/마일스톤/KPI(수치 목표) 포함
- KPI 재설정 필요 여부와 근거(최근 4분기 추세·경쟁사 비교) 명시
---

필수 지침
- 모든 주장에는 **수치·추세·비율** 등 데이터 근거를 명시
- 표와 불릿 템플릿을 **동시에** 출력(둘 중 하나라도 누락 금지)
- 줄바꿈/표 구조를 변경하지 말 것(행·열 합치기 금지)
"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 SK에너지의 수석 재무 분석가입니다. 정확하고 실용적인 분석을 제공해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            return response.choices[0].message.content
        
        except Exception as e:
            error_msg = str(e)
            st.error(f"🔍 **상세 오류 정보**: {error_msg}")
            
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return f"""⚠️ **OpenAI API 할당량/속도 제한 오류**

**상세 오류**: {error_msg}

**가능한 원인:**
1. **분당 요청 제한**: 너무 빠른 속도로 API 호출 (분당 3-10회 제한)
2. **일일 사용량 제한**: 일일 사용량 한도 초과
3. **계정 상태**: 결제 정보 미등록 또는 신용카드 한도 초과
4. **API 키 문제**: 잘못된 API 키 사용

**즉시 확인사항:**
• OpenAI 대시보드 → Usage & Billing에서 현재 사용량 확인
• 결제 정보가 올바르게 등록되어 있는지 확인
• 신용카드 한도나 잔액 확인

**해결 방법:**
1. **잠시 대기**: 1-2분 후 다시 시도
2. **사용량 확인**: OpenAI 대시보드에서 현재 사용량/한도 확인
3. **결제 정보 재확인**: Billing → Payment method에서 카드 정보 재입력"""
            elif "401" in error_msg or "invalid" in error_msg.lower():
                return f"""❌ **OpenAI API 키 인증 오류**

**상세 오류**: {error_msg}

**해결 방법:**
1. OpenAI 대시보드에서 새로운 API 키 생성
2. Streamlit secrets 또는 환경변수에 올바른 API 키 설정
3. API 키가 올바르게 복사되었는지 확인"""
            else:
                return f"AI 인사이트 생성 중 오류가 발생했습니다: {e}"

    def generate_news_insight(self, news_df: pd.DataFrame):
        """여러 경쟁사 뉴스를 종합하여 하나의 통합된 벤치마킹 보고서를 생성합니다."""
        if self.client is None: return "OpenAI API를 사용할 수 없습니다."
        if news_df is None or news_df.empty: return "분석할 뉴스 데이터가 없습니다."

        # 회사 컬럼이 없으면 제목에서 회사명을 추출하거나 기본값 사용
        if '회사' not in news_df.columns:
            # 제목에서 회사명 추출 시도
            news_df = news_df.copy()
            news_df['회사'] = news_df['제목'].apply(self._extract_company_from_title)
        
        # SK 관련 뉴스 제외하고 경쟁사 뉴스만 선택
        competitor_news = news_df[~news_df['회사'].astype(str).str.contains("SK", na=False)].head(10)
        
        if competitor_news.empty:
            return "분석할 경쟁사의 최신 뉴스가 없습니다."

        news_data_str = ""
        for i, row in enumerate(competitor_news.iterrows(), 1):
            title = row[1].get('제목', '제목 없음')
            company = row[1].get('회사', '회사 불명')
            news_data_str += f"기사 {i} ({company}): {title}\n"

        prompt = f"""
        당신은 SK에너지의 수석 전략 분석가입니다. 아래 제공된 경쟁사들의 최신 뉴스 목록을 종합적으로 분석하여,
        우리 회사가 즉시 검토해볼 만한 핵심적인 벤치마킹 아이디어를 도출하는 것이 당신의 임무입니다.
        개별 기사를 단순히 요약하지 말고, 여러 기사에서 나타나는 공통적인 트렌드나 중요한 단일 활동을 꿰뚫어 보세요.

        [분석 대상 최신 경쟁사 뉴스 목록]
        {news_data_str}

        [보고서 작성 지침]
        1.  **통합 분석 요약 (Executive Summary):**
            - 뉴스들을 관통하는 가장 중요한 시장 트렌드는 무엇입니까? (예: 친환경 투자 가속화, 원가 절감 노력 등)
            - 우리 회사가 가장 시급하게 주목해야 할 경쟁사의 활동은 무엇이며, 그 이유는 무엇입니까?

        2.  **핵심 벤치마킹 아이디어 TOP 2:**
            - 가장 가치가 높다고 판단되는 아이디어 두 가지를 선정하여 아래 형식으로 구체적으로 제시해주세요.

            ---
            ### 💡 아이디어 1: [벤치마킹 활동 요약, 예: 바이오 항공유 신사업 진출]
            - **관련 기사:** [분석 대상 뉴스 목록에서 가장 관련 있는 기사 번호를 1~2개 언급]
            - **벤치마킹 포인트:** [경쟁사가 무엇을, 왜, 어떻게 하고 있는지 구체적으로 서술]
            - **우리 회사 적용 방안:** [이 아이디어를 우리 회사 상황에 맞게 어떻게 적용할 수 있을지 구체적인 실행 계획 제안]
            - **예상 손익 영향:** [매출, 원가, 비용 관점에서 어떤 긍정적/부정적 영향이 있을지 예측. (예: 초기 투자비(고정비) 증가, 장기적 신규 매출 발생)]
            - **적용 가능성:** [높음/중간/낮음]

            ### 💡 아이디어 2: [두 번째 벤치마킹 활동 요약]
            - **관련 기사:**
            - **벤치마킹 포인트:**
            - **우리 회사 적용 방안:**
            - **예상 손익 영향:**
            - **적용 가능성:**
            ---

        3.  **기타 주목할 만한 활동:**
            - 위 TOP 2 외에 추가로 주목할 만한 경쟁사의 활동이 있다면 간략하게 언급해주세요.

        최종 결과물은 바로 경영진에게 보고할 수 있는 수준의 명확하고 논리적인 보고서 형식이어야 합니다.
        """
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 SK에너지의 수석 전략 분석가입니다. 정확하고 실용적인 벤치마킹 분석을 제공해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            st.error(f"🔍 **상세 오류 정보**: {error_msg}")
            
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return f"""⚠️ **OpenAI API 할당량/속도 제한 오류**

**상세 오류**: {error_msg}

**가능한 원인:**
1. **분당 요청 제한**: 너무 빠른 속도로 API 호출 (분당 3-10회 제한)
2. **일일 사용량 제한**: 일일 사용량 한도 초과
3. **계정 상태**: 결제 정보 미등록 또는 신용카드 한도 초과
4. **API 키 문제**: 잘못된 API 키 사용

**즉시 확인사항:**
• OpenAI 대시보드 → Usage & Billing에서 현재 사용량 확인
• 결제 정보가 올바르게 등록되어 있는지 확인
• 신용카드 한도나 잔액 확인

**해결 방법:**
1. **잠시 대기**: 1-2분 후 다시 시도
2. **사용량 확인**: OpenAI 대시보드에서 현재 사용량/한도 확인
3. **결제 정보 재확인**: Billing → Payment method에서 카드 정보 재입력"""
            elif "401" in error_msg or "invalid" in error_msg.lower():
                return f"""❌ **OpenAI API 키 인증 오류**

**상세 오류**: {error_msg}

**해결 방법:**
1. OpenAI 대시보드에서 새로운 API 키 생성
2. Streamlit secrets 또는 환경변수에 올바른 API 키 설정
3. API 키가 올바르게 복사되었는지 확인"""
            else:
                st.error(f"AI 뉴스 인사이트 생성 중 오류가 발생했습니다: {e}")
                return "AI 인사이트 생성에 실패했습니다."

    def _extract_company_from_title(self, title: str) -> str:
        """제목에서 회사명을 추출하는 헬퍼 메서드"""
        if not title:
            return "회사 불명"
        
        # 주요 정유사 회사명 매칭
        company_keywords = {
            "SK에너지": ["SK에너지", "SK에너", "SK"],
            "S-Oil": ["S-Oil", "에쓰오일", "에쓰-오일"],
            "HD현대오일뱅크": ["HD현대오일뱅크", "현대오일뱅크", "현대오일"],
            "GS칼텍스": ["GS칼텍스", "GS칼", "칼텍스"]
        }
        
        title_lower = title.lower()
        for company, keywords in company_keywords.items():
            if any(keyword.lower() in title_lower for keyword in keywords):
                return company
        
        # 회사명이 명확하지 않은 경우
        return "기타"

    def generate_integrated_insight(self, fin_insight_text: str, news_insight_text: str):
        """다트 기반 인사이트, 뉴스 벤치마킹 인사이트를 종합하여 통합 인사이트를 생성합니다."""
        if not self.client:
            return "OpenAI API를 사용할 수 없습니다. API 키를 확인해주세요."
        
        fin_insight_text = fin_insight_text or "재무 인사이트 입력 없음"
        news_insight_text = news_insight_text or "뉴스/벤치마킹 인사이트 입력 없음"

        prompt = f"""
당신은 SK에너지 전략기획팀의 애널리스트입니다.  
아래 두 가지 자료를 종합하여 **통합 인사이트와 손익 개선 전략**을 도출하세요.

[자료 1: 다트 기반 재무 인사이트] 
{fin_insight_text}

[자료 2: 뉴스 기반 벤치마킹 인사이트]
{news_insight_text}

[목표]  
- 재무 지표를 중심으로 회사의 현황과 문제점을 진단  
- 뉴스 인사이트를 활용해 경쟁사 벤치마킹 포인트 및 시장 기회 도출  
- 두 자료를 융합하여 실행 가능한 손익 개선 전략 제시

[출력 항목]
1. **종합 현황 진단**  
   - 재무 인사이트 기반 현 재무상태  
   - 뉴스 기반 시장 동향 및 경쟁사 주요 움직임  
   - 두 자료를 결합한 시장 내 포지션 평가

2. **핵심 문제점 & 기회요인**  
   - 재무 데이터에서 도출된 주요 문제  
   - 뉴스에서 파악된 기회 및 위협  
   - 두 자료를 융합한 전략적 시사점

3. **손익 개선 전략 제안**  
   - 단기(3~6개월): 즉시 실행 가능 전략, KPI, 예상 재무 효과  
   - 중장기(6~24개월): 구조 개선·사업 재편 전략, KPI, 예상 효과

4. **핵심 손익개선 포인트 요약**  
   | 구분 | 개선방안 | 예상 효과(정량) |
   |------|----------|----------------|
   | 매출 증대 | … | … |
   | 원가 절감 | … | … |
   | 효율성 향상 | … | … |
   | 리스크 최소화 | … | … |

[지침]
- 분석 근거에 반드시 재무 수치·비율·추세를 포함  
- 뉴스 인사이트는 실행 아이디어·벤치마킹 보조로 활용  
- 모호한 표현 대신 구체적 실행안 제시
"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "당신은 SK에너지 전략기획팀의 수석 애널리스트입니다. 정확하고 실용적인 통합 분석을 제공해주세요."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=4000,
                temperature=0.3
            )
            return response.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            st.error(f"🔍 **상세 오류 정보**: {error_msg}")
            
            if "429" in error_msg or "quota" in error_msg.lower() or "rate limit" in error_msg.lower():
                return f"""⚠️ **OpenAI API 할당량/속도 제한 오류**

**상세 오류**: {error_msg}

**가능한 원인:**
1. **분당 요청 제한**: 너무 빠른 속도로 API 호출 (분당 3-10회 제한)
2. **일일 사용량 제한**: 일일 사용량 한도 초과
3. **계정 상태**: 결제 정보 미등록 또는 신용카드 한도 초과
4. **API 키 문제**: 잘못된 API 키 사용

**즉시 확인사항:**
• OpenAI 대시보드 → Usage & Billing에서 현재 사용량 확인
• 결제 정보가 올바르게 등록되어 있는지 확인
• 신용카드 한도나 잔액 확인

**해결 방법:**
1. **잠시 대기**: 1-2분 후 다시 시도
2. **사용량 확인**: OpenAI 대시보드에서 현재 사용량/한도 확인
3. **결제 정보 재확인**: Billing → Payment method에서 카드 정보 재입력"""
            elif "401" in error_msg or "invalid" in error_msg.lower():
                return f"""❌ **OpenAI API 키 인증 오류**

**상세 오류**: {error_msg}

**해결 방법:**
1. OpenAI 대시보드에서 새로운 API 키 생성
2. Streamlit secrets 또는 환경변수에 올바른 API 키 설정
3. API 키가 올바르게 복사되었는지 확인"""
            else:
                return f"통합 인사이트 생성 중 오류가 발생했습니다: {e}"
