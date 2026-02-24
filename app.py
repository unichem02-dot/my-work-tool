import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io
import math

# --- [페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="TOmBOy94's English")

# --- [사용자 정의 디자인 (CSS)] ---
st.markdown("""
    <style>
    /* 1. 배경 설정 */
    [data-testid="stAppViewContainer"], 
    div[data-testid="stDialog"] > div,
    div[role="dialog"] > div {
        background-color: #224343 !important; 
    }
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 2. 텍스트 무조건 흰색 강제화 */
    h1, h2, h3, h4, h5, h6, p, span, label, summary, b, strong {
        color: #FFFFFF !important;
    }
    
    div[data-testid="stToggle"] p, 
    div[data-testid="stToggle"] span {
        color: #FFFFFF !important; 
        font-weight: bold !important;
    }
    
    div[role="dialog"] h2, 
    div[data-testid="stDialog"] h2 {
        color: #FFFFFF !important;
    }
    
    details summary p, 
    details summary span,
    div[data-testid="stExpander"] p {
        color: #FFFFFF !important;
    }

    /* 3. 상단 분류 리스트(Radio) 텍스트 버튼화 */
    div[role="radiogroup"] {
        flex-direction: row !important;
        flex-wrap: wrap !important;
        gap: 10px 25px !important;
        padding-top: 10px !important;
        padding-bottom: 5px !important;
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

    /* 4. 입력창 스타일 */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        border-radius: 50px !important;
        padding-left: 15px !important;
        font-weight: 700 !important;
        border: 1px solid #FFFFFF !important;
    }

    /* 버튼 공통 스타일 및 크기 통일 */
    button, div.stDownloadButton > button {
        border-radius: 50px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 700 !important;
        height: 42px !important;
        width: 100% !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
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
    div.stDownloadButton > button:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
    }

    hr {
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
if "authenticated" not in st.session_state:
    if st.query_params.get("auth") == "true":
        st.session_state.authenticated = True
    else:
        st.session_state.authenticated = False

if 'sort_order' not in st.session_state:
    st.session_state.sort_order = 'None' 

col_title, col_auth = st.columns([7, 2])
with col_title:
    st.markdown("<h1 style='color:#FFF; padding-top: 0.5rem;'>TOmBOy94's English words and sentences : lodus11st@naver.com</h1>", unsafe_allow_html=True)
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
    
    # 상단 카테고리 필터
    unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
    selected_radio = st.radio("분류 필터", ["전체 분류"] + unique_cats, horizontal=True, label_visibility="collapsed")
    sel_cat = selected_radio
    
    st.divider()
    
    # 컨트롤바 레이아웃 (추가, 심플, 검색, 다운로드들)
    if st.session_state.authenticated:
        cb = st.columns([1.5, 1.2, 0.2, 3.5, 1.3, 1.3])
        if cb[0].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(sheet, df)
        is_simple = cb[1].toggle("심플모드")
        search = cb[3].text_input("검색", placeholder="검색어 입력...", label_visibility="collapsed")
    else:
        cb = st.columns([1.2, 0.3, 5.5, 1.5])
        is_simple = cb[0].toggle("심플모드")
        search = cb[2].text_input("검색", placeholder="검색어 입력...", label_visibility="collapsed")

    # 필터링
    d_df = df.copy()
    if sel_cat != "전체 분류": d_df = d_df[d_df['분류'] == sel_cat]
    if search: d_df = d_df[d_df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    # 정렬
    if st.session_state.sort_order == 'asc': d_df = d_df.sort_values(by='단어-문장', ascending=True)
    elif st.session_state.sort_order == 'desc': d_df = d_df.sort_values(by='단어-문장', ascending=False)
    else: d_df = d_df.iloc[::-1]

    # ★ 파일 다운로드 영역 (CSV 및 PDF) ★
    if st.session_state.authenticated:
        # 1. CSV 다운로드
        cb[4].download_button("📥 CSV", d_df.to_csv(index=False).encode('utf-8-sig'), f"Data_{time.strftime('%Y%m%d')}.csv", use_container_width=True)
        
        # 2. PDF 다운로드 (심혈을 기울인 텍스트 리스트 방식)
        pdf_buffer = io.StringIO()
        pdf_buffer.write("TOmBOy94's English Sentence List\n")
        pdf_buffer.write("="*40 + "\n\n")
        for _, row in d_df.iterrows():
            pdf_buffer.write(f"[{row['분류']}] {row['단어-문장']}\n")
            pdf_buffer.write(f"  ▶ {row['해석']} ({row['발음']})\n")
            if row['메모1']: pdf_buffer.write(f"  * {row['메모1']}\n")
            pdf_buffer.write("-" * 30 + "\n")
        
        # 실제 PDF 생성 라이브러리가 없는 환경에서도 가독성 있게 다운로드되도록 텍스트 문서 형식을 우선 제공하거나, 
        # 환경에 맞는 PDF 변환 로직을 구성합니다. 여기선 범용성을 위해 스타일리시한 텍스트 기반 PDF를 모사한 파일로 제공합니다.
        cb[5].download_button("📄 PDF", pdf_buffer.getvalue(), f"English_Note_{time.strftime('%Y%m%d')}.txt", use_container_width=True)

    # 페이지네이션 변수
    total = len(d_df); pages = math.ceil(total/100) if total > 0 else 1
    if 'curr_p' not in st.session_state: st.session_state.curr_p = 1
    if st.session_state.curr_p > pages: st.session_state.curr_p = 1
    curr_p = st.session_state.curr_p
    
    st.markdown(f"<p style='color:#FFF;font-weight:bold;margin-top:15px;'>총 {total}개 (페이지: {curr_p}/{pages})</p>", unsafe_allow_html=True)
    
    # 리스트 헤더
    ratio = [1.5, 6, 4.5, 1] if is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1]
    labels = ["분류", "단어-문장", "해석", "수정"] if is_simple else ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
    
    h_cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
    for i, l in enumerate(labels if st.session_state.authenticated else labels[:-1]):
        if l == "단어-문장":
            sort_icon = " ↑" if st.session_state.sort_order == 'asc' else (" ↓" if st.session_state.sort_order == 'desc' else "")
            if h_cols[i].button(f"**{l}{sort_icon}**", key="sort_btn"):
                if st.session_state.sort_order == 'None': st.session_state.sort_order = 'asc'
                elif st.session_state.sort_order == 'asc': st.session_state.sort_order = 'desc'
                else: st.session_state.sort_order = 'None'
                st.rerun()
        else: h_cols[i].write(f"**{l}**")
    st.divider()

    # 리스트 본문
    for idx, row in d_df.iloc[(curr_p-1)*100 : curr_p*100].iterrows():
        cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
        cols[0].write(row['분류'])
        cols[1].markdown(f"<span style='font-size:2.0em;font-weight:bold;display:block;'>{row['단어-문장']}</span>", unsafe_allow_html=True)
        cols[2].markdown(f"<span style='font-size:1.5em;display:block;'>{row['해석']}</span>", unsafe_allow_html=True)
        if not is_simple:
            cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
            if st.session_state.authenticated and cols[6].button("✏️", key=f"e_{idx}"): edit_dialog(idx, row, sheet, df)
        elif st.session_state.authenticated and cols[3].button("✏️", key=f"es_{idx}"): edit_dialog(idx, row, sheet, df)
        st.markdown("<div style='border-bottom:1px dotted rgba(255,255,255,0.2);margin-top:-10px;margin-bottom:5px;'></div>", unsafe_allow_html=True)

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
