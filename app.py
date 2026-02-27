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
# Streamlit Secrets에서 비밀번호 로드
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
    
    /* 3. 입력창 가시성 확보 (검은 글씨 강제) */
    .stTextInput input {
        height: 50px !important;
        font-size: 1.2rem !important;
        background-color: #FFFFFF !important;
        color: #000000 !important; /* ★ 글자색 검정으로 수정 ★ */
        border-radius: 10px !important;
    }
    /* 비밀번호 입력창 눈알 제거 */
    div[data-testid="stTextInput"] button { display: none !important; }

    /* 4. 컨텐츠 행(Row) 디자인 */
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 16px 10px !important;
        border-bottom: 1px dotted rgba(255, 255, 255, 0.2) !important; 
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

    /* 6. 페이지 번호 버튼 디자인 (가시성 및 모양 보정) */
    div.page-num-container button {
        background-color: rgba(255, 255, 255, 0.15) !important; /* 배경 어둡게 */
        color: #FFFFFF !important; /* 글자색 흰색 고정 */
        border: 1px solid rgba(255, 255, 255, 0.4) !important;
        border-radius: 50% !important;
        width: 45px !important;
        height: 45px !important;
        padding: 0 !important;
        font-weight: bold !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        transition: all 0.2s ease !important;
    }

    /* 현재 페이지 활성화 스타일 */
    div.page-num-container button[kind="primary"] {
        background-color: #FFD700 !important;
        color: #224343 !important; /* 짙은 초록 글씨 */
        border: 1px solid #FFD700 !important;
        box-shadow: 0 0 12px rgba(255, 215, 0, 0.5) !important;
    }

    /* 페이지 버튼 호버 */
    div.page-num-container button:hover {
        border-color: #FFD700 !important;
        transform: translateY(-2px);
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

    /* 모바일 반응형 최적화 (가려짐 및 겹침 해결) */
    @media screen and (max-width: 768px) {
        .word-text { font-size: 1.21rem !important; }
        .mean-text { font-size: 0.9rem !important; }
        div[data-testid="stRadio"] label p { font-size: 1.2rem !important; }
        
        /* 모바일 제어 버튼 간격 확보 */
        div[data-testid="column"] button {
            width: 100% !important;
            margin-bottom: 5px !important;
        }
        
        /* 모바일 페이지 버튼 크기 조정 */
        div.page-num-container button {
            width: 38px !important;
            height: 38px !important;
            font-size: 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# [심플모드 확대 CSS]
if st.session_state.is_simple:
    st.markdown("<style>@media screen and (max-width:768px){.word-text{font-size:1.7rem!important;line-height:1.3!important;}.mean-text{font-size:1.26rem!important;line-height:1.3!important;}}</style>", unsafe_allow_html=True)

# --- [Google Sheets 연동 함수들] ---
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

# --- [다이얼로그 설정] ---
@st.dialog("새 항목 추가")
def add_dialog(unique_cats):
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        selected_cat = c1.selectbox("기존 분류", ["(새로 입력)"] + unique_cats)
        new_cat = c2.text_input("새 분류 입력")
        word_sent = st.text_input("단어-문장")
        c3, c4 = st.columns(2)
        mean = c3.text_input("해석"); pron = c4.text_input("발음")
        m1 = st.text_input("메모1"); m2 = st.text_input("메모2")
        if st.form_submit_button("저장하기", use_container_width=True, type="primary"):
            final_cat = new_cat.strip() if new_cat.strip() else (selected_cat if selected_cat != "(새로 입력)" else "")
            if word_sent:
                get_sheet().append_row([final_cat, word_sent, mean, pron, m1, m2])
                st.success("저장 완료!"); time.sleep(1); st.rerun()

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
            get_sheet().update(f"A{idx+2}:F{idx+2}", [[final_cat, word_sent, mean, pron, m1, m2]])
            st.rerun()
        if b2.form_submit_button("🗑️ 삭제", use_container_width=True):
            get_sheet().delete_rows(idx + 2); st.rerun()

# --- [메인 로직 시작] ---
if not st.session_state.authenticated and st.session_state.logging_in:
    st.write("## 🔐 Security Login")
    with st.form("login_form"):
        pwd = st.text_input("Enter Password", type="password")
        if st.form_submit_button("✅ LOGIN", use_container_width=True, type="primary"):
            if pwd == LOGIN_PASSWORD:
                st.session_state.authenticated = True; st.session_state.logging_in = False
                st.query_params["auth"] = "true"; st.rerun()
            else: st.error("❌ 비밀번호 오류")
    if st.button("🔙 CANCEL", use_container_width=True): st.session_state.logging_in = False; st.rerun()
else:
    # 1. 상단 인증 및 숫자 변환기
    col_auth, col_spacer, col_num = st.columns([2.0, 0.2, 7.8])
    with col_auth:
        if not st.session_state.authenticated:
            if st.button("🔐 LOGIN", use_container_width=True): st.session_state.logging_in = True; st.rerun()
        else:
            if st.button("🔓 LOGOUT", use_container_width=True, type="secondary"):
                st.session_state.authenticated = False; del st.query_params["auth"]; st.rerun()
    with col_num:
        st.text_input("Num.ENG :", key="num_input", on_change=lambda: setattr(st.session_state, 'num_input', f"{int(re.sub('[^0-9]', '', str(st.session_state.num_input))):,}" if re.sub('[^0-9]', '', str(st.session_state.num_input)) else ""))
    
    if st.session_state.num_input:
        clean_n = st.session_state.num_input.replace(",", "")
        if clean_n.isdigit():
            eng_t = num_to_eng(int(clean_n)).capitalize()
            r1, r2 = st.columns([8, 2])
            r1.markdown(f"<p class='num-result'>{eng_t}</p>", unsafe_allow_html=True)
            r2.button("❌", key="c_num", on_click=lambda: setattr(st.session_state, 'num_input', ""))

    # 2. 타이틀 및 날짜
    kst = timezone(timedelta(hours=9))
    date_str = datetime.now(kst).strftime("%A, %B %d, %Y")
    c_t, c_d = st.columns([4, 6])
    c_t.markdown("<h1 style='color:#FFF; padding-top: 0.5rem; font-size: clamp(1.6rem, 2.9vw, 2.9rem);'>TOmBOy94 English</h1>", unsafe_allow_html=True)
    with c_d:
        components.html(f"<div style='display:flex;align-items:center;gap:15px;color:#FFF;font-family:sans-serif;font-weight:bold;font-size:clamp(1.1rem,2.6vw,2.6rem);'>📅 {date_str} <button onclick=\"var t=document.createElement('textarea');t.value='{date_str}';document.body.appendChild(t);t.select();document.execCommand('copy');document.body.removeChild(t);this.innerHTML='✅';setTimeout(()=>{{this.innerHTML='📋';}},1000)\" style='background:transparent;border:1px solid #FFF;color:#FFF;cursor:pointer;padding:5px 10px;border-radius:5px;'>📋</button></div>", height=90)

    try:
        # 3. 데이터 로드 및 카테고리 필터
        sheet = get_sheet(); df = load_dataframe(sheet)
        unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
        sel_cat = st.radio("분류 필터", ["🔀 랜덤 10", "전체 분류"] + unique_cats, horizontal=True, label_visibility="collapsed", key="cat_radio", on_change=clear_search)
        st.divider()
        
        # 4. 제어 영역 (검색창 + 버튼들)
        # 모바일 대응을 위해 검색창을 별도 행으로 뺄 수도 있으나, 여기서는 컬럼 비율로 조정
        is_admin = st.session_state.authenticated
        cb = st.columns([3, 1.5, 1.5, 2, 1] if is_admin else [4, 2, 4])
        
        with cb[0]: st.text_input("🔍", key="search_input", on_change=handle_search, placeholder="Search...")
        
        if is_admin:
            if cb[1].button("➕ 새 항목", type="primary", use_container_width=True): add_dialog(unique_cats)
            if cb[2].button("✨ 심플" if not st.session_state.is_simple else "🔄 전체", use_container_width=True): st.session_state.is_simple = not st.session_state.is_simple; st.rerun()
            cb[4].download_button("📥 CSV", df.to_csv(index=False).encode('utf-8-sig'), "data.csv", use_container_width=True)
        else:
            if cb[1].button("✨ 심플모드" if not st.session_state.is_simple else "🔄 전체모드", use_container_width=True): st.session_state.is_simple = not st.session_state.is_simple; st.rerun()

        # 5. 데이터 필터링 로직
        d_df = df.copy()
        if st.session_state.active_search:
            d_df = d_df[d_df['단어-문장'].str.contains(st.session_state.active_search, case=False, na=False)]
        elif sel_cat == "🔀 랜덤 10":
            if st.session_state.current_cat != "🔀 랜덤 10" or 'random_df' not in st.session_state:
                st.session_state.random_df = df.sample(n=min(10, len(df)))
            d_df = st.session_state.random_df.copy()
        elif sel_cat != "전체 분류":
            d_df = d_df[d_df['분류'] == sel_cat]
        st.session_state.current_cat = sel_cat

        # 정렬
        if st.session_state.sort_order == 'asc': d_df = d_df.sort_values(by='단어-문장', ascending=True)
        elif st.session_state.sort_order == 'desc': d_df = d_df.sort_values(by='단어-문장', ascending=False)
        else: d_df = d_df.iloc[::-1]

        total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
        st.markdown(f"<div style='margin-bottom:10px;'><span style='color:#FF9999; font-weight:bold;'>{'🔍 '+st.session_state.active_search if st.session_state.active_search else ''}</span> <span style='color:#FFF;'>총 {total}개</span></div>", unsafe_allow_html=True)
        
        # 6. 리스트 출력
        ratio = [1.5, 6, 4.5, 1] if st.session_state.is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1]
        h_cols = st.columns(ratio if is_admin else ratio[:-1])
        labels = ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
        for i, l in enumerate(labels[:len(h_cols)]):
            if l == "단어-문장":
                icon = " ↑" if st.session_state.sort_order == 'asc' else (" ↓" if st.session_state.sort_order == 'desc' else "")
                if h_cols[i].button(f"{l}{icon}", key="s_btn"): st.session_state.sort_order = 'asc' if st.session_state.sort_order == 'None' else ('desc' if st.session_state.sort_order == 'asc' else 'None'); st.rerun()
            else: h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
        st.divider()

        # 목록 루프
        for idx, row in d_df.iloc[(st.session_state.curr_p-1)*100 : st.session_state.curr_p*100].iterrows():
            cols = st.columns(ratio if is_admin else ratio[:-1])
            cols[0].markdown(f"<span class='row-marker'></span><span class='cat-text-bold'>{row['분류']}</span>", unsafe_allow_html=True)
            cols[1].markdown(f"<span class='word-text'>{row['단어-문장']}</span>", unsafe_allow_html=True)
            cols[2].markdown(f"<span class='mean-text'>{row['해석']}</span>", unsafe_allow_html=True)
            if not st.session_state.is_simple:
                cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
                if is_admin and cols[6].button("✏️", key=f"e_{idx}", type="tertiary"): edit_dialog(idx, row.to_dict(), unique_cats)
            elif is_admin and cols[3].button("✏️", key=f"es_{idx}", type="tertiary"): edit_dialog(idx, row.to_dict(), unique_cats)

        # 7. ★ 중앙 정렬된 가시성 높은 페이지 내비게이션 ★
        if pages > 1:
            st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)
            p_range = range(max(1, st.session_state.curr_p-2), min(pages, st.session_state.curr_p+2)+1)
            
            # 중앙 배치를 위해 빈 컬럼 활용
            st.markdown('<div class="page-num-container">', unsafe_allow_html=True)
            p_cols = st.columns([3, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 3])
            
            # 이전
            if p_cols[1].button("◀", disabled=(st.session_state.curr_p == 1), key="prev_p"):
                st.session_state.curr_p -= 1; st.rerun()
            
            # 숫자 버튼들
            for i, p_num in enumerate(p_range):
                btn_kind = "primary" if p_num == st.session_state.curr_p else "secondary"
                if p_cols[i+2].button(str(p_num), key=f"p_{p_num}", type=btn_kind):
                    st.session_state.curr_p = p_num; st.rerun()
            
            # 다음
            if p_cols[len(p_range)+2].button("▶", disabled=(st.session_state.curr_p == pages), key="next_p"):
                st.session_state.curr_p += 1; st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e: st.error(f"오류: {e}")

    # 8. 푸터
    current_year = datetime.now(timezone(timedelta(hours=9))).year
    st.markdown(f"<div style='text-align: center; margin-top: 50px; padding: 20px; border-top: 1px dotted rgba(255,255,255,0.2); color: #A3B8B8; font-size: 1.2rem;'>Copyright © {current_year} TOmBOy94 | All rights reserved.</div>", unsafe_allow_html=True)
