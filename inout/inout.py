import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# --- [1. 페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# --- [2. 강력한 보안 및 세션 상태 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "failed_attempts" not in st.session_state: st.session_state.failed_attempts = 0
if "lockout_until" not in st.session_state: st.session_state.lockout_until = None
if "last_activity" not in st.session_state: st.session_state.last_activity = None

now = datetime.now()

# [보안 A] 5회 실패로 인한 계정 잠금 확인
if st.session_state.lockout_until:
    if now < st.session_state.lockout_until:
        lock_minutes = (st.session_state.lockout_until - now).seconds // 60
        st.error(f"🔒 해킹 방지: 비밀번호 5회 오류로 시스템이 잠겼습니다. {lock_minutes}분 후 다시 시도해주세요.")
        st.stop()
    else:
        # 잠금 시간(10분)이 지나면 초기화
        st.session_state.lockout_until = None
        st.session_state.failed_attempts = 0

# [보안 B] 30분 미사용 시 자동 로그아웃 확인
if st.session_state.authenticated and st.session_state.last_activity:
    if now - st.session_state.last_activity > timedelta(minutes=30):
        st.session_state.authenticated = False
        st.warning("⏱️ 안전을 위해 장시간(30분) 미사용으로 자동 로그아웃 되었습니다.")

# --- [3. 로그인 화면 렌더링] ---
if not st.session_state.authenticated:
    st.title("🔴 시스템 로그아웃 상태")
    st.info("데이터를 열람하려면 비밀번호를 입력해 주세요.")
    
    with st.form("login_form"):
        pwd = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
        submit_btn = st.form_submit_button("로그인", type="primary", use_container_width=True)
        
        if submit_btn:
            if "tom_password" not in st.secrets:
                st.error("⚠️ Streamlit Secrets에 'tom_password'가 설정되지 않았습니다.")
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
                    st.error("❌ 5회 연속 실패! 10분 동안 로그인이 차단됩니다.")
                    st.rerun()
                else:
                    st.error(f"❌ 비밀번호가 틀렸습니다. (남은 기회: {remains}번)")
    
    st.stop() # 인증 안 되면 여기서 멈춤

# --- [4. 로그인 성공 후 상단 상태바 & 로그아웃 버튼] ---
st.session_state.last_activity = datetime.now() # 사용자가 클릭/조작할 때마다 활동 시간 갱신

col_status, col_logout = st.columns([8, 2])
with col_status:
    st.success("🟢 **보안 접속 중** (30분간 조작이 없으면 자동 로그아웃됩니다)")
