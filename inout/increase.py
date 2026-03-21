import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import math
import html
import time
import streamlit.components.v1 as components # 독립 HTML 렌더링을 위한 패키지 추가

# 1. 페이지 기본 설정 (와이드 모드 유지)
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# ==========================================
# 🎨 앱 전반의 커스텀 CSS (표 스타일은 HTML 내부로 이동)
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
        color: #ff4b4b !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 로그인 기능 (비밀번호 확인 + 3시간 세션 유지)
# ==========================================
def check_password():
    TIMEOUT_SECONDS = 10800  # 3시간 (3 * 60 * 60 초)
    
    if st.query_params.get("auth") == "true":
        login_ts = float(st.query_params.get("ts", 0))
        if time.time() - login_ts < TIMEOUT_SECONDS:
            st.session_state["authenticated"] = True
        else:
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

# 상단 헤더 영역
st.markdown("<br>", unsafe_allow_html=True)
header_col1, header_col2 = st.columns([5, 1])

with header_col1:
    if st.button("📈 유니매입가격정보", type="tertiary", help="클릭하면 구글 시트의 최신 데이터를 강제로 다시 불러옵니다."):
        st.cache_data.clear()
        st.rerun()
        
    st.markdown("<p style='font-size: 1.2rem; color: #555; margin-top: -10px; margin-bottom: 20px;'>단가 인상 내역을 검색하세요. <b>(글자를 클릭하면 최신 데이터로 새로고침 됩니다!)</b></p>", unsafe_allow_html=True)

with header_col2:
    st.markdown("<div style='text-align: right; font-size: 0.95rem; color: #28a745; margin-bottom: 5px; font-weight: 600;'>🟢 안전하게 로그인됨</div>", unsafe_allow_html=True)
    if st.button("🔓 로그아웃", use_container_width=True):
        st.session_state["authenticated"] = False
        st.query_params.clear()
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
# 4. 데이터프레임 (JS 정렬 오류 완벽 해결을 위한 독립 HTML 컴포넌트)
# ==========================================
if filtered_df.empty:
    st.warning("👀 검색 조건에 맞는 데이터가 없습니다. 다른 조건으로 검색해 보세요.")
