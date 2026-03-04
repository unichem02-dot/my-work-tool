import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta, timezone
import re
import json

# --- [1] 페이지 기본 설정 (가장 먼저 와야 함) ---
st.set_page_config(layout="wide", page_title="송장텍스트변환 <LYC>")

# --- [2] 전체 테마(다크 모드) CSS ---
st.markdown("""
    <style>
        .stApp { background-color: #1a3636; color: white; }
        .stTextArea textarea { 
            background-color: #122626 !important; 
            color: white !important; 
            border: 1px solid #3c5e5d !important; 
            font-family: monospace; 
        }
        .stTabs [data-baseweb="tab-list"] { gap: 20px; }
        .stTabs [data-baseweb="tab"] { 
            background-color: transparent !important; 
            color: #8da9a7 !important; 
            font-size: 1.2rem; 
            font-weight: bold; 
        }
        .stTabs [aria-selected="true"] { 
            color: white !important; 
            border-bottom: 2px solid white !important; 
        }
        div[data-testid="stToolbar"] { display: none; }
    </style>
""", unsafe_allow_html=True)

# --- [3] 영어 학습 샘플 데이터 ---
study_data = [
    { "en": "Who is taller - Joe or David?", "ko": "조와 데이비드 중 누가 더 키가 큰가요?" },
    { "en": "We can go this way or that way.", "ko": "우리는 이쪽이나 저쪽으로 갈 수 있어요." },
    { "en": "Which way should we go?", "ko": "어느 쪽으로 가야 할까요?" },
    { "en": "There are four umbrellas here. Which is yours?", "ko": "여기에 네 개의 우산이 있습니다. 어느 것이 당신 것인가요?" },
    { "en": "What's the capital of Argentina?", "ko": "아르헨티나의 수도는 어디인가요?" },
    { "en": "I'm looking forward to the weekend.", "ko": "주말이 정말 기대돼요." },
    { "en": "Could you please speak a little slower?", "ko": "조금만 천천히 말씀해 주시겠어요?" },
    { "en": "It takes about an hour by train.", "ko": "기차로 약 한 시간 정도 걸립니다." },
    { "en": "Don't forget to lock the door.", "ko": "문 잠그는 것 잊지 마세요." },
    { "en": "Let's grab some coffee after work.", "ko": "퇴근하고 커피나 한잔 합시다." }
]

# --- [4] 세션 상태 초기화 ---
if 'show_study' not in st.session_state:
    st.session_state.show_study = False

# --- [5] 날짜 및 헤더 생성 로직 (KST 기준) ---
kst = timezone(timedelta(hours=9))
now = datetime.now(kst)

days = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
months = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']

day_name = days[int(now.strftime('%w'))]
month_name = months[now.month - 1]
full_english_date = f"{day_name}, {month_name} {now.day}, {now.year}"
today_str = now.strftime('%y%m%d')

copy_header = f"<<<<<<{full_english_date}, 경동마감>>>>>>"


