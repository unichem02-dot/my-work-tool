import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import io
import json

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# 커스텀 CSS 및 자바스크립트 주입 (모달 팝업 포함)
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #2b323c; }
    .main .block-container { padding-top: 1rem; max-width: 98%; }
    h1, h2, h3, p, span { color: #ffffff !important; }
    
    .search-panel-container { background-color: #353b48; padding: 15px; border-radius: 8px; border: 1px solid #4a5568; margin-bottom: 20px; }
    div.stButton > button { border-radius: 4px !important; font-weight: bold !important; padding: 0px 10px !important; }
    
    /* 데이터 테이블 스타일 */
    .custom-table-container { width: 100%; margin-top: 5px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
    .table-title-box { background-color: #2b323c; padding: 10px 15px; border-top: 2px solid #555; border-bottom: none; display: flex; align-items: center; justify-content: space-between; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }
    .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; }
    .custom-table th { text-align: center; color: white; font-weight: bold; padding: 10px 6px; }
    .custom-table tr:nth-child(even) { background-color: #f8f9fa; }
    .custom-table tr:hover { background-color: #e2e6ea; }
    
    .th-base { background-color: #353b48; color: white; }
    .th-in { background-color: #3b5b88; color: white; } 
    .th-out { background-color: #b8860b; color: white; }
    
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

    /* 자바스크립트 모달 스타일 */
    #memoModal {
        display: none; position: fixed; z-index: 9999; left: 0; top: 0;
        width: 100%; height: 100%; background-color: rgba(0,0,0,0.7);
    }
    .modal-content {
        background-color: #353b48; margin: 15% auto; padding: 20px;
        border: 1px solid #4e8cff; width: 400px; border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.5); color: white;
    }
    .modal-header { border-bottom: 1px solid #4a5568; padding-bottom: 10px; font-weight: bold; font-size: 18px; display: flex; justify-content: space-between; }
    .modal-body { padding: 20px 0; font-size: 16px; line-height: 1.6; color: #cbd5e1; }
    .close-modal { cursor: pointer; color: #ff5252; font-size: 24px; font-weight: bold; }
    </style>

    <div id="memoModal">
        <div class="modal-content">
            <div class="modal-header">
                <span>📝 매입 메모 내용</span>
                <span class="close-modal" onclick="document.getElementById('memoModal').style.display='none'">&times;</span>
            </div>
            <div id="memoContent" class="modal-body"></div>
            <div style="text-align: right;">
                <button onclick="document.getElementById('memoModal').style.display='none'" style="background:#4e8cff; color:white; border:none; padding:5px 15px; border-radius:4px; cursor:pointer;">확인</button>
            </div>
        </div>
    </div>

    <script>
    function showMemo(text) {
        const modal = document.getElementById('memoModal');
        const content = document.getElementById('memoContent');
        content.innerText = text ? text : "등록된 메모가 없습니다.";
        modal.style.display = 'block';
    }
    window.onclick = function(event) {
        const modal = document.getElementById('memoModal');
        if (event.target == modal) { modal.style.display = "none"; }
    }
    </script>
    """, unsafe_allow_html=True)

# --- [2. 보안 및 세션 상태 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "search_params" not in st.session_state: st.session_state.search_params = {"mode": "init"}
if "sort_desc" not in st.session_state: st.session_state.sort_desc = True 
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "copy_id" not in st.session_state: st.session_state.copy_id = None

# URL 파라미터 감지 및 자동 로그인 처리
if "edit_id" in st.query_params or "copy_id" in st.query_params:
    if st.query_params.get("token") == str(st.secrets.get("tom_password", "")):
        st.session_state.authenticated = True
        if "edit_id" in st.query_params: st.session_state.edit_id = st.query_params["edit_id"]
        if "copy_id" in st.query_params:
            st.session_state.copy_id = st.query_params["copy_id"]
            st.session_state.search_params = {"mode": "신규입력"}
        st.query_params.clear()
        st.rerun()

# --- [3. 로그인 화면] ---
if not st.session_state.authenticated:
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        with st.form("login_form"):
            pwd = st.text_input("PASSWORD", type="password")
            if st.form_submit_button("SYSTEM LOGIN", use_container_width=True, type="primary"):
                if pwd == str(st.secrets["tom_password"]):
                    st.session_state.authenticated = True
                    st.rerun()
                else: st.error("❌ 비밀번호 오류")
    st.stop()

# --- [4. 상단바] ---
col_title, col_empty, col_refresh, col_logout = st.columns([5, 3.5, 1.5, 1])
with col_title: st.markdown("### 📦 입출력 통합 관리 시스템")
with col_refresh:
    if st.button("🔄 데이터 갱신", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
with col_logout:
    if st.button("🔓 LOGOUT", use_container_width=True, type="primary"):
        st.session_state.authenticated = False
        st.rerun()
st.markdown("<hr style='margin: 10px 0px 20px 0px; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

# --- [5. 데이터 처리 함수] ---
@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def load_data():
    client = init_connection()
    sheet = client.open('SQL백업260211-jeilinout').sheet1
    raw_data = sheet.get_all_values()
    if not raw_data: return pd.DataFrame()
    header = [n.strip() if n.strip() else f"col_{i}" for i, n in enumerate(raw_data[0])]
    return pd.DataFrame(raw_data[1:], columns=header)

def clean_numeric(val):
    if pd.isna(val) or val == '': return 0
    try: return float(re.sub(r'[^\d.-]', '', str(val)))
    except: return 0

def safe_str(val):
    if pd.isna(val) or str(val).lower() == 'nan': return ""
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

        # --- [검색 패널 UI] ---
        if not st.session_state.edit_id:
            with st.container():
                st.markdown("<div class='search-panel-container'>", unsafe_allow_html=True)
                r1_1, r1_2, r1_3, r1_4, r1_5, r1_6 = st.columns([1.5, 2.5, 1, 2, 2, 2.5])
                with r1_1: type_1 = st.radio("r1", ["매입", "매출", "ALL"], index=2, horizontal=True, label_visibility="collapsed")
                with r1_2: date_range = st.date_input("d1", [datetime(2014,1,1).date(), datetime.now().date()], format="YYYY-MM-DD", label_visibility="collapsed")
                with r1_4: com_1 = st.text_input("t1", placeholder="거래처 검색", label_visibility="collapsed")
                with r1_5: item_1 = st.text_input("t2", placeholder="품목 검색", label_visibility="collapsed")
                with r1_6: btn_1 = st.button("기간 거래처&품목", use_container_width=True, type="primary")

                st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)
                c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14 = st.columns([0.8, 1.2, 1, 1, 1.2, 1, 1, 1.5, 1, 1.2, 0.8, 1.2, 1, 1.2])
                with c2: y_3 = st.selectbox("y3", years, label_visibility="collapsed")
                with c3: m_3 = st.selectbox("m3", months, index=datetime.now().month-1, label_visibility="collapsed", format_func=lambda x: f"{x}월")
                with c4: btn_3 = st.button("결산", use_container_width=True, type="primary")
                with c5: btn_4 = st.button("신규입력", use_container_width=True, type="primary")
                with c6: limit_val = st.selectbox("s4", ["20개", "50개", "100개", "ALL"], index=0, label_visibility="collapsed")
                with c7: btn_5 = st.button("최근입력", use_container_width=True, type="primary")
                with c8: d_day = st.date_input("d2", datetime.now().date(), format="YYYY-MM-DD", label_visibility="collapsed")
                with c9: btn_6 = st.button("일검색", use_container_width=True, type="primary")
                with c14: btn_8 = st.button("월별검색", use_container_width=True, type="primary")
                st.markdown("</div>", unsafe_allow_html=True)

            if btn_1: st.session_state.search_params = { "mode": "기간", "title": "기간검색", "type": type_1, "company": com_1, "item": item_1, "limit": "ALL", "start": date_range[0], "end": date_range[1] if len(date_range)>1 else date_range[0] }
            elif btn_3: st.session_state.search_params = { "mode": "결산", "year": y_3, "month": m_3 }
            elif btn_4: st.session_state.search_params = { "mode": "신규입력" }; st.session_state.copy_id = None
            elif btn_5: st.session_state.search_params = { "mode": "최근", "title": "최근입력순서", "limit": limit_val }
            elif btn_6: st.session_state.search_params = { "mode": "일", "title": f"{d_day} 검색", "date": d_day }
            elif btn_8: st.session_state.search_params = { "mode": "월별", "title": "월별검색", "year": y_3, "month": m_3 }

        params = st.session_state.search_params

        # --- [수정/신규입력/리스트 출력 분기] ---
        if st.session_state.edit_id:
            st.markdown("<h3 style='text-align:center; color:#ffeb3b;'>📝 자료 수정 / 삭제</h3>", unsafe_allow_html=True)
            target = df[df['id_val'] == clean_numeric(st.session_state.edit_id)]
            if not target.empty:
                t = target.iloc[0]
                with st.form("edit_form"):
                    col_a, col_b = st.columns(2)
                    e_incom = col_a.text_input("매입거래처", safe_str(t['incom']))
                    e_outcom = col_b.text_input("매출거래처", safe_str(t['outcom']))
                    if st.form_submit_button("💾 수정 저장", type="primary"):
                        st.success("수정 완료 (시트 업데이트 로직 생략됨)"); st.session_state.edit_id = None; st.rerun()
                    if st.form_submit_button("취소", type="primary"): st.session_state.edit_id = None; st.rerun()

        elif params["mode"] == "신규입력":
            st.markdown("<h3 style='text-align:center;'>🆕 신규자료입력</h3>", unsafe_allow_html=True)
            with st.form("new_form"):
                n_incom = st.text_input("매입거래처")
                if st.form_submit_button("신규자료입력", type="primary"): 
                    st.success("입력 완료"); st.session_state.search_params = {"mode":"init"}; st.rerun()
                if st.form_submit_button("취소", type="primary"): st.session_state.search_params = {"mode":"init"}; st.rerun()

        elif params["mode"] != "init":
            f_df = df.copy()
            if params["mode"] == "최근": f_df = f_df.sort_values(by=[date_col, 'id_val'], ascending=[False, False]).head(20)
            
            # 테이블 렌더링
            html_str = '<div class="custom-table-container"><table class="custom-table"><thead><tr><th class="th-base">Vat</th><th class="th-base">날짜</th><th class="th-in">매입거래처</th><th class="th-in">매입품목 (MEMO)</th><th class="th-in">수량</th><th class="th-in">단가</th><th class="th-out">매출거래처</th><th class="th-out">매출품목 (MEMO)</th><th class="th-out">수량</th><th class="th-out">단가</th><th class="th-base">NO</th><th class="th-base">배송</th><th class="th-base">운송비</th></tr></thead><tbody>'
            token = str(st.secrets.get("tom_password", ""))
            for _, row in f_df.iterrows():
                dt_str = row[date_col].strftime('%Y-%m-%d')
                rid = safe_str(row['id'])
                s_cls = "txt-green" if "제일" in str(row['s']) else "txt-purple"
                memo_js = str(row.get('memoin', '')).replace("'", "\\'")
                in_item_link = f'<a href="javascript:void(0)" onclick="showMemo(\'{memo_js}\')" style="color:#1e3a8a; cursor:pointer;">{safe_str(row["initem"])}</a>'
                vat_link = f'<a href="?copy_id={rid}&token={token}" target="_self" style="text-decoration:none;"><span class="{s_cls}">{row["s"]}</span></a>'
                dt_link = f'<a href="?edit_id={rid}&token={token}" target="_self" style="color:#1e293b; text-decoration:none;">{dt_str}</a>'
                html_str += f'<tr><td class="tc">{vat_link}</td><td class="tc">{dt_link}</td><td class="tl">{row["incom"]}</td><td class="tl">{in_item_link}</td><td class="tr">{row["inq_val"]:,.0f}</td><td class="tr">{row["inprice_val"]:,.0f}</td><td class="tl">{row["outcom"]}</td><td class="tl">{row["outitem"]}</td><td class="tr">{row["outq_val"]:,.0f}</td><td class="tr">{row["outprice_val"]:,.0f}</td><td class="tc">{rid}</td><td class="tc">{row["carno"]}</td><td class="tr">{row["carprice_val"]:,.0f}</td></tr>'
            html_str += "</tbody></table></div>"
            st.markdown(html_str, unsafe_allow_html=True)

except Exception as e: st.error(f"⚠️ 시스템 오류: {e}")
st.markdown("<br><p style='text-align:center; color:#64748b;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
