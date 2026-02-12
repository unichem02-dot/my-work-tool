import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 구글 시트와 연결하는 마법의 함수
def get_google_sheet():
    # Secrets에 저장한 정보를 불러옵니다
    creds_info = st.secrets["gspread_credentials"]
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(creds_info, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 사장님의 구글 시트 이름을 정확히 적으세요 (예: "입출고장부")
    sheet = client.open("입출고데이터_변환").sheet1 
    return sheet

st.divider()
st.subheader("📊 구글 시트 데이터 실시간 조회")

if st.button("시트 데이터 가져오기"):
    try:
        sheet = get_google_sheet()
        data = sheet.get_all_records() # 시트의 모든 데이터를 가져옴
        df = pd.DataFrame(data)
        
        st.success(f"연결 성공! 총 {len(df)}행의 데이터를 불러왔습니다.")
        st.dataframe(df) # 표 형식으로 화면에 출력
    except Exception as e:
        st.error(f"에러 발생: {e}")
        st.info("구글 시트에서 'tomboy@tomboy94...' 이메일을 편집자로 공유했는지 확인하세요!")
