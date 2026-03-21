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
    
    /* Primary 버튼 (검색, 새로고침 등) -> 파란색 */
    button[kind="primary"] {
        background-color: #4e8cff !important;
        border-color: #4e8cff !important;
        color: white !important;
    }
    button[kind="primary"]:hover { 
        background-color: #3b76e5 !important; 
        border-color: #3b76e5 !important; 
    }

    /* Secondary 버튼 (초기화, 로그아웃 등) -> 올리브색 */
    button[kind="secondary"] {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
    }
    button[kind="secondary"]:hover { 
        background-color: #646a39 !important; 
        border-color: #646a39 !important; 
    }
    
    /* 💡 타이틀 버튼 (Tertiary) 스타일링 - 흰색 창 현상 제거 */
    button[kind="tertiary"] {
        display: flex !important;
        justify-content: flex-start !important;
        padding: 0 !important;
        background-color: transparent !important;
        border: none !important;
        box-shadow: none !important;
        margin-top: 5px !important;
        outline: none !important;
    }
    button[kind="tertiary"] p {
        font-size: 1.8rem !important;
        font-weight: 800 !important;
        color: #ffffff !important;
        margin: 0 !important;
        padding: 0 !important;
    }
    button[kind="tertiary"]:hover p {
        color: #4e8cff !important;
    }
    button[kind="tertiary"]:focus {
        background-color: transparent !important;
        color: #ffffff !important;
    }
    
    /* 💡 EXCEL 다운로드 버튼 전용 올리브색 커스텀 */
    div[data-testid="stDownloadButton"] button[kind="primary"] {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
    }
    
    /* 검색 메뉴 굵게 및 색상 (검색창 내부는 가독성을 위해 밝게 유지) */
    div[data-testid="stTextInput"] input, div[data-baseweb="select"] > div {
        color: #1e293b !important;
        font-weight: bold !important;
        background-color: #f8f9fa !important;
    }
    div[data-baseweb="select"] span { color: #1e293b !important; }
    
    /* 구분선 라인 색상 */
    hr { margin: 15px 0px 15px 0px; border: 0.5px solid #4a5568 !important; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 로그인 기능 (비밀번호 확인 + 3시간 세션 유지)
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
    st.error("구글 시트를 불러오는 데 실패했습니다.")
    st.stop()

col_vendor, col_item, col_date = "업체명", "물품명", "인상날짜"
data = data.fillna("")

# ==========================================
# 🛠️ 상태 관리 (검색/전체보기 전용 로직)
# ==========================================
if 'active_vendor' not in st.session_state: st.session_state.active_vendor = "전체"
if 'active_item' not in st.session_state: st.session_state.active_item = "전체"
if 'active_year' not in st.session_state: st.session_state.active_year = "전체"

def do_search():
    """검색 버튼 클릭 시 필터링 적용 및 입력창을 '전체'로 초기화"""
    st.session_state.active_vendor = st.session_state.ui_vendor
    st.session_state.active_item = st.session_state.ui_item
    st.session_state.active_year = st.session_state.ui_year
    # 입력창은 다시 '전체'를 보여줌
    st.session_state.ui_vendor = "전체"
    st.session_state.ui_item = "전체"
    st.session_state.ui_year = "전체"

def do_reset():
    """초기화 및 전체보기 기능"""
    st.session_state.active_vendor = "전체"
    st.session_state.active_item = "전체"
    st.session_state.active_year = "전체"
    st.session_state.ui_vendor = "전체"
    st.session_state.ui_item = "전체"
    st.session_state.ui_year = "전체"

def do_full_refresh():
    """타이틀 클릭: 데이터 강제 갱신 + 초기화"""
    load_data.clear()
    do_reset()

# ==========================================
# UI 레이아웃 시작 (상단 상태바)
# ==========================================
col_t, col_l = st.columns([8.5, 1.5])
with col_t: 
    # 클릭 가능한 타이틀 (흰색 창 현상 방지 CSS 적용됨)
    st.button("📈 유니매입가격정보 (인상공문 현황)", type="tertiary", on_click=do_full_refresh)

with col_l:
    if st.button("🔓 LOGOUT", use_container_width=True, type="secondary"):
        st.session_state["authenticated"] = False
        st.query_params.clear()
        st.rerun()

st.markdown("<hr>", unsafe_allow_html=True)

# ==========================================
# 드롭다운 고유 항목 리스트 추출 ('전체' 포함)
# ==========================================
years_set = set()
if col_date in data.columns:
    for d in data[col_date].dropna().unique():
        s = str(d).strip()
        parts = s.replace('-', '.').replace('/', '.').split('.')
        if parts and parts[0].isdigit():
            y = parts[0]
            if len(y) == 2: years_set.add("20" + y)
            elif len(y) == 4: years_set.add(y)
year_list = ["전체"] + [f"{y}년" for y in sorted(list(years_set), reverse=True)]

# 목록에 '전체'를 다시 추가하여 드롭다운에서 선택 가능하게 함
vendor_list = ["전체"] + sorted([str(v).strip() for v in data[col_vendor].unique() if str(v).strip() != ""])
item_list = ["전체"] + sorted([str(v).strip() for v in data[col_item].unique() if str(v).strip() != ""])

# 1. 상세 검색 영역
search_col1, search_col2, search_col3, search_col4, search_col5 = st.columns([2.5, 2.5, 1.5, 1.2, 1.2])

with search_col1:
    st.selectbox("🏢 업체명 검색", vendor_list, key="ui_vendor")

with search_col2:
    st.selectbox("📦 물품명 검색", item_list, key="ui_item")

with search_col3:
    st.selectbox("📅 인상 연도", year_list, key="ui_year")

with search_col4:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔍 검색", use_container_width=True, type="primary", on_click=do_search)

with search_col5:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("📂 전체보기", use_container_width=True, type="secondary", on_click=do_reset)

# 2. 필터링 로직 (AND 조건)
filtered_df = data.copy()
if st.session_state.active_vendor != "전체":
    filtered_df = filtered_df[filtered_df[col_vendor].astype(str).str.contains(st.session_state.active_vendor, case=False, na=False)]
if st.session_state.active_item != "전체":
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(st.session_state.active_item, case=False, na=False)]
if st.session_state.active_year != "전체":
    target_y = st.session_state.active_year.replace("년", "")
    target_y_short = target_y[2:]
    filtered_df = filtered_df[filtered_df[col_date].apply(lambda d: str(d).strip().split('.')[0] in [target_y, target_y_short])]

# 정렬
sort_cols = [c for c in [col_date, col_vendor, col_item] if c in filtered_df.columns]
if sort_cols:
    asc_rules = [False if c == col_date else True for c in sort_cols]
    filtered_df = filtered_df.sort_values(by=sort_cols, ascending=asc_rules)

# 3. 요약 지표 바
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
            <span>🔍 총 검색 건수 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{len(filtered_df):,}</span> 건</span>
            <span style="color: #4a5568;">|</span>
            <span>📅 최근 인상 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{latest_date}</span></span>
            <span style="color: #4a5568;">|</span>
            <span>🏢 업체 수 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{valid_vendors_cnt:,}</span> 개사</span>
        </div>
    """, unsafe_allow_html=True)

# 4. PRINT/EXCEL 기능 (생략 없이 유지)
html_table = filtered_df.to_html(index=False, escape=True)
html_table = html_table.replace('border="1" class="dataframe"', 'class="custom-table"')
html_table = html_table.replace('<th>물품명</th>', '<th style="width: 18%;">물품명</th>').replace('<th>메모</th>', '<th style="width: 34%;">메모</th>').replace('<th>기존가날짜</th>', '<th style="width: 8%;">기존가날짜</th>')

print_html_content = f"<html><head><meta charset='utf-8'><style>body {{ font-family: 'Malgun Gothic'; }} .custom-table {{ width: 100%; border-collapse: collapse; }} .custom-table th, .custom-table td {{ border: 1px solid #aaa; padding: 6px; text-align: center; }} .custom-table th {{ background: #f1f5f9; }}</style></head><body><h2 style='text-align:center;'>유니매입가격정보 검색결과</h2>{html_table}</body></html>"

with col_print:
    components.html(f"<html><body><style>.btn {{ width: 100%; height: 42px; background: #757c43; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; }}</style><button class='btn' onclick='fastPrint()'>🖨️ PRINT</button><script>function fastPrint() {{ var html = {json.dumps(print_html_content)}; var win = window.open('', '_blank'); win.document.write(html); win.document.close(); setTimeout(function(){{ win.print(); }}, 200); }}</script></body></html>", height=45)

with col_excel:
    excel_output = io.BytesIO()
    try:
        with pd.ExcelWriter(excel_output, engine='openpyxl') as writer:
            filtered_df.to_excel(writer, index=False, sheet_name='검색결과')
        st.download_button("💾 EXCEL", data=excel_output.getvalue(), file_name=f"유니매입단가인상_{get_kst_now().strftime('%Y%m%d')}.xlsx", use_container_width=True, type="primary")
    except:
        st.download_button("💾 EXCEL", data=filtered_df.to_csv(index=False).encode('utf-8-sig'), file_name="export.csv", use_container_width=True, type="primary")

# 5. 검색 조건 표시
conds = []
if st.session_state.active_vendor != "전체": conds.append(f"업체({st.session_state.active_vendor})")
if st.session_state.active_item != "전체": conds.append(f"물품({st.session_state.active_item})")
if st.session_state.active_year != "전체": conds.append(f"연도({st.session_state.active_year})")
search_info = f"<span style='color:#ffeb3b;'>[검색조건: {' + '.join(conds)}]</span>" if conds else "(전체 데이터)"
st.markdown(f"#### 📋 상세 내역 {ads if 'ads' in locals() else search_info}", unsafe_allow_html=True)

# 6. 독립 HTML 테이블 렌더링
if filtered_df.empty:
    st.warning("검색 결과가 없습니다.")
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
        d_s = "" if idx < 100 else " style='display:none;'"
        r_s = f"<tr{d_s}>"
        for i, col_name in enumerate(filtered_df.columns):
            val = html.escape(str(row[i])) if row[i] != "" else ""
            cls = get_td_class(col_name) + (" bold-col" if col_name in ["물품명", "인상폭"] else "")
            r_s += f"<td class='{cls}'>{val}</td>"
        rows_html.append(r_s + "</tr>")

    table_body = "".join(rows_html)
    iframe_html = f"""
    <!DOCTYPE html><html><head><meta charset='utf-8'><style>
    body {{ background: #2b323c; font-family: 'Malgun Gothic'; margin: 0; color: #1e293b; }}
    .custom-table {{ width: 100%; border-collapse: collapse; background: white; font-size: 15px; }}
    .custom-table th, .custom-table td {{ border: 1px solid #d0d0d0; padding: 8px 10px; }}
    .custom-table th {{ color: white; font-weight: bold; cursor: pointer; user-select: none; }}
    .th-base {{ background: #353b48; }} .th-in {{ background: #3b5b88; }} .th-out {{ background: #b8860b; }} .th-etc {{ background: #757c43; }}
    .tc {{ text-align: center; }} .tl {{ text-align: left; }} .tr {{ text-align: right; }}
    .bold-col {{ font-weight: 900; color: black; }}
    .custom-table tr:nth-child(even) td {{ background: #f8f9fa; }}
    </style></head><body>
    <table class='custom-table'><thead><tr>
    """
    for col in filtered_df.columns:
        w = "width:18%;" if "물품" in col else "width:34%;" if "메모" in col else "width:8%;" if "기존가날짜" in col else ""
        iframe_html += f"<th class='{get_th_class(col)}' style='{w}'>{col}</th>"
    iframe_html += f"</tr></thead><tbody>{table_body}</tbody></table></body></html>"
    components.html(iframe_html, height=min(len(filtered_df)*40 + 60, 800), scrolling=True)
