import streamlit as st
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io
import math
import re
from datetime import datetime, timedelta, timezone

# --- [페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="TOmBOy94 English")

# --- [사용자 정의 디자인 (CSS)] ---
st.markdown("""
    <style>
    /* 1. 배경 설정: 짙은 다크그린 */
    [data-testid="stAppViewContainer"],
    div[data-testid="stDialog"] > div,
    div[role="dialog"] > div {
        background-color: #224343 !important;
    }
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 2. 글자색 화이트 강제화 */
    h1, h2, h3, h4, h5, h6, p, span, label, summary, b, strong {
        color: #FFFFFF !important;
    }
   
    /* 팝업창(Dialog) 제목 */
    #새-항목-추가,
    #항목-수정-및-삭제,
    div[data-testid="stDialog"] h2,
    div[role="dialog"] h2,
    section[role="dialog"] h2 {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 3. 일반 입력창 모바일 최적화 및 눈알 제거 */
    .stTextInput input {
        height: 50px !important;
        font-size: 1.2rem !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 10px !important;
    }
    
    /* 비밀번호 입력창 눈알 아이콘 제거 */
    div[data-testid="stTextInput"] button {
        display: none !important;
    }

    /* ★ 4. 컨텐츠 행(Row) 호버 효과 - 배경 꽉 채우기 및 상하 여백 밸런스 완벽 보정 ★ */
    div.element-container:has(.row-marker) {
        width: 100% !important;
        min-width: 100% !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 16px 10px !important; 
        border-radius: 0px !important; 
        margin-bottom: 0px !important;
        border-bottom: 1px dotted rgba(255, 255, 255, 0.2) !important; 
        width: 100% !important; 
        min-width: 100% !important; 
        flex: 1 1 100% !important;
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important; 
        overflow: visible !important; 
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        background-color: rgba(26, 47, 47, 0.9) !important;
    }
    
    /* 텍스트 쳐짐 완벽 해결 */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) > div[data-testid="column"] {
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important; 
        padding: 0 !important;
        margin: 0 !important;
        overflow: visible !important;
    }
    
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div.element-container,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div.stMarkdown,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) p {
        display: block !important; 
        margin: 0 !important;
        padding: 0 !important;
        line-height: 1.5 !important; 
        width: 100% !important;
    }

    /* 5. 상단 분류 리스트(Radio) 알약 형태 */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 10px 12px !important;
        padding-top: 10px !important;
        padding-bottom: 5px !important;
    }
   
    div[data-testid="stRadio"] label > div:first-of-type {
        display: none !important;
    }
   
    div[data-testid="stRadio"] label {
        cursor: pointer !important;
        margin: 0 !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        padding: 6px 18px !important;
        border-radius: 50px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.3s ease !important;
    }
   
    div[data-testid="stRadio"] label:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: #FFD700 !important;
    }
   
    div[data-testid="stRadio"] label p {
        color: #FFFFFF !important;
        font-size: clamp(0.9rem, 1.2vw, 1.3rem) !important;
        font-weight: 800 !important;
        white-space: nowrap !important;
    }
   
    div[data-testid="stRadio"] label:has(input:checked),
    div[data-testid="stRadio"] label:has(div[aria-checked="true"]) {
        background-color: #FFD700 !important;
        border-color: #FFD700 !important;
    }
   
    div[data-testid="stRadio"] label:has(input:checked) p,
    div[data-testid="stRadio"] label:has(div[aria-checked="true"]) p {
        color: #224343 !important;
    }

    /* 6. 버튼 스타일 */
    button, div.stDownloadButton > button {
        border-radius: 50px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 900 !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }
    button[kind="primary"] p {
        color: #224343 !important;
        font-size: clamp(0.75rem, 1.1vw, 1.15rem) !important;
        font-weight: 900 !important;
    }
    button[kind="secondary"], div.stDownloadButton > button {
        background-color: transparent !important;
        border: 2px solid #FFFFFF !important;
        color: #FFFFFF !important;
    }
    button[kind="secondary"] p, div.stDownloadButton > button p {
        font-size: clamp(0.75rem, 1.1vw, 1.15rem) !important;
        font-weight: 900 !important;
    }

    /* 7. 수정 버튼: 투명 연필 아이콘 */
    button[kind="tertiary"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        margin: 0 !important;
        min-height: 0 !important;
        min-width: 40px !important;
        box-shadow: none !important;
        display: flex !important;
        align-items: center !important;
    }
    button[kind="tertiary"] p {
        font-size: 1.6rem !important;
        margin: 0 !important;
        padding: 0 !important;
        line-height: normal !important;
        transition: transform 0.2s ease !important;
    }
    button[kind="tertiary"]:hover p {
        transform: scale(1.2) !important;
    }

    /* 8. 헤더 라벨 및 텍스트 시인성 */
    .header-label { 
        font-size: clamp(1.0rem, 1.4vw, 1.5rem) !important; 
        font-weight: 800 !important; 
        color: #FFFFFF !important; 
        white-space: nowrap !important;
    }
   
    /* 텍스트를 위로 살짝 띄워주는 시각적 보정 (margin-bottom: 2px) */
    /* 단어-문장 크기 기존 1.8em에서 10% 확대 (1.98em) */
    .word-text { font-size: 1.98em; font-weight: bold; color: #FFD700 !important; word-break: keep-all; display: inline-block !important; margin-bottom: 2px !important; }
    .mean-text { font-size: 1.3em; word-break: keep-all; display: inline-block !important; margin-bottom: 2px !important; }
    .cat-text-bold { font-weight: bold !important; font-size: 0.95rem; display: inline-block !important; margin-bottom: 2px !important; }
   
    /* 13. 로그인 PIN 입력창 사이트 테마 맞춤형 디자인 (Dark Green & Gold) */
    #login-pin-container div[data-testid="stForm"] {
        background-color: rgba(0, 0, 0, 0.2) !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        padding: 40px 30px !important;
        border-radius: 25px !important;
        max-width: 400px !important;
        margin: 60px auto !important;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4) !important;
    }
    
    #login-pin-container h3 {
        color: #FFD700 !important; 
        text-align: center !important;
        font-size: 1.5rem !important;
        font-weight: 900 !important;
        margin-bottom: 30px !important;
    }
    
    #login-pin-container input[aria-label^="pin"] {
        height: 75px !important;
        font-size: 2.5rem !important;
        text-align: center !important;
        border-radius: 15px !important;
        border: 2px solid rgba(255, 255, 255, 0.2) !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: #FFFFFF !important;
        padding: 0 !important;
        caret-color: #FFD700 !important;
        -webkit-text-security: disc;
    }
    
    #login-pin-container input[aria-label^="pin"]:focus {
        border-color: #FFD700 !important; 
        background-color: rgba(255, 255, 255, 0.1) !important;
        box-shadow: 0 0 15px rgba(255, 215, 0, 0.3) !important;
    }
    
    /* 취소 버튼 (Secondary 스타일) */
    #login-pin-container div[data-testid="column"]:nth-child(1) button {
        background-color: transparent !important;
        border: 2px solid #FFFFFF !important;
        border-radius: 50px !important;
        height: 50px !important;
    }
    #login-pin-container div[data-testid="column"]:nth-child(1) button p {
        color: #FFFFFF !important;
        font-weight: 800 !important;
    }
    
    /* 인증하기 버튼 (Primary 골드 스타일) */
    #login-pin-container div[data-testid="column"]:nth-child(2) button {
        background-color: #FFD700 !important;
        border: none !important;
        border-radius: 50px !important;
        height: 50px !important;
    }
    #login-pin-container div[data-testid="column"]:nth-child(2) button p {
        color: #224343 !important;
        font-weight: 900 !important;
    }
    #login-pin-container div[data-testid="column"]:nth-child(2) button:hover {
        transform: scale(1.05);
        box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
    }

    /* 9. Num.ENG 레이아웃 최적화 및 가로 크기 제한 */
    div[data-testid="stTextInput"]:has(input[aria-label="Num.ENG :"]) {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 8px !important;
        max-width: 350px !important; 
    }
    div[data-testid="stTextInput"]:has(input[aria-label="Num.ENG :"]) label p {
        font-weight: 900 !important;
        font-size: clamp(0.8rem, 1.1vw, 1.1rem) !important; 
        margin: 0 !important;
        white-space: nowrap !important;
    }
    input[aria-label="Num.ENG :"] {
        font-size: clamp(1.0rem, 1.4vw, 1.5rem) !important;
        min-width: 80px !important;
    }
    
    /* 전체 검색창 이모지 한 줄 정렬 CSS */
    div[data-testid="stTextInput"]:has(input[placeholder*="검색"]) {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 5px !important;
    }
    div[data-testid="stTextInput"]:has(input[placeholder*="검색"]) label {
        margin-bottom: 0 !important;
        display: flex;
        align-items: center;
    }
    div[data-testid="stTextInput"]:has(input[placeholder*="검색"]) label p {
        font-size: 1.2rem !important;
        margin: 0 !important;
    }
   
    /* 10. Num.ENG 결과물과 X 버튼 한 줄 배치 (Flexbox) */
    div[data-testid="stHorizontalBlock"]:has(.num-result) {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        justify-content: flex-start !important;
        gap: 15px !important;
        padding-top: 5px !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.num-result) > div {
        width: auto !important; 
        flex: 0 1 auto !important;
    }
    
    /* 결과물 텍스트 스타일 */
    .num-result { 
        color: #FFD700 !important; 
        font-weight: bold; 
        font-size: clamp(1.6rem, 2.2vw, 2.4rem) !important; 
        margin: 0 !important;
        line-height: 1.1;
        white-space: nowrap !important;
    }
    
    /* ❌ 버튼 전용 스타일 */
    div[data-testid="stHorizontalBlock"]:has(.num-result) button {
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        padding: 0 !important;
        margin: 0 !important;
        width: auto !important;
        height: auto !important;
        min-width: unset !important;
        margin-top: 5px !important; 
    }
    div[data-testid="stHorizontalBlock"]:has(.num-result) button p {
        font-size: 1.2rem !important; 
        margin: 0 !important;
        color: rgba(255, 255, 255, 0.6) !important;
        transition: transform 0.2s ease, color 0.2s ease !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.num-result) button:hover p {
        color: rgba(255, 255, 255, 1.0) !important;
        transform: scale(1.2) !important;
    }

    /* 11. 모바일 레이아웃 강제 교정 */
    @media screen and (max-width: 768px) {
        h1 { font-size: clamp(1.6rem, 2.5vw, 2.5rem) !important; }
        
        div[data-testid="stHorizontalBlock"]:has(.row-marker) {
            display: flex !important;
            flex-direction: row !important;
            padding: 12px 8px !important; /* 모바일에서도 넉넉한 패딩 적용 */
            width: 100% !important;
            gap: 8px !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:nth-child(1) { width: 18% !important; min-width: 55px; } 
        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:nth-child(2) { width: 38% !important; } 
        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:nth-child(3) { width: 34% !important; } 
        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:last-child { width: 10% !important; min-width: 40px; text-align: right; } 

        .word-text { font-size: 1.21rem !important; }
        .mean-text { font-size: 0.9rem !important; }
        
        button { padding: 0.5rem 0.8rem !important; }
    }

    /* ★ 12. 컨텐츠(행) 마우스 오버 시 '단어-문장' 열만 10% 확대 (스무스 효과) ★ */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) .word-text {
        transition: transform 0.2s ease !important;
        transform-origin: left center !important; /* 좌측 기준 확대 (글자가 왼쪽으로 넘어가지 않음) */
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover .word-text {
        transform: scale(1.1) !important; /* 10% 확대 */
        z-index: 10 !important; /* 커진 글씨가 다른 요소를 가리지 않도록 최상단 배치 */
    }
    </style>
    """, unsafe_allow_html=True)

