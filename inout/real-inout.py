import streamlit as st
import pandas as pd
import requests
from datetime import datetime
import json

# 1. API를 통한 데이터 조회 함수
def get_api_data(year, month):
    """
    외부 api.php 서버에 데이터를 요청합니다.
    """
    # 실제 api.php의 URL 주소로 수정이 필요합니다.
    api_url = "http://www.unichemical.co.kr/inout/api.php" 
    
    params = {
        "year": year,
        "month": f"{month:02d}"
    }

    try:
        # API 호출 (GET 방식)
        response = requests.get(api_url, params=params, timeout=10)
        
        # HTTP 상태 코드 확인
        if response.status_code == 200:
            # 서버 응답이 비어있는지 확인
            if not response.text.strip():
                st.warning("서버 응답이 비어있습니다. (Empty Response)")
                return pd.DataFrame()
            
            try:
                # JSON 파싱 시도
                data = response.json()
                return pd.DataFrame(data)
            except json.JSONDecodeError:
                # JSON 파싱 실패 시 서버가 보낸 원문 표시 (디버깅용)
                st.error("서버에서 올바른 JSON 형식을 보내지 않았습니다.")
                with st.expander("서버 응답 원문 보기 (Debug)"):
                    st.code(response.text)
                return pd.DataFrame()
        else:
            st.error(f"서버 응답 오류: {response.status_code}")
            with st.expander("에러 내용 보기"):
                st.write(response.text)
            return pd.DataFrame()
            
    except Exception as e:
        st.error(f"API 연결 실패: {e}")
        return pd.DataFrame()

def main():
    st.set_page_config(page_title="API Data Viewer", page_icon="🌐", layout="wide")
    
    st.title("🌐 API 기반 월별 데이터 조회")
    st.markdown("외부 `api.php` 서버와 통신하여 선택한 **년도와 월**의 데이터를 실시간으로 표시합니다.")
    st.divider()

    # 2. 사이드바 검색 필터
    st.sidebar.header("🔍 조회 조건 설정")
    
    current_year = datetime.now().year
    selected_year = st.sidebar.selectbox("년도 선택", [str(y) for y in range(current_year, current_year - 5, -1)])
    selected_month = st.sidebar.slider("월 선택", 1, 12, datetime.now().month)

    # 3. 데이터 로드 (API 호출)
    with st.spinner('서버에서 데이터를 불러오는 중...'):
        data = get_api_data(selected_year, selected_month)

    # 4. 결과 출력
    if not data.empty:
        st.subheader(f"📊 {selected_year}년 {selected_month}월 조회 결과")
        
        # 데이터에 필수 컬럼('date', 'item', 'amount')이 있다고 가정
        if all(col in data.columns for col in ['date', 'item', 'amount']):
            # 요약 지표
            try:
                data['amount'] = pd.to_numeric(data['amount'])
                total_amount = data['amount'].sum()
                count = len(data)
                
                col1, col2 = st.columns(2)
                col1.metric("총 항목 수", f"{count} 건")
                col2.metric("총 합계 금액", f"{total_amount:,} 원")

                # 데이터 테이블
                st.dataframe(data, use_container_width=True)
                
                # 차트 시각화
                st.bar_chart(data.set_index('item')['amount'])
            except Exception as e:
                st.error(f"데이터 처리 중 오류 발생: {e}")
                st.dataframe(data)
        else:
            st.warning("데이터는 수신했으나 컬럼 구성이 맞지 않습니다.")
            st.write("수신된 컬럼:", list(data.columns))
            st.dataframe(data)
    else:
        st.info(f"💡 {selected_year}년 {selected_month}월에 조회된 데이터가 없습니다.")
        st.caption("API URL이 정확한지, 서버에서 JSON 형식을 반환하는지 확인하세요.")

if __name__ == "__main__":
    main()

