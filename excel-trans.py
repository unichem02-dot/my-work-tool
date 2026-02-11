import streamlit as st
import pandas as pd
import re
import io

# 1. 페이지 설정
st.set_page_config(page_title="스마트 주문서 변환기", page_icon="⚡", layout="wide")
st.title("⚡ 스마트 주문서 변환기 (배송 '선불' 추가버전)")

# 2. 파싱 함수
def parse_smart_order(text):
    results = []
    
    cleaned_text = text.replace('\n', ' ').strip()
    
    # 데이터 담을 그릇 (순서 중요!)
    data = {
        "우편번호": "",
        "주소": "",
        "수취인": "",
        "전화번호1": "",
        "전화번호2": "",
        "수량": "1",
        "배송": "선불",  # 👈 요청하신 부분: 기본값 '선불'
        "상품명": "",
        "배송메세지": ""
    }
    
    # 1. 전화번호 찾기
    phone_matches = re.findall(r'01[016789]-?\d{3,4}-?\d{4}', cleaned_text)
    
    if not phone_matches:
        data["주소"] = cleaned_text
        results.append(data)
        # 컬럼 순서 강제 정렬해서 반환
        return pd.DataFrame(results)[["우편번호", "주소", "수취인", "전화번호1", "전화번호2", "수량", "배송", "상품명", "배송메세지"]]
        
    main_phone = phone_matches[0]
    data["전화번호1"] = main_phone
    if len(phone_matches) > 1:
        data["전화번호2"] = phone_matches[1]

    # 2. 전화번호 기준 앞/뒤 자르기
    parts = cleaned_text.split(main_phone, 1)
    before_phone = parts[0].strip()
    after_phone = parts[1].strip() if len(parts) > 1 else ""
    
    # 3. [앞부분] 이름/주소 분리
    if before_phone:
        tokens = before_phone.split()
        if tokens:
            candidate_name = tokens[-1]
            is_name = True
            address_keywords = ["시", "도", "군", "구", "읍", "면", "동", "리", "로", "길", "아파트", "빌라", "해뜨는집", "타워"]
            
            if len(candidate_name) > 5 or len(candidate_name) < 2: is_name = False
            elif any(kw in candidate_name for kw in address_keywords): is_name = False
            elif any(char.isdigit() for char in candidate_name): is_name = False
            
            if is_name:
                data["수취인"] = candidate_name
                data["주소"] = " ".join(tokens[:-1])
            else:
                data["주소"] = before_phone
    
    # 4. [자동감지] 상품명 & 수량 찾기
    # "숫자+통/개/박스" 바로 앞 단어를 상품명으로 인식
    product_pattern = re.search(r'(\S+)\s*(\d+)\s*(통|개|박스|can|CAN)', cleaned_text)
    
    if product_pattern:
        candidate_product = product_pattern.group(1)
        qty = product_pattern.group(2)
        
        blacklist_product = ["택배선불", "배송비", "입금", "주문", "선불", "착불"]
        
        if not any(word in candidate_product for word in blacklist_product):
            data["상품명"] = candidate_product
            data["수량"] = qty
        else:
            data["수량"] = qty

    # 5. 배송 '선불' vs '착불' 자동 구분
    if "착불" in cleaned_text:
        data["배송"] = "착불"
        data["배송메세지"] = "착불배송"
    else:
        data["배송"] = "선불" # 기본값 유지

    # 우편번호 추출
    zip_match = re.search(r'\d{3}-\d{3}|\d{5}', data["주소"])
    if zip_match: data["우편번호"] = zip_match.group()

    results.append(data)
    
    # 컬럼 순서를 사장님이 원하시는 대로 딱! 고정해서 반환
    cols = ["우편번호", "주소", "수취인", "전화번호1", "전화번호2", "수량", "배송", "상품명", "배송메세지"]
    return pd.DataFrame(results)[cols]

# 3. 화면 구성
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주문 문자 붙여넣기")
    raw_text = st.text_area("여기에 복사한 텍스트를 넣으세요", height=300,
                            placeholder="예시:\n강원도 홍천군 ... 해뜨는집\n최용남 010-4752-1001\n종균제 5통")
    
    convert_btn = st.button("변환하기 🚀", type="primary")

with col2:
    st.subheader("2. 변환 결과 확인")
    if convert_btn and raw_text:
        df_result = parse_smart_order(raw_text)
        
        st.success("변환 성공! '배송' 칸이 추가되었습니다.")
        st.dataframe(df_result, use_container_width=True)
        
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_result.to_excel(writer, index=False, sheet_name='주문목록')
            worksheet = writer.sheets['주문목록']
            worksheet.set_column('A:I', 15)
            worksheet.set_column('B:B', 40)
            
        output.seek(0)
        st.download_button(label="💾 엑셀 파일 다운로드", data=output, file_name="스마트주문_변환.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    elif not raw_text:
        st.info("왼쪽에 텍스트를 넣고 버튼을 눌러주세요.")