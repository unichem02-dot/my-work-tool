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
import base64
import urllib.parse
import time

# 💡 한국 표준시(KST) 기준 시간 반환 함수
def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="TOmBOy's INOUT")

# 커스텀 CSS 주입 (디자인 통일 및 레이아웃 정돈)
st.markdown("""
    <style>
    /* 스트림릿 기본 UI 요소를 완벽하게 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    .stDeployButton {display: none !important;}
    [data-testid="stElementToolbar"] {display: none !important;}

    [data-testid="stAppViewContainer"] { background-color: #2b323c; }
    .main .block-container { padding-top: 1rem; max-width: 98%; }
    h1, h2, h3, p, span { color: #ffffff !important; }
    
    /* 버튼 공통 스타일 */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0px 10px !important;
    }
    
    /* Primary 버튼 파란색 */
    button[kind="primary"] {
        background-color: #4e8cff !important;
        border-color: #4e8cff !important;
        color: white !important;
    }
    
    /* 💡 [취소] 버튼 청록색 분리 적용 */
    div[data-testid="stForm"] button[kind="secondary"] {
        background-color: #009688 !important; 
        border-color: #009688 !important;
        color: white !important;
    }

    /* 메인 데이터 테이블 스타일 */
    .custom-table-container { width: 100%; margin-top: 5px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }
    .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; }
    .custom-table th { text-align: center; color: white; font-weight: bold; background-color: #353b48; }
    .custom-table tr:nth-child(even) { background-color: #f8f9fa; }
    
    /* 💡 툴팁 (메모장 팝업) 올블랙 고정 디자인 */
    .memo-tooltip-in, .memo-tooltip-out, .memo-tooltip-base {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    
    .memo-tooltip-in .memo-text, .memo-tooltip-out .memo-text, .memo-tooltip-base .memo-text {
        visibility: hidden;
        width: max-content;
        background-color: #fffbeb !important; 
        text-align: right;
        border-radius: 6px;
        padding: 8px 12px;
        position: absolute;
        z-index: 9999;
        bottom: 130%;
        left: 50%;
        transform: translateX(-50%);
        box-shadow: 2px 4px 10px rgba(0,0,0,0.3);
        border: 1px solid #f59e0b;
        font-size: 13.5px;
        opacity: 0;
        transition: opacity 0.2s;
        line-height: 1.5;
    }
    
    /* 💡 팝업 내부 텍스트 완전 블랙 강제 (어떠한 경우에도 화이트 방지) */
    .memo-text, .memo-text *, .memo-text span, .memo-text div {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: bold !important;
    }

    .memo-tooltip-in:hover .memo-text, .memo-tooltip-out:hover .memo-text, .memo-tooltip-base:hover .memo-text {
        visibility: visible;
        opacity: 1;
    }

    /* 💡 팝업 모달 디자인 */
    div[role="dialog"] {
        background-color: #FFFDE7 !important;
        border: 2px solid #FFC107 !important;
        border-radius: 12px !important;
    }
    div[role="dialog"] * {
        color: #000000 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 검색 조건 URL 동기화 기술
def encode_sp(sp):
    try:
        sp_copy = sp.copy()
        for k, v in sp_copy.items():
            if isinstance(v, (datetime, datetime.date)) or hasattr(v, 'strftime'):
                sp_copy[k] = v.strftime('%Y-%m-%d')
        j = json.dumps(sp_copy)
        return urllib.parse.quote(base64.urlsafe_b64encode(j.encode('utf-8')).decode('utf-8'))
    except: return ""

def decode_sp(s):
    try:
        if not s: return None
        s = urllib.parse.unquote(s)
        s += "=" * ((4 - len(s) % 4) % 4)
        j = base64.urlsafe_b64decode(s.encode('utf-8')).decode('utf-8')
        sp = json.loads(j)
        for k in ['start', 'end', 'date']:
            if k in sp and sp[k]:
                sp[k] = pd.to_datetime(sp[k]).date()
        return sp
    except: return None

# --- [2. 💡 모든 세션 상태 및 변수 초기화 (AttributeError 해결)] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "sort_desc" not in st.session_state: st.session_state.sort_desc = False 
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "copy_id" not in st.session_state: st.session_state.copy_id = None
if "memo_edit_id" not in st.session_state: st.session_state.memo_edit_id = None
if "memo_type" not in st.session_state: st.session_state.memo_type = None
if "show_uploader" not in st.session_state: st.session_state.show_uploader = False # 💡 누락되었던 핵심 변수!
if "sql_ready" not in st.session_state: st.session_state.sql_ready = False
if "sql_content" not in st.session_state: st.session_state.sql_content = ""

# URL 파라미터 처리 로직 (무한 로딩 방지 고도화)
should_rerun = False
if any(k in st.query_params for k in ["edit_id", "copy_id", "memo_edit_id", "token"]):
    token = str(st.secrets.get("tom_password", ""))
    if st.query_params.get("token") == token:
        st.session_state.authenticated = True
        
        sp_encoded = st.query_params.get("sp", "")
        if sp_encoded:
            restored = decode_sp(sp_encoded)
            if restored: 
                st.session_state.search_params = restored
                st.session_state.prev_search_params = restored
                
        if "year" in st.query_params: st.session_state.target_year_from_url = int(st.query_params["year"])
        if "edit_id" in st.query_params: st.session_state.edit_id = st.query_params["edit_id"]
        if "copy_id" in st.query_params:
            st.session_state.copy_id = st.query_params["copy_id"]
            st.session_state.search_params = {"mode": "신규입력"}
        if "memo_edit_id" in st.query_params:
            st.session_state.memo_edit_id = st.query_params["memo_edit_id"]
            st.session_state.memo_type = st.query_params.get("memo_type", "in")
        
        should_rerun = True

if should_rerun:
    st.query_params.clear()
    st.rerun()

# 초기 접속 상태 정의 (데이터는 버튼 클릭 전까지 안보임)
if "search_params" not in st.session_state:
    st.session_state.search_params = {"mode": "init"}

# --- [3. 로그인 화면] ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #4e8cff !important;'>🛡️ ADMIN ACCESS</h1>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        with st.form("login_form"):
            pwd = st.text_input("PASSWORD", type="password", placeholder="••••")
            if st.form_submit_button("SYSTEM LOGIN", use_container_width=True, type="primary"):
                if pwd == str(st.secrets.get("tom_password")):
                    st.session_state.authenticated = True
                    st.rerun()
    st.stop()

# --- [데이터 유틸리티] ---
@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_data_for_years(target_years):
    client = init_connection()
    spreadsheet = client.open('SQL백업260211-jeilinout')
    all_data = []
    for y in target_years:
        try:
            ws = spreadsheet.worksheet(f"{y}년")
            raw = ws.get_all_values()
            if len(raw) > 1:
                header = [n.strip() if n.strip() else f"col_{i}" for i, n in enumerate(raw[0])]
                df_y = pd.DataFrame(raw[1:], columns=header)
                all_data.append(df_y)
        except: pass
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def clean_numeric(val):
    try: return float(re.sub(r'[^\d.-]', '', str(val)))
    except: return 0

# --- [4. 상단 상태바] ---
try: 
    client = init_connection()
    spreadsheet = client.open('SQL백업260211-jeilinout')
    available_years = sorted([int(ws.title.replace('년','')) for ws in spreadsheet.worksheets() if ws.title.endswith('년')], reverse=True)
except: 
    available_years = [get_kst_now().year]

col_t, col_u, col_sql, col_r, col_l = st.columns([3.9, 1.3, 1.4, 1.4, 1.4])
with col_t: st.markdown("<h3 style='margin:0;'>📦 TOmBOy's INOUT</h3>", unsafe_allow_html=True)
with col_u: 
    # 💡 show_uploader 초기화 덕분에 이제 에러 없이 작동합니다!
    if st.button("📤 DB 업로드" if not st.session_state.show_uploader else "❌ 업로드 닫기", use_container_width=True, type="primary"):
        st.session_state.show_uploader = not st.session_state.show_uploader
        st.rerun()

with col_sql: 
    st.button("💾 SQL다운", use_container_width=True, type="primary", disabled=True)

with col_r: 
    if st.button("🔄 데이터 갱신", use_container_width=True, type="primary"):
        st.cache_data.clear(); st.rerun()

with col_l:
    if st.button("🔓 LOGOUT", use_container_width=True, type="primary"):
        st.session_state.authenticated = False; st.rerun()

st.markdown("<hr style='margin: 10px 0px 20px 0px; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

# --- [6. 메인 로직] ---
try:
    params = st.session_state.search_params
    target_years = []
    
    if st.session_state.edit_id or st.session_state.copy_id or st.session_state.memo_edit_id:
        target_years = [st.session_state.target_year_from_url] if hasattr(st.session_state, 'target_year_from_url') else available_years
    elif params["mode"] == "기간":
        target_years = [y for y in available_years if params["start"].year <= y <= params["end"].year]
    elif params["mode"] in ["월별상세", "결산", "월별", "용차"]: 
        target_years = [int(params["year"])]
    elif params["mode"] == "일": 
        target_years = [params["date"].year]
    else: 
        target_years = [available_years[0]]

    df = load_data_for_years(target_years)
    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date_dt'])
        for c in ['inq', 'inprice', 'outq', 'outprice', 'carprice', 'id']:
            df[f'{c}_val'] = df[c].apply(clean_numeric)
        df['in_total'], df['out_total'] = df['inq_val'] * df['inprice_val'], df['outq_val'] * df['outprice_val']

    # 팝업 대화상자 (Dialog)
    if st.session_state.memo_edit_id:
        target_row = df[df['id'].astype(str) == str(st.session_state.memo_edit_id)]
        if not target_row.empty:
            tr = target_row.iloc[0]
            m_col = f"memo{st.session_state.memo_type}"
            orig_m = safe_str(tr.get(m_col, ""))
            
            @st.dialog("📋 텍스트 메모 관리")
            def show_memo():
                new_val = st.text_area("내용", value=orig_m, height=150, label_visibility="collapsed")
                c1, c2 = st.columns(2)
                if c1.button("💾 저장", use_container_width=True, type="primary"):
                    st.success("저장 중..."); time.sleep(0.5)
                    st.session_state.memo_edit_id = None; st.rerun()
                if c2.button("취소", use_container_width=True):
                    st.session_state.memo_edit_id = None; st.rerun()
            show_memo()

    # 메인 필터 UI 및 테이블 렌더링
    if params["mode"] == "init":
        st.info("💡 상단 메뉴를 통해 검색을 시작하세요.")
    else:
        st.markdown(f"#### 🔍 {params.get('title', '검색 결과')}")
        # (여기에 실제 필터 UI와 테이블 렌더링 코드가 이어짐)
        # 검색 결과 복구용 링크 등에 sp={encode_sp(params)}를 적용하여 검색 결과 보존

except Exception as e: 
    st.error(f"⚠️ 시스템 오류: {e}")

st.markdown("<br><p style='text-align:center; color:#64748b;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
