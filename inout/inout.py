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

# 💡 구글 API 429(할당량 초과) 에러 자동 방어용 Retry 래퍼 함수
def api_retry(action):
    for attempt in range(4):
        try:
            return action()
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                time.sleep(2) # 429 발생 시 2초 대기 후 재시도
            else:
                raise e

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
    
    /* 매입/매출 품목, 배송 글자색 복구용 특정 클래스 */
    span.disp-in { color: #1e3a8a !important; }
    span.disp-out { color: #9a3412 !important; }
    span.disp-car { color: #475569 !important; }

    /* 검색 패널 컨테이너 */
    .search-panel-container {
        background-color: #353b48;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #4a5568;
        margin-bottom: 20px;
    }
    
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
    button[kind="primary"]:hover {
        background-color: #3b76e5 !important;
        border-color: #3b76e5 !important;
        color: white !important;
    }
    
    /* 💡 날짜정렬 버튼 (Secondary 일반 버튼) 올리브색 적용 */
    button[kind="secondary"] {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
    }
    button[kind="secondary"]:hover {
        background-color: #646a39 !important;
        border-color: #646a39 !important;
        color: white !important;
    }
    
    /* 💡 EXCEL 버튼 (Primary Download 버튼) 올리브색 적용 */
    div[data-testid="stDownloadButton"] button[kind="primary"] {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
    }
    div[data-testid="stDownloadButton"] button[kind="primary"]:hover {
        background-color: #646a39 !important;
        border-color: #646a39 !important;
        color: white !important;
    }

    /* SQL 다운로드 생성완료 버튼 (Secondary 타입) 빨간색 적용 */
    div[data-testid="stDownloadButton"] button[kind="secondary"] {
        background-color: #ef4444 !important; /* 빨간색(Red) */
        border-color: #ef4444 !important;
        color: white !important;
    }
    div[data-testid="stDownloadButton"] button[kind="secondary"]:hover {
        background-color: #dc2626 !important;
        border-color: #dc2626 !important;
        color: white !important;
    }
    
    /* 기간/월별 검색버튼 청록색 커스텀 */
    [data-testid="stFormSubmitButton"] > button {
        background-color: #009688 !important; /* 청록색 */
        border-color: #009688 !important;
        color: white !important;
    }
    [data-testid="stFormSubmitButton"] > button:hover {
        background-color: #00796B !important; /* 마우스 오버시 진한 청록색 */
        border-color: #00796B !important;
        color: white !important;
    }
    
    /* [취소] 버튼 청록색 분리 적용 (더 높은 우선순위로 날짜정렬 버튼과 분리) */
    div[data-testid="stForm"] button[kind="secondary"] {
        background-color: #009688 !important; /* 청록색 */
        border-color: #009688 !important;
        color: white !important;
    }
    div[data-testid="stForm"] button[kind="secondary"]:hover {
        background-color: #00796B !important; /* 진한 청록색 */
        border-color: #00796B !important;
        color: white !important;
    }
    
    /* 결산버튼 초록색 커스텀을 위한 예외처리 */
    div:nth-child(4) > div[data-testid="stButton"] > button {
        background-color: #8ba966 !important;
        border-color: #8ba966 !important;
    }

    /* 메인 데이터 테이블 스타일 */
    .custom-table-container { width: 100%; margin-top: 5px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
    .table-title-box { background-color: #2b323c; padding: 10px 15px; border-top: 2px solid #555; border-bottom: none; display: flex; align-items: center; justify-content: space-between; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }
    .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; }
    .custom-table th { text-align: center; color: white; font-weight: bold; padding: 10px 6px; }
    .custom-table tr:nth-child(even) { background-color: #f8f9fa; }
    .custom-table tr:hover { background-color: #e2e6ea; }
    
    /* 인쇄용 가짜 상하단 여백 */
    .print-fake-margin { display: none !important; }
    
    /* 인쇄 전용 타이틀 숨김 처리 */
    .print-only-title { display: none !important; }
    
    /* 테이블 구역별 색상 복구 완벽 완료 */
    .th-base { background-color: #353b48 !important; color: white !important; }
    .th-in { background-color: #3b5b88 !important; color: white !important; } 
    .th-out { background-color: #b8860b !important; color: white !important; }
    .th-etc { background-color: #757c43 !important; color: white !important; } /* 배송, 운송비 전용 올리브색 */
    
    /* 텍스트 색상 강조 */
    .txt-in-bold { color: #1e3a8a !important; font-weight: bold; }
    .txt-in { color: #1e3a8a !important; }
    .txt-out-bold { color: #9a3412 !important; font-weight: bold; }
    .txt-out { color: #9a3412 !important; }
    .txt-green { color: #059669 !important; font-weight: bold; }
    .txt-purple { color: #7e22ce !important; font-weight: bold; }
    .txt-gray { color: #475569 !important; }
    .txt-black { color: #1e293b !important; }
    .tc { text-align: center; } .tl { text-align: left; } .tr { text-align: right; }
    
    .sum-profit { background-color: #2b323c; color: white; padding: 12px 20px; text-align: right; font-weight: bold; font-size: 16px; border-top: 1px solid #444; }

    /* 신규입력/수정창 헤더 스타일 */
    .nh-box { padding: 10px 8px; text-align: center; color: white; font-weight: bold; border: 1px solid #555; margin-bottom: 5px; font-size: 14px;}
    .nh-base { background-color: #353b48; }
    .nh-in { background-color: #3b5b88; }
    .nh-out { background-color: #b8860b; }
    .nh-etc { background-color: #757c43; }

    /* 결산 뷰 전용 대시보드 폰트 오버라이드 */
    [data-testid="stMetricValue"] { color: #ffffff !important; }
    [data-testid="stMetricLabel"] { color: #cbd5e1 !important; font-size: 16px !important; }
    
    /* 검색 메뉴 굵게(Bold) 변경 */
    div[data-baseweb="select"] > div { font-weight: bold !important; }
    div[data-baseweb="input"] > input { font-weight: bold !important; }
    div[data-testid="stDateInput"] input { font-weight: bold !important; }
    
    /* Form 테두리 제거 */
    div[data-testid="stForm"] { border: none !important; padding: 0 !important; margin-bottom: -15px !important; }
    
    /* 매입/매출 수량 및 품목/배송 툴팁 완전 불투명(Solid) 적용 CSS */
    .memo-tooltip-in, .memo-tooltip-out, .memo-tooltip-base {
        position: relative;
        display: inline-block;
        cursor: pointer;
    }
    .memo-tooltip-in { color: #1e3a8a; } 
    .memo-tooltip-out { color: #9a3412; }
    .memo-tooltip-base { color: inherit; } 
    
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
        border: 1px solid rgba(245, 158, 11, 0.8);
        font-size: 13.5px;
        opacity: 0;
        transition: opacity 0.2s;
        line-height: 1.5;
        color: #000000 !important; 
    }
    /* 메모장 내부 텍스트 완벽 블랙 강제 */
    .memo-tooltip-in .memo-text, .memo-tooltip-in .memo-text *, 
    .memo-tooltip-out .memo-text, .memo-tooltip-out .memo-text *, 
    .memo-tooltip-base .memo-text, .memo-tooltip-base .memo-text * {
        color: #000000 !important;
        font-weight: bold !important;
        text-shadow: none !important;
        -webkit-text-fill-color: #000000 !important; 
    }
    /* 말풍선 아래쪽 화살표 */
    .memo-tooltip-in .memo-text::after, .memo-tooltip-out .memo-text::after, .memo-tooltip-base .memo-text::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -6px;
        border-width: 6px;
        border-style: solid;
        border-color: #f59e0b transparent transparent transparent; 
    }
    .memo-tooltip-in:hover .memo-text, .memo-tooltip-in:active .memo-text,
    .memo-tooltip-out:hover .memo-text, .memo-tooltip-out:active .memo-text,
    .memo-tooltip-base:hover .memo-text, .memo-tooltip-base:active .memo-text {
        visibility: visible;
        opacity: 1;
    }

    /* 입력창 텍스트 색상 고정 */
    div[data-testid="stTextArea"] textarea, div[data-testid="stTextInput"] input {
        color: #1e293b !important;
        font-weight: bold !important;
    }

    /* 파일 업로드 창 가시성 해결 */
    div[data-testid="stFileUploader"] {
        background-color: #f1f5f9 !important; 
        border-radius: 8px !important;
        padding: 10px !important;
    }
    div[data-testid="stFileUploader"] * {
        color: #1e293b !important; 
        font-weight: bold !important;
    }
    div[data-testid="stFileUploadDropzone"] {
        background-color: transparent !important;
        border: 2px dashed #94a3b8 !important;
    }
    div[data-testid="stFileUploader"] svg {
        fill: #1e293b !important;
        color: #1e293b !important;
    }
    div[data-testid="stFileUploader"] button {
        background-color: #ffffff !important;
        border: 1px solid #1e293b !important;
        color: #1e293b !important; 
    }
    div[data-testid="stFileUploader"] button:hover {
        background-color: #e2e8f0 !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 검색 조건 URL 동기화 기술
def encode_sp(sp):
    try:
        sp_copy = sp.copy()
        for k, v in sp_copy.items():
            if hasattr(v, 'strftime'):
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

# --- [2. 모든 세션 상태 및 변수 초기화] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "sort_desc" not in st.session_state: st.session_state.sort_desc = False 
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "copy_id" not in st.session_state: st.session_state.copy_id = None
if "show_new" not in st.session_state: st.session_state.show_new = False 
if "show_uploader" not in st.session_state: st.session_state.show_uploader = False 
if "sql_ready" not in st.session_state: st.session_state.sql_ready = False
if "sql_content" not in st.session_state: st.session_state.sql_content = ""

# URL 파라미터 처리 로직 (무한 로딩 방지 및 검색 조건 완벽 복원)
should_rerun = False

# 홈 로고 클릭 감지
if "home" in st.query_params:
    st.session_state.search_params = {"mode": "init"}
    st.session_state.edit_id = None
    st.session_state.copy_id = None
    st.session_state.show_new = False
    should_rerun = True

if any(k in st.query_params for k in ["edit_id", "copy_id", "token"]):
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
            st.session_state.show_new = True 
        
        should_rerun = True

if should_rerun:
    st.query_params.clear()
    st.rerun()

# 초기 접속 상태 정의
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
            raw = api_retry(lambda: ws.get_all_values())
            if len(raw) > 1:
                header = [n.strip() if n.strip() else f"col_{i}" for i, n in enumerate(raw[0])]
                df_y = pd.DataFrame(raw[1:], columns=header)
                all_data.append(df_y)
        except: pass
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()

def clean_numeric(val):
    try: return float(re.sub(r'[^\d.-]', '', str(val)))
    except: return 0

def safe_str(val):
    if pd.isna(val) or str(val).lower() == 'nan': return ""
    if isinstance(val, float) and val.is_integer(): return str(int(val))
    return str(val)

# 💡 [핵심 기술 1] SQL 생성을 위한 유틸리티 함수 복구
def generate_sql_for_backup(df_data):
    lines = ["CREATE TABLE IF NOT EXISTS `jeilinout` (",
             "  `id` bigint(20) NOT NULL,",
             "  `date` varchar(50) DEFAULT NULL,",
             "  `incom` varchar(255) DEFAULT NULL,",
             "  `initem` varchar(255) DEFAULT NULL,",
             "  `inq` varchar(50) DEFAULT '0',",
             "  `inprice` varchar(50) DEFAULT '0',",
             "  `outcom` varchar(255) DEFAULT NULL,",
             "  `outitem` varchar(255) DEFAULT NULL,",
             "  `outq` varchar(50) DEFAULT '0',",
             "  `outprice` varchar(50) DEFAULT '0',",
             "  `memo` text,",
             "  `s` varchar(50) DEFAULT NULL,",
             "  `carno` varchar(100) DEFAULT NULL,",
             "  `carprice` varchar(50) DEFAULT '0',",
             "  `memoin` text,",
             "  `memoout` text,",
             "  `memocar` text,",
             "  PRIMARY KEY (`id`)",
             ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;", ""]
    if not df_data.empty:
        for _, r in df_data.iterrows():
            val_str = []
            for c in ['id', 'date', 'incom', 'initem', 'inq', 'inprice', 'outcom', 'outitem', 'outq', 'outprice', 'memo', 's', 'carno', 'carprice', 'memoin', 'memoout', 'memocar']:
                v = str(r.get(c, ''))
                if pd.isna(r.get(c)) or v.lower() == 'nan': v = ""
                v = v.replace("'", "''") 
                val_str.append(f"'{v}'")
            vals = ", ".join(val_str)
            lines.append(f"INSERT IGNORE INTO `jeilinout` (`id`, `date`, `incom`, `initem`, `inq`, `inprice`, `outcom`, `outitem`, `outq`, `outprice`, `memo`, `s`, `carno`, `carprice`, `memoin`, `memoout`, `memocar`) VALUES ({vals});")
    return "\n".join(lines)

# --- [4. 상단 상태바] ---
try: 
    client = init_connection()
    spreadsheet = client.open('SQL백업260211-jeilinout')
    available_years = sorted([int(ws.title.replace('년','')) for ws in spreadsheet.worksheets() if ws.title.endswith('년')], reverse=True)
except: 
    available_years = [get_kst_now().year]

col_t, col_u, col_sql, col_r, col_l = st.columns([3.9, 1.3, 1.4, 1.4, 1.4])
with col_t: 
    pwd_token = str(st.secrets.get("tom_password", ""))
    st.markdown(f"<h3 style='margin:0;'><a href='?home=1&token={pwd_token}' target='_self' style='text-decoration: none; color: #ffffff;'>📦 TOmBOy's INOUT</a></h3>", unsafe_allow_html=True)
    
with col_u: 
    if st.button("📤 DB 업로드" if not st.session_state.show_uploader else "❌ 업로드 닫기", use_container_width=True, type="primary"):
        st.session_state.show_uploader = not st.session_state.show_uploader
        st.rerun()

with col_sql: 
    # 💡 [핵심 기술 2] SQL 다운로드 버튼 로직 완벽 복구
    if not st.session_state.sql_ready:
        if st.button("💾 SQL다운", use_container_width=True, type="primary"):
            with st.spinner("⏳ SQL 데이터를 생성 중입니다..."):
                try:
                    all_data_for_sql = load_data_for_years(available_years)
                    st.session_state.sql_content = generate_sql_for_backup(all_data_for_sql)
                    st.session_state.sql_ready = True
                    st.rerun()
                except Exception as e:
                    st.error("생성 실패")
    else:
        st.download_button("💾 생성완료! 다운로드", data=st.session_state.sql_content.encode('utf-8-sig'), file_name=f"db_backup_{get_kst_now().strftime('%Y%m%d')}.sql", mime="application/sql", use_container_width=True, type="secondary")

with col_r: 
    if st.button("🔄 데이터 갱신", use_container_width=True, type="primary"):
        st.cache_data.clear(); st.rerun()

with col_l:
    if st.button("🔓 LOGOUT", use_container_width=True, type="primary"):
        st.session_state.authenticated = False; st.rerun()

st.markdown("<hr style='margin: 10px 0px 20px 0px; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

# 💡 [핵심 기술 3] DB 파일 업로드 UI 완벽 복구
if st.session_state.show_uploader:
    st.markdown("<div class='search-panel-container'>", unsafe_allow_html=True)
    st.markdown("<h4 style='color: #4e8cff; margin-bottom: 10px;'>📂 과거 통합 데이터 연도별 분할 업로드</h4>", unsafe_allow_html=True)
    st.info("💡 과거의 모든 데이터가 들어있는 엑셀(또는 CSV) 파일을 올리시면, 연도별로 탭(시트)을 자동으로 쪼개서 구글 시트에 저장합니다.")
    
    uploaded_file = st.file_uploader("여기에 엑셀/CSV 파일을 끌어다 놓거나 클릭하여 업로드하세요.", type=["xlsx", "xls", "csv"])
    
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    upload_df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    upload_df = pd.read_csv(uploaded_file, encoding='cp949')
            else:
                try:
                    upload_df = pd.read_excel(uploaded_file, engine='openpyxl')
                except Exception:
                    try:
                        uploaded_file.seek(0)
                        upload_df = pd.read_excel(uploaded_file, engine='xlrd')
                    except Exception:
                        uploaded_file.seek(0)
                        raw_bytes = uploaded_file.getvalue()
                        try:
                            html_content = raw_bytes.decode('utf-8')
                        except UnicodeDecodeError:
                            html_content = raw_bytes.decode('cp949', errors='ignore')
                        
                        trs = re.findall(r'<tr[^>]*>(.*?)</tr>', html_content, re.IGNORECASE | re.DOTALL)
                        if not trs:
                            raise ValueError("표 데이터를 찾을 수 없습니다. 진짜 엑셀(.xlsx)로 '다른 이름으로 저장' 후 시도해주세요.")
                        
                        data = []
                        for tr in trs:
                            tds = re.findall(r'<t[dh][^>]*>(.*?)</t[dh]>', tr, re.IGNORECASE | re.DOTALL)
                            tds = [re.sub(r'<[^>]+>', '', td).replace('&nbsp;', ' ').strip() for td in tds]
                            if any(tds):
                                data.append(tds)
                                
                        if len(data) > 1:
                            upload_df = pd.DataFrame(data[1:], columns=data[0])
                        else:
                            upload_df = pd.DataFrame(data)
                
            st.success(f"✅ 파일 읽기 성공! 총 {len(upload_df):,}개의 데이터를 가져왔습니다.")
            st.dataframe(upload_df.head(5), use_container_width=True)
            
            if st.button("🚀 구글 시트에 연도별로 분할 저장하기", type="primary"):
                target_date_col = 'date' if 'date' in upload_df.columns else None
                if not target_date_col:
                    for col in upload_df.columns:
                        if 'date' in str(col).lower() or '날짜' in str(col):
                            target_date_col = col
                            break

                if not target_date_col:
                    st.error("⚠️ 업로드한 파일에 'date' 또는 '날짜' 열을 찾을 수 없어 연도별 분석이 불가능합니다.")
                else:
                    with st.spinner("⏳ 데이터를 연도별로 분석하여 구글 시트에 분할 업로드 중입니다... (데이터량에 따라 1~2분 소요될 수 있습니다)"):
                        try:
                            client = init_connection()
                            spreadsheet = client.open('SQL백업260211-jeilinout')
                            
                            temp_df = upload_df.copy()
                            temp_df[target_date_col] = pd.to_datetime(temp_df[target_date_col], errors='coerce')
                            valid_df = temp_df.dropna(subset=[target_date_col]).copy()
                            valid_df['분할연도'] = valid_df[target_date_col].dt.year.astype(int)
                            
                            years_found = valid_df['분할연도'].unique()
                            
                            for y in sorted(years_found, reverse=True):
                                year_str = f"{y}년"
                                year_df = valid_df[valid_df['분할연도'] == y].drop(columns=['분할연도'])
                                
                                year_df[target_date_col] = year_df[target_date_col].dt.strftime('%Y-%m-%d')
                                year_df = year_df.fillna("")
                                
                                try:
                                    worksheet = spreadsheet.worksheet(year_str)
                                    api_retry(lambda: worksheet.clear())
                                except gspread.exceptions.WorksheetNotFound:
                                    worksheet = spreadsheet.add_worksheet(title=year_str, rows=str(len(year_df)+100), cols=str(len(year_df.columns)))
                                
                                data_to_upload = [year_df.columns.tolist()] + year_df.values.tolist()
                                api_retry(lambda: worksheet.update("A1", data_to_upload))
                            
                            st.success(f"🎉 성공! 총 {len(years_found)}개의 연도별 탭({', '.join(f'{y}년' for y in sorted(years_found, reverse=True))})으로 깔끔하게 분할 저장이 완료되었습니다!")
                            st.balloons()
                            st.cache_data.clear() 
                            st.session_state.sql_ready = False 
                            
                        except Exception as e:
                            st.error(f"⚠️ 구글 시트 전송 중 오류가 발생했습니다: {e}")
                            
        except Exception as e:
            st.error(f"⚠️ 파일을 읽는 중 오류가 발생했습니다: {e}")
            
    st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("<hr style='margin: 10px 0px 20px 0px; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)


# --- [6. 메인 로직] ---
try:
    years = available_years
    months = list(range(1, 13))
    params = st.session_state.search_params
    
    # 데이터 로딩 범위 최적화
    target_years = set()
    if params["mode"] == "기간":
        target_years.update([y for y in available_years if params["start"].year <= y <= params["end"].year])
    elif params["mode"] in ["월별상세", "결산", "월별", "용차"]: 
        target_years.add(int(params["year"]))
    elif params["mode"] == "일": 
        target_years.add(params["date"].year)
    elif params["mode"] == "최근":
        if available_years:
            target_years.add(available_years[0])
        else:
            target_years.add(get_kst_now().year)

    if st.session_state.edit_id or st.session_state.copy_id:
        if hasattr(st.session_state, 'target_year_from_url'):
            target_years.add(st.session_state.target_year_from_url)
        else:
            target_years.update(available_years)
            
    if not target_years:
        if available_years:
            target_years.add(available_years[0])
        else:
            target_years.add(get_kst_now().year)

    df = load_data_for_years(sorted(list(target_years), reverse=True))
    
    date_col = 'date_dt'
    if not df.empty:
        df[date_col] = pd.to_datetime(df['date'], errors='coerce')
        df = df.dropna(subset=[date_col])
        df['year'] = df[date_col].dt.year.astype(int)
        df['month'] = df[date_col].dt.month.astype(int)
        for c in ['inq', 'inprice', 'outq', 'outprice', 'carprice', 'id']:
            df[f'{c}_val'] = df[c].apply(clean_numeric)
        df['in_total'], df['out_total'] = df['inq_val'] * df['inprice_val'], df['outq_val'] * df['outprice_val']
    else:
        df = pd.DataFrame(columns=['id', 'date', 'year', 'month', 'incom', 'initem', 'inq_val', 'inprice_val', 'outcom', 'outitem', 'outq_val', 'outprice_val', 'carno', 'carprice_val', 'in_total', 'out_total', 's', 'memoin', 'memoout', 'memocar', date_col])

    # ---------------------------------------------------------
    # [1] 등록 자료 수정 / 삭제 폼
    # ---------------------------------------------------------
    if st.session_state.edit_id:
        st.markdown("<h3 style='text-align:center; color:#ffeb3b; font-weight:bold;'>📝 등록 자료 및 메모 수정 / 삭제</h3>", unsafe_allow_html=True)
        target = df[df['id'].astype(str) == str(st.session_state.edit_id)]
        if not target.empty:
            t = target.iloc[0]
            def_date = pd.to_datetime(t['date']).date() if pd.notnull(t['date']) else get_kst_now().date()
            orig_year = def_date.year
            s_idx_edit = 1 if '중부' in safe_str(t.get('s')) else 0
            
            with st.form("edit_form"):
                c1, c2, c3, c4, c5, c6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                for i, txt in enumerate(["종류","매입거래처","매입품목","수량","단가","배송"]):
                    [c1, c2, c3, c4, c5, c6][i].markdown(f'<div class="nh-box nh-{"base" if i==0 else "in" if i<5 else "etc"}">{txt}</div>', unsafe_allow_html=True)
                e_s = c1.selectbox("s", ["제일", "중부"], index=s_idx_edit, label_visibility="collapsed")
                e_incom = c2.text_input("incom", safe_str(t.get('incom')), label_visibility="collapsed")
                e_initem = c3.text_input("initem", safe_str(t.get('initem')), label_visibility="collapsed")
                e_inq = c4.text_input("inq", safe_str(t.get('inq')), label_visibility="collapsed")
                e_inprice = c5.text_input("inprice", safe_str(t.get('inprice')), label_visibility="collapsed")
                e_carno = c6.text_input("carno", safe_str(t.get('carno')), label_visibility="collapsed")

                c7, c8, c9, c10, c11, c12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                for i, txt in enumerate(["날짜","매출거래처","매출품목","수량","단가","운송비"]):
                    [c7, c8, c9, c10, c11, c12][i].markdown(f'<div class="nh-box nh-{"base" if i==0 else "out" if i<5 else "etc"}">{txt}</div>', unsafe_allow_html=True)
                e_date = c7.date_input("date", def_date, format="YYYY-MM-DD", label_visibility="collapsed")
                e_outcom = c8.text_input("outcom", safe_str(t.get('outcom')), label_visibility="collapsed")
                e_outitem = c9.text_input("outitem", safe_str(t.get('outitem')), label_visibility="collapsed")
                e_outq = c10.text_input("outq", safe_str(t.get('outq')), label_visibility="collapsed")
                e_outprice = c11.text_input("outprice", safe_str(t.get('outprice')), label_visibility="collapsed")
                e_carprice = c12.text_input("carprice", safe_str(t.get('carprice')), label_visibility="collapsed")
                
                # 메모 입력칸 3개 동시 배치
                st.markdown("<hr style='margin: 15px 0 10px 0; border: 0.5px dashed #555;'>", unsafe_allow_html=True)
                m1, m2, m3 = st.columns(3)
                m1.markdown('<div class="nh-box nh-in" style="font-size:13px;">📝 매입품목 메모</div>', unsafe_allow_html=True)
                e_memoin = m1.text_area("memoin", safe_str(t.get('memoin')), label_visibility="collapsed", height=80)
                
                m2.markdown('<div class="nh-box nh-out" style="font-size:13px;">📝 매출품목 메모</div>', unsafe_allow_html=True)
                e_memoout = m2.text_area("memoout", safe_str(t.get('memoout')), label_visibility="collapsed", height=80)
                
                m3.markdown('<div class="nh-box nh-etc" style="font-size:13px;">🚚 배송 메모</div>', unsafe_allow_html=True)
                e_memocar = m3.text_area("memocar", safe_str(t.get('memocar')), label_visibility="collapsed", height=80)
                
                st.markdown("<hr style='margin: 10px 0; border: none;'>", unsafe_allow_html=True)
                bc1, bc2, bc3, bc4 = st.columns([6, 1.5, 1.5, 1])
                
                if bc2.form_submit_button("💾 수정 저장", use_container_width=True, type="primary"):
                    client = init_connection()
                    try:
                        sheet = client.open('SQL백업260211-jeilinout').worksheet(f"{orig_year}년")
                        headers = api_retry(lambda: sheet.row_values(1))
                        needs_update = False
                        for req_col in ['memoin', 'memoout', 'memocar']:
                            if req_col not in headers:
                                headers.append(req_col)
                                needs_update = True
                        if needs_update:
                            api_retry(lambda: sheet.update(f"A1:{gspread.utils.rowcol_to_a1(1, len(headers))}", [headers]))
                        
                        cell = api_retry(lambda: sheet.find(str(st.session_state.edit_id), in_column=1))
                        if cell:
                            new_row = [st.session_state.edit_id, e_date.strftime('%Y-%m-%d'), e_incom, e_initem, e_inq, e_inprice, e_outcom, e_outitem, e_outq, e_outprice, "", e_s, e_carno, e_carprice, e_memoin, e_memoout, e_memocar]
                            end_col_alpha = gspread.utils.rowcol_to_a1(cell.row, len(new_row))
                            api_retry(lambda: sheet.update(f"A{cell.row}:{end_col_alpha}", [new_row]))
                        st.cache_data.clear(); st.session_state.edit_id = None; st.rerun()
                    except Exception as e:
                        st.error(f"수정 오류: {e}")
                        
                if bc3.form_submit_button("🗑️ 이 줄 삭제", use_container_width=True, type="primary"):
                    client = init_connection()
                    try:
                        sheet = client.open('SQL백업260211-jeilinout').worksheet(f"{orig_year}년")
                        cell = api_retry(lambda: sheet.find(str(st.session_state.edit_id), in_column=1))
                        if cell: 
                            api_retry(lambda: sheet.delete_rows(cell.row))
                        st.cache_data.clear(); st.session_state.edit_id = None; st.rerun()
                    except Exception as e:
                        st.error(f"삭제 오류: {e}")
                        
                if bc4.form_submit_button("취소", use_container_width=True, type="secondary"):
                    st.session_state.edit_id = None
                    if "prev_search_params" in st.session_state:
                        st.session_state.search_params = st.session_state.prev_search_params
                    st.rerun()

    # ---------------------------------------------------------
    # [2] 신규입력 및 복사 창
    # ---------------------------------------------------------
    elif st.session_state.show_new:
        st.markdown("<h3 style='text-align:center; font-weight:bold;'>🆕 신규자료입력 / 복사입력</h3>", unsafe_allow_html=True)
        def_v = {"s_idx":0, "date":get_kst_now().date()}
        if st.session_state.copy_id:
            cr = df[df['id'].astype(str) == str(st.session_state.copy_id)]
            if not cr.empty:
                cr = cr.iloc[0]
                def_v.update({k: safe_str(cr.get(k)) for k in ['incom','initem','inq','inprice','outcom','outitem','outq','outprice','carno','carprice']})
                def_v["s_idx"] = 1 if '중부' in safe_str(cr.get('s')) else 0

        with st.form("new_form"):
            c1, c2, c3, c4, c5, c6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
            for i, txt in enumerate(["종류","매입거래처","매입품목","수량","단가","배송"]):
                [c1, c2, c3, c4, c5, c6][i].markdown(f'<div class="nh-box nh-{"base" if i==0 else "in" if i<5 else "etc"}">{txt}</div>', unsafe_allow_html=True)
            n_s = c1.selectbox("s", ["제일", "중부"], index=def_v["s_idx"], label_visibility="collapsed")
            n_incom = c2.text_input("incom", def_v.get("incom",""), label_visibility="collapsed")
            n_initem = c3.text_input("initem", def_v.get("initem",""), label_visibility="collapsed")
            n_inq = c4.text_input("inq", def_v.get("inq",""), label_visibility="collapsed")
            n_inprice = c5.text_input("inprice", def_v.get("inprice",""), label_visibility="collapsed")
            n_carno = c6.text_input("carno", def_v.get("carno",""), label_visibility="collapsed")
            
            c7, c8, c9, c10, c11, c12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
            for i, txt in enumerate(["날짜","매출거래처","매출품목","수량","단가","운송비"]):
                [c7, c8, c9, c10, c11, c12][i].markdown(f'<div class="nh-box nh-{"base" if i==0 else "out" if i<5 else "etc"}">{txt}</div>', unsafe_allow_html=True)
            n_date = c7.date_input("date", def_v["date"], format="YYYY-MM-DD", label_visibility="collapsed")
            n_outcom = c8.text_input("outcom", def_v.get("outcom",""), label_visibility="collapsed")
            n_outitem = c9.text_input("outitem", def_v.get("outitem",""), label_visibility="collapsed")
            n_outq = c10.text_input("outq", def_v.get("outq",""), label_visibility="collapsed")
            n_outprice = c11.text_input("outprice", def_v.get("outprice",""), label_visibility="collapsed")
            n_carprice = c12.text_input("carprice", def_v.get("carprice",""), label_visibility="collapsed")

            st.markdown("<hr style='margin: 10px 0; border: none;'>", unsafe_allow_html=True)
            bc1, bc2, bc3 = st.columns([8.2, 1.1, 0.7])
            
            if bc2.form_submit_button("신규자료입력", use_container_width=True, type="primary"):
                client = init_connection()
                spreadsheet = client.open('SQL백업260211-jeilinout')
                target_year_str = f"{n_date.year}년"
                
                max_id = 0
                for y in available_years:
                    temp_df = load_data_for_years([y])
                    if not temp_df.empty and 'id' in temp_df.columns:
                        temp_max = temp_df['id'].apply(clean_numeric).max()
                        if pd.notna(temp_max) and temp_max > 0:
                            max_id = int(temp_max)
                            break 
                next_id = max_id + 1 if max_id > 0 else int(get_kst_now().strftime("%y%m%d%H%M%S"))
                
                try:
                    sheet = spreadsheet.worksheet(target_year_str)
                except gspread.exceptions.WorksheetNotFound:
                    sheet = spreadsheet.add_worksheet(title=target_year_str, rows="1000", cols="15")
                    sheet.append_row(['id', 'date', 'incom', 'initem', 'inq', 'inprice', 'outcom', 'outitem', 'outq', 'outprice', 'memo', 's', 'carno', 'carprice', 'memoin', 'memoout', 'memocar'])
                
                headers = api_retry(lambda: sheet.row_values(1))
                needs_update = False
                for req_col in ['memoin', 'memoout', 'memocar']:
                    if req_col not in headers:
                        headers.append(req_col)
                        needs_update = True
                if needs_update:
                    api_retry(lambda: sheet.update(f"A1:{gspread.utils.rowcol_to_a1(1, len(headers))}", [headers]))
                
                new_full_row = [next_id, n_date.strftime('%Y-%m-%d'), n_incom, n_initem, n_inq, n_inprice, n_outcom, n_outitem, n_outq, n_outprice, "", n_s, n_carno, n_carprice, "", "", ""]
                api_retry(lambda: sheet.append_row(new_full_row))
                            
                st.cache_data.clear()
                st.session_state.copy_id = None
                st.session_state.show_new = False
                
                st.session_state.sort_desc = True 
                st.session_state.search_params = {"mode":"최근","title":"최근 입력순서","limit":"20개", "s_filter": "ALL"}
                st.session_state.prev_search_params = st.session_state.search_params
                st.rerun()
                
            if bc3.form_submit_button("취소", use_container_width=True, type="secondary"):
                st.session_state.copy_id = None; st.session_state.show_new = False
                if "prev_search_params" in st.session_state:
                    st.session_state.search_params = st.session_state.prev_search_params
                else:
                    st.session_state.search_params = {"mode":"init"}
                st.rerun()

    # ---------------------------------------------------------
    # [3] 메인 검색 UI 및 데이터 테이블
    # ---------------------------------------------------------
    with st.container():
        
        components.html(
            """
            <!DOCTYPE html>
            <html>
            <head>
            <style>
            body { margin: 0; background-color: #353b48; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; overflow: hidden; }
            .rt-calc-wrap {
                display: flex; justify-content: space-between; align-items: center;
                background-color: #242a33; padding: 12px 18px; border-radius: 6px;
                border: 1px solid #4a5568; margin-bottom: 15px;
            }
            .rt-group { display: flex; align-items: center; gap: 8px; }
            .rt-in {
                width: 100px; height: 32px; box-sizing: border-box;
                padding: 0 8px; border-radius: 4px; border: 1px solid #64748b;
                background: #dbeafe; color: #0f172a; text-align: right; font-weight: bold; outline: none; font-size: 14px;
            }
            .rt-in:focus { border-color: #4e8cff; box-shadow: 0 0 0 2px rgba(78,140,255,0.2); background: #ffffff; }
            .rt-out {
                width: 100px; height: 32px; box-sizing: border-box;
                padding: 0 8px; border-radius: 4px; border: 1px solid #4a5568;
                background: #e2e8f0; color: #1e293b; font-size: 14px;
                display: flex; align-items: center; justify-content: flex-end;
                cursor: default; overflow: hidden; white-space: nowrap;
            }
            .rt-out.orange { background: #ffedd5; border-color: #fdba74; color: #9a3412; }
            .rt-txt { font-size: 13px; font-weight: bold; }
            .rt-txt.blue { color: #60a5fa; }
            .rt-txt.yellow { color: #fbbf24; }
            .rt-op { font-weight: bold; font-size: 16px; }
            .rt-op.blue { color: #60a5fa; }
            .rt-op.yellow { color: #fbbf24; }
            input[type=number]::-webkit-inner-spin-button, input[type=number]::-webkit-outer-spin-button { -webkit-appearance: none; margin: 0; }
            </style>
            </head>
            <body>
            <div class="rt-calc-wrap">
                <div class="rt-group">
                    <input type="number" class="rt-in" id="rt-m1" oninput="rtCalc()" placeholder="0">
                    <span class="rt-op yellow">X</span>
                    <input type="number" class="rt-in" id="rt-m2" oninput="rtCalc()" placeholder="0">
                    <span class="rt-op yellow">=</span>
                    <div class="rt-out" id="rt-mr">0</div>
                </div>
                <div class="rt-group">
                    <input type="number" class="rt-in" id="rt-d1" oninput="rtCalc()" placeholder="0">
                    <span class="rt-op blue">/</span>
                    <input type="number" class="rt-in" id="rt-d2" oninput="rtCalc()" placeholder="0">
                    <span class="rt-op blue">=</span>
                    <div class="rt-out" id="rt-dr">0</div>
                </div>
                <div class="rt-group">
                    <div class="rt-out" id="rt-vm" style="width: auto; min-width: 90px;">0</div>
                    <span class="rt-txt blue">VAT-10%</span>
                    <span class="rt-op" style="color: #4a5568; margin: 0 4px;">/</span>
                    <input type="number" class="rt-in" id="rt-v1" oninput="rtCalc()" placeholder="기준금액" style="text-align: center; width: 120px;">
                    <span class="rt-op" style="color: #4a5568; margin: 0 4px;">/</span>
                    <span class="rt-txt yellow">VAT+10%</span>
                    <div class="rt-out orange" id="rt-vp" style="width: auto; min-width: 90px;">0</div>
                </div>
            </div>
            <script>
            function rtFmt(num) {
                if (!num || isNaN(num) || !isFinite(num)) return '<span style="font-weight: bold;">0</span>';
                let parts = num.toString().split('.');
                let intPart = parseInt(parts[0], 10).toLocaleString('ko-KR');
                if (parts[1]) { 
                    let decPart = parts[1].length > 4 ? parts[1].substring(0, 4) : parts[1]; 
                    return '<span style="font-weight: bold;">' + intPart + '</span><span style="font-weight: normal; opacity: 0.85;">.' + decPart + '</span>';
                }
                return '<span style="font-weight: bold;">' + intPart + '</span>';
            }
            function rtCalc() {
                let d1 = parseFloat(document.getElementById('rt-d1').value) || 0;
                let d2 = parseFloat(document.getElementById('rt-d2').value) || 0;
                document.getElementById('rt-dr').innerHTML = d2 !== 0 ? rtFmt(d1 / d2) : '<span style="font-weight: bold;">0</span>';
                let v1 = parseFloat(document.getElementById('rt-v1').value) || 0;
                document.getElementById('rt-vm').innerHTML = rtFmt(v1 / 1.1);
                document.getElementById('rt-vp').innerHTML = rtFmt(v1 * 1.1);
                let m1 = parseFloat(document.getElementById('rt-m1').value) || 0;
                let m2 = parseFloat(document.getElementById('rt-m2').value) || 0;
                document.getElementById('rt-mr').innerHTML = rtFmt(m1 * m2);
            }
            </script>
            </body>
            </html>
            """,
            height=75
        )

        sp = params
        s_filt = sp.get("s_filter", "ALL")
        s_idx = ["ALL", "제일", "중부"].index(s_filt) if s_filt in ["ALL", "제일", "중부"] else 0
        
        is_gigan = (sp.get("mode") == "기간")
        comp1 = sp.get("company", "") if is_gigan else ""
        item1 = sp.get("item", "") if is_gigan else ""
        t_idx1 = ["ALL", "매입", "매출"].index(sp.get("type", "ALL")) if is_gigan and sp.get("type", "ALL") in ["ALL", "매입", "매출"] else 0

        is_month = (sp.get("mode") == "월별상세")
        comp2 = sp.get("company", "") if is_month else ""
        item2 = sp.get("item", "") if is_month else ""
        t_idx2 = ["ALL", "매입", "매출"].index(sp.get("type", "ALL")) if is_month and sp.get("type", "ALL") in ["ALL", "매입", "매출"] else 0
        
        d_start = sp.get("start", datetime(2014,1,1).date()) if is_gigan else datetime(2014,1,1).date()
        d_end = sp.get("end", get_kst_now().date()) if is_gigan else get_kst_now().date()
        
        m_year = sp.get("year", get_kst_now().year)
        y_idx = years.index(m_year) if m_year in years else 0
        m_month = sp.get("month", get_kst_now().month)
        m_idx = months.index(m_month) if m_month in months else get_kst_now().month-1
        
        target_date = sp.get("date", get_kst_now().date())

        with st.form(key="form_row1", border=False):
            r1_1, r1_2, r1_3, r1_4, r1_5, r1_6 = st.columns([1.5, 2.5, 1, 2, 2, 2.5])
            with r1_1: t1 = st.radio("t1", ["ALL", "매입", "매출"], index=t_idx1, horizontal=True, label_visibility="collapsed")
            with r1_2: dr1 = st.date_input("dr1", [d_start, d_end], format="YYYY-MM-DD", label_visibility="collapsed")
            with r1_3: s1 = st.selectbox("s1", ["ALL", "제일", "중부"], index=s_idx, label_visibility="collapsed")
            with r1_4: c1 = st.text_input("c1", value=comp1, placeholder="거래처 검색", label_visibility="collapsed")
            with r1_5: i1 = st.text_input("i1", value=item1, placeholder="품목 검색", label_visibility="collapsed")
            with r1_6: b1 = st.form_submit_button("기간 거래처&품목", use_container_width=True, type="primary")

        st.markdown("<hr style='margin:10px 0; border:0.5px solid #4a5568;'>", unsafe_allow_html=True)

        with st.form(key="form_row2", border=False):
            r2_1, r2_2, r2_3, r2_4, r2_5, r2_6, r2_7 = st.columns([1.5, 1.2, 1.3, 1, 2, 2, 2.5])
            with r2_1: t2 = st.radio("t2", ["ALL", "매입", "매출"], index=t_idx2, horizontal=True, label_visibility="collapsed")
            with r2_2: y2 = st.selectbox("y2", years, index=y_idx, label_visibility="collapsed", format_func=lambda x: f"{x}년")
            with r2_3: m2 = st.selectbox("m2", months, index=m_idx, format_func=lambda x:f"{x}월", label_visibility="collapsed")
            with r2_4: s2 = st.selectbox("s2", ["ALL", "제일", "중부"], index=s_idx, label_visibility="collapsed")
            with r2_5: c2 = st.text_input("c2", value=comp2, placeholder="거래처 검색", label_visibility="collapsed")
            with r2_6: i2 = st.text_input("i2", value=item2, placeholder="품목 검색", label_visibility="collapsed")
            with r2_7: b2 = st.form_submit_button("월별 거래처&품목", use_container_width=True, type="primary")

        st.markdown("<hr style='margin:10px 0; border:0.5px solid #4a5568;'>", unsafe_allow_html=True)

        u1, u2, u3, u4, u5, u6, u7, u8, u9, u10, u11, u12, u13, u14, u15 = st.columns([0.7, 1.0, 0.8, 0.8, 1.0, 0.8, 0.8, 1.3, 0.8, 1.1, 0.7, 1.0, 0.8, 0.9, 0.9])
        
        with u1: s3 = st.selectbox("s3", ["ALL", "제일", "중부"], index=s_idx, label_visibility="collapsed")
        with u2: y3 = st.selectbox("y3", years, index=y_idx, label_visibility="collapsed", format_func=lambda x: f"{x}년")
        with u3: m3 = st.selectbox("m3", months, index=m_idx, format_func=lambda x:f"{x}월", label_visibility="collapsed")
        with u4: b_set = st.button("결산", use_container_width=True, type="primary")
        
        with u5: b_new = st.button("신규", use_container_width=True, type="primary")
        
        with u6: lmt = st.selectbox("l4", ["20개", "50개", "100개"], index=0, label_visibility="collapsed")
        with u7: b_rec = st.button("최근", use_container_width=True, type="primary")
        
        with u8: d_day = st.date_input("d2", value=target_date, format="YYYY-MM-DD", label_visibility="collapsed")
        with u9: b_day = st.button("일검색", use_container_width=True, type="primary")
        with u10: b_ayt = st.button("어제오늘내일", use_container_width=True, type="primary")
        
        with u11: s5 = st.selectbox("s5", ["ALL", "제일", "중부"], index=s_idx, label_visibility="collapsed")
        with u12: y4 = st.selectbox("y4", years, index=y_idx, key="y4_sel", label_visibility="collapsed", format_func=lambda x: f"{x}년")
        with u13: m4 = st.selectbox("m4", months, index=m_idx, format_func=lambda x:f"{x}월", key="m4_sel", label_visibility="collapsed")
        with u14: b_mon = st.button("월별", use_container_width=True, type="primary")
        with u15: b_yong = st.button("용차", use_container_width=True, type="primary")

        if b1: st.session_state.search_params = {"mode":"기간","title":f"기간 검색 ({dr1[0]} ~ {dr1[1] if len(dr1)>1 else dr1[0]})","type":t1,"company":c1,"item":i1,"limit":"ALL","start":dr1[0],"end":dr1[1] if len(dr1)>1 else dr1[0], "s_filter": s1}; st.session_state.sort_desc = False; st.session_state.prev_search_params = st.session_state.search_params; st.rerun()
        elif b2: st.session_state.search_params = {"mode":"월별상세","title":f"{y2}년 {m2}월 상세 검색","type":t2,"year":y2,"month":m2,"company":c2,"item":i2, "s_filter": s2}; st.session_state.sort_desc = False; st.session_state.prev_search_params = st.session_state.search_params; st.rerun()
        elif b_set: st.session_state.search_params = {"mode":"결산","year":y3,"month":m3, "s_filter": s3}; st.session_state.sort_desc = False; st.session_state.prev_search_params = st.session_state.search_params; st.rerun()
        elif b_new: 
            st.session_state.show_new = True; st.session_state.copy_id = None; st.rerun()
        elif b_rec: st.session_state.search_params = {"mode":"최근","title":"최근 입력순서","limit":lmt, "s_filter": "ALL"}; st.session_state.sort_desc = True; st.session_state.prev_search_params = st.session_state.search_params; st.rerun()
        elif b_day: st.session_state.search_params = {"mode":"일","title":f"일간 검색 ({d_day})","date":d_day, "s_filter": "ALL"}; st.session_state.sort_desc = False; st.session_state.prev_search_params = st.session_state.search_params; st.rerun()
        elif b_ayt:
            st.session_state.search_params = {
                "mode":"기간",
                "title":f"어제·오늘·내일 검색 ({d_day} 기준)",
                "type":"ALL",
                "company":"",
                "item":"",
                "limit":"ALL",
                "start": d_day - timedelta(days=1),
                "end": d_day + timedelta(days=1),
                "s_filter": "ALL"
            }
            st.session_state.sort_desc = False
            st.session_state.prev_search_params = st.session_state.search_params
            st.rerun()
        elif b_mon: st.session_state.search_params = {"mode":"월별","title":f"{y4}년 {m4}월 기본 검색","year":y4,"month":m4, "s_filter": s5}; st.session_state.sort_desc = False; st.session_state.prev_search_params = st.session_state.search_params; st.rerun()
        elif b_yong: st.session_state.search_params = {"mode":"용차","title":f"{y4}년 {m4}월 배송(용/다) 검색","year":y4,"month":m4, "s_filter": s5}; st.session_state.sort_desc = False; st.session_state.prev_search_params = st.session_state.search_params; st.rerun()

        if params["mode"] != "init":
            f_df = df.copy()
            
            if params["mode"] == "기간": 
                f_df = f_df[(f_df[date_col].dt.date >= params["start"]) & (f_df[date_col].dt.date <= params["end"])]
            elif params["mode"] in ["월별상세", "월별", "용차", "결산"]: 
                f_df = f_df[(f_df['year']==params['year'])&(f_df['month']==params['month'])]
                if params["mode"] == "용차":
                    f_df = f_df[f_df['carno'].astype(str).str.contains('용|다', na=False, regex=True)]
            elif params["mode"] == "일": 
                f_df = f_df[f_df[date_col].dt.date == params["date"]]

            target_type = params.get("type", "ALL")
            if target_type == "매입": f_df = f_df[f_df['incom'].astype(str).str.strip() != '']
            elif target_type == "매출": f_df = f_df[f_df['outcom'].astype(str).str.strip() != '']
            
            s_filter = params.get("s_filter", "ALL")
            if s_filter != "ALL":
                f_df = f_df[f_df['s'].astype(str).str.contains(s_filter, na=False)]
            
            if params.get("company"): f_df = f_df[f_df['incom'].str.contains(params["company"], na=False)|f_df['outcom'].str.contains(params["company"], na=False)]
            if params.get("item"): f_df = f_df[f_df['initem'].str.contains(params["item"], na=False)|f_df['outitem'].str.contains(params["item"], na=False)]
            
            if params["mode"] == "최근":
                f_df = f_df.sort_values(by=['id_val'], ascending=[False])
            else:
                f_df = f_df.sort_values(by=[date_col, 'id_val'], ascending=[not st.session_state.sort_desc, not st.session_state.sort_desc])
            
            limit_str = str(params.get("limit", "ALL"))
            if "개" in limit_str:
                num = int(limit_str.replace("개", ""))
                if st.session_state.sort_desc or params["mode"] == "최근": 
                    f_df = f_df.head(num)
                else: 
                    f_df = f_df.tail(num)

            t_in_q, t_in_a = f_df['inq_val'].sum(), f_df['in_total'].sum()
            t_out_q, t_out_a = f_df['outq_val'].sum(), f_df['out_total'].sum()
            t_car = f_df['carprice_val'].sum()
            t_profit = t_out_a - t_in_a - t_car
            
            f_df['profit'] = f_df['out_total'] - f_df['in_total'] - f_df['carprice_val']
            
            print_title = params.get("title", "검색결과")
            cond_texts = []
            if params.get("type", "ALL") != "ALL": cond_texts.append(f"분류: {params['type']}")
            if params.get("company"): cond_texts.append(f"거래처: '{params['company']}'")
            if params.get("item"): cond_texts.append(f"품목: '{params['item']}'")
            if cond_texts: print_title += f" ➔ (검색조건: {', '.join(cond_texts)})"
            if s_filter != "ALL": print_title = f"[{s_filter}] " + print_title

            if params["mode"] == "결산":
                st.markdown(f"<h2 style='text-align: center; color: #4e8cff; margin-bottom: 20px;'>📊 {print_title} 결산 요약 대시보드</h2>", unsafe_allow_html=True)
                
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("총 매출액 (A) ↗", f"{t_out_a:,.0f} 원")
                with col2: st.metric("총 매입액 (B) ↘", f"{t_in_a:,.0f} 원")
                with col3: st.metric("총 운송비 (C) 🚚", f"{t_car:,.0f} 원")
                with col4:
                    margin = (t_profit / t_out_a * 100) if t_out_a > 0 else 0
                    st.metric("최종 순수익 (A-B-C) 💰", f"{t_profit:,.0f} 원", f"마진율 {margin:.1f}%")
                
                st.markdown("<hr style='border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)
                
                st.markdown("<h4 style='color: #f8fafc;'>📈 일별 매출 및 매입 흐름</h4>", unsafe_allow_html=True)
                daily_df = f_df.groupby('date')[['out_total', 'in_total']].sum().reset_index()
                if not daily_df.empty:
                    daily_df.set_index('date', inplace=True)
                    daily_df.columns = ['매출액', '매입액']
                    st.bar_chart(daily_df, height=350, use_container_width=True)
                else:
                    st.info("해당 월의 차트 데이터가 없습니다.")

                st.markdown("<br>", unsafe_allow_html=True)
                
                rank_col1, rank_col2, rank_col3 = st.columns(3)
                
                with rank_col1:
                    st.markdown("<h4 style='color: #60a5fa;'>🏆 최고 매출 거래처 Top 5</h4>", unsafe_allow_html=True)
                    valid_outcom = f_df[f_df['outcom'].astype(str).str.strip() != '']
                    if not valid_outcom.empty:
                        top_out = valid_outcom.groupby('outcom')['out_total'].sum().sort_values(ascending=False).head(5).reset_index()
                        top_out.columns = ['거래처명', '매출액']
                        st.dataframe(top_out.style.format({'매출액': '{:,.0f}'}), use_container_width=True, hide_index=True)
                    else: st.caption("매출 내역이 없습니다.")
                        
                    st.markdown("<br><h4 style='color: #fbbf24;'>💎 최고 이익 거래처 Top 5</h4>", unsafe_allow_html=True)
                    if not valid_outcom.empty:
                        top_profit = valid_outcom.groupby('outcom')['profit'].sum().sort_values(ascending=False).head(5).reset_index()
                        top_profit.columns = ['거래처명', '순이익']
                        st.dataframe(top_profit.style.format({'순이익': '{:,.0f}'}), use_container_width=True, hide_index=True)
                    else: st.caption("수익 내역이 없습니다.")
                
                with rank_col2:
                    st.markdown("<h4 style='color: #f472b6;'>📉 최고 매입 거래처 Top 5</h4>", unsafe_allow_html=True)
                    valid_incom = f_df[f_df['incom'].astype(str).str.strip() != '']
                    if not valid_incom.empty:
                        top_in = valid_incom.groupby('incom')['in_total'].sum().sort_values(ascending=False).head(5).reset_index()
                        top_in.columns = ['거래처명', '매입액']
                        st.dataframe(top_in.style.format({'매입액': '{:,.0f}'}), use_container_width=True, hide_index=True)
                    else: st.caption("매입 내역이 없습니다.")
                        
                    st.markdown("<br><h4 style='color: #a78bfa;'>🚚 운송비 지출(배송) Top 5</h4>", unsafe_allow_html=True)
                    valid_car = f_df[f_df['carno'].astype(str).str.strip() != '']
                    if not valid_car.empty:
                        top_car = valid_car.groupby('carno')['carprice_val'].sum().sort_values(ascending=False).head(5).reset_index()
                        top_car.columns = ['배송수단', '운송비총액']
                        st.dataframe(top_car.style.format({'운송비총액': '{:,.0f}'}), use_container_width=True, hide_index=True)
                    else: st.caption("운송비 내역이 없습니다.")

                with rank_col3:
                    st.markdown("<h4 style='color: #34d399;'>📦 베스트셀러 품목 Top 5</h4>", unsafe_allow_html=True)
                    valid_item = f_df[f_df['outitem'].astype(str).str.strip() != '']
                    if not valid_item.empty:
                        top_item = valid_item.groupby('outitem')['outq_val'].sum().sort_values(ascending=False).head(5).reset_index()
                        top_item.columns = ['품목명', '판매수량']
                        st.dataframe(top_item.style.format({'판매수량': '{:,.0f}'}), use_container_width=True, hide_index=True)
                    else: st.caption("판매 품목 내역이 없습니다.")
                        
                    st.markdown("<br><h4 style='color: #818cf8;'>📥 최다 매입 품목 Top 5</h4>", unsafe_allow_html=True)
                    valid_initem = f_df[f_df['initem'].astype(str).str.strip() != '']
                    if not valid_initem.empty:
                        top_initem = valid_initem.groupby('initem')['inq_val'].sum().sort_values(ascending=False).head(5).reset_index()
                        top_initem.columns = ['품목명', '매입수량']
                        st.dataframe(top_initem.style.format({'매입수량': '{:,.0f}'}), use_container_width=True, hide_index=True)
                    else: st.caption("매입 품목 내역이 없습니다.")

            # 💡 그 외 검색 버튼 클릭 시 (테이블 렌더링)
            else:
                pwd_token = str(st.secrets["tom_password"])
                current_sp_encoded = encode_sp(st.session_state.search_params)
                
                row_html_list = []
                for _, r in f_df.iterrows():
                    rid, dt = safe_str(r['id']), r[date_col].strftime('%Y-%m-%d')
                    s_cls = "txt-green" if "제일" in str(r['s']) else "txt-purple"
                    row_year = int(r['year'])
                    
                    v_link = f'<a href="?copy_id={rid}&year={row_year}&token={pwd_token}&sp={current_sp_encoded}" target="_self" style="text-decoration:none;"><span class="{s_cls}">{r["s"]}</span></a>'
                    edit_link_target = f"?edit_id={rid}&year={row_year}&token={pwd_token}&sp={current_sp_encoded}"
                    d_link = f'<a href="{edit_link_target}" target="_self" style="color:#1e293b; text-decoration:none;">{dt}</a>'
                    
                    # 💡 [검토 및 수정] 수익 계산 로직 정교화 (운송비 포함)
                    in_tot = r["in_total"] if pd.notnull(r["in_total"]) else 0
                    in_tot_vat = in_tot * 1.1       
                    in_vat_only = in_tot * 0.1      
                    
                    out_tot = r["out_total"] if pd.notnull(r["out_total"]) else 0
                    out_tot_vat = out_tot * 1.1     
                    out_vat_only = out_tot * 0.1    
                    
                    car_val = r["carprice_val"] if pd.notnull(r["carprice_val"]) else 0
                    
                    # 운송비까지 뺀 진짜 최종 순이익!
                    profit_final = out_tot_vat - in_tot_vat - car_val
                    
                    memoin_val = safe_str(r.get("memoin", ""))
                    initem_val = safe_str(r.get("initem", ""))
                    in_disp = initem_val if initem_val.strip() else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    
                    if memoin_val:
                        initem_html = f'<div class="memo-tooltip-in" style="font-weight: bold;"><a href="{edit_link_target}" target="_self" style="text-decoration:none;"><span class="disp-in">{in_disp}</span></a><span class="memo-text" style="text-align:left; white-space:pre-wrap;"><span style="color:#000000 !important; font-weight:bold !important;">{memoin_val}</span></span></div>'
                    else:
                        initem_html = f'<a href="{edit_link_target}" target="_self" style="text-decoration:none;"><span class="disp-in">{in_disp}</span></a>'

                    memoout_val = safe_str(r.get("memoout", ""))
                    outitem_val = safe_str(r.get("outitem", ""))
                    out_disp = outitem_val if outitem_val.strip() else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    if memoout_val:
                        outitem_html = f'<div class="memo-tooltip-out" style="font-weight: bold;"><a href="{edit_link_target}" target="_self" style="text-decoration:none;"><span class="disp-out">{out_disp}</span></a><span class="memo-text" style="text-align:left; white-space:pre-wrap;"><span style="color:#000000 !important; font-weight:bold !important;">{memoout_val}</span></span></div>'
                    else:
                        outitem_html = f'<a href="{edit_link_target}" target="_self" style="text-decoration:none;"><span class="disp-out">{out_disp}</span></a>'

                    memocar_val = safe_str(r.get("memocar", ""))
                    carno_val = safe_str(r.get("carno", ""))
                    car_disp = carno_val if carno_val.strip() else "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                    if memocar_val:
                        carno_html = f'<div class="memo-tooltip-base" style="font-weight: bold;"><a href="{edit_link_target}" target="_self" style="text-decoration:none;"><span class="disp-car">{car_disp}</span></a><span class="memo-text" style="text-align:left; white-space:pre-wrap;"><span style="color:#000000 !important; font-weight:bold !important;">{memocar_val}</span></span></div>'
                    else:
                        carno_html = f'<a href="{edit_link_target}" target="_self" style="text-decoration:none;"><span class="disp-car">{car_disp}</span></a>'
                    
                    inq_val_str = f'{r["inq_val"]:,.0f}' if pd.notnull(r["inq_val"]) else '0'
                    in_memo = f"<div style='text-align:right;'><span style='color:#000000 !important;'>공급가액(VAT별도) : {in_tot:,.0f} 원</span><br><span style='color:#000000 !important;'>+ 부가세(10%) : {in_vat_only:,.0f} 원</span><br><hr style='margin:4px 0; border:0.5px dashed #000000 !important;'><span style='color:#000000 !important; font-weight:bold;'>매입 합계(VAT포함) : {in_tot_vat:,.0f} 원</span></div>"
                    inq_html = f'<div class="memo-tooltip-in">{inq_val_str}<span class="memo-text">{in_memo}</span></div>'
                    
                    outq_val_str = f'{r["outq_val"]:,.0f}' if pd.notnull(r["outq_val"]) else '0'
                    
                    # 💡 [핵심 기술] 매출 툴팁을 '결산 영수증' 형태로 전면 개편! 매입, 매출, 운송비 내역까지 한방에 표기
                    out_memo = f"""<div style='text-align:right;'>
                    <span style='color:#000000 !important;'>[매출] 공급가: {out_tot:,.0f} + VAT: {out_vat_only:,.0f}</span><br>
                    <span style='color:#000000 !important; font-weight:bold;'>▶ 매출 합계(A) : {out_tot_vat:,.0f} 원</span><br>
                    <hr style='margin:4px 0; border:0.5px dashed #000000 !important;'>
                    <span style='color:#000000 !important;'>[매입] 공급가: {in_tot:,.0f} + VAT: {in_vat_only:,.0f}</span><br>
                    <span style='color:#000000 !important; font-weight:bold;'>▶ 매입 합계(B) : {in_tot_vat:,.0f} 원</span><br>
                    <hr style='margin:4px 0; border:0.5px dashed #000000 !important;'>
                    <span style='color:#000000 !important; font-weight:bold;'>▶ 운송비(C) : {car_val:,.0f} 원</span><br>
                    <hr style='margin:4px 0; border:0.5px solid #000000 !important;'>
                    <span style='color:#000000 !important; font-weight:bold; font-size: 14px;'>= 순이익(A-B-C) : {profit_final:,.0f} 원</span>
                    </div>"""
                    outq_html = f'<div class="memo-tooltip-out">{outq_val_str}<span class="memo-text">{out_memo}</span></div>'
                    
                    row_html = f'<tr><td class="tc">{v_link}</td><td class="tc">{d_link}</td><td class="tl txt-in-bold">{r["incom"]}</td><td class="tl txt-in">{initem_html}</td><td class="tr txt-in">{inq_html}</td><td class="tr txt-in">{r["inprice_val"]:,.0f}</td><td class="tl txt-out-bold">{r["outcom"]}</td><td class="tl txt-out">{outitem_html}</td><td class="tr txt-out">{outq_html}</td><td class="tr txt-out">{r["outprice_val"]:,.0f}</td><td class="tc txt-gray print-hide-col">{rid}</td><td class="tc txt-gray">{carno_html}</td><td class="tr txt-black">{r["carprice_val"]:,.0f}</td></tr>'
                    row_html_list.append(row_html)
                    
                footer_html = f'<tr><td colspan="2" class="th-base">자료수 : {len(f_df)}개</td><td colspan="4" class="th-in">매입수량 : {t_in_q:,.0f} | 매입금액 : {t_in_a:,.0f}원</td><td colspan="4" class="th-out">매출수량 : {t_out_q:,.0f} | 매출금액 : {t_out_a:,.0f}원</td><td colspan="3" class="th-base">운송비 : {t_car:,.0f}원</td></tr>'
                footer_html += f'<tr><td colspan="13" class="sum-profit">검색내 총수익 : {t_profit:,.0f}원</td></tr>'

                title_div = f'<div class="print-only-title" style="background-color: white !important; color: black !important; text-align: left; font-size: 26px; border-bottom: 2px solid #555 !important; padding: 10px 0px !important; margin-bottom: 10px; font-weight: bold;">{print_title} &nbsp; <span style="font-size: 15px; color: #555 !important; font-weight: normal !important;">| 출력 개수: {len(f_df)}개</span></div>'
                
                table_html = '<div class="custom-table-container">'
                table_html += title_div
                table_html += '<table class="custom-table">'
                table_html += '<thead><tr class="print-fake-margin"><th colspan="13" style="height: 12mm; border: none !important; background-color: white !important; padding: 0 !important;"></th></tr>'
                table_html += '<tr><th class="th-base">Vat</th><th class="th-base">날짜</th><th class="th-in">매입거래처</th><th class="th-in">매입품목 (MEMO)</th><th class="th-in">수량</th><th class="th-in">단가</th><th class="th-out">매출거래처</th><th class="th-out">매출품목 (MEMO)</th><th class="th-out">수량</th><th class="th-out">단가</th><th class="th-base print-hide-col">NO</th><th class="th-etc">배송</th><th class="th-etc">운송비</th></tr></thead>'
                table_html += '<tbody>'
                table_html += "".join(row_html_list)
                table_html += footer_html
                table_html += '</tbody>'
                table_html += '<tfoot style="display: table-footer-group !important;"><tr class="print-fake-margin"><td colspan="13" style="height: 12mm; border: none !important; background-color: white !important; padding: 0 !important;"></td></tr></tfoot>'
                table_html += '</table></div>'

                # 인쇄 관련 코드는 절대 변경하지 않음 (안전 보존)
                print_html_content = f"""
                <!DOCTYPE html>
                <html><head><title>인쇄 미리보기</title>
                <meta charset="utf-8">
                <style>
                    @page {{ size: A4 portrait; margin: 0mm; }} 
                    body {{ font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; color: black; background: white; margin: 0; padding: 0 10mm; box-sizing: border-box; }}
                    .custom-table-container {{ width: 100%; zoom: 67%; }} 
                    .custom-table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; background: white !important; }}
                    .custom-table th, .custom-table td {{ border: 1px solid #aaa; padding: 6px 8px; color: black !important; }}
                    .custom-table th {{ text-align: center; font-weight: bold; padding: 8px 6px; }}
                    .print-only-title {{ display: block !important; margin-top: 15mm !important; }}
                    .print-fake-margin {{ display: table-row !important; }}
                    .th-base {{ background-color: #e2e8f0 !important; color: black !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                    .th-in {{ background-color: #dbeafe !important; color: black !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                    .th-out {{ background-color: #ffedd5 !important; color: black !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                    .th-etc {{ background-color: #fef08a !important; color: black !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                    .sum-profit {{ background-color: #f1f5f9 !important; text-align: right; padding: 12px 20px; font-weight: bold; border-top: 1px solid #444; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
                    .tc {{ text-align: center; }} .tl {{ text-align: left; }} .tr {{ text-align: right; }}
                    a {{ color: black !important; text-decoration: none !important; pointer-events: none; }}
                    span.disp-in, span.disp-out, span.disp-car {{ color: black !important; }} /* 인쇄 시 텍스트 강제 블랙 */
                    .print-hide-col {{ display: none !important; }}
                    thead {{ display: table-header-group !important; }}
                    .custom-table tr {{ page-break-inside: avoid; }}
                    .memo-text {{ display: none !important; }}
                </style>
                </head><body>
                {table_html}
                </body></html>
                """
                
                col_t1, col_t2, col_t3, col_t4 = st.columns([5.3, 1.7, 1.5, 1.5])
                with col_t1: st.markdown(f'<div class="table-title-box"><span style="font-size:26px; font-weight:bold; color:#f8fafc;">{print_title}</span> <span style="font-size:15px; color:#cbd5e1; margin-left:10px;">| 출력 개수: {len(f_df)}개</span></div>', unsafe_allow_html=True)
                
                with col_t2: 
                    if st.button("🔄 날짜정렬", use_container_width=True, type="secondary"):
                        st.session_state.sort_desc = not st.session_state.sort_desc; st.rerun()
                
                with col_t3:
                    components.html(
                        f"""
                        <!DOCTYPE html>
                        <html>
                        <head>
                        <style>
                        body {{ margin: 0; padding: 0; overflow: hidden; background-color: transparent; }}
                        .btn-print {{
                            width: 100%; height: 40px; background-color: #757c43; color: white;
                            border: 1px solid #757c43; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;
                            font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
                            display: flex; align-items: center; justify-content: center; box-sizing: border-box;
                        }}
                        .btn-print:hover {{ background-color: #646a39; border-color: #646a39; }}
                        </style>
                        <script>
                        function fastPrint() {{
                            const htmlContent = {json.dumps(print_html_content)};
                            let iframe = document.getElementById('print-frame');
                            if (iframe) {{ document.body.removeChild(iframe); }}
                            iframe = document.createElement('iframe');
                            iframe.id = 'print-frame';
                            iframe.style.position = 'absolute';
                            iframe.style.width = '1px';
                            iframe.style.height = '1px';
                            iframe.style.opacity = '0';
                            iframe.style.pointerEvents = 'none';
                            document.body.appendChild(iframe);
                            const doc = iframe.contentWindow.document;
                            doc.open();
                            doc.write(htmlContent);
                            doc.close();
                            setTimeout(function() {{
                                iframe.contentWindow.focus();
                                iframe.contentWindow.print();
                            }}, 150);
                        }}
                        </script>
                        </head>
                        <body>
                        <button class="btn-print" onclick="fastPrint()">🖨️ PRINT</button>
                        </body>
                        </html>
                        """,
                        height=40
                    )
                
                with col_t4:
                    csv = f_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("💾 EXCEL", data=csv, file_name=f"검색결과_{get_kst_now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True, type="primary")

                st.markdown(table_html, unsafe_allow_html=True)

except Exception as e: st.error(f"⚠️ 시스템 오류: {e}")
st.markdown("<br><p style='text-align:center; color:#64748b;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
