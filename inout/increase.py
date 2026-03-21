import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import math
import time

# 1. 페이지 기본 설정 (와이드 모드 유지)
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# ==========================================
# 🎨 깔끔한 스트림릿 순정 디자인 + 폰트 30% 확대 CSS
# ==========================================
st.markdown("""
    <style>
    /* 기본 메뉴 및 푸터 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 전체 여백 최적화 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 95%;
    }
    
    /* 텍스트 크기 30% 확대 적용 */
    .stMarkdown p, .stMarkdown li, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 { 
        font-size: 1.15rem !important; 
    }
    .stMultiSelect label, .stTextInput label {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #333333;
    }
    /* 요약 지표 글자 크기 조정 */
    div[data-testid="stMetricValue"] { font-size: 2.3rem !important; }
    div[data-testid="stMetricLabel"] { font-size: 1.15rem !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 로그인 기능 (비밀번호 확인 + 3시간 세션 유지)
# ==========================================
def check_password():
    TIMEOUT_SECONDS = 10800  # 3시간 유지
    
    if st.query_params.get("auth") == "true":
        try:
            login_ts = float(st.query_params.get("ts", 0))
            if time.time() - login_ts < TIMEOUT_SECONDS:
                st.session_state["authenticated"] = True
            else:
                st.session_state["authenticated"] = False
                st.query_params.clear()
        except:
            st.session_state["authenticated"] = False
            st.query_params.clear()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔒 보안 접속")
            st.info("유니매입가격정보를 열람하시려면 비밀번호를 입력해주세요.")
            
            with st.form("login_form"):
                pwd = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
                submit = st.form_submit_button("확인", use_container_width=True)
                
                if submit:
                    if pwd == str(st.secrets.get("tom_password", "")):
                        st.session_state["authenticated"] = True
                        st.query_params["auth"] = "true"
                        st.query_params["ts"] = str(time.time())
                        st.rerun()
                    else:
                        st.error("🚨 비밀번호가 일치하지 않습니다.")
        return False
    return True

if not check_password():
    st.stop()

# 2. 구글 시트 데이터 불러오기 (실시간 5초 캐시 유지)
@st.cache_data(ttl=5)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="시트1", ttl=5) 
    
    # 에러 방지: 완전 빈 행 제거 및 이름 없는 열 제거
    df = df.dropna(how="all")
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')] 
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    data = load_data()
except Exception as e:
    st.error("구글 시트를 불러오는 데 실패했습니다. '.streamlit/secrets.toml' 설정과 공유 상태를 확인해주세요.")
    st.stop()

col_vendor = "업체명"
col_item = "물품명"
col_date = "인상날짜"

required_cols = [col_vendor, col_item, col_date]
missing_cols = [col for col in required_cols if col not in data.columns]

if missing_cols:
    st.error(f"🚨 컬럼명 오류: 구글 시트에서 '{', '.join(missing_cols)}' 열을 찾을 수 없습니다.")
    st.info(f"💡 현재 시트에 있는 실제 1열 제목들: {', '.join(map(str, data.columns))}")
    st.stop()

data = data.fillna("")

# ==========================================
# UI 레이아웃 시작 (사진과 완벽하게 동일한 순정 디자인)
# ==========================================

# 상단 헤더 영역
st.markdown("<br>", unsafe_allow_html=True)
header_col1, header_col2 = st.columns([5, 1])

with header_col1:
    st.markdown("## 📈 유니매입가격정보 (인상공문 현황)")
    st.markdown("단가 인상 내역을 **업체명, 물품명, 날짜**로 쉽고 빠르게 교차 검색해 보세요.")

with header_col2:
    st.markdown("<div style='text-align: right; font-size: 0.9rem; color: #28a745; margin-bottom: 5px; font-weight: 600;'>🟢 로그인됨</div>", unsafe_allow_html=True)
    
    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        if st.button("🔄 새로고침", use_container_width=True, help="최신 구글 시트 데이터 가져오기"):
            st.cache_data.clear()
            st.rerun()
    with btn_col2:
        if st.button("🔓 로그아웃", use_container_width=True):
            st.session_state["authenticated"] = False
            st.query_params.clear()
            st.rerun()

st.markdown("---")

# 1. 상세 검색 영역 (깔끔한 3단 콤보)
st.markdown("#### 🔍 상세 검색")
search_col1, search_col2, search_col3 = st.columns(3)

with search_col1:
    vendor_raw = [str(v).strip() for v in data[col_vendor].unique() if str(v).strip() != ""]
    vendor_list = ["전체"] + sorted(vendor_raw)
    selected_vendors = st.multiselect("🏢 업체명 선택", vendor_list, default=["전체"])

with search_col2:
    search_item = st.text_input("📦 물품명 검색", placeholder="예: 황산, 소다 등 부분 검색 가능")

with search_col3:
    date_raw = [str(d).strip() for d in data[col_date].unique() if str(d).strip() != ""]
    date_list = ["전체"] + sorted(date_raw, reverse=True)
    selected_dates = st.multiselect("📅 인상날짜 선택", date_list, default=["전체"])

# 2. 필터링 로직
filtered_df = data.copy()

if "전체" not in selected_vendors and len(selected_vendors) > 0:
    filtered_df = filtered_df[filtered_df[col_vendor].isin(selected_vendors)]

if "전체" not in selected_dates and len(selected_dates) > 0:
    filtered_df = filtered_df[filtered_df[col_date].astype(str).str.strip().isin(selected_dates)]

if search_item:
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(search_item, case=False, na=False)]

# 초기 정렬(Python)
sort_cols = [c for c in [col_date, col_vendor, col_item] if c in filtered_df.columns]
if sort_cols:
    asc_rules = [False if c == col_date else True for c in sort_cols]
    filtered_df = filtered_df.sort_values(by=sort_cols, ascending=asc_rules)

st.markdown("<br>", unsafe_allow_html=True)

# 3. 요약 지표 (Metrics) - 순정 디자인
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="총 검색된 건수", value=f"{len(filtered_df):,} 건")
with col2:
    if not filtered_df.empty and col_date in filtered_df.columns:
        valid_dates = [d for d in filtered_df[col_date].tolist() if str(d).strip() != ""]
        latest_date = max(valid_dates) if valid_dates else "-"
        st.metric(label="최근 인상 날짜", value=str(latest_date))
    else:
        st.metric(label="최근 인상 날짜", value="-")
with col3:
    if not filtered_df.empty:
        valid_vendors = [v for v in filtered_df[col_vendor].unique() if str(v).strip() != ""]
        st.metric(label="검색된 업체 수", value=f"{len(valid_vendors):,} 개사")
    else:
        st.metric(label="검색된 업체 수", value="0 개사")

st.markdown("---")
st.markdown("#### 📋 상세 내역 (표 제목을 클릭하면 정렬됩니다)")

# ==========================================
# 4. 데이터프레임 (스트림릿 순정 기능 사용 - 오류 없음, 클릭 정렬 지원)
# ==========================================
if filtered_df.empty:
    st.warning("👀 검색 조건에 맞는 데이터가 없습니다. 다른 조건으로 검색해 보세요.")
else:
    ROWS_PER_PAGE = 100
    total_pages = math.ceil(len(filtered_df) / ROWS_PER_PAGE)

    # 검색 조건 변경 시 1페이지로 자동 초기화
    filter_hash = hash(str(selected_vendors) + str(search_item) + str(selected_dates))
    if st.session_state.get('last_filter_hash') != filter_hash:
        st.session_state.current_page = 1
        st.session_state.last_filter_hash = filter_hash

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
        
    start_idx = (st.session_state.current_page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    
    # 현재 페이지에 띄울 100개 데이터
    display_df = filtered_df.iloc[start_idx:end_idx].copy()
    
    # --- 물품명, 인상폭 열을 굵은 글씨로 설정하는 안전한 로직 ---
    styled_df = display_df.style
    bold_cols = [c for c in ["물품명", "인상폭"] if c in display_df.columns]
    
    if bold_cols:
        # 지정된 열만 폰트 굵게 처리 (에러 없는 Pandas 고유 기능)
        styled_df = styled_df.map(lambda _: 'font-weight: 900;', subset=bold_cols)
    
    # 100개가 스크롤 없이 다 보이도록 높이 자동 계산 (1줄 약 35px + 헤더 40px)
    table_height = (len(display_df) * 35) + 40
    
    # 스트림릿 순정 표출 (자동 정렬 기능 포함)
    st.dataframe(
        styled_df, 
        use_container_width=True, 
        hide_index=True, 
        height=table_height
    )

    # 페이지 이동(Pagination) 하단 버튼 UI
    if total_pages > 1:
        st.markdown("<br>", unsafe_allow_html=True)
        page_cols = st.columns([4, 1, 1, 1, 4])
        
        with page_cols[1]:
            if st.button("◀ 이전", disabled=st.session_state.current_page <= 1, use_container_width=True):
                st.session_state.current_page -= 1
                st.rerun()
                
        with page_cols[2]:
            st.markdown(f"<div style='text-align: center; padding-top: 7px; font-weight: 600; font-size: 1.15rem; color: #333;'>{st.session_state.current_page} / {total_pages}</div>", unsafe_allow_html=True)
            
        with page_cols[3]:
            if st.button("다음 ▶", disabled=st.session_state.current_page >= total_pages, use_container_width=True):
                st.session_state.current_page += 1
                st.rerun()
