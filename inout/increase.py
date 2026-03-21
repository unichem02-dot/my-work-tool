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

# 1. 페이지 기본 설정
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# ==========================================
# 🎨 TOmBOy's INOUT 스타일 다크 테마 커스텀 CSS
# ==========================================
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden !important;}
    [data-testid="stHeader"] {display: none !important;}
    
    [data-testid="stAppViewContainer"] { background-color: #2b323c; }
    .main .block-container { padding-top: 1rem; max-width: 98%; }
    
    h1, h2, h3, h4, h5, p, span, label { color: #ffffff !important; }
    
    /* 버튼 공통 스타일 */
    div.stButton > button {
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0px 10px !important;
    }
    
    /* 검색 버튼 (Primary) -> 파란색 */
    button[kind="primary"] {
        background-color: #4e8cff !important;
        border-color: #4e8cff !important;
        color: white !important;
    }
    button[kind="primary"]:hover { 
        background-color: #3b76e5 !important; 
    }

    /* 전체보기/로그아웃 (Secondary) -> 올리브색 */
    button[kind="secondary"] {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
    }
    
    /* 💾 EXCEL/CSV 버튼 정렬 및 스타일 (높이 42px 강제 일치) */
    div[data-testid="stDownloadButton"] {
        display: flex;
        align-items: center;
        height: 42px;
        margin-top: 0px !important;
    }
    div[data-testid="stDownloadButton"] button {
        background-color: #525252 !important;
        border-color: #525252 !important;
        color: white !important;
        height: 42px !important;
        width: 100% !important;
        padding: 0 !important;
        margin: 0 !important;
        font-family: 'Malgun Gothic', sans-serif !important;
        font-weight: bold !important;
    }
    div[data-testid="stDownloadButton"] button:hover {
        background-color: #3f3f3f !important;
    }
    
    /* 타이틀 클릭 버튼 */
    button[kind="tertiary"] {
        display: flex !important;
        justify-content: flex-start !important;
        padding: 0 !important;
        background-color: transparent !important;
        border: none !important;
        margin-top: 5px !important;
    }
    button[kind="tertiary"] p {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin: 0 !important;
    }
    button[kind="tertiary"]:hover p { color: #4e8cff !important; }
    
    /* 입력창 내부 디자인 */
    div[data-testid="stTextInput"] input, div[data-baseweb="select"] > div {
        color: #1e293b !important;
        font-weight: bold !important;
        background-color: #f8f9fa !important;
    }
    div[data-baseweb="select"] span { color: #1e293b !important; }
    
    hr { margin: 12px 0px 12px 0px; border: 0.5px solid #4a5568 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 로그인 기능
# ==========================================
def check_password():
    TIMEOUT_SECONDS = 10800
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

# 2. 데이터 불러오기
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
except:
    st.error("데이터를 불러오지 못했습니다.")
    st.stop()

col_vendor, col_item, col_date = "업체명", "물품명", "인상날짜"
data = data.fillna("")

# ==========================================
# 🛠️ 상태 관리
# ==========================================
if 'act_mode' not in st.session_state: st.session_state.act_mode = "init"
if 'act_t1_v' not in st.session_state: st.session_state.act_t1_v = ""
if 'act_t1_i' not in st.session_state: st.session_state.act_t1_i = ""
if 'act_t1_y' not in st.session_state: st.session_state.act_t1_y = "전체"
if 'act_t2_v' not in st.session_state: st.session_state.act_t2_v = "전체"
if 'act_t2_i' not in st.session_state: st.session_state.act_t2_i = "전체"
if 'act_t2_y' not in st.session_state: st.session_state.act_t2_y = "전체"

def do_search_t1():
    st.session_state.act_mode = "text"
    st.session_state.act_t1_v = st.session_state.ui_t1_v
    st.session_state.act_t1_i = st.session_state.ui_t1_i
    st.session_state.act_t1_y = st.session_state.ui_t1_y
    st.session_state.ui_t1_v = ""
    st.session_state.ui_t1_i = ""
    st.session_state.ui_t1_y = "전체"

def do_search_t2():
    st.session_state.act_mode = "dropdown"
    st.session_state.act_t2_v = st.session_state.ui_t2_v
    st.session_state.act_t2_i = st.session_state.ui_t2_i
    st.session_state.act_t2_y = st.session_state.ui_t2_y
    st.session_state.ui_t2_v = "전체"
    st.session_state.ui_t2_i = "전체"
    st.session_state.ui_t2_y = "전체"

def do_reset():
    st.session_state.act_mode = "init"
    st.session_state.act_t1_v = ""
    st.session_state.act_t1_i = ""
    st.session_state.act_t1_y = "전체"
    st.session_state.act_t2_v = "전체"
    st.session_state.act_t2_i = "전체"
    st.session_state.act_t2_y = "전체"
    st.session_state.ui_t1_v = ""
    st.session_state.ui_t1_i = ""
    st.session_state.ui_t1_y = "전체"
    st.session_state.ui_t2_v = "전체"
    st.session_state.ui_t2_i = "전체"
    st.session_state.ui_t2_y = "전체"

def do_full_refresh():
    load_data.clear()
    do_reset()

# ==========================================
# UI 상단 검색 영역
# ==========================================
col_t, col_l = st.columns([8.5, 1.5])
with col_t: 
    st.button("📈 유니매입가격정보 (인상공문 현황)", type="tertiary", on_click=do_full_refresh)
with col_l:
    if st.button("🔓 LOGOUT", use_container_width=True, type="secondary"):
        st.session_state["authenticated"] = False
        st.query_params.clear()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

years_set = set()
if col_date in data.columns:
    for d in data[col_date].dropna().unique():
        s = str(d).strip().replace('-', '.').replace('/', '.')
        parts = s.split('.')
        if parts and parts[0].isdigit():
            y = parts[0]
            if len(y) == 2: years_set.add("20" + y)
            elif len(y) == 4: years_set.add(y)
year_list = ["전체"] + [f"{y}년" for y in sorted(list(years_set), reverse=True)]

vendor_list = ["전체"] + sorted([str(v).strip() for v in data[col_vendor].unique() if str(v).strip() != ""])
item_list = ["전체"] + sorted([str(v).strip() for v in data[col_item].unique() if str(v).strip() != ""])

# 1라인 검색
c1_1, c1_2, c1_3, c1_4, c1_5 = st.columns([2.5, 2.5, 1.5, 1.7, 1.8])
with c1_1: st.text_input("🏢 업체명 타이핑", placeholder="부분 일치 검색", key="ui_t1_v")
with c1_2: st.text_input("📦 물품명 타이핑", placeholder="부분 일치 검색", key="ui_t1_i")
with c1_3: st.selectbox("📅 인상연도", year_list, key="ui_t1_y")
with c1_4:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔍 텍스트 검색", use_container_width=True, type="primary", on_click=do_search_t1)
with c1_5:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("📂 전체보기", use_container_width=True, type="secondary", on_click=do_reset, key="res1")

# 2라인 검색
c2_1, c2_2, c2_3, c2_4, c2_5 = st.columns([2.5, 2.5, 1.5, 1.7, 1.8])
with c2_1: st.selectbox("🏢 업체명 선택", vendor_list, key="ui_t2_v")
with c2_2: st.selectbox("📦 물품명 선택", item_list, key="ui_t2_i")
with c2_3: st.selectbox("📅 연도 선택", year_list, key="ui_t2_y")
with c2_4:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔍 선택 검색", use_container_width=True, type="primary", on_click=do_search_t2)
with c2_5:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("📂 전체보기", use_container_width=True, type="secondary", on_click=do_reset, key="res2")

# 필터링
filtered_df = data.copy()
if st.session_state.act_mode == "text":
    if st.session_state.act_t1_v:
        filtered_df = filtered_df[filtered_df[col_vendor].astype(str).str.contains(st.session_state.act_t1_v, case=False, na=False)]
    if st.session_state.act_t1_i:
        filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(st.session_state.act_t1_i, case=False, na=False)]
    if st.session_state.act_t1_y != "전체":
        ty = st.session_state.act_t1_y.replace("년", "")
        filtered_df = filtered_df[filtered_df[col_date].apply(lambda d: str(d).strip().replace('-', '.').replace('/', '.').split('.')[0] in [ty, ty[2:]])]
elif st.session_state.act_mode == "dropdown":
    if st.session_state.act_t2_v != "전체":
        filtered_df = filtered_df[filtered_df[col_vendor].astype(str) == st.session_state.act_t2_v]
    if st.session_state.act_t2_i != "전체":
        filtered_df = filtered_df[filtered_df[col_item].astype(str) == st.session_state.act_t2_i]
    if st.session_state.act_t2_y != "전체":
        ty = st.session_state.act_t2_y.replace("년", "")
        filtered_df = filtered_df[filtered_df[col_date].apply(lambda d: str(d).strip().replace('-', '.').replace('/', '.').split('.')[0] in [ty, ty[2:]])]

sort_cols = [c for c in [col_date, col_vendor, col_item] if c in filtered_df.columns]
if sort_cols:
    filtered_df = filtered_df.sort_values(by=sort_cols, ascending=[False if c == col_date else True for c in sort_cols])

# ==========================================
# 📊 요약 지표 및 버튼 레이아웃
# ==========================================
latest_date = "-"
if not filtered_df.empty:
    valid_dates = [d for d in filtered_df[col_date].tolist() if str(d).strip() != ""]
    if valid_dates: latest_date = max(valid_dates)
valid_vendors_cnt = len(filtered_df[col_vendor].unique()) if not filtered_df.empty else 0

st.markdown("<br>", unsafe_allow_html=True)
col_bar, col_print, col_excel = st.columns([7, 1.5, 1.5])

with col_bar:
    st.markdown(f"""
        <div style="background-color: #353b48; height: 42px; padding: 0 20px; border-radius: 8px; color: #ffffff; font-size: 15px; display: flex; justify-content: space-around; align-items: center; border: 1px solid #4a5568;">
            <span>🔍 검색 건수 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{len(filtered_df):,}</span> 건</span>
            <span style="color: #4a5568;">|</span>
            <span>📅 최근 인상 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{latest_date}</span></span>
            <span style="color: #4a5568;">|</span>
            <span>🏢 업체 수 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{valid_vendors_cnt:,}</span> 개사</span>
        </div>
    """, unsafe_allow_html=True)

with col_print:
    html_table_p = filtered_df.to_html(index=False, escape=True)
    html_table_p = html_table_p.replace('border="1" class="dataframe"', 'class="custom-table"')
    html_table_p = html_table_p.replace('<th>물품명</th>', '<th style="width: 18%;">물품명</th>').replace('<th>메모</th>', '<th style="width: 34%;">메모</th>').replace('<th>기존가날짜</th>', '<th style="width: 8%;">기존가날짜</th>')
    p_content = f"<html><head><style>body {{ font-family: 'Malgun Gothic'; }} .custom-table {{ width: 100%; border-collapse: collapse; }} th, td {{ border: 1px solid #aaa; padding: 6px; text-align: center; }} th {{ background: #f1f5f9; }}</style></head><body><h2 style='text-align:center;'>인상공문 검색결과</h2>{html_table_p}</body></html>"
    components.html(f"""
        <html><body style='margin:0; padding:0;'>
        <style>
            .btn {{ width: 100%; height: 42px; background: #525252; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-family: 'Malgun Gothic'; font-size: 14px; display: flex; align-items: center; justify-content: center; }}
            .btn:hover {{ background: #3f3f3f; }}
        </style>
        <button class='btn' onclick='pr()'>🖨️ PRINT</button>
        <script>function pr(){{var w=window.open('','_blank');w.document.write({json.dumps(p_content)});w.document.close();setTimeout(function(){{w.print();}},250);}}</script>
        </body></html>
    """, height=42)

with col_excel:
    try:
        excel_io = io.BytesIO()
        with pd.ExcelWriter(excel_io, engine='openpyxl') as wr:
            filtered_df.to_excel(wr, index=False, sheet_name='Sheet1')
        st.download_button("💾 EXCEL", data=excel_io.getvalue(), file_name=f"export_{get_kst_now().strftime('%Y%m%d')}.xlsx", use_container_width=True)
    except:
        st.download_button("💾 CSV", data=filtered_df.to_csv(index=False).encode('utf-8-sig'), file_name="export.csv", use_container_width=True)

conds = []
if st.session_state.act_mode == "text":
    if st.session_state.act_t1_v: conds.append(f"업체({st.session_state.act_t1_v})")
    if st.session_state.act_t1_i: conds.append(f"물품({st.session_state.act_t1_i})")
    if st.session_state.act_t1_y != "전체": conds.append(f"연도({st.session_state.act_t1_y})")
elif st.session_state.act_mode == "dropdown":
    if st.session_state.act_t2_v != "전체": conds.append(f"업체({st.session_state.act_t2_v})")
    if st.session_state.act_t2_i != "전체": conds.append(f"물품({st.session_state.act_t2_i})")
    if st.session_state.act_t2_y != "전체": conds.append(f"연도({st.session_state.act_t2_y})")
search_info = f"<span style='color:#ffeb3b;'>[검색조건: {' + '.join(conds)}]</span>" if conds else "(전체 데이터)"
st.markdown(f"#### 📋 상세 내역 {search_info} <span style='font-size:12px; color:#cbd5e1; font-weight:normal; margin-left:10px;'>(제목 클릭 시 정렬)</span>", unsafe_allow_html=True)

# ==========================================
# 📋 메인 테이블 (스크롤바 제거 버전)
# ==========================================
if filtered_df.empty:
    st.warning("👀 조건에 맞는 데이터가 없습니다.")
else:
    def get_th_class(col):
        if "기존" in str(col): return "th-in"
        if "인상" in str(col): return "th-out"
        return "th-etc" if "메모" in str(col) else "th-base"
    def get_td_class(col):
        if any(x in str(col) for x in ["업체", "물품", "메모"]): return "tl"
        return "tr" if any(x in str(col) for x in ["가", "폭", "수량"]) else "tc"

    rows_html = []
    for idx, row in enumerate(filtered_df.itertuples(index=False)):
        rs = "<tr>"
        for i, col_name in enumerate(filtered_df.columns):
            val = html.escape(str(row[i])) if row[i] != "" else ""
            cls = get_td_class(col_name) + (" bold-col" if col_name in ["물품명", "인상폭"] else "")
            rs += f"<td class='{cls}'>{val}</td>"
        rows_html.append(rs + "</tr>")

    t_html = f"""
    <!DOCTYPE html><html><head><meta charset='utf-8'><style>
    body {{ background: #2b323c; font-family: 'Malgun Gothic'; margin: 0; padding: 0; color: #1e293b; overflow: hidden; }}
    .custom-table {{ width: 100%; border-collapse: collapse; background: white; font-size: 15px; table-layout: fixed; }}
    .custom-table th, .custom-table td {{ border: 1px solid #d0d0d0; padding: 8px 10px; word-wrap: break-word; }}
    .custom-table th {{ color: white; background: #353b48; font-weight: bold; cursor: pointer; user-select: none; position: relative; }}
    .th-in {{ background: #3b5b88 !important; }} .th-out {{ background: #b8860b !important; }} .th-etc {{ background: #757c43 !important; }}
    .tc {{ text-align: center; }} .tl {{ text-align: left; }} .tr {{ text-align: right; }}
    .bold-col {{ font-weight: 900; color: black !important; }}
    .custom-table tr:nth-child(even) td {{ background-color: #f8f9fa; }}
    .sort-icon {{ font-size: 10px; color: #ffeb3b; margin-left: 5px; }}
    .pagination {{ text-align: center; padding: 20px; background: #2b323c; }}
    .page-btn {{ padding: 8px 16px; margin: 0 5px; cursor: pointer; background: #4e8cff; color: white; border: none; border-radius: 4px; font-weight: bold; }}
    .page-btn:disabled {{ background: #4a5568; cursor: not-allowed; }}
    .page-info {{ color: white; margin: 0 15px; font-weight: bold; }}
    </style></head><body>
    <table class='custom-table' id='mainTable'>
    <thead><tr>
    """
    for i, col in enumerate(filtered_df.columns):
        w = "width:18%;" if "물품" in col else "width:34%;" if "메모" in col else "width:8%;" if "기존가날짜" in col else ""
        t_html += f"<th class='{get_th_class(col)}' style='{w}' onclick='sortTable({i})'>{col}<span class='sort-icon' id='icon-{i}'></span></th>"
    
    t_html += f"""
    </tr></thead><tbody id='tableBody'>{''.join(rows_html)}</tbody></table>
    <div id='nav' class='pagination'>
        <button id='prev' class='page-btn' onclick='changePage(-1)'>◀ 이전</button>
        <span id='pageLabel' class='page-info'></span>
        <button id='next' class='page-btn' onclick='changePage(1)'>다음 ▶</button>
    </div>
    <script>
    let sortOrder = 1; let currentPage = 1; const rowsPerPage = 100;
    function renderTable() {{
        const tbody = document.getElementById("tableBody");
        const rows = Array.from(tbody.rows);
        const totalPages = Math.ceil(rows.length / rowsPerPage);
        if (currentPage < 1) currentPage = 1;
        if (currentPage > totalPages) currentPage = totalPages;
        rows.forEach((row, index) => {{
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            row.style.display = (index >= start && index < end) ? "" : "none";
        }});
        document.getElementById("pageLabel").innerText = currentPage + " / " + (totalPages || 1);
        document.getElementById("prev").disabled = (currentPage === 1);
        document.getElementById("next").disabled = (currentPage === totalPages || totalPages === 0);
        document.getElementById("nav").style.display = rows.length > rowsPerPage ? "block" : "none";
    }}
    function changePage(delta) {{ currentPage += delta; renderTable(); window.scrollTo(0,0); }}
    function sortTable(n) {{
        const tbody = document.getElementById("tableBody"); const rows = Array.from(tbody.rows); sortOrder *= -1;
        document.querySelectorAll('.sort-icon').forEach(icon => icon.innerText = '');
        document.getElementById('icon-' + n).innerText = sortOrder === 1 ? " ▲" : " ▼";
        rows.sort((a, b) => {{
            let tA = a.cells[n].innerText.trim(); let tB = b.cells[n].innerText.trim();
            let nA = parseFloat(tA.replace(/,/g, '')); let nB = parseFloat(tB.replace(/,/g, ''));
            if (!isNaN(nA) && !isNaN(nB)) {{ return (nA - nB) * sortOrder; }}
            return tA.localeCompare(tB, 'ko') * sortOrder;
        }});
        rows.forEach(row => tbody.appendChild(row)); currentPage = 1; renderTable();
    }}
    window.onload = renderTable;
    </script></body></html>
    """
    # 💡 데이터 개수에 따라 높이를 동적으로 계산 (스크롤 방지 핵심)
    display_rows = min(len(filtered_df), 100)
    # 한 행당 약 45px + 헤더/푸터 약 130px
    dynamic_height = (display_rows * 45) + 130
    if len(filtered_df) > 100: dynamic_height += 40 # 네비게이션 공간 추가
    
    components.html(t_html, height=dynamic_height, scrolling=False)
