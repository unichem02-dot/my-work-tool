import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# --- [1. 페이지 기본 설정] ---
# 레이아웃을 넓게 설정하고 웹 브라우저 탭 제목을 지정합니다.
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# --- [보안: 비밀번호 로그인 로직] ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 시스템 접속")
    st.info("데이터를 열람하려면 비밀번호를 입력해 주세요.")
    
    with st.form("login_form"):
        pwd = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
        submit_btn = st.form_submit_button("확인", type="primary", use_container_width=True)
        
        if submit_btn:
            # 💡 시크릿에 비밀번호가 설정되어 있는지 먼저 확인 (KeyError 에러 방지)
            if "tom_password" not in st.secrets:
                st.error("⚠️ Streamlit Secrets에 'tom_password'가 설정되지 않았습니다. 클라우드 설정(Advanced settings)을 확인해주세요.")
            # 하드코딩된 "3709" 대신 스트림릿 시크릿에서 비밀번호 불러오기
            elif pwd == str(st.secrets["tom_password"]):
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ 비밀번호가 일치하지 않습니다.")
    
    # 🚨 로그인이 안 되었을 경우 여기서 코드 실행을 멈춤 (데이터 유출 완벽 차단)
    st.stop()

# --- [2. 구글 시트 연결 및 데이터 로드] ---

@st.cache_resource
def init_connection():
    """구글 서비스 계정 인증 정보를 사용하여 gspread 클라이언트를 초기화합니다."""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # Streamlit Cloud의 Secrets에 저장된 정보를 사용합니다.
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=300) # 5분(300초) 동안 데이터를 캐싱하여 속도를 높입니다.
def load_data():
    """구글 시트에서 데이터를 읽어와 Pandas 데이터프레임으로 변환합니다."""
    client = init_connection()
    # 지정하신 시트 이름으로 연결합니다.
    sheet = client.open('SQL백업260211-jeilinout').sheet1
    
    # get_all_records()의 중복 헤더 오류를 피하기 위해 전체 값을 리스트로 먼저 가져옵니다.
    raw_data = sheet.get_all_values()
    if not raw_data:
        return pd.DataFrame()
    
    # 첫 번째 줄(헤더) 처리: 중복된 이름이나 빈 칸이 있으면 숫자를 붙여 고유하게 만듭니다.
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
            
    # 데이터프레임 생성 (두 번째 줄부터 데이터)
    df = pd.DataFrame(raw_data[1:], columns=new_header)
    return df

# --- [3. 메인 화면 구성 및 로직] ---

st.title("📂 입출력 내역 조회 시스템")

try:
    df = load_data()
    
    # 올려주신 이미지에 맞게 날짜 열 이름을 'date'로 수정했습니다!
    date_col = 'date'
    
    if date_col in df.columns:
        # 1. 날짜 데이터 형식 변환 (에러 발생 시 NaT로 처리)
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # 2. 날짜값이 비어있는 행은 제거합니다.
        df = df.dropna(subset=[date_col])
        
        # 3. 필터링을 위한 년도(year)와 월(month) 열 생성
        df['year'] = df[date_col].dt.year.astype(int)
        df['month'] = df[date_col].dt.month.astype(int)

        # --- 상단 선택 필터 구역 ---
        filter_col1, filter_col2, filter_col3 = st.columns([2, 2, 6])
        
        with filter_col1:
            # 시트에 있는 년도 목록 (최신순 정렬)
            years = sorted(df['year'].unique().tolist(), reverse=True)
            selected_year = st.selectbox("📅 조회 년도 선택", years)
            
        with filter_col2:
            # 1월부터 12월까지 선택
            months = list(range(1, 13))
            # 현재 시스템 날짜의 월을 기본값으로 설정
            this_month = datetime.now().month
            selected_month = st.selectbox("📆 조회 월 선택", months, index=this_month-1)

        # --- 데이터 필터링 실행 ---
        mask = (df['year'] == selected_year) & (df['month'] == selected_month)
        filtered_df = df[mask].copy()

        # 사용자에게 보여줄 때는 내부용으로 만든 year, month 열은 숨깁니다.
        display_df = filtered_df.drop(columns=['year', 'month'])
        
        # 보기 좋게 날짜순으로 정렬 (최신 날짜가 위로)
        display_df = display_df.sort_values(by=date_col, ascending=False)
        
        # 💡 영어로 된 헤더 이름을 화면 표시용으로 보기 좋게 한글로 변경합니다 (원하시는 대로 수정 가능합니다)
        rename_dict = {
            'id': '순번',
            'date': '날짜',
            'incom': '입고처',
            'initem': '입고품목',
            'inq': '입고수량',
            'inprice': '입고단가',
            'outcom': '출고처',
            'outitem': '출고품목',
            'outq': '출고수량',
            'outprice': '출고단가',
            'etc': '비고',
            's': '상태',
            'carno': '차량번호',
            'carprice': '운임',
            'memoin': '입고메모',
            'memoout': '출고메모',
            'memocar': '차량메모'
        }
        display_df = display_df.rename(columns=rename_dict)

        st.divider()
        st.subheader(f"📊 {selected_year}년 {selected_month}월 상세 내역 (총 {len(display_df)}건)")
        
        # --- 결과 테이블 출력 ---
        if not display_df.empty:
            st.dataframe(
                display_df, 
                use_container_width=True, 
                hide_index=True # 인덱스 번호는 숨겨서 엑셀처럼 보이게 함
            )
        else:
            st.info(f"선택하신 {selected_year}년 {selected_month}월에는 데이터가 없습니다.")

    else:
        st.error(f"❌ 시트의 헤더에서 '{date_col}' 열을 찾을 수 없습니다. 엑셀의 첫 줄 이름을 확인해 주세요.")

except Exception as e:
    st.error(f"⚠️ 시스템 오류가 발생했습니다: {e}")

# --- [4. 하단 카피라이트] ---
st.markdown("---")
st.caption(f"© {datetime.now().year} unichem02-dot. All rights reserved.")
