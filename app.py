import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io

# --- [페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="TOmBOy94's English")

# --- [사용자 정의 디자인 (CSS)] ---
st.markdown("""
    <style>
    /* 전체 배경색 설정 */
    .stApp {
        background-color: #0B3D3D;
        color: #FFFFFF;
    }
    
    /* 헤더 스타일 */
    h1, h2, h3 {
        color: #FFFFFF !important;
    }
    
    /* 버튼 공통 스타일 (Pill shape) */
    div.stButton > button {
        border-radius: 50px !important;
        padding: 0.5rem 2rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease;
    }
    
    /* Primary 버튼 (흰색 배경, 어두운 글자) - data-testid 활용 */
    div.stButton > button[data-testid="baseButton-primary"] {
        background-color: #FFFFFF !important;
        color: #0B3D3D !important;
        border: none !important;
    }
    div.stButton > button[data-testid="baseButton-primary"]:hover {
        background-color: #F0F0F0 !important;
        transform: scale(1.05);
    }
    
    /* Secondary 버튼 (테두리만 있는 스타일) - data-testid 활용 */
    div.stButton > button[data-testid="baseButton-secondary"] {
        background-color: transparent !important;
        color: #FFFFFF !important;
        border: 1px solid #FFFFFF !important;
    }
    div.stButton > button[data-testid="baseButton-secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
        transform: scale(1.05);
    }
    
    /* 입력창 및 셀렉트박스 스타일 */
    .stTextInput > div > div > input, .stSelectbox > div > div > div {
        border-radius: 15px !important;
        background-color: rgba(255, 255, 255, 0.05) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    /* 카드 형태 리스트 아이템 스타일 */
    .data-row {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* 엑셀 다운로드 버튼 스타일링 */
    .stDownloadButton > button {
        background-color: #FFFFFF !important;
        color: #0B3D3D !important;
        border-radius: 50px !important;
        border: none !important;
    }

    /* 구분선 색상 */
    hr {
        border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- [보안 설정: 비밀번호] ---
LOGIN_PASSWORD = "0315" 

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

# 2. 데이터 불러오기
def load_dataframe(sheet):
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            if not data: 
                return pd.DataFrame(columns=['분류', '단어', '문장', '발음', '해석', '메모1', '메모2'])
            rows = data[1:]
            headers = ['분류', '단어', '문장', '발음', '해석', '메모1', '메모2']
            rows = [row + [""] * (7 - len(row)) for row in rows]
            rows = [row[:7] for row in rows]
            df = pd.DataFrame(rows, columns=headers)
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
            return df
        except Exception as e:
            time.sleep(1)
    raise Exception("구글 시트 응답 지연 (잠시 후 다시 시도해주세요)")

# 3. 팝업창 - 새 항목 추가
@st.dialog("➕ 새 항목 추가")
def add_dialog(sheet, full_df):
    unique_cats = full_df['분류'].unique().tolist() if not full_df.empty else []
    unique_cats = [x for x in unique_cats if x != '']
    try: unique_cats.sort(key=float)
    except: unique_cats.sort()

    with st.form("add_sentence_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_cat = st.selectbox("분류 선택 (기존)", ["(새로 입력)"] + unique_cats)
        with col2:
            new_cat = st.text_input("새 분류 입력")
        
        col3, col4 = st.columns(2)
        with col3:
            new_word = st.text_input("단어")
        with col4:
            new_sent = st.text_input("문장")
            
        col5, col6 = st.columns(2)
        with col5:
            new_pron = st.text_input("발음")
        with col6:
            new_mean = st.text_input("해석")
            
        new_memo1 = st.text_input("메모1")
        new_memo2 = st.text_input("메모2")
        
        submitted = st.form_submit_button("시트에 저장하기", use_container_width=True, type="primary")
        if submitted:
            final_cat = new_cat.strip() if new_cat.strip() else selected_cat
            if final_cat == "(새로 입력)": final_cat = ""
            if new_word or new_sent:
                try:
                    sheet.append_row([final_cat, new_word, new_sent, new_pron, new_mean, new_memo1, new_memo2])
                    st.success("저장되었습니다! 🔄")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"추가 오류: {e}")
            else: st.error("내용을 입력해주세요.")

# 4. 팝업창 - 수정 및 삭제
@st.dialog("✏️ 항목 수정 및 삭제")
def edit_dialog(idx, row_data, sheet, full_df):
    st.markdown(f"**[{row_data['분류']}] {row_data['단어']}** 데이터를 관리합니다.")
    unique_cats = [x for x in full_df['분류'].unique().tolist() if x != '']
    try: unique_cats.sort(key=float)
    except: unique_cats.sort()

    with st.form(f"edit_form_{idx}"):
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            current_cat = row_data['분류']
            if current_cat not in unique_cats: unique_cats.append(current_cat); unique_cats.sort()
            try: default_idx = unique_cats.index(current_cat) + 1
            except: default_idx = 0
            edit_selected_cat = st.selectbox("분류 선택 (기존)", ["(직접 입력)"] + unique_cats, index=default_idx)
        with row1_col2: edit_new_cat = st.text_input("분류 직접 입력")
        
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1: edit_word = st.text_input("단어", value=row_data['단어'])
        with row2_col2: edit_sent = st.text_input("문장", value=row_data['문장'])
        
        row3_col1, row3_col2 = st.columns(2)
        with row3_col1: edit_pron = st.text_input("발음", value=row_data['발음'])
        with row3_col2: edit_mean = st.text_input("해석", value=row_data['해석'])
        
        edit_memo1 = st.text_input("메모1", value=row_data['메모1'])
        edit_memo2 = st.text_input("메모2", value=row_data['메모2'])
        
        st.divider()
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1: update_submitted = st.form_submit_button("💾 수정 내용 저장", use_container_width=True, type="primary")
        with btn_col2: delete_submitted = st.form_submit_button("🗑️ 항목 삭제", use_container_width=True)
        
        if update_submitted:
            final_edit_cat = edit_new_cat.strip() if edit_new_cat.strip() else edit_selected_cat
            if final_edit_cat == "(직접 입력)": final_edit_cat = ""
            if edit_word or edit_sent:
                try:
                    sheet_row = idx + 2 
                    new_values = [final_edit_cat, edit_word, edit_sent, edit_pron, edit_mean, edit_memo1, edit_memo2]
                    cell_list = sheet.range(f"A{sheet_row}:G{sheet_row}")
                    for i, cell in enumerate(cell_list): cell.value = new_values[i]
                    sheet.update_cells(cell_list)
                    st.success("수정되었습니다! 🔄")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e: st.error(f"수정 오류: {e}")
        if delete_submitted:
            try:
                sheet.delete_rows(idx + 2)
                st.warning("삭제되었습니다. 🔄")
                time.sleep(0.5)
                st.rerun()
            except Exception as e: st.error(f"삭제 오류: {e}")

# --- [메인 로직 시작] ---

if "authenticated" not in st.session_state:
    st.session_state
