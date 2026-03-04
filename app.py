import streamlit as st
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io
import math
import re
import json
from datetime import datetime, timedelta, timezone

# --- [페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="TOmBOy94 English")

# --- [세션 상태 관리 초기화] ---
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
if 'curr_p' not in st.session_state: st.session_state.curr_p = 1
# ★ 새 페이지 전환용 상태 추가 ★
if 'app_mode' not in st.session_state: st.session_state.app_mode = 'English' 
# ★ 학습 모드 상태 추가 ★
if 'show_study' not in st.session_state: st.session_state.show_study = False

# --- [보안 설정 및 Google Sheets 연결] ---
LOGIN_PASSWORD = st.secrets["tom_password"]

# 콜백 함수들
def handle_search():
    st.session_state.active_search = st.session_state.search_input.strip()
    st.session_state.search_input = ""
    st.session_state.curr_p = 1

def clear_search():
    st.session_state.active_search = ""
    st.session_state.curr_p = 1

def reset_page():
    st.session_state.curr_p = 1

# --- [전체화면 학습 모드 컴포넌트 렌더링 함수] ---
def render_study_mode(study_data):
    data_json = json.dumps(study_data, ensure_ascii=False)
    html_code = f"""
    <div style="background: #0a0a0a; color: white; height: 80vh; display: flex; flex-direction: column; justify-content: space-between; align-items: center; font-family: sans-serif; border-radius: 20px; overflow: hidden; position: relative;">
        
        <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; width: 100%; text-align: center;">
            <div id="rolling-container"></div>
        </div>

        <div style="width: 100%; border-top: 1px solid rgba(255,255,255,0.1); padding: 40px; text-align: center;">
            <p id="ko-text" style="color: #a08b7a; font-size: 26px; font-weight: bold; margin: 0; transition: opacity 0.5s;"></p>
        </div>
    </div>

    <script>
        const studyData = {data_json};
        let currentIndex = 0;
        const container = document.getElementById('rolling-container');
        const koText = document.getElementById('ko-text');

        function render() {{
            if (!studyData || studyData.length === 0) return;
            container.innerHTML = '';
            koText.style.opacity = 0;
            
            setTimeout(() => {{
                koText.innerText = studyData[currentIndex].ko || "";
                koText.style.opacity = 1;
            }}, 200);

            studyData.forEach((item, index) => {{
                const distance = index - currentIndex;
                if (distance < -2 || distance > 2) return;

                const div = document.createElement('div');
                div.style.position = 'absolute';
                div.style.width = '100%';
                div.style.transition = 'all 0.7s ease-in-out';
                div.style.left = '0';
                
                if (distance === 0) {{
                    div.style.top = '50%';
                    div.style.transform = 'translateY(-50%) scale(1.1)';
                    div.style.opacity = '1';
                    div.style.color = '#E67E22'; // 요청하신 오렌지색
                    div.style.fontWeight = '900';
                    div.style.textShadow = '0 0 15px rgba(230,126,34,0.3)';
                    div.style.zIndex = '10';
                }} else {{
                    div.style.top = `calc(50% + ${{distance * 80}}px)`; // ★ 파이썬 f-string 중복 파싱 에러 방지용 이중 괄호 적용
                    div.style.transform = 'translateY(-50%) scale(0.85)';
                    div.style.opacity = Math.abs(distance) === 1 ? '0.3' : '0.1';
                    div.style.color = 'rgba(255,255,255,0.4)';
                    div.style.fontWeight = '500';
                    div.style.zIndex = '5';
                }}

                div.innerHTML = `<p style="font-size: 36px; margin: 0; letter-spacing: 0.5px;">${{item.en}}</p>`; // ★ 파이썬 f-string 중복 파싱 에러 방지용 이중 괄호 적용
                container.appendChild(div);
            }});
        }}

        // 5초(5000ms)마다 인덱스 변경 및 다시 그리기
        if (studyData && studyData.length > 0) {{
            setInterval(() => {{
                currentIndex = (currentIndex + 1) % studyData.length;
                render();
            }}, 5000);
            render();
        }}
    </script>
    """
    components.html(html_code, height=750)

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

    /* 2. 글자색 화이트 강제화 및 타이틀 하단 여백 제거 */
    h1, h2, h3, h4, h5, h6, p, span, label, summary, b, strong {
        color: #FFFFFF !important;
    }
    h1 {
        margin-bottom: 0px !important;
        padding-bottom: 0px !important;
    }
    
    /* 팝업창(Dialog) 제목 */
    #새-항목-추가, #항목-수정-및-삭제, #새-링크-추가, #링크-수정-및-삭제,
    div[data-testid="stDialog"] h2,
    div[role="dialog"] h2,
    section[role="dialog"] h2 {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 3. 로그인 입력창 모바일 최적화 및 눈알 제거 */
    .stTextInput input {
        height: 50px !important;
        font-size: 1.2rem !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stTextInput"] button { display: none !important; }

    /* 4. 컨텐츠 행(Row) 호버 효과 및 레이아웃 보정 */
    div.element-container:has(.row-marker) { width: 100% !important; min-width: 100% !important; }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 12px 10px !important; 
        border-radius: 0px !important; 
        margin-bottom: 0px !important; border-bottom: 1px dotted rgba(255, 255, 255, 0.2) !important; 
        width: 100% !important; min-width: 100% !important; flex: 1 1 100% !important;
        display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
        align-items: center !important; overflow: visible !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover { background-color: rgba(26, 47, 47, 0.9) !important; }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) > div[data-testid="column"] {
        display: flex !important; flex-direction: column !important; justify-content: center !important; 
        padding: 0 !important; margin: 0 !important; overflow: visible !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div.element-container,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div.stMarkdown,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) p {
        display: block !important; margin: 0 !important; padding: 0 !important;
        line-height: 1.5 !important; width: 100% !important;
    }

    /* 5. 상단 분류 리스트(Radio) 알약 형태 */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row !important; flex-wrap: wrap !important; gap: 10px 12px !important;
        padding-top: 0px !important; padding-bottom: 5px !important;
    }
    div[data-testid="stRadio"] label > div:first-of-type { display: none !important; }
    div[data-testid="stRadio"] label {
        cursor: pointer !important; margin: 0 !important; background-color: rgba(255, 255, 255, 0.1) !important;
        padding: 6px 18px !important; border-radius: 50px !important; border: 1px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    div[data-testid="stRadio"] label:hover { background-color: rgba(255, 255, 255, 0.2) !important; border-color: #FFD700 !important; }
    div[data-testid="stRadio"] label p {
        color: #FFFFFF !important; font-size: clamp(0.9rem, 1.2vw, 1.3rem) !important;
        font-weight: 800 !important; white-space: pre-wrap !important; text-align: center !important; line-height: 1.2 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked), div[data-testid="stRadio"] label:has(div[aria-checked="true"]) {
        background-color: #FFD700 !important; border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) p, div[data-testid="stRadio"] label:has(div[aria-checked="true"]) p {
        color: #224343 !important;
    }

    /* ★ 소분류 전용 라디오 버튼 스타일 */
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label {
        padding: 4px 14px !important;
    }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label p {
        color: #FFA500 !important; 
        font-size: clamp(0.7rem, 0.9vw, 1.0rem) !important; 
    }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:hover {
        border-color: #FFA500 !important;
        background-color: rgba(255, 165, 0, 0.15) !important;
    }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(input:checked), 
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(div[aria-checked="true"]) {
        background-color: #FFA500 !important;
        border-color: #FFA500 !important;
    }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(input:checked) p, 
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(div[aria-checked="true"]) p {
        color: #224343 !important;
    }

    /* 6. 버튼 스타일 */
    button, div.stDownloadButton > button {
        border-radius: 50px !important; padding: 0.5rem 1.2rem !important; font-weight: 900 !important;
        transition: all 0.3s ease !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;
    }
    button[kind="primary"] { background-color: #FFFFFF !important; border-color: #FFFFFF !important; }
    button[kind="primary"] p { color: #224343 !important; font-size: clamp(0.75rem, 1.1vw, 1.15rem) !important; font-weight: 900 !important; }
    button[kind="secondary"], div.stDownloadButton > button { background-color: transparent !important; border: 2px solid #FFFFFF !important; color: #FFFFFF !important; }

    /* 7. 수정 버튼: 투명 연필 아이콘 */
    button[kind="tertiary"] {
        background-color: transparent !important; border: none !important; padding: 0 !important; margin: 0 !important;
        min-height: 0 !important; min-width: 40px !important; box-shadow: none !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }
    button[kind="tertiary"] p { font-size: 1.6rem !important; margin: 0 !important; padding: 0 !important; transition: transform 0.2s ease !important; }
    button[kind="tertiary"]:hover p { transform: scale(1.2) !important; }

    /* 8. 텍스트 스타일 */
    .header-label { font-size: clamp(1.0rem, 1.4vw, 1.5rem) !important; font-weight: 800 !important; color: #FFFFFF !important; white-space: nowrap !important; }
    .word-text { font-size: 1.98em; font-weight: bold; color: #FFD700 !important; word-break: keep-all; display: inline-block !important; margin-bottom: 0px !important; transition: transform 0.2s ease !important; transform-origin: left center !important; }
    .mean-text { font-size: 1.3em; word-break: keep-all; display: inline-block !important; margin-bottom: 0px !important; }
    .cat-text-bold { font-weight: bold !important; font-size: 0.95rem; display: inline-block !important; margin-bottom: 0px !important; }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover .word-text { transform: scale(1.1) !important; z-index: 10 !important; }

    /* 9. Num.ENG 및 검색창 레이아웃 */
    div[data-testid="stTextInput"]:has(label p) { display: flex !important; flex-direction: row !important; align-items: center !important; gap: 8px !important; }
    div[data-testid="stTextInput"]:has(label p) label { margin-bottom: 0 !important; margin-top: 5px !important; min-width: fit-content !important; }
    div[data-testid="stTextInput"]:has(label p):not(:has(input[aria-label="Num.ENG :"])) { width: 100% !important; }
    div[data-testid="stTextInput"]:has(input[aria-label="Num.ENG :"]) { max-width: 350px !important; }
    
    /* 10. Num.ENG 결과물 */
    div[data-testid="stHorizontalBlock"]:has(.num-result) { display: flex !important; flex-direction: row !important; align-items: center !important; justify-content: flex-start !important; gap: 12px !important; width: 100% !important; }
    div[data-testid="stHorizontalBlock"]:has(.num-result) > div { width: fit-content !important; flex: 0 1 auto !important; min-width: unset !important; }
    .num-result { color: #FFD700 !important; font-weight: bold; font-size: clamp(1.6rem, 2.2vw, 2.4rem) !important; margin: 0 !important; line-height: 1.1; white-space: nowrap !important; }
    div[data-testid="stHorizontalBlock"]:has(.num-result) button { background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; margin: 0 !important; margin-top: 2px !important; }

    /* ★ 링크 모음 전용 아이템 스타일 */
    .link-table-cat1 { font-size: 1.8rem !important; color: #FFD700 !important; font-weight: bold; display: inline-block; margin-bottom: 0px; }
    .link-table-cat2 { font-size: 1.2rem !important; color: #FFA500 !important; font-weight: bold; display: inline-block; margin-bottom: 0px; }
    
    a.link-table-title { font-size: 2.0em !important; font-weight: bold; color: #FFD700 !important; text-decoration: none !important; border-bottom: none !important; background-image: none !important; display: inline-block; margin-bottom: 0px; transition: opacity 0.2s; }
    a.link-table-title:hover { opacity: 0.8; text-decoration: none !important; border-bottom: none !important; }
    
    /* ★ 복사 가능한 링크 스타일 */
    span.link-table-url, span.link-table-url a { 
        cursor: pointer; 
        font-size: 0.85rem; 
        color: #9ACD32 !important; 
        text-decoration: none !important; 
        border-bottom: none !important; 
        background-image: none !important; 
        display: block; 
        overflow: hidden; 
        text-overflow: ellipsis; 
        white-space: nowrap; 
        max-width: 100%; 
        transition: all 0.2s; 
    }
    span.link-table-url:hover, span.link-table-url a:hover { opacity: 0.8; color: #FFD700 !important; }
    
    div[data-testid="stMarkdownContainer"] a, div[data-testid="stMarkdownContainer"] a:hover { border-bottom: 0px !important; text-decoration: none !important; background-image: none !important; }
    
    .link-table-memo { font-size: 1.3em !important; color: #FFFFFF; opacity: 0.9; word-break: keep-all; margin-bottom: 0px; }

    @media screen and (max-width: 768px) {
        .word-text { font-size: 1.21rem !important; }
        .mean-text { font-size: 0.9rem !important; }
        div[data-testid="stRadio"] label p { font-size: 1.2rem !important; }
        .link-table-cat1 { font-size: 1.4rem !important; }
        a.link-table-title { font-size: 1.5rem !important; }
        .link-table-memo { font-size: 1.1rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# [심플모드 CSS]
if st.session_state.is_simple:
    st.markdown("""
        <style>
        @media screen and (max-width: 768px) {
            .word-text { font-size: 1.7rem !important; line-height: 1.3 !important; }
            .mean-text { font-size: 1.26rem !important; line-height: 1.3 !important; }
        }
        </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

def get_sheet():
    return init_connection().open("English_Sentences").sheet1

def get_links_sheet():
    return init_connection().open("English_Sentences").get_worksheet(1) # 인덱스 1 (시트2)

def load_dataframe(sheet):
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            if not data: return pd.DataFrame(columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])
            rows = [row + [""] * (6 - len(row)) for row in data[1:]]
            df = pd.DataFrame(rows, columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])
            for col in df.columns: df[col] = df[col].astype(str).str.strip()
            return df
        except: time.sleep(1)
    raise Exception("데이터 로드 실패")

def load_links_dataframe(sheet):
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            if not data: return pd.DataFrame(columns=['대분류', '소분류', '제목', '메모', '링크'])
            rows = [row + [""] * (5 - len(row)) for row in data[1:]]
            df = pd.DataFrame(rows, columns=['대분류', '소분류', '제목', '메모', '링크'])
            for col in df.columns: df[col] = df[col].astype(str).str.strip()
            return df
        except: time.sleep(1)
    raise Exception("링크 데이터 로드 실패")

# --- [다이얼로그 설정 (영어 단어장)] ---
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
            sheet.update(f"A{idx+2}:F{idx+2}", [[final_cat, word_sent, mean, pron, m1, m2]])
            st.rerun()
        if b2.form_submit_button("🗑️ 삭제", use_container_width=True):
            sheet = get_sheet()
            sheet.delete_rows(idx + 2)
            st.rerun()

# --- [다이얼로그 설정 (링크 모음)] ---
@st.dialog("새 링크 추가")
def add_link_dialog(unique_cats1, unique_cats2):
    with st.form("add_link_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        selected_cat1 = c1.selectbox("기존 대분류", ["(새로 입력)"] + unique_cats1)
        new_cat1 = c2.text_input("새 대분류 입력")
        
        c3, c4 = st.columns(2)
        selected_cat2 = c3.selectbox("기존 소분류", ["(새로 입력)"] + unique_cats2)
        new_cat2 = c4.text_input("새 소분류 입력")
        
        title = st.text_input("제목 (필수)")
        memo = st.text_input("메모")
        link_url = st.text_input("링크 주소 (URL) (필수)")
        
        if st.form_submit_button("저장하기", use_container_width=True, type="primary"):
            final_cat1 = new_cat1.strip() if new_cat1.strip() else (selected_cat1 if selected_cat1 != "(새로 입력)" else "")
            final_cat2 = new_cat2.strip() if new_cat2.strip() else (selected_cat2 if selected_cat2 != "(새로 입력)" else "")
            
            if title and link_url:
                sheet2 = get_links_sheet()
                sheet2.append_row([final_cat1, final_cat2, title, memo, link_url])
                st.success("새 링크 저장 완료!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("제목과 링크 주소는 필수입니다.")

@st.dialog("링크 수정 및 삭제")
def edit_link_dialog(idx, row_data, unique_cats1, unique_cats2):
    safe_cats1 = unique_cats1 if unique_cats1 else ["(없음)"]
    cat1_val = row_data.get('대분류', '')
    cat1_index = safe_cats1.index(cat1_val) if cat1_val in safe_cats1 else 0
    
    safe_cats2 = unique_cats2 if unique_cats2 else ["(없음)"]
    cat2_val = row_data.get('소분류', '')
    cat2_index = safe_cats2.index(cat2_val) if cat2_val in safe_cats2 else 0
    
    with st.form(f"edit_link_{idx}"):
        c1, c2 = st.columns(2)
        edit_cat1 = c1.selectbox("대분류", safe_cats1, index=cat1_index)
        new_cat1 = c2.text_input("대분류 직접 수정")
        
        c3, c4 = st.columns(2)
        edit_cat2 = c3.selectbox("소분류", safe_cats2, index=cat2_index)
        new_cat2 = c4.text_input("소분류 직접 수정")
        
        title = st.text_input("제목", value=row_data.get('제목', ''))
        memo = st.text_input("메모", value=row_data.get('메모', ''))
        link_url = st.text_input("링크 주소(URL)", value=row_data.get('링크', ''))
        
        b1, b2 = st.columns(2)
        if b1.form_submit_button("💾 저장", use_container_width=True, type="primary"):
            final_cat1 = new_cat1.strip() if new_cat1.strip() else edit_cat1
            final_cat2 = new_cat2.strip() if new_cat2.strip() else edit_cat2
            sheet2 = get_links_sheet()
            sheet2.update(f"A{idx+2}:E{idx+2}", [[final_cat1, final_cat2, title, memo, link_url]])
            st.rerun()
        if b2.form_submit_button("🗑️ 삭제", use_container_width=True):
            sheet2 = get_links_sheet()
            sheet2.delete_rows(idx + 2)
            st.rerun()

# --- [비즈니스 로직 함수] ---
def format_num_input():
    cleaned = re.sub(r'[^0-9]', '', str(st.session_state.num_input))
    st.session_state.num_input = f"{int(cleaned):,}" if cleaned else ""

def clear_num_input():
    st.session_state.num_input = ""

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

# 1. 로그인 화면
if not st.session_state.authenticated and st.session_state.logging_in:
    st.write("## 🔐 Security Login")
    with st.form("login_form", clear_on_submit=False):
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        pwd = st.text_input("Enter Password", type="password", placeholder="비밀번호를 입력하세요...")
        submit = st.form_submit_button("✅ LOGIN", use_container_width=True, type="primary")
        if submit:
            if pwd == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.logging_in = False
                st.query_params["auth"] = "true"
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
    if st.button("🔙 CANCEL", use_container_width=True):
        st.session_state.logging_in = False
        st.rerun()
else:
    # 2. 메인 앱 화면
    col_auth, col_spacer, col_num_combined = st.columns([2.0, 0.2, 7.8], vertical_alignment="center")
    
    with col_auth:
        if not st.session_state.authenticated:
            if st.button("🔐 LOGIN", use_container_width=True):
                st.session_state.logging_in = True
                st.rerun()
        else:
            if st.button("🔓 LOGOUT", use_container_width=True, type="secondary"):
                st.session_state.authenticated = False
                st.session_state.app_mode = 'English'  # ★ 로그아웃 시 영어모드로 강제 초기화
                if "auth" in st.query_params: del st.query_params["auth"]
                st.rerun()

    with col_num_combined:
        st.text_input("Num.ENG :", key="num_input", on_change=format_num_input)

    if st.session_state.num_input:
        clean_num = st.session_state.num_input.replace(",", "").strip()
        if clean_num.isdigit():
            eng_text = num_to_eng(int(clean_num)).capitalize()
            res_col1, res_col2 = st.columns([1, 1], vertical_alignment="center")
            with res_col1:
                st.markdown(f"<p class='num-result'>{eng_text}</p>", unsafe_allow_html=True)
            with res_col2:
                st.button("❌", key="btn_clear_res_inline", on_click=clear_num_input)
        else:
            st.markdown("<p class='num-result' style='color:#FF9999!important; font-size:1.5rem!important;'>⚠️ 숫자만 입력 가능</p>", unsafe_allow_html=True)

    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    date_str = now_kst.strftime("%A, %B %d, %Y")

    # 타이틀과 모드 전환, 학습 모드 버튼
    col_title, col_link_btn, col_study_btn, col_date = st.columns([2.5, 1.5, 1.5, 4.5], vertical_alignment="center")
    with col_title:
        st.markdown("<h1 style='color:#FFF; padding-top: 0.5rem; font-size: clamp(1.6rem, 2.9vw, 2.9rem);'>TOmBOy94</h1>", unsafe_allow_html=True)

    with col_link_btn:
        # ★ 로그인 상태일 때만 전환 버튼 렌더링
        if st.session_state.authenticated:
            if st.session_state.app_mode == 'English':
                if st.button("🔗 링크 모음", use_container_width=True, type="secondary"):
                    st.session_state.app_mode = 'Links'
                    st.rerun()
            else:
                if st.button("🇬🇧 영어 모음", use_container_width=True, type="secondary"):
                    st.session_state.app_mode = 'English'
                    st.rerun()

    with col_study_btn:
        if st.session_state.app_mode == 'English':
            if st.button("📚 학습 모드", use_container_width=True, type="primary"):
                st.session_state.show_study = True
                st.rerun()

    with col_date:
        components.html(f"""
            <style>
                body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: visible; }}
                .date-wrapper {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: clamp(5px, 1.5vw, 15px); padding-top: 5px; font-family: sans-serif; width: 100%; }}
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
            
            // ★ 링크 클릭 시 클립보드 복사 이벤트 글로벌 등록 (재렌더링 시 끊김 완벽 방지)
            const doc = window.parent.document;
            if (doc.copyLinkHandler) {{
                doc.removeEventListener('click', doc.copyLinkHandler, true); // 이전 리스너 찌꺼기 제거
            }}
            
            doc.copyLinkHandler = function(e) {{
                let target = e.target.closest('.copyable-link');
                if (target) {{
                    e.preventDefault();
                    e.stopPropagation(); // Streamlit 기본 a 태그 속성 발동(새창 열기) 완벽 차단
                    
                    let url = target.getAttribute('data-url');
                    if (url) {{
                        let temp = doc.createElement("textarea");
                        temp.value = url;
                        temp.style.position = "fixed"; 
                        temp.style.opacity = "0"; 
                        doc.body.appendChild(temp);
                        temp.select();
                        try {{ doc.execCommand("copy"); }} catch(err) {{}}
                        doc.body.removeChild(temp);
                        
                        let originalText = target.innerHTML;
                        target.innerHTML = "✅ 복사완료!";
                        target.style.color = "#FFD700";
                        setTimeout(function(){{ 
                            target.innerHTML = originalText; 
                            target.style.color = ""; 
                        }}, 1500);
                    }}
                }}
            }};
            doc.addEventListener('click', doc.copyLinkHandler, true);
            </script>
        """, height=90) 

    # ==============================================================
    # 🇬🇧 영어 단어장 모드
    # ==============================================================
    if st.session_state.app_mode == 'English':
        try:
            sheet = get_sheet(); df = load_dataframe(sheet)
            
            # --- 학습 모드가 켜져있을 때 (새창 느낌으로 렌더링) ---
            if st.session_state.show_study:
                # 1. 데이터 필터링 연동
                d_df = df.copy()
                if st.session_state.active_search:
                    d_df = d_df[d_df['단어-문장'].str.contains(st.session_state.active_search, case=False, na=False)]
                else:
                    if st.session_state.current_cat == "🔀 랜덤 10":
                        if 'random_df' in st.session_state: d_df = st.session_state.random_df
                        else: d_df = df.sample(n=min(10, len(df)))
                    elif st.session_state.current_cat != "전체 분류":
                        d_df = d_df[d_df['분류'] == st.session_state.current_cat]

                # 2. 학습 모드 UI 렌더링
                st.markdown("<br>", unsafe_allow_html=True)
                col1, col2, col3 = st.columns([1, 8, 1])
                with col2:
                    if st.button("❌ 학습 모드 종료 (돌아가기)", use_container_width=True):
                        st.session_state.show_study = False
                        st.rerun()
                    
                    if d_df.empty:
                        st.warning("조건에 맞는 문장이 없어 학습 모드를 실행할 수 없습니다.")
                    else:
                        study_data = d_df[['단어-문장', '해석']].rename(columns={'단어-문장': 'en', '해석': 'ko'}).to_dict('records')
                        render_study_mode(study_data)
                
                # 여기서 실행을 멈춰 기존 메뉴와 표가 보이지 않게 함 (새창 효과)
                st.stop()


            # --- 기본 UI 렌더링 (학습 모드가 꺼져있을 때) ---
            unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
            sel_cat = st.radio("분류 필터", ["🔀 랜덤 10", "전체 분류"] + unique_cats, horizontal=True, label_visibility="collapsed", key="cat_radio", on_change=clear_search)
            
            st.divider()
            
            cb_cols = [1.5, 1.5, 1.4, 2.6, 1.5] if st.session_state.authenticated else [1.5, 1.4, 4.1]
            cb = st.columns(cb_cols, vertical_alignment="center")
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
                cb[4].download_button("📥 CSV", d_df.to_csv(index=False).encode('utf-8-sig'), f"Data_{time.strftime('%Y%m%d')}.csv", use_container_width=True)

            total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
            curr_p = st.session_state.curr_p
            
            components.html(f"""
                <style>body {{ margin:0; padding:0; background:transparent!important; overflow:hidden; }}</style>
                <div style="display:flex; flex-wrap:wrap; align-items:center; gap:8px; padding-top:5px; font-family:sans-serif;">
                    <span style="color:#FF9999; font-weight:bold; font-size:0.9rem; margin-right:15px;">{'🔍 ' + search if search else ''}</span>
                    <span style="color:#FFF; font-weight:bold; font-size:0.95rem;">총 {total}개 (페이지: {curr_p}/{pages})</span>
                </div>
                <script>
                const doc = window.parent.document;
                if (doc.liveCommaHandler) {{ doc.removeEventListener('input', doc.liveCommaHandler, true); }}
                doc.liveCommaHandler = function(e) {{
                    if (e.target && e.target.tagName === 'INPUT') {{
                        let label = e.target.getAttribute('aria-label');
                        if (label && label.includes('Num.ENG')) {{
                            let val = e.target.value;
                            let numStr = val.replace(/[^0-9]/g, '');
                            let formatted = numStr ? Number(numStr).toLocaleString('en-US') : '';
                            if (val !== formatted) {{
                                let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                                nativeSetter.call(e.target, formatted);
                                e.target.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            }}
                        }}
                    }}
                }};
                doc.addEventListener('input', doc.liveCommaHandler, true);
                </script>
            """, height=35)
            
            ratio = [1.5, 6, 4.5, 1] if is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1]
            labels = ["분류", "단어-문장", "해석", "수정"] if is_simple else ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
            h_cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1], vertical_alignment="center")
            for i, l in enumerate(labels if st.session_state.authenticated else labels[:-1]):
                if l == "단어-문장":
                    sort_icon = " ↑" if st.session_state.sort_order == 'asc' else (" ↓" if st.session_state.sort_order == 'desc' else "")
                    if h_cols[i].button(f"{l}{sort_icon}", key="sort_btn"):
                        st.session_state.sort_order = 'asc' if st.session_state.sort_order == 'None' else ('desc' if st.session_state.sort_order == 'asc' else 'None')
                        st.rerun()
                else: h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
            
            st.markdown("<div style='border-bottom:2px solid rgba(255,255,255,0.4); margin-top:-20px; margin-bottom:5px;'></div>", unsafe_allow_html=True)

            for idx, row in d_df.iloc[(curr_p-1)*100 : curr_p*100].iterrows():
                cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1], vertical_alignment="center")
                cols[0].markdown(f"<span class='row-marker'></span><span class='cat-text-bold'>{row['분류']}</span>", unsafe_allow_html=True)
                cols[1].markdown(f"<span class='word-text'>{row['단어-문장']}</span>", unsafe_allow_html=True)
                cols[2].markdown(f"<span class='mean-text'>{row['해석']}</span>", unsafe_allow_html=True)
                if not is_simple:
                    cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
                    if st.session_state.authenticated and cols[6].button("✏️", key=f"e_{idx}", type="tertiary"): edit_dialog(idx, row.to_dict(), unique_cats)
                elif st.session_state.authenticated and cols[3].button("✏️", key=f"es_{idx}", type="tertiary"): edit_dialog(idx, row.to_dict(), unique_cats)

            if pages > 1:
                p_cols = st.columns([3.5, 1.5, 2, 1.5, 3.5], vertical_alignment="center")
                if p_cols[1].button("◀ 이전", disabled=(st.session_state.curr_p == 1)): 
                    st.session_state.curr_p -= 1
                    st.rerun()
                p_cols[2].markdown(f"<div style='text-align:center; padding:10px; color:#FFD700; font-weight:bold;'>Page {st.session_state.curr_p} / {pages}</div>", unsafe_allow_html=True)
                if p_cols[3].button("다음 ▶", disabled=(st.session_state.curr_p == pages)): 
                    st.session_state.curr_p += 1
                    st.rerun()

        except Exception as e: st.error(f"오류 발생: {e}")

    # ==============================================================
    # 🔗 링크 모음 모드 (시트2 연동)
    # ==============================================================
    elif st.session_state.app_mode == 'Links':
        try:
            sheet2 = get_links_sheet()
            df_links = load_links_dataframe(sheet2)
            
            unique_links_cats1 = sorted([x for x in df_links['대분류'].unique().tolist() if x != ''])
            unique_links_cats2 = sorted([x for x in df_links['소분류'].unique().tolist() if x != ''])
            
            # 1. 대분류 라디오 버튼 (✨ 최근 5개를 기본으로 추가)
            sel_link_cat1 = st.radio("대분류 필터", ["✨ 최근 5개", "전체 링크"] + unique_links_cats1, horizontal=True, label_visibility="collapsed")
            
            # 2. 대분류 선택 시, 바로 밑에 소분류 라디오 버튼 렌더링
            sel_link_cat2 = "전체"
            if sel_link_cat1 not in ["✨ 최근 5개", "전체 링크"]:
                subset_cat2 = sorted([x for x in df_links[df_links['대분류'] == sel_link_cat1]['소분류'].unique().tolist() if x != ''])
                if subset_cat2:
                    display_cat2 = ["전체"] + subset_cat2
                    sel_link_cat2 = st.radio("소분류 필터", display_cat2, horizontal=True, label_visibility="collapsed", key="cat2_radio")

            st.divider()
            
            # ★ 검색, 추가, 다운로드 컨트롤 바
            cb_cols = [1.5, 1.5, 5.5, 1.5] if st.session_state.authenticated else [1.5, 7.0, 1.5]
            cb = st.columns(cb_cols, vertical_alignment="center")
            cb[0].text_input("🔍", key="search_input", on_change=handle_search)
            
            if st.session_state.authenticated:
                if cb[1].button("➕ 새 링크 추가", type="primary", use_container_width=True):
                    add_link_dialog(unique_links_cats1, unique_links_cats2)
            
            # 데이터 필터링 로직
            search = st.session_state.active_search
            if search:
                df_links = df_links[df_links['제목'].str.contains(search, case=False, na=False) | df_links['메모'].str.contains(search, case=False, na=False) | df_links['링크'].str.contains(search, case=False, na=False)]
            else:
                if sel_link_cat1 == "✨ 최근 5개":
                    df_links = df_links.iloc[::-1].head(5) # 최신 역순으로 5개만 추출
                elif sel_link_cat1 != "전체 링크":
                    df_links = df_links[df_links['대분류'] == sel_link_cat1]
                    if sel_link_cat2 != "전체":
                        df_links = df_links[df_links['소분류'] == sel_link_cat2]

            # CSV 다운로드 버튼
            if st.session_state.authenticated:
                cb[3].download_button("📥 CSV", df_links.to_csv(index=False).encode('utf-8-sig'), f"Links_{time.strftime('%Y%m%d')}.csv", use_container_width=True)
            else:
                cb[2].download_button("📥 CSV", df_links.to_csv(index=False).encode('utf-8-sig'), f"Links_{time.strftime('%Y%m%d')}.csv", use_container_width=True)

            # --- 표 형식 헤더 ---
            l_ratio = [1.2, 1.2, 2.5, 2.0, 2.5, 1.0] if st.session_state.authenticated else [1.2, 1.2, 2.5, 2.0, 2.5]
            l_labels = ["대분류", "소분류", "제목", "메모", "링크", "수정"] if st.session_state.authenticated else ["대분류", "소분류", "제목", "메모", "링크"]
            
            h_cols = st.columns(l_ratio, vertical_alignment="center")
            for i, l in enumerate(l_labels):
                h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
            
            st.markdown("<div style='border-bottom:2px solid rgba(255,255,255,0.4); margin-top:-20px; margin-bottom:5px;'></div>", unsafe_allow_html=True)

            # --- 표 내용 출력 ---
            if df_links.empty:
                st.info("등록된 링크가 없습니다.")
            else:
                for idx, row in df_links.iterrows():
                    # ★ 컨텐츠 행 수직 중앙 정렬
                    cols = st.columns(l_ratio, vertical_alignment="center")
                    
                    # 1. 대분류
                    cols[0].markdown(f"<span class='row-marker'></span><span class='link-table-cat1'>{row['대분류']}</span>", unsafe_allow_html=True)
                    
                    # 2. 소분류
                    cols[1].markdown(f"<span class='link-table-cat2'>{row['소분류']}</span>", unsafe_allow_html=True)
                    
                    # 3. 제목
                    title_html = f"<a href='{row['링크']}' target='_blank' class='link-table-title'>{row['제목']}</a>"
                    cols[2].markdown(title_html, unsafe_allow_html=True)
                    
                    # 4. 메모
                    cols[3].markdown(f"<span class='link-table-memo'>{row['메모']}</span>", unsafe_allow_html=True)
                    
                    # 5. 링크 (Streamlit 자동 링크 변환 꼼수 차단용: 텍스트 사이에 보이지 않는 공백 강제 삽입)
                    safe_display_url = row['링크'].replace('http', 'http&#8203;').replace('www', 'www&#8203;')
                    link_html = f"<span class='link-table-url copyable-link' data-url='{row['링크']}' title='클릭하여 복사'>{safe_display_url}</span>"
                    cols[4].markdown(link_html, unsafe_allow_html=True)
                    
                    # 6. 수정 버튼
                    if st.session_state.authenticated:
                        if len(cols) > 5 and cols[5].button("✏️", key=f"el_{idx}", type="tertiary"):
                            edit_link_dialog(idx, row.to_dict(), unique_links_cats1, unique_links_cats2)

        except Exception as e: st.error(f"링크 데이터 오류 발생: {e}")

    # --- 공통 푸터 ---
    current_year = datetime.now(timezone(timedelta(hours=9))).year
    st.markdown(f"""
        <div style='text-align: center; margin-top: 30px; margin-bottom: 20px; padding-top: 15px; border-top: 1px dotted rgba(255, 255, 255, 0.2);'>
            <p style='color: #A3B8B8; font-size: 1.7rem; font-weight: bold; margin-bottom: 5px;'>
                Copyright © {current_year} TOmBOy94 &nbsp;|&nbsp; lodus11st@naver.com &nbsp;|&nbsp; All rights reserved.
            </p>
        </div>
    """, unsafe_allow_html=True)
