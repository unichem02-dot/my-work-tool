import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 구글 시트 연결 함수
def get_google_sheet():
    # Secrets에 저장한 정보를 가져옵니다.
    creds_info = st.secrets["gspread_credentials"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 사장님이 만드신 '구글 시트의 이름'을 정확히 적어주세요.
    # 예: "입출고데이터_변환"
    sheet = client.open("입출고데이터_변환").sheet1 
    return sheet

# 화면에 데이터 불러오기 버튼 만들기
st.divider() # 구분선
st.subheader("📊 구글 시트 데이터 확인")

if st.button("시트 데이터 가져오기"):
    try:
        sheet = get_google_sheet()
        data = sheet.get_all_records() # 모든 데이터 가져오기
        df = pd.DataFrame(data)
        
        st.success(f"성공! 총 {len(df)}개의 기록을 찾았습니다.")
        st.dataframe(df.head(100)) # 일단 상위 100개만 보여주기
    except Exception as e:
        st.error(f"연결 오류: {e}")
        st.info("구글 시트에서 '공유' 버튼을 눌러 tomboy@... 이메일을 추가했는지 확인하세요!")