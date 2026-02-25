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

    /* 2. ★ 글자색 화이트 강제화 ★ */
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

    /* 3. ★ 컨텐츠 행(Row) 호버 효과 및 간격 최소화 ★ */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 2px 12px !important;
        border-radius: 12px;
        margin-bottom: 0px;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        background-color: #1a2f2f !important;
    }

    /* ★ 4. 상단 분류 리스트(Radio) 깔끔한 알약(태그) 형태로 디자인 개선 ★ */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 12px 15px !important;
        padding-top: 10px !important;
        padding-bottom: 5px !important;
    }
    
    /* 기존 동그란 라디오 아이콘 완벽하게 숨기기 */
    div[data-testid="stRadio"] label > div:first-of-type {
        display: none !important;
    }
    
    /* 라벨(버튼) 기본 스타일 */
    div[data-testid="stRadio"] label {
        cursor: pointer !important;
        margin: 0 !important;
        background-color: rgba(255, 255, 255, 0.1) !important;
        padding: 8px 22px !important;
        border-radius: 50px !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        transition: all 0.3s ease !important;
    }
    
    /* 마우스 호버 효과 */
    div[data-testid="stRadio"] label:hover {
        background-color: rgba(255, 255, 255, 0.2) !important;
        border-color: #FFD700 !important;
    }
    
    /* 텍스트 기본 상태 */
    div[data-testid="stRadio"] label p {
        color: #FFFFFF !important; 
        font-size: 1.4rem !important; 
        font-weight: 800 !important;
        transition: color 0.2s ease;
        margin: 0 !important;
    }
    
    /* ★ 선택된 분류 상태 (배경 노란색, 글자 다크그린) ★ */
    div[data-testid="stRadio"] label:has(input:checked),
    div[data-testid="stRadio"] label:has(div[aria-checked="true"]) {
        background-color: #FFD700 !important;
        border-color: #FFD700 !important;
    }
    
    div[data-testid="stRadio"] label:has(input:checked) p,
    div[data-testid="stRadio"] label:has(div[aria-checked="true"]) p {
        color: #224343 !important; /* 다크그린 배경을 글자색으로 */
        text-decoration: none !important; /* 밑줄 제거 */
    }

    /* 5. 일반 입력창 스타일: 배경 화이트 / 글자 블랙 */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 50px !important;
        padding-left: 15px !important;
        font-weight: 700 !important;
        border: 1px solid #FFFFFF !important;
    }

    /* 특정 입력창(숫자입력) 폰트 크기 확대 (1.6rem) - 내부 라벨로 추적 */
    input[aria-label="숫자입력"] {
        font-size: 1.6rem !important;
    }

    /* 6. 패스워드 눈알 아이콘 숨기기 (모바일 입력 최적화) */
    div[data-testid="stTextInput"] button {
        display: none !important;
    }

    /* 7. 버튼 스타일: 알약 모양 */
    button, div.stDownloadButton > button {
        border-radius: 50px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }
    button[kind="primary"] p {
        color: #224343 !important;
        font-size: 1.15rem !important;
    }
    button[kind="secondary"], div.stDownloadButton > button {
        background-color: transparent !important;
        border: 2px solid #FFFFFF !important;
        color: #FFFFFF !important;
    }
    button[kind="secondary"] p {
        font-size: 1.15rem !important;
    }

    /* 8. 헤더 및 일반 텍스트용 클래스 (모바일 대응을 위한 분리) */
    .header-label { font-size: 1.6rem !important; font-weight: 800 !important; color: #FFFFFF !important; display: block; margin-bottom: 0px !important; }
    .sort-header-btn button { background-color: transparent !important; border: none !important; padding: 0 !important; color: #FFFFFF !important; font-weight: 800 !important; font-size: 1.6rem !important; text-decoration: underline !important; }
    
    .word-text { font-size: 2.0em; font-weight: bold; display: block; }
    .mean-text { font-size: 1.5em; display: block; }
    
    /* 상단 숫자 변환 라벨 및 결과용 클래스 */
    .num-label { color: #FFF; font-weight: bold; margin-top: 12px; text-align: right; font-size: 1.6rem; }
    .num-result { color: #FFD700; font-weight: bold; font-size: 1.6rem; margin-top: 12px; }
    .num-warning { color: #FF9999; font-weight: bold; font-size: 1.2rem; margin-top: 16px; }
    .num-input-container { margin-top: 8px; }
    
    .row-divider { border-bottom: 1px dotted rgba(255,255,255,0.2); margin-top: -25px; margin-bottom: 2px; }

    /* ★ 9. 모바일 반응형(Responsive) 디자인 최적화 ★ */
    @media screen and (max-width: 768px) {
        /* 타이틀 및 상단 간격 축소 */
        h1 { font-size: 1.8rem !important; }
        
        /* 모바일에서는 라벨을 좌측 정렬하고 폰트 크기 조정 */
        .num-label { font-size: 1.2rem !important; text-align: left !important; margin-top: 5px !important; }
        .num-result { font-size: 1.3rem !important; margin-top: 5px !important; }
        .num-warning { margin-top: 5px !important; }
        .num-input-container { margin-top: 0px !important; }
        input[aria-label="숫자입력"] { font-size: 1.3rem !important; }
        
        /* 리스트 본문 글자 크기 축소 */
        .word-text { font-size: 1.4em !important; }
        .mean-text { font-size: 1.1em !important; }
        
        /* 모바일에서는 표(가로) 형태가 아닌 카드(세로) 형태로 보여지므로 배경색과 패딩 추가 */
        div[data-testid="stHorizontalBlock"]:has(.row-marker) {
            padding: 15px !important;
            background-color: rgba(255, 255, 255, 0.05) !important;
            border-radius: 15px;
            margin-bottom: 15px !important;
            gap: 0.3rem !important;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        /* 카드형태에서는 점선이 겹치므로 제거 */
        .row-divider { display: none !important; }
        
        /* 버튼류 및 분류 텍스트 모바일용 축소 */
        .header-label { font-size: 1.2rem !important; }
        .sort-header-btn button { font-size: 1.2rem !important; }
        button[kind="primary"] p { font-size: 1.0rem !important; }
        button[kind="secondary"] p { font-size: 1.0rem !important; }
        
        /* 모바일용 분류 알약 버튼 사이즈 조정 */
        div[data-testid="stRadio"] > div[role="radiogroup"] { gap: 8px 10px !important; }
        div[data-testid="stRadio"] label { padding: 6px 16px !important; }
        div[data-testid="stRadio"] label p { font-size: 1.1rem !important; }
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

# ★ 상단 레이아웃 (타이틀 + 날짜 + 숫자변환 + 로그인) ★
# 날짜 영역이 잘리지 않도록 컬럼 가로 비율 조정 (col_date 영역 확대: 1.7 -> 2.5)
col_title, col_date, col_num_label, col_num_input, col_num_result, col_auth = st.columns([2.2, 2.5, 0.9, 1.5, 2.0, 0.9])

with col_title:
    st.markdown("<h1 style='color:#FFF; padding-top: 0.5rem;'>TOmBOy94's English</h1>", unsafe_allow_html=True)

with col_date:
    # ★ 줄바꿈 방지(white-space: nowrap) 추가 및 높이(height) 확대 ★
    components.html(f"""
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: hidden; }}
            button:hover {{ background-color: rgba(255,255,255,0.2) !important; }}
        </style>
        <div style="display: flex; align-items: center; gap: 8px; padding-top: 15px; font-family: sans-serif; white-space: nowrap;">
            <span style="color: #FFFFFF; font-weight: bold; font-size: 1.3rem;">
                📅 {date_str}
            </span>
            <button onclick="copyDate()" style="background-color: transparent; border: 1px solid rgba(255,255,255,0.5); color: #FFF; padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 0.9rem; font-weight:bold; transition: 0.3s; margin-top: 2px; white-space: nowrap;">
                📋 복사
            </button>
        </div>
        <script>
        function copyDate() {{
            var temp = document.createElement("textarea");
            temp.value = "{date_str}";
            document.body.appendChild(temp);
            temp.select();
            document.execCommand("copy");
            document.body.removeChild(temp);
            
            var btn = document.querySelector("button");
            btn.innerHTML = "✅";
            setTimeout(function(){{ btn.innerHTML = "📋 복사"; }}, 2000);
        }}
        </script>
    """, height=80)

with col_num_label:
    st.markdown("<p class='num-label'>Num.ENG :</p>", unsafe_allow_html=True)
    
with col_num_input:
    st.markdown("<div class='num-input-container'>", unsafe_allow_html=True)
    st.text_input("숫자입력", key="num_input", on_change=format_num_input, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)
    num_val = st.session_state.num_input
    
with col_num_result:
    if num_val:
        clean_num = num_val.replace(",", "").strip()
        if clean_num.isdigit():
            eng_text = num_to_eng(int(clean_num)).capitalize()
            st.markdown(f"<p class='num-result'>📝 {eng_text}</p>", unsafe_allow_html=True)
        else:
            st.markdown("<p class='num-warning'>⚠️ 숫자만 입력해주세요.</p>", unsafe_allow_html=True)

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
        cb = st.columns([3.8, 1.5, 1.4, 0.3, 1.5])
        cb[0].text_input("검색", key="search_input", on_change=handle_search, placeholder="전체 검색 후 엔터...", label_visibility="collapsed")
        if cb[1].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(sheet, df)
        
        btn_text = "🔄 전체모드" if st.session_state.is_simple else "✨ 심플모드"
        btn_type = "secondary" if st.session_state.is_simple else "primary"
        
        if cb[2].button(btn_text, type=btn_type, use_container_width=True):
            st.session_state.is_simple = not st.session_state.is_simple
            st.rerun()
    else:
        cb = st.columns([5.3, 1.4, 3.3])
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

    search_msg = f"<span style='color: #FF9999; font-weight: bold; font-size: 1rem; margin-right: 15px;'>🔍 '{search}' 검색됨</span>" if search else ""
    
    components.html(f"""
        <style>
            body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: hidden; }}
        </style>
        <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-start; gap: 8px; padding-top: 10px; font-family: sans-serif;">
            {search_msg}
            <span style="color: #FFF; font-weight: bold; font-size: 1rem;">
                총 {total}개 (페이지: {curr_p}/{pages})
            </span>
        </div>
        <script>
        const doc = window.parent.document;
        if (!doc.formatListenerAdded) {{
            doc.body.addEventListener('input', function(e) {{
                if (e.target && e.target.getAttribute('aria-label') === '숫자입력') {{
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
    """, height=40)
    
    ratio = [1.5, 6, 4.5, 1] if is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1]
    labels = ["분류", "단어-문장", "해석", "수정"] if is_simple else ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
    
    h_cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
    for i, l in enumerate(labels if st.session_state.authenticated else labels[:-1]):
        if l == "단어-문장":
            sort_icon = " ↑" if st.session_state.sort_order == 'asc' else (" ↓" if st.session_state.sort_order == 'desc' else "")
            st.markdown(f"<div class='sort-header-btn'>", unsafe_allow_html=True)
            if h_cols[i].button(f"**{l}{sort_icon}**", key="sort_btn"):
                if st.session_state.sort_order == 'None': st.session_state.sort_order = 'asc'
                elif st.session_state.sort_order == 'asc': st.session_state.sort_order = 'desc'
                else: st.session_state.sort_order = 'None'
                st.rerun()
            st.markdown(f"</div>", unsafe_allow_html=True)
        else:
            h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
    
    st.markdown("<div style='border-bottom: 2px solid rgba(255,255,255,0.4); margin-top: -20px; margin-bottom: 10px;'></div>", unsafe_allow_html=True)

    for idx, row in d_df.iloc[(curr_p-1)*100 : curr_p*100].iterrows():
        cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
        
        cols[0].markdown(f"<span class='row-marker'></span>{row['분류']}", unsafe_allow_html=True)
        cols[1].markdown(f"<span class='word-text'>{row['단어-문장']}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span class='mean-text'>{row['해석']}</span>", unsafe_allow_html=True)
        
        if not is_simple:
            cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
            if st.session_state.authenticated and cols[6].button("✏️", key=f"e_{idx}"): edit_dialog(idx, row, sheet, df)
        elif st.session_state.authenticated and cols[3].button("✏️", key=f"es_{idx}"): edit_dialog(idx, row, sheet, df)
        
        st.markdown("<div class='row-divider'></div>", unsafe_allow_html=True)

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

# --- [푸터(Footer) 추가] ---
current_year = datetime.now(timezone(timedelta(hours=9))).year
st.markdown(f"""
    <div style='text-align: center; margin-top: 50px; margin-bottom: 20px; padding-top: 20px; border-top: 1px dotted rgba(255, 255, 255, 0.2);'>
        <p style='color: #A3B8B8; font-size: 0.95rem; font-weight: bold; margin-bottom: 5px;'>
            Copyright © {current_year} TOmBOy94 &nbsp;|&nbsp; lodus11st@naver.com &nbsp;|&nbsp; All rights reserved.
        </p>
    </div>
""", unsafe_allow_html=True)
