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
if 'curr_p' not in st.session_state: st.session_state.curr_p = 1  # 페이지 초기화

# --- [보안 설정] ---
LOGIN_PASSWORD = st.secrets.get("tom_password", "3709")

# --- [사용자 정의 디자인 (CSS)] ---
st.markdown("""
    <style>
    /* 1. 배경 설정 */
    [data-testid="stAppViewContainer"] {
        background-color: #224343 !important;
    }
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 2. 글자색 기본 설정 */
    h1, h2, h3, h4, h5, h6, p, span, label, b, strong {
        color: #FFFFFF !important;
    }

    /* 3. 입력창 디자인 및 가시성 */
    .stTextInput input {
        height: 50px !important;
        font-size: 1.2rem !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stTextInput"] button { display: none !important; }

    /* 4. 컨텐츠 행 호버 효과 */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 16px 10px !important;
        border-bottom: 1px dotted rgba(255, 255, 255, 0.2) !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        background-color: rgba(26, 47, 47, 0.9) !important;
    }

    /* 5. 분류 필터 알약 디자인 */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 10px 12px !important;
    }
    div[data-testid="stRadio"] label > div:first-of-type { display: none !important; }
    div[data-testid="stRadio"] label {
        cursor: pointer !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        padding: 6px 18px !important;
        border-radius: 50px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) {
        background-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) p {
        color: #224343 !important;
    }

    /* 6. ★ 페이지 번호 디자인: 배경 제거, 숫자 2rem 확대, 중앙 정렬 ★ */
    div.page-nav-container {
        display: flex !important;
        justify-content: center !important;
        align-items: center !important;
        gap: 20px !important;
        margin-top: 40px !important;
        width: 100% !important;
    }

    div.page-nav-container button {
        background-color: transparent !important; /* 배경 투명 */
        border: none !important; /* 테두리 제거 */
        box-shadow: none !important;
        color: #FFFFFF !important; /* 기본 흰색 */
        font-size: 2.2rem !important; /* 요청하신 크기 */
        font-weight: 800 !important;
        transition: all 0.2s ease !important;
        min-width: 50px !important;
    }

    /* 현재 활성화된 페이지 숫자 */
    div.page-nav-container button[kind="primary"] p {
        color: #FFD700 !important; /* 현재 페이지는 골드색 */
        font-size: 2.5rem !important;
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5) !important;
    }

    /* 호버 시 숫자 효과 */
    div.page-nav-container button:hover p {
        color: #FFD700 !important;
        transform: scale(1.1);
    }

    /* 8. 목록 텍스트 스타일 */
    .word-text { font-size: 1.98em; font-weight: bold; color: #FFD700 !important; word-break: keep-all; transition: transform 0.2s ease !important; transform-origin: left center !important; }
    .mean-text { font-size: 1.3em; word-break: keep-all; }
    
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover .word-text {
        transform: scale(1.1) !important;
        z-index: 10 !important;
    }

    /* 모바일 가시성 보정 */
    @media screen and (max-width: 768px) {
        .word-text { font-size: 1.21rem !important; }
        .mean-text { font-size: 0.9rem !important; }
        div.page-nav-container button { font-size: 1.8rem !important; min-width: 40px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- [Google Sheets 연결 함수] ---
@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

def get_sheet():
    return init_connection().open("English_Sentences").sheet1

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
    return pd.DataFrame()

# --- [콜백 함수들] ---
def handle_search():
    st.session_state.active_search = st.session_state.search_input.strip()
    st.session_state.search_input = ""
    st.session_state.curr_p = 1

def clear_search():
    st.session_state.active_search = ""
    st.session_state.curr_p = 1

# --- [메인 앱 로직] ---
if not st.session_state.authenticated and st.session_state.logging_in:
    # 로그인 화면
    st.write("## 🔐 Security Login")
    with st.form("login_form"):
        pwd = st.text_input("Enter Password", type="password")
        if st.form_submit_button("✅ LOGIN", use_container_width=True, type="primary"):
            if pwd == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.logging_in = False
                st.query_params["auth"] = "true"
                st.rerun()
            else: st.error("❌ 비밀번호가 틀렸습니다.")
    if st.button("🔙 CANCEL", use_container_width=True):
        st.session_state.logging_in = False
        st.rerun()
else:
    # 메인 헤더 (로그인 버튼 및 날짜)
    col_auth, col_date = st.columns([2, 8])
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
    
    with col_date:
        kst = timezone(timedelta(hours=9))
        date_str = datetime.now(kst).strftime("%A, %B %d, %Y")
        components.html(f"<div style='text-align:right;color:#FFF;font-family:sans-serif;font-weight:bold;font-size:1.5rem;'>📅 {date_str}</div>", height=40)

    st.markdown("<h1 style='text-align:center;'>TOmBOy94 English</h1>", unsafe_allow_html=True)

    try:
        sheet = get_sheet(); df = load_dataframe(sheet)
        unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
        
        # 카테고리 필터
        sel_cat = st.radio("분류 필터", ["🔀 랜덤 10", "전체 분류"] + unique_cats, horizontal=True, label_visibility="collapsed", key="cat_radio", on_change=clear_search)
        st.divider()

        # 검색창 및 제어 버튼
        cb = st.columns([2, 1.5, 1.5, 3, 2])
        cb[0].text_input("🔍", key="search_input", on_change=handle_search, placeholder="Search...")
        if st.session_state.authenticated and cb[1].button("➕ 추가", type="primary", use_container_width=True): pass # add dialog logic
        if cb[2].button("✨ 심플" if not st.session_state.is_simple else "🔄 전체", use_container_width=True):
            st.session_state.is_simple = not st.session_state.is_simple; st.rerun()

        # 데이터 필터링
        d_df = df.copy()
        if st.session_state.active_search:
            d_df = d_df[d_df['단어-문장'].str.contains(st.session_state.active_search, case=False, na=False)]
        elif sel_cat == "🔀 랜덤 10":
            if 'random_df' not in st.session_state or st.session_state.current_cat != "🔀 랜덤 10":
                st.session_state.random_df = df.sample(n=min(10, len(df)))
            d_df = st.session_state.random_df.copy()
        elif sel_cat != "전체 분류":
            d_df = d_df[d_df['분류'] == sel_cat]
        st.session_state.current_cat = sel_cat

        # 정렬 (기본 최신순)
        if st.session_state.sort_order == 'asc': d_df = d_df.sort_values(by='단어-문장', ascending=True)
        elif st.session_state.sort_order == 'desc': d_df = d_df.sort_values(by='단어-문장', ascending=False)
        else: d_df = d_df.iloc[::-1]

        total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
        st.write(f"총 {total}개 데이터")

        # 목록 출력 헤더
        ratio = [1.5, 6, 4.5] if st.session_state.is_simple else [1.2, 4, 2.5, 2, 2.5]
        h_cols = st.columns(ratio)
        labels = ["분류", "단어-문장", "해석", "발음", "메모1"]
        for i, l in enumerate(labels[:len(ratio)]):
            h_cols[i].markdown(f"**{l}**")
        st.divider()

        # 목록 루프 (100개씩 페이징)
        start_idx = (st.session_state.curr_p - 1) * 100
        end_idx = start_idx + 100
        for idx, row in d_df.iloc[start_idx:end_idx].iterrows():
            cols = st.columns(ratio)
            cols[0].markdown(f"<span class='row-marker'></span>{row['분류']}", unsafe_allow_html=True)
            cols[1].markdown(f"<span class='word-text'>{row['단어-문장']}</span>", unsafe_allow_html=True)
            cols[2].markdown(f"<span class='mean-text'>{row['해석']}</span>", unsafe_allow_html=True)
            if not st.session_state.is_simple:
                cols[3].write(row['발음']); cols[4].write(row['메모1'])

        # ★ 중앙 정렬된 대왕 숫자 페이지 내비게이션 ★
        if pages > 1:
            st.markdown('<div class="page-nav-container">', unsafe_allow_html=True)
            p_range = range(max(1, st.session_state.curr_p-2), min(pages, st.session_state.curr_p+2)+1)
            
            # 중앙 배치를 위해 빈 컬럼 활용
            p_cols = st.columns([2.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 2.5])
            
            # 이전 화살표
            if p_cols[1].button("«", disabled=(st.session_state.curr_p == 1), key="prev_p"):
                st.session_state.curr_p -= 1; st.rerun()
            
            # 숫자 버튼들
            for i, p_num in enumerate(p_range):
                btn_kind = "primary" if p_num == st.session_state.curr_p else "secondary"
                if p_cols[i+2].button(str(p_num), key=f"p_{p_num}", type=btn_kind):
                    st.session_state.curr_p = p_num; st.rerun()
            
            # 다음 화살표
            if p_cols[len(p_range)+2].button("»", disabled=(st.session_state.curr_p == pages), key="next_p"):
                st.session_state.curr_p += 1; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e: st.error(f"오류 발생: {e}")

    # 푸터
    st.markdown(f"<div style='text-align:center;margin-top:50px;opacity:0.5;'>Copyright © 2026 TOmBOy94</div>", unsafe_allow_html=True)
