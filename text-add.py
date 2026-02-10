import streamlit as st

# 1. 페이지 설정 (인터넷 탭 제목)
st.set_page_config(page_title="텍스트변환(유니케미칼)", page_icon="📝", layout="wide")

# 2. 화면 큰 제목
st.title("📝 텍스트변환(유니케미칼)")
st.caption("엑셀 한 줄을 복사해 넣으면, 5단 세로 양식으로 변환합니다.")

# 3. 화면 구성 (왼쪽 입력 -> 오른쪽 출력)
col1, col2 = st.columns(2)

# --- 왼쪽: 입력창 ---
with col1:
    st.subheader("1. 엑셀 내용 붙여넣기 (Ctrl+V)")
    raw_text = st.text_area("엑셀의 한 행(Row)을 복사해서 붙여넣으세요. (여러 줄 가능)", height=300)

# --- 변환 로직 함수 ---
def format_order(line):
    parts = line.split('\t')
    parts = [p.strip() for p in parts] 
    
    if len(parts) < 5:
        return f"⚠️ 데이터 부족 (칸 개수 확인 필요): {line}"
    
    try:
        # 데이터 가져오기
        zipcode = parts[0]
        addr = parts[1]
        name = parts[2]
        tel1 = parts[3]
        tel2 = parts[4]
        
        qty = parts[5] if len(parts) > 5 else ""
        pay = parts[6] if len(parts) > 6 else ""
        product = parts[7] if len(parts) > 7 else ""
        memo = parts[8] if len(parts) > 8 else "" 

        # 5단 포맷 조립
        formatted = (
            f"{zipcode}\n"
            f"{addr}\n"
            f"{name}\t{tel1}\t{tel2}\n"
            f"{qty}\t{pay}\t{product}\n"
            f"{memo}"
        )
        return formatted

    except Exception as e:
        return f"❌ 처리 중 에러 발생: {line}"

# --- 오른쪽: 결과창 ---
with col2:
    st.subheader("2. 변환 결과 (복사용)")
    
    # [★핵심 수정] 에러 방지를 위해 '빈 결과물'을 먼저 만들어둡니다.
    result_text = ""
    
    if raw_text:
        lines = raw_text.strip().split('\n')
        for line in lines:
            if line.strip():
                result_text += format_order(line)
                result_text += "\n\n" + "-"*30 + "\n\n"
    
    # 이제 언제나 result_text가 존재하므로 에러가 나지 않습니다.
    st.text_area("결과물", value=result_text, height=500)