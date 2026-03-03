import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import io

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# 커스텀 CSS 주입 (디자인 통일 및 레이아웃 정돈)
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #2b323c; }
    .main .block-container { padding-top: 1rem; max-width: 98%; }
    h1, h2, h3, p, span { color: #ffffff !important; }
    
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
        border-radius: 4px !important;
        font-weight: bold !important;
        padding: 0px 10px !important;
    }

    /* 메인 데이터 테이블 스타일 */
    .custom-table-container { width: 100%; margin-top: 5px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
    .table-title-box { background-color: #2b323c; padding: 10px 15px; border-top: 2px solid #555; border-bottom: none; display: flex; align-items: center; justify-content: space-between; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }
    .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; }
    .custom-table th { text-align: center; color: white; font-weight: bold; padding: 10px 6px; }
    .custom-table tr:nth-child(even) { background-color: #f8f9fa; }
    .custom-table tr:hover { background-color: #e2e6ea; }
    
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

    /* 결산 뷰 스타일 */
    .settle-header-top { background-color: #5d607e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; border-bottom: 3px solid #b8b8b8; }
    .settle-container { display: flex; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; color: #333; margin-top: 5px; }
    .settle-lists { display: flex; flex: 1; border: 1px solid #777; background: white; }
    .settle-col { flex: 1; border-right: 1px solid #ccc; background: white; }
    .settle-col:last-child { border-right: none; }
    .sh-title { text-align: center; color: white; padding: 8px; font-weight: bold; border-bottom: 1px solid #ccc; font-size: 14px;}
    .sh-1 { background-color: #8385b2; } .sh-2 { background-color: #7b9cbf; } .sh-3 { background-color: #c99f5e; } .sh-4 { background-color: #d1b15c; } .sh-5 { background-color: #8ba966; }
    .ul-list { list-style: none; padding: 0; margin: 0; }
    .ul-list li { padding: 6px 10px; border-bottom: 1px solid #eee; display: flex; align-items: flex-start; font-size: 14px;}
    .li-num { width: 25px; color: #555; } .li-name { flex: 1; word-break: break-all; } .li-icon { color: #a1a1aa; font-size: 16px; }
    .settle-summary { width: 350px; border: 1px solid #777; margin-left: 10px; background-color: #5d607e; color: white; display: flex; flex-direction: column;}
    .sum-subhead { background-color: #3b3d56; text-align: center; padding: 8px; font-size: 14px; font-weight: bold;}
    .sum-table { width: 100%; border-collapse: collapse; }
    .sum-table td { padding: 10px 12px; border-bottom: 1px solid #888; font-size: 14px; color: white; }
    .bg-blue { background-color: #707b9e; } .bg-orange { background-color: #c58f55; } .bg-olive { background-color: #757c43; } .bg-dark { background-color: #2b2b2b; }
    .tr-right { text-align: right; font-weight: bold;}
    .alert-box { background-color: white; color: black; margin: 10px; border: 1px solid #ccc; font-size: 13px; }
    .alert-title { background-color: #cc0000; color: white; text-align: center; padding: 6px; font-weight: bold; }
    .alert-ul { padding-left: 20px; margin: 10px 10px 10px 0; } .alert-ul li { margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 보안 및 세션 상태 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "search_params" not in st.session_state: st.session_state.search_params = {"mode": "init"}
if "sort_desc" not in st.session_state: st.session_state.sort_desc = True 
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "copy_id" not in st.session_state: st.session_state.copy_id = None

# URL 파라미터 감지 및 자동 로그인 (복사/수정 연동)
if "edit_id" in st.query_params or "copy_id" in st.query_params:
    token = str(st.secrets.get("tom_password", ""))
    if st.query_params.get("token") == token:
        st.session_state.authenticated = True
        if "edit_id" in st.query_params: st.session_state.edit_id = st.query_params["edit_id"]
        if "copy_id" in st.query_params:
            st.session_state.copy_id = st.query_params["copy_id"]
            st.session_state.search_params = {"mode": "신규입력"}
    st.query_params.clear()
    st.rerun()

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
                else: st.error("❌ 비밀번호 오류")
    st.stop()

# --- [4. 상단 상태바] ---
col_t, col_r, col_l = st.columns([7, 1.5, 1.5])
with col_t: st.markdown("<h3 style='margin:0;'>📦 입출력 통합 관리 시스템</h3>", unsafe_allow_html=True)
with col_r:
    if st.button("🔄 데이터 갱신", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
with col_l:
    if st.button("🔓 LOGOUT", use_container_width=True, type="primary"):
        st.session_state.authenticated = False
        st.rerun()
st.markdown("<hr style='margin: 10px 0px 20px 0px; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

# --- [5. 데이터 유틸리티] ---
@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_data():
    client = init_connection()
    sheet = client.open('SQL백업260211-jeilinout').sheet1
    raw = sheet.get_all_values()
    if not raw: return pd.DataFrame()
    header = [n.strip() if n.strip() else f"col_{i}" for i, n in enumerate(raw[0])]
    return pd.DataFrame(raw[1:], columns=header)

def clean_numeric(val):
    if pd.isna(val) or val == '': return 0
    try: return float(re.sub(r'[^\d.-]', '', str(val)))
    except: return 0

def safe_str(val):
    if pd.isna(val) or str(val).lower() == 'nan': return ""
    if isinstance(val, float) and val.is_integer(): return str(int(val))
    return str(val)

def make_ul_list(items):
    html = '<ul class="ul-list">'
    for idx, item in enumerate(items):
        html += f'<li><div class="li-num">{idx+1}</div><div class="li-name">{item}</div><div class="li-icon">📄</div></li>'
    return html + '</ul>'

# --- [6. 메인 로직] ---
try:
    df = load_data()
    date_col = 'date'
    
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df['year'], df['month'] = df[date_col].dt.year.astype(int), df[date_col].dt.month.astype(int)
        for c in ['inq', 'inprice', 'outq', 'outprice', 'carprice', 'id']:
            df[f'{c}_val'] = df[c].apply(clean_numeric)
        df['in_total'], df['out_total'] = df['inq_val'] * df['inprice_val'], df['outq_val'] * df['outprice_val']
        years = sorted(df['year'].unique().tolist(), reverse=True)
        months = list(range(1, 13))

        # ---------------------------------------------------------
        # [모드 분기 1] 수정 및 삭제
        # ---------------------------------------------------------
        if st.session_state.edit_id:
            st.markdown("<h3 style='text-align:center; color:#ffeb3b; font-weight:bold;'>📝 등록 자료 수정 / 삭제</h3>", unsafe_allow_html=True)
            target = df[df['id'].astype(str) == str(st.session_state.edit_id)]
            if not target.empty:
                t = target.iloc[0]
                def_date = pd.to_datetime(t['date']).date() if pd.notnull(t['date']) else datetime.now().date()
                s_idx = 1 if '중부' in safe_str(t.get('s')) else 0
                with st.form("edit_form"):
                    c1, c2, c3, c4, c5, c6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    c1.markdown('<div class="nh-box nh-base">종류</div>', unsafe_allow_html=True)
                    c2.markdown('<div class="nh-box nh-in">매입거래처</div>', unsafe_allow_html=True)
                    c3.markdown('<div class="nh-box nh-in">매입품목</div>', unsafe_allow_html=True)
                    c4.markdown('<div class="nh-box nh-in">수량</div>', unsafe_allow_html=True)
                    c5.markdown('<div class="nh-box nh-in">단가</div>', unsafe_allow_html=True)
                    c6.markdown('<div class="nh-box nh-etc">배송</div>', unsafe_allow_html=True)
                    e_s = c1.selectbox("s", ["제일", "중부"], index=s_idx, label_visibility="collapsed")
                    e_incom = c2.text_input("incom", safe_str(t.get('incom')), label_visibility="collapsed")
                    e_initem = c3.text_input("initem", safe_str(t.get('initem')), label_visibility="collapsed")
                    e_inq = c4.text_input("inq", safe_str(t.get('inq')), label_visibility="collapsed")
                    e_inprice = c5.text_input("inprice", safe_str(t.get('inprice')), label_visibility="collapsed")
                    e_carno = c6.text_input("carno", safe_str(t.get('carno')), label_visibility="collapsed")

                    c7, c8, c9, c10, c11, c12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    c7.markdown('<div class="nh-box nh-base">날짜</div>', unsafe_allow_html=True)
                    c8.markdown('<div class="nh-box nh-out">매출거래처</div>', unsafe_allow_html=True)
                    c9.markdown('<div class="nh-box nh-out">매출품목</div>', unsafe_allow_html=True)
                    c10.markdown('<div class="nh-box nh-out">수량</div>', unsafe_allow_html=True)
                    c11.markdown('<div class="nh-box nh-out">단가</div>', unsafe_allow_html=True)
                    c12.markdown('<div class="nh-box nh-etc">운송비</div>', unsafe_allow_html=True)
                    e_date = c7.date_input("date", def_date, format="YYYY-MM-DD", label_visibility="collapsed")
                    e_outcom = c8.text_input("outcom", safe_str(t.get('outcom')), label_visibility="collapsed")
                    e_outitem = c9.text_input("outitem", safe_str(t.get('outitem')), label_visibility="collapsed")
                    e_outq = c10.text_input("outq", safe_str(t.get('outq')), label_visibility="collapsed")
                    e_outprice = c11.text_input("outprice", safe_str(t.get('outprice')), label_visibility="collapsed")
                    e_carprice = c12.text_input("carprice", safe_str(t.get('carprice')), label_visibility="collapsed")
                    
                    st.markdown("<hr>", unsafe_allow_html=True)
                    bc1, bc2, bc3, bc4 = st.columns([6, 1.5, 1.5, 1])
                    if bc2.form_submit_button("💾 수정 저장", use_container_width=True, type="primary"):
                        client = init_connection(); sheet = client.open('SQL백업260211-jeilinout').sheet1
                        cell = sheet.find(str(st.session_state.edit_id), in_column=1)
                        if cell:
                            new_row = [st.session_state.edit_id, e_date.strftime('%Y-%m-%d'), e_incom, e_initem, e_inq, e_inprice, e_outcom, e_outitem, e_outq, e_outprice, "", e_s, e_carno, e_carprice]
                            sheet.update(f"A{cell.row}:N{cell.row}", [new_row])
                            st.cache_data.clear(); st.session_state.edit_id = None; st.rerun()
                    if bc3.form_submit_button("🗑️ 이 줄 삭제", use_container_width=True, type="primary"):
                        client = init_connection(); sheet = client.open('SQL백업260211-jeilinout').sheet1
                        cell = sheet.find(str(st.session_state.edit_id), in_column=1)
                        if cell: sheet.delete_rows(cell.row)
                        st.cache_data.clear(); st.session_state.edit_id = None; st.rerun()
                    if bc4.form_submit_button("취소", use_container_width=True, type="primary"):
                        st.session_state.edit_id = None; st.rerun()

        # ---------------------------------------------------------
        # [모드 분기 2] 신규입력 및 복사
        # ---------------------------------------------------------
        elif st.session_state.search_params["mode"] == "신규입력":
            st.markdown("<h3 style='text-align:center; font-weight:bold;'>🆕 신규자료입력 / 복사입력</h3>", unsafe_allow_html=True)
            def_v = {"s_idx":0, "date":datetime.now().date()}
            if st.session_state.copy_id:
                cr = df[df['id'].astype(str) == str(st.session_state.copy_id)].iloc[0]
                def_v.update({k: safe_str(cr.get(k)) for k in ['incom','initem','inq','inprice','outcom','outitem','outq','outprice','carno','carprice']})
                def_v["s_idx"] = 1 if '중부' in safe_str(cr.get('s')) else 0
                def_v["date"] = pd.to_datetime(cr['date']).date()

            with st.form("new_form"):
                c1, c2, c3, c4, c5, c6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                for i, txt in enumerate(["종류","매입거래처","매입품목","수량","단가","배송"]):
                    c_list = [c1, c2, c3, c4, c5, c6]
                    c_list[i].markdown(f'<div class="nh-box nh-{"base" if i==0 else "in" if i<5 else "etc"}">{txt}</div>', unsafe_allow_html=True)
                n_s = c1.selectbox("s", ["제일", "중부"], index=def_v["s_idx"], label_visibility="collapsed")
                n_incom = c2.text_input("incom", def_v.get("incom",""), label_visibility="collapsed")
                n_initem = c3.text_input("initem", def_v.get("initem",""), label_visibility="collapsed")
                n_inq = c4.text_input("inq", def_v.get("inq",""), label_visibility="collapsed")
                n_inprice = c5.text_input("inprice", def_v.get("inprice",""), label_visibility="collapsed")
                n_carno = c6.text_input("carno", def_v.get("carno",""), label_visibility="collapsed")
                
                c7, c8, c9, c10, c11, c12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                for i, txt in enumerate(["날짜","매출거래처","매출품목","수량","단가","운송비"]):
                    c_list = [c7, c8, c9, c10, c11, c12]
                    c_list[i].markdown(f'<div class="nh-box nh-{"base" if i==0 else "out" if i<5 else "etc"}">{txt}</div>', unsafe_allow_html=True)
                n_date = c7.date_input("date", def_v["date"], format="YYYY-MM-DD", label_visibility="collapsed")
                n_outcom = c8.text_input("outcom", def_v.get("outcom",""), label_visibility="collapsed")
                n_outitem = c9.text_input("outitem", def_v.get("outitem",""), label_visibility="collapsed")
                n_outq = c10.text_input("outq", def_v.get("outq",""), label_visibility="collapsed")
                n_outprice = c11.text_input("outprice", def_v.get("outprice",""), label_visibility="collapsed")
                n_carprice = c12.text_input("carprice", def_v.get("carprice",""), label_visibility="collapsed")

                st.markdown("<hr>", unsafe_allow_html=True)
                bc1, bc2, bc3 = st.columns([8.2, 1.1, 0.7])
                if bc2.form_submit_button("신규자료입력", use_container_width=True, type="primary"):
                    client = init_connection(); sheet = client.open('SQL백업260211-jeilinout').sheet1
                    next_id = int(df['id_val'].max()) + 1 if not df.empty else 1
                    sheet.append_row([next_id, n_date.strftime('%Y-%m-%d'), n_incom, n_initem, n_inq, n_inprice, n_outcom, n_outitem, n_outq, n_outprice, "", n_s, n_carno, n_carprice])
                    st.cache_data.clear(); st.session_state.copy_id = None; st.session_state.search_params = {"mode":"최근","title":"최근입력순서","limit":"20개"}; st.rerun()
                if bc3.form_submit_button("취소", use_container_width=True, type="primary"):
                    st.session_state.copy_id = None; st.session_state.search_params = {"mode":"init"}; st.rerun()

        # ---------------------------------------------------------
        # [모드 분기 3] 메인 검색 및 리스트
        # ---------------------------------------------------------
        else:
            with st.container():
                st.markdown("<div class='search-panel-container'>", unsafe_allow_html=True)
                
                # 💡 [버그 완전 수정] 소수점까지 100% 정확히 표시되는 실시간 계산기
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
                        width: 100px; padding: 6px 8px; border-radius: 4px; border: 1px solid #64748b;
                        background: #dbeafe; color: #0f172a; text-align: right; font-weight: bold; outline: none; font-size: 14px;
                    }
                    .rt-in:focus { border-color: #4e8cff; box-shadow: 0 0 0 2px rgba(78,140,255,0.2); background: #ffffff; }
                    .rt-out {
                        width: 100px; padding: 6px 8px; border-radius: 4px; border: 1px solid #4a5568;
                        background: #e2e8f0; color: #1e293b; text-align: right; font-weight: bold; cursor: default; font-size: 14px;
                    }
                    .rt-out.orange { background: #ffedd5; border-color: #fdba74; color: #9a3412; }
                    .rt-txt { font-size: 13px; font-weight: bold; }
                    .rt-txt.blue { color: #60a5fa; }
                    .rt-txt.yellow { color: #fbbf24; }
                    .rt-op { font-weight: bold; font-size: 16px; }
                    .rt-op.blue { color: #60a5fa; }
                    .rt-op.yellow { color: #fbbf24; }
                    </style>
                    </head>
                    <body>
                    <div class="rt-calc-wrap">
                        <!-- 나눗셈 -->
                        <div class="rt-group">
                            <input type="text" class="rt-in" id="rt-d1" oninput="formatAndCalc(this)" placeholder="0">
                            <span class="rt-op blue">/</span>
                            <input type="text" class="rt-in" id="rt-d2" oninput="formatAndCalc(this)" placeholder="0">
                            <span class="rt-op blue">=</span>
                            <input type="text" class="rt-out" id="rt-dr" readonly placeholder="0">
                        </div>
                        <!-- 부가세 -->
                        <div class="rt-group">
                            <input type="text" class="rt-in" id="rt-v1" oninput="formatAndCalc(this)" placeholder="기준금액">
                            <span class="rt-txt blue">VAT-10%</span>
                            <input type="text" class="rt-out" id="rt-vm" readonly placeholder="0">
                            <span class="rt-txt yellow">VAT+10%</span>
                            <input type="text" class="rt-out orange" id="rt-vp" readonly placeholder="0">
                        </div>
                        <!-- 곱셈 -->
                        <div class="rt-group">
                            <input type="text" class="rt-in" id="rt-m1" oninput="formatAndCalc(this)" placeholder="0">
                            <span class="rt-op yellow">X</span>
                            <input type="text" class="rt-in" id="rt-m2" oninput="formatAndCalc(this)" placeholder="0">
                            <span class="rt-op yellow">=</span>
                            <input type="text" class="rt-out" id="rt-mr" readonly placeholder="0">
                        </div>
                    </div>
                    
                    <script>
                    function rtFmt(num) {
                        if (num === 0) return "0";
                        if (!num || isNaN(num) || !isFinite(num)) return "0";
                        // 소수점 10자리까지 절사 없이 정확하게 표현되도록 수정
                        return num.toLocaleString('ko-KR', { maximumFractionDigits: 10 });
                    }
                    
                    function rtParse(str) {
                        return parseFloat(str.replace(/,/g, '')) || 0;
                    }
                    
                    function formatAndCalc(el) {
                        // 1. 입력창 포맷팅 (소수점 입력 가능하도록 수정)
                        let rawVal = el.value.replace(/[^0-9.-]/g, '');
                        if (rawVal === '-' || rawVal === '') {
                            el.value = rawVal;
                        } else if (!isNaN(parseFloat(rawVal))) {
                            let start = el.selectionStart;
                            let len = el.value.length;
                            
                            let parts = rawVal.split('.');
                            parts[0] = parseInt(parts[0] || '0', 10).toLocaleString('ko-KR');
                            el.value = parts.join('.');
                            
                            el.setSelectionRange(start + (el.value.length - len), start + (el.value.length - len));
                        }
                        
                        // 2. 실시간 계산 (Math.round 및 Math.floor 제거하여 소수점 정확도 유지)
                        let d1 = rtParse(document.getElementById('rt-d1').value);
                        let d2 = rtParse(document.getElementById('rt-d2').value);
                        document.getElementById('rt-dr').value = d2 !== 0 ? rtFmt(d1 / d2) : "0";

                        let v1 = rtParse(document.getElementById('rt-v1').value);
                        document.getElementById('rt-vm').value = rtFmt(v1 / 1.1);
                        document.getElementById('rt-vp').value = rtFmt(v1 * 1.1);

                        let m1 = rtParse(document.getElementById('rt-m1').value);
                        let m2 = rtParse(document.getElementById('rt-m2').value);
                        document.getElementById('rt-mr').value = rtFmt(m1 * m2);
                    }
                    </script>
                    </body>
                    </html>
                    """,
                    height=75
                )

                # Row 1
                r1_1, r1_2, r1_3, r1_4, r1_5, r1_6 = st.columns([1.5, 2.5, 1, 2, 2, 2.5])
                with r1_1: t1 = st.radio("t1", ["매입", "매출", "ALL"], index=2, horizontal=True, label_visibility="collapsed")
                with r1_2: dr1 = st.date_input("dr1", [datetime(2014,1,1).date(), datetime.now().date()], format="YYYY-MM-DD", label_visibility="collapsed")
                with r1_4: c1 = st.text_input("c1", placeholder="거래처 검색", label_visibility="collapsed")
                with r1_5: i1 = st.text_input("i1", placeholder="품목 검색", label_visibility="collapsed")
                with r1_6: b1 = st.button("기간 거래처&품목", use_container_width=True, type="primary")

                st.markdown("<hr style='margin:10px 0; border:0.5px solid #4a5568;'>", unsafe_allow_html=True)
                # Row 2
                r2_1, r2_2, r2_3, r2_4, r2_5, r2_6, r2_7 = st.columns([1.5, 1.2, 1.3, 1, 2, 2, 2.5])
                with r2_1: t2 = st.radio("t2", ["매입", "매출", "ALL"], index=2, horizontal=True, label_visibility="collapsed")
                with r2_2: y2 = st.selectbox("y2", years, label_visibility="collapsed")
                with r2_3: m2 = st.selectbox("m2", months, index=datetime.now().month-1, format_func=lambda x:f"{x}월", label_visibility="collapsed")
                with r2_5: c2 = st.text_input("c2", placeholder="거래처 검색", label_visibility="collapsed")
                with r2_6: i2 = st.text_input("i2", placeholder="품목 검색", label_visibility="collapsed")
                with r2_7: b2 = st.button("월별 거래처&품목", use_container_width=True, type="primary")

                st.markdown("<hr style='margin:10px 0; border:0.5px solid #4a5568;'>", unsafe_allow_html=True)
                # Row 3
                u1, u2, u3, u4, u5, u6, u7, u8, u9, u10, u11, u12, u13, u14 = st.columns([0.8, 1.2, 1, 1, 1.2, 1, 1, 1.5, 1, 1.2, 0.8, 1.2, 1, 1.2])
                with u2: y3 = st.selectbox("y3", years, label_visibility="collapsed")
                with u3: m3 = st.selectbox("m3", months, index=datetime.now().month-1, format_func=lambda x:f"{x}월", label_visibility="collapsed")
                with u4: b_set = st.button("결산", use_container_width=True, type="primary")
                with u5: b_new = st.button("신규입력", use_container_width=True, type="primary")
                with u6: lmt = st.selectbox("l4", ["20개", "50개", "100개", "ALL"], index=0, label_visibility="collapsed")
                with u7: b_rec = st.button("최근입력", use_container_width=True, type="primary")
                with u8: d_day = st.date_input("d2", datetime.now().date(), format="YYYY-MM-DD", label_visibility="collapsed")
                with u9: b_day = st.button("일검색", use_container_width=True, type="primary")
                with u14: b_mon = st.button("월별검색", use_container_width=True, type="primary")
                st.markdown("</div>", unsafe_allow_html=True)

            if b1: st.session_state.search_params = {"mode":"기간","title":"기간검색","type":t1,"company":c1,"item":i1,"limit":"ALL","start":dr1[0],"end":dr1[1] if len(dr1)>1 else dr1[0]}
            elif b2: st.session_state.search_params = {"mode":"월별상세","title":"월별상세검색","type":t2,"year":y2,"month":m2,"company":c2,"item":i2}
            elif b_set: st.session_state.search_params = {"mode":"결산","year":y3,"month":m3}
            elif b_new: st.session_state.search_params = {"mode":"신규입력"}; st.session_state.copy_id = None; st.rerun()
            elif b_rec: st.session_state.search_params = {"mode":"최근","title":"최근입력순서","limit":lmt}
            elif b_day: st.session_state.search_params = {"mode":"일","title":f"{d_day} 검색","date":d_day}
            elif b_mon: st.session_state.search_params = {"mode":"월별","title":f"{y3}년 {m3}월 검색","year":y3,"month":m3}

            params = st.session_state.search_params
            if params["mode"] != "init":
                f_df = df.copy()
                
                # 1. 모드별 날짜 필터링
                if params["mode"] == "기간": 
                    f_df = f_df[(f_df[date_col].dt.date >= params["start"]) & (f_df[date_col].dt.date <= params["end"])]
                elif params["mode"] in ["월별상세", "월별"]: 
                    f_df = f_df[(f_df['year']==params['year'])&(f_df['month']==params['month'])]
                elif params["mode"] == "일": 
                    f_df = f_df[f_df[date_col].dt.date == params["date"]]

                # 2. 종류(매입/매출) 필터링 (누락되었던 부분 복구)
                target_type = params.get("type", "ALL")
                if target_type == "매입": f_df = f_df[f_df['incom'].astype(str).str.strip() != '']
                elif target_type == "매출": f_df = f_df[f_df['outcom'].astype(str).str.strip() != '']
                
                # 3. 검색어 필터링
                if params.get("company"): f_df = f_df[f_df['incom'].str.contains(params["company"], na=False)|f_df['outcom'].str.contains(params["company"], na=False)]
                if params.get("item"): f_df = f_df[f_df['initem'].str.contains(params["item"], na=False)|f_df['outitem'].str.contains(params["item"], na=False)]
                
                # 4. 정렬 (검색된 결과 내에서만 정렬 적용)
                f_df = f_df.sort_values(by=[date_col, 'id_val'], ascending=[not st.session_state.sort_desc, not st.session_state.sort_desc])
                
                # 5. 표시 개수 리미트
                limit_str = str(params.get("limit", "ALL"))
                if "개" in limit_str:
                    num = int(limit_str.replace("개", ""))
                    if st.session_state.sort_desc: f_df = f_df.head(num)
                    else: f_df = f_df.tail(num)

                t_in_q, t_in_a = f_df['inq_val'].sum(), f_df['in_total'].sum()
                t_out_q, t_out_a = f_df['outq_val'].sum(), f_df['out_total'].sum()
                t_car = f_df['carprice_val'].sum()
                t_profit = t_out_a - t_in_a - t_car

                col_t1, col_t2, col_t3 = st.columns([6.5, 1.8, 1.7])
                with col_t1: st.markdown(f'<div class="table-title-box"><span style="font-size:16px; font-weight:bold; color:#f8fafc;">{params.get("title","검색결과")}</span> <span style="font-size:13px; color:#cbd5e1; margin-left:10px;">| 출력 개수: {len(f_df)}</span></div>', unsafe_allow_html=True)
                with col_t2: 
                    if st.button("🔄 날짜 정렬 전환", use_container_width=True, type="primary"):
                        st.session_state.sort_desc = not st.session_state.sort_desc; st.rerun()
                with col_t3:
                    csv = f_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button("💾 엑셀 다운로드", data=csv, file_name="export.csv", mime="text/csv", use_container_width=True, type="primary")

                html = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th class="th-base">Vat</th><th class="th-base">날짜</th><th class="th-in">매입거래처</th><th class="th-in">매입품목 (MEMO)</th><th class="th-in">수량</th><th class="th-in">단가</th><th class="th-out">매출거래처</th><th class="th-out">매출품목 (MEMO)</th><th class="th-out">수량</th><th class="th-out">단가</th><th class="th-base">NO</th><th class="th-base">배송</th><th class="th-base">운송비</th></tr></thead><tbody>'
                pwd_token = str(st.secrets["tom_password"])
                for _, r in f_df.iterrows():
                    rid, dt = safe_str(r['id']), r[date_col].strftime('%Y-%m-%d')
                    s_cls = "txt-green" if "제일" in str(r['s']) else "txt-purple"
                    v_link = f'<a href="?copy_id={rid}&token={pwd_token}" target="_self" style="text-decoration:none;"><span class="{s_cls}">{r["s"]}</span></a>'
                    d_link = f'<a href="?edit_id={rid}&token={pwd_token}" target="_self" style="color:#1e293b; text-decoration:none;">{dt}</a>'
                    html += f'<tr><td class="tc">{v_link}</td><td class="tc">{d_link}</td><td class="tl txt-in-bold">{r["incom"]}</td><td class="tl txt-in">{r["initem"]}</td><td class="tr txt-in">{r["inq_val"]:,.0f}</td><td class="tr txt-in">{r["inprice_val"]:,.0f}</td><td class="tl txt-out-bold">{r["outcom"]}</td><td class="tl txt-out">{r["outitem"]}</td><td class="tr txt-out">{r["outq_val"]:,.0f}</td><td class="tr txt-out">{r["outprice_val"]:,.0f}</td><td class="tc txt-gray">{rid}</td><td class="tc txt-gray">{r["carno"]}</td><td class="tr txt-black">{r["carprice_val"]:,.0f}</td></tr>'
                html += f'</tbody><tfoot><tr><td colspan="2" class="th-base">자료수 : {len(f_df)}개</td><td colspan="4" class="th-in">매입수량 : {t_in_q:,.0f} | 매입금액 : {t_in_a:,.0f}원</td><td colspan="4" class="th-out">매출수량 : {t_out_q:,.0f} | 매출금액 : {t_out_a:,.0f}원</td><td colspan="3" class="th-base">운송비 : {t_car:,.0f}원</td></tr><tr><td colspan="13" class="sum-profit">검색내 총수익 : {t_profit:,.0f}원</td></tr></tfoot></table></div>'
                st.markdown(html, unsafe_allow_html=True)

except Exception as e: st.error(f"⚠️ 시스템 오류: {e}")
st.markdown("<br><p style='text-align:center; color:#64748b;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