# --- [보안 설정 및 Google Sheets 연결] ---
LOGIN_PASSWORD = "0315"

@st.cache_resource
def init_connection():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
        return gspread.authorize(creds)
    except Exception:
        return None

def get_sheet():
    client = init_connection()
    return client.open("English_Sentences").sheet1 if client else None

def load_dataframe(sheet):
    if sheet:
        for _ in range(3):
            try:
                data = sheet.get_all_values()
                if not data: return pd.DataFrame(columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])
                rows = [row + [""] * (6 - len(row)) for row in data[1:]]
                df = pd.DataFrame(rows, columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])
                for col in df.columns: df[col] = df[col].astype(str).str.strip()
                return df
            except Exception:
                time.sleep(1)
    
    #Fallback 임시 데이터
    return pd.DataFrame([
        ['구동사', 'Hang out', '시간 보내다/놀다', '행아웃', '', ''],
        ['여행', 'Keep the change.', '잔돈은 가지세요.', '킵 더 체인지', '', ''],
        ['독해(구분)', 'so that', '~하기 위해서 / 그래서 ~하도록', '', '', ''],
        ['TOM사용영어', 'The tracking number is missing.', '송장번호 누락', '더 트래킹 넘버 이즈 미씽', '', '']
    ], columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])

