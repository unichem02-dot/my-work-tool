import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# 1. 구글 시트 연동 설정
@st.cache_resource
def init_connection():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"], scopes=scopes
    )
    client = gspread.authorize(creds)
    return client

def get_sheet():
    client = init_connection()
    return client.open("English_Sentences").sheet1

# 2. 변경된 구조에 맞춘 데이터 불러오기
def load_dataframe(sheet):
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            
            # 텅 빈 시트일 경우 기본 7개 항목 세팅
            if not data: 
                return pd.DataFrame(columns=['번호', '단어', '문장', '발음', '해석', '메모1', '메모2'])
                
            headers = data[0]
            rows = data[1:]
            
            # 헤더가 부족하거나 비어있으면 강제 지정
            if len(headers) < 7 or headers[0] == "":
                headers = ['번호', '단어', '문장', '발음', '해석', '메모1', '메모2']
                # 데이터 길이가 안 맞으면 빈칸으로 채움
                rows = [row + [""] * (7 - len(row)) for row in rows]
                
            return pd.DataFrame(rows, columns=headers)
        except Exception as e:
            time.sleep(1)
            
    raise Exception("구글 시트 응답 지연 (잠시 후 다시 시도해주세요)")

st.title("📚 나의 영어 문장 관리장")

data_loaded = False
try:
    sheet = get_sheet()
    df = load_dataframe(sheet)
    data_loaded = True
except Exception as e:
    st.error(f"구글 시트 데이터를 불러오는 중 오류가 발생했습니다.\n\n에러 내용: {e}")

if data_loaded:
    # --- [검색 기능] ---
    st.header("🔍 단어/문장 검색")
    search_query = st.text_input("검색어를 입력하세요 (단어, 문장, 해석 등)")
    
    if search_query:
        # 존재하는 열에서만 안전하게 검색하도록 동적 필터링
        mask = pd.Series(False, index=df.index)
        search_columns = ['단어', '문장', '해석', '메모1', '메모2', '매모2'] # '매모2' 오타 대비
        
        for col in search_columns:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(search_query, case=False, na=False)
                
        filtered_df = df[mask]
        st.dataframe(filtered_df, use_container_width=True)
    else:
        st.dataframe(df, use_container_width=True)

    st.divider()

    # --- [추가 기능] ---
    st.header("➕ 새 항목 추가")
    with st.form("add_sentence_form", clear_on_submit=True):
        # 7개 항목을 깔끔하게 보여주기 위해 2단 레이아웃 사용
        col1, col2 = st.columns(2)
        
        with col1:
            new_num = st.text_input("1. 번호 (예: 2)")
            new_word = st.text_input("2. 단어 (예: involve)")
            new_sent = st.text_input("3. 문장")
            
        with col2:
            new_pron = st.text_input("4. 발음")
            new_mean = st.text_input("5. 해석 (예: 집어넣다.)")
            new_memo1 = st.text_input("6. 메모1 (예: 돌돌말아서 안에 넣다.)")
            
        new_memo2 = st.text_input("7. 메모2")
        
        submitted = st.form_submit_button("시트에 저장하기")
        
        if submitted:
            # 단어 또는 문장 둘 중 하나라도 입력되면 저장 진행
            if new_word or new_sent:
                try:
                    # 7개 데이터를 순서대로 추가
                    sheet.append_row([new_num, new_word, new_sent, new_pron, new_mean, new_memo1, new_memo2])
                    st.success("성공적으로 저장되었습니다! 🔄")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"데이터 추가 중 오류가 발생했습니다. 상세: {e}")
            else:
                st.error("최소한 '단어'나 '문장' 중 하나는 입력해주세요.")
