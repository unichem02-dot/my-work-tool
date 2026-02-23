import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time

# --- [페이지 기본 설정 (가로 넓게 쓰기)] ---
st.set_page_config(layout="wide", page_title="TOmBOy94's English")

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

# 3. 팝업창(모달) 띄우기 함수 - 새 항목 추가하기
@st.dialog("➕ 새 항목 추가")
def add_dialog(sheet, full_df):
    # 기존 분류 목록 가져오기
    unique_cats = full_df['분류'].unique().tolist() if not full_df.empty else []
    unique_cats = [x for x in unique_cats if x != '']
    try:
        unique_cats.sort(key=float)
    except ValueError:
        unique_cats.sort()

    with st.form("add_sentence_form", clear_on_submit=True):
        # 1번째 줄: 분류 선택 / 입력
        col1, col2 = st.columns(2)
        with col1:
            selected_cat = st.selectbox("분류 선택 (기존)", ["(새로 입력)"] + unique_cats)
        with col2:
            new_cat = st.text_input("새 분류 입력 (우선 적용됩니다)")
            
        # 2번째 줄: 단어 / 문장
        col3, col4 = st.columns(2)
        with col3:
            new_word = st.text_input("단어")
        with col4:
            new_sent = st.text_input("문장")
            
        # 3번째 줄: 발음 / 해석
        col5, col6 = st.columns(2)
        with col5:
            new_pron = st.text_input("발음")
        with col6:
            new_mean = st.text_input("해석")
            
        # 4, 5번째 줄: 메모1, 메모2
        new_memo1 = st.text_input("메모1")
        new_memo2 = st.text_input("메모2")
            
        submitted = st.form_submit_button("시트에 저장하기", use_container_width=True, type="primary")
        
        if submitted:
            final_cat = new_cat.strip() if new_cat.strip() else selected_cat
            if final_cat == "(새로 입력)":
                final_cat = ""
                
            if new_word or new_sent:
                try:
                    sheet.append_row([final_cat, new_word, new_sent, new_pron, new_mean, new_memo1, new_memo2])
                    st.success("성공적으로 저장되었습니다! 🔄")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"데이터 추가 중 오류가 발생했습니다. 상세: {e}")
            else:
                st.error("최소한 '단어'나 '문장' 중 하나는 입력해주세요.")

# 4. 팝업창(모달) 띄우기 함수 - 기존 항목 수정 및 삭제하기
@st.dialog("✏️ 항목 수정 및 삭제")
def edit_dialog(idx, row_data, sheet, full_df):
    st.markdown(f"**[{row_data['분류']}] {row_data['단어']}** 데이터를 관리합니다.")
    
    # 수정 창에서도 기존 분류 목록 활용
    unique_cats = full_df['분류'].unique().tolist() if not full_df.empty else []
    unique_cats = [x for x in unique_cats if x != '']
    try:
        unique_cats.sort(key=float)
    except ValueError:
        unique_cats.sort()

    with st.form(f"edit_form_{idx}"):
        # 1번째 줄: 분류 선택 / 입력 (추가 창과 동일한 배치)
        row1_col1, row1_col2 = st.columns(2)
        with row1_col1:
            # 현재 행의 분류가 드롭다운의 기본값이 되도록 설정
            current_cat = row_data['분류']
            if current_cat not in unique_cats:
                unique_cats.append(current_cat)
                unique_cats.sort()
            
            try:
                default_idx = unique_cats.index(current_cat) + 1
            except ValueError:
                default_idx = 0
                
            edit_selected_cat = st.selectbox("분류 선택 (기존)", ["(직접 입력)"] + unique_cats, index=default_idx)
        with row1_col2:
            # 새로 입력할 경우 사용
            edit_new_cat = st.text_input("분류 직접 입력 (변경 시에만 입력)")
            
        # 2번째 줄: 단어 / 문장
        row2_col1, row2_col2 = st.columns(2)
        with row2_col1:
            edit_word = st.text_input("단어", value=row_data['단어'])
        with row2_col2:
            edit_sent = st.text_input("문장", value=row_data['문장'])
            
        # 3번째 줄: 발음 / 해석
        row3_col1, row3_col2 = st.columns(2)
        with row3_col1:
            edit_pron = st.text_input("발음", value=row_data['발음'])
        with row3_col2:
            edit_mean = st.text_input("해석", value=row_data['해석'])
            
        # 4, 5번째 줄: 메모1, 메모2
        edit_memo1 = st.text_input("메모1", value=row_data['메모1'])
        edit_memo2 = st.text_input("메모2", value=row_data['메모2'])
        
        st.divider()
        
        # 하단 버튼 배치: 저장 및 삭제
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1:
            update_submitted = st.form_submit_button("💾 수정 내용 저장", use_container_width=True, type="primary")
        with btn_col2:
            delete_submitted = st.form_submit_button("🗑️ 항목 삭제", use_container_width=True)
        
        # 수정 로직
        if update_submitted:
            # 분류 결정 로직
            final_edit_cat = edit_new_cat.strip() if edit_new_cat.strip() else edit_selected_cat
            if final_edit_cat == "(직접 입력)":
                final_edit_cat = ""

            if edit_word or edit_sent:
                try:
                    sheet_row = idx + 2 
                    new_values = [final_edit_cat, edit_word, edit_sent, edit_pron, edit_mean, edit_memo1, edit_memo2]
                    
                    cell_list = sheet.range(f"A{sheet_row}:G{sheet_row}")
                    for i, cell in enumerate(cell_list):
                        cell.value = new_values[i]
                    sheet.update_cells(cell_list)
                    
                    st.success("수정되었습니다! 🔄")
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"수정 오류: {e}")
            else:
                st.error("입력값이 부족합니다.")
                
        # 삭제 로직
        if delete_submitted:
            try:
                sheet_row = idx + 2
                sheet.delete_rows(sheet_row)
                st.warning("항목이 삭제되었습니다. 🔄")
                time.sleep(0.5)
                st.rerun()
            except Exception as e:
                st.error(f"삭제 오류: {e}")

