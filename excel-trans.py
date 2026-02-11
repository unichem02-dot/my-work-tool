import streamlit as st
import pandas as pd
import re
import io

# 1. 페이지 설정
st.set_page_config(page_title="스마트 주문서 변환기", page_icon="⚡", layout="wide")
st.title("⚡ 스마트 주문서 변환기 (텍스트 → 엑셀)")

# 2. 비밀번호 설정 (필요하면 주석 해제)
# if st.text_input("비밀번호", type="password") != "1234": st.stop()

# 3. 파싱 함수 (핵심 로직)
def parse_smart_order(text):
    results = []
    
    # 텍스트를 줄 단위로 나누기 (빈 줄 제거)
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    # 한 덩어리의 주문으로 처리 (여기서는 1개의 주문만 있다고 가정하거나, 
    # 여러 주문이 섞여 있다면 '구분자'로 나누는 로직이 추가로 필요함. 
    # 현재는 통째로 1개의 주문으로 해석)
    
    data = {
        "우편번호": "",
        "주소": "",
        "수취인": "",
        "전화번호1": "",
        "전화번호2": "",
        "수량": "",
        "상품명": "",
        "배송메세지": ""
    }
    
    # --- 분석 시작 ---
    full_text = " ".join(lines) # 전체를 한 줄로 합쳐서 분석도 병행

    # 1. 전화번호 찾기 (010-0000-0000)
    phone_matches = re.findall(r'01[016789]-?\d{3,4}-?\d{4}', full_text)
    if phone_matches:
        data["전화번호1"] = phone_matches[0]
        if len(phone_matches) > 1:
            data["전화번호2"] = phone_matches[1]

    # 2. 상품명 찾기 (사장님 취급 품목 리스트)
    known_products = ["울크론", "PAC", "차염", "가성소다", "구연산", "염산", "황산"]
    found_product = ""
    for prod in known_products:
        if prod in full_text:
            found_product = prod
            break # 하나 찾으면 중단 (여러 개면 수정 필요)
    
    if found_product:
        data["상품명"] = found_product
    else:
        # 못 찾았으면 첫 번째 줄을 상품명으로 추정해볼 수도 있음
        pass

    # 3. 수량 찾기 (숫자 + '통', '개', '박스')
    qty_match = re.search(r'(\d+)\s*(통|개|박스|can|CAN)', full_text)
    if qty_match:
        data["수량"] = qty_match.group(1) # 숫자만 추출
    else:
        data["수량"] = "1" # 기본값 1

    # 4. 주소 및 이름 찾기 (가장 어려움 - 휴리스틱 사용)
    # 전략: '시', '도', '로', '길'이 들어간 긴 문장을 주소로 본다.
    # 전략: 전화번호 앞뒤에 있는 짧은 단어(2~4글자)를 이름으로 본다.

    address_candidate = ""
    name_candidate = ""

    for line in lines:
        # 전화번호, 가격, 계좌번호 등이 포함된 줄은 주소가 아닐 확률 높음
        if any(x in line for x in ["010-", "농협", "기업", "입금", "원", "배송비"]):
            # 이름 찾기: 전화번호가 있는 줄에서 전화번호를 뺀 나머지
            if "010-" in line:
                temp = re.sub(r'01[016789]-?\d{3,4}-?\d{4}', '', line).strip()
                if 2 <= len(temp) <= 5: # 남은 글자가 2~4자면 이름일 확률 높음
                    name_candidate = temp
            continue
        
        # 주소 찾기 ('시', '도', '로', '길' 포함하고 숫자가 섞인 긴 문장)
        if any(x in line for x in ["시 ", "도 ", "로", "길"]) and len(line) > 10:
            address_candidate = line

    data["주소"] = address_candidate
    
    # 이름이 위에서 안 구해졌으면, 주소 다음 줄이나 전화번호 윗줄을 의심
    if not name_candidate:
        # 간단하게: '전화번호' 데이터 바로 앞 단어를 찾거나 함 (복잡해서 생략)
        # 여기서는 예시 데이터의 "곽태규"가 전화번호 옆에 있어서 위 로직으로 잡힘
        pass
    else:
        data["수취인"] = name_candidate

    # 5. 우편번호 (주소에서 추출하거나, 없으면 빈칸)
    # 예시 데이터 "113-701"은 우편번호 형식이지만 구 우편번호임.
    # 신주소(5자리)만 찾으려면: re.search(r'\d{5}', address_candidate)
    
    results.append(data)
    return pd.DataFrame(results)

# 4. 화면 구성
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1. 주문 문자 붙여넣기")
    raw_text = st.text_area("여기에 복사한 텍스트를 넣으세요", height=300,
                            placeholder="예시:\n유니케미칼입니다\n울크론 1통\n...\n충주시 중앙탑면...")
    
    convert_btn = st.button("변환하기 🚀", type="primary")

with col2:
    st.subheader("2. 변환 결과 확인")
    if convert_btn and raw_text:
        df_result = parse_smart_order(raw_text)
        
        # 화면에 표 보여주기
        st.dataframe(df_result, use_container_width=True)
        
        # 엑셀 다운로드 버튼
        # 엑셀 파일 메모리에 생성
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_result.to_excel(writer, index=False, sheet_name='주문목록')
            
            # 엑셀 꾸미기 (열 너비 자동 조절 등)
            worksheet = writer.sheets['주문목록']
            worksheet.set_column('B:B', 40) # 주소 컬럼 넓게
            worksheet.set_column('G:G', 15) # 상품명 넓게
            
        output.seek(0)
        
        st.download_button(
            label="💾 엑셀 파일 다운로드",
            data=output,
            file_name="스마트주문_변환.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    elif not raw_text:
        st.info("왼쪽에 텍스트를 넣고 버튼을 눌러주세요.")