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
if 'curr_p' not in st.session_state: st.session_state.curr_p = 1 

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
    h1 { margin-bottom: 0px !important; padding-bottom: 0px !important; }
    
    /* 3. 로그인 입력창 모바일 최적화 */
    .stTextInput input {
        height: 50px !important;
        font-size: 1.2rem !important;
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 10px !important;
    }
    div[data-testid="stTextInput"] button { display: none !important; }

    /* 4. 컨텐츠 행(Row) 호버 효과 */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 16px 10px !important;
        border-bottom: 1px dotted rgba(255, 255, 255, 0.2) !important; 
        width: 100% !important; 
        display: flex !important;
        align-items: center !important; 
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        background-color: rgba(26, 47, 47, 0.9) !important;
    }
    
    /* 5. 상단 분류 리스트(Radio) 알약 형태 */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 10px 12px !important;
        padding-top: 0px !important; 
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

    /* 6. 버튼 스타일 */
    button, div.stDownloadButton > button {
        border-radius: 50px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 900 !important;
    }
    
    /* 페이지 번호 버튼 전용 스타일 */
    div.page-num-container button {
        padding: 0.2rem 0.8rem !important;
        min-width: 40px !important;
        margin: 0 2px !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
    }

    /* 8. 텍스트 스타일 */
    .word-text { font-size: 1.98em; font-weight: bold; color: #FFD700 !important; word-break: keep-all; transition: transform 0.2s ease !important; transform-origin: left center !important; }
    .mean-text { font-size: 1.3em; word-break: keep-all; }
    .cat-text-bold { font-weight: bold !important; font-size: 0.95rem; }
   
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover .word-text {
        transform: scale(1.1) !important;
        z-index: 10 !important;
    }

    /* 10. Num.ENG 결과물 ❌ 버튼 가로 밀착 */
    div[data-testid="stHorizontalBlock"]:has(.num-result) {
        display: flex !important;
        align-items: center !important;
        gap: 12px !important; 
    }
    .num-result { color: #FFD700 !important; font-weight: bold; font-size: clamp(1.6rem, 2.2vw, 2.4rem) !important; line-height: 1.1; }

    @media screen and (max-width: 768px) {
        .word-text { font-size: 1.21rem !important; }
        .mean-text { font-size: 0.9rem !important; }
        div[data-testid="stRadio"] label p { font-size: 1.2rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

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
if not st.session_state.authenticated and st.session_state.logging_in:
    st.write("## 🔐 Security Login")
    with st.form("login_form", clear_on_submit=False):
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        pwd = st.text_input("Enter Password", type="password", placeholder="비밀번호를 입력하세요...")
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
        else: st.markdown("<p class='num-result' style='color:#FF9999!important; font-size:1.5rem!important;'>⚠️ 숫자만 입력 가능</p>", unsafe_allow_html=True)

    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst); date_str = now_kst.strftime("%A, %B %d, %Y")
    col_title, col_date = st.columns([4.0, 6.0])
    with col_title: st.markdown("<h1 style='color:#FFF; padding-top: 0.5rem; font-size: clamp(1.6rem, 2.9vw, 2.9rem);'>TOmBOy94 English</h1>", unsafe_allow_html=True)
    with col_date:
        components.html(f"""
            <style>
                body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: visible; }}
                .date-wrapper {{ display: flex; flex-wrap: wrap; align-items: center; gap: clamp(5px, 1.5vw, 15px); padding-top: 5px; font-family: sans-serif; width: 100%; }}
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
        """, height=90) 

    try:
        sheet = get_sheet(); df = load_dataframe(sheet)
        unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
        sel_cat = st.radio("분류 필터", ["🔀 랜덤 10", "전체 분류"] + unique_cats, horizontal=True, label_visibility="collapsed", key="cat_radio", on_change=clear_search)
        st.divider()
        
        cb_cols = [1.5, 1.5, 1.4, 2.6, 1.5] if st.session_state.authenticated else [1.5, 1.4, 4.1]
        cb = st.columns(cb_cols)
        cb[0].text_input("🔍", key="search_input", on_change=handle_search)
        if st.session_state.authenticated and cb[1].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(unique_cats)
        btn_idx = 2 if st.session_state.authenticated else 1
        btn_text = "🔄 전체모드" if st.session_state.is_simple else "✨ 심플모드"
        if cb[btn_idx].button(btn_text, type="primary" if not st.session_state.is_simple else "secondary", use_container_width=True):
            st.session_state.is_simple = not st.session_state.is_simple; st.rerun()

        is_simple = st.session_state.is_simple
        search = st.session_state.active_search; d_df = df.copy()
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

        if st.session_state.authenticated: cb[4].download_button("📥 CSV", d_df.to_csv(index=False).encode('utf-8-sig'), f"Data_{time.strftime('%Y%m%d')}.csv", use_container_width=True)

        total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
        curr_p = st.session_state.curr_p
        
        st.markdown(f"<div style='margin-bottom:10px;'><span style='color:#FF9999; font-weight:bold;'>{'🔍 ' + search if search else ''}</span> <span style='color:#FFF; font-weight:bold;'>총 {total}개</span></div>", unsafe_allow_html=True)
        
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

        # ★ 클릭 가능한 숫자형 페이지 내비게이션 ★
        if pages > 1:
            st.markdown("<div style='height:30px;'></div>", unsafe_allow_html=True)
            # 페이지 버튼들을 담을 수평 레이아웃 (최대 11개 버튼: 이전 + 숫자들 + 다음)
            p_range = range(max(1, curr_p-2), min(pages, curr_p+2)+1)
            p_cols = st.columns([1] * (len(p_range) + 2) + [5]) # 유동적 너비 조절
            
            # 이전 버튼
            if p_cols[0].button("◀", disabled=(curr_p == 1), key="prev_p"):
                st.session_state.curr_p -= 1
                st.rerun()
            
            # 숫자 버튼들
            for i, p_num in enumerate(p_range):
                btn_type = "primary" if p_num == curr_p else "secondary"
                if p_cols[i+1].button(str(p_num), key=f"p_{p_num}", type=btn_type):
                    st.session_state.curr_p = p_num
                    st.rerun()
            
            # 다음 버튼
            if p_cols[len(p_range)+1].button("▶", disabled=(curr_p == pages), key="next_p"):
                st.session_state.curr_p += 1
                st.rerun()

    except Exception as e: st.error(f"오류 발생: {e}")

    current_year = datetime.now(timezone(timedelta(hours=9))).year
    st.markdown(f"""
        <div style='text-align: center; margin-top: 30px; margin-bottom: 20px; padding-top: 15px; border-top: 1px dotted rgba(255, 255, 255, 0.2);'>
            <p style='color: #A3B8B8; font-size: 1.7rem; font-weight: bold; margin-bottom: 5px;'>
                Copyright © {current_year} TOmBOy94 &nbsp;|&nbsp; lodus11st@naver.com &nbsp;|&nbsp; All rights reserved.
            </p>
        </div>
    """, unsafe_allow_html=True)
