import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# 커스텀 CSS 주입 (다크 테마 및 컴팩트한 레이아웃)
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #2b323c;
    }
    .main .block-container {
        padding-top: 1rem;
        max-width: 98%;
    }
    h1, h2, h3, p, span {
        color: #ffffff !important;
    }
    
    /* 검색 패널 전체 배경 */
    .search-panel-container {
        background-color: #353b48;
        padding: 15px;
        border-radius: 8px;
        border: 1px solid #4a5568;
        margin-bottom: 20px;
    }
    
    /* 요약 카드 스타일 */
    .metric-card {
        background: linear-gradient(135deg, #2b3648 0%, #1e2530 100%);
        border-radius: 12px;
        padding: 20px;
        border-left: 5px solid #4e8cff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        text-align: center;
        height: 110px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        margin-bottom: 10px;
    }
    
    /* 버튼 둥글기 및 컴팩트화 */
    div.stButton > button {
        border-radius: 5px !important;
        font-weight: bold !important;
        padding: 0px 10px !important;
    }
    
    /* 데이터프레임 배경 */
    [data-testid="stDataFrame"] {
        background-color: #ffffff;
        border-radius: 5px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 보안 및 세션/검색 상태 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "failed_attempts" not in st.session_state: st.session_state.failed_attempts = 0
if "lockout_until" not in st.session_state: st.session_state.lockout_until = None
if "last_activity" not in st.session_state: st.session_state.last_activity = None
if "search_params" not in st.session_state: 
    st.session_state.search_params = {"mode": "init"} # 초기 상태

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
col_title, col_status, col_logout = st.columns([5, 4.5, 1])
with col_title:
    st.markdown("<h3 style='margin-bottom:0px; padding-bottom:0px;'>📦 입출력 통합 관리 시스템</h3>", unsafe_allow_html=True)
with col_logout:
    if st.button("🔓 LOGOUT", use_container_width=True):
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
            
    df = pd.DataFrame(raw_data[1:], columns=new_header)
    return df

# --- [6. 메인 화면 구성 및 복합 검색 UI] ---
try:
    df = load_data()
    date_col = 'date'
    
    if date_col in df.columns:
        # 기본 데이터 정제
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df['year'] = df[date_col].dt.year.astype(int)
        df['month'] = df[date_col].dt.month.astype(int)
        df['year_month'] = df[date_col].dt.strftime('%Y-%m')

        df['inq_val'] = pd.to_numeric(df['inq'], errors='coerce').fillna(0)
        df['inprice_val'] = pd.to_numeric(df['inprice'], errors='coerce').fillna(0)
        df['outq_val'] = pd.to_numeric(df['outq'], errors='coerce').fillna(0)
        df['outprice_val'] = pd.to_numeric(df['outprice'], errors='coerce').fillna(0)
        
        df['in_total'] = df['inq_val'] * df['inprice_val']
        df['out_total'] = df['outq_val'] * df['outprice_val']

        years = sorted(df['year'].unique().tolist(), reverse=True)
        months = list(range(1, 13))
        if not years: years = [datetime.now().year]

        # ---------------------------------------------------------
        # 💡 스크린샷과 동일한 복합 검색 UI
        # ---------------------------------------------------------
        with st.container():
            st.markdown("<div class='search-panel-container'>", unsafe_allow_html=True)
            
            # [Row 1] 기간 거래처&품목
            r1_1, r1_2, r1_3, r1_4, r1_5, r1_6 = st.columns([1.5, 2.5, 1, 2, 2, 2.5])
            with r1_1: type_1 = st.radio("r1", ["매입", "매출", "ALL"], index=2, horizontal=True, label_visibility="collapsed")
            with r1_2: date_range = st.date_input("d1", [datetime(2014,1,1).date(), datetime.now().date()], label_visibility="collapsed")
            with r1_3: st.selectbox("s1", ["ALL"], label_visibility="collapsed")
            with r1_4: com_1 = st.text_input("t1", placeholder="거래처 검색", label_visibility="collapsed")
            with r1_5: item_1 = st.text_input("t2", placeholder="품목 검색", label_visibility="collapsed")
            with r1_6: btn_1 = st.button("기간 거래처&품목", use_container_width=True, type="primary")

            st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

            # [Row 2] 월별 거래처&품목
            r2_1, r2_2, r2_3, r2_4, r2_5, r2_6, r2_7 = st.columns([1.5, 1.2, 1.3, 1, 2, 2, 2.5])
            with r2_1: type_2 = st.radio("r2", ["매입", "매출", "ALL"], index=2, horizontal=True, label_visibility="collapsed")
            with r2_2: year_2 = st.selectbox("y2", years, label_visibility="collapsed")
            with r2_3: month_2 = st.selectbox("m2", months, index=datetime.now().month-1, label_visibility="collapsed", format_func=lambda x: f"{x}월")
            with r2_4: st.selectbox("s2", ["ALL"], label_visibility="collapsed")
            with r2_5: com_2 = st.text_input("t3", placeholder="거래처 검색", label_visibility="collapsed")
            with r2_6: item_2 = st.text_input("t4", placeholder="품목 검색", label_visibility="collapsed")
            with r2_7: btn_2 = st.button("월별 거래처&품목", use_container_width=True, type="primary")

            st.markdown("<hr style='margin: 10px 0; border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)

            # [Row 3] 하단 멀티 컨트롤 패널
            c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11, c12, c13, c14 = st.columns([0.8, 1.2, 1, 1,   1.2,   1, 1,   1.5, 1,   1.2,   0.8, 1.2, 1, 1.2])
            
            # 결산 그룹
            with c1: st.selectbox("s3", ["ALL"], label_visibility="collapsed")
            with c2: y_3 = st.selectbox("y3", years, label_visibility="collapsed")
            with c3: m_3 = st.selectbox("m3", months, index=datetime.now().month-1, label_visibility="collapsed", format_func=lambda x: f"{x}월")
            with c4: btn_3 = st.button("결산", use_container_width=True)

            # 신규입력
            with c5: btn_4 = st.button("신규입력", use_container_width=True)

            # 최근입력 그룹
            with c6: limit_val = st.selectbox("s4", ["ALL", "20개", "50개"], index=0, label_visibility="collapsed")
            with c7: btn_5 = st.button("최근입력", use_container_width=True, type="primary")

            # 일검색 그룹
            with c8: d_day = st.date_input("d2", datetime.now().date(), label_visibility="collapsed")
            with c9: btn_6 = st.button("일검색", use_container_width=True, type="primary")

            # 어제오늘내일
            with c10: btn_7 = st.button("어제오늘내일", use_container_width=True, type="primary")

            # 월별검색 그룹
            with c11: st.selectbox("s5", ["ALL"], label_visibility="collapsed")
            with c12: y_4 = st.selectbox("y4", years, label_visibility="collapsed")
            with c13: m_4 = st.selectbox("m4", months, index=datetime.now().month-1, label_visibility="collapsed", format_func=lambda x: f"{x}월")
            with c14: btn_8 = st.button("월별검색", use_container_width=True, type="primary")
            
            st.markdown("</div>", unsafe_allow_html=True)

        # ---------------------------------------------------------
        # 💡 클릭 이벤트 처리 및 세션 저장 (액션 라우팅)
        # ---------------------------------------------------------
        if btn_1:
            st.session_state.search_params = {
                "mode": "기간", "type": type_1, "company": com_1, "item": item_1, "limit": "ALL",
                "start": date_range[0], "end": date_range[1] if len(date_range)>1 else date_range[0]
            }
        elif btn_2:
            st.session_state.search_params = {
                "mode": "월별", "type": type_2, "company": com_2, "item": item_2, "limit": "ALL",
                "year": year_2, "month": month_2
            }
        elif btn_3: # 결산
            st.session_state.search_params = {"mode": "월별단순", "year": y_3, "month": m_3, "type": "ALL", "company": "", "item": "", "limit": "ALL"}
        elif btn_4: # 신규입력 (임시)
            st.info("신규입력 기능은 아직 구현되지 않았습니다.")
        elif btn_5: # 최근입력
            st.session_state.search_params = {"mode": "최근", "type": "ALL", "company": "", "item": "", "limit": limit_val}
        elif btn_6: # 일검색
            st.session_state.search_params = {"mode": "일", "date": d_day, "type": "ALL", "company": "", "item": "", "limit": "ALL"}
        elif btn_7: # 어제오늘내일
            st.session_state.search_params = {
                "mode": "기간", "type": "ALL", "company": "", "item": "", "limit": "ALL",
                "start": datetime.now().date() - timedelta(days=1), "end": datetime.now().date() + timedelta(days=1)
            }
        elif btn_8: # 월별검색
            st.session_state.search_params = {"mode": "월별단순", "year": y_4, "month": m_4, "type": "ALL", "company": "", "item": "", "limit": "ALL"}
        
        # ---------------------------------------------------------
        # 💡 데이터 필터링 실행
        # ---------------------------------------------------------
        f_df = df.copy()
        params = st.session_state.search_params
        
        if params["mode"] != "init":
            # 1. 날짜 조건 필터
            if params["mode"] == "기간":
                f_df = f_df[(f_df[date_col].dt.date >= params["start"]) & (f_df[date_col].dt.date <= params["end"])]
            elif params["mode"] in ["월별", "월별단순"]:
                f_df = f_df[(f_df['year'] == params["year"]) & (f_df['month'] == params["month"])]
            elif params["mode"] == "일":
                f_df = f_df[f_df[date_col].dt.date == params["date"]]
            elif params["mode"] == "최근":
                f_df = f_df.sort_values(by=date_col, ascending=False) # 날짜 역순 정렬 우선

            # 2. 매입/매출 구분 필터
            target_type = params.get("type", "ALL")
            if target_type == "매입":
                f_df = f_df[f_df['incom'].astype(str).str.strip() != '']
            elif target_type == "매출":
                f_df = f_df[f_df['outcom'].astype(str).str.strip() != '']

            # 3. 키워드 검색 (거래처/품목)
            com_kw = params.get("company", "")
            item_kw = params.get("item", "")
            if com_kw:
                f_df = f_df[f_df['incom'].str.contains(com_kw, case=False, na=False) | f_df['outcom'].str.contains(com_kw, case=False, na=False)]
            if item_kw:
                f_df = f_df[f_df['initem'].str.contains(item_kw, case=False, na=False) | f_df['outitem'].str.contains(item_kw, case=False, na=False)]
                
            # 4. 개수 제한 필터 (limit)
            limit_str = params.get("limit", "ALL")
            if limit_str != "ALL" and "개" in limit_str:
                num = int(limit_str.replace("개", ""))
                f_df = f_df.head(num)

        # ---------------------------------------------------------
        # 📊 대시보드 및 결과 출력
        # ---------------------------------------------------------
        total_in_amt = f_df['in_total'].sum()
        total_out_amt = f_df['out_total'].sum()
        data_count = len(f_df)
        
        # 내부 계산용 컬럼 제거 (원본 컬럼 17개는 모두 살림)
        display_df = f_df.drop(columns=['year', 'month', 'year_month', 'inq_val', 'inprice_val', 'outq_val', 'outprice_val', 'in_total', 'out_total'])
        
        # 날짜 최신순 정렬 및 문자열 변환
        display_df = display_df.sort_values(by=date_col, ascending=False)
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        
        # 보기 좋은 한글 이름으로 전체 변경
        rename_dict = {
            'id': '순번', 'date': '날짜', 'incom': '입고처', 'initem': '입고품목',
            'inq': '수량(入)', 'inprice': '단가(入)', 'outcom': '출고처', 'outitem': '출고품목',
            'outq': '수량(出)', 'outprice': '단가(出)', 'etc': '비고', 's': '상태',
            'carno': '차량번호', 'carprice': '운임', 'memoin': '메모(入)', 'memoout': '메모(出)',
            'memocar': '메모(차)'
        }
        display_df = display_df.rename(columns=rename_dict)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='metric-card' style='border-left-color: #00c853;'><p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>TOTAL IN AMT</p><h2 style='margin:0; color: #00c853 !important;'>₩ {total_in_amt:,.0f}</h2></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-card' style='border-left-color: #ff5252;'><p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>TOTAL OUT AMT</p><h2 style='margin:0; color: #ff5252 !important;'>₩ {total_out_amt:,.0f}</h2></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-card' style='border-left-color: #4e8cff;'><p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>DATA COUNT</p><h2 style='margin:0; color: #4e8cff !important;'>{data_count}건</h2></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='metric-card' style='border-left-color: #9c27b0;'><p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>ROW COUNT (행 수)</p><h2 style='margin:0; color: #9c27b0 !important;'>{data_count}줄</h2></div>", unsafe_allow_html=True)

        # 📈 거래처 실적 그래프 섹션 (검색 시에만)
        com_kw = params.get("company", "")
        if com_kw and not f_df.empty:
            st.markdown(f"### 📈 '{com_kw}' 전체 월별 실적 흐름")
            chart_df = df[df['incom'].str.contains(com_kw, case=False, na=False) | df['outcom'].str.contains(com_kw, case=False, na=False)].copy()
            if not chart_df.empty:
                monthly_stats = chart_df.groupby('year_month')[['in_total', 'out_total']].sum().sort_index()
                monthly_stats.columns = ['매입금액(IN)', '매출금액(OUT)']
                st.bar_chart(monthly_stats)

        # 결과 테이블 (잘림 없이 전체 데이터 표시)
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(display_df, use_container_width=True, hide_index=True, height=600)

    else:
        st.error("❌ 'date' 열을 찾을 수 없습니다.")

except Exception as e:
    st.error(f"⚠️ 시스템 오류: {e}")

# --- [7. 하단 카피라이트] ---
st.markdown("<br><hr style='border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b !important;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
