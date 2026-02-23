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
        search_columns = ['단어', '문장', '해석', '메모1', '메모2', '매모2'] 
        
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
    
    # 💡 자동 번호 계산 (기존 번호 중 가장 큰 값 + 1)
    if df.empty:
        next_num = 1
    else:
        # 문자가 섞여 있어도 숫자로 변환 후 최댓값 찾기
        next_num = int(pd.to_numeric(df['번호'], errors='coerce').fillna(0).max()) + 1

    with st.form("add_sentence_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("번호 (자동 부여)", value=str(next_num), disabled=True)
            new_word = st.text_input("단어")
            new_sent = st.text_input("문장")
            
        with col2:
            new_pron = st.text_input("발음")
            new_mean = st.text_input("해석")
            new_memo1 = st.text_input("메모1")
            
        new_memo2 = st.text_input("메모2")
        
        submitted = st.form_submit_button("시트에 저장하기")
        
        if submitted:
            if new_word or new_sent:
                try:
                    sheet.append_row([str(next_num), new_word, new_sent, new_pron, new_mean, new_memo1, new_memo2])
                    st.success("성공적으로 저장되었습니다! 🔄")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"데이터 추가 중 오류가 발생했습니다. 상세: {e}")
            else:
                st.error("최소한 '단어'나 '문장' 중 하나는 입력해주세요.")

    st.divider()

    # --- [수정 기능] ---
    st.header("✏️ 기존 항목 수정")
    
    if not df.empty:
        # 선택상자에 보여줄 목록 만들기 (예: [1] involve - 집어넣다)
        options = df.apply(lambda x: f"[{x['번호']}] {x['단어']} | {x['해석']}", axis=1).tolist()
        selected_option = st.selectbox("수정할 항목을 선택하세요", ["선택 안함"] + options)

        if selected_option != "선택 안함":
            # "[1] involve..." 형식에서 번호 "1"만 추출
            selected_id = selected_option.split("]")[0][1:]
            
            # 추출한 번호에 해당하는 기존 데이터 불러오기
            target_row = df[df['번호'] == selected_id].iloc[0]
            
            with st.form("edit_sentence_form"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.text_input("번호 (수정 불가)", value=selected_id, disabled=True)
                    edit_word = st.text_input("단어", value=target_row['단어'])
                    edit_sent = st.text_input("문장", value=target_row['문장'])
                    
                with col2:
                    edit_pron = st.text_input("발음", value=target_row['발음'])
                    edit_mean = st.text_input("해석", value=target_row['해석'])
                    edit_memo1 = st.text_input("메모1", value=target_row['메모1'])
                    
                edit_memo2 = st.text_input("메모2", value=target_row['메모2'])
                
                update_submitted = st.form_submit_button("수정 내용 저장하기")
                
                if update_submitted:
                    if edit_word or edit_sent:
                        try:
                            # 1. 시트에서 해당 번호가 위치한 행 번호 계산 (표의 첫째 줄이 2번 행이므로 +2)
                            sheet_row = df.index[df['번호'] == selected_id][0] + 2
                            
                            # 2. 덮어씌울 새 데이터 배열
                            new_values = [selected_id, edit_word, edit_sent, edit_pron, edit_mean, edit_memo1, edit_memo2]
                            
                            # 3. gspread 안정성을 위해 해당 줄의 셀들을 가져와서 값 교체
                            cell_list = sheet.range(f"A{sheet_row}:G{sheet_row}")
                            for i, cell in enumerate(cell_list):
                                cell.value = new_values[i]
                            sheet.update_cells(cell_list)
                            
                            st.success("성공적으로 수정되었습니다! 🔄")
                            time.sleep(1)
                            st.rerun()
                        except Exception as e:
                            st.error(f"데이터 수정 중 오류가 발생했습니다. 상세: {e}")
                    else:
                        st.error("최소한 '단어'나 '문장' 중 하나는 입력해주세요.")
