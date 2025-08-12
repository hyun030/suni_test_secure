# -*- coding: utf-8 -*-
from config import SK_COLORS

def get_company_color(company_name: str, all_companies: list) -> str:
    """회사별 고유 색상 반환
    - SK에너지: 빨간색
    - GS칼텍스: 청록색
    - HD현대오일뱅크: 파란색
    - S-Oil: 노란색
    """
    name = (company_name or "").strip()

    # 1) 원하는 고정 팔레트(HEX)
    fixed = {
        "SK에너지":        "#E60012",  # Red
        "GS칼텍스":        "#00B7A1",  # Teal
        "HD현대오일뱅크":  "#2F6FFF",  # Blue
        "S-Oil":          "#FFD400",  # Yellow
    }

    # 2) 이름 변형(공백/하이픈/영문) 보정
    norm = name.lower().replace(" ", "").replace("-", "")
    alias_map = {
        "sk에너지": "SK에너지",
        "gscaltex": "GS칼텍스",
        "gs칼텍스": "GS칼텍스",
        "hd현대오일뱅크": "HD현대오일뱅크",
        "현대오일뱅크": "HD현대오일뱅크",
        "soil": "S-Oil",
        "s-oil": "S-Oil",
    }
    canonical = alias_map.get(norm, name)

    # 3) 고정 매핑 우선
    if canonical in fixed:
        return fixed[canonical]

    # 4) 혹시 'SK' 포함된 기타 이름이면 SK 빨강
    if "sk" in norm:
        return fixed["SK에너지"]

    # 5) 그 외 회사는 기존 파스텔 팔레트에서 순환 (fallback)
    competitor_colors = [
        SK_COLORS["competitor_green"],
        SK_COLORS["competitor_blue"],
        SK_COLORS["competitor_yellow"],
        SK_COLORS["competitor_purple"],
        SK_COLORS["competitor_orange"],
        SK_COLORS["competitor_mint"],
    ]
    non_sk = [c for c in all_companies if "SK" not in c]
    try:
        idx = non_sk.index(company_name)
        return competitor_colors[idx % len(competitor_colors)]
    except ValueError:
        return SK_COLORS["competitor"]
