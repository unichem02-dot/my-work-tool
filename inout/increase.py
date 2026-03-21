import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import math
import html
import time

# 1. 페이지 기본 설정 (와이드 모드 유지)
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# ==========================================
# 🎨 커스텀 CSS (텍스트 확대, 클릭 버튼 및 디자인 업그레이드)
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
    
    /* 텍스트 크기 확대 적용 */
    .stMarkdown p, .stMarkdown li { font-size: 1.2rem !important; }
    .stMultiSelect label, .stTextInput label {
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #333333;
    }
    div[data-testid="metric-container"] label { font-size: 1.15rem !important; }
    div[data-testid="metric-container"] div { font-size: 2.3rem !important; }

    /* 타이틀 텍스트 버튼 (Tertiary) 스타일링 - 제목 클릭 새로고침용 */
    button[kind="tertiary"] {
        display: flex !important;
        justify-content: flex-start !important;
        padding: 0 !important;
        background-color: transparent !important;
    }
    button[kind="tertiary"] p {
        font-size: 2.3rem !important;
        font-weight: 800 !important;
        color: #31333F !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    button[kind="tertiary"]:hover p {
        color: #ff4b4b !important; /* 마우스 올리면 빨간색으로 변함 */
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
        cursor: pointer; /* 마우스 오버 시 손가락 모양 (클릭 가능 표시) */
        transition: background-color 0.2s;
        user-select: none; /* 클릭 시 텍스트 드래그 방지 */
    }
    .custom-table th:hover {
        background-color: #e2e6ea; /* 마우스 올렸을 때 색상 변화 */
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
    .sort-icon {
        color: #ff4b4b;
        margin-left: 5px;
    }
    
    /* 하단 JS 페이지 이동 버튼 스타일 */
    .page-btn {
        padding: 8px 16px;
        font-size: 1.15rem;
        font-weight: 600;
        cursor: pointer;
        border: 1px solid #ddd;
        border-radius: 5px;
        background-color: #fff;
        color: #333;
        transition: 0.2s;
    }
    .page-btn:hover:not(:disabled) {
        background-color: #f8f9fa;
        border-color: #ff4b4b;
        color: #ff4b4b;
    }
    .page-btn:disabled {
        opacity: 0.4;
        cursor: not-allowed;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 로그인 기능 (비밀번호 확인 + 3시간 세션 유지)
# ==========================================
def check_password():
    TIMEOUT_SECONDS = 10800  # 3시간 (3 * 60 * 60 초)
    
    # 1. URL 파라미터를 이용한 세션 복구 (F5 새로고침 생존 로직)
    if st.query_params.get("auth") == "true":
        login_ts = float(st.query_params.get("ts", 0))
        if time.time() - login_ts < TIMEOUT_SECONDS:
            st.session_state["authenticated"] = True
        else:
            # 3시간 경과 시 로그인 만료 및 URL 초기화
            st.session_state["authenticated"] = False
            st.query_params.clear()

    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔒 보안 접속")
            st.info("유니매입가격정보를 열람하시려면 비밀번호를 입력해주세요. (로그인 시 3시간 유지됩니다.)")
            
            with st.form("login_form"):
                pwd = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
                submit = st.form_submit_button("확인", use_container_width=True)
                
                if submit:
                    if pwd == str(st.secrets.get("tom_password", "")):
                        st.session_state["authenticated"] = True
                        # URL 파라미터에 인증 상태 및 로그인 시간 기록 (새로고침 방어용)
                        st.query_params["auth"] = "true"
                        st.query_params["ts"] = str(time.time())
                        st.rerun()
                    else:
                        st.error("🚨 비밀번호가 일치하지 않습니다.")
        return False
    return True

if not check_password():
    st.stop()

# 2. 구글 시트 데이터 불러오기
# 실시간 연동을 위해 캐시(저장) 시간을 5초로 매우 짧게 변경 (구글 API 차단 방지용 최소 시간)
@st.cache_data(ttl=5)
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    # connection 자체의 기본 캐시 기능도 무력화하여 항상 최신 데이터(5초 이내)를 가져옴
    df = conn.read(worksheet="시트1", ttl=5) 
    
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
# UI 레이아웃 시작
# ==========================================

# 상단 헤더 영역 (타이틀버튼 + 로그아웃)
st.markdown("<br>", unsafe_allow_html=True)
header_col1, header_col2 = st.columns([5, 1])

with header_col1:
    # 제목을 클릭 가능한 버튼으로 생성 (캐시 강제 초기화 및 새로고침)
    if st.button("📈 유니매입가격정보", type="tertiary", help="클릭하면 구글 시트의 최신 데이터를 강제로 다시 불러옵니다."):
        st.cache_data.clear() # 숨어있는 모든 캐시 완벽히 삭제 (강력한 새로고침)
        st.rerun() # 화면 새로고침
        
    st.markdown("<p style='font-size: 1.2rem; color: #555; margin-top: -10px; margin-bottom: 20px;'>단가 인상 내역을 검색하세요. <b>(글자를 클릭하면 최신 데이터로 새로고침 됩니다!)</b></p>", unsafe_allow_html=True)

with header_col2:
    # 우측 상단 로그인 상태 및 로그아웃 버튼
    st.markdown("<div style='text-align: right; font-size: 0.95rem; color: #28a745; margin-bottom: 5px; font-weight: 600;'>🟢 안전하게 로그인됨</div>", unsafe_allow_html=True)
    if st.button("🔓 로그아웃", use_container_width=True):
        st.session_state["authenticated"] = False
        st.query_params.clear() # 유지되던 URL 정보 삭제
        st.rerun()

# 1. 상세 검색 영역
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

# 2. 필터링 로직 적용
filtered_df = data.copy()

if "전체" not in selected_vendors and len(selected_vendors) > 0:
    filtered_df = filtered_df[filtered_df[col_vendor].isin(selected_vendors)]

if "전체" not in selected_dates and len(selected_dates) > 0:
    filtered_df = filtered_df[filtered_df[col_date].astype(str).str.strip().isin(selected_dates)]

if search_item:
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(search_item, case=False, na=False)]

# 기본 초기 정렬 설정
sort_cols = [c for c in [col_date, col_vendor, col_item] if c in filtered_df.columns]
if sort_cols:
    asc_rules = [False if c == col_date else True for c in sort_cols]
    filtered_df = filtered_df.sort_values(by=sort_cols, ascending=asc_rules)

st.markdown("<br>", unsafe_allow_html=True)

# 3. 요약 지표 (Metrics)
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
# 4. 데이터프레임 (JS 정렬 & 페이지네이션이 포함된 최적화 테이블)
# ==========================================
if filtered_df.empty:
    st.warning("👀 검색 조건에 맞는 데이터가 없습니다. 다른 조건으로 검색해 보세요.")
else:
    # --- 제목 클릭 시 JS 정렬 함수(sortTable) 호출 ---
    table_html = "<table class='custom-table' id='myTable'><thead><tr>"
    for i, col in enumerate(filtered_df.columns):
        table_html += f"<th onclick='sortTable({i})' title='클릭하여 {html.escape(str(col), quote=True)} 기준 정렬'>{html.escape(str(col))} <span class='sort-icon' id='icon-{i}'></span></th>"
    table_html += "</tr></thead><tbody id='tableBody'>"
    
    # 강조할 열 지정
    bold_cols = ["물품명", "인상폭"]
    
    # 100개가 아닌 '전체' 데이터를 HTML로 렌더링 (이후 JS로 100개씩 나눠서 보여줌)
    for _, row in filtered_df.iterrows():
        table_html += "<tr>"
        for col in filtered_df.columns:
            val = row[col]
            safe_val = "" if pd.isna(val) or val == "" else html.escape(str(val))
            
            if col in bold_cols:
                table_html += f"<td class='bold-col'>{safe_val}</td>"
            else:
                table_html += f"<td>{safe_val}</td>"
        table_html += "</tr>"
    table_html += "</tbody></table>"

    # 스트림릿 에러 방지를 위해 자바스크립트 내 줄바꿈과 충돌 기호를 제거한 안전한 압축 버전
    table_html += """
    <div id='paginationControls' style='display: none; text-align: center; margin-top: 30px; margin-bottom: 25px;'>
        <button class='page-btn' onclick='changePage(-1)' id='prevBtn'>◀ 이전</button>
        <span id='pageInfo' style='margin: 0 25px; font-weight: 700; font-size: 1.2rem; color: #31333F;'>1 / 1</span>
        <button class='page-btn' onclick='changePage(1)' id='nextBtn'>다음 ▶</button>
    </div>
    <script>
    (function(){
        var ROWS_PER_PAGE = 100;
        var currentPage = 1;
        var sortCol = -1;
        var sortAsc = true;
        window.updateTable = function() {
            var tbody = document.getElementById("tableBody");
            if (!tbody) return;
            var rows = Array.prototype.slice.call(tbody.getElementsByTagName("tr"));
            var totalPages = Math.ceil(rows.length / ROWS_PER_PAGE) || 1;
            if (currentPage < 1) currentPage = 1;
            if (currentPage > totalPages) currentPage = totalPages;
            for(var i=0; i<rows.length; i++){
                if (i >= (currentPage - 1) * ROWS_PER_PAGE && i < currentPage * ROWS_PER_PAGE) {
                    rows[i].style.display = "";
                } else {
                    rows[i].style.display = "none";
                }
            }
            var pageInfo = document.getElementById("pageInfo");
            if (pageInfo) pageInfo.innerText = currentPage + " / " + totalPages;
            var prevBtn = document.getElementById("prevBtn");
            if (prevBtn) prevBtn.disabled = (currentPage === 1);
            var nextBtn = document.getElementById("nextBtn");
            if (nextBtn) nextBtn.disabled = (currentPage === totalPages);
            var pagControls = document.getElementById("paginationControls");
            if (pagControls) pagControls.style.display = (rows.length > ROWS_PER_PAGE) ? "block" : "none";
        };
        window.changePage = function(delta) {
            currentPage += delta;
            window.updateTable();
        };
        window.sortTable = function(n) {
            var tbody = document.getElementById("tableBody");
            if (!tbody) return;
            var rows = Array.prototype.slice.call(tbody.getElementsByTagName("tr"));
            if (sortCol === n) { sortAsc = !sortAsc; } else { sortCol = n; sortAsc = true; }
            var icons = document.querySelectorAll('.sort-icon');
            for(var k=0; k<icons.length; k++){ icons[k].innerText = ''; }
            var iconEl = document.getElementById('icon-' + n);
            if (iconEl) { iconEl.innerText = sortAsc ? "▲" : "▼"; }
            rows.sort(function(a, b) {
                var tdA = a.getElementsByTagName("td")[n];
                var tdB = b.getElementsByTagName("td")[n];
                var valA = tdA ? tdA.innerText.trim() : "";
                var valB = tdB ? tdB.innerText.trim() : "";
                if (valA === "" && valB !== "") return 1;
                if (valB === "" && valA !== "") return -1;
                var cleanA = valA.replace(/,/g, '').replace(/원/g, '').replace(/ /g, '');
                var cleanB = valB.replace(/,/g, '').replace(/원/g, '').replace(/ /g, '');
                var numA = parseFloat(cleanA);
                var numB = parseFloat(cleanB);
                if (!isNaN(numA) && !isNaN(numB) && cleanA == numA && cleanB == numB) { valA = numA; valB = numB; }
                if (valA < valB) return sortAsc ? -1 : 1;
                if (valA > valB) return sortAsc ? 1 : -1;
                return 0;
            });
            for(var j=0; j<rows.length; j++){ tbody.appendChild(rows[j]); }
            currentPage = 1;
            window.updateTable();
        };
        window.updateTable();
    })();
    </script>
    """
    
    st.markdown(table_html, unsafe_allow_html=True)

# 하단 안내
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("🔄 **실시간 동기화 지원:** 엑셀 내용 수정 후 약 5초 뒤면 즉시 데이터가 반영됩니다. (수동 즉시 새로고침: 상단 큰 제목 클릭)")
