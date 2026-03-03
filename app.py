import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import io

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# 커스텀 CSS 주입
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #2b323c; }
    .main .block-container { padding-top: 1rem; max-width: 98%; }
    h1, h2, h3, p, span { color: #ffffff !important; }
    
    .search-panel-container { background-color: #353b48; padding: 15px; border-radius: 8px; border: 1px solid #4a5568; margin-bottom: 20px; }
    div.stButton > button { border-radius: 4px !important; font-weight: bold !important; padding: 0px 10px !important; }
    div.btn-green > div > button { background-color: #8bc34a !important; color: white !important; border: 1px solid #7cb342 !important; }
    div.btn-pink > div > button { background-color: #e57373 !important; color: white !important; border: 1px solid #e53935 !important; }

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

# --- [2. 보안 및 세션/검색 상태 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "failed_attempts" not in st.session_state: st.session_state.failed_attempts = 0
if "lockout_until" not in st.session_state: st.session_state.lockout_until = None
if "last_activity" not in st.session_state: st.session_state.last_activity = None
if "search_params" not in st.session_state: st.session_state.search_params = {"mode": "init"}
if "sort_desc" not in st.session_state: st.session_state.sort_desc = True 
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "copy_id" not in st.session_state: st.session_state.copy_id = None

# 💡 URL 파라미터 감지 및 자동 로그인 처리 (복사기능 & 수정기능 둘 다 지원)
if "edit_id" in st.query_params or "copy_id" in st.query_params:
    if st.query_params.get("token") == str(st.secrets.get("tom_password", "")):
        st.session_state.authenticated = True
        st.session_state.last_activity = datetime.now()
        
    if "edit_id" in st.query_params:
        st.session_state.edit_id = st.query_params["edit_id"]
    if "copy_id" in st.query_params:
        st.session_state.copy_id = st.query_params["copy_id"]
        st.session_state.search_params = {"mode": "신규입력"}
        
    st.query_params.clear()
    st.rerun()

now = datetime.now()

if st.session_state.lockout_until:
    if now < st.session_state.lockout_until:
        lock_minutes = (st.session_state.lockout_until - now).seconds // 60
        st.error(f"🔒 해킹 방지: 비밀번호 5회 오류로 시스템이 잠겼습니다. {lock_minutes}분 후 다시 시도해주세요.")
        st.stop()
    else:
        st.session_state.lockout_until = None
        st.session_state.failed_attempts = 0

if st.session_state.authenticated and st.session_state.last_activity:
    if now - st.session_state.last_activity > timedelta(minutes=30):
        st.session_state.authenticated = False
        st.warning("⏱️ 안전을 위해 장시간(30분) 미사용으로 자동 로그아웃 되었습니다.")

# --- [3. 로그인 화면] ---
if not st.session_state.authenticated:
    st.markdown("<h1 style='text-align: center; color: #4e8cff !important;'>🛡️ ADMIN ACCESS</h1>", unsafe_allow_html=True)
    col_l, col_c, col_r = st.columns([1, 1.2, 1])
    with col_c:
        with st.form("login_form"):
            pwd = st.text_input("PASSWORD", type="password", placeholder="••••")
            submit_btn = st.form_submit_button("SYSTEM LOGIN", use_container_width=True, type="primary")
            if submit_btn:
                if "tom_password" not in st.secrets:
                    st.error("⚠️ Streamlit Secrets 설정 오류")
                elif pwd == str(st.secrets["tom_password"]):
                    st.session_state.authenticated = True
                    st.session_state.failed_attempts = 0
                    st.session_state.last_activity = datetime.now()
                    st.rerun()
                else:
                    st.session_state.failed_attempts += 1
                    remains = 5 - st.session_state.failed_attempts
                    if remains <= 0:
                        st.session_state.lockout_until = datetime.now() + timedelta(minutes=10)
                        st.rerun()
                    else:
                        st.error(f"❌ 비밀번호 오류 (남은 기회: {remains}번)")
    st.stop()

# --- [4. 상단 상태바] ---
st.session_state.last_activity = datetime.now()
col_title, col_empty, col_refresh, col_logout = st.columns([5, 3.5, 1.5, 1])
with col_title:
    st.markdown("<h3 style='margin-bottom:0px; padding-bottom:0px;'>📦 입출력 통합 관리 시스템</h3>", unsafe_allow_html=True)
with col_refresh:
    if st.button("🔄 데이터 갱신", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()
with col_logout:
    if st.button("🔓 LOGOUT", use_container_width=True, type="primary"):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("<hr style='margin: 10px 0px 20px 0px; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

# --- [5. 데이터 로드] ---
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
    header = raw_data[0]
    new_header = []
    for i, name in enumerate(header):
        n = name.strip()
        if not n: new_header.append(f"col_{i}")
        elif n in new_header: new_header.append(f"{n}_{i}")
        else: new_header.append(n)
    return pd.DataFrame(raw_data[1:], columns=new_header)

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
    html += '</ul>'
    return html

# --- [6. 메인 화면 구성 및 복합 검색 UI] ---
try:
    df = load_data()
    date_col = 'date'
    
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df['year'] = df[date_col].dt.year.astype(int)
        df['month'] = df[date_col].dt.month.astype(int)
        
        df['inq_val'] = df['inq'].apply(clean_numeric)
        df['inprice_val'] = df['inprice'].apply(clean_numeric)
        df['outq_val'] = df['outq'].apply(clean_numeric)
        df['outprice_val'] = df['outprice'].apply(clean_numeric)
        df['carprice_val'] = df['carprice'].apply(clean_numeric)
        
        df['in_total'] = df['inq_val'] * df['inprice_val']
        df['out_total'] = df['outq_val'] * df['outprice_val']

        years = sorted(df['year'].unique().tolist(), reverse=True)
        months = list(range(1, 13))
        if not years: years = [datetime.now().year]

        # ---------------------------------------------------------
        # [수정 화면 분기] 편집 모드일 경우
        # ---------------------------------------------------------
        if st.session_state.edit_id:
            st.markdown("<h3 style='text-align:center; color:#ffeb3b; margin-top:10px; font-weight:bold;'>📝 등록 자료 수정 / 삭제</h3>", unsafe_allow_html=True)
            
            target_row = df[df['id'].astype(str) == str(st.session_state.edit_id)]
            
            if not target_row.empty:
                t_data = target_row.iloc[0]
                def_s = safe_str(t_data.get('s', '제일'))
                s_idx = 1 if '중부' in def_s else 0
                def_date = pd.to_datetime(t_data['date']).date() if pd.notnull(t_data['date']) else datetime.now().date()
                
                with st.form("edit_entry_form", clear_on_submit=False):
                    st.markdown("""
                    <style>
                    .nh-box { padding: 10px 8px; text-align: center; color: white; font-weight: bold; border: 1px solid #555; margin-bottom: 5px; font-size: 14px;}
                    .nh-base { background-color: #353b48; } .nh-in { background-color: #3b5b88; } .nh-out { background-color: #b8860b; } .nh-etc { background-color: #757c43; }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    fc1.markdown('<div class="nh-box nh-base">종류</div>', unsafe_allow_html=True)
                    fc2.markdown('<div class="nh-box nh-in">매입거래처</div>', unsafe_allow_html=True)
                    fc3.markdown('<div class="nh-box nh-in">매입품목 (MEMO)</div>', unsafe_allow_html=True)
                    fc4.markdown('<div class="nh-box nh-in">수량</div>', unsafe_allow_html=True)
                    fc5.markdown('<div class="nh-box nh-in">단가</div>', unsafe_allow_html=True)
                    fc6.markdown('<div class="nh-box nh-etc">배송</div>', unsafe_allow_html=True)
                    
                    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    edit_s = ic1.selectbox("종류", ["제일", "중부"], index=s_idx, label_visibility="collapsed")
                    edit_incom = ic2.text_input("매입거래처", safe_str(t_data.get('incom')), label_visibility="collapsed")
                    edit_initem = ic3.text_input("매입품목", safe_str(t_data.get('initem')), label_visibility="collapsed")
                    edit_inq = ic4.text_input("매입수량", safe_str(t_data.get('inq')), label_visibility="collapsed")
                    edit_inprice = ic5.text_input("매입단가", safe_str(t_data.get('inprice')), label_visibility="collapsed")
                    edit_carno = ic6.text_input("배송", safe_str(t_data.get('carno')), label_visibility="collapsed")
                    
                    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                    
                    fc7, fc8, fc9, fc10, fc11, fc12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    fc7.markdown('<div class="nh-box nh-base">날짜</div>', unsafe_allow_html=True)
                    fc8.markdown('<div class="nh-box nh-out">매출거래처</div>', unsafe_allow_html=True)
                    fc9.markdown('<div class="nh-box nh-out">매출품목 (MEMO)</div>', unsafe_allow_html=True)
                    fc10.markdown('<div class="nh-box nh-out">수량</div>', unsafe_allow_html=True)
                    fc11.markdown('<div class="nh-box nh-out">단가</div>', unsafe_allow_html=True)
                    fc12.markdown('<div class="nh-box nh-etc">운송비</div>', unsafe_allow_html=True)
                    
                    ic7, ic8, ic9, ic10, ic11, ic12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    edit_date = ic7.date_input("날짜", def_date, format="YYYY-MM-DD", label_visibility="collapsed")
                    edit_outcom = ic8.text_input("매출거래처", safe_str(t_data.get('outcom')), label_visibility="collapsed")
                    edit_outitem = ic9.text_input("매출품목", safe_str(t_data.get('outitem')), label_visibility="collapsed")
                    edit_outq = ic10.text_input("매출수량", safe_str(t_data.get('outq')), label_visibility="collapsed")
                    edit_outprice = ic11.text_input("매출단가", safe_str(t_data.get('outprice')), label_visibility="collapsed")
                    edit_carprice = ic12.text_input("운송비", safe_str(t_data.get('carprice')), label_visibility="collapsed")
                    
                    st.markdown("<hr style='margin: 15px 0; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)
                    
                    bc1, bc2, bc3, bc4 = st.columns([6, 1.5, 1.5, 1])
                    btn_update = bc2.form_submit_button("💾 수정 저장", use_container_width=True, type="primary")
                    btn_delete = bc3.form_submit_button("🗑️ 이 줄 삭제", use_container_width=True, type="primary")
                    btn_cancel = bc4.form_submit_button("취소", use_container_width=True, type="primary")
                    
                    if btn_update:
                        try:
                            client = init_connection()
                            sheet = client.open('SQL백업260211-jeilinout').sheet1
                            cell = sheet.find(str(st.session_state.edit_id), in_column=1)
                            if cell:
                                dt_str = edit_date.strftime('%Y-%m-%d')
                                new_row = [st.session_state.edit_id, dt_str, edit_incom, edit_initem, edit_inq, edit_inprice, edit_outcom, edit_outitem, edit_outq, edit_outprice, "", edit_s, edit_carno, edit_carprice, "", "", ""]
                                try:
                                    sheet.update(values=[new_row], range_name=f"A{cell.row}:Q{cell.row}")
                                except TypeError:
                                    sheet.update(f"A{cell.row}:Q{cell.row}", [new_row])
                                
                                st.cache_data.clear()
                                st.session_state.edit_id = None
                                st.success("✅ 자료가 성공적으로 수정되었습니다!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ 저장 중 시스템 오류가 발생했습니다: {e}")
                            
                    elif btn_delete:
                        try:
                            client = init_connection()
                            sheet = client.open('SQL백업260211-jeilinout').sheet1
                            cell = sheet.find(str(st.session_state.edit_id), in_column=1)
                            if cell:
                                sheet.delete_rows(cell.row)
                                st.cache_data.clear()
                                st.session_state.edit_id = None
                                st.success("✅ 해당 자료가 완전히 삭제되었습니다!")
                                st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ 삭제 중 오류가 발생했습니다: {e}")

                    elif btn_cancel:
                        st.session_state.edit_id = None
                        st.rerun()
            else:
                st.error("데이터를 찾을 수 없습니다. 이미 삭제되었을 수 있습니다.")
                if st.button("돌아가기"):
                    st.session_state.edit_id = None
                    st.rerun()
                    
        # ---------------------------------------------------------
        # (기본) 검색 UI 및 표 렌더링 블록 (수정 모드가 아닐 때만 노출)
        # ---------------------------------------------------------
        else:
            with st.container():
                st.markdown("<div class='search-panel-container'>", unsafe_allow_html=True)
                
                r1_1, r1_2, r1_3, r1_4, r1_5, r1_6 = st.columns([1.5, 2.5, 1, 2, 2, 2.5])
                with r1_1: type_1 = st.radio("r1", ["매입", "매출", "ALL"], index=2, horizontal=True, label_visibility="collapsed")
                with r1_2: date_range = st.date_input("d1", [datetime(2014,1,1).date(), datetime.now().date()], format="YYYY-MM-DD", label_visibility="collapsed")
                with r1_3: st.selectbox("s1", ["ALL"], label_visibility="collapsed")
                with r1_4: com_1 = st.text_input("t1", placeholder="거래처 검색", label_visibility="collapsed")
                with r1_5: item_1 = st.text_input("t2", placeholder="품목 검색", label_visibility="collapsed")
                with r1_6: btn_1 = st.button("기간 거래처&품목", use_container_width=True, type="primary")

                st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

                r2_1, r2_2, r2_3, r2_4, r2_5, r2_6, r2_7 = st.columns([1.5, 1.2, 1.3, 1, 2, 2, 2.5])
                with r2_1: type_2 = st.radio("r2", ["매입", "매출", "ALL"], index=2, horizontal=True, label_visibility="collapsed")
                with r2_2: year_2 = st.selectbox("y2", years, label_visibility="collapsed")
                with r2_3: month_2 = st.selectbox("m2", months, index=datetime.now().month-1, label_visibility="collapsed", format_func=lambda x: f"{x}월")
                with r2_4: st.selectbox("s2", ["ALL"], label_visibility="collapsed")
                with r2_5: com_2 = st.text_input("t3", placeholder="거래처 검색", label_visibility="collapsed")
                with r2_6: item_2 = st.text_input("t4", placeholder="품목 검색", label_visibility="collapsed")
                with r2_7: btn_2 = st.button("월별 거래처&품목", use_container_width=True, type="primary")

                st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

                c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14 = st.columns([0.8, 1.2, 1, 1, 1.2, 1, 1, 1.5, 1, 1.2, 0.8, 1.2, 1, 1.2])
                with c1: st.selectbox("s3", ["ALL"], label_visibility="collapsed")
                with c2: y_3 = st.selectbox("y3", years, label_visibility="collapsed")
                with c3: m_3 = st.selectbox("m3", months, index=datetime.now().month-1, label_visibility="collapsed", format_func=lambda x: f"{x}월")
                with c4: btn_3 = st.button("결산", use_container_width=True, type="primary")
                with c5: btn_4 = st.button("신규입력", use_container_width=True, type="primary")
                with c6: limit_val = st.selectbox("s4", ["20개", "50개", "100개", "ALL"], index=0, label_visibility="collapsed")
                with c7: btn_5 = st.button("최근입력", use_container_width=True, type="primary")
                with c8: d_day = st.date_input("d2", datetime.now().date(), format="YYYY-MM-DD", label_visibility="collapsed")
                with c9: btn_6 = st.button("일검색", use_container_width=True, type="primary")
                with c10: btn_7 = st.button("어제오늘내일", use_container_width=True, type="primary")
                with c11: st.selectbox("s5", ["ALL"], label_visibility="collapsed")
                with c12: y_4 = st.selectbox("y4", years, label_visibility="collapsed")
                with c13: m_4 = st.selectbox("m4", months, index=datetime.now().month-1, label_visibility="collapsed", format_func=lambda x: f"{x}월")
                with c14: btn_8 = st.button("월별검색", use_container_width=True, type="primary")
                
                st.markdown("</div>", unsafe_allow_html=True)

            if btn_1: st.session_state.search_params = { "mode": "기간", "title": "기간검색순서", "type": type_1, "company": com_1, "item": item_1, "limit": "ALL", "start": date_range[0], "end": date_range[1] if len(date_range)>1 else date_range[0] }
            elif btn_2: st.session_state.search_params = { "mode": "월별", "title": f"{year_2}년 {month_2}월 검색순서", "type": type_2, "company": com_2, "item": item_2, "limit": "ALL", "year": year_2, "month": month_2 }
            elif btn_3: st.session_state.search_params = { "mode": "결산", "year": y_3, "month": m_3 }
            elif btn_4: 
                st.session_state.search_params = { "mode": "신규입력" }
                st.session_state.copy_id = None
            elif btn_5: st.session_state.search_params = { "mode": "최근", "title": "최근입력순서", "type": "ALL", "company": "", "item": "", "limit": limit_val }
            elif btn_6: st.session_state.search_params = { "mode": "일", "title": f"{d_day} 검색순서", "date": d_day, "type": "ALL", "company": "", "item": "", "limit": "ALL" }
            elif btn_7: st.session_state.search_params = { "mode": "기간", "title": "어제/오늘/내일 검색순서", "type": "ALL", "company": "", "item": "", "limit": "ALL", "start": datetime.now().date() - timedelta(days=1), "end": datetime.now().date() + timedelta(days=1) }
            elif btn_8: st.session_state.search_params = { "mode": "월별단순", "title": "월별검색순서", "year": y_4, "month": m_4, "type": "ALL", "company": "", "item": "", "limit": "ALL" }
            
            params = st.session_state.search_params
            
            # --- 신규입력 화면 렌더링 (복사 데이터 채우기 포함) ---
            if params["mode"] == "신규입력":
                st.markdown("<h3 style='text-align:center; color:white; margin-top:20px; font-weight:bold;'>신규자료입력 | New</h3>", unsafe_allow_html=True)
                
                def_s_idx, def_incom, def_initem, def_inq, def_inprice, def_carno = 0, "", "", "", "", ""
                def_outcom, def_outitem, def_outq, def_outprice, def_carprice = "", "", "", "", ""
                def_date = datetime.now().date()
                
                if st.session_state.copy_id:
                    st.info("💡 선택하신 자료가 복사되었습니다. 내용을 수정하여 새롭게 저장하세요.")
                    copy_row = df[df['id'].astype(str) == str(st.session_state.copy_id)]
                    if not copy_row.empty:
                        t_data = copy_row.iloc[0]
                        def_s_idx = 1 if '중부' in safe_str(t_data.get('s')) else 0
                        def_incom = safe_str(t_data.get('incom'))
                        def_initem = safe_str(t_data.get('initem'))
                        def_inq = safe_str(t_data.get('inq'))
                        def_inprice = safe_str(t_data.get('inprice'))
                        def_carno = safe_str(t_data.get('carno'))
                        def_outcom = safe_str(t_data.get('outcom'))
                        def_outitem = safe_str(t_data.get('outitem'))
                        def_outq = safe_str(t_data.get('outq'))
                        def_outprice = safe_str(t_data.get('outprice'))
                        def_carprice = safe_str(t_data.get('carprice'))
                        if pd.notnull(t_data['date']): def_date = pd.to_datetime(t_data['date']).date()
                
                with st.form("new_entry_form", clear_on_submit=True):
                    st.markdown("""
                    <style>
                    .nh-box { padding: 10px 8px; text-align: center; color: white; font-weight: bold; border: 1px solid #555; margin-bottom: 5px; font-size: 14px;}
                    .nh-base { background-color: #353b48; } .nh-in { background-color: #3b5b88; } .nh-out { background-color: #b8860b; } .nh-etc { background-color: #757c43; }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    fc1.markdown('<div class="nh-box nh-base">종류</div>', unsafe_allow_html=True)
                    fc2.markdown('<div class="nh-box nh-in">매입거래처</div>', unsafe_allow_html=True)
                    fc3.markdown('<div class="nh-box nh-in">매입품목 (MEMO)</div>', unsafe_allow_html=True)
                    fc4.markdown('<div class="nh-box nh-in">수량</div>', unsafe_allow_html=True)
                    fc5.markdown('<div class="nh-box nh-in">단가</div>', unsafe_allow_html=True)
                    fc6.markdown('<div class="nh-box nh-etc">배송</div>', unsafe_allow_html=True)
                    
                    ic1, ic2, ic3, ic4, ic5, ic6 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    new_s = ic1.selectbox("종류", ["제일", "중부"], index=def_s_idx, label_visibility="collapsed")
                    new_incom = ic2.text_input("매입거래처", value=def_incom, label_visibility="collapsed")
                    new_initem = ic3.text_input("매입품목", value=def_initem, label_visibility="collapsed")
                    new_inq = ic4.text_input("매입수량", value=def_inq, label_visibility="collapsed")
                    new_inprice = ic5.text_input("매입단가", value=def_inprice, label_visibility="collapsed")
                    new_carno = ic6.text_input("배송", value=def_carno, label_visibility="collapsed")
                    
                    st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
                    
                    fc7, fc8, fc9, fc10, fc11, fc12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    fc7.markdown('<div class="nh-box nh-base">날짜</div>', unsafe_allow_html=True)
                    fc8.markdown('<div class="nh-box nh-out">매출거래처</div>', unsafe_allow_html=True)
                    fc9.markdown('<div class="nh-box nh-out">매출품목 (MEMO)</div>', unsafe_allow_html=True)
                    fc10.markdown('<div class="nh-box nh-out">수량</div>', unsafe_allow_html=True)
                    fc11.markdown('<div class="nh-box nh-out">단가</div>', unsafe_allow_html=True)
                    fc12.markdown('<div class="nh-box nh-etc">운송비</div>', unsafe_allow_html=True)
                    
                    ic7, ic8, ic9, ic10, ic11, ic12 = st.columns([1, 2.5, 3, 1.2, 1.2, 1.2])
                    new_date = ic7.date_input("날짜", def_date, format="YYYY-MM-DD", label_visibility="collapsed")
                    new_outcom = ic8.text_input("매출거래처", value=def_outcom, label_visibility="collapsed")
                    new_outitem = ic9.text_input("매출품목", value=def_outitem, label_visibility="collapsed")
                    new_outq = ic10.text_input("매출수량", value=def_outq, label_visibility="collapsed")
                    new_outprice = ic11.text_input("매출단가", value=def_outprice, label_visibility="collapsed")
                    new_carprice = ic12.text_input("운송비", value=def_carprice, label_visibility="collapsed")
                    
                    st.markdown("<hr style='margin: 15px 0; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)
                    
                    bc1, bc2, bc3 = st.columns([8.2, 1.1, 0.7])
                    submitted = bc2.form_submit_button("신규자료입력", use_container_width=True, type="primary")
                    canceled = bc3.form_submit_button("취소", use_container_width=True, type="primary")
                    
                    if submitted:
                        try:
                            client = init_connection()
                            sheet = client.open('SQL백업260211-jeilinout').sheet1
                            
                            all_ids = df['id'].dropna().apply(clean_numeric).tolist()
                            next_id = int(max(all_ids)) + 1 if all_ids else 1
                            dt_str = new_date.strftime('%Y-%m-%d')
                            
                            new_row = [next_id, dt_str, new_incom, new_initem, new_inq, new_inprice, new_outcom, new_outitem, new_outq, new_outprice, "", new_s, new_carno, new_carprice, "", "", ""]
                            sheet.append_row(new_row)
                            
                            st.cache_data.clear()
                            st.session_state.copy_id = None
                            st.success("✅ 신규 자료가 구글 시트에 완벽하게 저장되었습니다!")
                            st.session_state.search_params = {"mode": "최근", "title": "최근입력순서", "type": "ALL", "company": "", "item": "", "limit": "20개"}
                            st.rerun()
                        except Exception as e:
                            st.error(f"⚠️ 저장 중 시스템 오류가 발생했습니다: {e}")
                            
                    if canceled:
                        st.session_state.copy_id = None
                        st.session_state.search_params = {"mode": "init"}
                        st.rerun()

            # --- 결산 화면 렌더링 ---
            elif params["mode"] == "결산":
                s_year = params["year"]
                s_month = params["month"]
                f_df = df[(df['year'] == s_year) & (df['month'] == s_month)].copy()
                
                incom_list = sorted([str(x) for x in f_df['incom'].unique() if str(x).strip() != ''])
                initem_list = sorted([str(x) for x in f_df['initem'].unique() if str(x).strip() != ''])
                outcom_list = sorted([str(x) for x in f_df['outcom'].unique() if str(x).strip() != ''])
                outitem_list = sorted([str(x) for x in f_df['outitem'].unique() if str(x).strip() != ''])
                carno_list = sorted([str(x) for x in f_df['carno'].unique() if str(x).strip() != ''])
                
                in_q = f_df['inq_val'].sum()
                in_amt = f_df['in_total'].sum()
                in_tax = in_amt * 0.1
                in_amt_total = in_amt + in_tax
                out_q = f_df['outq_val'].sum()
                out_amt = f_df['out_total'].sum()
                out_tax = out_amt * 0.1
                out_amt_total = out_amt + out_tax
                car_amt = f_df['carprice_val'].sum()
                profit = out_amt - in_amt
                
                settle_html = f'<div class="settle-header-top"><div style="font-size: 16px;">▶ {s_year}년 {s_month:02d}월 전체리스트 / 결산 종류: ALL</div><div style="font-size: 26px;">{s_year}년 {s_month:02d}월</div></div>'
                settle_html += f'<div class="settle-container"><div class="settle-lists"><div class="settle-col"><div class="sh-title sh-1">매입거래처</div>{make_ul_list(incom_list)}</div><div class="settle-col"><div class="sh-title sh-2">매입품목</div>{make_ul_list(initem_list)}</div><div class="settle-col"><div class="sh-title sh-3">매출거래처</div>{make_ul_list(outcom_list)}</div><div class="settle-col"><div class="sh-title sh-4">매출품목</div>{make_ul_list(outitem_list)}</div><div class="settle-col"><div class="sh-title sh-5">차량NO</div>{make_ul_list(carno_list)}</div></div>'
                settle_html += f'<div class="settle-summary"><div class="sum-subhead">[ALL] 총결산 내역</div><table class="sum-table"><tr><td class="bg-blue">매입수량</td><td class="bg-blue tr-right">{in_q:,.0f}</td></tr><tr><td class="bg-blue">매입액</td><td class="bg-blue tr-right">\{in_amt:,.0f}</td></tr><tr><td class="bg-blue">매입세액</td><td class="bg-blue tr-right">\{in_tax:,.0f}</td></tr><tr><td class="bg-blue" style="border-bottom: 2px solid white;">매입금액(세액포함)</td><td class="bg-blue tr-right" style="border-bottom: 2px solid white;">\{in_amt_total:,.0f}</td></tr><tr><td class="bg-orange">매출수량</td><td class="bg-orange tr-right">{out_q:,.0f}</td></tr><tr><td class="bg-orange">매출액</td><td class="bg-orange tr-right">\{out_amt:,.0f}</td></tr><tr><td class="bg-orange">매출세액</td><td class="bg-orange tr-right">\{out_tax:,.0f}</td></tr><tr><td class="bg-orange" style="border-bottom: 2px solid white;">매출금액(세액포함)</td><td class="bg-orange tr-right" style="border-bottom: 2px solid white;">\{out_amt_total:,.0f}</td></tr><tr><td class="bg-olive" style="border-bottom: 2px solid white;">운송비</td><td class="bg-olive tr-right" style="border-bottom: 2px solid white;">\{car_amt:,.0f}</td></tr><tr><td class="bg-dark">총이익 <span style="font-size:11px">(운송비미포함)</span></td><td class="bg-dark tr-right">\{profit:,.0f}</td></tr></table><div class="alert-box"><div class="alert-title">전자시스템 알림사항</div><ul class="alert-ul"><li>오타확인은 전체리스트를 보시면 쉽게 확인/수정 가능 합니다.</li><li>자료입력후 꼭 자료일관성 확인을 해주시기 바랍니다.</li></ul></div></div></div>'
                st.markdown(settle_html, unsafe_allow_html=True)

            # --- 일반 표 검색 결과 화면 렌더링 ---
            elif params["mode"] != "init":
                f_df = df.copy()
                if params["mode"] == "기간": f_df = f_df[(f_df[date_col].dt.date >= params["start"]) & (f_df[date_col].dt.date <= params["end"])]
                elif params["mode"] in ["월별", "월별단순"]: f_df = f_df[(f_df['year'] == params["year"]) & (f_df['month'] == params["month"])]
                elif params["mode"] == "일": f_df = f_df[f_df[date_col].dt.date == params["date"]]

                target_type = params.get("type", "ALL")
                if target_type == "매입": f_df = f_df[f_df['incom'].astype(str).str.strip() != '']
                elif target_type == "매출": f_df = f_df[f_df['outcom'].astype(str).str.strip() != '']

                com_kw = params.get("company", "")
                item_kw = params.get("item", "")
                if com_kw: f_df = f_df[f_df['incom'].str.contains(com_kw, case=False, na=False) | f_df['outcom'].str.contains(com_kw, case=False, na=False)]
                if item_kw: f_df = f_df[f_df['initem'].str.contains(item_kw, case=False, na=False) | f_df['outitem'].str.contains(item_kw, case=False, na=False)]
                
                f_df = f_df.sort_values(by=[date_col, 'id'], ascending=[not st.session_state.sort_desc, not st.session_state.sort_desc])
                    
                limit_str = params.get("limit", "ALL")
                if limit_str != "ALL" and "개" in limit_str:
                    num = int(limit_str.replace("개", ""))
                    if st.session_state.sort_desc: f_df = f_df.head(num)
                    else: f_df = f_df.tail(num)

                data_count = len(f_df)
                total_in_q = f_df['inq_val'].sum()
                total_in_amt = f_df['in_total'].sum()
                total_out_q = f_df['outq_val'].sum()
                total_out_amt = f_df['out_total'].sum()
                total_carprice = f_df['carprice_val'].sum()
                total_profit = total_out_amt - total_in_amt - total_carprice
                
                table_title_text = params.get("title", "데이터 검색 결과")

                col_t1, col_t2, col_t3 = st.columns([6.5, 1.8, 1.7])
                with col_t1:
                    st.markdown(f'<div class="table-title-box"><span style="font-size: 16px; font-weight: bold; color: #f8fafc;">{table_title_text}</span> <span style="font-size: 13px; color: #cbd5e1; margin-left:10px;">| 출력된 자료 갯수 : {data_count} 개 (오로지 검색 조건순으로만 정렬되었습니다)</span></div>', unsafe_allow_html=True)
                with col_t2:
                    sort_btn_text = "🔄 날짜 정렬 (현재:최신순)" if st.session_state.sort_desc else "🔄 날짜 정렬 (현재:과거순)"
                    if st.button(sort_btn_text, use_container_width=True, type="primary"):
                        st.session_state.sort_desc = not st.session_state.sort_desc
                        st.rerun()
                with col_t3:
                    export_df = f_df[['s', 'date', 'incom', 'initem', 'inq_val', 'inprice_val', 'outcom', 'outitem', 'outq_val', 'outprice_val', 'id', 'carno', 'carprice_val']].copy()
                    export_df['date'] = export_df['date'].dt.strftime('%Y-%m-%d')
                    export_df.columns = ['Vat(상태)', '날짜', '매입거래처', '매입품목', '매입수량', '매입단가', '매출거래처', '매출품목', '매출수량', '매출단가', 'NO', '차량배송', '운송비']
                    csv_data = export_df.to_csv(index=False).encode('utf-8-sig')
                    st.download_button(label="💾 엑셀 다운로드", data=csv_data, file_name=f"검색결과_{datetime.now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True, type="primary")

                html_str = '<div class="custom-table-container">'
                html_str += '<table class="custom-table">'
                html_str += '<thead><tr>'
                html_str += '<th class="th-base">Vat</th>'
                html_str += '<th class="th-base">날짜</th>'
                html_str += '<th class="th-in">매입거래처</th><th class="th-in">매입품목 (MEMO)</th><th class="th-in">수량</th><th class="th-in">단가</th>'
                html_str += '<th class="th-out">매출거래처</th><th class="th-out">매출품목 (MEMO)</th><th class="th-out">수량</th><th class="th-out">단가</th>'
                html_str += '<th class="th-base">NO</th><th class="th-base">배송</th><th class="th-base">운송비</th>'
                html_str += '</tr></thead><tbody>'

                secret_token = str(st.secrets.get("tom_password", ""))

                for _, row in f_df.iterrows():
                    dt_str = row[date_col].strftime('%Y-%m-%d') if pd.notnull(row[date_col]) else ''
                    in_q_str = f"{row['inq_val']:,.0f}" if row['inq_val'] else "0"
                    in_p_str = f"{row['inprice_val']:,.0f}" if row['inprice_val'] else "0"
                    out_q_str = f"{row['outq_val']:,.0f}" if row['outq_val'] else "0"
                    out_p_str = f"{row['outprice_val']:,.0f}" if row['outprice_val'] else "0"
                    car_p_str = f"{row['carprice_val']:,.0f}" if row['carprice_val'] else "0"
                    in_item_full = safe_str(row.get('initem'))
                    out_item_full = safe_str(row.get('outitem'))
                    s_val = safe_str(row.get("s"))
                    if "제일" in s_val: s_cls = "txt-green"
                    elif "중부" in s_val: s_cls = "txt-purple"
                    else: s_cls = "txt-gray"
                    
                    row_id = safe_str(row.get("id"))
                    
                    # 💡 [핵심 복구] Vat 링크(복사) 유지, NO 링크 해제, 날짜(dt_link)에 수정/삭제 기능 다시 부여 (밑줄 제거)
                    vat_link = f'<a href="?copy_id={row_id}&token={secret_token}" target="_self" style="text-decoration:none; cursor:pointer;" title="클릭하여 내용을 복사해 신규입력합니다."><span class="{s_cls}">{s_val}</span></a>'
                    dt_link = f'<a href="?edit_id={row_id}&token={secret_token}" target="_self" style="color:#1e293b; text-decoration:none; cursor:pointer;" title="클릭하여 데이터 수정/삭제">{dt_str}</a>' if dt_str else ''

                    html_str += f'<tr><td class="tc">{vat_link}</td><td class="tc">{dt_link}</td><td class="tl txt-in-bold">{safe_str(row.get("incom"))}</td><td class="tl txt-in">{in_item_full}</td><td class="tr txt-in">{in_q_str}</td><td class="tr txt-in">{in_p_str}</td><td class="tl txt-out-bold">{safe_str(row.get("outcom"))}</td><td class="tl txt-out">{out_item_full}</td><td class="tr txt-out">{out_q_str}</td><td class="tr txt-out">{out_p_str}</td><td class="tc txt-gray">{row_id}</td><td class="tc txt-gray">{safe_str(row.get("carno"))}</td><td class="tr txt-black">{car_p_str}</td></tr>'
                    
                html_str += '</tbody>'
                html_str += '<tfoot><tr>'
                html_str += f'<td colspan="2" class="th-base" style="text-align:left; font-weight:bold; padding:12px 15px; color:white;">자료수 : <span style="color:#ffeb3b;">{data_count}</span> 개</td>'
                html_str += f'<td colspan="4" class="th-in" style="text-align:center; font-weight:bold; padding:12px 15px; color:white;">매입수량 : {total_in_q:,.0f} &nbsp;&nbsp;&nbsp;&nbsp; 매입금액 : {total_in_amt:,.0f}원</td>'
                html_str += f'<td colspan="4" class="th-out" style="text-align:center; font-weight:bold; padding:12px 15px; color:white;">매출수량 : {total_out_q:,.0f} &nbsp;&nbsp;&nbsp;&nbsp; 매출금액 : {total_out_amt:,.0f}원</td>'
                html_str += f'<td colspan="3" class="th-base" style="background-color:#5d607e; text-align:center; font-weight:bold; padding:12px 15px; color:white;">운송비 : {total_carprice:,.0f}원</td>'
                html_str += f'</tr><tr><td colspan="13" class="sum-profit">검색내 총수익 &nbsp;&nbsp; {total_profit:,.0f}원</td></tr></tfoot></table></div>'

                st.markdown(html_str, unsafe_allow_html=True)

    else:
        st.error("❌ 'date' 열을 찾을 수 없습니다.")

except Exception as e:
    st.error(f"⚠️ 시스템 오류: {e}")

# --- [7. 하단 카피라이트] ---
st.markdown("<br><hr style='border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b !important;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