# =========================================================
#  ★ 학습 모드 (전체 화면 대체 로직)
# =========================================================
def render_study_mode():
    data_json = json.dumps(study_data)
    html_code = f"""
    <div style="background: #0a0a0a; color: white; height: 85vh; display: flex; flex-direction: column; justify-content: space-between; align-items: center; font-family: sans-serif; border-radius: 20px; overflow: hidden; position: relative;">
        
        <div style="flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; width: 100%; text-align: center;">
            <div id="rolling-container"></div>
        </div>

        <div style="width: 100%; border-top: 1px solid rgba(255,255,255,0.1); padding: 40px; text-align: center;">
            <p id="ko-text" style="color: #a08b7a; font-size: 26px; font-weight: bold; margin: 0; transition: opacity 0.5s;"></p>
        </div>
    </div>

    <script>
        const studyData = {data_json};
        let currentIndex = 0;
        const container = document.getElementById('rolling-container');
        const koText = document.getElementById('ko-text');

        function render() {{
            container.innerHTML = '';
            koText.style.opacity = 0;
            
            setTimeout(() => {{
                koText.innerText = studyData[currentIndex].ko;
                koText.style.opacity = 1;
            }}, 200);

            studyData.forEach((item, index) => {{
                const distance = index - currentIndex;
                if (distance < -2 || distance > 2) return;

                const div = document.createElement('div');
                div.style.position = 'absolute';
                div.style.width = '100%';
                div.style.transition = 'all 0.7s ease-in-out';
                div.style.left = '0';
                
                if (distance === 0) {{
                    div.style.top = '50%';
                    div.style.transform = 'translateY(-50%) scale(1.2)';
                    div.style.opacity = '1';
                    div.style.color = '#E67E22';
                    div.style.fontWeight = '900';
                    div.style.textShadow = '0 0 15px rgba(230,126,34,0.3)';
                    div.style.zIndex = '10';
                }} else {{
                    div.style.top = `calc(50% + ${{distance * 90}}px)`;
                    div.style.transform = 'translateY(-50%) scale(0.9)';
                    div.style.opacity = Math.abs(distance) === 1 ? '0.4' : '0.15';
                    div.style.color = 'rgba(255,255,255,0.4)';
                    div.style.fontWeight = '500';
                    div.style.zIndex = '5';
                }}

                div.innerHTML = `<p style="font-size: 32px; margin: 0; letter-spacing: 1px;">${{item.en}}</p>`;
                container.appendChild(div);
            }});
        }}

        setInterval(() => {{
            currentIndex = (currentIndex + 1) % studyData.length;
            render();
        }}, 5000);

        render();
    </script>
    """
    components.html(html_code, height=800)

if st.session_state.show_study:
    # 학습 모드가 켜져있으면 다른 화면은 숨기고 학습 화면만 띄웁니다.
    col1, col2, col3 = st.columns([1, 8, 1])
    with col2:
        if st.button("❌ 학습 모드 종료 (돌아가기)", use_container_width=True):
            st.session_state.show_study = False
            st.rerun()
        render_study_mode()
    st.stop() # 이후의 메인 앱 UI는 그리지 않음


# =========================================================
#  ★ 메인 송장 변환기 앱
# =========================================================

# --- 복사 버튼용 커스텀 컴포넌트 ---
copy_html = f"""
<div style="display: flex; align-items: center; justify-content: space-between; font-family: sans-serif; color: white;">
    <span style="font-size: 22px; font-weight: 900;">{copy_header}</span>
    <button id="copybtn" onclick="copyText()"
            style="padding: 10px 20px; border-radius: 50px; border: 1px solid white; background: transparent; color: white; cursor: pointer; font-weight: bold; font-size: 14px;">
        📋 복사하기
    </button>
</div>
<script>
    function copyText() {{
        const el = document.createElement('textarea');
        el.value = '{copy_header}';
        document.body.appendChild(el);
        el.select();
        document.execCommand('copy');
        document.body.removeChild(el);
        const btn = document.getElementById('copybtn');
        btn.innerText = '✅ 복사완료!';
        btn.style.backgroundColor = '#03C75A';
        btn.style.borderColor = '#03C75A';
        setTimeout(() => {{ 
            btn.innerText = '📋 복사하기'; 
            btn.style.backgroundColor = 'transparent';
            btn.style.borderColor = 'white';
        }}, 2000);
    }}
</script>
"""

# 상단 레이아웃
top_col1, top_col2 = st.columns([7, 3])
with top_col1:
    components.html(copy_html, height=60)
with top_col2:
    if st.button("📚 영어 문장 학습 (새창)", use_container_width=True, type="primary"):
        st.session_state.show_study = True
        st.rerun()

st.markdown("""
<div style="display:flex; align-items: baseline; gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.1); padding-bottom: 15px; margin-bottom: 20px;">
    <h1 style="margin: 0; font-weight: 900; font-size: 2.2rem;">송장텍스트변환 &lt;LYC&gt;</h1>
    <span style="color: rgba(255,255,255,0.6); font-weight: bold;">lodus11st@naver.com</span>
</div>
""", unsafe_allow_html=True)


