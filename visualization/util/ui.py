# util/ui.py
# -*- coding: utf-8 -*-
import streamlit as st
import re, textwrap

def _render_ai_html(raw: str):
    if not raw:
        return ""
    s = raw.strip()
    s = re.sub(r"^```(?:html|HTML)?\s*", "", s, flags=re.MULTILINE)
    s = re.sub(r"\s*```$", "", s, flags=re.MULTILINE)
    s = textwrap.dedent(s)
    s = "\n".join(line.lstrip() if line.lstrip().startswith("<") else line
                  for line in s.splitlines())
    return s

def render_insight_as_cards(text: str):
    # 👉 여기에 지금 쓰고 있는 당신의 함수 본문 그대로 붙여넣기
    # (질문에 올린 버전 그대로 복사)
    ...