# --- [메인 앱 화면] ---
st.title("📚 TOmBOy94's English words and sentences")

data_loaded = False
try:
    sheet = get_sheet()
    df = load_dataframe(sheet)
    data_loaded = True
except Exception as e:
    st.error(f"구글 시트 데이터를 불러오는 중 오류가 발생했습니다.\n\n에러 내용: {e}")

if data_loaded:
    # --- [새 항목 추가 버튼] ---
    if st.button("➕ 새 항목 추가", type="primary", use_container_width=True):
        add_dialog(sheet, df)
        
    st.divider()

    # --- [검색 및 필터 구역] ---
    if 'filter_type' not in st.session_state:
        st.session_state.filter_type = '전체보기'

    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3, 2, 1, 1, 1])
    
    with col_h1:
        st.header("🔍 단어/문장 검색")
        
    with col_h2:
        st.write("") 
        unique_cats = df['분류'].unique().tolist()
        unique_cats = [x for x in unique_cats if x != '']
        try:
            unique_cats.sort(key=float)
        except ValueError:
            unique_cats.sort()
            
        selected_category = st.selectbox("분류", ["전체 분류"] + unique_cats, label_visibility="collapsed")
        
    with col_h3:
        st.write("")
        if st.button("단어", type="primary" if st.session_state.filter_type == '단어' else "secondary", use_container_width=True):
            st.session_state.filter_type = '단어'
            st.rerun()
            
    with col_h4:
        st.write("")
        if st.button("문장", type="primary" if st.session_state.filter_type == '문장' else "secondary", use_container_width=True):
            st.session_state.filter_type = '문장'
            st.rerun()
            
    with col_h5:
        st.write("")
        if st.button("전체보기", type="primary" if st.session_state.filter_type == '전체보기' else "secondary", use_container_width=True):
            st.session_state.filter_type = '전체보기'
            st.rerun()

    search_query = st.text_input("검색어를 입력하세요 (단어, 문장, 해석 등)")
    
    display_df = df.copy()

    if selected_category != "전체 분류":
        display_df = display_df[display_df['분류'] == selected_category]

    if st.session_state.filter_type == '단어':
        display_df = display_df[display_df['단어'] != '']
    elif st.session_state.filter_type == '문장':
        display_df = display_df[display_df['문장'] != '']

    if search_query:
        mask = pd.Series(False, index=display_df.index)
        search_columns = ['단어', '문장', '해석', '메모1', '메모2'] 
        for col in search_columns:
            if col in display_df.columns:
                mask |= display_df[col].astype(str).str.contains(search_query, case=False, na=False)
        display_df = display_df[mask]
    
    if not display_df.empty:
        if len(display_df) > 50:
            st.info(f"검색 결과가 너무 많습니다. 최근 추가된 50개만 표시합니다. (전체 {len(display_df)}개)")
            display_df = display_df.iloc[::-1].head(50) 
            
        col_ratio = [1, 2, 4, 2, 3, 3, 3, 1]
        header_cols = st.columns(col_ratio)
        header_cols[0].markdown("**분류**")
        header_cols[1].markdown("**단어**")
        header_cols[2].markdown("**문장**")
        header_cols[3].markdown("**발음**")
        header_cols[4].markdown("**해석**")
        header_cols[5].markdown("**메모1**")
        header_cols[6].markdown("**메모2**")
        header_cols[7].markdown("**수정**")
        st.divider()
        
        for idx, row in display_df.iterrows():
            cols = st.columns(col_ratio)
            cols[0].write(row['분류'])
            cols[1].markdown(f"<span style='font-size: 1.4em; font-weight: bold;'>{row['단어']}</span>", unsafe_allow_html=True)
            cols[2].markdown(f"<span style='font-size: 1.4em; font-weight: bold;'>{row['문장']}</span>", unsafe_allow_html=True)
            cols[3].write(row['발음'])
            cols[4].write(row['해석'])
            cols[5].write(row['메모1'])
            cols[6].write(row['메모2'])
            
            if cols[7].button("✏️", key=f"edit_btn_{idx}"):
                edit_dialog(idx, row, sheet, df) # 수정 창에서도 전체 df 전달
    else:
        st.warning(f"[{selected_category} / {st.session_state.filter_type}] 조건에 맞는 데이터가 없습니다.")
