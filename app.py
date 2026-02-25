import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io
import math
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
    
    /* 토글 스위치(심플모드) 라벨 */
    div[data-testid="stToggle"] label p,
    div[data-testid="stWidgetLabel"] p {
        color: #FFFFFF !important;
        font-weight: bold !important;
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
        padding: 2px 12px !important; /* 상하 패딩 추가 축소 */
        border-radius: 12px;
        margin-bottom: 0px;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover {
        background-color: #1a2f2f !important;
    }

    /* 4. 상단 분류 리스트(Radio) 텍스트 버튼화 */
    div[role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 10px 25px !important;
        padding-top: 10px !important;
    }
    div[role="radiogroup"] div[role="radio"] {
        display: none !important;
    }
    div[role="radiogroup"] label {
        cursor: pointer !important;
        margin: 0 !important;
    }
    div[role="radiogroup"] label p {
        color: #A3B8B8 !important;
        font-size: 1.15rem !important;
        font-weight: 800 !important;
        transition: color 0.2s ease;
    }
    div[role="radiogroup"] label:hover p {
        color: #FFFFFF !important;
    }
    div[role="radiogroup"] label:has(div[aria-checked="true"]) p {
        color: #FFD700 !important;
        text-decoration: underline;
    }

    /* 5. 입력창 스타일: 배경 화이트 / 글자 블랙 */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 50px !important;
        padding-left: 15px !important;
        font-weight: 700 !important;
        border: 1px solid #FFFFFF !important;
    }

    /* ★ 6. 패스워드 눈알 아이콘 숨기기 (모바일 입력 최적화) ★ */
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
    }
    button[kind="secondary"], div.stDownloadButton > button {
        background-color: transparent !important;
        border: 2px solid #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* ★ 8. 헤더 라벨 전용 스타일 ★ */
    .header-label {
        font-size: 1.6rem !important;
        font-weight: 800 !important;
        color: #FFFFFF !important;
        display: block;
        margin-bottom: 0px !important;
    }

    /* 정렬 헤더 버튼 크기 및 간격 조정 */
    .sort-header-btn button {
        background-color: transparent !important;
        border: none !important;
        padding: 0 !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 1.6rem !important;
        text-decoration: underline !important;
    }

    /* ★ 구분선 간격 압축 (최소화) ★ */
    hr {
        margin-top: 0px !important;
        margin-bottom: 5px !important;
        border-top: 1px dotted rgba(255, 255, 255, 0.3) !important;
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
# 세션 상태 초기화 (랜덤 안정성을 위한 변수 포함)
if "authenticated" not in st.session_state:
    if st.query_params.get("auth") == "true":
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

if 'sort_order' not in st.session_state:
    st.session_state.sort_order = 'None'

if 'current_cat' not in st.session_state:
    st.session_state.current_cat = "🔀 랜덤 10" # 첫 시작 시 기본 카테고리 기록

col_title, col_auth = st.columns([7, 2])
with col_title:
    st.markdown("<h1 style='color:#FFF; padding-top: 0.5rem;'>TOmBOy94's English</h1>", unsafe_allow_html=True)
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
    
    # ★ 상단 카테고리 필터 ('🔀 랜덤 10'을 맨 앞에 추가) ★
    unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
    cat_options = ["🔀 랜덤 10", "전체 분류"] + unique_cats
    selected_radio = st.radio("분류 필터", cat_options, horizontal=True, label_visibility="collapsed")
    sel_cat = selected_radio
    
    # ★ 새로고침 전용 버튼 (랜덤 10 상태일 때만 노출) ★
    if sel_cat == "🔀 랜덤 10":
        _, btn_col = st.columns([8.5, 1.5])
        with btn_col:
            if st.button("🔄 10개 다시 뽑기", type="primary", use_container_width=True):
                st.session_state.random_df = df.sample(n=min(10, len(df)))
                st.rerun()

    st.divider()
    
    # 컨트롤바
    if st.session_state.authenticated:
        cb = st.columns([1.5, 1.2, 0.3, 4.0, 1.5])
        if cb[0].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(sheet, df)
        is_simple = cb[1].toggle("심플모드")
        search = cb[3].text_input("검색", placeholder="검색어 입력...", label_visibility="collapsed")
    else:
        cb = st.columns([1.2, 0.3, 5.5, 1.5])
        is_simple = cb[0].toggle("심플모드")
        search = cb[2].text_input("검색", placeholder="검색어 입력...", label_visibility="collapsed")

    # ★ 필터링 및 랜덤 데이터 추출 로직 ★
    d_df = df.copy()
    
    if sel_cat == "🔀 랜덤 10":
        # 사용자가 다른 카테고리에서 '랜덤 10'으로 막 넘어왔거나, 처음 시작할 때만 새로운 10개를 뽑음
        if st.session_state.current_cat != "🔀 랜덤 10" or 'random_df' not in st.session_state:
            st.session_state.random_df = df.sample(n=min(10, len(df)))
        # 심플모드 토글이나 검색 시 문장이 안 바뀌게 저장된 랜덤 데이터 사용
        d_df = st.session_state.random_df.copy()
    elif sel_cat != "전체 분류":
        d_df = d_df[d_df['분류'] == sel_cat]
        
    st.session_state.current_cat = sel_cat # 현재 선택된 카테고리 저장
    
    # '단어-문장' 열에서만 검색
    if search:
        d_df = d_df[d_df['단어-문장'].str.contains(search, case=False, na=False)]

    # 정렬
    if st.session_state.sort_order == 'asc': d_df = d_df.sort_values(by='단어-문장', ascending=True)
    elif st.session_state.sort_order == 'desc': d_df = d_df.sort_values(by='단어-문장', ascending=False)
    else: d_df = d_df.iloc[::-1]

    # CSV 다운로드
    if st.session_state.authenticated:
        cb[4].download_button("📥 CSV", d_df.to_csv(index=False).encode('utf-8-sig'), f"Data_{time.strftime('%Y%m%d')}.csv", use_container_width=True)

    # 페이지네이션 변수 초기화
    total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
    if 'curr_p' not in st.session_state: st.session_state.curr_p = 1
    if st.session_state.curr_p > pages: st.session_state.curr_p = 1
    curr_p = st.session_state.curr_p
    
    # 한국 시간 기준 날짜 계산
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    date_str = now_kst.strftime("%A, %B %d, %Y")
    
    st.markdown(f"""
        <p style='color:#FFF; font-weight:bold; margin-top:15px;'>
            총 {total}개 (페이지: {curr_p}/{pages}) &nbsp;&nbsp;&nbsp;&nbsp;
            <span style='color: #FFD700;'>📅 {date_str}</span>
        </p>
    """, unsafe_allow_html=True)
    
    # 리스트 헤더 출력
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
    
    st.divider()

    # 리스트 본문 (★ Duplicate Key 에러 해결: pandas의 원래 idx 사용)
    for idx, row in d_df.iloc[(curr_p-1)*100 : curr_p*100].iterrows():
        cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
        
        # 호버 효과를 위한 투명 마커
        cols[0].markdown(f"<span class='row-marker'></span>{row['분류']}", unsafe_allow_html=True)
        
        cols[1].markdown(f"<span style='font-size:2.0em;font-weight:bold;display:block;'>{row['단어-문장']}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span style='font-size:1.5em;display:block;'>{row['해석']}</span>", unsafe_allow_html=True)
        if not is_simple:
            cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
            if st.session_state.authenticated and cols[6].button("✏️", key=f"e_{idx}"): edit_dialog(idx, row, sheet, df)
        elif st.session_state.authenticated and cols[3].button("✏️", key=f"es_{idx}"): edit_dialog(idx, row, sheet, df)
        
        # 점선 간격 극소화 (-25px 적용)
        st.markdown("<div style='border-bottom:1px dotted rgba(255,255,255,0.2);margin-top:-25px;margin-bottom:2px;'></div>", unsafe_allow_html=True)

    # 하단 페이지네이션
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
