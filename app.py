import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# 1. 구글 시트 연동 설정 (인증 정보만 캐싱하여 속도 유지)
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

def get_sheet():
    client = init_connection()
    return client.open("English_Sentences").sheet1

# 2. 데이터 불러오기 (에러의 원인이었던 캐싱 제거 및 재시도 로직 추가)
def load_dataframe(sheet):
    # 구글 API가 정상(200)인데도 데이터를 늦게 주어 에러가 나는 현상 방지 (최대 3번 재시도)
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            
            # 구글 시트에 아직 아무 데이터도 없을 경우의 오류 방지
            if not data: 
                return pd.DataFrame(columns=['English', 'Korean', 'Tags'])
                
            # 첫 번째 줄은 헤더, 나머지는 데이터로 분리
            headers = data[0]
            rows = data[1:]
            
            # 만약 첫째 줄(헤더)이 비어있다면 강제 지정
            if len(headers) < 3 or headers[0] == "":
                headers = ['English', 'Korean', 'Tags']
                rows = data
                
            return pd.DataFrame(rows, columns=headers)
        except Exception as e:
            # 에러 발생 시 1초 대기 후 다시 시도
            time.sleep(1)
            
    # 3번 모두 실패했을 때만 에러 발생
    raise Exception("구글 시트 응답 지연 (잠시 후 다시 시도해주세요)")

st.title("📚 나의 영어 문장 관리장")

# 데이터 로딩 시도
data_loaded = False
try:
    sheet = get_sheet() # 연결 객체 불러오기
    df = load_dataframe(sheet) # 데이터 프레임 불러오기
    data_loaded = True
except Exception as e:
    st.error(f"구글 시트 데이터를 불러오는 중 오류가 발생했습니다.\n\n에러 내용: {e}")

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
    # clear_on_submit=True 를 추가하여 저장 완료 시 입력칸이 자동으로 비워지게 개선
    with st.form("add_sentence_form", clear_on_submit=True):
        new_eng = st.text_input("영어 문장")
        new_kor = st.text_input("한국어 뜻")
        new_tags = st.text_input("태그 (예: 비즈니스, 일상, 토익)")
        
        submitted = st.form_submit_button("시트에 저장하기")
        
        if submitted:
            if new_eng and new_kor:
                try:
                    # 구글 시트의 마지막 줄에 데이터 추가
                    sheet.append_row([new_eng, new_kor, new_tags])
                    st.success("성공적으로 저장되었습니다! 🔄")
                    time.sleep(1) # 구글 시트에 반영될 수 있도록 1초 대기
                    st.rerun() # 화면 새로고침
                except Exception as e:
                    st.error(f"데이터 추가 중 오류가 발생했습니다. 상세: {e}")
            else:
                st.error("영어 문장과 뜻을 모두 입력해주세요.")
