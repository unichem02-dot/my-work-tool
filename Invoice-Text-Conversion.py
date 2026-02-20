import streamlit as st
import re # 정규표현식 (숫자만 추출하기 위해)
import datetime # [수정됨] 날짜 추출을 위한 모듈 추가

# 1. 페이지 설정
st.set_page_config(page_title="송장텍스트변환 <LYC>", page_icon="📦", layout="wide")

# 2. 메인 제목
st.title("📝 송장텍스트변환 <LYC> lodus11st@naver.com")

# [추가됨] 탭 글자 크기를 키우기 위한 CSS 스타일 적용
st.markdown("""
<style>
    /* 탭 메뉴 글자 크기 및 굵기 변경 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 26px !important;
        font-weight: 900 !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 탭 설정
tab1, tab2 = st.tabs(["📦 텍스트변환(전진발주)", "📝 텍스트변환(유니케미칼)"])

# ==============================================================================
# [탭 1] 전진발주 변환기
# ==============================================================================
with tab1:
    col1_a, col2_a = st.columns(2)

    with col1_a:
        st.subheader("1. 엑셀 데이터 붙여넣기")
        
        # 지우기 버튼 기능
        def clear_jeonjin():
            st.session_state["jeonjin_input"] = ""
        
        st.button("🔄 입력창 비우기", on_click=clear_jeonjin, key="btn_clear_1")

        # [수정됨] 안내 문구 제거 (label_visibility="collapsed")
        raw_text_jeonjin = st.text_area(
            label="입력창",  # 코드를 위해 이름은 두되
            height=500, 
            key="jeonjin_input",
            label_visibility="collapsed" # 화면에서는 숨김 처리
        )

    def convert_line_jeonjin(line):
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        if len(parts) < 7: return ""

        try:
            zip_code = parts[0]
            address = parts[1]
            name = parts[2]
            
            # 전화번호 로직
            phone1 = parts[3].strip()
            phone2 = parts[4].strip() if len(parts) > 4 else ""
            
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
# [탭 2] 유니케미칼 변환기
# ==============================================================================
with tab2:
    col1_b, col2_b = st.columns(2)

    with col1_b:
        st.subheader("1. 엑셀 내용 붙여넣기")
        
        # 지우기 버튼 기능
        def clear_uni():
            st.session_state["uni_input"] = ""
            
        st.button("🔄 입력창 비우기", on_click=clear_uni, key="btn_clear_2")

        # [수정됨] 안내 문구 제거 (label_visibility="collapsed")
        raw_text_uni = st.text_area(
            label="입력창", 
            height=500, 
            key="uni_input",
            label_visibility="collapsed" # 화면에서는 숨김 처리
        )

    def format_order_uni(line):
        parts = line.split('\t')
        parts = [p.strip() for p in parts]
        if len(parts) < 5: return f"⚠️ 데이터 부족: {line}"
        try:
            zipcode = parts[0]
            addr = parts[1]
            name = parts[2]
            
            # 전화번호 중복 제거 로직
            tel1 = parts[3].strip()
            tel2_raw = parts[4].strip() if len(parts) > 4 else ""
            
            t1_clean = re.sub(r'[^0-9]', '', tel1)
            t2_clean = re.sub(r'[^0-9]', '', tel2_raw)
            
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

            return f"""{zipcode}
{addr}
{name}\t{tel1}\t{tel2}
{qty}\t{pay}\t{product}
{memo_line}"""
        except: return f"❌ 에러: {line}"

    with col2_b:
        st.subheader("2. 변환 결과")
        result_text_uni = ""
        
        # [수정됨] 한국 시간(KST, UTC+9)으로 설정하여 오늘 날짜 가져오기
        kst = datetime.timezone(datetime.timedelta(hours=9))
        today_str = datetime.datetime.now(kst).strftime("%y%m%d")
        
        # [수정됨] 날짜(6자리) 뒤에 하이픈(-) 24개를 붙여 총 30자리의 구분선 만들기
        separator = f"{today_str}" + "-" * 24 

        if raw_text_uni:
            lines = raw_text_uni.strip().split('\n')
            for line in lines:
                if line.strip():
                    result_text_uni += format_order_uni(line)
                    # [수정됨] 기존 "-"*30 대신 새롭게 만든 구분선 적용
                    result_text_uni += f"\n\n{separator}\n\n"
            st.text_area("결과물", value=result_text_uni, height=500)
        else:
            st.info("왼쪽에 데이터를 붙여넣으세요.")
