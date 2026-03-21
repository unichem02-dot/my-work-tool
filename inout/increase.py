import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import math
import html
import time
import io
import json
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# 💡 한국 표준시(KST) 기준 시간 반환
def get_kst_now():
    return datetime.utcnow() + timedelta(hours=9)

# 1. 페이지 기본 설정 (와이드 모드 유지)
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# ==========================================
# 🎨 TOmBOy's INOUT 스타일 다크 테마 커스텀 CSS
# ==========================================
st.markdown("""
    <style>
    /* 스트림릿 기본 UI 요소를 완벽하게 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    
    /* 전체 여백 최적화 및 다크 테마 배경 */
    [data-testid="stAppViewContainer"] { background-color: #2b323c; }
    .main .block-container { padding-top: 1rem; max-width: 98%; }
    
    /* 텍스트 기본 색상 흰색 (가독성 최적화) */
    h1, h2, h3, h4, p, span, label { color: #ffffff !important; }
    
    /* 버튼 공통 스타일 */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0px 10px !important;
    }
    
    /* Primary 버튼 (새로고침, 검색 등) -> 파란색 */
    button[kind="primary"] {
        background-color: #4e8cff !important;
        border-color: #4e8cff !important;
        color: white !important;
    }
    button[kind="primary"]:hover { 
        background-color: #3b76e5 !important; 
        border-color: #3b76e5 !important; 
    }

    /* Secondary 버튼 (로그아웃, 취소 등) -> 올리브색 */
    button[kind="secondary"] {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
    }
    button[kind="secondary"]:hover { 
        background-color: #646a39 !important; 
        border-color: #646a39 !important; 
    }
    
    /* 💡 EXCEL 다운로드 버튼 전용 올리브색 커스텀 */
    div[data-testid="stDownloadButton"] button[kind="primary"] {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
    }
    div[data-testid="stDownloadButton"] button[kind="primary"]:hover {
        background-color: #646a39 !important;
        border-color: #646a39 !important;
        color: white !important;
    }
    
    /* 검색 메뉴 굵게 및 색상 (검색창은 밝게 유지하여 가독성 확보) */
    div[data-testid="stTextInput"] input {
        color: #1e293b !important;
        font-weight: bold !important;
        background-color: #f8f9fa !important;
    }
    div[data-baseweb="select"] > div { 
        font-weight: bold !important; 
        background-color: #f8f9fa !important;
        color: #1e293b !important;
    }
    div[data-baseweb="select"] span { color: #1e293b !important; }
    
    /* 요약 지표 폰트 오버라이드 (다크 대시보드 전용) */
    [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 2.3rem !important; }
    [data-testid="stMetricLabel"] { color: #cbd5e1 !important; font-size: 1.15rem !important; }
    
    /* 구분선 라인 색상 */
    hr { margin: 15px 0px 15px 0px; border: 0.5px solid #4a5568 !important; }
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
        st.markdown("<h1 style='text-align: center; color: #4e8cff !important; margin-top: 50px;'>🛡️ ADMIN ACCESS</h1>", unsafe_allow_html=True)
        col_l, col_c, col_r = st.columns([1, 1.2, 1])
        with col_c:
            st.info("유니매입가격정보를 열람하시려면 비밀번호를 입력해주세요.")
            with st.form("login_form"):
                pwd = st.text_input("PASSWORD", type="password", placeholder="••••")
                submit = st.form_submit_button("SYSTEM LOGIN", use_container_width=True, type="primary")
                
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
# UI 레이아웃 시작 (상단 상태바)
# ==========================================

col_t, col_r, col_l = st.columns([6.5, 1.5, 1.5])
with col_t: 
    st.markdown(f"<h3 style='margin:0;'>📈 유니매입가격정보 (인상공문 현황)</h3>", unsafe_allow_html=True)
    st.markdown("<p style='color: #cbd5e1; margin-top: 5px; font-size: 15px;'>단가 인상 내역을 업체명, 물품명, 날짜로 쉽고 빠르게 교차 검색해 보세요.</p>", unsafe_allow_html=True)

with col_r: 
    if st.button("🔄 새로고침", use_container_width=True, type="primary"):
        load_data.clear() # 확실한 새로고침을 위해 함수 캐시 강제 삭제
        # 검색창에 입력된 텍스트 값들을 모두 지워서 초기화합니다.
        for key in ["search_vendor_key", "search_item_key", "search_date_key"]:
            if key in st.session_state:
                del st.session_state[key]
        st.rerun()

with col_l:
    if st.button("🔓 LOGOUT", use_container_width=True, type="secondary"):
        st.session_state["authenticated"] = False
        st.query_params.clear()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# 1. 상세 검색 영역 (깔끔한 3단 텍스트 입력 배치)
st.markdown("<h4 style='color: #4e8cff;'>🔍 상세 검색</h4>", unsafe_allow_html=True)
search_col1, search_col2, search_col3 = st.columns(3)

with search_col1:
    search_vendor = st.text_input("🏢 업체명 검색", placeholder="예: 부흥산업사 등 부분 검색 가능", key="search_vendor_key")

with search_col2:
    search_item = st.text_input("📦 물품명 검색", placeholder="예: 황산, 소다 등 부분 검색 가능", key="search_item_key")

with search_col3:
    search_date = st.text_input("📅 인상날짜 검색", placeholder="예: 26.03.20 또는 03 (자유롭게 텍스트로 검색)", key="search_date_key")

# 2. 필터링 로직
filtered_df = data.copy()

if search_vendor:
    filtered_df = filtered_df[filtered_df[col_vendor].astype(str).str.contains(search_vendor, case=False, na=False)]

if search_item:
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(search_item, case=False, na=False)]

if search_date:
    filtered_df = filtered_df[filtered_df[col_date].astype(str).str.contains(search_date, case=False, na=False)]

# 초기 정렬 설정 (파이썬)
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

st.markdown("<hr>", unsafe_allow_html=True)

# ==========================================
# 4. 데이터프레임 헤더 및 [인쇄/엑셀] 버튼 영역
# ==========================================
col_title, col_print, col_excel = st.columns([6, 1.5, 1.5])
with col_title:
    st.markdown("<h4 style='color: #ffffff; margin-bottom: 5px; margin-top: 10px;'>📋 상세 내역 <span style='font-size: 14px; color: #cbd5e1; font-weight: normal;'>(표 제목을 클릭하면 정렬됩니다)</span></h4>", unsafe_allow_html=True)

# --- 🖨️ PRINT 기능용 HTML 생성 ---
print_html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>인쇄 미리보기</title>
    <meta charset="utf-8">
    <style>
        @page {{ size: A4 portrait; margin: 10mm; }}
        body {{ font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; color: black; background: white; margin: 0; }}
        .title {{ font-size: 22px; font-weight: bold; text-align: center; margin-bottom: 20px; }}
        .info {{ font-size: 12px; margin-bottom: 10px; color: #555; text-align: right; }}
        .custom-table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; }}
        .custom-table th, .custom-table td {{ border: 1px solid #aaa; padding: 6px 8px; color: black !important; }}
        .custom-table th {{ text-align: center; font-weight: bold; background-color: #f1f5f9; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    </style>
</head>
<body>
    <div class="title">유니매입가격정보 검색 결과</div>
    <div class="info">출력 일자: {get_kst_now().strftime('%Y-%m-%d %H:%M')} | 총 검색 건수: {len(filtered_df):,}건</div>
    <table class="custom-table">
        <thead><tr>
"""
for col in filtered_df.columns:
    print_html_content += f"<th>{html.escape(str(col))}</th>"
print_html_content += "</tr></thead><tbody>"
for _, row in filtered_df.iterrows():
    print_html_content += "<tr>"
    for col in filtered_df.columns:
        val = "" if pd.isna(row[col]) or row[col] == "" else str(row[col])
        print_html_content += f"<td>{html.escape(val)}</td>"
    print_html_content += "</tr>"
print_html_content += "</tbody></table></body></html>"

with col_print:
    components.html(
        f"""
        <!DOCTYPE html>
        <html><head>
        <style>
            body {{ margin: 0; padding: 0; overflow: hidden; background-color: transparent; }}
            .btn-print {{
                width: 100%; height: 40px; background-color: #757c43; color: white;
                border: 1px solid #757c43; border-radius: 8px; font-weight: bold; cursor: pointer; font-size: 15px;
                font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
                display: flex; align-items: center; justify-content: center; box-sizing: border-box;
                margin-top: 5px;
            }}
            .btn-print:hover {{ background-color: #646a39; border-color: #646a39; }}
        </style>
        <script>
            function fastPrint() {{
                const htmlContent = {json.dumps(print_html_content)};
                let iframe = document.getElementById('print-frame');
                if (iframe) {{ document.body.removeChild(iframe); }}
                iframe = document.createElement('iframe');
                iframe.id = 'print-frame';
                iframe.style.position = 'absolute'; iframe.style.width = '1px'; iframe.style.height = '1px'; 
                iframe.style.opacity = '0'; iframe.style.pointerEvents = 'none';
                document.body.appendChild(iframe);
                const doc = iframe.contentWindow.document;
                doc.open(); doc.write(htmlContent); doc.close();
                setTimeout(function() {{ 
                    iframe.contentWindow.focus(); 
                    iframe.contentWindow.print(); 
                }}, 150);
            }}
        </script>
        </head>
        <body>
            <button class="btn-print" onclick="fastPrint()">🖨️ PRINT</button>
        </body></html>
        """, height=50
    )

with col_excel:
    # --- 💾 EXCEL 추출 로직 (오류 100% 방지 자동화) ---
    excel_output = io.BytesIO()
    has_openpyxl = False
    try:
        import openpyxl
        from openpyxl.styles import PatternFill, Font, Alignment, Border, Side
        has_openpyxl = True
    except ImportError:
        pass
        
    if has_openpyxl and not filtered_df.empty:
        try:
            with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
                filtered_df.to_excel(writer, index=False, sheet_name='검색결과')
                ws = writer.sheets['검색결과']
                
                # 디자인 설정 (헤더 색상 맞춤)
                font_white = Font(color="FFFFFF", bold=True)
                align_center = Alignment(horizontal="center", vertical="center")
                border_thin = Border(left=Side(style='thin', color='D0D0D0'), right=Side(style='thin', color='D0D0D0'), 
                                     top=Side(style='thin', color='D0D0D0'), bottom=Side(style='thin', color='D0D0D0'))
                
                for col_idx, col_name in enumerate(filtered_df.columns, 1):
                    c_lower = str(col_name).lower()
                    if "기존" in c_lower: fill_color = "3B5B88"
                    elif "인상" in c_lower: fill_color = "B8860B"
                    elif "메모" in c_lower: fill_color = "757C43"
                    else: fill_color = "353B48"
                    
                    cell = ws.cell(row=1, column=col_idx)
                    cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type="solid")
                    cell.font = font_white
                    cell.alignment = align_center
                    cell.border = border_thin
                    
                    # 컬럼 너비 자동 설정 (약식)
                    col_letter = openpyxl.utils.get_column_letter(col_idx)
                    ws.column_dimensions[col_letter].width = 15
                    
                # 본문 보더 적용
                for row_idx in range(2, len(filtered_df) + 2):
                    for col_idx in range(1, len(filtered_df.columns) + 1):
                        cell = ws.cell(row=row_idx, column=col_idx)
                        cell.border = border_thin
                        cell.alignment = Alignment(vertical="center")

            excel_data = excel_output.getvalue()
            st.download_button("💾 EXCEL", data=excel_data, file_name=f"유니매입단가인상_{get_kst_now().strftime('%Y%m%d')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="primary")
        except Exception as e:
            st.error(f"엑셀 생성 오류: {e}")
    else:
        # openpyxl 모듈이 없거나 에러 날 경우 CSV로 안전하게 대체
        csv_data = filtered_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button("💾 EXCEL (기본)", data=csv_data, file_name=f"유니매입단가인상_{get_kst_now().strftime('%Y%m%d')}.csv", mime="text/csv", use_container_width=True, type="primary")


if filtered_df.empty:
    pass # 경고 메시지는 위에서 이미 출력
else:
    # 각 헤더 컬럼의 성격에 따라 클래스 이름 부여 (원하시는 테이블 디자인 색상 적용)
    def get_th_class(col_name):
        c_lower = str(col_name)
        if "기존" in c_lower: return "th-in"     # 네이비 블루
        if "인상" in c_lower: return "th-out"    # 황금색/오렌지
        if "메모" in c_lower: return "th-etc"    # 올리브색
        return "th-base"                         # 딥그레이 (업체명, 물품명 등)

    # 텍스트 정렬 로직
    def get_td_class(col_name):
        c_lower = str(col_name)
        if "업체" in c_lower or "물품" in c_lower or "메모" in c_lower: return "tl"
        if "가" in c_lower or "폭" in c_lower or "수량" in c_lower: return "tr"
        return "tc"

    bold_cols = ["물품명", "인상폭"]

    iframe_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            body {{
                margin: 0; padding: 0; 
                font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif;
                background-color: #2b323c; /* 메인 배경색 완벽 동기화 */
            }}
            .custom-table-container {{ width: 100%; margin-top: 5px; }}
            .custom-table {{ width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }}
            .custom-table th, .custom-table td {{ border: 1px solid #d0d0d0; padding: 8px 10px; color: #1e293b; }}
            
            /* 마우스 클릭 기능 추가 및 드래그 방지 */
            .custom-table th {{ 
                text-align: center; color: white !important; font-weight: bold; 
                padding: 10px 6px; cursor: pointer; user-select: none; transition: 0.2s;
            }}
            
            /* 색상 디자인 클래스 */
            .custom-table tr:nth-child(even) td {{ background-color: #f8f9fa; }}
            .custom-table tr:hover td {{ background-color: #e2e6ea; }}
            .th-base {{ background-color: #353b48 !important; }}
            .th-in {{ background-color: #3b5b88 !important; }}
            .th-out {{ background-color: #b8860b !important; }}
            .th-etc {{ background-color: #757c43 !important; }}
            
            .tc {{ text-align: center; }} .tl {{ text-align: left; }} .tr {{ text-align: right; }}
            .bold-col {{ font-weight: 900 !important; color: #000000 !important; }}
            .sort-icon {{ color: #ffeb3b; margin-left: 5px; font-size: 12px; }}
            
            /* 하단 JS 페이지 이동 버튼 스타일 */
            .page-btn {{
                padding: 6px 16px; font-size: 15px; font-weight: bold; cursor: pointer;
                border: 1px solid #4e8cff; border-radius: 6px; background-color: #4e8cff; color: white; transition: 0.2s;
            }}
            .page-btn:hover:not(:disabled) {{ background-color: #3b76e5; border-color: #3b76e5; }}
            .page-btn:disabled {{ opacity: 0.4; cursor: not-allowed; background-color: #4a5568; border-color: #4a5568; }}
        </style>
    </head>
    <body>
        <div class="custom-table-container">
            <table class='custom-table' id='myTable'>
                <thead><tr>
    """
    
    # 1. 헤더 생성 (디자인 클래스 부여)
    for i, col in enumerate(filtered_df.columns):
        th_class = get_th_class(col)
        iframe_html += f"<th class='{th_class}' onclick='sortTable({i})' title='클릭하여 정렬'>{html.escape(str(col))} <span class='sort-icon' id='icon-{i}'></span></th>"
    iframe_html += "</tr></thead><tbody id='tableBody'>"
    
    # 2. 본문 데이터 삽입 (초기 깜빡임 방지를 위해 100개 이후는 숨김 처리)
    for idx, (_, row) in enumerate(filtered_df.iterrows()):
        display_style = "" if idx < 100 else " style='display: none;'"
        iframe_html += f"<tr{display_style}>"
        
        for col in filtered_df.columns:
            val = row[col]
            safe_val = "" if pd.isna(val) or val == "" else html.escape(str(val))
            
            td_class = get_td_class(col)
            if col in bold_cols:
                td_class += " bold-col"
                
            iframe_html += f"<td class='{td_class}'>{safe_val}</td>"
        iframe_html += "</tr>"
        
    iframe_html += """
                </tbody>
            </table>
        </div>
        
        <!-- 하단 페이지네이션 컨트롤 -->
        <div id='paginationControls' style='display: none; text-align: center; margin-top: 25px; margin-bottom: 25px;'>
            <button class='page-btn' onclick='changePage(-1)' id='prevBtn'>◀ 이전</button>
            <span id='pageInfo' style='margin: 0 25px; font-weight: bold; font-size: 16px; color: #ffffff;'></span>
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
                allRows = Array.from(tbody.getElementsByTagName("tr"));
                updateTable();
            };

            function updateTable() {
                const tbody = document.getElementById("tableBody");
                const totalPages = Math.ceil(allRows.length / ROWS_PER_PAGE) || 1;
                
                if (currentPage < 1) currentPage = 1;
                if (currentPage > totalPages) currentPage = totalPages;

                tbody.innerHTML = "";
                const startIdx = (currentPage - 1) * ROWS_PER_PAGE;
                const endIdx = startIdx + ROWS_PER_PAGE;
                
                for(let i = startIdx; i < endIdx && i < allRows.length; i++) {
                    allRows[i].style.display = ""; 
                    tbody.appendChild(allRows[i]);
                }

                document.getElementById("pageInfo").innerText = currentPage + " / " + totalPages;
                document.getElementById("prevBtn").disabled = (currentPage === 1);
                document.getElementById("nextBtn").disabled = (currentPage === totalPages);
                document.getElementById("paginationControls").style.display = (allRows.length > ROWS_PER_PAGE) ? "block" : "none";
            }

            function changePage(delta) {
                currentPage += delta;
                updateTable();
                window.scrollTo(0, 0); 
            }

            function sortTable(n) {
                if (sortCol === n) { sortAsc = !sortAsc; } 
                else { sortCol = n; sortAsc = true; }
                
                document.querySelectorAll('.sort-icon').forEach(icon => icon.innerHTML = '');
                const iconEl = document.getElementById('icon-' + n);
                if (iconEl) { iconEl.innerHTML = sortAsc ? "▲" : "▼"; }
                
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
                    
                    let cmpA = (!isNaN(numA) && cleanA === numA.toString()) ? numA : valA;
                    let cmpB = (!isNaN(numB) && cleanB === numB.toString()) ? numB : valB;
                    
                    if (cmpA < cmpB) return sortAsc ? -1 : 1;
                    if (cmpA > cmpB) return sortAsc ? 1 : -1;
                    return 0;
                });
                
                currentPage = 1;
                updateTable();
            }
        </script>
    </body>
    </html>
    """

    # 컴포넌트의 높이를 데이터 개수에 맞춰 동적으로 계산하여 스크롤바 방지
    num_rows = min(len(filtered_df), 100)
    iframe_height = 80 + (num_rows * 39) + (100 if len(filtered_df) > 100 else 30)
    
    # 스트림릿 전용 컴포넌트로 안전하고 완벽하게 HTML/JS 표 렌더링
    components.html(iframe_html, height=iframe_height, scrolling=False)
