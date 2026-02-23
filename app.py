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

# 시트 연결 객체 가져오기 (연결 속성이므로 캐싱 대상에서 제외)
def get_sheet():
    client = init_connection()
    return client.open("English_Sentences").sheet1

# 2. 데이터 불러오기 (순수 데이터만 캐싱)
@st.cache_data(ttl=10) # 10초마다 데이터 갱신
def load_dataframe():
    sheet = get_sheet()
    data = sheet.get_all_records()
    # 구글 시트에 아직 아무 데이터도 없을 경우의 오류 방지
    if not data: 
        return pd.DataFrame(columns=['English', 'Korean', 'Tags'])
    return pd.DataFrame(data)

st.title("📚 나의 영어 문장 관리장")

# 데이터 로딩 시도 및 에러 처리 분리
data_loaded = False
try:
    sheet = get_sheet() # 연결 객체는 따로 불러옴
    df = load_dataframe() # 데이터 프레임만 캐시에서 불러옴
    data_loaded = True
except Exception as e:
    st.error(f"구글 시트 데이터를 불러오는 중 오류가 발생했습니다.\n\n설정(Secrets)이나 시트 이름을 확인해주세요.\n\n에러 내용: {e}")

# 정상적으로 불러와졌을 때만 아래 UI들을 보여줍니다.
if data_loaded:
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
                try:
                    # 구글 시트의 마지막 줄에 데이터 추가
                    sheet.append_row([new_eng, new_kor, new_tags])
                    st.success("성공적으로 저장되었습니다! 🔄 잠시 후 새로고침됩니다.")
                    st.cache_data.clear() # 캐시 초기화하여 새 데이터 반영
                    st.rerun() # 화면 새로고침
                except Exception as e:
                    # 실제 추가 중 에러가 발생했을 때만 표시
                    st.error(f"데이터 추가 중 오류가 발생했습니다. 상세: {e}")
            else:
                st.error("영어 문장과 뜻을 모두 입력해주세요.")
