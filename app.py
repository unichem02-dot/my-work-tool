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
st.set_page_config(layout="wide", page_title="TOmBOy94's English")

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

    /* 로그인(Expander) 제목 */
    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] span,
    details summary p {
        color: #FFFFFF !important;
    }

    /* 3. ★ 컨텐츠 행(Row) 호버 효과 및 전체 영역 하이라이트 ★ */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 12px 15px !important;
        border-radius: 12px;
        margin-bottom: 2px;
        display: flex !important;
        flex-direction: row !important;
        flex-wrap: nowrap !important;
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        background-color: rgba(26, 47, 47, 0.9) !important;
    }

    /* 4. 상단 분류 리스트(Radio) 알약 형태 */
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
        text-decoration: none !important;
    }

    /* 5. 일반 입력창 스타일 */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 50px !important;
        padding-left: 15px !important;
        font-weight: 700 !important;
        border: 1px solid #FFFFFF !important;
    }

    /* 6. 패스워드 눈알 아이콘 숨기기 */
    div[data-testid="stTextInput"] button {
        display: none !important;
    }

    /* 7. 버튼 스타일 */
    button, div.stDownloadButton > button {
        border-radius: 50px !important;
        padding: 0.5rem 1.2rem !important;
        font-weight: 900 !important;
        transition: all 0.3s ease !important;
        white-space: nowrap !important;
    }
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }
    button[kind="primary"] p {
        color: #224343 !important;
        font-size: clamp(0.9rem, 1.1vw, 1.15rem) !important;
        font-weight: 900 !important;
    }
    button[kind="secondary"], div.stDownloadButton > button {
        background-color: transparent !important;
        border: 2px solid #FFFFFF !important;
        color: #FFFFFF !important;
    }
    button[kind="secondary"] p {
        font-size: clamp(0.9rem, 1.1vw, 1.15rem) !important;
        font-weight: 900 !important;
    }

    /* 8. 수정 버튼: 투명 연필 아이콘 */
    button[kind="tertiary"] {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        min-width: 40px !important;
        box-shadow: none !important;
    }
    button[kind="tertiary"] p {
        font-size: 1.6rem !important;
        margin: 0 !important;
        transition: transform 0.2s ease !important;
    }
    button[kind="tertiary"]:hover p {
        transform: scale(1.2) !important;
    }

    /* 9. 헤더 라벨 */
    .header-label, .sort-header-btn button { 
        font-size: clamp(1.0rem, 1.4vw, 1.5rem) !important; 
        font-weight: 800 !important; 
        color: #FFFFFF !important; 
        white-space: nowrap !important;
    }
   
    .word-text { font-size: 1.8em; font-weight: bold; display: block; color: #FFD700 !important; word-break: keep-all; }
    .mean-text { font-size: 1.3em; display: block; word-break: keep-all; }
   
    /* 10. 상단 검색창 크기 */
    div[data-testid="stTextInput"]:has(input[placeholder*="검색"]) {
        max-width: 160px !important;
    }

    /* Num.ENG 레이아웃 */
    div[data-testid="stTextInput"]:has(input[aria-label="Num.ENG :"]) {
        display: flex !important;
        flex-direction: row !important;
        align-items: center !important;
        gap: 8px !important;
        margin-top: 5px !important;
    }
    div[data-testid="stTextInput"]:has(input[aria-label="Num.ENG :"]) label p {
        font-weight: 900 !important;
        font-size: clamp(1.0rem, 1.4vw, 1.5rem) !important;
        white-space: nowrap !important;
        margin: 0 !important;
    }
    input[aria-label="Num.ENG :"] {
        font-size: clamp(1.0rem, 1.4vw, 1.5rem) !important;
        min-width: 90px !important;
    }
   
    .num-result { color: #FFD700; font-weight: bold; font-size: clamp(1.0rem, 1.4vw, 1.5rem); margin-top: 10px; }
   
    .row-divider { border-bottom: 1px dotted rgba(255,255,255,0.2); margin-top: -5px; margin-bottom: 5px; }

    /* 11. 모바일 레이아웃 교정 */
    @media screen and (max-width: 768px) {
        h1 { font-size: 1.4rem !important; }
        
        div[data-testid="stHorizontalBlock"]:has(.row-marker) {
            display: flex !important;
            flex-direction: row !important;
            padding: 8px 10px !important;
            gap: 10px !important;
        }

        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:nth-child(1) { width: 15% !important; min-width: 50px; } 
        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:nth-child(2) { width: 40% !important; } 
        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:nth-child(3) { width: 35% !important; } 
        div[data-testid="stHorizontalBlock"]:has(.row-marker) > div:last-child { width: 10% !important; min-width: 40px; text-align: right; } 

        .word-text { font-size: 1.1rem !important; }
        .mean-text { font-size: 0.9rem !important; }
        
        div[data-testid="stHorizontalBlock"] { gap: 5px !important; }
        button p { font-size: 0.85rem !important; }
        
        div[data-testid="stTextInput"]:has(input[aria-label="Num.ENG :"]) { gap: 5px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- [보안 설정] ---
LOGIN_PASSWORD = "0315"

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
def add_dialog(sheet, full_df):
    unique_cats = sorted([x for x in full_df['분류'].unique().tolist() if x != ''])
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
                sheet.append_row([final_cat, word_sent, mean, pron, m1, m2])
                st.success("저장 완료!"); time.sleep(1); st.rerun()

@st.dialog("항목 수정 및 삭제")
def edit_dialog(idx, row_data, sheet, full_df):
    unique_cats = sorted([x for x in full_df['분류'].unique().tolist() if x != ''])
    with st.form(f"edit_{idx}"):
        c1, c2 = st.columns(2)
        edit_cat = c1.selectbox("분류", unique_cats, index=unique_cats.index(row_data['분류']) if row_data['분류'] in unique_cats else 0)
        new_cat = c2.text_input("분류 직접 수정")
        word_sent = st.text_input("단어-문장", value=row_data['단어-문장'])
        c3, c4 = st.columns(2)
        mean = c3.text_input("해석", value=row_data['해석'])
        pron = c4.text_input("발음", value=row_data['발음'])
        m1 = st.text_input("메모1", value=row_data['메모1'])
        m2 = st.text_input("메모2", value=row_data['메모2'])
        b1, b2 = st.columns(2)
        if b1.form_submit_button("💾 저장", use_container_width=True, type="primary"):
            final_cat = new_cat.strip() if new_cat.strip() else edit_cat
            sheet.update(f"A{idx+2}:F{idx+2}", [[final_cat, word_sent, mean, pron, m1, m2]])
            st.rerun()
        if b2.form_submit_button("🗑️ 삭제", use_container_width=True):
            sheet.delete_rows(idx + 2); st.rerun()

# --- [메인 실행] ---
if "authenticated" not in st.session_state:
    if st.query_params.get("auth") == "true":
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

if 'sort_order' not in st.session_state:
    st.session_state.sort_order = 'None'

if 'current_cat' not in st.session_state:
    st.session_state.current_cat = "🔀 랜덤 10"

if 'num_input' not in st.session_state:
    st.session_state.num_input = ""

if 'active_search' not in st.session_state:
    st.session_state.active_search = ""
if 'search_input' not in st.session_state:
    st.session_state.search_input = ""

if 'is_simple' not in st.session_state:
    st.session_state.is_simple = False

def format_num_input():
    raw_val = str(st.session_state.num_input)
    cleaned = re.sub(r'[^0-9]', '', raw_val)
    if cleaned:
        st.session_state.num_input = f"{int(cleaned):,}"
    else:
        st.session_state.num_input = ""

def handle_search():
    val = st.session_state.search_input.strip()
    if val:
        st.session_state.active_search = val
    else:
        st.session_state.active_search = ""
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
            if n < 1000 ** (i + 1):
                return _convert(n // (1000 ** i)) + " " + scales[i] + (" " + _convert(n % (1000 ** i)) if n % (1000 ** i) != 0 else "")
        return str(n)
    return _convert(num).strip()

# 오늘 날짜 계산
kst = timezone(timedelta(hours=9))
now_kst = datetime.now(kst)
date_str = now_kst.strftime("%A, %B %d, %Y")

# 상단 레이아웃
col_title, col_date, col_num_combined, col_num_result, col_auth = st.columns([2.0, 3.2, 2.4, 2.0, 0.9])

with col_title:
    st.markdown("<h1 style='color:#FFF; padding-top: 0.5rem; font-size: clamp(1.2rem, 2.2vw, 2.2rem);'>TOmBOy94's English</h1>", unsafe_allow_html=True)

with col_date:
    # ★ 오늘 날짜 텍스트 크기 2배 확대 (clamp 값 조정) ★
    components.html(f"""
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: hidden; }}
            .date-wrapper {{
                display: flex; flex-wrap: wrap; align-items: center; gap: 15px;
                padding-top: 15px; font-family: sans-serif;
            }}
            .date-text {{
                color: #FFFFFF; font-weight: bold; 
                font-size: clamp(1.8rem, 2.8vw, 2.6rem); /* 2배로 확대 */
                white-space: nowrap;
            }}
            .copy-btn {{
                background-color: transparent; border: 1px solid rgba(255,255,255,0.5);
                color: #FFF; padding: 6px 12px; border-radius: 8px; cursor: pointer;
                font-size: clamp(1.0rem, 1.4vw, 1.3rem); font-weight:bold; transition: 0.3s;
                white-space: nowrap;
            }}
            .copy-btn:hover {{ background-color: rgba(255,255,255,0.2) !important; }}
        </style>
        <div class="date-wrapper">
            <span class="date-text">📅 {date_str}</span>
            <button class="copy-btn" onclick="copyDate()">📋 복사</button>
        </div>
        <script>
        function copyDate() {{
            var temp = document.createElement("textarea");
            temp.value = "{date_str}";
            document.body.appendChild(temp);
            temp.select();
            document.execCommand("copy");
            document.body.removeChild(temp);
           
            var btn = document.querySelector(".copy-btn");
            btn.innerHTML = "✅";
            setTimeout(function(){{ btn.innerHTML = "📋 복사"; }}, 1500);
        }}
        </script>
    """, height=120)
   
with col_num_combined:
    st.text_input("Num.ENG :", key="num_input", on_change=format_num_input)
    num_val = st.session_state.num_input
   
with col_num_result:
    if num_val:
        clean_num = num_val.replace(",", "").strip()
        if clean_num.isdigit():
            eng_text = num_to_eng(int(clean_num)).capitalize()
            st.markdown(f"<p class='num-result'>📝 {eng_text}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='num-result' style='color:#FF9999;'>⚠️ 숫자만</p>", unsafe_allow_html=True)

with col_auth:
    if not st.session_state.authenticated:
        with st.expander("🔐 로그인"):
            if st.text_input("Password", type="password") == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.query_params["auth"] = "true"
                st.rerun()
    else:
        if st.button("🔓 로그아웃", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            if "auth" in st.query_params: del st.query_params["auth"]
            st.rerun()

try:
    sheet = get_sheet(); df = load_dataframe(sheet)
   
    unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
    cat_options = ["🔀 랜덤 10", "전체 분류"] + unique_cats
    sel_cat = st.radio("분류 필터", cat_options, horizontal=True, label_visibility="collapsed", key="cat_radio", on_change=clear_search)
   
    st.divider()
   
    if st.session_state.authenticated:
        cb = st.columns([1.5, 1.5, 1.4, 2.6, 1.5])
        cb[0].text_input("검색", key="search_input", on_change=handle_search, placeholder="전체 검색 후 엔터...", label_visibility="collapsed")
        if cb[1].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(sheet, df)
       
        btn_text = "🔄 전체모드" if st.session_state.is_simple else "✨ 심플모드"
        btn_type = "secondary" if st.session_state.is_simple else "primary"
       
        if cb[2].button(btn_text, type=btn_type, use_container_width=True):
            st.session_state.is_simple = not st.session_state.is_simple
            st.rerun()
    else:
        cb = st.columns([1.5, 1.4, 4.1])
        cb[0].text_input("검색", key="search_input", on_change=handle_search, placeholder="전체 검색 후 엔터...", label_visibility="collapsed")
       
        btn_text = "🔄 전체모드" if st.session_state.is_simple else "✨ 심플모드"
        btn_type = "secondary" if st.session_state.is_simple else "primary"
       
        if cb[1].button(btn_text, type=btn_type, use_container_width=True):
            st.session_state.is_simple = not st.session_state.is_simple
            st.rerun()

    is_simple = st.session_state.is_simple
    search = st.session_state.active_search
    d_df = df.copy()
   
    if search:
        d_df = d_df[d_df['단어-문장'].str.contains(search, case=False, na=False)]
    else:
        if sel_cat == "🔀 랜덤 10":
            if st.session_state.current_cat != "🔀 랜덤 10" or 'random_df' not in st.session_state:
                st.session_state.random_df = df.sample(n=min(10, len(df)))
            d_df = st.session_state.random_df.copy()
        elif sel_cat != "전체 분류":
            d_df = d_df[d_df['분류'] == sel_cat]
        st.session_state.current_cat = sel_cat

    if st.session_state.sort_order == 'asc': d_df = d_df.sort_values(by='단어-문장', ascending=True)
    elif st.session_state.sort_order == 'desc': d_df = d_df.sort_values(by='단어-문장', ascending=False)
    else: d_df = d_df.iloc[::-1]

    if st.session_state.authenticated:
        cb[4].download_button("📥 CSV", d_df.to_csv(index=False).encode('utf-8-sig'), f"Data_{time.strftime('%Y%m%d')}.csv", use_container_width=True)

    total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
    if 'curr_p' not in st.session_state: st.session_state.curr_p = 1
    if st.session_state.curr_p > pages: st.session_state.curr_p = 1
    curr_p = st.session_state.curr_p

    search_msg = f"<span style='color: #FF9999; font-weight: bold; font-size: 0.9rem; margin-right: 15px;'>🔍 '{search}'</span>" if search else ""
   
    components.html(f"""
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: hidden; }}
        </style>
        <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-start; gap: 8px; padding-top: 5px; font-family: sans-serif;">
            {search_msg}
            <span style="color: #FFF; font-weight: bold; font-size: 0.95rem;">
                총 {total}개 (페이지: {curr_p}/{pages})
            </span>
        </div>
        <script>
        const doc = window.parent.document;
        if (!doc.formatListenerAdded) {{
            doc.body.addEventListener('input', function(e) {{
                if (e.target && e.target.getAttribute('aria-label') === 'Num.ENG :') {{
                    let rawVal = e.target.value.replace(/[^0-9]/g, '');
                    if (rawVal) {{
                        e.target.value = Number(rawVal).toLocaleString('en-US');
                    }} else {{
                        e.target.value = '';
                    }}
                }}
            }});
            doc.formatListenerAdded = true;
        }}
        </script>
    """, height=35)
   
    # 제목 행
    ratio = [1.5, 6, 4.5, 1] if is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1]
    labels = ["분류", "단어-문장", "해석", "수정"] if is_simple else ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
   
    h_cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
    for i, l in enumerate(labels if st.session_state.authenticated else labels[:-1]):
        if l == "단어-문장":
            sort_icon = " ↑" if st.session_state.sort_order == 'asc' else (" ↓" if st.session_state.sort_order == 'desc' else "")
            if h_cols[i].button(f"{l}{sort_icon}", key="sort_btn"):
                if st.session_state.sort_order == 'None': st.session_state.sort_order = 'asc'
                elif st.session_state.sort_order == 'asc': st.session_state.sort_order = 'desc'
                else: st.session_state.sort_order = 'None'
                st.rerun()
        else:
            h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
   
    st.markdown("<div style='border-bottom: 2px solid rgba(255,255,255,0.4); margin-top: -20px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)

    # 본문 리스트
    for idx, row in d_df.iloc[(curr_p-1)*100 : curr_p*100].iterrows():
        cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
       
        # ★ 분류 항목 텍스트 굵게(font-weight:bold) 적용 ★
        cols[0].markdown(f"<span class='row-marker'></span><span style='font-size:0.9rem; font-weight:bold;'>{row['분류']}</span>", unsafe_allow_html=True)
        cols[1].markdown(f"<span class='word-text'>{row['단어-문장']}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span class='mean-text'>{row['해석']}</span>", unsafe_allow_html=True)
       
        if not is_simple:
            cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
            if st.session_state.authenticated and cols[6].button("✏️", key=f"e_{idx}", type="tertiary"): edit_dialog(idx, row, sheet, df)
        elif st.session_state.authenticated and cols[3].button("✏️", key=f"es_{idx}", type="tertiary"): edit_dialog(idx, row, sheet, df)
       
        st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)

    # 페이지네이션
    if pages > 1:
        st.write(""); p_cols = st.columns([3.5, 1.5, 2, 1.5, 3.5])
        with p_cols[1]:
            if st.button("◀ 이전", key="btn_prev", disabled=(curr_p == 1), use_container_width=True):
                st.session_state.curr_p -= 1; st.rerun()
        with p_cols[2]:
            st.markdown(f"<div style='display: flex; justify-content: center; align-items: center; height: 100%;'><div style='background-color: rgba(255, 255, 255, 0.1); padding: 0.5rem 1.5rem; border-radius: 50px; border: 1px solid rgba(255,255,255,0.3); font-weight: bold; font-size: 1.1rem;'><span style='color: #FFD700;'>Page {curr_p}</span> <span style='color: #FFFFFF;'> / {pages}</span></div></div>", unsafe_allow_html=True)
        with p_cols[3]:
            if st.button("다음 ▶", key="btn_next", disabled=(curr_p == pages), use_container_width=True):
                st.session_state.curr_p += 1; st.rerun()

except Exception as e:
    st.error(f"오류 발생: {e}")

# --- [푸터(Footer)] ---
current_year = datetime.now(timezone(timedelta(hours=9))).year
st.markdown(f"""
    <div style='text-align: center; margin-top: 30px; margin-bottom: 20px; padding-top: 15px; border-top: 1px dotted rgba(255, 255, 255, 0.2);'>
        <p style='color: #A3B8B8; font-size: 0.85rem; font-weight: bold; margin-bottom: 5px;'>
            Copyright © {current_year} TOmBOy94 &nbsp;|&nbsp; lodus11st@naver.com &nbsp;|&nbsp; All rights reserved.
        </p>
    </div>
""", unsafe_allow_html=True)
