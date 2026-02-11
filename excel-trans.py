import streamlit as st
import pandas as pd
import re
import io

# 1. 페이지 설정
st.set_page_config(page_title="스마트 주문서 변환기", page_icon="⚡", layout="wide")
st.title("⚡ 스마트 주문서 변환기 (텍스트 → 엑셀)")

# 2. 파싱 함수 (주소/우편번호 인식 개선)
def parse_smart_order(text):
    results = []
    
    # 빈 줄 제거하고 리스트로 만들기
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    data = {
        "우편번호": "",
        "주소": "",
        "수취인": "",
        "전화번호1": "",
        "전화번호2": "",
        "수량": "1", # 기본값
        "상품명": "",
        "배송메세지": ""
    }
    
    # 전체 텍스트를 한 줄로 합쳐서 분석 (전화번호, 상품명 등 찾기 용도)
    full_text = " ".join(lines)

    # 1. 전화번호 찾기 (010-0000-0000)
    phone_matches = re.findall(r'01[016789]-?\d{3,4}-?\d{4}', full_text)
    if phone_matches:
        data["전화번호1"] = phone_matches[0]
        if len(phone_matches) > 1:
            data["전화번호2"] = phone_matches[1]

    # 2. 상품명 찾기 (사장님 취급 품목)
    known_products = ["울크론", "PAC", "차염", "가성소다", "구연산", "염산", "황산"]
    for prod in known_products:
        if prod in full_text:
            data["상품명"] = prod
            break
            
    # 3. 수량 찾기 (숫자 + '통', '개', '박스')
    qty_match = re.search(r'(\d+)\s*(통|개|박스|can|CAN)', full_text)
    if qty_match:
        data["수량"] = qty_match.group(1)

    # 4. 주소 및 우편번호 찾기 (여기가 핵심!)
    address_candidate = ""
    zip_code_candidate = ""
    name_candidate = ""

    # 주소로 의심되는 단어들
    address_keywords = ["시 ", "도 ", "군 ", "구 ", "읍 ", "면 ", "동 ", "로", "길", "아파트", "빌라", "번지", "충주", "제천"]
    # 제외할 단어들 (은행, 입금 등)
    blacklist = ["농협", "기업", "입금", "예금", "배송비", "감사합니다", "국민", "신한", "우리", "하나"]

    for line in lines:
        # 블랙리스트 단어가 있으면 주소가 아님
        if any(x in line for x in blacklist):
            continue
        
        # '원' 글자가 있어도, 숫자가 바로 앞에 붙어있는 경우(가격)만 제외
        # 예: "10000원"(제외), "원앙길"(포함)
        if re.search(r'\d+\s*원', line) and not any(k in line for k in ["길", "로", "동"]):
            continue

        # 점수 매기기
        score = 0
        for kw in address_keywords:
            if kw in line:
                score += 1
        
        # 우편번호 찾기 (123-456 또는 12345 형태)
        zip_match = re.search(r'\d{3}-\d{3}|\d{5}', line)
        if zip_match:
            score += 2 # 우편번호가 있으면 주소일 확률 매우 높음!
            
        # 주소 결정 로직 (길이가 좀 길고, 주소 키워드나 우편번호가 있는 경우)
        if len(line) > 8 and score >= 1:
            address_candidate = line
            if zip_match:
                zip_code_candidate = zip_match.group()
            
            # 주소가 확정되면 반복문 종료 (첫 번째 주소 라인을 사용)
            break
    
    # 5. 이름 찾기 (전화번호가 있는 줄에서 이름만 남기기)
    for line in lines:
        if data["전화번호1"] in line:
            # 전화번호 지우고 남은 글자를 이름으로 추정
            temp = line.replace(data["전화번호1"], "").replace(data["전화번호2"], "").strip()
            # 특수문자나 잡다한 글자 제거
            temp = re.sub(r'[^\w\s가-힣]', '', temp).strip()
            if 2 <= len(temp) <= 5: # 이름은 보통 2~5글자
                name_candidate = temp
                break

    data["주소"] = address_candidate
    data["우편번호"] = zip_code_candidate
    if name_candidate:
        data["수취인"] = name_candidate
    elif not data["수취인"]:
        # 전화번호 줄에서 이름을 못 찾았으면, '곽태규' 처럼 혼자 있는 줄을 찾을 수도 있음 (추후 개선 가능)
        pass

    results.append(data)
    return pd.DataFrame(results)

# 3. 화면 구성
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
        
        # 엑셀 다운로드
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_result.to_excel(writer, index=False, sheet_name='주문목록')
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