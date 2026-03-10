import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import io
import json
import math

# 💡 한국 표준시(KST) 기준 시간 반환 함수
def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="TOmBOy's INOUT")

# 커스텀 CSS 주입 (디자인 통일 및 레이아웃 정돈)
st.markdown("""
    <style>
    /* 💡 스트림릿 기본 UI 요소를 완벽하게 숨기기 (메뉴, 푸터, Manage app 버튼) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    .stDeployButton {display: none !important;}
    
    /* 💡 표 우측 상단에 나타나는 기본 툴바(흰색 빈 박스 버그) 완전 숨김 처리 */
    [data-testid="stElementToolbar"] {display: none !important;}

    [data-testid="stAppViewContainer"] { background-color: #2b323c; }
    .main .block-container { padding-top: 1rem; max-width: 98%; }
    h1, h2, h3, p, span { color: #ffffff !important; }
    
    /* 검색 패널 컨테이너 */
    .search-panel-container {
        background-color: #353b48;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #4a5568;
        margin-bottom: 20px;
    }
    
    /* 버튼 공통 스타일 */
    div.stButton > button {
        border-radius: 4px !important;
        font-weight: bold !important;
        padding: 0px 10px !important;
    }
    
    /* Primary 버튼 파란색 커스텀 */
    button[kind="primary"] {
        background-color: #4e8cff !important;
        border-color: #4e8cff !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #3b76e5 !important;
        border-color: #3b76e5 !important;
        color: white !important;
    }
    
    /* SQL 다운로드 생성완료 버튼 (Secondary 타입으로 분리하여 빨간색 완벽 고정 적용!) */
    div[data-testid="stDownloadButton"] button[kind="secondary"] {
        background-color: #ef4444 !important; /* 빨간색(Red) */
        border-color: #ef4444 !important;
        color: white !important;
    }
    div[data-testid="stDownloadButton"] button[kind="secondary"]:hover {
        background-color: #dc2626 !important; /* 마우스 오버시 진한 빨간색 */
        border-color: #dc2626 !important;
        color: white !important;
    }
    
    /* 기간/월별 검색버튼(Form 내부 Submit 버튼) 청록색 커스텀 */
    [data-testid="stFormSubmitButton"] > button {
        background-color: #009688 !important; /* 청록색 */
        border-color: #009688 !important;
        color: white !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #00796B !important; /* 마우스 오버시 진한 청록색 */
        border-color: #00796B !important;
        color: white !important;
    }
    
    /* 결산버튼 초록색 커스텀을 위한 예외처리 */
    div:nth-child(4) > div[data-testid="stButton"] > button {
        background-color: #8ba966 !important;
        border-color: #8ba966 !important;
    }

    /* 메인 데이터 테이블 스타일 */
    .custom-table-container { width: 100%; margin-top: 5px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
    .table-title-box { background-color: #2b323c; padding: 10px 15px; border-top: 2px solid #555; border-bottom: none; display: flex; align-items: center; justify-content: space-between; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }
    .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; }
    .custom-table th { text-align: center; color: white; font-weight: bold; padding: 10px 6px; }
    .custom-table tr:nth-child(even) { background-color: #f8f9fa; }
    .custom-table tr:hover { background-color: #e2e6ea; }
    
    /* 인쇄용 가짜 상하단 여백 (웹 화면에서는 보이지 않도록 숨김) */
    .print-fake-margin { display: none !important; }
    
    /* 인쇄 전용 타이틀 숨김 처리 (웹 화면에서는 안보이게 분리) */
    .print-only-title { display: none !important; }
    
    /* 테이블 구역별 색상 */
    .th-base { background-color: #353b48; color: white; }
    .th-in { background-color: #3b5b88; color: white; } 
    .th-out { background-color: #b8860b; color: white; }
    
    /* 텍스트 색상 강조 */
    .txt-in-bold { color: #1e3a8a !important; font-weight: bold; }
    .txt-in { color: #1e3a8a !important; }
    .txt-out-bold { color: #9a3412 !important; font-weight: bold; }
    .txt-out { color: #9a3412 !important; }
    .txt-green { color: #059669 !important; font-weight: bold; }
    .txt-purple { color: #7e22ce !important; font-weight: bold; }
    .txt-gray { color: #475569 !important; }
    .txt-black { color: #1e293b !important; }
    .tc { text-align: center; } .tl { text-
