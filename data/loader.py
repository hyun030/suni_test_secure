# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Dict, List, Union

import pandas as pd
import requests
import streamlit as st
from dateutil import parser

# 프로젝트 설정 파일 import
import config


class DartAPICollector:
    """DART API를 통해 재무 데이터를 수집하는 클래스"""
    def __init__(self, api_key):
        self.api_key = api_key
        self.source_tracking = {}
        self.company_name_mapping = config.COMPANY_NAME_MAPPING
        self.stock_code_mapping = config.STOCK_CODE_MAPPING

    def get_corp_code_enhanced(self, company_name):
        url = f"https://opendart.fss.or.kr/api/corpCode.xml?crtfc_key={self.api_key}"
        search_names = self.company_name_mapping.get(company_name, [company_name])
        
        try:
            res = requests.get(url)
            with zipfile.ZipFile(io.BytesIO(res.content)) as z:
                xml_file = z.open(z.namelist()[0])
                tree = ET.parse(xml_file)
                root = tree.getroot()
            
            all_companies = []
            for corp in root.findall("list"):
                corp_name_elem = corp.find("corp_name")
                corp_code_elem = corp.find("corp_code")
                stock_code_elem = corp.find("stock_code")
                
                if corp_name_elem is not None and corp_code_elem is not None:
                    all_companies.append({
                        'name': corp_name_elem.text,
                        'code': corp_code_elem.text,
                        'stock_code': stock_code_elem.text.strip() if stock_code_elem is not None and stock_code_elem.text else None
                    })
            
            for search_name in search_names:
                if search_name.isdigit(): # 종목코드로 검색
                    for company in all_companies:
                        if company['stock_code'] == search_name:
                            return company['code']
                
                for company in all_companies: # 정확히 일치
                    if company['name'] == search_name:
                        return company['code']
            
            return None
        except Exception as e:
            st.error(f"회사 코드 조회 오류: {e}")
            return None

    def get_financial_statement(self, corp_code, bsns_year, reprt_code, fs_div="CFS"):
        url = "https://opendart.fss.or.kr/api/fnlttSinglAcntAll.json"
        params = {
            "crtfc_key": self.api_key, "corp_code": corp_code, "bsns_year": bsns_year,
            "reprt_code": reprt_code, "fs_div": fs_div
        }
        try:
            res = requests.get(url, params=params).json()
            if res.get("status") == "000" and "list" in res:
                df = pd.DataFrame(res["list"])
                df["보고서구분"] = reprt_code
                return df
            return pd.DataFrame()
        except Exception:
            return pd.DataFrame()

    def get_company_financials_auto(self, company_name, bsns_year):
        corp_code = self.get_corp_code_enhanced(company_name)
        if not corp_code:
            st.warning(f"DART에서 '{company_name}'에 대한 고유코드를 찾을 수 없습니다.")
            return None

        report_codes = ["11011", "11014", "11012", "11013"] # 년간 -> 3분기 -> 반기 -> 1분기 순
        for report_code in report_codes:
            df = self.get_financial_statement(corp_code, str(bsns_year), report_code)
            if not df.empty:
                rcept_no = self._get_rcept_no(corp_code, str(bsns_year), report_code)
                self._save_source_info(company_name, corp_code, report_code, str(bsns_year), rcept_no)
                return df
        return None
    
    def _get_rcept_no(self, corp_code, bsns_year, report_code):
        # 실제 API를 통해 가장 최신 보고서의 접수번호를 가져오는 로직 (샘플)
        # 현재는 시간 관계상 간단한 형태로 대체
        return f"{corp_code}_{bsns_year}_{report_code}_sample"

    def _save_source_info(self, company_name, corp_code, report_code, bsns_year, rcept_no):
        report_type_map = {
            "11011": "사업보고서", "11014": "3분기보고서",
            "11012": "반기보고서", "11013": "1분기보고서"
        }
        self.source_tracking[company_name] = {
            'company_code': corp_code, 'report_type': report_type_map.get(report_code, "재무제표"),
            'year': bsns_year, 'rcept_no': rcept_no,
            'dart_url': f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcept_no}"
        }