# --- [다이얼로그 설정] ---
@st.dialog("새 항목 추가")
def add_dialog(unique_cats):
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        selected_cat = c1.selectbox("기존 분류", ["(새로 입력)"] + unique_cats)
        new_cat = c2.text_input("새 분류 입력")
        word_sent = st.text_input("단어-문장")
        c3, c4 = st.columns(2)
        mean = c3.text_input("해석")
        pron = c4.text_input("발음")
        m1 = st.text_input("메모1")
        m2 = st.text_input("메모2")
        if st.form_submit_button("저장하기", use_container_width=True, type="primary"):
            final_cat = new_cat.strip() if new_cat.strip() else (selected_cat if selected_cat != "(새로 입력)" else "")
            if word_sent:
                sheet = get_sheet()
                if sheet:
                    sheet.append_row([final_cat, word_sent, mean, pron, m1, m2])
                    st.success("저장 완료!")
                    time.sleep(1)
                    st.rerun()

@st.dialog("항목 수정 및 삭제")
def edit_dialog(idx, row_data, unique_cats):
    safe_cats = unique_cats if unique_cats else ["(없음)"]
    cat_val = row_data.get('분류', '')
    cat_index = safe_cats.index(cat_val) if cat_val in safe_cats else 0
    
    with st.form(f"edit_{idx}"):
        c1, c2 = st.columns(2)
        edit_cat = c1.selectbox("분류", safe_cats, index=cat_index)
        new_cat = c2.text_input("분류 직접 수정")
        word_sent = st.text_input("단어-문장", value=row_data.get('단어-문장', ''))
        c3, c4 = st.columns(2)
        mean = c3.text_input("해석", value=row_data.get('해석', ''))
        pron = c4.text_input("발음", value=row_data.get('발음', ''))
        m1 = st.text_input("메모1", value=row_data.get('메모1', ''))
        m2 = st.text_input("메모2", value=row_data.get('메모2', ''))
        b1, b2 = st.columns(2)
        if b1.form_submit_button("💾 저장", use_container_width=True, type="primary"):
            final_cat = new_cat.strip() if new_cat.strip() else edit_cat
            sheet = get_sheet()
            if sheet:
                sheet.update(f"A{idx+2}:F{idx+2}", [[final_cat, word_sent, mean, pron, m1, m2]])
                st.rerun()
        if b2.form_submit_button("🗑️ 삭제", use_container_width=True):
            sheet = get_sheet()
            if sheet:
                sheet.delete_rows(idx + 2)
                st.rerun()

