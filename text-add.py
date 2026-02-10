import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="주문서 5단 정리기", page_icon="📝", layout="wide")
st.title("📝 주문서 5단 정리기")
st.caption("엑셀 한 줄을 복사해 넣으면, 5단 세로 양식으로 변환합니다.")

# 2. 화면 구성 (왼쪽 입력 -> 오른쪽 출력)
col1, col2 = st.columns(2)

# --- 왼쪽: 입력창 ---
with col1:
    st.subheader("1. 엑셀 내용 붙여넣기 (Ctrl+V)")
    raw_text = st.text_area("엑셀의 한 행(Row)을 복사해서 붙여넣으세요. (여러 줄 가능)", height=300)

# --- 변환 로직 ---
def format_order(line):
    # 탭(Tab)으로 칸을 나눕니다.
    parts = line.split('\t')
    parts = [p.strip() for p in parts] # 앞뒤 공백 제거
    
    # 데이터 개수가 너무 적으면 (오류 방지)
    if len(parts) < 5:
        return f"⚠️ 데이터 부족 (칸 개수 확인 필요): {line}"
    
    try:
        # 엑셀 순서대로 데이터 가져오기 (사장님 예시 기준)
        # 0:우편번호, 1:주소, 2:이름, 3:전번1, 4:전번2, 5:수량, 6:선불, 7:상품명, 8:메모(문앞)
        
        zipcode = parts[0]  # 52409
        addr = parts[1]     # 주소 전체
        name = parts[2]     # 이름
        tel1 = parts[3]     # 전화번호1
        tel2 = parts[4]     # 전화번호2 (기타)
        
        # 데이터가 없을 경우를 대비해 안전하게 가져오기
        qty = parts[5] if len(parts) > 5 else ""
        pay = parts[6] if len(parts) > 6 else ""
        product = parts[7] if len(parts) > 7 else ""
        memo = parts[8] if len(parts) > 8 else "" 

        # ★ 사장님이 원하시는 5단 포맷 만들기 ★
        formatted = (
            f"{zipcode}\n"                                      # 1줄: 우편번호
            f"{addr}\n"                                         # 2줄: 주소
            f"{name}\t{tel1}\t{tel2}\n"                         # 3줄: 이름 전번 전번
            f"{qty}\t{pay}\t{product}\n"                        # 4줄: 수량 선불 상품명
            f"{memo}"                                           # 5줄: 메모 (문앞)
        )
        return formatted

    except Exception as e:
        return f"❌ 처리 중 에러 발생: {line}"

# --- 오른쪽: 결과창 ---
with col2:
    st.subheader("2. 변환 결과 (복사용)")
    
    if raw_text:
        result_text = ""
        lines = raw_text.strip().split('\n')
        
        for line in lines:
            if line.strip(): # 빈 줄이 아니면 처리
                result_text += format_order(line)
                result_text += "\n\n" + "-"*30 + "\n\n" # 구분선 추가
        
        st.text_area("결과물", value=result_text, height=500)
    else:
        st.info("왼쪽에 텍스트를 넣으면 자동으로 변환됩니다.")