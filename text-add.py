import streamlit as st
import base64
import os

# 1. 페이지 설정 (인터넷 탭 제목)
st.set_page_config(page_title="송장텍스트변환 <LYC>", page_icon="📝", layout="wide")

# --- 배경 이미지 설정 함수 ---
def add_bg_from_local(image_file):
    with open(image_file, "rb") as f:
        encoded_string = base64.b64encode(f.read()).decode()
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url(data:image/png;base64,{encoded_string});
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

# 2. 배경 이미지 적용 (여기를 uni.png로 변경했습니다!)
image_filename = 'uni.png'

try:
    add_bg_from_local(image_filename)
except FileNotFoundError:
    st.warning(f"배경 이미지를 찾을 수 없습니다. ({image_filename}) GitHub에 파일이 올라갔는지 확인해주세요.")

# 3. 화면 큰 제목
st.title("📝 송장텍스트변환 <LYC> lodus11st@naver.com")
st.caption("엑셀 한 줄을 복사해 넣으면, 5단 세로 양식으로 변환합니다.")

# 4. 화면 구성 (왼쪽 입력 -> 오른쪽 출력)
col1, col2 = st.columns(2)

# --- 왼쪽: 입력창 ---
with col1:
    st.subheader("1. 엑셀 내용 붙여넣기 (Ctrl+V)")
    # 배경이 있어서 글자가 잘 안 보일 수 있으니 입력창을 약간 불투명하게
    st.markdown(
        """
        <style>
        .stTextArea textarea {
            background-color: rgba(255, 255, 255, 0.9);
            color: black;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    raw_text = st.text_area("엑셀의 한 행(Row)을 복사해서 붙여넣으세요. (여러 줄 가능)", height=300)

# --- 변환 로직 함수 ---
def format_order(line):
    parts = line.split('\t')
    parts = [p.strip() for p in parts] 
    
    if len(parts) < 5:
        return f"⚠️ 데이터 부족 (칸 개수 확인 필요): {line}"
    
    try:
        # 데이터 매핑
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
    
    result_text = ""
    
    if raw_text:
        lines = raw_text.strip().split('\n')
        for line in lines:
            if line.strip():
                result_text += format_order(line)
                result_text += "\n\n" + "-"*30 + "\n\n"
    
    st.text_area("결과물", value=result_text, height=500)