# --- 데이터 변환 함수 ---
def convert_jeonjin(text):
    if not text.strip(): return ""
    lines = text.strip().split('\n')
    result = []
    for line in lines:
        parts = [p.strip() for p in line.split('\t')]
        if len(parts) < 7: continue
        try:
            zip_code, addr, name, p1, p2, qty_str = parts[:6]
            raw_prod = parts[7] if len(parts) > 7 else ""
            note = parts[8] if len(parts) > 8 else ""
            
            p1_clean = re.sub(r'[^0-9]', '', p1)
            p2_clean = re.sub(r'[^0-9]', '', p2) if p2 else ""
            phone = f"{p1} / {p2}" if p2_clean and p1_clean != p2_clean else p1
            
            qty = int(qty_str) if qty_str.isdigit() else 1
            product_name = raw_prod
            if "차아염소산" in raw_prod or "차염" in raw_prod: product_name = "차염산"
            elif "구연산" in raw_prod: product_name = "구연산수50%(20kg)"
            elif "PAC" in raw_prod: product_name = "PAC17%"
            elif "가성소다" in raw_prod: product_name = "가성소다4.5%(20kg)"
            
            pallet_text = " - 파래트" if qty >= 10 else ""
            
            res = f"{product_name} {qty}통{pallet_text} (송장번호필요)\n--------------\n택배선불로 보내주세요^^\n{zip_code}\n{addr}\n{name} {phone}"
            if note: res += f"\n{note}"
            result.append(res)
        except Exception:
            continue
    return '\n\n'.join(result)

def convert_uni(text):
    if not text.strip(): return ""
    separator = f"{today_str}{'-'*24}"
    lines = text.strip().split('\n')
    result = []
    for line in lines:
        parts = [p.strip() for p in line.split('\t')]
        if len(parts) < 5:
            result.append(f"⚠️ 데이터 부족: {line}")
            continue
        try:
            zip_code, addr, name, tel1 = parts[:4]
            tel2_raw = parts[4] if len(parts) > 4 else ""
            qty = parts[5] if len(parts) > 5 else ""
            pay = parts[6] if len(parts) > 6 else ""
            prod = parts[7] if len(parts) > 7 else ""
            memo = parts[8] if len(parts) > 8 else ""

            t1_clean = re.sub(r'[^0-9]', '', tel1)
            t2_clean = re.sub(r'[^0-9]', '', tel2_raw)
            tel_display = tel1 if t1_clean == t2_clean or not tel2_raw else f"{tel1}\t{tel2_raw}"
            
            res = f"{zip_code}\n{addr}\n{name}\t{tel_display}\n{qty}\t{pay}\t{prod}"
            if memo: res += f"\n{memo}"
            result.append(res)
        except Exception:
            result.append(f"❌ 에러: {line}")
    
    joined = f"\n\n{separator}\n\n".join(result)
    return f"{joined}\n\n{separator}"


# --- 탭 UI ---
tab1, tab2 = st.tabs(["📦 텍스트변환(전진발주)", "📝 텍스트변환(유니케미칼)"])

with tab1:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**1. 엑셀 데이터 붙여넣기**")
        j_in = st.text_area("jeonjin_input", label_visibility="collapsed", height=500)
    with col2:
        st.markdown("**2. 변환 결과**")
        st.text_area("jeonjin_output", value=convert_jeonjin(j_in), label_visibility="collapsed", height=500)

with tab2:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**1. 엑셀 데이터 붙여넣기**")
        u_in = st.text_area("uni_input", label_visibility="collapsed", height=500)
    with col2:
        st.markdown("**2. 변환 결과**")
        st.text_area("uni_output", value=convert_uni(u_in), label_visibility="collapsed", height=500)

st.markdown(f"<div style='text-align: center; margin-top: 50px; color: rgba(255,255,255,0.4); font-weight: bold;'>© {now.year} LYC TEXT CONVERTER | All rights reserved.</div>", unsafe_allow_html=True)
