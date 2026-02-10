import streamlit as st

# 1. 페이지 설정
st.set_page_config(page_title="송장텍스트변환", page_icon="📦", layout="wide")
st.title("📦 송장텍스트변환")

# 2. 탭 설정
tab1, tab2 = st.tabs(["📦 텍스트변환(전진발주)", "📝 텍스트변환(유니케미칼)"])

# ==============================================================================
# [탭 1] 전진발주 변환기
# ==============================================================================
with tab1:
    col1_a, col2_a = st.columns(2)

    with col1_a:
        st.subheader("1. 엑셀 데이터 붙여넣기")
        # 입력창
        raw_text_jeonjin = st.text_area("여기에 붙여넣으세요 (Ctrl+Enter로 바로 변환)", height=500, key="jeonjin_input")

    # --- 전진발주 로직 (전화번호 수정됨) ---
    def convert_line_jeonjin(line):
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        if len(parts) < 7: return ""

        try:
            zip_code = parts[0]
            address = parts[1]
            name = parts[2]
            
            # [수정] 전화번호 로직: 둘 다 있으면 같이 표시
            phone1 = parts[3].strip()
            phone2 = parts[4].strip() if len(parts) > 4 else ""
            
            if phone2 and (phone1 != phone2):
                phone = f"{phone1} / {phone2}" # 두 개 다 표시
            else:
                phone = phone1 # 하나만 있거나 같으면 하나만 표시

            qty_str = parts[5]
            qty = int(qty_str) if qty_str.isdigit() else 1
            
            raw_product = parts[7]
            note = parts[8] if len(parts) > 8 else ""

            # 상품명 변환
            product_name = raw_product
            if "차아염소산" in raw_product or "차염" in raw_product: product_name = "차염산"
            elif "구연산" in raw_product: product_name = "구연산수50%(20kg)"
            elif "PAC" in raw_product: product_name = "PAC17%"
            elif "가성소다" in raw_product: product_name = "가성소다4.5%(20kg)"
            
            pallet_text = " - 파래트" if qty >= 10 else ""

            formatted_block = (
                f"{product_name} {qty}