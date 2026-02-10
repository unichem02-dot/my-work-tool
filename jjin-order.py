import streamlit as st

# 1. 화면 설정
st.set_page_config(page_title="주문서 포맷 변환기", page_icon="📦", layout="wide")
st.title("📦 주문서 포맷 변환기")
st.caption("엑셀 내용을 붙여넣으면 '택배선불' 양식으로 바꿔줍니다.")

# 2. 화면 구성 (왼쪽 입력 -> 오른쪽 출력)
col1, col2 = st.columns(2)

with col1:
    st.subheader("1. 엑셀 데이터 붙여넣기")
    raw_text = st.text_area("여기에 붙여넣으세요", height=500)

# --- 변환 로직 (사장님 코드 이식) ---
def convert_line(line):
    parts = line.split('\t')
    parts = [p.strip() for p in parts]
    
    # 데이터 부족하면 패스
    if len(parts) < 7:
        return ""

    try:
        # 데이터 파싱
        zip_code = parts[0]
        address = parts[1]
        name = parts[2]
        
        # 전화번호 (두번째꺼 우선)
        phone1 = parts[3]
        phone2 = parts[4] if len(parts) > 4 else ""
        phone = phone2 if phone2 else phone1
        
        # 수량
        qty_str = parts[5]
        qty = int(qty_str) if qty_str.isdigit() else 1
        
        # 상품명 및 비고
        raw_product = parts[7]
        note = parts[8] if len(parts) > 8 else ""

        # --- 상품명 변환 로직 ---
        product_name = raw_product
        if "차아염소산" in raw_product or "차염" in raw_product:
            product_name = "차염산"
        elif "구연산" in raw_product:
            product_name = "구연산수50%(20kg)"
        elif "PAC" in raw_product:
            product_name = "PAC17%"
        elif "가성소다" in raw_product:
            product_name = "가성소다4.5%(20kg)"
        
        # --- 파래트 여부 로직 ---
        pallet_text = ""
        if qty >= 10:
            pallet_text = " - 파래트"

        # --- 최종 포맷 생성 ---
        formatted_block = (
            f"{product_name} {qty}통{pallet_text} (송장번호필요)\n"
            f"--------------\n"
            f"택배선불로 보내주세요^^\n"
            f"{zip_code}\n"
            f"{address}\n"
            f"{name} {phone}"
        )
        
        if note:
            formatted_block += f"\n{note}"
            
        return formatted_block

    except Exception as e:
        return f"❌ 오류 발생: {line} ({e})"

# --- 오른쪽 출력 ---
with col2:
    st.subheader("2. 변환 결과")
    
    if raw_text:
        lines = raw_text.strip().split('\n')
        result_text = ""
        
        for line in lines:
            if line.strip():
                converted = convert_line(line)
                if converted:
                    result_text += converted + "\n\n"
        
        st.text_area("결과물 (복사해서 쓰세요)", value=result_text, height=500)
    else:
        st.info("왼쪽에 데이터를 넣으면 자동으로 변환됩니다.")