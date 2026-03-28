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
    div.stButton > button, div.stLinkButton > a {
        border-radius: 8px !important;
        font-weight: bold !important;
        padding: 0px 10px !important;
        display: flex;
        align-items: center;
        justify-content: center;
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

    /* 전체보기/로그아웃/구글시트/즐겨찾기 (Secondary) -> 올리브색 계열 */
    button[kind="secondary"], div.stLinkButton > a {
        background-color: #757c43 !important;
        border-color: #757c43 !important;
        color: white !important;
        text-decoration: none !important;
    }
    button[kind="secondary"]:hover, div.stLinkButton > a:hover { 
        background-color: #646a39 !important; 
    }
    
    /* 💾 EXCEL/CSV 버튼 전용 스타일 */
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
        outline: none !important;
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
# 🔒 로그인 기능 (4시간 유지 + 외부 링크 자동인증 완벽 적용)
# ==========================================
def check_password():
    TIMEOUT_SECONDS = 14400 
    
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    # 💡 1. 링크 접속 (자동 로그인) 처리
    if st.query_params.get("pass") == "uni":
        st.session_state["authenticated"] = True
        st.query_params["auth"] = "true"
        st.query_params["ts"] = str(time.time())
        if "pass" in st.query_params:
            del st.query_params["pass"]
        st.rerun() 

    # 💡 2. 기존 로그인된 상태 유지 관리
    elif st.query_params.get("auth") == "true":
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

    # 💡 3. 인증되지 않았을 때만 로그인 화면 표시
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
    
    # 💡 구글 시트의 변경된 열 순서 강제 지정 (기존가날짜 제외)
    desired_order = ['Favor', '업체명', '물품명', '인상날짜', '인상폭', '인상가', '기존가', '메모']
    # 시트에 존재하는 열만 순서에 맞춰 가져오기 (오류 방지)
    final_cols = [c for c in desired_order if c in data.columns]
    # 지정되지 않은 추가 열이 있다면 뒤쪽에 붙임
    final_cols += [c for c in data.columns if c not in desired_order]
    
    data = data[final_cols]
    
except:
    st.error("데이터를 불러오지 못했습니다.")
    st.stop()

col_vendor, col_item, col_date = "업체명", "물품명", "인상날짜"
data = data.fillna("")

# 💡 'Favor' 또는 'Faver' 열 유동적 감지 (오타 방지)
fav_col = None
for c in data.columns:
    if c.strip().lower() in ['favor', 'faver']:
        fav_col = c
        break

# ==========================================
# 💡 그래프용 가격 변동 히스토리 데이터 생성 
# (기존가날짜가 없으므로 첫 기존가를 X축 '0'으로 강제 생성하여 선 연결)
# ==========================================
history_data = {}
for _, r in data.iterrows():
    v = str(r.get('업체명', '')).strip()
    i = str(r.get('물품명', '')).strip()
    d_str = str(r.get('인상날짜', '')).strip()
    p_new = str(r.get('인상가', '')).strip()
    p_old = str(r.get('기존가', '')).strip()
    p_inc = str(r.get('인상폭', '')).strip()
    
    if not v or not i or not d_str:
        continue
        
    # 문자열에서 숫자만 추출 (에러 방어 포함)
    p_new_clean = ''.join(filter(str.isdigit, p_new.split('.')[0])) if str(p_new).lower() != 'nan' else ""
    p_old_clean = ''.join(filter(str.isdigit, p_old.split('.')[0])) if str(p_old).lower() != 'nan' else ""
    inc_clean = ''.join(filter(str.isdigit, p_inc.split('.')[0])) if str(p_inc).lower() != 'nan' else ""
    
    key = f"{v}:::{i}"
    if key not in history_data:
        history_data[key] = []
        
    # 모든 기록을 임시 저장
    history_data[key].append({
        'date': d_str,
        'p_new': int(p_new_clean) if p_new_clean else None,
        'p_old': int(p_old_clean) if p_old_clean else None,
        'inc': int(inc_clean) if inc_clean else None
    })

# 💡 아이템별로 가장 오래된 기록의 '기존가'를 찾아 X축 '0'에 배치
final_history = {}
for k, records in history_data.items():
    records = sorted(records, key=lambda x: x['date']) # 날짜 오름차순 정렬
    final_list = []
    
    for idx, rec in enumerate(records):
        # 1. 항목의 제일 첫 번째 기록인 경우에만 '0' 시작점 앵커(Anchor) 생성
        if idx == 0 and rec['p_old'] is not None:
            final_list.append({'date': '0', 'price': rec['p_old'], 'inc': None})
        
        # 2. 현재 날짜의 인상가/인상폭 기록 추가 (날짜 중복 방지)
        if rec['p_new'] is not None or rec['inc'] is not None:
            if not any(x['date'] == rec['date'] for x in final_list):
                final_list.append({
                    'date': rec['date'],
                    'price': rec['p_new'],
                    'inc': rec['inc']
                })
    final_history[k] = final_list


# ==========================================
# 🛠️ 상태 관리 (콜백 최적화 적용)
# ==========================================
if 'act_mode' not in st.session_state: st.session_state.act_mode = "init"
if 'act_t1_v' not in st.session_state: st.session_state.act_t1_v = ""
if 'act_t1_i' not in st.session_state: st.session_state.act_t1_i = ""
if 'act_t1_y' not in st.session_state: st.session_state.act_t1_y = "전체"
if 'act_t2_v' not in st.session_state: st.session_state.act_t2_v = "전체"
if 'act_t2_i' not in st.session_state: st.session_state.act_t2_i = "전체"
if 'act_t2_y' not in st.session_state: st.session_state.act_t2_y = "전체"

# 💡 즐겨찾기 필터 모드 (기본값: False - 처음 접속 시 전체 리스트 표시)
if 'show_favorites' not in st.session_state: st.session_state.show_favorites = False

# 💡 검색 시 입력 텍스트를 강제로 비우지 않도록 수정하여 버튼 반응성을 확보
def do_search_t1():
    st.session_state.show_favorites = False # 검색 시 전체 데이터 대상으로 강제 전환
    st.session_state.act_mode = "text"
    st.session_state.act_t1_v = st.session_state.ui_t1_v
    st.session_state.act_t1_i = st.session_state.ui_t1_i
    st.session_state.act_t1_y = st.session_state.ui_t1_y

def do_search_t2():
    st.session_state.show_favorites = False
    st.session_state.act_mode = "dropdown"
    st.session_state.act_t2_v = st.session_state.ui_t2_v
    st.session_state.act_t2_i = st.session_state.ui_t2_i
    st.session_state.act_t2_y = st.session_state.ui_t2_y

def do_reset():
    st.session_state.act_mode = "init"
    st.session_state.show_favorites = False
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

# 💡 즐겨찾기 토글 전용 콜백 함수 (무반응 현상 제거)
def toggle_fav():
    st.session_state.show_favorites = not st.session_state.show_favorites
    st.session_state.act_mode = "init" # 탭 전환 시 혼란 방지를 위해 검색 필터 리셋

# ==========================================
# UI 구성 (상단 버튼 배치 - 5등분)
# ==========================================
col_t, col_f, col_i, col_g, col_l = st.columns([4.0, 1.5, 1.5, 1.5, 1.5])
with col_t: 
    st.button("📈 유니매입가격정보 (인상공문 현황)", type="tertiary", on_click=do_full_refresh)

with col_f:
    # 💡 즉시 반응하는 콜백(on_click) 적용
    if st.session_state.show_favorites:
        st.button("📜 전체 리스트", use_container_width=True, type="primary", on_click=toggle_fav)
    else:
        st.button("⭐ 즐겨찾기", use_container_width=True, type="primary", on_click=toggle_fav)

with col_i:
    st.link_button("🧾 송장텍스트변환", "https://my-work-tool-vtpqjyh9zjypweqr8txz77.streamlit.app/", use_container_width=True)

with col_g:
    st.link_button("📂 Google Sheet", "https://drive.google.com/drive/starred", use_container_width=True)

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
c1_1, c1_2, c1_3, c1_4 = st.columns([3.0, 3.0, 2.0, 2.0])
with c1_1: st.text_input("🏢 업체명 타이핑", placeholder="부분 일치 검색", key="ui_t1_v")
with c1_2: st.text_input("📦 물품명 타이핑", placeholder="부분 일치 검색", key="ui_t1_i")
with c1_3: st.selectbox("📅 인상연도", year_list, key="ui_t1_y")
with c1_4:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔍 텍스트 검색", use_container_width=True, type="primary", on_click=do_search_t1)

# 2라인 검색
c2_1, c2_2, c2_3, c2_4 = st.columns([3.0, 3.0, 2.0, 2.0])
with c2_1: st.selectbox("🏢 업체명 선택", vendor_list, key="ui_t2_v")
with c2_2: st.selectbox("📦 물품명 선택", item_list, key="ui_t2_i")
with c2_3: st.selectbox("📅 연도 선택", year_list, key="ui_t2_y")
with c2_4:
    st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
    st.button("🔍 선택 검색", use_container_width=True, type="primary", on_click=do_search_t2)

# ==========================================
# 필터링 로직
# ==========================================
filtered_df = data.copy()

# 💡 1. 즐겨찾기 최우선 필터링
if st.session_state.show_favorites and fav_col:
    filtered_df = filtered_df[filtered_df[fav_col].astype(str).str.strip().str.lower() == 'v']

# 💡 2. 검색 조건 필터링
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

# 요약 지표 및 버튼 레이아웃
latest_date = "-"
if not filtered_df.empty:
    valid_dates = [d for d in filtered_df[col_date].tolist() if str(d).strip() != ""]
    if valid_dates: latest_date = max(valid_dates)
valid_vendors_cnt = len(filtered_df[col_vendor].unique()) if not filtered_df.empty else 0

st.markdown("<br>", unsafe_allow_html=True)
col_bar, col_print, col_excel = st.columns([7, 1.5, 1.5])

with col_bar:
    fav_mode_txt = "<span style='color:#ffeb3b; margin-left:10px;'>[⭐ 즐겨찾기 모드]</span>" if st.session_state.show_favorites else ""
    st.markdown(f"""
        <div style="background-color: #353b48; height: 42px; padding: 0 20px; border-radius: 8px; color: #ffffff; font-size: 15px; display: flex; justify-content: space-around; align-items: center; border: 1px solid #4a5568;">
            <span>🔍 검색 건수 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{len(filtered_df):,}</span> 건 {fav_mode_txt}</span>
            <span style="color: #4a5568;">|</span>
            <span>📅 최근 인상 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{latest_date}</span></span>
            <span style="color: #4a5568;">|</span>
            <span>🏢 업체 수 : <span style="color: #4e8cff; font-size: 18px; font-weight: bold;">{valid_vendors_cnt:,}</span> 개사</span>
        </div>
    """, unsafe_allow_html=True)

with col_print:
    # 💡 PRINT 데이터 전처리 (소수점 제거 및 '원' 추가)
    print_df = filtered_df.copy()
    for c in print_df.columns:
        print_df[c] = print_df[c].astype(str).str.replace(r'\.0$', '', regex=True)
        if c in ["인상폭", "인상가", "기존가"]:
            print_df[c] = print_df[c].apply(lambda x: f"{x}원" if str(x).strip() != "" and str(x).strip().lower() != "nan" and "원" not in str(x) else ("" if str(x).strip().lower() == "nan" else x))
    
    html_table_p = print_df.to_html(index=False, escape=True)
    html_table_p = html_table_p.replace('border="1" class="dataframe"', 'class="custom-table"')
    
    if fav_col and fav_col in print_df.columns:
        html_table_p = html_table_p.replace(f'<th>{fav_col}</th>', '<th style="width: 4%;">⭐</th>')
        html_table_p = html_table_p.replace('<td>v</td>', '<td style="text-align:center;">⭐</td>').replace('<td>V</td>', '<td style="text-align:center;">⭐</td>')
        
    # 💡 인쇄 화면 폭 비율 재조정 (업체명 9%, 물품명 20%, 메모 19%)
    html_table_p = html_table_p.replace('<th>업체명</th>', '<th style="width: 9%;">업체명</th>')
    html_table_p = html_table_p.replace('<th>물품명</th>', '<th style="width: 20%;">물품명</th>')
    html_table_p = html_table_p.replace('<th>메모</th>', '<th style="width: 19%;">메모</th>')
    html_table_p = html_table_p.replace('<th>인상날짜</th>', '<th style="white-space: nowrap;">인상날짜</th>')
    html_table_p = html_table_p.replace('<th>인상폭</th>', '<th style="white-space: nowrap;">인상폭</th>')
    html_table_p = html_table_p.replace('<th>인상가</th>', '<th style="white-space: nowrap;">인상가</th>')
    html_table_p = html_table_p.replace('<th>기존가</th>', '<th style="white-space: nowrap;">기존가</th>')
    
    # 💡 인쇄 팝업 창을 띄울 때 가로(landscape) 설정 및 td 줄바꿈 방지 스타일 적용
    p_content = "<html><head><style>@page { size: landscape; } body { font-family: 'Malgun Gothic'; } .custom-table { width: 100%; border-collapse: collapse; } th, td { border: 1px solid #aaa; padding: 6px; text-align: center; } th { background: #f1f5f9; } .custom-table td:nth-child(2), .custom-table td:nth-child(4), .custom-table td:nth-child(5), .custom-table td:nth-child(6), .custom-table td:nth-child(7) { white-space: nowrap !important; }</style></head><body><h2 style='text-align:center;'>인상공문 검색결과</h2>" + html_table_p + "</body></html>"
    
    components.html(
        "<html><body style='margin:0; padding:0;'>"
        "<style>"
        ".btn { width: 100%; height: 42px; background: #525252; color: white; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; font-family: 'Malgun Gothic'; font-size: 14px; display: flex; align-items: center; justify-content: center; }"
        ".btn:hover { background: #3f3f3f; }"
        "</style>"
        "<button class='btn' onclick='pr()'>🖨️ PRINT</button>"
        "<script>function pr(){var w=window.open('','_blank');w.document.write(" + json.dumps(p_content) + ");w.document.close();setTimeout(function(){w.print();},250);}</script>"
        "</body></html>", 
        height=42
    )

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
# 📋 메인 테이블 (마우스오버 그래프 및 커스텀 스타일)
# ==========================================
if filtered_df.empty:
    st.warning("👀 조건에 맞는 데이터가 없습니다.")
else:
    def get_th_class(col):
        if "기존" in str(col): return "th-in"
        if "인상" in str(col): return "th-out"
        return "th-etc" if "메모" in str(col) else "th-base"
        
    def get_td_class(col):
        if col == fav_col: return "tc"
        if any(x in str(col) for x in ["업체", "물품", "메모"]): return "tl"
        return "tr" if any(x in str(col) for x in ["가", "폭", "수량"]) else "tc"

    vendor_idx = filtered_df.columns.get_loc('업체명') if '업체명' in filtered_df.columns else -1
    
    rows_html = []
    for idx, row in enumerate(filtered_df.itertuples(index=False)):
        is_fav = False
        if fav_col and fav_col in filtered_df.columns:
            faver_idx = filtered_df.columns.get_loc(fav_col)
            if str(row[faver_idx]).strip().lower() == "v":
                is_fav = True
        
        tr_class = " class='favorite-row'" if is_fav else ""
        rs = f"<tr{tr_class}>"
        
        # 그래프 키 생성을 위해 업체명 텍스트 추출
        v_raw = str(row[vendor_idx]).strip() if vendor_idx >= 0 else ""
        
        for i, col_name in enumerate(filtered_df.columns):
            val_raw = str(row[i]).strip()
            
            # 💡 pandas 자동 할당 소수점(.0) 및 nan 텍스트 방어
            if val_raw.lower() == "nan": 
                val_raw = ""
            if val_raw.endswith(".0"): 
                val_raw = val_raw[:-2]
            
            # 💡 가격 데이터에 '원' 추가 로직 적용
            if col_name in ["인상폭", "인상가", "기존가"] and val_raw != "":
                if not val_raw.endswith("원"):
                    val_raw += "원"
            
            if col_name == fav_col:
                val = "⭐" if val_raw.lower() == "v원" or val_raw.lower() == "v" else ""
            else:
                val = html.escape(val_raw) if val_raw != "" else ""
            
            cls = get_td_class(col_name)
            
            # 💡 강제 줄바꿈 방지 클래스 추가
            if col_name in ["업체명", "인상날짜", "인상폭", "인상가", "기존가"]:
                cls += " nowrap-col"
                
            if col_name == "물품명":
                cls += " text-item-name hover-graph"
                # 💡 마우스오버 이벤트 추가 (업체명 + 물품명 매칭으로 데이터 호출)
                v_safe = v_raw.replace("'", "\\'").replace('"', '\\"')
                i_safe = val_raw.replace("'", "\\'").replace('"', '\\"')
                rs += f"<td class='{cls}' onmousemove=\"showGraph(event, '{v_safe}:::{i_safe}', '{html.escape(val_raw)}')\" onmouseout='hideGraph()'>{val}</td>"
            elif col_name == "인상날짜":
                cls += " bold-col"
                rs += f"<td class='{cls}'>{val}</td>"
            elif col_name == "업체명":
                cls += " text-darkgreen"
                rs += f"<td class='{cls}'>{val}</td>"
            elif col_name == "인상폭":
                cls += " text-red-large"
                rs += f"<td class='{cls}'>{val}</td>"
            elif col_name == "인상가":
                cls += " text-red-110"
                rs += f"<td class='{cls}'>{val}</td>"
            elif col_name == "기존가":
                cls += " text-blue"
                rs += f"<td class='{cls}'>{val}</td>"
            elif col_name == fav_col and val == "⭐":
                rs += f"<td class='{cls}' style='font-size:16px;'>{val}</td>"
            else:
                rs += f"<td class='{cls}'>{val}</td>"
        rows_html.append(rs + "</tr>")

    t_html_base = """
    <!DOCTYPE html><html><head><meta charset='utf-8'>
    <!-- 💡 Chart.js 라이브러리 로드 -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
    body { background: #2b323c; font-family: 'Malgun Gothic'; margin: 0; padding: 0; color: #1e293b; overflow: hidden; }
    .custom-table { width: 100%; border-collapse: collapse; background: white; font-size: 15px; table-layout: fixed; }
    .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; word-wrap: break-word; }
    .custom-table th { color: white; background: #353b48; font-weight: bold; cursor: pointer; user-select: none; position: relative; }
    .th-in { background: #3b5b88 !important; } .th-out { background: #b8860b !important; } .th-etc { background: #757c43 !important; }
    .tc { text-align: center; } .tl { text-align: left; } .tr { text-align: right; }
    
    /* 개별 열 색상 및 굵기 하이라이트 CSS */
    .bold-col { font-weight: 900; color: black !important; }
    .text-item-name { font-weight: 900; color: black !important; font-size: 120% !important; } 
    
    /* 💡 물품명 파란색 점선 완전 제거, 마우스 포인트 손가락 모양 유지 */
    .hover-graph { cursor: pointer; } 
    
    .nowrap-col { white-space: nowrap !important; } 
    .text-darkgreen { font-weight: 900; color: #1b5e20 !important; } 
    .text-red-large { font-weight: 900; color: #e53935 !important; font-size: 130% !important; } 
    .text-red-110 { font-weight: 900; color: red !important; font-size: 110% !important; } 
    .text-blue { font-weight: 900; color: #1e88e5 !important; } 
    
    .custom-table tr:nth-child(even) td { background-color: #f8f9fa; }
    
    .custom-table tr.favorite-row td { background-color: #e8f5e9 !important; }
    .custom-table tr.favorite-row:hover td { background-color: #c8e6c9 !important; cursor: pointer; transition: background-color 0.1s ease; }
    .custom-table tr:not(.favorite-row):hover td { background-color: #e2e6ea !important; cursor: pointer; transition: background-color 0.1s ease; }
    
    .sort-icon { font-size: 10px; color: #ffeb3b; margin-left: 5px; }
    .pagination-container { text-align: center; padding: 15px 0; background: #2b323c; display: flex; justify-content: center; align-items: center; gap: 5px; }
    .page-btn { padding: 6px 12px; cursor: pointer; background: #4e8cff; color: white; border: none; border-radius: 4px; font-weight: bold; font-size: 14px; }
    .page-btn:disabled { background: #4a5568; cursor: not-allowed; opacity: 0.6; }
    .page-num { padding: 6px 12px; cursor: pointer; background: #525252; color: #ddd; border: none; border-radius: 4px; font-size: 14px; }
    .page-num.active { background: #ffeb3b; color: #000; font-weight: 800; }
    </style></head><body>
    
    <!-- 💡 마우스오버 툴팁(그래프) 박스 HTML -->
    <div id="graphTooltip" style="display:none; position:absolute; z-index:9999; width:340px; height:240px; background:white; border:3px solid #1e88e5; border-radius:10px; padding:12px; box-shadow:0px 6px 16px rgba(0,0,0,0.3); pointer-events:none;">
        <h4 id="tooltipTitle" style="margin:0 0 10px 0; font-size:15px; color:#1e293b; text-align:center; font-weight:900; word-break:keep-all;"></h4>
        <div style="position:relative; width:100%; height:170px;">
            <canvas id="hoverChart"></canvas>
        </div>
    </div>
    
    <div id='nav-top' class='pagination-container'></div>
    <table class='custom-table' id='mainTable'>
    <thead><tr>
    """
    
    t_html = t_html_base
    
    # 헤더(제목) 생성 시 Favor 열 제목을 '⭐' 로 자동 변경
    for i, col in enumerate(filtered_df.columns):
        # 💡 업체명은 9%, 물품명은 20%로 넓히고, 메모를 19%로 줄여서 재조정
        if col == fav_col: w = "width:4%;"
        elif "업체" in col: w = "width:9%;"
        elif "물품" in col: w = "width:20%;"
        elif "메모" in col: w = "width:19%;"
        else: w = ""
        
        disp_col = "⭐" if col == fav_col else col
        
        # 💡 헤더에도 nowrap 클래스 적용
        th_cls = get_th_class(col)
        if col in ["업체명", "인상날짜", "인상폭", "인상가", "기존가"]:
            th_cls += " nowrap-col"
            
        t_html += f"<th class='{th_cls}' style='{w}' onclick='sortTable({i})'>{disp_col}<span class='sort-icon' id='icon-{i}'></span></th>"
    
    t_html += "</tr></thead><tbody id='tableBody'>" + "".join(rows_html) + "</tbody></table>"
    
    t_html += """
    <script>
    // 💡 Python에서 생성한 가격 히스토리 데이터 연결
    const priceHistory = """ + json.dumps(final_history) + """;
    
    let hoverChart = null;
    const tooltip = document.getElementById('graphTooltip');
    const tooltipTitle = document.getElementById('tooltipTitle');
    
    function showGraph(event, key, itemName) {
        const history = priceHistory[key];
        // 💡 가격 기록 데이터가 없을 경우 그래프 띄우지 않음
        if (!history || history.length < 1) return;

        // 화면 잘림 방지용 위치 계산 (X, Y 좌표)
        let tx = event.clientX + 20;
        let ty = event.clientY + 20;
        const tWidth = 360; 
        const tHeight = 260;
        
        if (tx + tWidth > window.innerWidth) tx = event.clientX - tWidth - 10;
        if (ty + tHeight > window.innerHeight) ty = event.clientY - tHeight - 10;
        
        tooltip.style.left = tx + 'px';
        tooltip.style.top = ty + 'px';
        tooltip.style.display = 'block';

        const labels = history.map(h => h.date);
        
        // 💡 단가 데이터가 하나라도 있는지 확인
        const hasPrice = history.some(h => h.price !== null);
        let plotData;
        let labelName;
        
        // 단가가 있으면 단가 그래프, 없으면 인상폭 그래프로 스마트 전환
        if (hasPrice) {
            plotData = history.map(h => h.price);
            labelName = '단가(원)';
            tooltipTitle.innerText = itemName + ' [가격 변동 추이]';
        } else {
            plotData = history.map(h => h.inc);
            labelName = '인상폭(원)';
            tooltipTitle.innerText = itemName + ' [인상폭 변동 추이]';
        }

        const ctx = document.getElementById('hoverChart').getContext('2d');
        if (hoverChart) hoverChart.destroy(); // 기존 그래프 파괴 후 재설정

        // 💡 Chart.js 를 활용한 단가 그래프 그리기 (X축에 0과 날짜가 있으면 자동으로 선으로 연결됨)
        hoverChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: labelName,
                    data: plotData,
                    borderColor: '#e53935',
                    backgroundColor: 'rgba(229, 57, 53, 0.1)',
                    borderWidth: 2.5,
                    pointBackgroundColor: '#1e88e5',
                    pointRadius: 5,
                    fill: true,
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: { duration: 0 }, // 즉시 표시
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { font: { size: 11, weight: 'bold' } } },
                    y: { 
                        ticks: { 
                            font: { size: 11, weight: 'bold' },
                            callback: function(value) { return value.toLocaleString() + '원'; }
                        } 
                    }
                }
            }
        });
    }

    function hideGraph() {
        tooltip.style.display = 'none';
        if (hoverChart) {
            hoverChart.destroy();
            hoverChart = null;
        }
    }

    let sortOrder = 1; let currentPage = 1; const rowsPerPage = 50; 
    function renderTable() {
        const tbody = document.getElementById("tableBody");
        const rows = Array.from(tbody.rows);
        const totalPages = Math.ceil(rows.length / rowsPerPage);
        if (currentPage < 1) currentPage = 1;
        if (currentPage > totalPages) currentPage = totalPages;
        rows.forEach((row, index) => {
            const start = (currentPage - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            row.style.display = (index >= start && index < end) ? "" : "none";
        });
        updatePagination(totalPages);
        window.scrollTo(0,0); 
    }
    function updatePagination(totalPages) {
        const container = document.getElementById('nav-top');
        container.innerHTML = "";
        if (totalPages <= 1) return;
        const prevBtn = document.createElement("button");
        prevBtn.className = "page-btn"; prevBtn.innerText = "◀ 이전";
        prevBtn.disabled = (currentPage === 1);
        prevBtn.onclick = () => { currentPage--; renderTable(); };
        container.appendChild(prevBtn);
        let startPage = Math.max(1, currentPage - 4);
        let endPage = Math.min(totalPages, startPage + 9);
        if (endPage - startPage < 9) startPage = Math.max(1, endPage - 9);
        for (let i = startPage; i <= endPage; i++) {
            if (i < 1) continue;
            const pageNum = document.createElement("button");
            pageNum.className = (i === currentPage) ? "page-num active" : "page-num";
            pageNum.innerText = i;
            pageNum.onclick = () => { currentPage = i; renderTable(); };
            container.appendChild(pageNum);
        }
        const nextBtn = document.createElement("button");
        nextBtn.className = "page-btn"; nextBtn.innerText = "다음 ▶";
        nextBtn.disabled = (currentPage === totalPages);
        nextBtn.onclick = () => { currentPage++; renderTable(); };
        container.appendChild(nextBtn);
    }
    function sortTable(n) {
        const tbody = document.getElementById("tableBody"); const rows = Array.from(tbody.rows); sortOrder *= -1;
        document.querySelectorAll('.sort-icon').forEach(icon => icon.innerText = '');
        document.getElementById('icon-' + n).innerText = sortOrder === 1 ? " ▲" : " ▼";
        rows.sort((a, b) => {
            let tA = a.cells[n].innerText.trim(); let tB = b.cells[n].innerText.trim();
            // 💡 숫자 정렬 시 자동으로 붙은 '원' 글자와 콤마 무시하고 계산
            let nA = parseFloat(tA.replace(/,/g, '').replace(/원/g, '')); 
            let nB = parseFloat(tB.replace(/,/g, '').replace(/원/g, ''));
            if (!isNaN(nA) && !isNaN(nB)) { return (nA - nB) * sortOrder; }
            return tA.localeCompare(tB, 'ko') * sortOrder;
        });
        rows.forEach(row => tbody.appendChild(row)); currentPage = 1; renderTable();
    }
    window.onload = renderTable;
    </script></body></html>
    """
    
    display_rows = min(len(filtered_df), 50)
    dynamic_height = (display_rows * 42) + 120
    components.html(t_html, height=dynamic_height, scrolling=False)
