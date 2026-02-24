import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io
import math

# --- [페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="TOmBOy94's English")

# --- [사용자 정의 디자인 (CSS) 및 음성 출력 스크립트] ---
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

    /* ★ 팝업창 제목 포함 모든 헤딩 태그를 완벽한 흰색으로 고정 ★ */
    h1, h2, h3, h4, h5, h6,
    h1 *, h2 *, h3 *, h4 *, h5 *, h6 * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 3. ★ 모바일 입력 오류 해결 및 입력창 스타일 ★ */
    .stTextInput input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border-radius: 50px !important;
        padding-left: 15px !important;
        font-weight: 700 !important;
        border: 1px solid #FFFFFF !important;
        pointer-events: auto !important;
        user-select: text !important;
    }
    
    /* 패스워드 필드 특화 */
    input[type="password"] {
        color: #000000 !important;
        -webkit-text-fill-color: #000000 !important;
    }

    /* ★ 비밀번호 눈동자 아이콘 제거 ★ */
    div[data-testid="stTextInput"] button {
        display: none !important;
    }
    
    /* 드롭다운(Selectbox) 스타일 */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: 50px !important;
        border: none !important;
    }
    .stSelectbox div[data-baseweb="select"] * {
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* 팝업창 폼 테두리 */
    [data-testid="stForm"] {
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 15px !important;
    }

    /* 4. 버튼 공통 스타일 (Pill) */
    button {
        border-radius: 50px !important;
        padding: 0.5rem 1.5rem !important;
        font-weight: 700 !important;
        transition: all 0.3s ease !important;
    }

    /* Primary 버튼 */
    button[kind="primary"] {
        background-color: #FFFFFF !important;
        color: #224343 !important;
    }
    
    /* Secondary 버튼 */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 2px solid #FFFFFF !important;
        color: #FFFFFF !important;
    }
    
    /* 구분선 */
    hr {
        border-top: 1px dotted rgba(255, 255, 255, 0.3) !important;
    }

    /* ★ 토글 스위치 화이트 라벨 강력 고정 ★ */
    .stToggle label p, 
    div[data-testid="stToggle"] label p,
    div[data-testid="stToggle"] label div,
    div[data-testid="stToggle"] * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        font-weight: bold !important;
    }

    /* ★ 팝업창(Dialog) 최상단 제목 완벽 흰색 고정 ★ */
    div[data-testid="stDialog"] header h2,
    div[data-testid="stDialog"] header h2 *,
    div[data-testid="stDialog"] header p,
    div[data-testid="stDialog"] header div,
    div[role="dialog"] header * {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    </style>
    
    <script>
    // 브라우저 소리 잠금 해제 상태 확인
    let speechReady = false;

    // 페이지 어디든 클릭하면 음성 엔진 활성화 (브라우저 정책 대응)
    document.addEventListener('click', function() {
        if (!speechReady) {
            window.speechSynthesis.cancel();
            speechReady = true;
            console.log("음성 엔진 활성화됨");
        }
    }, { once: true });

    function speakText(text, lang) {
        if (!text || text.trim() === "") return;

        // 즉시 반응을 위해 진행 중인 음성 취소
        window.speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = lang; 
        utterance.rate = 1.0; 
        utterance.pitch = 1.0;
        
        // 지연 시간 최소화를 위해 즉시 실행
        setTimeout(() => {
            window.speechSynthesis.speak(utterance);
        }, 50);
    }
    </script>
    """, unsafe_allow_html=True)

# --- [보안 설정] ---
LOGIN_PASSWORD = "0315" 

@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

def get_sheet():
    return init_connection().open("English_Sentences").sheet1

def load_dataframe(sheet):
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            if not data: return pd.DataFrame(columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])
            rows = [row + [""] * (6 - len(row)) for row in data[1:]]
            df = pd.DataFrame(rows, columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])
            for col in df.columns: df[col] = df[col].astype(str).str.strip()
            return df
        except: time.sleep(1)
    raise Exception("데이터 로드 실패")

@st.dialog("새 항목 추가")
def add_dialog(sheet, full_df):
    unique_cats = sorted([x for x in full_df['분류'].unique().tolist() if x != ''])
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        selected_cat = c1.selectbox("기존 분류", ["(새로 입력)"] + unique_cats)
        new_cat = c2.text_input("새 분류 입력")
        word_sent = st.text_input("단어-문장")
        c3, c4 = st.columns(2)
        mean = c3.text_input("해석")
        pron = c4.text_input("발음")
        m1 = st.text_input("메모1")
        m2 = st.text_input("메모2")
        if st.form_submit_button("저장하기", use_container_width=True, type="primary"):
            final_cat = new_cat.strip() if new_cat.strip() else (selected_cat if selected_cat != "(새로 입력)" else "")
            if word_sent:
                sheet.append_row([final_cat, word_sent, mean, pron, m1, m2])
                st.success("저장 완료!"); time.sleep(1); st.rerun()

@st.dialog("항목 수정 및 삭제")
def edit_dialog(idx, row_data, sheet, full_df):
    unique_cats = sorted([x for x in full_df['분류'].unique().tolist() if x != ''])
    with st.form(f"edit_{idx}"):
        c1, c2 = st.columns(2)
        edit_cat = c1.selectbox("분류", unique_cats, index=unique_cats.index(row_data['분류']) if row_data['분류'] in unique_cats else 0)
        new_cat = c2.text_input("분류 직접 수정")
        word_sent = st.text_input("단어-문장", value=row_data['단어-문장'])
        c3, c4 = st.columns(2)
        mean = c3.text_input("해석", value=row_data['해석'])
        pron = c4.text_input("발음", value=row_data['발음'])
        m1 = st.text_input("메모1", value=row_data['메모1'])
        m2 = st.text_input("메모2", value=row_data['메모2'])
        b1, b2 = st.columns(2)
        if b1.form_submit_button("💾 저장", use_container_width=True, type="primary"):
            final_cat = new_cat.strip() if new_cat.strip() else edit_cat
            sheet.update(f"A{idx+2}:F{idx+2}", [[final_cat, word_sent, mean, pron, m1, m2]])
            st.rerun()
        if b2.form_submit_button("🗑️ 삭제", use_container_width=True):
            sheet.delete_rows(idx + 2); st.rerun()

# --- [메인 실행] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False

col_title, col_auth = st.columns([7, 2])
with col_title:
    st.markdown("<h1 style='color:#FFF;'>TOmBOy94's English words and sentences : lodus11st@naver.com</h1>", unsafe_allow_html=True)
with col_auth:
    if not st.session_state.authenticated:
        with st.expander("🔐 로그인"):
            if st.text_input("Password", type="password") == LOGIN_PASSWORD: 
                st.session_state.authenticated = True; st.rerun()
    else:
        if st.button("🔓 로그아웃", use_container_width=True, type="secondary"): 
            st.session_state.authenticated = False; st.rerun()

try:
    sheet = get_sheet(); df = load_dataframe(sheet)
    st.divider()
    
    # 컨트롤바
    if st.session_state.authenticated:
        cb = st.columns([1.5, 1.2, 0.3, 1.5, 3.7, 1.5])
        if cb[0].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(sheet, df)
        is_simple = cb[1].toggle("심플모드")
        sel_cat = cb[3].selectbox("분류", ["전체 분류"] + sorted(df['분류'].unique().tolist()), label_visibility="collapsed")
        search = cb[4].text_input("검색", placeholder="검색어 입력...", label_visibility="collapsed")
        cb[5].download_button("📥 CSV", df.to_csv(index=False).encode('utf-8-sig'), "data.csv", use_container_width=True)
    else:
        cb = st.columns([1.2, 1.5, 4.0, 1.5])
        is_simple = cb[0].toggle("심플모드")
        sel_cat = cb[1].selectbox("분류", ["전체 분류"] + sorted(df['분류'].unique().tolist()), label_visibility="collapsed")
        search = cb[2].text_input("검색", label_visibility="collapsed")

    # 필터링
    d_df = df.copy()
    if sel_cat != "전체 분류": d_df = d_df[d_df['분류'] == sel_cat]
    if search: d_df = d_df[d_df.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]
    d_df = d_df.iloc[::-1]

    # 페이지네이션
    total = len(d_df)
    pages = math.ceil(total/100) if total > 0 else 1
    curr_p = st.session_state.get('curr_p', 1)
    if curr_p > pages: curr_p = 1
    
    st.markdown(f"<p style='color:#FFF;font-weight:bold;'>총 {total}개 (페이지: {curr_p}/{pages})</p>", unsafe_allow_html=True)
    
    # 리스트 출력
    ratio = [1.5, 6, 4.5, 1] if is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1]
    labels = ["분류", "단어-문장", "해석", "수정"] if is_simple else ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
    
    h_cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
    for i, l in enumerate(labels if st.session_state.authenticated else labels[:-1]): h_cols[i].write(f"**{l}**")
    st.divider()

    for idx, row in d_df.iloc[(curr_p-1)*100 : curr_p*100].iterrows():
        cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1])
        
        # 텍스트 이스케이프 및 줄바꿈 처리 (JS 오류 방지 및 전체 문장 낭독 보장)
        txt_en = row['단어-문장'].replace("'", "\\'").replace('"', '&quot;').replace("\n", " ").strip()
        txt_ko = row['해석'].replace("'", "\\'").replace('"', '&quot;').replace("\n", " ").strip()
        
        cols[0].write(row['분류'])
        
        # 영어 발음 (단어-문장)
        cols[1].markdown(f"""
            <span style='font-size:2.0em;font-weight:bold;cursor:pointer;display:block;' 
                  onmouseenter=\"speakText('{txt_en}', 'en-US')\">
                {row['단어-문장']}
            </span>
        """, unsafe_allow_html=True)
        
        # 한국어 발음 (해석)
        cols[2].markdown(f"""
            <span style='font-size:1.5em;cursor:pointer;display:block;' 
                  onmouseenter=\"speakText('{txt_ko}', 'ko-KR')\">
                {row['해석']}
            </span>
        """, unsafe_allow_html=True)
        
        if not is_simple:
            cols[3].write(row['발음'])
            cols[4].write(row['메모1'])
            cols[5].write(row['메모2'])
            if st.session_state.authenticated:
                if cols[6].button("✏️", key=f"e_{idx}"): edit_dialog(idx, row, sheet, df)
        elif st.session_state.authenticated:
            if cols[3].button("✏️", key=f"es_{idx}"): edit_dialog(idx, row, sheet, df)
        
        st.markdown("<div style='border-bottom:1px dotted rgba(255,255,255,0.2);margin-top:-10px;margin-bottom:5px;'></div>", unsafe_allow_html=True)

    # 하단 페이지네이션
    if pages > 1:
        p_cols = st.columns([5, 1, 1, 1, 5])
        if p_cols[1].button("◀") and curr_p > 1: st.session_state.curr_p = curr_p - 1; st.rerun()
        p_cols[2].write(f"**{curr_p}**")
        if p_cols[3].button("▶") and curr_p < pages: st.session_state.curr_p = curr_p + 1; st.rerun()

except Exception as e:
    st.error(f"오류 발생: {e}")
