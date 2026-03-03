import streamlit as st

def main():
    # 1. 페이지 설정 및 제목
    st.set_page_config(page_title="Real-time I/O System", page_icon="⚡")
    st.title("⚡ 실시간 데이터 입출력 시스템")
    st.markdown("스트림릿에서는 `input()` 대신 **위젯**을 사용해야 화면에 표시됩니다.")
    st.divider()

    # 2. 안내 메시지
    st.info("텍스트를 입력창에 넣고 엔터를 누르면 실시간으로 분석 결과가 업데이트됩니다.")

    # 3. 사용자 입력 (Streamlit 전용 위젯)
    # 기존 python의 input() 역할을 수행합니다.
    user_input = st.text_input("입력값을 넣어주세요", placeholder="여기에 입력...")

    # 4. 데이터 처리 및 결과 출력
    if user_input:
        # 로직 처리
        upper_text = user_input.upper()
        reversed_text = user_input[::-1]
        length = len(user_input)

        # 결과 레이아웃 구성
        st.subheader("📊 분석 결과")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("대문자 변환", upper_text)
        with col2:
            st.metric("글자 역순", reversed_text)
        with col3:
            st.metric("텍스트 길이", f"{length} 자")
        
        st.success("데이터 처리가 완료되었습니다.")
    else:
        st.warning("현재 입력된 데이터가 없습니다.")

if __name__ == "__main__":
    main()
