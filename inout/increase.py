import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import math
import html

# 1. 페이지 기본 설정 (와이드 모드 유지)
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# ==========================================
# 🎨 커스텀 CSS (텍스트 30% 확대 및 디자인 업그레이드)
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
    
    /* 요약 지표(Metric) 카드 스타일링 */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e9ecef;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* ---------------------------------
       텍스트 크기 30% 확대 적용 영역 
       --------------------------------- */
    .stMarkdown p, .stMarkdown li {
        font-size: 1.2rem !important;
    }
    .stMultiSelect label, .stTextInput label {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #333333;
    }
    div[data-testid="metric-container"] label {
        font-size: 1.15rem !important;
    }
    div[data-testid="metric-container"] div {
        font-size: 2.3rem !important;
    }

    /* 커스텀 데이터 표(Table) 스타일링 */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        font-size: 1.15rem; /* 약 30% 확대 */
    }
    .custom-table th {
        background-color: #f8f9fa;
        color: #31333F;
        font-weight: 700;
        padding: 14px 16px;
        border-bottom: 2px solid #e6e6e6;
        text-align: left;
    }
    .custom-table td {
        padding: 14px 16px;
        border-bottom: 1px solid #f0f2f6;
        color: #31333F;
    }
    .custom-table tr:hover td {
        background-color: #f1f3f5;
    }
    .bold-col {
        font-weight: 900 !important;
        color: #000000 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 로그인 기능 (비밀번호 확인)
# ==========================================
def check_password():
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        # 로그인 화면 중앙 정렬을 위한 여백 추가
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
                        st.rerun()
                    else:
                        st.error("🚨 비밀번호가 일치하지 않습니다.")
        return False
    return True

if not check_password():
    st.stop()

# 2. 구글 시트 데이터 불러오기
@st.cache_data(ttl=600)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="시트1") 
    
    # 데이터 전처리 (빈 행 제거 및 엑셀 특유의 '투명한 빈 열' 제거)
    df = df.dropna(how="all")
    df = df.dropna(axis=1, how="all")
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    data = load_data()
except Exception as e:
    st.error("구글 시트를 불러오는 데 실패했습니다. '.streamlit/secrets.toml' 설정과 공유 상태를 확인해주세요.")
    st.stop()

# 엑셀 데이터에 맞춘 실제 컬럼명
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
# UI 레이아웃 시작
# ==========================================

st.title("📈 유니매입가격정보")
st.markdown("단가 인상 내역(기존가, 인상폭, 메모 등)을 빠르고 정확하게 검색하세요.")
st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 1. 상세 검색 영역 (박스형 컨테이너 적용)
# ==========================================
with st.container(border=True):
    st.markdown("##### 🔍 상세 검색")
    search_col1, search_col2, search_col3 = st.columns(3)

    with search_col1:
        vendor_raw = [str(v).strip() for v in data[col_vendor].unique() if str(v).strip() != ""]
        vendor_list = ["전체"] + sorted(vendor_raw)
        selected_vendors = st.multiselect("🏢 업체명", vendor_list, default=["전체"])

    with search_col2:
        search_item = st.text_input("📦 물품명 검색", placeholder="예: 황산, 소다 등 입력")

    with search_col3:
        date_raw = [str(d).strip() for d in data[col_date].unique() if str(d).strip() != ""]
        date_list = ["전체"] + sorted(date_raw, reverse=True)
        selected_dates = st.multiselect("📅 인상날짜", date_list, default=["전체"])

# ==========================================
# 2. 필터링 로직 적용
# ==========================================
filtered_df = data.copy()

if "전체" not in selected_vendors and len(selected_vendors) > 0:
    filtered_df = filtered_df[filtered_df[col_vendor].isin(selected_vendors)]

if "전체" not in selected_dates and len(selected_dates) > 0:
    filtered_df = filtered_df[filtered_df[col_date].astype(str).str.strip().isin(selected_dates)]

if search_item:
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(search_item, case=False, na=False)]

sort_cols = [c for c in [col_date, col_vendor, col_item] if c in filtered_df.columns]
if sort_cols:
    asc_rules = [False if c == col_date else True for c in sort_cols]
    filtered_df = filtered_df.sort_values(by=sort_cols, ascending=asc_rules)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. 요약 지표 (Metrics)
# ==========================================
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

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 4. 데이터프레임 (상세 내역) 출력 및 페이지네이션
# ==========================================
if filtered_df.empty:
    st.warning("👀 검색 조건에 맞는 데이터가 없습니다. 다른 조건으로 검색해 보세요.")
else:
    ROWS_PER_PAGE = 100
    total_pages = math.ceil(len(filtered_df) / ROWS_PER_PAGE)

    # 검색 조건이 변경되면 페이지를 1로 자동 초기화하는 스마트 로직
    filter_hash = hash(str(selected_vendors) + str(search_item) + str(selected_dates))
    if st.session_state.get('last_filter_hash') != filter_hash:
        st.session_state.current_page = 1
        st.session_state.last_filter_hash = filter_hash

    if 'current_page' not in st.session_state:
        st.session_state.current_page = 1
        
    # 현재 페이지에 해당하는 100개 데이터 자르기
    start_idx = (st.session_state.current_page - 1) * ROWS_PER_PAGE
    end_idx = start_idx + ROWS_PER_PAGE
    display_df = filtered_df.iloc[start_idx:end_idx]
    
    # --- 스크롤 없는 맞춤형 HTML 표 생성 (굵은 글씨 및 텍스트 크기 완벽 적용) ---
    table_html = "<table class='custom-table'><thead><tr>"
    for col in display_df.columns:
        table_html += f"<th>{html.escape(str(col))}</th>"
    table_html += "</tr></thead><tbody>"
    
    # 강조할 열 지정
    bold_cols = ["물품명", "인상폭"]
    
    for _, row in display_df.iterrows():
        table_html += "<tr>"
        for col in display_df.columns:
            val = row[col]
            if pd.isna(val) or val == "": 
                safe_val = ""
            else:
                safe_val = html.escape(str(val))
            
            # 물품명, 인상폭 열은 굵은 글씨 클래스 적용
            if col in bold_cols:
                table_html += f"<td class='bold-col'>{safe_val}</td>"
            else:
                table_html += f"<td>{safe_val}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"
    
    # 화면에 표출
    st.markdown(table_html, unsafe_allow_html=True)
    
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

# 하단 안내
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("🔄 데이터 갱신: 구글 시트 수정 후 약 10분 소요 (수동 새로고침: 우측 상단 메뉴 ⋮ > Clear cache)")
