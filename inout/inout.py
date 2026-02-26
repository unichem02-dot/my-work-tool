import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

# --- [1. 기본 설정] ---
st.set_page_config(layout="wide", page_title="데이터 조회")

# --- [2. 구글 시트 연결] ---
@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=600) # 10분마다 데이터 새로고침
def load_data():
    client = init_connection()
    # 지정하신 구글 시트 이름 연결
    sheet = client.open('SQL백업260211-jeilinout').sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# --- [3. 메인 화면 및 필터링 로직] ---
st.title("📊 월별 데이터 조회 프로그램")

try:
    df = load_data()
    
    # 🚨 필수 확인: 실제 구글 시트의 날짜가 적힌 열 이름을 아래에 적어주세요! (예: '일자', 'Date', '주문일' 등)
    date_col = '날짜' 
    
    if date_col in df.columns:
        # 1. 텍스트 날짜를 진짜 날짜형식으로 변환하고 '년도', '월' 추출
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df['년도'] = df[date_col].dt.year
        df['월'] = df[date_col].dt.month

        # 2. 화면을 2칸으로 나누어 드롭다운(선택창) 배치
        col1, col2 = st.columns(2)
        
        with col1:
            # 시트에 있는 년도만 뽑아서 내림차순 정렬 (최신년도가 위로 오게)
            years = sorted(df['년도'].dropna().unique().tolist(), reverse=True)
            selected_year = st.selectbox("📅 년도 선택", years)
            
        with col2:
            # 1월 ~ 12월 리스트 생성
            months = list(range(1, 13))
            selected_month = st.selectbox("📆 월 선택", months)

        # 3. 선택한 년도와 월에 해당하는 데이터만 걸러내기(필터링)
        filtered_df = df[(df['년도'] == selected_year) & (df['월'] == selected_month)]

        # 4. 필터링된 데이터 화면에 출력
        st.divider()
        st.write(f"### 📋 {int(selected_year)}년 {selected_month}월 데이터 (총 {len(filtered_df)}건)")
        st.dataframe(filtered_df, use_container_width=True)
        
    else:
        st.error(f"❌ 구글 시트 첫 번째 줄(헤더)에 '{date_col}' 이라는 열이 없습니다. 코드 31번째 줄의 date_col 이름을 수정해주세요.")

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")