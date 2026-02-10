import streamlit as st

# 1. 페이지 설정 (인터넷 탭 제목 변경)
st.set_page_config(page_title="텍스트변환(유니케미칼)", page_icon="📝", layout="wide")

# 2. 화면 큰 제목 변경
st.title("📝 텍스트변환(유니케미칼)")
st.caption("엑셀 한 줄을 복사해 넣으면, 5단 세로 양식으로 변환합니다.")

# 3. 화면 구성 (왼쪽 입력 -> 오른쪽 출력)
col1, col2 = st.columns(2)

# --- 왼쪽: 입력창 ---
with col1:
    st.subheader("1. 엑셀 내용 붙여넣기 (Ctrl+V)")
    raw_text = st.text_area("엑셀의 한 행(Row)을 복사해서 붙여넣으세요. (여러 줄 가능)", height=300)

# --- 변환 로직 (기존 5단 정리 기능 유지) ---
def format_order(line):
    # 탭(Tab)으로 칸을 나눕니다.
    parts = line.split('\t')
    parts = [p.strip() for p in parts] # 앞뒤 공백 제거
    
    # 데이터 개수가 너무 적으면 (오류 방지)
    if len(parts) < 5:
        return f"⚠️ 데이터 부족 (칸 개수 확인 필요): {line}"
    
    try:
        # 엑셀 순서대로 데이터 가져오기
        # 0:우편번호, 1:주소, 2:이름, 3:전번1, 4:전번2, 5:수량, 6:선불, 7:상품명, 8:메모(문앞)
        
        zipcode = parts[0]
        addr = parts[1]
        name = parts[2]
        tel1 = parts[3]
        tel2 = parts[4]
        
        # 데이터가 없을 경우를 대비해 안전하게 가져오기
        qty = parts[5] if len(parts) > 5 else ""
        pay = parts[6] if len(parts) > 6 else ""
        product = parts[7] if len(parts) > 7 else ""
        memo = parts[8] if len(parts) > 8 else "" 

        # ★ 5단 포맷 만들기 ★
        formatted = (
            f"{zipcode}\n"                                      # 1줄
            f"{addr}\n"                                         # 2줄
            f"{name}\t{tel1}\t{tel2}\n"                         # 3줄
            f"{qty}\t{pay}\t{product}\n"                        # 4줄
            f"{memo}"                                           # 5줄
        )
        return formatted

    except Exception as e:
        return f"❌ 처리 중 에러 발생: {line}"

# --- 오른쪽: 결과창 ---
with col2:
    st.subheader("2. 변환 결과 (복사용)")
    
    if raw_text:
        result_text