class QuarterlyDataCollector:
    """분기별 재무 데이터를 수집하는 클래스 (Q4=연간-(Q1+Q2+Q3))"""
    def __init__(self, dart_collector: DartAPICollector):
        self.dart_collector = dart_collector
        # DART API 보고서 코드 (모두 '누적' 값)
        self.report_codes = {
            "Q1": "11013",  # 1분기보고서(누적)
            "Q2": "11012",  # 반기보고서(누적)
            "Q3": "11014",  # 3분기보고서(누적)
            "Q4": "11011",  # 사업보고서(연간, 누적)
        }
        # 라벨(설명) - Q4는 연간(사업)임을 명확히
        self.quarter_names = {
            "Q1": "1분기보고서",
            "Q2": "반기보고서",
            "Q3": "3분기보고서",
            "Q4": "연간(사업보고서)",
        }

    def _extract_raw_amounts(self, df, column='thstrm_amount'):
        """지정 컬럼에서 원시값(원 단위)을 dict로 반환
           column: 'thstrm_amount'(당기금액) 또는 'thstrm_add_amount'(당기누계)"""
        def find_amount(keywords):
            for keyword in keywords:
                rows = df[df['account_nm'].str.contains(keyword, case=False, na=False)]
                if not rows.empty:
                    try:
                        raw = rows.iloc[0].get(column, '0')
                        val = str(raw).replace(',', '')
                        # 괄호 음수
                        if '(' in val and ')' in val:
                            val = f"-{val.strip('()')}"
                        if val.strip() in ['-', '']:
                            return 0.0
                        return float(val)
                    except Exception:
                        continue
            return 0.0

        return {
            '매출액':     find_amount(['매출액', 'revenue', 'sales']),
            '매출원가':   find_amount(['매출원가', 'cost of sales']),
            '매출총이익': find_amount(['매출총이익', 'gross profit', '총이익']),
            '영업이익':   find_amount(['영업이익', 'operating profit', '영업손익']),
            '당기순이익': find_amount(['당기순이익', 'net income', '순이익']),
            '판관비':     find_amount(['판매비와관리비', '판관비', 'selling and administrative']),
            '판매비':     find_amount(['판매비', 'selling expenses']),
            '관리비':     find_amount(['관리비', 'administrative expenses']),
            
            # 고정비 관련 항목들
            '감가상각비': find_amount(['감가상각비', 'depreciation', 'depreciation and amortization']),
            '인건비':     find_amount(['인건비', 'personnel costs', 'employee benefits', '급여', '임금']),
            '임차료':     find_amount(['임차료', 'rent expense', 'rent']),
            '관리비':     find_amount(['관리비', 'administrative expenses']),
            
            # 변동비 관련 항목들
            '판매수수료': find_amount(['판매수수료', 'sales commission', 'commission']),
            '운반배송비': find_amount(['운반배송비', 'shipping cost', 'delivery cost']),
            '포장비':     find_amount(['포장비', 'packaging cost']),
            '외주가공비': find_amount(['외주가공비', 'outsourcing cost']),
            '판촉비':     find_amount(['판촉비', 'promotional cost']),
            '샘플비':     find_amount(['샘플비', 'sample cost']),
            '소모품비':   find_amount(['소모품비', 'consumables']),
            '동력비':     find_amount(['동력비', 'power cost', '전력비']),
            '원재료비':   find_amount(['원재료비', 'raw material cost']),
        }


    def _build_display_row(self, company_name, year, label, raw, report_name=None):
        """표시용(조원/억원 & 비율) 행 생성: raw는 '원' 단위 당기(or 연간) dict"""
        row = {'회사': company_name, '연도': year, '분기': label}
        if report_name:
            row['보고서구분'] = report_name

        # 금액 변환
        if raw.get('매출액'):     row['매출액(조원)']     = raw['매출액']     / 1_000_000_000_000
        if raw.get('매출원가'):   row['매출원가(조원)']   = raw['매출원가']   / 1_000_000_000_000
        if raw.get('매출총이익'): row['매출총이익(조원)'] = raw['매출총이익'] / 1_000_000_000_000
        if raw.get('영업이익'):   row['영업이익(억원)']   = raw['영업이익']   / 100_000_000
        if raw.get('당기순이익'): row['당기순이익(억원)'] = raw['당기순이익'] / 100_000_000
        if raw.get('판관비'):     row['판관비(억원)']     = raw['판관비']     / 100_000_000

        # 비율(분모: 매출액)
        sales = raw.get('매출액', 0)
        if sales:
            if '영업이익'   in raw: row['영업이익률(%)']   = (raw['영업이익']   / sales) * 100
            if '매출총이익' in raw: row['매출총이익률(%)'] = (raw['매출총이익'] / sales) * 100
            if '당기순이익' in raw: row['순이익률(%)']     = (raw['당기순이익'] / sales) * 100
            if '매출원가'   in raw: row['매출원가율(%)']   = (raw['매출원가']   / sales) * 100
        return row

    def collect_quarterly_data(self, company_name, year=2024):
        import pandas as pd

        corp_code = self.dart_collector.get_corp_code_enhanced(company_name)
        if not corp_code:
            return pd.DataFrame()

        st.info(f"🔍 {company_name} {year}년 분기별 데이터(당기/연간) 산출 중...")

        # (1) 보고서별 원시값 수집: 당기(curr) / 누계(cum) 둘 다 준비
        curr, cum = {}, {}
        for q, code in self.report_codes.items():
            df = self.dart_collector.get_financial_statement(corp_code, str(year), code)
            if df.empty:
                st.warning(f"⚠️ {self.quarter_names[q]} 데이터 없음")
                continue
            # 당기금액(분기 금액)
            curr[q] = self._extract_raw_amounts(df, column='thstrm_amount')
            # 누적금액(없으면 당기로 대체)
            if 'thstrm_add_amount' in df.columns:
                cum[q] = self._extract_raw_amounts(df, column='thstrm_add_amount')
            else:
                cum[q] = curr[q]

        if not curr:
            st.error("❌ 분기 데이터 수집 실패")
            return pd.DataFrame()

        # (2) dict 합/차 유틸
        def add_dicts(*dicts):
            keys = set().union(*[d.keys() for d in dicts if d])
            return {k: sum(float(d.get(k, 0) or 0) for d in dicts if d) for k in keys}

        def sub_dict(a, b):
            keys = set(a.keys()) | set(b.keys())
            return {k: float(a.get(k, 0) or 0) - float(b.get(k, 0) or 0) for k in keys}

        # (3) 당기 산출: Q1~Q3는 '당기금액'을 그대로, Q4만 연산
        q1 = curr.get('Q1', {})
        q2 = curr.get('Q2', {})  # ✅ 더 이상 빼지 않음
        q3 = curr.get('Q3', {})  # ✅ 더 이상 빼지 않음

        # ✅ Q4(당기) = 연간(당기) − (Q1당기 + Q2당기 + Q3당기)
        if 'Q4' in curr:
            q4 = sub_dict(curr['Q4'], add_dicts(q1, q2, q3))
        else:
            q4 = {}

        # (디버그) 확인
        if 'Q4' in curr:
            st.caption(
                "🧪 산식 확인 | "
                f"연간(당기) 매출={curr['Q4'].get('매출액')} / "
                f"Q1={q1.get('매출액')} / Q2={q2.get('매출액')} / Q3={q3.get('매출액')} / "
                f"Q4(연간-합계)={q4.get('매출액')}"
            )

        # (4) 표 생성: Q1~Q4(당기) + 연간(누적)
        rows = []
        if q1: rows.append(self._build_display_row(company_name, year, f"{year}Q1", q1, "1분기(당기)"))
        if q2: rows.append(self._build_display_row(company_name, year, f"{year}Q2", q2, "2분기(당기)"))
        if q3: rows.append(self._build_display_row(company_name, year, f"{year}Q3", q3, "3분기(당기)"))
        if q4: rows.append(self._build_display_row(company_name, year, f"{year}Q4", q4, "4분기(당기)"))  # 10/01~12/31
        # 연간 행은 누적(cum['Q4'])로 표시 (없으면 당기와 동일)
        if 'Q4' in cum:
            rows.append(self._build_display_row(company_name, year, f"{year} 연간", cum['Q4'], "연간(사업보고서)"))

        return pd.DataFrame(rows)

    def _extract_key_metrics(self, df, quarter, year):
        # 분기 표시를 더 명확하게 (예: 2024Q1, 2024Q2 등)
        quarter_display = f"{year}{quarter}"
        metrics = {'분기': quarter_display}
        
        def find_amount(keywords):
            for keyword in keywords:
                rows = df[df['account_nm'].str.contains(keyword, case=False, na=False)]
                if not rows.empty:
                    try:
                        return float(str(rows.iloc[0]['thstrm_amount']).replace(',', '').replace('-', '0'))
                    except:
                        continue
            return 0

        # 핵심 재무지표 추출
        revenue = find_amount(['매출액', 'revenue', 'sales'])
        cost_of_sales = find_amount(['매출원가', 'cost of sales', '매출원가'])
        gross_profit = find_amount(['매출총이익', 'gross profit', '총이익'])
        operating_profit = find_amount(['영업이익', 'operating profit', '영업손익'])
        net_income = find_amount(['당기순이익', 'net income', '순이익'])
        selling_expenses = find_amount(['판매비', 'selling expenses'])
        administrative_expenses = find_amount(['관리비', 'administrative expenses'])
        sg_and_a = find_amount(['판매비와관리비', '판관비', 'selling and administrative'])

        # 금액 단위 변환 및 저장
        if revenue > 0:
            metrics['매출액(조원)'] = revenue / 1_000_000_000_000
        if cost_of_sales > 0:
            metrics['매출원가(조원)'] = cost_of_sales / 1_000_000_000_000
        if gross_profit > 0:
            metrics['매출총이익(조원)'] = gross_profit / 1_000_000_000_000
        if operating_profit > 0:
            metrics['영업이익(억원)'] = operating_profit / 100_000_000
        if net_income > 0:
            metrics['당기순이익(억원)'] = net_income / 100_000_000
        if selling_expenses > 0:
            metrics['판매비(억원)'] = selling_expenses / 100_000_000
        if administrative_expenses > 0:
            metrics['관리비(억원)'] = administrative_expenses / 100_000_000
        if sg_and_a > 0:
            metrics['판관비(억원)'] = sg_and_a / 100_000_000

        # 비율 계산
        if '매출액(조원)' in metrics and '영업이익(억원)' in metrics and metrics['매출액(조원)'] > 0:
            metrics['영업이익률(%)'] = (metrics['영업이익(억원)'] * 100) / (metrics['매출액(조원)'] * 10_000)
        
        if '매출액(조원)' in metrics and '매출총이익(조원)' in metrics and metrics['매출액(조원)'] > 0:
            metrics['매출총이익률(%)'] = (metrics['매출총이익(조원)'] / metrics['매출액(조원)']) * 100
        
        if '매출액(조원)' in metrics and '당기순이익(억원)' in metrics and metrics['매출액(조원)'] > 0:
            metrics['순이익률(%)'] = (metrics['당기순이익(억원)'] * 100) / (metrics['매출액(조원)'] * 10_000)
        
        if '매출액(조원)' in metrics and '매출원가(조원)' in metrics and metrics['매출액(조원)'] > 0:
            metrics['매출원가율(%)'] = (metrics['매출원가(조원)'] / metrics['매출액(조원)']) * 100
        
        return metrics if len(metrics) > 1 else None
