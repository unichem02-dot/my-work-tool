import streamlit as st
import re # 정규표현식 (숫자만 추출하기 위해)
import datetime # 날짜 추출을 위한 모듈 추가

# [수정됨] 공통으로 사용할 한국 시간(KST) 오늘 날짜와 요일 가져오기
kst = datetime.timezone(datetime.timedelta(hours=9))
current_dt = datetime.datetime.now(kst)
today_str = current_dt.strftime("%y%m%d") # 기존 유니케미칼 하단 구분선 유지용

# [수정됨] 요일이 포함된 완벽한 정식 영어 날짜 형식 (예: Friday, February 20, 2026)
full_english_date = f"{current_dt.strftime('%A')}, {current_dt.strftime('%B')} {current_dt.day}, {current_dt.year}"

# 1. 페이지 설정
st.set_page_config(page_title="송장텍스트변환 <LYC>", page_icon="📦", layout="wide")

# [수정됨] 웹 브라우저가 < > 기호를 코드로 인식하지 않도록 화면 표시용 텍스트 변환
copy_text = f"<<<<<<{full_english_date}, 경동마감>>>>>>"
display_text = copy_text.replace("<", "&lt;").replace(">", "&gt;")

# [수정됨] 다크 테마에 맞춘 복사 버튼 UI (흰색 텍스트 및 캡슐형 테두리 버튼)
html_code = f"""
<div style="display: flex; align-items: center; gap: 10px; font-family: 'Malgun Gothic', sans-serif;">
    <span style="font-size: 1.2rem; font-weight: 900; color: #FFFFFF;">{display_text}</span>
    <button onclick="copyToClipboard()" style="background-color: transparent; color: white; border: 1px solid white; padding: 6px 18px; border-radius: 30px; cursor: pointer; font-weight: bold; transition: 0.2s;">
        📋 복사하기
    </button>
</div>
<script>
function copyToClipboard() {{
    var el = document.createElement('textarea');
    el.value = '{copy_text}';
    document.body.appendChild(el);
    el.select();
    document.execCommand('copy');
    document.body.removeChild(el);
    
    var btn = document.querySelector('button');
    btn.innerHTML = '✅ 복사완료!';
    btn.style.backgroundColor = '#03C75A';
    btn.style.borderColor = '#03C75A';
    setTimeout(function() {{
        btn.innerHTML = '📋 복사하기';
        btn.style.backgroundColor = 'transparent';
        btn.style.borderColor = 'white';
    }}, 2000);
}}
</script>
"""
st.components.v1.html(html_code, height=50)

# [수정됨] 2. 메인 제목 (이모티콘 제거)
st.title("송장텍스트변환 <LYC> lodus11st@naver.com")

