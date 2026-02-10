import streamlit as st
import re # 정규표현식 (숫자만 추출하기 위해 추가)

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
        raw_text_jeonjin = st.text_area("여기에 붙여넣으세요 (Ctrl+Enter로 바로 변환)", height=500, key="jeonjin_input")

    def convert_line_jeonjin(line):
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        if len(parts) < 7: return ""

        try:
            zip_code = parts[0]
            address = parts[1]
            name = parts[2]
            
            # [전진발주] 전화번호 로직
            phone1 = parts[3].strip()
            phone2 = parts[4].strip() if len(parts) > 4 else ""
            
            # 숫자만 추출해서 비교 (안전장치)
            p1_clean = re.sub(r'[^0-9]', '', phone1)
            p2_clean = re.sub(r'[^0-9]', '', phone2)
            
            if p2_clean and (p1_clean != p2_clean):
                phone = f"{phone1} / {phone2}" 
            else:
                phone = phone1 

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

            formatted_block = f"""{product_name} {qty}통{pallet_text} (송장번호필요)
--------------
택배선불로 보내주세요^^
{zip_code}
{address}
{name} {phone}"""
            
            if note:
                formatted_block += f"\n{note}"
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
# [탭 2] 유니케미칼 변환기 (강력한 중복 제거!)
# ==============================================================================
with tab2:
    col1_b, col2_b = st.columns(2)

    with col1_b:
        st.subheader("1. 엑셀 내용 붙여넣기")
        raw_text_uni = st.text_area("엑셀 데이터를 붙여넣으세요 (Ctrl+Enter로 바로 변환)", height=500, key="uni_input")

    def format_order_uni(line):
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        if len(parts) < 5: return f"⚠️ 데이터 부족: {line}"
        try:
            zipcode = parts[0]
            addr = parts[1]
            name = parts[2]
            
            # [★여기 수정됨] 전화번호 숫자만 비교해서 중복 제거
            tel1 = parts[3].strip()
            tel2_raw = parts[4].strip() if len(parts) > 4 else ""
            
            # 숫자만 남기고 다 지워서 비교 (공백, 하이픈 무시)
            t1_clean = re.sub(r'[^0-9]', '', tel1)
            t2_clean = re.sub(r'[^0-9]', '', tel2_raw)
            
            # 숫자가 똑같으면 두 번째 칸은 비워버림
            if t1_clean == t2_clean:
                tel2 = ""
            else:
                tel2 = tel2_raw

            qty = parts[5] if len(parts) > 5 else ""
            pay = parts[6] if len(parts) > 6 else ""
            product = parts[7] if len(parts) > 7 else ""
            memo = parts[8] if len(parts) > 8 else "" 
            
            # 메모가 있으면 출력, 없으면 빈칸
            memo_line = f"{memo}" if memo else ""

            # 결과 조립 (줄바꿈 이슈 해결된 삼중 따옴표 사용)
            return f"""{zipcode}
{addr}
{name}\t{tel1}\t{tel2}
{qty}\t{pay}\t{product}
{memo_line}"""
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