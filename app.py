import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io
import math

# --- [페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="TOmBOy94's English")

# --- [사용자 정의 디자인 (CSS): 첨부이미지 스타일 완벽 적용 및 글씨 색상 오류 해결] ---
st.markdown("""
    <style>
    /* 1. 배경: 짙은 다크그린 (메인 & 팝업창) */
    [data-testid="stAppViewContainer"], 
    div[data-testid="stDialog"] > div,
    div[role="dialog"] > div {
        background-color: #224343 !important; 
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }

    /* 2. 화면 기본 글씨 강제 흰색 */
    .stMarkdown, .stMarkdown p, .stMarkdown span, 
    label, .stText {
        color: #FFFFFF !important;
    }

    /* ★ 팝업창 제목 포함 모든 헤딩 태그를 완벽한 흰색으로 고정 (가장 강력한 선택자 적용) ★ */
    h1, h2, h3, h4, h5, h6,
    h1 *, h2 *, h3 *, h4 *, h5 *, h6 *,
    div[role="dialog"] h2, div[role="dialog"] h2 *,
    div[role="dialog"] div[data-testid="stMarkdownContainer"] *,
    [data-testid="stDialog"] h2, [data-testid="stDialog"] h2 * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 3. ★ 핵심 수정: 입력창 뚜렷하게 (흰 바탕 + 검은 글씨 강제 고정) ★ */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important; /* 글자색을 무조건 검은색으로 */
        border-radius: 50px !important;
        padding-left: 15px !important;
        font-weight: 900 !important;
        border: none !important;
    }
    
    /* 드롭다운(Selectbox) 뚜렷하게 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: 50px !important;
        border: none !important;
    }
    .stSelectbox div[data-baseweb="select"] * {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
        font-weight: bold !important;
    }

    /* 팝업창 내부 폼(Form) 테두리 */
    [data-testid="stForm"] {
        background-color: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
    }

    /* 팝업창 닫기 버튼 (X) 완벽한 흰색 */
    button[aria-label="Close"], button[aria-label="Close"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    /* 4. --- [버튼 공통: 완벽한 알약(Pill) 모양] --- */
    button {
        border-radius: 50px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
        border: 2px solid transparent !important;
    }

    /* 5. ★ Primary 버튼 완벽 덮어쓰기 (흰 바탕 + 짙은 녹색 글씨) ★ */
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        border-color: #FFFFFF !important;
    }
    button[kind="primary"] p, 
    button[kind="primary"] span, 
    button[kind="primary"] div {
        color: #224343 !important; /* 글씨색 다크그린 */
        -webkit-text-fill-color: #224343 !important;
    }
    button[kind="primary"]:hover {
        transform: scale(1.05);
        background-color: #EAEAEA !important;
    }

    /* 6. ★ Secondary 버튼 완벽 덮어쓰기 (투명 바탕 + 흰색 테두리 및 글씨) ★ */
    button[kind="secondary"] {
        background-color: transparent !important;
        border-color: #FFFFFF !important; 
    }
    button[kind="secondary"] p, 
    button[kind="secondary"] span, 
    button[kind="secondary"] div {
        color: #FFFFFF !important; 
        -webkit-text-fill-color: #FFFFFF !important;
    }
    button[kind="secondary"]:hover {
        transform: scale(1.05);
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 엑셀 다운로드 버튼 (Secondary 스타일 복사) */
    .stDownloadButton > button {
        background-color: transparent !important;
        border-color: #FFFFFF !important;
        border-radius: 50px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }
    .stDownloadButton > button p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    .stDownloadButton > button:hover {
        transform: scale(1.05);
        background-color: rgba(255, 255, 255, 0.1) !important;
    }
    
    /* 구분선 흐리게 */
    hr {
        border-top: 1px solid rgba(255, 255, 255, 0.2) !important;
        margin-top: 10px !important;
        margin-bottom: 10px !important;
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

# 2. 데이터 불러오기 (6열 구조로 변경)
def load_dataframe(sheet):
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            if not data: 
                return pd.DataFrame(columns=['분류', '단어-문장', '발음', '해석', '메모1', '메모2'])
            rows = data[1:]
            headers = ['분류', '단어-문장', '발음', '해석', '메모1', '메모2']
            # 6열로 패딩 및 자르기
            rows = [row + [""] * (6 - len(row)) for row in rows]
            rows = [row[:6] for row in rows]
            df = pd.DataFrame(rows, columns=headers)
            for col in df.columns:
                df[col] = df[col].astype(str).str.strip()
            return df
        except Exception as e:
            time.sleep(1)
    raise Exception("구글 시트 응답 지연 (잠시 후 다시 시도해주세요)")

# 3. 팝업창 - 새 항목 추가 (단어/문장 통합)
@st.dialog("새 항목 추가")
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
            new_cat = st.text_input("새 분류 입력 (우선 적용됩니다)")
        
        # 통합된 단어-문장 필드 (한 줄 전체 차지)
        new_word_sent = st.text_input("단어-문장")
            
        col3, col4 = st.columns(2)
        with col3:
            new_pron = st.text_input("발음")
        with col4:
            new_mean = st.text_input("해석")
            
        new_memo1 = st.text_input("메모1")
        new_memo2 = st.text_input("메모2")
        
        submitted = st.form_submit_button("시트에 저장하기", use_container_width=True, type="primary")
        if submitted:
            final_cat = new_cat.strip() if new_cat.strip() else selected_cat
            if final_cat == "(새로 입력)": final_cat = ""
            if new_word_sent:
                try:
                    sheet.append_row([final_cat, new_word_sent, new_pron, new_mean, new_memo1, new_memo2])
                    st.success("저장되었습니다! 🔄")
                    time.sleep(1)
                    st.rerun()
                except Exception as e: st.error(f"추가 오류: {e}")
            else: st.error("내용을 입력해주세요.")

# 4. 팝업창 - 수정 및 삭제 (단어/문장 통합)
@st.dialog("항목 수정 및 삭제")
def edit_dialog(idx, row_data, sheet, full_df):
    st.markdown(f"**[{row_data['분류']}] {row_data['단어-문장']}** 데이터를 관리합니다.")
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
        with row1_col2: edit_new_cat = st.text_input("분류 직접 입력 (변경 시에만 입력)")
        
        # 통합된 단어-문장 필드
        edit_word_sent = st.text_input("단어-문장", value=row_data['단어-문장'])
        
        row3_col1, row3_col2 = st.columns(2)
        with row3_col1: edit_pron = st.text_input("발음", value=row_data['발음'])
        with row3_col2: edit_mean = st.text_input("해석", value=row_data['해석'])
        
        edit_memo1 = st.text_input("메모1", value=row_data['메모1'])
        edit_memo2 = st.text_input("메모2", value=row_data['메모2'])
        
        st.divider()
        btn_col1, btn_col2 = st.columns(2)
        with btn_col1: update_submitted = st.form_submit_button("💾 수정 내용 저장", use_container_width=True, type="primary")
        with btn_col2: delete_submitted = st.form_submit_button("🗑️ 항목 삭제", use_container_width=True, type="secondary")
        
        if update_submitted:
            final_edit_cat = edit_new_cat.strip() if edit_new_cat.strip() else edit_selected_cat
            if final_edit_cat == "(직접 입력)": final_edit_cat = ""
            if edit_word_sent:
                try:
                    sheet_row = idx + 2 
                    new_values = [final_edit_cat, edit_word_sent, edit_pron, edit_mean, edit_memo1, edit_memo2]
                    # F열까지 6개 열 업데이트
                    cell_list = sheet.range(f"A{sheet_row}:F{sheet_row}")
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
    st.session_state.authenticated = False

# 타이틀 및 로그아웃 버튼 가로 배치
col_title, col_auth = st.columns([7, 2])
with col_title:
    # ★ 이메일 링크 자동 변환을 막기 위해 HTML로 직접 타이틀을 렌더링합니다 ★
    st.markdown("""
        <h1 style='padding-top: 0.5rem; font-size: 2.2rem; font-weight: 700; color: #FFFFFF;'>
            TOmBOy94's English words and sentences : lodus11st<span>@</span>naver.com
        </h1>
    """, unsafe_allow_html=True)

with col_auth:
    if not st.session_state.authenticated:
        with st.expander("🔐 관리자 로그인"):
            password_input = st.text_input("Password", type="password")
            if st.button("로그인", use_container_width=True, type="primary"):
                if password_input == LOGIN_PASSWORD:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("비밀번호 오류")
    else:
        st.write("")
        st.write("")
        if st.button("🔓 로그아웃", use_container_width=True, type="secondary"):
            st.session_state.authenticated = False
            st.rerun()

data_loaded = False
try:
    sheet = get_sheet()
    df = load_dataframe(sheet)
    data_loaded = True
except Exception as e:
    st.error(f"데이터 연결 오류: {e}")

if data_loaded:
    st.divider()

    # 로그인 상태에 따라 컬럼을 동적으로 분할 (필터 버튼들을 제거하고 심플하게 유지)
    if st.session_state.authenticated:
        cols = st.columns([1.5, 1.2, 3.0, 1.5, 1.5])
        col_add = cols[0]
        col_h1, col_h2, col_h3, col_dl = cols[1:]
        
        with col_add:
            if st.button("➕ 새 항목 추가", type="primary", use_container_width=True):
                add_dialog(sheet, df)
    else:
        cols = st.columns([1.2, 3.0, 1.5, 1.5])
        col_h1, col_h2, col_h3, col_dl = cols
    
    with col_h1: 
        st.subheader("🔍 검색")
        
    with col_h2:
        search_query = st.text_input("검색어", placeholder="검색어를 입력하세요...", label_visibility="collapsed")
        
    with col_h3:
        unique_cats = [x for x in df['분류'].unique().tolist() if x != '']
        try: unique_cats.sort(key=float)
        except: unique_cats.sort()
        selected_category = st.selectbox("분류", ["전체 분류"] + unique_cats, label_visibility="collapsed")
        
    # 필터링 로직
    display_df = df.copy()
    if selected_category != "전체 분류": 
        display_df = display_df[display_df['분류'] == selected_category]
    
    if search_query:
        mask = display_df.apply(lambda r: r.astype(str).str.contains(search_query, case=False).any(), axis=1)
        display_df = display_df[mask]

    # 최신 등록 항목이 위로 올라오도록 정렬 (인덱스는 유지해야 수정/삭제가 올바른 열을 찾아감)
    display_df = display_df.iloc[::-1]

    # ★ CSV 내보내기는 전체 필터링된 내용을 대상으로 생성합니다. ★
    with col_dl:
        if st.session_state.authenticated:
            csv_data = display_df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 CSV 다운로드",
                data=csv_data,
                file_name=f"English_Data_{time.strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )

    if not display_df.empty:
        # --- [페이지네이션 로직] ---
        ITEMS_PER_PAGE = 100
        total_items = len(display_df)
        total_pages = math.ceil(total_items / ITEMS_PER_PAGE) if total_items > 0 else 1

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 1

        # 검색/필터 변경으로 페이지가 초과되면 1페이지로 복구
        if st.session_state.current_page > total_pages or st.session_state.current_page < 1:
            st.session_state.current_page = 1

        # 현재 페이지에 맞게 100개만 슬라이싱
        start_idx = (st.session_state.current_page - 1) * ITEMS_PER_PAGE
        end_idx = start_idx + ITEMS_PER_PAGE
        page_df = display_df.iloc[start_idx:end_idx]

        # ★ st.info 대신 완벽하게 흰색이 보장되는 HTML(st.markdown) 방식으로 교체 ★
        st.markdown(f"""
            <div style='color: #FFFFFF !important; font-weight: bold; margin-bottom: 15px; font-size: 1.1em;'>
                총 {total_items}개의 항목 중 {start_idx + 1} ~ {min(end_idx, total_items)}번째 표시 중 
                (현재 페이지: {st.session_state.current_page} / {total_pages})
            </div>
        """, unsafe_allow_html=True)
        
        # 헤더 출력 부분 (6열에 맞춘 비율)
        if st.session_state.authenticated:
            col_ratio = [1.2, 4, 2, 2.5, 2.5, 2.5, 1]
            h_labels = ["분류", "단어-문장", "발음", "해석", "메모1", "메모2", "수정"]
        else:
            col_ratio = [1.2, 4, 2, 2.5, 2.5, 2.5]
            h_labels = ["분류", "단어-문장", "발음", "해석", "메모1", "메모2"]

        header_cols = st.columns(col_ratio)
        for i, label in enumerate(h_labels): header_cols[i].markdown(f"**{label}**")
        st.divider()
        
        # 데이터 출력 (1페이지당 100개)
        for idx, row in page_df.iterrows():
            cols = st.columns(col_ratio)
            cols[0].write(row['분류'])
            cols[1].markdown(f"<span style='font-size: 1.4em; font-weight: bold;'>{row['단어-문장']}</span>", unsafe_allow_html=True)
            cols[2].write(row['발음'])
            cols[3].write(row['해석'])
            cols[4].write(row['메모1'])
            cols[5].write(row['메모2'])
            
            if st.session_state.authenticated:
                if cols[6].button("✏️", key=f"edit_{idx}", type="secondary"):
                    edit_dialog(idx, row, sheet, df)

            # 💡 컨텐츠 라인마다 간격을 반으로 확 줄인 점선 추가 (기본 여백 상쇄용 음수 마진 적용)
            st.markdown("<div style='border-bottom: 1px dotted rgba(255, 255, 255, 0.3); margin-top: -10px; margin-bottom: 5px;'></div>", unsafe_allow_html=True)

        # --- [하단 페이지 번호 이동 컨트롤 UI] ---
        if total_pages > 1:
            st.write("") # 상단 여백
            
            # 중앙 정렬을 위해 표시할 페이지 번호를 계산 (현재 페이지 기준 앞뒤 2개씩, 총 5개)
            start_page = max(1, st.session_state.current_page - 2)
            end_page = min(total_pages, start_page + 4)
            start_page = max(1, end_page - 4) # 끝 페이지에 도달했을 때 앞쪽 버튼을 채워줌
            
            visible_pages = list(range(start_page, end_page + 1))
            
            # 레이아웃을 동적으로 만들어 항상 중앙에 위치하도록 함 [여백, 이전, 번호들..., 다음, 여백]
            cols_layout = [3, 1] + [1] * len(visible_pages) + [1, 3]
            page_cols = st.columns(cols_layout)
            
            with page_cols[1]:
                if st.button("◀", key="prev_page", disabled=(st.session_state.current_page == 1), use_container_width=True):
                    st.session_state.current_page -= 1
                    st.rerun()
                    
            for i, p in enumerate(visible_pages):
                with page_cols[i + 2]:
                    if st.button(str(p), key=f"page_btn_{p}", type="primary" if p == st.session_state.current_page else "secondary", use_container_width=True):
                        st.session_state.current_page = p
                        st.rerun()
                        
            with page_cols[len(visible_pages) + 2]:
                if st.button("▶", key="next_page", disabled=(st.session_state.current_page == total_pages), use_container_width=True):
                    st.session_state.current_page += 1
                    st.rerun()
    else:
        st.warning("표시할 데이터가 없습니다.")
