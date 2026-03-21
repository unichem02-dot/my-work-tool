import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection
import datetime

# 1. 페이지 기본 설정
st.set_page_config(page_title="유니매입가격정보 - 인상공문 검색", page_icon="📈", layout="wide")

# 2. 구글 시트 데이터 불러오기 (캐싱 적용으로 속도 향상)
@st.cache_data(ttl=600) # 10분마다 데이터 갱신
def load_data():
    # secrets.toml에 설정된 구글 시트 연결
    conn = st.connection("gsheets", type=GSheetsConnection)
    # worksheet 이름이나 URL을 지정하여 데이터를 가져옵니다.
    df = conn.read(worksheet="시트1") 
    
    # 데이터 전처리 (빈 행 제거 및 컬럼명 앞뒤 공백 제거 - 에러 방지용)
    df = df.dropna(how="all")
    df.columns = df.columns.astype(str).str.strip()
    return df

try:
    data = load_data()
except Exception as e:
    st.error("구글 시트를 불러오는 데 실패했습니다. '.streamlit/secrets.toml' 설정과 공유 상태를 확인해주세요.")
    st.stop()

# 3. 사이드바: 검색 및 필터링 기능
st.sidebar.header("🔍 상세 검색")

# 업로드해주신 엑셀 데이터에 맞춘 실제 컬럼명
col_vendor = "업체명"
col_item = "물품명"
col_date = "인상날짜"

# --- 에러 방지 코드: 컬럼명 확인 ---
required_cols = [col_vendor, col_item, col_date]
missing_cols = [col for col in required_cols if col not in data.columns]

if missing_cols:
    st.error(f"🚨 컬럼명 오류: 구글 시트에서 '{', '.join(missing_cols)}' 열을 찾을 수 없습니다.")
    st.info(f"💡 현재 시트에 있는 실제 1열 제목들: {', '.join(map(str, data.columns))}")
    st.warning("👉 해결방법: 구글 시트의 첫 번째 줄 제목을 확인해주세요.")
    st.stop()
# ------------------------------------------

# 업체명 필터 (다중 선택)
# 빈 값(NaN) 제거 후 리스트 생성
vendor_list = ["전체"] + list(data[col_vendor].dropna().unique())
selected_vendors = st.sidebar.multiselect("🏢 업체명 선택", vendor_list, default=["전체"])

# 품목명 검색 (텍스트 입력)
search_item = st.sidebar.text_input("📦 물품명 검색", "")

# 4. 필터링 로직 적용
filtered_df = data.copy()

if "전체" not in selected_vendors and len(selected_vendors) > 0:
    filtered_df = filtered_df[filtered_df[col_vendor].isin(selected_vendors)]

if search_item:
    # 대소문자 구분 없이 포함된 문자열 검색
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(search_item, case=False, na=False)]

# NaN(빈칸) 데이터 깔끔하게 빈 문자열로 처리 (화면 표시용)
filtered_df = filtered_df.fillna("")

# 5. 메인 화면 구성
st.title("📈 유니매입가격정보 (인상공문 현황)")
st.markdown("구글 시트에 추가된 단가 인상 공문 내역을 검색하고 조회할 수 있습니다.")

# 상단 요약 지표 (Metrics)
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="총 검색된 건수", value=f"{len(filtered_df)} 건")
with col2:
    if not filtered_df.empty and col_date in filtered_df.columns:
        # 날짜 데이터 중 가장 큰(최근) 값 찾기 (빈칸 제외)
        valid_dates = [d for d in filtered_df[col_date].tolist() if str(d).strip() != ""]
        if valid_dates:
            latest_date = max(valid_dates)
            st.metric(label="최근 인상 날짜", value=str(latest_date))
        else:
            st.metric(label="최근 인상 날짜", value="-")
    else:
        st.metric(label="최근 인상 날짜", value="-")
with col3:
    if not filtered_df.empty:
        # 빈칸 제외하고 순수 업체 수만 카운트
        valid_vendors = [v for v in filtered_df[col_vendor].unique() if str(v).strip() != ""]
        st.metric(label="검색된 업체 수", value=f"{len(valid_vendors)} 개사")
    else:
        st.metric(label="검색된 업체 수", value="0 개사")
st.markdown("---")

# 6. 데이터프레임 출력
st.subheader("📋 상세 내역")
if filtered_df.empty:
    st.warning("검색 조건에 맞는 데이터가 없습니다.")
else:
    # 화면에 꽉 차게 데이터프레임 표시, 인덱스는 숨김 처리
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

# 7. 하단 안내문
st.caption("💡 엑셀(구글 시트)에 새로운 내용을 추가하면 약 10분 뒤, 혹은 우측 상단의 'Clear Cache'를 누르면 즉시 사이트에 반영됩니다.")