else:
    # 스트림릿의 보안 차단을 우회하기 위해 완벽한 형태의 HTML 문서 구조로 작성
    iframe_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0; padding: 0; 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                background-color: white;
            }}
            .custom-table {{ width: 100%; border-collapse: collapse; font-size: 1.15rem; }}
            .custom-table th {{
                background-color: #f8f9fa; color: #31333F; font-weight: 700; 
                padding: 14px 16px; border-bottom: 2px solid #e6e6e6; text-align: left; 
                cursor: pointer; transition: background-color 0.2s; user-select: none;
            }}
            .custom-table th:hover {{ background-color: #e2e6ea; }}
            .custom-table td {{ padding: 14px 16px; border-bottom: 1px solid #f0f2f6; color: #31333F; }}
            .custom-table tr:hover td {{ background-color: #f1f3f5; }}
            .bold-col {{ font-weight: 900 !important; color: #000000 !important; }}
            .sort-icon {{ color: #ff4b4b; margin-left: 5px; }}
            .page-btn {{
                padding: 8px 16px; font-size: 1.15rem; font-weight: 600; cursor: pointer;
                border: 1px solid #ddd; border-radius: 5px; background-color: #fff; color: #333; transition: 0.2s;
            }}
            .page-btn:hover:not(:disabled) {{ background-color: #f8f9fa; border-color: #ff4b4b; color: #ff4b4b; }}
            .page-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
        </style>
    </head>
    <body>
        <table class='custom-table' id='myTable'>
            <thead><tr>
    """
    
    # 1. 헤더 생성
    for i, col in enumerate(filtered_df.columns):
        iframe_html += f"<th onclick='sortTable({i})' title='클릭하여 정렬'>{html.escape(str(col))} <span class='sort-icon' id='icon-{i}'></span></th>"
    iframe_html += "</tr></thead><tbody id='tableBody'>"
    
    # 2. 본문 데이터 삽입 (초기 깜빡임 방지를 위해 100개 이후는 숨김 처리)
    bold_cols = ["물품명", "인상폭"]
    for idx, (_, row) in enumerate(filtered_df.iterrows()):
        display_style = "" if idx < 100 else " style='display: none;'"
        iframe_html += f"<tr{display_style}>"
        for col in filtered_df.columns:
            val = row[col]
            safe_val = "" if pd.isna(val) or val == "" else html.escape(str(val))
            if col in bold_cols:
                iframe_html += f"<td class='bold-col'>{safe_val}</td>"
            else:
                iframe_html += f"<td>{safe_val}</td>"
        iframe_html += "</tr>"
        
    iframe_html += """
            </tbody>
        </table>
        
        <!-- 하단 페이지네이션 컨트롤 -->
        <div id='paginationControls' style='display: none; text-align: center; margin-top: 30px; margin-bottom: 25px;'>
            <button class='page-btn' onclick='changePage(-1)' id='prevBtn'>◀ 이전</button>
            <span id='pageInfo' style='margin: 0 25px; font-weight: 700; font-size: 1.2rem; color: #31333F;'></span>
            <button class='page-btn' onclick='changePage(1)' id='nextBtn'>다음 ▶</button>
        </div>

        <script>
            const ROWS_PER_PAGE = 100;
            let currentPage = 1;
            let sortCol = -1;
            let sortAsc = true;
            let allRows = [];

            window.onload = function() {
                const tbody = document.getElementById("tableBody");
                // 자바스크립트가 안전하게 모든 행을 배열로 저장
                allRows = Array.from(tbody.getElementsByTagName("tr"));
                updateTable();
            };

            function updateTable() {
                const tbody = document.getElementById("tableBody");
                const totalPages = Math.ceil(allRows.length / ROWS_PER_PAGE) || 1;
                
                if (currentPage < 1) currentPage = 1;
                if (currentPage > totalPages) currentPage = totalPages;

                // 기존 화면의 행을 지우고, 현재 페이지에 맞는 행만 다시 부착 (초고속 화면 전환)
                tbody.innerHTML = "";
                const startIdx = (currentPage - 1) * ROWS_PER_PAGE;
                const endIdx = startIdx + ROWS_PER_PAGE;
                
                for(let i = startIdx; i < endIdx && i < allRows.length; i++) {
                    allRows[i].style.display = ""; // 숨겼던 행 보이게 처리
                    tbody.appendChild(allRows[i]);
                }

                // 하단 페이지 번호 업데이트
                document.getElementById("pageInfo").innerText = currentPage + " / " + totalPages;
                document.getElementById("prevBtn").disabled = (currentPage === 1);
                document.getElementById("nextBtn").disabled = (currentPage === totalPages);
                document.getElementById("paginationControls").style.display = (allRows.length > ROWS_PER_PAGE) ? "block" : "none";
            }

            function changePage(delta) {
                currentPage += delta;
                updateTable();
                window.scrollTo(0, 0); // 다음 페이지로 넘어가면 표 맨 위로 스크롤
            }

            function sortTable(n) {
                // 클릭한 열(기둥)이 이전과 같으면 오름/내림차순 반전, 다르면 무조건 오름차순(가나다순)
                if (sortCol === n) { sortAsc = !sortAsc; } 
                else { sortCol = n; sortAsc = true; }
                
                // 화살표 UI 업데이트
                document.querySelectorAll('.sort-icon').forEach(icon => icon.innerHTML = '');
                const iconEl = document.getElementById('icon-' + n);
                if (iconEl) { iconEl.innerHTML = sortAsc ? "<span style='color:#ff4b4b;'>▲</span>" : "<span style='color:#ff4b4b;'>▼</span>"; }
                
                // 정렬 핵심 로직 (숫자와 텍스트 완벽 구분)
                allRows.sort((a, b) => {
                    const tdA = a.getElementsByTagName("td")[n];
                    const tdB = b.getElementsByTagName("td")[n];
                    const valA = tdA ? tdA.innerText.trim() : "";
                    const valB = tdB ? tdB.innerText.trim() : "";
                    
                    if (valA === "" && valB !== "") return 1;
                    if (valB === "" && valA !== "") return -1;
                    
                    const cleanA = valA.replace(/,/g, '').replace(/원/g, '').replace(/%/g, '').replace(/ /g, '');
                    const cleanB = valB.replace(/,/g, '').replace(/원/g, '').replace(/%/g, '').replace(/ /g, '');
                    
                    const numA = parseFloat(cleanA);
                    const numB = parseFloat(cleanB);
                    
                    // 순수 숫자인지 확인 후 비교, 아니면 글자 비교
                    let cmpA = (!isNaN(numA) && cleanA === numA.toString()) ? numA : valA;
                    let cmpB = (!isNaN(numB) && cleanB === numB.toString()) ? numB : valB;
                    
                    if (cmpA < cmpB) return sortAsc ? -1 : 1;
                    if (cmpA > cmpB) return sortAsc ? 1 : -1;
                    return 0;
                });
                
                // 정렬 후엔 항상 1페이지로 돌아감
                currentPage = 1;
                updateTable();
            }
        </script>
    </body>
    </html>
    """

    # 컴포넌트의 높이를 동적으로 계산하여 스크롤바 방지
    num_rows = min(len(filtered_df), 100)
    # 80(기본여백) + (행 개수 * 53픽셀) + 100(페이지네이션 여백)
    iframe_height = 80 + (num_rows * 53) + (100 if len(filtered_df) > 100 else 20)
    
    # 스트림릿 전용 컴포넌트로 안전하고 완벽하게 HTML/JS 렌더링
    components.html(iframe_html, height=iframe_height, scrolling=False)

# 하단 안내
st.markdown("<br><br>", unsafe_allow_html=True)
st.caption("💡 표 제목을 클릭하면 즉시 정렬되며, 상단의 큰 제목(유니매입가격정보)을 누르면 구글 시트 내용이 새로고침 됩니다.")
