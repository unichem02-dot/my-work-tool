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
                return pd.DataFrame(columns=['번호', '단어', '문장', '발음', '해석', '메모1', '메모2'])
                
            rows = data[1:]
            headers = ['번호', '단어', '문장', '발음', '해석', '메모1', '메모2']
            
            rows = [row + [""] * (7 - len(row)) for row in rows]
            rows = [row[:7] for row in rows]
                
            return pd.DataFrame(rows, columns=headers)
        except Exception as e:
            time.sleep(1)
            
    raise Exception("구글 시트 응답 지연 (잠시 후 다시 시도해주세요)")

# 3. 팝업창(모달) 띄우기 함수 - 새 항목 추가하기
@st.dialog("➕ 새 항목 추가")
def add_dialog(sheet, full_df):
    if full_df.empty:
        next_num = 1
    else:
        next_num = int(pd.to_numeric(full_df['번호'], errors='coerce').fillna(0).max()) + 1

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

# 4. 팝업창(모달) 띄우기 함수 - 기존 항목 수정하기
@st.dialog("✏️ 항목 수정")
def edit_dialog(row_data, sheet, full_df):
    st.markdown(f"**[{row_data['번호']}] {row_data['단어']}** 데이터를 수정합니다.")
    
    with st.form(f"edit_form_{row_data['번호']}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.text_input("번호 (수정 불가)", value=row_data['번호'], disabled=True)
            edit_word = st.text_input("단어", value=row_data['단어'])
            edit_sent = st.text_input("문장", value=row_data['문장'])
            
        with col2:
            edit_pron = st.text_input("발음", value=row_data['발음'])
            edit_mean = st.text_input("해석", value=row_data['해석'])
            edit_memo1 = st.text_input("메모1", value=row_data['메모1'])
            
        edit_memo2 = st.text_input("메모2", value=row_data['메모2'])
        
        update_submitted = st.form_submit_button("수정 내용 저장하기")
        
        if update_submitted:
            if edit_word or edit_sent:
                try:
                    selected_id = row_data['번호']
                    # 시트에서 해당 번호가 위치한 행 번호 계산
                    sheet_row = full_df.index[full_df['번호'] == selected_id][0] + 2
                    
                    # 덮어씌울 새 데이터 배열
                    new_values = [selected_id, edit_word, edit_sent, edit_pron, edit_mean, edit_memo1, edit_memo2]
                    
                    # gspread 업데이트
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
    # --- [새 항목 추가 버튼 (상단 배치)] ---
    if st.button("➕ 새 항목 추가", type="primary", use_container_width=True):
        add_dialog(sheet, df)
        
    st.divider()

    # --- [검색 기능 및 상단 필터 버튼] ---
    if 'filter_type' not in st.session_state:
        st.session_state.filter_type = '전체보기'

    col_h1, col_h2, col_h3, col_h4, col_h5 = st.columns([3, 2, 1, 1, 1])
    
    with col_h1:
        st.header("🔍 단어/문장 검색")
        
    # 💡 [신규] 번호(분류) 선택 리스트 추가
    with col_h2:
        st.write("") # 헤더와 높이 맞춤용
        # 번호 고유값 추출 (빈 값 제외)
        unique_nums = df['번호'].dropna().unique().tolist()
        unique_nums = [str(x).strip() for x in unique_nums if str(x).strip() != '']
        # 숫자로 정렬 시도 (실패시 문자로 정렬)
        try:
            unique_nums.sort(key=float)
        except ValueError:
            unique_nums.sort()
            
        selected_category = st.selectbox("분류(번호)", ["전체 분류"] + unique_nums, label_visibility="collapsed")
        
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

    # 💡 [신규] 0. 번호(분류) 선택에 따른 필터링 적용
    if selected_category != "전체 분류":
        display_df = display_df[display_df['번호'] == selected_category]

    # 1. 상단 버튼(단어/문장/전체보기)에 따른 1차 필터링
    if st.session_state.filter_type == '단어':
        # 단어 칸이 비어있지 않은 항목만 남김
        display_df = display_df[display_df['단어'].fillna('').str.strip() != '']
    elif st.session_state.filter_type == '문장':
        # 문장 칸이 비어있지 않은 항목만 남김
        display_df = display_df[display_df['문장'].fillna('').str.strip() != '']

    # 2. 검색어 입력 시 2차 필터링 적용
    if search_query:
        mask = pd.Series(False, index=display_df.index)
        search_columns = ['단어', '문장', '해석', '메모1', '메모2'] 
        for col in search_columns:
            if col in display_df.columns:
                mask |= display_df[col].astype(str).str.contains(search_query, case=False, na=False)
        display_df = display_df[mask]
    
    # 표(Dataframe) 대신, 직접 리스트를 그려서 우측에 버튼 배치
    if not display_df.empty:
        # 데이터가 너무 많아 렉이 걸리는 것을 방지 (가장 최신 50개만 보여줌)
        if len(display_df) > 50:
            st.info(f"검색 결과가 너무 많습니다. 최근 추가된 50개만 표시합니다. (전체 {len(display_df)}개)")
            display_df = display_df.iloc[::-1].head(50) # 역순 정렬 후 50개 컷
            
        # 테이블 헤더 디자인: 메모1, 메모2 컬럼 추가 (비율 조정)
        col_ratio = [1, 2, 4, 2, 3, 3, 3, 1]
        header_cols = st.columns(col_ratio)
        header_cols[0].markdown("**번호**")
        header_cols[1].markdown("**단어**")
        header_cols[2].markdown("**문장**")
        header_cols[3].markdown("**발음**")
        header_cols[4].markdown("**해석**")
        header_cols[5].markdown("**메모1**")
        header_cols[6].markdown("**메모2**")
        header_cols[7].markdown("**수정**")
        st.divider()
        
        # 각 행마다 데이터 및 수정 버튼 생성: 단어와 문장은 굵고 크게 표시
        for idx, row in display_df.iterrows():
            cols = st.columns(col_ratio)
            cols[0].write(row['번호'])
            
            # 단어와 문장 내용에 HTML/CSS를 적용하여 굵게, 크기 1.4배 적용
            cols[1].markdown(f"<span style='font-size: 1.4em; font-weight: bold;'>{row['단어']}</span>", unsafe_allow_html=True)
            cols[2].markdown(f"<span style='font-size: 1.4em; font-weight: bold;'>{row['문장']}</span>", unsafe_allow_html=True)
            
            cols[3].write(row['발음'])
            cols[4].write(row['해석'])
            cols[5].write(row['메모1'])
            cols[6].write(row['메모2'])
            
            # 수정 버튼 클릭 시 팝업(Dialog) 호출
            if cols[7].button("✏️", key=f"edit_btn_{idx}"):
                edit_dialog(row, sheet, df)
    else:
        st.warning(f"[{selected_category} / {st.session_state.filter_type}] 조건에 맞는 데이터가 없습니다.")