with col_logout:
    if st.button("🔓 안전하게 로그아웃", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

st.markdown("---")

# --- [5. 구글 시트 연결 및 데이터 로드] ---
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
    if not raw_data:
        return pd.DataFrame()
    
    original_header = raw_data[0]
    new_header = []
    for i, name in enumerate(original_header):
        clean_name = name.strip()
        if not clean_name:
            new_header.append(f"empty_{i}")
        elif clean_name in new_header:
            new_header.append(f"{clean_name}_{i}")
        else:
            new_header.append(clean_name)
            
    df = pd.DataFrame(raw_data[1:], columns=new_header)
    return df

# --- [6. 메인 화면 구성 및 로직] ---
st.title("📂 입출력 내역 조회 시스템")

try:
    df = load_data()
    date_col = 'date'
    
    if date_col in df.columns:
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        df['year'] = df[date_col].dt.year.astype(int)
        df['month'] = df[date_col].dt.month.astype(int)

        # ---------------------------------------------------------
        # 💡 업그레이드된 통합 검색 UI
        # ---------------------------------------------------------
        st.markdown("### 🔍 상세 검색 조건")
        
        with st.container(border=True): # 깔끔한 박스 테두리 적용
            row1_1, row1_2, row1_3 = st.columns([1.5, 3, 5])
            
            with row1_1:
                search_mode = st.radio("조회 방식", ["월별 검색", "기간 검색", "빠른 일검색"])
                
            with row1_2:
                if search_mode == "월별 검색":
                    years = sorted(df['year'].unique().tolist(), reverse=True)
                    sel_year = st.selectbox("📅 년도", years)
                    sel_month = st.selectbox("📆 월", list(range(1, 13)), index=datetime.now().month-1)
                elif search_mode == "기간 검색":
                    start_date = datetime.now().date() - timedelta(days=30)
                    end_date = datetime.now().date()
                    date_range = st.date_input("🗓️ 기간 선택", [start_date, end_date])
                else: # 빠른 일검색
                    quick_mode = st.radio("일자 선택", ["오늘", "어제", "내일", "직접 선택"], horizontal=True)
                    if quick_mode == "오늘": target_date = datetime.now().date()
                    elif quick_mode == "어제": target_date = (datetime.now() - timedelta(days=1)).date()
                    elif quick_mode == "내일": target_date = (datetime.now() + timedelta(days=1)).date()
                    else: target_date = st.date_input("특정일 선택", datetime.now().date())
            
            with row1_3:
                trade_type = st.radio("구분 (매입/매출)", ["ALL (전체)", "매입 (입고)", "매출 (출고)"], horizontal=True)
                col_k1, col_k2 = st.columns(2)
                with col_k1:
                    search_company = st.text_input("🏢 거래처 검색 (입/출고처)")
                with col_k2:
                    search_item = st.text_input("📦 품목 검색 (입/출고품목)")

        # ---------------------------------------------------------
        # 💡 데이터 필터링 실행
        # ---------------------------------------------------------
        filtered_df = df.copy()

        # 1. 날짜 필터 적용
        if search_mode == "월별 검색":
            filtered_df = filtered_df[(filtered_df['year'] == sel_year) & (filtered_df['month'] == sel_month)]
        elif search_mode == "기간 검색":
            if len(date_range) == 2:
                filtered_df = filtered_df[(filtered_df[date_col].dt.date >= date_range[0]) & (filtered_df[date_col].dt.date <= date_range[1])]
            elif len(date_range) == 1: # 사용자가 아직 종료일을 선택하지 않은 경우 방어코드
                filtered_df = filtered_df[filtered_df[date_col].dt.date == date_range[0]]
        else: # 빠른 일검색
            filtered_df = filtered_df[filtered_df[date_col].dt.date == target_date]

        # 2. 분류 필터 적용 (매입/매출)
        if trade_type == "매입 (입고)":
            filtered_df = filtered_df[filtered_df['incom'].astype(str).str.strip() != '']
        elif trade_type == "매출 (출고)":
            filtered_df = filtered_df[filtered_df['outcom'].astype(str).str.strip() != '']

        # 3. 키워드 필터 적용 (거래처 및 품목)
        if search_company:
            mask_com = (
                filtered_df['incom'].astype(str).str.contains(search_company, case=False, na=False) |
                filtered_df['outcom'].astype(str).str.contains(search_company, case=False, na=False)
            )
            filtered_df = filtered_df[mask_com]
            
        if search_item:
            mask_item = (
                filtered_df['initem'].astype(str).str.contains(search_item, case=False, na=False) |
                filtered_df['outitem'].astype(str).str.contains(search_item, case=False, na=False)
            )
            filtered_df = filtered_df[mask_item]

        # ---------------------------------------------------------
        # 💡 결과 출력
        # ---------------------------------------------------------
        display_df = filtered_df.drop(columns=['year', 'month'])
        display_df = display_df.sort_values(by=date_col, ascending=False)
        
        rename_dict = {
            'id': '순번', 'date': '날짜', 'incom': '입고처', 'initem': '입고품목',
            'inq': '입고수량', 'inprice': '입고단가', 'outcom': '출고처', 'outitem': '출고품목',
            'outq': '출고수량', 'outprice': '출고단가', 'etc': '비고', 's': '상태',
            'carno': '차량번호', 'carprice': '운임', 'memoin': '입고메모', 'memoout': '출고메모',
            'memocar': '차량메모'
        }
        display_df = display_df.rename(columns=rename_dict)

        st.divider()
        st.subheader(f"📊 검색 결과 상세 내역 (총 {len(display_df)}건)")
        
        if not display_df.empty:
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        else:
            st.info("조건에 맞는 데이터가 없습니다. 검색 조건을 다시 확인해주세요.")
    else:
        st.error(f"❌ 시트의 헤더에서 '{date_col}' 열을 찾을 수 없습니다. 엑셀의 첫 줄 이름을 확인해 주세요.")

except Exception as e:
    st.error(f"⚠️ 시스템 오류가 발생했습니다: {e}")

# --- [7. 하단 카피라이트] ---
st.markdown("---")
st.caption(f"© {datetime.now().year} unichem02-dot. All rights reserved.")
