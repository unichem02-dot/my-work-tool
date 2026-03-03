import streamlit as st
import pymysql
import pandas as pd
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="월별 입출고 데이터 조회", layout="wide")

# 1. DB 연결 (스트림릿 클라우드의 Secrets 기능을 사용하여 보안 유지)
@st.cache_resource
def init_connection():
    return pymysql.connect(
        host=st.secrets["DB_HOST"],         
        user=st.secrets["DB_USER"],         
        password=st.secrets["DB_PASSWORD"], 
        database=st.secrets["DB_NAME"],     
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )

# 2. 데이터 쿼리 실행 함수
@st.cache_data(ttl=600) # 10분간 데이터 캐싱
def run_query(query, params=None):
    conn = init_connection()
    with conn.cursor() as cursor:
        cursor.execute(query, params)
        result = cursor.fetchall()
    return pd.DataFrame(result)

# --- UI 구성 ---
st.title("📊 년/월별 입출고 데이터 대시보드")

# 3. 테이블 및 년/월 선택 필터
# 알려주신 3개의 테이블을 선택할 수 있도록 구성했습니다.
table_dict = {
    "tomboy2 (inout)": "tomboy2",
    "tomboy (t)": "tomboy",
    "anymod (any)": "anymod"
}

st.subheader("검색 조건 설정")
col_table, col_year, col_month = st.columns(3)

with col_table:
    selected_table_label = st.selectbox("조회할 테이블 선택", list(table_dict.keys()))
    target_table = table_dict[selected_table_label]

current_year = datetime.now().year
years = list(range(current_year - 5, current_year + 2))
months = list(range(1, 13))

with col_year:
    selected_year = st.selectbox("년도 선택", years, index=5)
with col_month:
    selected_month = st.selectbox("월 선택", months, index=datetime.now().month - 1)

# 4. 조회 버튼 및 결과 출력
if st.button("데이터 조회하기", type="primary"):
    try:
        # ⚠️ 주의: 'date_column' 부분을 실제 DB 테이블에 있는 날짜 컬럼명으로 꼭 변경해야 합니다!
        # 예: reg_date, created_at 등
        query = f"""
            SELECT * FROM {target_table} 
            WHERE YEAR(date_column) = %s AND MONTH(date_column) = %s
        """
        
        with st.spinner('데이터를 불러오는 중입니다...'):
            df = run_query(query, (selected_year, selected_month))
        
        if df.empty:
            st.warning(f"[{target_table}] 테이블에 {selected_year}년 {selected_month}월 해당하는 데이터가 없습니다.")
        else:
            st.success(f"[{target_table}] 테이블에서 총 {len(df)}건의 데이터를 불러왔습니다.")
            st.dataframe(df, use_container_width=True) # 표 형태로 출력
            
    except Exception as e:
        st.error(f"데이터베이스 오류가 발생했습니다: {e}")