# [수정됨] 업로드하신 이미지의 다크 틸(Dark Teal) & 캡슐 테두리 스타일 적용 및 UI 숨김 추가
st.markdown("""
<style>
    /* 전체 배경을 다크 청록색으로 변경 */
    .stApp {
        background-color: #1a3636 !important;
    }
    
    /* 전체 폰트 색상을 흰색으로 적용 */
    .stApp h1, .stApp h2, .stApp h3, .stApp p, .stApp label, .stApp div[data-testid="stText"] {
        color: #FFFFFF !important;
    }

    /* 제목의 이메일 주소 링크 밑줄 제거 및 흰색 유지 */
    h1 a {
        text-decoration: none !important;
        color: #FFFFFF !important;
    }
    
    /* 1. 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 26px !important;
        font-weight: 900 !important;
        color: #8da9a7 !important; /* 선택 안된 탭은 약간 어두운 회청색 */
    }
    
    /* 선택된 탭 밑줄(흰색) */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #FFFFFF !important;
    }
    
    /* 선택된 탭 글자색(흰색) */
    .stTabs [aria-selected="true"] p {
        color: #FFFFFF !important; 
    }
    
    /* 2. 버튼 스타일 (투명 배경, 흰색 테두리, 캡슐 모양) */
    button[kind="secondary"] {
        background-color: transparent !important;
        border: 1px solid #FFFFFF !important;
        color: #FFFFFF !important;
        border-radius: 30px !important; /* 둥근 캡슐형 */
        font-weight: bold !important;
        padding: 0.5rem 1.5rem !important;
        transition: all 0.3s ease;
    }
    button[kind="secondary"]:hover {
        background-color: rgba(255, 255, 255, 0.1) !important; /* 호버 시 약간 밝아짐 */
        transform: translateY(-2px); 
    }
    
    /* 3. 텍스트 입력창 (다크 모드형 어두운 배경) */
    div[data-baseweb="textarea"] > div {
        background-color: #122626 !important; /* 배경보다 살짝 더 어두운 색 */
        border: 1px solid #3c5e5d !important;
        border-radius: 8px !important;
    }
    div[data-baseweb="textarea"] > div:focus-within {
        border: 1px solid #FFFFFF !important; /* 클릭 시 흰색 테두리 */
    }
    /* 텍스트 입력 시 글자색 */
    textarea {
        color: #FFFFFF !important;
    }
    
    /* 4. st.info 알림창 다크 모드 최적화 */
    .stAlert {
        background-color: #214544 !important;
        border: none !important;
        color: #FFFFFF !important;
    }
    .stAlert p {
        color: #FFFFFF !important;
    }

    /* 5. ★추가됨★ Streamlit 기본 UI 숨기기 */
    #MainMenu {visibility: hidden !important;} /* 우측 상단 햄버거 메뉴 숨김 */
    header {visibility: hidden !important;} /* 상단 헤더 영역 숨김 */
    footer {visibility: hidden !important;} /* 하단 Made with Streamlit 워터마크 숨김 */
    .stDeployButton {display: none !important;} /* Deploy 버튼 숨김 */
    [data-testid="stToolbar"] {visibility: hidden !important;} /* 툴바 숨김 */
    
    /* 우측 하단 < Manage app 버튼 완벽 숨김 */
    .viewerBadge_container__1QSob,
    .styles_viewerBadge__1yB5_,
    .viewerBadge_link__1S137,
    [data-testid="manage-app-button"] {
        display: none !important;
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
        # [수정됨] 제목과 버튼을 나란히 배치하기 위해 컬럼 분할
        header_col1, header_col2 = st.columns([0.7, 0.3])
        with header_col1:
            st.subheader("1. 엑셀 데이터 붙여넣기")
        
        # 지우기 버튼 기능
        def clear_jeonjin():
            st.session_state["jeonjin_input"] = ""
            
        with header_col2:
            # 스타일 맞춤을 위해 약간의 여백 추가
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            st.button("🔄 입력창 비우기", on_click=clear_jeonjin, key="btn_clear_1")

        # 안내 문구 제거 (label_visibility="collapsed")
        raw_text_jeonjin = st.text_area(
            label="입력창",  
            height=500, 
            key="jeonjin_input",
            label_visibility="collapsed" 
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
            
            # [수정됨] 결과물 텍스트 라벨 숨김 처리 (label_visibility="collapsed")
            st.text_area(label="결과물", value=result_text_jeonjin, height=500, label_visibility="collapsed")
        else:
            st.info("왼쪽에 데이터를 붙여넣으세요.")

# ==============================================================================
# [탭 2] 유니케미칼 변환기
# ==============================================================================
with tab2:
    col1_b, col2_b = st.columns(2)

    with col1_b:
        # [수정됨] 제목과 버튼을 나란히 배치하기 위해 컬럼 분할
        header_col3, header_col4 = st.columns([0.7, 0.3])
        with header_col3:
            st.subheader("1. 엑셀 내용 붙여넣기")
        
        # 지우기 버튼 기능
        def clear_uni():
            st.session_state["uni_input"] = ""
            
        with header_col4:
            # 스타일 맞춤을 위해 약간의 여백 추가
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            st.button("🔄 입력창 비우기", on_click=clear_uni, key="btn_clear_2")

        # 안내 문구 제거 (label_visibility="collapsed")
        raw_text_uni = st.text_area(
            label="입력창", 
            height=500, 
            key="uni_input",
            label_visibility="collapsed" 
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
        
        # 날짜(6자리) 뒤에 하이픈(-) 24개를 붙여 총 30자리의 구분선 만들기
        separator = f"{today_str}" + "-" * 24 

        if raw_text_uni:
            lines = raw_text_uni.strip().split('\n')
            for line in lines:
                if line.strip():
                    result_text_uni += format_order_uni(line)
                    # 기존 "-"*30 대신 새롭게 만든 구분선 적용
                    result_text_uni += f"\n\n{separator}\n\n"
            
            # [수정됨] 결과물 텍스트 라벨 숨김 처리 (label_visibility="collapsed")
            st.text_area(label="결과물", value=result_text_uni, height=500, label_visibility="collapsed")
        else:
            st.info("왼쪽에 데이터를 붙여넣으세요.")
