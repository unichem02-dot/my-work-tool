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
        # 입력창 (버튼 없음, 그냥 붙여넣으면 됨)
        raw_text_jeonjin = st.text_area("여기에 붙여넣으세요 (Ctrl+Enter로 바로 변환)", height=500, key="jeonjin_input")

    # --- 전진발주 로직 ---
    def convert_line_jeonjin(line):
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        if len(parts) < 7: return ""
        try:
            zip_code = parts[0]
            address = parts[1]
            name = parts[2]
            phone1 = parts[3]
            phone2 = parts[4] if len(parts) > 4 else ""
            phone = phone2 if phone2 else phone1
            qty_str = parts[5]
            qty = int(qty_str) if qty_str.isdigit() else 1
            raw_product = parts[7]
            note = parts[8] if len(parts) > 8 else ""

            product_name = raw_product
            if "차아염소산" in raw_product or "차염" in raw_product: product_name = "차염산"
            elif "구연산" in raw_product: product_name = "구연산수50%(20kg)"
            elif "PAC" in raw_product: product_name = "PAC17%"
            elif "가성소다" in raw_product: product_name = "가성소다4.5%(20kg)"
            
            pallet_text = " - 파래트" if qty >= 10 else ""

            formatted_block = (
                f"{product_name} {qty}통{pallet_text} (송장번호필요)\n"
                f"--------------\n"
                f"택배선불로 보내주세요^^\n"
                f"{zip_code}\n"
                f"{address}\n"
                f"{name} {phone}"
            )
            if note: formatted_block += f"\n{note}"
            return formatted_block
        except: return ""

    with col2_a:
        st.subheader("2. 변환 결과")
        result_text_jeonjin = ""
        if raw_text_jeonjin:
            lines = raw_text_jeonjin.strip().split('\n')
            for line in lines:
                if line.strip():
                    converted = convert_line_jeonjin(line)
                    if converted: result_text_jeonjin += converted + "\n\n"
            st.text_area("결과물 (복사해서 쓰세요)", value=result_text_jeonjin, height=500)
        else:
            st.info("왼쪽에 데이터를 붙여넣으세요.")

# ==============================================================================
# [탭 2] 유니케미칼 변환기
# ==============================================================================
with tab2:
    col1_b, col2_b = st.columns(2)

    with col1_b:
        st.subheader("1. 엑셀 내용 붙여넣기")
        # 입력창 (버튼 없음)
        raw_text_uni = st.text_area("엑셀 데이터를 붙여넣으세요 (Ctrl+Enter로 바로 변환)", height=500, key="uni_input")

    # --- 유니케미칼 로직 ---
    def format_order_uni(line):
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        if len(parts) < 5: return f"⚠️ 데이터 부족: {line}"
        try:
            zipcode = parts[0]
            addr = parts[1]
            name = parts[2]
            tel1 = parts[3]
            tel2 = parts[4]
            qty = parts[5] if len(parts) > 5 else ""
            pay = parts[6] if len(parts) > 6 else ""
            product = parts[7] if len(parts) > 7 else ""
            memo = parts[8] if len(parts) > 8 else "" 
            return f"{zipcode}\n{addr}\n{name}\t{tel1}\t{tel2}\n{qty}\t{pay}\t{product}\n{memo}"
        except: return f"❌ 에러: {line}"

    with col2_b:
        st.subheader("2. 변환 결과")
        result_text_uni = ""
        if raw_text_uni:
            lines = raw_text_uni.strip().split('\n')
            for line in lines:
                if line.strip():
                    result_text_uni += format_order_uni(line)
                    result_text_uni += "\n\n" + "-"*30 + "\n\n"
            st.text_area("결과물", value=result_text_uni, height=500)
        else:
            st.info("왼쪽에 데이터를 붙여넣으세요.")