# --- [세션 상태 관리] ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = st.query_params.get("auth") == "true"
if "logging_in" not in st.session_state:
    st.session_state.logging_in = False
if 'sort_order' not in st.session_state: st.session_state.sort_order = 'None'
if 'current_cat' not in st.session_state: st.session_state.current_cat = "🔀 랜덤 10"
if 'num_input' not in st.session_state: st.session_state.num_input = ""
if 'active_search' not in st.session_state: st.session_state.active_search = ""
if 'search_input' not in st.session_state: st.session_state.search_input = ""
if 'is_simple' not in st.session_state: st.session_state.is_simple = False

# 콜백 함수들
def format_num_input():
    cleaned = re.sub(r'[^0-9]', '', str(st.session_state.num_input))
    st.session_state.num_input = f"{int(cleaned):,}" if cleaned else ""

def clear_num_input():
    st.session_state.num_input = ""

def handle_search():
    st.session_state.active_search = st.session_state.search_input.strip()
    st.session_state.search_input = ""

def clear_search():
    st.session_state.active_search = ""

def num_to_eng(num):
    if num == 0: return "zero"
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    scales = ["", "thousand", "million", "billion", "trillion"]
    def _convert(n):
        if n < 20: return ones[n]
        if n < 100: return tens[n // 10] + ("-" + ones[n % 10] if n % 10 != 0 else "")
        if n < 1000: return ones[n // 100] + " hundred" + (" " + _convert(n % 100) if n % 100 != 0 else "")
        for i in range(1, len(scales)):
            if n < 1000 ** (i + 1): return _convert(n // (1000 ** i)) + " " + scales[i] + (" " + _convert(n % (1000 ** i)) if n % (1000 ** i) != 0 else "")
        return str(n)
    return _convert(num).strip()

# --- [메인 로직] ---

# ★ 1. 로그인 전용 화면 (사이트 테마 맞춤형 PIN 입력창) ★
if not st.session_state.authenticated and st.session_state.logging_in:
    st.markdown('<div id="login-pin-container">', unsafe_allow_html=True)
    with st.form("login_form", clear_on_submit=True):
        st.markdown("<h3>비밀번호 4자리 입력</h3>", unsafe_allow_html=True)
        c1, c2, c3, c4 = st.columns(4)
        pwd1 = c1.text_input("pin1", max_chars=1, type="password", label_visibility="collapsed")
        pwd2 = c2.text_input("pin2", max_chars=1, type="password", label_visibility="collapsed")
        pwd3 = c3.text_input("pin3", max_chars=1, type="password", label_visibility="collapsed")
        pwd4 = c4.text_input("pin4", max_chars=1, type="password", label_visibility="collapsed")
        st.markdown("<div style='height:15px;'></div>", unsafe_allow_html=True)
        bc1, bc2 = st.columns(2)
        cancel = bc1.form_submit_button("취소", use_container_width=True)
        submit = bc2.form_submit_button("인증하기", use_container_width=True)
        if submit:
            entered_pwd = pwd1 + pwd2 + pwd3 + pwd4
            if entered_pwd == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.logging_in = False
                st.query_params["auth"] = "true"
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
        if cancel:
            st.session_state.logging_in = False
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    # PIN 자동 이동 및 오토 서브밋 JS
    components.html("""
        <script>
        const doc = window.parent.document;
        function setupPin() {
            const inputs = ['pin1', 'pin2', 'pin3', 'pin4'].map(id => doc.querySelector(`input[aria-label="${id}"]`));
            if (!inputs[0] || inputs[0].hasAttribute('data-bound')) return;
            inputs.forEach((input, i) => {
                input.setAttribute('data-bound', 'true');
                if(i===0) setTimeout(() => input.focus(), 300);
                input.addEventListener('input', (e) => {
                    let val = e.target.value.replace(/[^0-9]/g, '').slice(-1);
                    let setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                    setter.call(e.target, val);
                    e.target.dispatchEvent(new Event('input', { bubbles: true }));
                    if(val && i < 3) inputs[i+1].focus();
                    else if(val && i === 3) {
                        const btn = Array.from(doc.querySelectorAll('button')).find(b => b.innerText.includes('인증하기'));
                        if(btn) setTimeout(() => btn.click(), 150);
                    }
                });
                input.addEventListener('keydown', (e) => {
                    if(e.key === 'Backspace' && !e.target.value && i > 0) inputs[i-1].focus();
                });
            });
        }
        setInterval(setupPin, 300);
        </script>
    """, height=0)

else:
    # ★ 2. 메인 앱 화면 ★
    col_auth, col_spacer, col_num_combined = st.columns([2.0, 0.2, 7.8])
    with col_auth:
        if not st.session_state.authenticated:
            if st.button("🔐 LOGIN", use_container_width=True):
                st.session_state.logging_in = True
                st.rerun()
        else:
            if st.button("🔓 LOGOUT", use_container_width=True, type="secondary"):
                st.session_state.authenticated = False
                if "auth" in st.query_params: del st.query_params["auth"]
                st.rerun()

    with col_num_combined:
        st.text_input("Num.ENG :", key="num_input", on_change=format_num_input)

    if st.session_state.num_input:
        clean_num = st.session_state.num_input.replace(",", "").strip()
        if clean_num.isdigit():
            eng_text = num_to_eng(int(clean_num)).capitalize()
            res_col1, res_col2 = st.columns([1, 1])
            with res_col1: st.markdown(f"<p class='num-result'>{eng_text}</p>", unsafe_allow_html=True)
            with res_col2: st.button("❌", key="btn_clear_res_inline", on_click=clear_num_input)
        else:
            st.markdown("<p class='num-result' style='color:#FF9999!important; font-size:1.5rem!important;'>⚠️ 숫자만 입력 가능</p>", unsafe_allow_html=True)

    kst = timezone(timedelta(hours=9)); now_kst = datetime.now(kst); date_str = now_kst.strftime("%A, %B %d, %Y")
    col_title, col_date = st.columns([4.0, 6.0])
    with col_title: st.markdown("<h1 style='color:#FFF; padding-top: 0.5rem; font-size: clamp(1.6rem, 2.9vw, 2.9rem);'>TOmBOy94 English</h1>", unsafe_allow_html=True)

    with col_date:
        components.html(f"""
            <style>
                body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: visible; }}
                .date-wrapper {{ display: flex; flex-wrap: wrap; align-items: center; gap: clamp(5px, 1.5vw, 15px); padding-top: 15px; font-family: sans-serif; width: 100%; }}
                .date-text {{ color: #FFFFFF; font-weight: bold; font-size: clamp(1.1rem, 2.6vw, 2.6rem); white-space: nowrap; }}
                .copy-btn {{ background-color: transparent; border: 1px solid rgba(255,255,255,0.5); color: #FFF; padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: clamp(0.7rem, 1vw, 1.1rem); font-weight:bold; transition: 0.3s; white-space: nowrap; }}
                .copy-btn:hover {{ background-color: rgba(255,255,255,0.2) !important; }}
            </style>
            <div class="date-wrapper">
                <span class="date-text">📅 {date_str}</span>
                <button class="copy-btn" onclick="copyDate()">📋 복사</button>
            </div>
            <script>
            function copyDate() {{
                var temp = document.createElement("textarea"); temp.value = "{date_str}"; document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
                var btn = document.querySelector(".copy-btn"); btn.innerHTML = "✅"; 
                setTimeout(function(){{ btn.innerHTML = "📋 복사"; }}, 1500);
            }}
            </script>
        """, height=130)

    try:
        sheet = get_sheet(); df = load_dataframe(sheet)
        unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
        sel_cat = st.radio("분류 필터", ["🔀 랜덤 10", "전체 분류"] + unique_cats, horizontal=True, label_visibility="collapsed", key="cat_radio", on_change=clear_search)
        st.divider()
        cb_cols = [1.5, 1.5, 1.4, 2.6, 1.5] if st.session_state.authenticated else [1.5, 1.4, 4.1]
        cb = st.columns(cb_cols)
        
        # ★ 검색창 내부의 '전체 검색 후 엔터...' 문구 제거 ★
        cb[0].text_input("🔍", key="search_input", on_change=handle_search)
        
        if st.session_state.authenticated and cb[1].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(unique_cats)
        btn_idx = 2 if st.session_state.authenticated else 1
        btn_text = "🔄 전체모드" if st.session_state.is_simple else "✨ 심플모드"
        if cb[btn_idx].button(btn_text, type="primary" if not st.session_state.is_simple else "secondary", use_container_width=True):
            st.session_state.is_simple = not st.session_state.is_simple; st.rerun()

        is_simple = st.session_state.is_simple
        search = st.session_state.active_search
        d_df = df.copy()
        if search: d_df = d_df[d_df['단어-문장'].str.contains(search, case=False, na=False)]
        else:
            if sel_cat == "🔀 랜덤 10":
                if st.session_state.current_cat != "🔀 랜덤 10" or 'random_df' not in st.session_state:
                    st.session_state.random_df = df.sample(n=min(10, len(df)))
                d_df = st.session_state.random_df.copy()
            elif sel_cat != "전체 분류": d_df = d_df[d_df['분류'] == sel_cat]
            st.session_state.current_cat = sel_cat

        if st.session_state.sort_order == 'asc': d_df = d_df.sort_values(by='단어-문장', ascending=True)
        elif st.session_state.sort_order == 'desc': d_df = d_df.sort_values(by='단어-문장', ascending=False)
        else: d_df = d_df.iloc[::-1]

        if st.session_state.authenticated:
            cb[4].download_button(
                "📥 CSV", 
                d_df.to_csv(index=False).encode('utf-8-sig'), 
                f"Data_{time.strftime('%Y%m%d')}.csv", 
                use_container_width=True
            )

        total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
        curr_p = st.session_state.curr_p if 'curr_p' in st.session_state else 1
        
        components.html(f"""
            <style>body {{ margin:0; padding:0; background:transparent!important; overflow:hidden; }}</style>
            <div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px; padding-top:5px; font-family:sans-serif;">
                <span style="color:#FF9999; font-weight:bold; font-size:0.9rem; margin-right:15px;">{'🔍 ' + search if search else ''}</span>
                <span style="color:#FFF; font-weight:bold; font-size:0.95rem;">총 {total}개 (페이지: {curr_p}/{pages})</span>
            </div>
            <script>
            const doc = window.parent.document;
            
            if (doc.liveCommaHandler) {{
                doc.removeEventListener('input', doc.liveCommaHandler, true);
            }}
            
            doc.liveCommaHandler = function(e) {{
                if (e.target && e.target.tagName === 'INPUT') {{
                    let label = e.target.getAttribute('aria-label');
                    if (label && label.includes('Num.ENG')) {{
                        let val = e.target.value;
                        let numStr = val.replace(/[^0-9]/g, '');
                        let formatted = numStr ? Number(numStr).toLocaleString('en-US') : '';
                        
                        if (val !== formatted) {{
                            let cursorPosition = e.target.selectionStart;
                            let oldLength = val.length;
                            
                            let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                            nativeSetter.call(e.target, formatted);
                            e.target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            
                            let newLength = formatted.length;
                            let newCursorPos = cursorPosition + (newLength - oldLength);
                            
                            setTimeout(() => {{
                                e.target.setSelectionRange(newCursorPos, newCursorPos);
                            }}, 0);
                        }}
                    }}
                }}
            }};
            
            doc.addEventListener('input', doc.liveCommaHandler, true);
            </script>
        """, height=35)
       
        ratio = [1.5, 6, 4.5, 1] if is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1]
        labels = ["분류", "단어-문장", "해석", "수정"] if is_simple else ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
        h_cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
        for i, l in enumerate(labels if st.session_state.authenticated else labels[:-1]):
            if l == "단어-문장":
                sort_icon = " ↑" if st.session_state.sort_order == 'asc' else (" ↓" if st.session_state.sort_order == 'desc' else "")
                if h_cols[i].button(f"{l}{sort_icon}", key="sort_btn"):
                    st.session_state.sort_order = 'asc' if st.session_state.sort_order == 'None' else ('desc' if st.session_state.sort_order == 'asc' else 'None')
                    st.rerun()
            else: h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
       
        st.markdown("<div style='border-bottom:2px solid rgba(255,255,255,0.4); margin-top:-20px; margin-bottom:5px;'></div>", unsafe_allow_html=True)

        for idx, row in d_df.iloc[(curr_p-1)*100 : curr_p*100].iterrows():
            cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
            cols[0].markdown(f"<span class='row-marker'></span><span class='cat-text-bold'>{row['분류']}</span>", unsafe_allow_html=True)
            cols[1].markdown(f"<span class='word-text'>{row['단어-문장']}</span>", unsafe_allow_html=True)
            cols[2].markdown(f"<span class='mean-text'>{row['해석']}</span>", unsafe_allow_html=True)
            if not is_simple:
                cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
                if st.session_state.authenticated and cols[6].button("✏️", key=f"e_{idx}", type="tertiary"): edit_dialog(idx, row.to_dict(), unique_cats)
            elif st.session_state.authenticated and cols[3].button("✏️", key=f"es_{idx}", type="tertiary"): edit_dialog(idx, row.to_dict(), unique_cats)

        if pages > 1:
            p_cols = st.columns([3.5, 1.5, 2, 1.5, 3.5])
            if p_cols[1].button("◀ 이전", disabled=(curr_p == 1)): st.session_state.curr_p -= 1; st.rerun()
            p_cols[2].markdown(f"<div style='text-align:center; padding:10px; color:#FFD700; font-weight:bold;'>Page {curr_p} / {pages}</div>", unsafe_allow_html=True)
            if p_cols[3].button("다음 ▶", disabled=(curr_p == pages)): st.session_state.curr_p += 1; st.rerun()

    except Exception:
        pass

    current_year = datetime.now(timezone(timedelta(hours=9))).year
    st.markdown(f"""
        <div style='text-align: center; margin-top: 30px; margin-bottom: 20px; padding-top: 15px; border-top: 1px dotted rgba(255, 255, 255, 0.2);'>
            <p style='color: #A3B8B8; font-size: 1.7rem; font-weight: bold; margin-bottom: 5px;'>
                Copyright © {current_year} TOmBOy94 &nbsp;|&nbsp; lodus11st@naver.com &nbsp;|&nbsp; All rights reserved.
            </p>
        </div>
    """, unsafe_allow_html=True)
