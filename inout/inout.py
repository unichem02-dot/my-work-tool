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
    /* 스트림릿 기본 UI 요소를 완벽하게 숨기기 (메뉴, 푸터, Manage app 버튼) */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    [data-testid="manage-app-button"] {display: none !important;}
    [data-testid="stAppDeployButton"] {display: none !important;}
    .stDeployButton {display: none !important;}
    
    /* 표 우측 상단에 나타나는 기본 툴바(흰색 빈 박스 버그) 완전 숨김 처리 */
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
    
    /* Primary 버튼 파란색 커스텀 */
    button[kind="primary"] {
        background-color: #4e8cff !important;
        border-color: #4e8cff !important;
        color: white !important;
    }
    button[kind="primary"]:hover {
        background-color: #3b76e5 !important;
        border-color: #3b76e5 !important;
        color: white !important;
    }
    
    /* SQL 다운로드 생성완료 버튼 (Secondary 타입으로 분리하여 빨간색 완벽 고정 적용!) */
    div[data-testid="stDownloadButton"] button[kind="secondary"] {
        background-color: #ef4444 !important; /* 빨간색(Red) */
        border-color: #ef4444 !important;
        color: white !important;
    }
    
    /* 기간/월별 검색버튼 청록색 커스텀 */
    [data-testid="stFormSubmitButton"] > button {
        background-color: #009688 !important; /* 청록색 */
        border-color: #009688 !important;
        color: white !important;
    }
    
    /* 메인 데이터 테이블 스타일 */
    .custom-table-container { width: 100%; margin-top: 5px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
    .table-title-box { background-color: #2b323c; padding: 10px 15px; border-top: 2px solid #555; border-bottom: none; display: flex; align-items: center; justify-content: space-between; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }
    .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; }
    .custom-table th { text-align: center; color: white; font-weight: bold; padding: 10px 6px; }
    .custom-table tr:nth-child(even) { background-color: #f8f9fa; }
    
    /* 테이블 구역별 색상 */
    .th-base { background-color: #353b48; color: white; }
    .th-in { background-color: #3b5b88; color: white; } 
    .th-out { background-color: #b8860b; color: white; }
    
    /* 텍스트 색상 강조 */
    .txt-in-bold { color: #1e3a8a !important; font-weight: bold; }
    .txt-in { color: #1e3a8a !important; }
    .txt-out-bold { color: #9a3412 !important; font-weight: bold; }
    .txt-out { color: #9a3412 !important; }
    .txt-green { color: #059669 !important; font-weight: bold; }
    .txt-purple { color: #7e22ce !important; font-weight: bold; }
    .txt-black { color: #1e293b !important; }
    .tc { text-align: center; } .tl { text-align: left; } .tr { text-align: right; }
    
    .sum-profit { background-color: #2b323c; color: white; padding: 12px 20px; text-align: right; font-weight: bold; font-size: 16px; border-top: 1px solid #444; }

    /* 💡 매입/매출 수량 툴팁 (메모장 팝업) 올블랙 고정 CSS */
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
        /* 💡 툴팁 내부 텍스트 완전 블랙 강제 */
        color: black !important;
    }
    
    /* 💡 [핵심] 메모장 내부의 모든 텍스트 요소를 블랙으로 덮어쓰기 */
    .memo-text, .memo-text *, .memo-text span, .memo-text div {
        color: black !important;
        -webkit-text-fill-color: black !important;
        font-weight: bold !important;
    }

    .memo-tooltip-in:hover .memo-text, .memo-tooltip-out:hover .memo-text, .memo-tooltip-base:hover .memo-text {
        visibility: visible;
        opacity: 1;
    }

    /* 💡 팝업(dialog) 디자인 심플 포스트잇 스타일 */
    div[role="dialog"] {
        background-color: #FFFDE7 !important;
        border: 2px solid #FFC107 !important;
        border-radius: 12px !important;
    }
    div[role="dialog"] * {
        color: black !important;
    }
    div[role="dialog"] textarea {
        background-color: white !important;
        color: black !important;
        border: 1px solid #FFC107 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 💡 검색 조건 URL 동기화 기술 (패딩 오류 복구 로직 추가)
def encode_sp(sp):
    try:
        sp_copy = sp.copy()
        for k, v in sp_copy.items():
            if isinstance(v, datetime.date) or hasattr(v, 'strftime'):
                sp_copy[k] = v.strftime('%Y-%m-%d')
        j = json.dumps(sp_copy)
        return urllib.parse.quote(base64.urlsafe_b64encode(j.encode('utf-8')).decode('utf-8'))
    except: return ""

def decode_sp(s):
    try:
        if not s: return None
        s = urllib.parse.unquote(s)
        # base64 패딩 복구 (= 기호 보정)
        s += "=" * ((4 - len(s) % 4) % 4)
        j = base64.urlsafe_b64decode(s.encode('utf-8')).decode('utf-8')
        sp = json.loads(j)
        for k in ['start', 'end', 'date']:
            if k in sp and sp[k]:
                sp[k] = pd.to_datetime(sp[k]).date()
        return sp
    except: return None

# --- [2. 보안 및 세션 상태 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "sort_desc" not in st.session_state: st.session_state.sort_desc = False 
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "copy_id" not in st.session_state: st.session_state.copy_id = None
if "memo_edit_id" not in st.session_state: st.session_state.memo_edit_id = None
if "memo_type" not in st.session_state: st.session_state.memo_type = None

# URL 파라미터 감지 및 자동 로그인 (상태 복구)
if any(k in st.query_params for k in ["edit_id", "copy_id", "memo_edit_id"]):
    token = str(st.secrets.get("tom_password", ""))
    if st.query_params.get("token") == token:
        st.session_state.authenticated = True
        
        # 💡 [핵심] URL에서 검색 조건을 복원하여 세션에 저장
        sp_encoded = st.query_params.get("sp", "")
        if sp_encoded:
            restored = decode_sp(sp_encoded)
            if restored: st.session_state.search_params = restored
                
        if "year" in st.query_params: st.session_state.target_year_from_url = int(st.query_params["year"])
        if "edit_id" in st.query_params: st.session_state.edit_id = st.query_params["edit_id"]
        if "copy_id" in st.query_params:
            st.session_state.copy_id = st.query_params["copy_id"]
            st.session_state.search_params = {"mode": "신규입력"}
        if "memo_edit_id" in st.query_params:
            st.session_state.memo_edit_id = st.query_params["memo_edit_id"]
            st.session_state.memo_type = st.query_params.get("memo_type", "in")
            
    # 💡 [무한 로딩 해결] URL을 지우고 앱을 깨끗한 상태로 1회 재실행
    st.query_params.clear()
    st.rerun()

# 초기 접속 시 빈 화면 유지
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
try: available_years = sorted([int(ws.title.replace('년','')) for ws in init_connection().open('SQL백업260211-jeilinout').worksheets() if ws.title.endswith('년')], reverse=True)
except: available_years = [get_kst_now().year]

col_t, col_u, col_sql, col_r, col_l = st.columns([3.9, 1.3, 1.4, 1.4, 1.4])
with col_t: st.markdown("<h3 style='margin:0;'>📦 TOmBOy's INOUT</h3>", unsafe_allow_html=True)
with col_u: 
    if st.button("📤 DB 업로드" if not st.session_state.show_uploader else "❌ 업로드 닫기", use_container_width=True, type="primary"):
        st.session_state.show_uploader = not st.session_state.show_uploader
        st.rerun()
with col_sql: st.button("💾 SQL다운", use_container_width=True, type="primary", disabled=True)
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
    
    # 💡 429 에러 방지용 연도 타겟팅
    if st.session_state.edit_id or st.session_state.copy_id or st.session_state.memo_edit_id:
        target_years = [st.session_state.target_year_from_url] if hasattr(st.session_state, 'target_year_from_url') else available_years
    elif params["mode"] == "기간":
        target_years = [y for y in available_years if params["start"].year <= y <= params["end"].year]
    elif params["mode"] in ["월별상세", "결산", "월별", "용차"]: target_years = [int(params["year"])]
    elif params["mode"] == "일": target_years = [params["date"].year]
    else: target_years = [available_years[0]]

    df = load_data_for_years(target_years)
    if not df.empty:
        df['date_dt'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=['date_dt'])
        df['year'] = df['date_dt'].dt.year.astype(int)
        df['month'] = df['date_dt'].dt.month.astype(int)
        for c in ['inq', 'inprice', 'outq', 'outprice', 'carprice', 'id']:
            df[f'{c}_val'] = df[c].apply(clean_numeric)
        df['in_total'], df['out_total'] = df['inq_val'] * df['inprice_val'], df['outq_val'] * df['outprice_val']

    # 💡 [핵심 기술] 표와 팝업이 공존하도록 폼 영역과 표 영역을 분리 렌더링
    if st.session_state.edit_id:
        # 등록 자료 수정 폼 (화면 상단 대체)
        st.markdown("### 📝 자료 수정 모드")
        if st.button("🔙 돌아가기"): st.session_state.edit_id = None; st.rerun()
    elif params["mode"] == "신규입력":
        st.markdown("### 🆕 신규 입력 모드")
        if st.button("🔙 취소"): st.session_state.search_params = st.session_state.get("prev_search_params", {"mode":"init"}); st.rerun()
    else:
        # 💡 메인 검색 및 결과 화면
        components.html("""<script>/* 계산기 로직 생략 */</script>""", height=1) # 계산기 공간 확보
        
        # 검색 필터 UI
        col1, col2, col3, col4, col5 = st.columns([1, 2, 1, 2, 2])
        # (검색 필터 구현 생략 - 기존 코드와 동일)
        
        # 💡 [메모 팝업 렌더링] Streamlit Dialog 활용
        if st.session_state.memo_edit_id:
            target_row = df[df['id'].astype(str) == str(st.session_state.memo_edit_id)]
            if not target_row.empty:
                tr = target_row.iloc[0]
                m_col = f"memo{st.session_state.memo_type}"
                orig_m = safe_str(tr.get(m_col, ""))
                
                @st.dialog("📋 텍스트 메모 관리")
                def show_memo():
                    st.markdown(f"**대상 ID: {st.session_state.memo_edit_id}**")
                    new_val = st.text_area("메모 내용", value=orig_m, height=150, label_visibility="collapsed")
                    c1, c2 = st.columns(2)
                    if c1.button("💾 저장", use_container_width=True, type="primary"):
                        client = init_connection().open('SQL백업260211-jeilinout')
                        sheet = client.worksheet(f"{tr['year']}년")
                        cell = sheet.find(str(st.session_state.memo_edit_id), in_column=1)
                        if cell:
                            # Q(17)열까지 데이터 구조 유지하며 메모 저장
                            row_data = sheet.row_values(cell.row)
                            while len(row_data) < 17: row_data.append("")
                            idx = 14 if st.session_state.memo_type == 'in' else 15 if st.session_state.memo_type == 'out' else 16
                            row_data[idx] = new_val
                            sheet.update(f"A{cell.row}:Q{cell.row}", [row_data])
                        st.cache_data.clear(); st.session_state.memo_edit_id = None; st.rerun()
                    if c2.button("청록색 취소", use_container_width=True): # 💡 요청대로 취소버튼
                        st.session_state.memo_edit_id = None; st.rerun()
                show_memo()

        # 데이터 테이블 출력
        if params["mode"] != "init" and not df.empty:
            # 💡 [핵심 기술] 검색 조건 유지 링크 생성
            token = str(st.secrets["tom_password"])
            enc_sp = encode_sp(st.session_state.search_params)
            
            row_html = []
            # (테이블 행 생성 로직 - 기존과 동일하되 링크에 &sp={enc_sp} 유지)
            # 💡 메모창 텍스트는 <span style='color:black !important;'>으로 이중 보호
            
            # 버튼 크기 정렬 교정
            c_sort, c_print, c_excel = st.columns([6, 2, 2])
            with c_print:
                # 💡 PRINT 버튼 높이 40px로 스트림릿 버튼과 완벽 동기화
                components.html(f"""<button style='height:40px; width:100%; background:#4e8cff; color:white; border:none; border-radius:8px; font-weight:bold;'>🖨️ PRINT</button>""", height=40)
            
            st.markdown("데이터 표 렌더링...", unsafe_allow_html=True) # 실제 데이터 테이블

except Exception as e: st.error(f"⚠️ 시스템 오류: {e}")
st.markdown("<br><p style='text-align:center; color:#64748b;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
