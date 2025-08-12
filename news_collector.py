# -*- coding: utf-8 -*-
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional

class GoogleNewsCollector:
    """Google News API를 활용한 정유 관련 뉴스 수집기"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.search_url = "https://google.serper.dev/news"
        
        # 정유 관련 키워드 설정
        self.company_keywords = ["SK에너지", "S-Oil", "HD현대오일뱅크", "GS칼텍스"]
        self.industry_keywords = ["정유", "정유업계", "정유사", "석유화학", "석유화학사"]
        self.business_keywords = ["영업이익", "실적", "수익성", "투자", "매출", "손실", "정제마진"]
        
    def collect_news(self, query: str, num_results: int = 100) -> pd.DataFrame:
        """Google News API를 통해 뉴스 수집"""
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }
        
        # 검색 쿼리 정리 (특수문자 제거 및 단순화)
        clean_query = query.replace('"', '').replace('(', '').replace(')', '')
        
        payload = {
            "q": clean_query,
            "num": min(num_results, 100),  # API 제한
            "gl": "kr",  # 한국 지역 설정
            "hl": "ko"   # 한국어 결과
        }
        
        try:
            response = requests.post(self.search_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 400:
                st.error(f"API 요청 실패: 검색 쿼리를 단순화해보세요.")
                return pd.DataFrame()
            elif response.status_code != 200:
                st.error(f"API 요청 실패: {response.status_code}")
                return pd.DataFrame()
            
            data = response.json()
            news_data = data.get("news", [])
            if not news_data:
                st.warning("⚠️ 검색 결과가 없습니다.")
                return pd.DataFrame()
            
            # DataFrame 변환 및 전처리
            df = pd.DataFrame(news_data)
            df = self._preprocess_news_data(df)
            
            return df
            
        except requests.exceptions.RequestException as e:
            st.error(f"API 요청 실패: {str(e)}")
            return pd.DataFrame()
        except Exception as e:
            st.error(f"뉴스 수집 중 오류 발생: {str(e)}")
            return pd.DataFrame()
    
    def _preprocess_news_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """뉴스 데이터 전처리"""
        if df.empty:
            return df
        
        # 필요한 컬럼만 선택
        required_columns = ["title", "link", "date", "snippet"]
        available_columns = [col for col in required_columns if col in df.columns]
        
        if not available_columns:
            return df
        
        df = df[available_columns].copy()
        
        # 컬럼명 한글화
        column_mapping = {
            "title": "제목",
            "link": "URL",
            "date": "날짜",
            "snippet": "요약"
        }
        df = df.rename(columns=column_mapping)
        
        # 날짜 전처리 (URL에서 자동 추출)
        if "날짜" in df.columns:
            df["날짜"] = df.apply(self._extract_date_from_url, axis=1)
        
        # 요약 컬럼이 없으면 제목으로 대체
        if "요약" not in df.columns:
            df["요약"] = df["제목"]
        
        # URL 컬럼이 없으면 빈 문자열로 설정
        if "URL" not in df.columns:
            df["URL"] = ""
        
        # 회사 컬럼 추가 (제목에서 회사명 추출)
        df["회사"] = df["제목"].apply(self._extract_company_from_title)
        
        # 날짜순으로 정렬 (최신순)
        if "날짜" in df.columns:
            df = df.sort_values("날짜", ascending=False).reset_index(drop=True)
        else:
            df = df.reset_index(drop=True)
        
        return df
    
    def _extract_date_from_url(self, row):
        """URL에서 날짜 정보를 자동으로 추출"""
        url = str(row.get("URL", ""))
        date = str(row.get("날짜", ""))
        
        # 1. 기존 날짜가 유효하면 사용
        if date and date != "None" and date != "nan":
            try:
                parsed_date = pd.to_datetime(date, errors="coerce")
                if pd.notna(parsed_date):
                    return parsed_date.strftime("%Y-%m-%d")
            except:
                pass
        
        # 2. URL에서 날짜 패턴 찾기
        import re
        
        # 다양한 날짜 패턴
        patterns = [
            r'/(\d{4})/(\d{2})/(\d{2})/',  # /2024/08/12/
            r'(\d{4})-(\d{2})-(\d{2})',    # 2024-08-12
            r'(\d{4})\.(\d{2})\.(\d{2})',  # 2024.08.12
            r'(\d{4})_(\d{2})_(\d{2})',    # 2024_08_12
            r'(\d{4})(\d{2})(\d{2})',      # 20240812
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                if len(match.groups()) == 3:
                    year, month, day = match.groups()
                    try:
                        return f"{year}-{month}-{day}"
                    except:
                        continue
        
        return "날짜 정보 없음"
    
    def _extract_company_from_title(self, title: str) -> str:
        """제목에서 회사명을 추출하는 메서드"""
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
    
    def generate_search_queries(self) -> List[str]:
        """정유 관련 검색 쿼리 생성"""
        queries = [
            "SK에너지 정유",
            "S-Oil 정유",
            "HD현대오일뱅크 정유",
            "GS칼텍스 정유",
            "정유업계 SK에너지",
            "석유화학 SK에너지",
            "정유사 영업이익",
            "정유사 실적"
        ]
        return queries

def create_google_news_tab():
    """Google News 수집 탭 생성"""
    st.subheader("🔍 정유 업계 관련 Google 뉴스 수집")
    st.info("💡 Google News API를 통해 정유 관련 최신 뉴스를 수집하고 분석합니다.")
    
    # 분석 상태 표시
    if hasattr(st.session_state, 'google_news_data') and st.session_state.google_news_data is not None:
        st.success(f"✅ Google News 수집 완료! 총 {len(st.session_state.google_news_data)}개 뉴스")
    
    # config에서 API 키 자동 가져오기
    try:
        import config
        api_key = config.GOOGLE_NEWS_API_KEY
        st.success("✅ API 키가 자동으로 설정되었습니다!")
    except:
        st.error("❌ config.py에서 API 키를 찾을 수 없습니다.")
        return
    
    if api_key:
        st.session_state.google_news_api_key = api_key
        
        # 검색 설정
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input(
                "검색 쿼리",
                value='SK에너지 S-Oil HD현대오일뱅크 GS칼텍스 정유 석유화학',
                help="검색어를 공백으로 구분하여 입력하세요 (예: SK에너지 정유)"
            )
        
        with col2:
            num_results = st.number_input(
                "수집할 뉴스 개수",
                min_value=10,
                max_value=200,
                value=100,
                step=10
            )
        
        # 미리 정의된 검색 쿼리 선택
        st.markdown("**📋 추천 검색 쿼리**")
        collector = GoogleNewsCollector(api_key)
        recommended_queries = collector.generate_search_queries()
        
        selected_query = st.selectbox(
            "추천 쿼리 선택",
            recommended_queries,
            help="미리 정의된 검색 쿼리 중에서 선택하거나 직접 입력할 수 있습니다"
        )
        
        if st.button("🔍 뉴스 수집 시작", type="primary"):
            if not search_query.strip():
                st.error("검색 쿼리를 입력해주세요.")
                return
            
            with st.spinner("🔄 뉴스 수집 및 분석 진행 중..."):
                try:
                    collector = GoogleNewsCollector(api_key)
                    news_df = collector.collect_news(search_query, num_results)
                    
                    if not news_df.empty:
                        # AI 인사이트 자동 생성 (백그라운드에서)
                        try:
                            from insight.openai_api import OpenAIInsightGenerator
                            import config
                            
                            # OpenAI 인사이트 생성기 초기화
                            openai = OpenAIInsightGenerator(config.OPENAI_API_KEY)
                            
                            # 뉴스 인사이트 생성 (자동)
                            insight = openai.generate_news_insight(news_df)
                            
                            if insight:
                                st.session_state.google_news_insight = insight
                            else:
                                st.error("❌ AI 인사이트 생성에 실패했습니다.")
                                
                        except Exception as e:
                            st.error(f"❌ AI 인사이트 생성 중 오류 발생: {str(e)}")
                        
                        # 세션에 데이터 저장
                        st.session_state.google_news_data = news_df
                        st.session_state.google_news_query = search_query
                        st.session_state.google_news_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        
                        st.success(f"✅ 뉴스 수집 및 AI 분석 완료! 총 {len(news_df)}개 뉴스")
                    else:
                        st.error("❌ 뉴스 수집에 실패했습니다. API 키와 검색어를 확인해주세요.")
                        
                except Exception as e:
                    st.error(f"❌ 뉴스 수집 중 오류 발생: {str(e)}")

    # 수집된 뉴스 목록 표시 (데이터가 있을 때만)
    if hasattr(st.session_state, 'google_news_data') and st.session_state.google_news_data is not None:
        st.markdown("---")
        st.subheader("📊 수집된 뉴스 목록")
        
        # 수집 정보 표시
        if hasattr(st.session_state, 'google_news_timestamp'):
            st.info(f"📅 수집 시간: {st.session_state.google_news_timestamp}")
        if hasattr(st.session_state, 'google_news_query'):
            st.info(f"🔍 검색 쿼리: {st.session_state.google_news_query}")
        
        # 회사 컬럼이 있으면 표시에 포함
        display_columns = ["제목", "URL", "날짜", "요약"]
        if "회사" in st.session_state.google_news_data.columns:
            display_columns.insert(1, "회사")
        
        st.dataframe(
            st.session_state.google_news_data[display_columns],
            use_container_width=True,
            column_config={
                "제목": st.column_config.TextColumn("제목", width="large"),
                "회사": st.column_config.TextColumn("회사", width="medium") if "회사" in display_columns else None,
                "URL": st.column_config.LinkColumn("🔗 링크", width="medium"),
                "날짜": st.column_config.TextColumn("날짜", width="small"),
                "요약": st.column_config.TextColumn("요약", width="large")
            }
        )
        
        # AI 인사이트 표시
        if hasattr(st.session_state, 'google_news_insight') and st.session_state.google_news_insight:
            st.markdown("---")
            st.subheader("📋 AI 종합 분석 리포트")
            st.markdown(st.session_state.google_news_insight)
