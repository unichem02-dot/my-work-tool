import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# 커스텀 CSS 주입
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background-color: #1e2530;
    }
    .main .block-container {
        padding-top: 2rem;
    }
    h1, h2, h3, p, span {
        color: #ffffff !important;
    }
    
    [data-testid="stVerticalBlock"] > div:has(div.stContainer) {
        background-color: #262f3d;
        border-radius: 15px;
        padding: 20px;
        border: 1px solid #3d4b5f;
    }
    
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
    }
    
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }
    
    [data-testid="stDataFrame"] {
        background-color: #ffffff;
        border-radius: 10px;
        overflow: hidden;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [2. 보안 및 세션 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "failed_attempts" not in st.session_state: st.session_state.failed_attempts = 0
if "lockout_until" not in st.session_state: st.session_state.lockout_until = None
if "last_activity" not in st.session_state: st.session_state.last_activity = None

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
col_status, col_logout = st.columns([8.5, 1.5])
with col_status:
    st.markdown(f"🟢 **보안 접속 중** | 현재 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
with col_logout:
    if st.button("🔓 LOGOUT", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("<hr style='border: 0.5px solid #3d4b5f;'>", unsafe_allow_html=True)

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

# --- [6. 메인 화면 구성] ---
st.markdown("<h1 style='color: #4e8cff !important;'>📦 입출력 통합 관리 시스템</h1>", unsafe_allow_html=True)

try:
    df = load_data()
    date_col = 'date'
    
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df['year'] = df[date_col].dt.year.astype(int)
        df['month'] = df[date_col].dt.month.astype(int)
        df['year_month'] = df[date_col].dt.strftime('%Y-%m')

        # 금액 계산을 위한 숫자형 변환
        df['inq_val'] = pd.to_numeric(df['inq'], errors='coerce').fillna(0)
        df['inprice_val'] = pd.to_numeric(df['inprice'], errors='coerce').fillna(0)
        df['outq_val'] = pd.to_numeric(df['outq'], errors='coerce').fillna(0)
        df['outprice_val'] = pd.to_numeric(df['outprice'], errors='coerce').fillna(0)
        
        # 총액 계산
        df['in_total'] = df['inq_val'] * df['inprice_val']
        df['out_total'] = df['outq_val'] * df['outprice_val']

        # --- 검색 패널 ---
        with st.container():
            st.markdown("### 🔍 SEARCH FILTERS")
            r1_1, r1_2, r1_3 = st.columns([2, 4, 4])
            
            with r1_1:
                search_mode = st.selectbox("📅 조회 기준", ["월별 검색", "기간 검색", "빠른 일검색"])
                trade_type = st.radio("🔄 거래 구분", ["전체", "매입(입고)", "매출(출고)"], horizontal=True)
                
            with r1_2:
                if search_mode == "월별 검색":
                    c_y, c_m = st.columns(2)
                    sel_year = c_y.selectbox("년도", sorted(df['year'].unique(), reverse=True))
                    sel_month = c_m.selectbox("월", list(range(1, 13)), index=datetime.now().month-1)
                elif search_mode == "기간 검색":
                    date_range = st.date_input("조회 기간 선택", [datetime.now().date() - timedelta(days=30), datetime.now().date()])
                else:
                    quick_mode = st.selectbox("일자 선택", ["오늘", "어제", "직접 선택"])
                    if quick_mode == "오늘": target_date = datetime.now().date()
                    elif quick_mode == "어제": target_date = (datetime.now() - timedelta(days=1)).date()
                    else: target_date = st.date_input("날짜 선택", datetime.now().date())
            
            with r1_3:
                search_company = st.text_input("🏢 거래처 입력 (그래프 분석 대상)", placeholder="업체명을 입력하세요")
                search_item = st.text_input("📦 품목 입력", placeholder="품목명을 입력하세요")

        # --- 필터링 ---
        f_df = df.copy()
        if search_mode == "월별 검색":
            f_df = f_df[(f_df['year'] == sel_year) & (f_df['month'] == sel_month)]
        elif search_mode == "기간 검색":
            if len(date_range) == 2:
                f_df = f_df[(f_df[date_col].dt.date >= date_range[0]) & (f_df[date_col].dt.date <= date_range[1])]
        else:
            f_df = f_df[f_df[date_col].dt.date == target_date]

        if trade_type == "매입(입고)":
            f_df = f_df[f_df['incom'].astype(str).str.strip() != '']
        elif trade_type == "매출(출고)":
            f_df = f_df[f_df['outcom'].astype(str).str.strip() != '']

        if search_company:
            f_df = f_df[f_df['incom'].str.contains(search_company, case=False) | f_df['outcom'].str.contains(search_company, case=False)]
        if search_item:
            f_df = f_df[f_df['initem'].str.contains(search_item, case=False) | f_df['outitem'].str.contains(search_item, case=False)]

        # --- 요약 대시보드 (4컬럼 레이아웃) ---
        st.markdown("<br>", unsafe_allow_html=True)
        total_in_amt = f_df['in_total'].sum()
        total_out_amt = f_df['out_total'].sum()
        data_count = len(f_df) # 총 행의 갯수 (데이터 줄 수)
        
        # 표시용 데이터프레임 생성
        display_df = f_df.drop(columns=['year', 'month', 'year_month', 'inq_val', 'inprice_val', 'outq_val', 'outprice_val', 'in_total', 'out_total']).sort_values(by=date_col, ascending=False)
        
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
            st.markdown(f"""<div class='metric-card' style='border-left-color: #00c853;'>
                <p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>TOTAL IN AMT</p>
                <h2 style='margin:0; color: #00c853 !important;'>₩ {total_in_amt:,.0f}</h2>
            </div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class='metric-card' style='border-left-color: #ff5252;'>
                <p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>TOTAL OUT AMT</p>
                <h2 style='margin:0; color: #ff5252 !important;'>₩ {total_out_amt:,.0f}</h2>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class='metric-card' style='border-left-color: #4e8cff;'>
                <p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>DATA COUNT</p>
                <h2 style='margin:0; color: #4e8cff !important;'>{data_count}건</h2>
            </div>""", unsafe_allow_html=True)
        with m4:
            # 💡 행의 갯수로 수정 완료
            st.markdown(f"""<div class='metric-card' style='border-left-color: #9c27b0;'>
                <p style='margin:0; font-size: 0.9rem; color: #aeb9cc;'>ROW COUNT (행 수)</p>
                <h2 style='margin:0; color: #9c27b0 !important;'>{data_count}줄</h2>
            </div>""", unsafe_allow_html=True)

        # --- 📈 거래처 실적 그래프 섹션 ---
        if search_company and not f_df.empty:
            st.markdown(f"### 📈 '{search_company}' 월별 실적 분석")
            chart_df = df[df['incom'].str.contains(search_company, case=False) | df['outcom'].str.contains(search_company, case=False)].copy()
            
            if not chart_df.empty:
                monthly_stats = chart_df.groupby('year_month')[['in_total', 'out_total']].sum().sort_index()
                monthly_stats.columns = ['매입금액(IN)', '매출금액(OUT)']
                st.bar_chart(monthly_stats)
            else:
                st.info("그래프를 표시할 데이터가 부족합니다.")

        # --- 결과 테이블 ---
        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

    else:
        st.error("❌ 'date' 열을 찾을 수 없습니다.")

except Exception as e:
    st.error(f"⚠️ 시스템 오류: {e}")

# --- [7. 하단 카피라이트] ---
st.markdown("<br><hr style='border: 0.5px solid #3d4b5f;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b !important;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
