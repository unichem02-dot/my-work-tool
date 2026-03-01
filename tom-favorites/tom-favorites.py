import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 페이지 설정
st.set_page_config(page_title="Tom's Favorites", page_icon="🔖", layout="wide")

# 1. 구글 시트 연결 설정 (st.secrets 사용)
# Streamlit Cloud 배포 시 설정의 Secrets에 GCP 서비스 계정 JSON 정보를 넣어야 합니다.
@st.cache_resource
def init_connection():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        # st.secrets에서 인증 정보 가져오기
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )
        client = gspread.authorize(credentials)
        return client
    except Exception as e:
        st.error(f"구글 API 연결 실패. Secrets 설정을 확인해주세요. ({e})")
        return None

client = init_connection()

# 2. 데이터 불러오기
@st.cache_data(ttl=10) # 10초마다 데이터 갱신
def load_data():
    if client:
        try:
            # 'tom-favorites' 구글 시트의 첫 번째 워크시트 열기
            sheet = client.open("tom-favorites").sheet1
            data = sheet.get_all_records()
            return pd.DataFrame(data)
        except gspread.exceptions.SpreadsheetNotFound:
            st.error("'tom-favorites' 시트를 찾을 수 없습니다. 서비스 계정 이메일로 시트를 공유했는지 확인하세요.")
            return pd.DataFrame()
    return pd.DataFrame()

df = load_data()

# --- 화면 UI 구성 ---
st.title("🔖 Tom's Favorites Links")

# 사이드바: 네비게이션 및 추가 폼
with st.sidebar:
    # 네비게이션 (분류1 선택)
    st.header("📂 메뉴")
    selected_cat1 = None
    if not df.empty and '분류1' in df.columns:
        categories1 = sorted([c for c in df['분류1'].unique() if pd.notna(c) and str(c).strip()])
        if categories1:
            selected_cat1 = st.radio("대분류 이동", categories1)
    
    st.divider()
    
    # 새 링크 추가 폼 (접기/펴기 기능으로 UI 깔끔하게 유지)
    with st.expander("➕ 새 링크 추가"):
        with st.form("add_link_form", clear_on_submit=True):
            cat1 = st.text_input("분류1 (필수)*", placeholder="예: 업무툴")
            cat2 = st.text_input("분류2 (선택)", placeholder="예: 기획, 레퍼런스")
            title = st.text_input("제목 (필수)*", placeholder="예: 구글 애널리틱스")
            url = st.text_input("링크 (필수)*", placeholder="https://...")
            memo = st.text_area("메모 (선택)", placeholder="링크에 대한 간단한 설명")
            parent_memo = st.text_area("모분류메모 (선택)", placeholder="이 대분류(분류1)에 대한 공통 설명")
            
            submitted = st.form_submit_button("저장하기")
            
            if submitted:
                if not title or not url or not cat1:
                    st.warning("분류1, 제목, 링크는 필수 입력 사항입니다.")
                else:
                    try:
                        sheet = client.open("tom-favorites").sheet1
                        # 구글 시트 열 순서: 분류1, 분류2, 제목, 링크, 메모, 모분류메모
                        sheet.append_row([cat1, cat2, title, url, memo, parent_memo])
                        st.success(f"'{title}' 저장 완료!")
                        st.cache_data.clear() # 캐시 초기화
                        st.rerun() # 화면 새로고침
                    except Exception as e:
                        st.error(f"오류 발생: {e}")

# 메인 화면: 선택된 분류1에 대한 데이터 렌더링
if df.empty or '분류1' not in df.columns:
    st.info("📌 아직 등록된 링크가 없거나 구글 시트 형식이 맞지 않습니다. 왼쪽 '새 링크 추가'에서 링크를 등록해보세요.")
elif selected_cat1:
    # 1. 선택된 대분류(분류1) 데이터만 필터링
    cat1_df = df[df['분류1'] == selected_cat1]
    
    # 2. 대분류 타이틀 및 모분류메모 표시
    st.header(f"📁 {selected_cat1}")
    parent_memos = cat1_df['모분류메모'].dropna().unique()
    valid_parent_memos = [m for m in parent_memos if str(m).strip()]
    if valid_parent_memos:
        st.info(f"💡 {valid_parent_memos[0]}") # 첫 번째 모분류메모를 상단 팁으로 표시
        
    st.divider()
    
    # 3. 중분류(분류2) 기준으로 그룹화하여 화면에 카드 형태로 표시
    categories2 = sorted([c for c in cat1_df['분류2'].unique() if pd.notna(c)])
    
    # 분류2가 비어있는 데이터 처리
    has_empty_cat2 = cat1_df['분류2'].isna().any() or (cat1_df['분류2'] == '').any()
    if has_empty_cat2 and "" not in categories2:
        categories2.append("")
        
    for cat2 in categories2:
        # 서브헤더 이름 지정
        display_cat2 = cat2 if str(cat2).strip() else "기본 분류"
        st.subheader(f"🔹 {display_cat2}")
        
        # 해당 분류2 데이터 추출
        if str(cat2).strip():
            cat2_df = cat1_df[cat1_df['분류2'] == cat2]
        else:
            cat2_df = cat1_df[cat1_df['분류2'].isna() | (cat1_df['분류2'] == '')]
            
        # 반응형 3열 그리드 생성 (카드 레이아웃)
        cols = st.columns(3)
        for idx, row in cat2_df.reset_index().iterrows():
            with cols[idx % 3]: # 3개의 열에 번갈아가며 배치
                with st.container(border=True): # 테두리가 있는 카드 UI
                    st.markdown(f"**[{row['제목']}]({row['링크']})**")
                    if pd.notna(row.get('메모')) and str(row.get('메모')).strip():
                        st.caption(f"📝 {row['메모']}")
        st.write("") # 섹션 간 간격 띄우기
