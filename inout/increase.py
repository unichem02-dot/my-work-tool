import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. 페이지 기본 설정 (와이드 모드 유지)
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# ==========================================
# 🔒 로그인 기능 (비밀번호 확인)
# ==========================================
def check_password():
    # 로그인 상태 저장 (새로고침해도 풀리지 않도록)
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False

    if not st.session_state["authenticated"]:
        st.title("🔒 보안 접속")
        st.info("유니매입가격정보를 열람하시려면 비밀번호를 입력해주세요.")
        
        # 비밀번호 입력 폼 (엔터키 지원)
        with st.form("login_form"):
            pwd = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력")
            submit = st.form_submit_button("확인")
            
            if submit:
                # secrets에 설정한 tom_password와 비교 (안전하게 문자로 변환)
                if pwd == str(st.secrets.get("tom_password", "")):
                    st.session_state["authenticated"] = True
                    st.rerun()  # 인증 성공 시 메인 화면으로 새로고침
                else:
                    st.error("🚨 비밀번호가 일치하지 않습니다.")
        return False
    return True

# 비밀번호가 틀리면 여기서 사이트 작동을 멈춤 (데이터 유출 완벽 차단)
if not check_password():
    st.stop()

# 2. 구글 시트 데이터 불러오기
@st.cache_data(ttl=600) # 10분마다 데이터 갱신
def load_data():
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(worksheet="시트1") 
    
    # 데이터 전처리 (빈 행 제거 및 컬럼명 공백 제거)
    df = df.dropna(how="all")
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

# --- 에러 방지 코드 ---
required_cols = [col_vendor, col_item, col_date]
missing_cols = [col for col in required_cols if col not in data.columns]

if missing_cols:
    st.error(f"🚨 컬럼명 오류: 구글 시트에서 '{', '.join(missing_cols)}' 열을 찾을 수 없습니다.")
    st.info(f"💡 현재 시트에 있는 실제 1열 제목들: {', '.join(map(str, data.columns))}")
    st.stop()
# --------------------

# NaN(빈칸) 데이터 깔끔하게 처리
data = data.fillna("")

# ==========================================
# UI 레이아웃 시작
# ==========================================

# 상단 제목
st.title("📈 유니매입가격정보 (인상공문 현황)")
st.markdown("단가 인상 내역을 **업체명, 물품명, 날짜**로 쉽고 빠르게 교차 검색해 보세요.")
st.markdown("---")

# ==========================================
# 1. 상세 검색 영역 (가로 3단 배치로 가독성 및 검색 효율 극대화)
# ==========================================
st.markdown("#### 🔍 상세 검색")
search_col1, search_col2, search_col3 = st.columns(3)

with search_col1:
    # 업체명 리스트 (가나다 순 정렬)
    vendor_raw = [str(v).strip() for v in data[col_vendor].unique() if str(v).strip() != ""]
    vendor_list = ["전체"] + sorted(vendor_raw)
    selected_vendors = st.multiselect("🏢 업체명 선택", vendor_list, default=["전체"])

with search_col2:
    # 물품명 검색 (텍스트)
    search_item = st.text_input("📦 물품명 검색", placeholder="예: 황산, 소다 등 부분 검색 가능")

with search_col3:
    # 날짜 리스트 (최신 날짜가 위로 오게 정렬)
    date_raw = [str(d).strip() for d in data[col_date].unique() if str(d).strip() != ""]
    date_list = ["전체"] + sorted(date_raw, reverse=True)
    selected_dates = st.multiselect("📅 인상날짜 선택", date_list, default=["전체"])

# ==========================================
# 2. 필터링 로직 적용 (검색 조건 교차 적용)
# ==========================================
filtered_df = data.copy()

# 업체명 필터 적용
if "전체" not in selected_vendors and len(selected_vendors) > 0:
    filtered_df = filtered_df[filtered_df[col_vendor].isin(selected_vendors)]

# 인상날짜 필터 적용
if "전체" not in selected_dates and len(selected_dates) > 0:
    filtered_df = filtered_df[filtered_df[col_date].astype(str).str.strip().isin(selected_dates)]

# 물품명 텍스트 검색 적용 (대소문자 무시, 포함 여부 확인)
if search_item:
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(search_item, case=False, na=False)]

# 최종 정렬 (날짜순 > 업체명순 > 물품명순)
sort_cols = [c for c in [col_date, col_vendor, col_item] if c in filtered_df.columns]
if sort_cols:
    asc_rules = [False if c == col_date else True for c in sort_cols]
    filtered_df = filtered_df.sort_values(by=sort_cols, ascending=asc_rules)

st.markdown("<br>", unsafe_allow_html=True)

# ==========================================
# 3. 요약 지표 (Metrics) - 검색 결과에 따라 즉각 변동
# ==========================================
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="총 검색된 건수", value=f"{len(filtered_df)} 건")
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
        st.metric(label="검색된 업체 수", value=f"{len(valid_vendors)} 개사")
    else:
        st.metric(label="검색된 업체 수", value="0 개사")

st.markdown("---")

# ==========================================
# 4. 데이터프레임 (상세 내역) 출력
# ==========================================
st.markdown("#### 📋 상세 내역")
if filtered_df.empty:
    st.warning("👀 검색 조건에 맞는 데이터가 없습니다. 다른 조건으로 검색해 보세요.")
else:
    # 100개 초기 노출 제한
    display_df = filtered_df.head(100)
    
    # 꽉 찬 화면, 인덱스 숨김 처리하여 표출
    st.dataframe(display_df, use_container_width=True, hide_index=True, height=500)
    
    if len(filtered_df) > 100:
        st.info(f"💡 총 {len(filtered_df)}건 중 상위 100건만 표시되었습니다. 물품명이나 날짜를 선택하여 범위를 좁혀보세요.")

# 하단 안내
st.markdown("<br>", unsafe_allow_html=True)
st.caption("🔄 구글 시트에 내용 추가 후 우측 상단 메뉴(⋮)에서 'Clear cache'를 누르면 즉시 새로고침 됩니다.")
