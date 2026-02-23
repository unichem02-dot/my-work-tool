import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. 구글 시트 연동 설정
# Streamlit Secrets에서 구글 서비스 계정 정보를 가져옵니다.
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    # st.secrets["gcp_service_account"] 에 JSON 키 내용을 설정해야 합니다.
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client

# 2. 데이터 불러오기
@st.cache_data(ttl=10) # 10초마다 데이터 갱신
def load_data():
    client = init_connection()
    # 'English_Sentences'라는 이름의 구글 시트 파일을 엽니다. (이름을 본인 시트에 맞게 변경하세요)
    sheet = client.open("English_Sentences").sheet1
    data = sheet.get_all_records()
    return pd.DataFrame(data), sheet

st.title("📚 나의 영어 문장 관리장")

try:
    df, sheet = load_data()
    
    # --- [검색 기능] ---
    st.header("🔍 문장 검색")
    search_query = st.text_input("검색어를 입력하세요 (영어 또는 뜻)")
    
    if search_query:
        # 영어 문장이나 한국어 뜻에 검색어가 포함된 데이터 필터링
        filtered_df = df[
            df['English'].str.contains(search_query, case=False, na=False) |
            df['Korean'].str.contains(search_query, case=False, na=False)
        ]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    st.divider()

    # --- [추가 기능] ---
    st.header("➕ 새 문장 추가")
    with st.form("add_sentence_form"):
        new_eng = st.text_input("영어 문장")
        new_kor = st.text_input("한국어 뜻")
        new_tags = st.text_input("태그 (예: 비즈니스, 일상, 토익)")
        
        submitted = st.form_submit_button("시트에 저장하기")
        if submitted:
            if new_eng and new_kor:
                # 구글 시트의 마지막 줄에 데이터 추가
                sheet.append_row([new_eng, new_kor, new_tags])
                st.success("성공적으로 저장되었습니다! 🔄 새로고침을 눌러 확인하세요.")
                st.cache_data.clear() # 캐시 초기화하여 새 데이터 반영
                st.rerun()
            else:
                st.error("영어 문장과 뜻을 모두 입력해주세요.")

except Exception as e:
    st.error(f"구글 시트 연동 중 오류가 발생했습니다. 설정(Secrets)을 확인해주세요.\n\n에러 내용: {e}")