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
    # 주의: 실제 구글 시트의 컬럼명과 아래 코드의 컬럼명이 일치해야 합니다.
    df = conn.read(worksheet="시트1") 
    
    # 데이터 전처리 (빈 행 제거)
    df = df.dropna(how="all")
    return df

try:
    data = load_data()
except Exception as e:
    st.error("구글 시트를 불러오는 데 실패했습니다. '.streamlit/secrets.toml' 설정과 공유 상태를 확인해주세요.")
    st.stop()

# 3. 사이드바: 검색 및 필터링 기능
st.sidebar.header("🔍 상세 검색")

# 가정된 엑셀 컬럼명: '공문일자', '업체명', '브랜드', '품목명', '기존단가', '인상단가', '적용일자', '비고'
# (실제 엑셀 컬럼명에 맞춰 아래 문자열들을 수정해주세요)
col_vendor = "업체명"
col_item = "품목명"
col_date = "공문일자"

# --- 추가된 에러 방지 코드: 컬럼명 확인 ---
required_cols = [col_vendor, col_item, col_date]
missing_cols = [col for col in required_cols if col not in data.columns]

if missing_cols:
    st.error(f"🚨 컬럼명 오류: 구글 시트에서 '{', '.join(missing_cols)}' 열을 찾을 수 없습니다.")
    st.info(f"💡 현재 시트에 있는 실제 1열 제목들: {', '.join(map(str, data.columns))}")
    st.warning("👉 해결방법: 파이썬 코드의 37~39번째 줄 글자를 아래 시트 제목과 똑같이(띄어쓰기 포함) 바꾸거나, 구글 시트의 첫 번째 줄 제목을 바꿔주세요!")
    st.stop()
# ------------------------------------------

# 업체명 필터 (다중 선택)
vendor_list = ["전체"] + list(data[col_vendor].dropna().unique())
selected_vendors = st.sidebar.multiselect("🏢 업체명 선택", vendor_list, default=["전체"])

# 품목명 검색 (텍스트 입력)
search_item = st.sidebar.text_input("📦 품목명 검색", "")

# 4. 필터링 로직 적용
filtered_df = data.copy()

if "전체" not in selected_vendors and len(selected_vendors) > 0:
    filtered_df = filtered_df[filtered_df[col_vendor].isin(selected_vendors)]

if search_item:
    # 대소문자 구분 없이 포함된 문자열 검색
    filtered_df = filtered_df[filtered_df[col_item].astype(str).str.contains(search_item, case=False, na=False)]

# 5. 메인 화면 구성
st.title("📈 유니매입가격정보 (인상공문 현황)")
st.markdown("구글 시트에 추가된 단가 인상 공문 내역을 검색하고 조회할 수 있습니다.")

# 상단 요약 지표 (Metrics)
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="총 인상 공문 건수", value=f"{len(filtered_df)} 건")
with col2:
    if not filtered_df.empty:
        latest_date = filtered_df[col_date].max()
        st.metric(label="최근 공문 등록일", value=str(latest_date))
    else:
        st.metric(label="최근 공문 등록일", value="-")
with col3:
    st.metric(label="검색된 업체 수", value=f"{filtered_df[col_vendor].nunique()} 개사")
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
