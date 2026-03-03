import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 데이터베이스 초기화 및 샘플 데이터 생성
def init_db():
    conn = sqlite3.connect('my_data.db')
    cursor = conn.cursor()
    # 테이블 생성 (날짜, 항목, 금액)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            item TEXT NOT NULL,
            amount INTEGER NOT NULL
        )
    ''')
    
    # 샘플 데이터가 없는 경우 삽입
    cursor.execute("SELECT count(*) FROM records")
    if cursor.fetchone()[0] == 0:
        sample_data = [
            ('2023-01-15', 'Office Supplies', 50000),
            ('2023-01-20', 'Coffee', 5000),
            ('2023-02-10', 'Internet Bill', 35000),
            ('2024-01-05', 'New Monitor', 300000),
            ('2024-03-12', 'Lunch', 12000),
            ('2024-03-15', 'Keyboard', 85000)
        ]
        cursor.executemany("INSERT INTO records (date, item, amount) VALUES (?, ?, ?)", sample_data)
        conn.commit()
    conn.close()

# 2. 데이터 조회 함수
def get_filtered_data(year, month):
    conn = sqlite3.connect('my_data.db')
    # SQL의 strftime을 사용하여 년/월 필터링
    query = f"SELECT date, item, amount FROM records WHERE strftime('%Y', date) = '{year}' AND strftime('%m', date) = '{month:02d}'"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def main():
    st.set_page_config(page_title="DB Data Viewer", page_icon="📅", layout="wide")
    
    # DB 초기화 실행
    init_db()

    st.title("📅 월별 데이터 조회 시스템")
    st.markdown("데이터베이스에 연결하여 선택한 **년도와 월**에 해당하는 내역을 표시합니다.")
    st.divider()

    # 3. 사이드바 검색 필터
    st.sidebar.header("🔍 조회 조건 설정")
    
    current_year = datetime.now().year
    selected_year = st.sidebar.selectbox("년도 선택", [str(y) for y in range(current_year, current_year - 5, -1)])
    selected_month = st.sidebar.slider("월 선택", 1, 12, datetime.now().month)

    # 4. 데이터 로드 및 출력
    data = get_filtered_data(selected_year, selected_month)

    if not data.empty:
        st.subheader(f"📊 {selected_year}년 {selected_month}월 조회 결과")
        
        # 요약 지표
        total_amount = data['amount'].sum()
        count = len(data)
        
        col1, col2 = st.columns(2)
        col1.metric("총 항목 수", f"{count} 건")
        col2.metric("총 합계 금액", f"{total_amount:,} 원")

        # 데이터 테이블
        st.dataframe(data, use_container_width=True)
        
        # 간단한 차트 시각화
        st.bar_chart(data.set_index('item')['amount'])
    else:
        st.warning(f"⚠️ {selected_year}년 {selected_month}월에 해당하는 데이터가 없습니다.")
        st.info("샘플 데이터 확인: 2023년 1월/2월 또는 2024년 1월/3월을 선택해보세요.")

if __name__ == "__main__":
    main()
