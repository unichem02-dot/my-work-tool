import streamlit as st
import streamlit.components.v1 as components
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import time
import io
import math
import re
import json
import urllib.parse
import concurrent.futures
from datetime import datetime, timedelta, timezone

# --- [페이지 기본 설정] ---
st.set_page_config(layout="wide", page_title="TOmBOy94 English")

# --- [세션 상태 관리 초기화] ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = st.query_params.get("auth") == "true"
if "logging_in" not in st.session_state:
    st.session_state.logging_in = False
if 'sort_order' not in st.session_state: st.session_state.sort_order = 'None'
if 'current_cat' not in st.session_state: st.session_state.current_cat = "🔀 랜덤 10"
if 'num_input' not in st.session_state: st.session_state.num_input = ""
if 'active_search' not in st.session_state: st.session_state.active_search = ""
if 'search_input' not in st.session_state: st.session_state.search_input = ""
if 'is_simple' not in st.session_state: st.session_state.is_simple = False
if 'curr_p' not in st.session_state: st.session_state.curr_p = 1
if 'app_mode' not in st.session_state: st.session_state.app_mode = 'English' 

# --- [보안 설정 및 Google Sheets 연결] ---
LOGIN_PASSWORD = st.secrets["tom_password"]

# 콜백 함수들
def handle_search():
    st.session_state.active_search = st.session_state.search_input.strip()
    st.session_state.search_input = ""
    st.session_state.curr_p = 1

def clear_search():
    st.session_state.active_search = ""
    st.session_state.curr_p = 1

def reset_page():
    st.session_state.curr_p = 1

def set_state(key, val):
    st.session_state[key] = val

# ★ 안전한 CSV 변환 전용 함수 (모바일 에러 방지용)
@st.cache_data(show_spinner=False)
def convert_df_to_csv(df_to_convert):
    return df_to_convert.to_csv(index=False).encode('utf-8-sig')

# --- [전체화면 학습 모드 컴포넌트 렌더링 함수] ---
def render_study_mode(study_data, unique_cats, initial_cat):
    data_json = json.dumps(study_data, ensure_ascii=False)
    cats_json = json.dumps(unique_cats, ensure_ascii=False)
    
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <style>
        /* 내부 iframe의 여백 완벽 제거 */
        body {{ margin: 0; padding: 0; background: #0a0a0a; overflow: hidden; font-family: sans-serif; cursor: pointer; user-select: none; -webkit-user-select: none; }}
        .container {{ width: 100vw; height: 100vh; display: flex; flex-direction: column; justify-content: space-between; align-items: center; position: relative; }}
        
        /* 상단 헤더 바 (좌측 컨트롤 그룹) */
        .header-bar {{ position: absolute; top: 20px; left: 30px; right: 30px; display: flex; justify-content: space-between; align-items: center; z-index: 100; cursor: default; }}
        .left-controls {{ display: flex; gap: 15px; align-items: center; flex-wrap: wrap; background: rgba(0,0,0,0.5); padding: 5px 15px; border-radius: 15px; }}
        
        /* 셀렉터 투명화 및 테두리 제거 */
        .cat-select {{ background: transparent; color: #FFFFFF; border: none; padding: 8px 10px; font-size: 18px; border-radius: 8px; font-weight: bold; cursor: pointer; outline: none; transition: 0.3s; appearance: none; -webkit-appearance: none; text-align: center; }}
        .cat-select:hover {{ background: rgba(255,255,255,0.15); }}
        .cat-select option {{ background: #0a0a0a; color: #FFFFFF; }}
        
        /* 재생 컨트롤러 */
        .playback-controls {{ display: flex; gap: 8px; border-left: 1px solid rgba(255,255,255,0.2); border-right: 1px solid rgba(255,255,255,0.2); padding: 0 15px; }}
        .playback-controls button {{ background: rgba(255,255,255,0.15); border: none; color: white; font-size: 14px; padding: 8px 14px; border-radius: 8px; cursor: pointer; transition: 0.3s; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }}
        .playback-controls button:hover {{ background: rgba(255,255,255,0.3); transform: translateY(-2px); }}
        .playback-controls button:active {{ transform: translateY(0); box-shadow: 0 2px 4px rgba(0,0,0,0.3); }}

        /* SIMPLE & 기타 버튼 */
        .simple-btn {{ background: rgba(255,255,255,0.15); border: none; color: white; font-size: 14px; padding: 8px 14px; border-radius: 8px; cursor: pointer; transition: 0.3s; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.3); margin-left: 5px; }}
        .simple-btn:hover {{ background: rgba(255,255,255,0.3); transform: translateY(-2px); }}
        .simple-btn:active {{ transform: translateY(0); box-shadow: 0 2px 4px rgba(0,0,0,0.3); }}
        
        /* 현재 단어의 분류 표시 라벨 */
        #word-cat-display {{ color: #FFFFFF; font-weight: bold; font-size: 17px; margin-left: 5px; padding-left: 15px; border-left: 1px solid rgba(255,255,255,0.2); opacity: 0.8; letter-spacing: 1px; }}

        /* 메인 컨텐츠 영역 */
        #rolling-container {{ flex: 1; display: flex; flex-direction: column; justify-content: center; position: relative; width: 100%; text-align: center; align-items: center; padding: 0 20px; }}
        
        /* 텍스트 스타일 관련 클래스 제거 및 인라인 적용 (자바스크립트에서 관리) */
    </style>
    </head>
    <body>
    <div class="container">
        <div class="header-bar">
            <div class="left-controls">
                <select id="category-select" class="cat-select" onchange="changeCategory()"></select>
                <div class="playback-controls">
                    <button onclick="movePrev()">&lt;</button>
                    <button onclick="togglePause()" id="pause-btn">멈춤</button>
                    <button onclick="moveNext()">&gt;</button>
                </div>
                <select id="speed-select" class="cat-select" onchange="changeSpeed()">
                    <option value="2300">2.3초</option>
                    <option value="4000">4초</option>
                    <option value="7000">7초</option>
                    <option value="10000" selected>10초</option>
                    <option value="15000">15초</option>
                    <option value="20000">20초</option>
                    <option value="30000">30초</option>
                </select>
                <button id="touch-btn" class="simple-btn" onclick="toggleTouchMode()">👆 TOUCH OFF</button>
                <button id="simple-btn" class="simple-btn" onclick="toggleSimpleMode()">SIMPLE OFF</button>
                <button id="tts-btn" class="simple-btn" onclick="toggleTTS()">🔇 소리 끄기</button>
                <span id="word-cat-display"></span>
            </div>
        </div>
        
        <div id="rolling-container"></div>
    </div>

    <script>
        const rawData = {data_json};
        const categories = {cats_json};
        let filteredData = [];
        let currentIndex = 0;
        let intervalId;
        let isPaused = false;
        let currentSpeed = 10000;
        let isSimpleMode = false;
        let isTTSEnabled = false;
        let isTouchMode = false; // ★ 터치 모드 상태 변수
        let availableVoices = [];

        // 브라우저에 내장된 고품질 음성 목록 미리 로드
        function loadVoices() {{
            availableVoices = window.speechSynthesis.getVoices();
        }}
        loadVoices();
        if (window.speechSynthesis.onvoiceschanged !== undefined) {{
            window.speechSynthesis.onvoiceschanged = loadVoices;
        }}

        // 확실한 창닫기 (iframe 우회하여 최상위 부모 창 닫기 시도)
        function closeWindow() {{
            try {{ window.top.close(); }} catch(e) {{}}
            try {{ window.parent.close(); }} catch(e) {{}}
            window.close();
        }}

        // 카테고리 드롭다운 렌더링
        const selectEl = document.getElementById('category-select');
        let allOpt = document.createElement('option');
        allOpt.value = "ALL";
        allOpt.innerText = "전체 랜덤";
        selectEl.appendChild(allOpt);
        
        categories.forEach(cat => {{
            let opt = document.createElement('option');
            opt.value = cat;
            opt.innerText = cat; // 랜덤 글자 제거됨
            if (cat === "{initial_cat}") opt.selected = true;
            selectEl.appendChild(opt);
        }});
        
        if ("{initial_cat}" === "ALL") {{
            selectEl.value = "ALL";
        }}

        // 속도 변경
        function changeSpeed() {{
            currentSpeed = parseInt(document.getElementById('speed-select').value);
            if(!isPaused && !isTouchMode) resetInterval();
        }}

        // 배열 셔플
        function shuffle(array) {{
            let arr = [...array];
            for (let i = arr.length - 1; i > 0; i--) {{
                const j = Math.floor(Math.random() * (i + 1));
                [arr[i], arr[j]] = [arr[j], arr[i]];
            }}
            return arr;
        }}

        // 카테고리 변경 시 실행
        function changeCategory() {{
            const selected = selectEl.value;
            if (selected === "ALL") {{
                filteredData = shuffle(rawData);
            }} else {{
                // 모든 카테고리(시트 이름 상관없이) 랜덤 섞기 적용
                let catData = rawData.filter(d => d.cat === selected);
                filteredData = shuffle(catData);
            }}
            currentIndex = 0;
            renderRolling();
            resetInterval();
        }}

        // 컨트롤러 기능
        function movePrev() {{
            if (!filteredData || filteredData.length === 0) return;
            currentIndex = (currentIndex - 1 + filteredData.length) % filteredData.length;
            renderRolling();
            resetInterval();
        }}
        function moveNext() {{
            if (!filteredData || filteredData.length === 0) return;
            currentIndex = (currentIndex + 1) % filteredData.length;
            renderRolling();
            resetInterval();
        }}
        
        function togglePause() {{
            isPaused = !isPaused;
            const btn = document.getElementById('pause-btn');
            if(isPaused) {{
                if (intervalId) clearInterval(intervalId);
                btn.innerText = "재생";
                btn.style.background = "rgba(255,255,255,0.3)";
            }} else {{
                resetInterval();
                btn.innerText = "멈춤";
                btn.style.background = "rgba(255,255,255,0.15)";
            }}
        }}

        // ★ TOUCH 모드 토글 (터치 시에만 다음으로 넘어가는 수동 모드)
        function toggleTouchMode() {{
            isTouchMode = !isTouchMode;
            const btn = document.getElementById('touch-btn');
            if(isTouchMode) {{
                btn.style.background = "rgba(230,126,34,0.7)";
                btn.innerText = "👆 TOUCH ON";
                // 터치 모드를 켜면 자동 재생 인터벌 해제
                if (intervalId) clearInterval(intervalId);
            }} else {{
                btn.style.background = "rgba(255,255,255,0.15)";
                btn.innerText = "👆 TOUCH OFF";
                // 터치 모드를 끄면 다시 자동 재생 시작 (일시정지 상태가 아니라면)
                resetInterval();
            }}
        }}

        // SIMPLE 모드 토글
        function toggleSimpleMode() {{
            isSimpleMode = !isSimpleMode;
            const btn = document.getElementById('simple-btn');
            if(isSimpleMode) {{
                btn.style.background = "rgba(230,126,34,0.7)";
                btn.innerText = "SIMPLE ON";
            }} else {{
                btn.style.background = "rgba(255,255,255,0.15)";
                btn.innerText = "SIMPLE OFF";
            }}
            renderRolling(); // 모드 변경 즉시 화면 갱신
        }}

        // TTS 음성 재생 토글
        function toggleTTS() {{
            isTTSEnabled = !isTTSEnabled;
            const btn = document.getElementById('tts-btn');
            if(isTTSEnabled) {{
                btn.style.background = "rgba(230,126,34,0.7)";
                btn.innerText = "🔊 소리 켜기";
                if(filteredData.length > 0) {{
                    window.speechSynthesis.cancel();
                    speakText(filteredData[currentIndex].en, 'en-US');
                    if(filteredData[currentIndex].ko) speakText(filteredData[currentIndex].ko, 'ko-KR');
                }}
            }} else {{
                btn.style.background = "rgba(255,255,255,0.15)";
                btn.innerText = "🔇 소리 끄기";
                window.speechSynthesis.cancel();
            }}
        }}

        // 오직 미국식(US) 고품질 원어민 음성을 최우선으로 선택하는 로직
        function speakText(text, lang) {{
            if (!window.speechSynthesis) return;
            
            // 파이썬 f-string 충돌 방지 및 특수 기호(/, ?, (, ), [, ], ~) 제거 필터링
            const cleanText = text.replace(/[/?()[\\]~]/g, ' ');
            
            const utterance = new SpeechSynthesisUtterance(cleanText);
            utterance.lang = lang; 
            
            // 영어는 연음이 부드럽고 자연스럽게 들리도록 0.95 세팅, 한국어는 0.9 유지
            utterance.rate = lang === 'en-US' ? 0.95 : 0.9; 
            utterance.pitch = 1.0;

            if (availableVoices.length > 0) {{
                let bestVoice = null;
                
                if (lang === 'en-US') {{
                    // 1순위: 크롬 브라우저의 고품질 클라우드 음성 (미국식)
                    bestVoice = availableVoices.find(voice => voice.name === 'Google US English');
                    
                    // 2순위: 엣지 브라우저의 고품질 신경망(Natural) 미국식 음성
                    if (!bestVoice) {{
                        bestVoice = availableVoices.find(voice => voice.name.includes('Natural') && voice.lang === 'en-US');
                    }}
                    // 3순위: 애플 Mac/iOS의 자연스러운 기본 식 음성
                    if (!bestVoice) {{
                        bestVoice = availableVoices.find(voice => (voice.name === 'Samantha' || voice.name === 'Alex') && voice.lang === 'en-US');
                    }}
                    // 4순위: 기타 고품질 미국 영어
                    if (!bestVoice) {{
                        bestVoice = availableVoices.find(voice => voice.lang === 'en-US' && (voice.name.includes('Premium') || voice.name.includes('Enhanced')));
                    }}
                    // 5순위: 기본 미국 영어 (영국식 배제 보장)
                    if (!bestVoice) {{
                        bestVoice = availableVoices.find(voice => voice.lang === 'en-US');
                    }}
                }} else if (lang === 'ko-KR') {{
                    bestVoice = availableVoices.find(voice => voice.name === 'Google 한국의');
                    if (!bestVoice) bestVoice = availableVoices.find(voice => voice.name.includes('Natural') && voice.lang.includes('ko'));
                    if (!bestVoice) bestVoice = availableVoices.find(voice => voice.lang.includes('ko-KR'));
                }}

                // 가장 좋은 음성 엔진 적용
                if (bestVoice) {{
                    utterance.voice = bestVoice;
                }}
            }}
            
            window.speechSynthesis.speak(utterance);
        }}

        // 1단 집중 디자인 및 시간차 렌더링
        function renderRolling() {{
            if (!filteredData || filteredData.length === 0) return;
            const container = document.getElementById('rolling-container');
            
            // 기존 문장 부드럽게 지우기
            const oldItems = container.children;
            for(let i=0; i<oldItems.length; i++) {{
                oldItems[i].style.opacity = '0';
                setTimeout((el) => {{ if (container.contains(el)) container.removeChild(el); }}, 600, oldItems[i]);
            }}

            const item = filteredData[currentIndex];
            
            // 상단 바에 현재 단어의 카테고리 표시
            document.getElementById('word-cat-display').innerText = item.cat;

            // 새 컨테이너 박스 생성
            const div = document.createElement('div');
            div.style.position = 'absolute';
            div.style.width = '100%';
            div.style.transition = 'opacity 0.6s ease-in-out';
            div.style.left = '0';
            div.style.top = '50%';
            div.style.transform = 'translateY(-50%)'; 
            div.style.padding = '0 20px';
            div.style.boxSizing = 'border-box';
            div.style.opacity = '0'; 
            div.style.zIndex = '10';

            // ★ 창 크기(vw, vh)에 비례하여 화면에 완벽하게 꽉 차도록 사이즈 동적 계산
            let enFontSize = item.en.length > 25 ? 'min(7vw, 9vh)' : 'min(10vw, 13vh)';
            let pronSize = 'min(3.5vw, 4.5vh)';
            let koSize = 'min(5.5vw, 7vh)';
            let memoSize = 'min(3vw, 4vh)';

            // 구성 요소들 (발음, 해석, 메모) - 높이 비율에 맞춘 여백(vh) 적용
            let pronHtml = (item.pron && item.pron.length <= 60) ? `<p style="font-size: ` + pronSize + `; color: #FFFFFF; margin: 2vh 0 0 0; font-weight: normal; font-style: italic; text-shadow: none;">${{item.pron}}</p>` : "";
            
            let koHtml = item.ko ? `<p class="anim-ko" style="color: #a08b7a; font-size: ` + koSize + `; font-weight: bold; margin: 3vh 0 0 0; opacity: 0; transition: opacity 0.5s ease-in-out; word-break: keep-all; line-height: 1.4; text-shadow: none;">${{item.ko}}</p>` : "";
            
            let memoHtml = "";
            if (!isSimpleMode) {{
                memoHtml = `<div class="anim-memo" style="opacity: 0; transition: opacity 0.5s ease-in-out; margin-top: 2.5vh; text-shadow: none;">`;
                if (item.memo1) memoHtml += `<p style="color: #FFFF00; font-size: ` + memoSize + `; font-weight: 500; margin: 1vh 0; word-break: keep-all; line-height: 1.4;">${{item.memo1}}</p>`;
                if (item.memo2) memoHtml += `<p style="color: #FFFF00; font-size: ` + memoSize + `; font-weight: 500; margin: 1vh 0; word-break: keep-all; line-height: 1.4;">${{item.memo2}}</p>`;
                memoHtml += `</div>`;
            }}

            // DOM 병합 (중앙 영역)
            div.innerHTML = `<div style="color: #E67E22; font-weight: 900; text-shadow: 0 0 20px rgba(230,126,34,0.4);"><p style="font-size: ` + enFontSize + `; margin: 0; letter-spacing: 0.5px; word-break: keep-all; line-height: 1.2;">${{item.en}}</p></div>` 
                            + pronHtml 
                            + koHtml 
                            + memoHtml; 
            
            container.appendChild(div);

            // 전체 프레임 페이드 인
            setTimeout(() => {{ div.style.opacity = '1'; }}, 50);

            // 2초 뒤 해석 페이드 인
            if(item.ko) {{
                setTimeout(() => {{
                    const koEl = div.querySelector('.anim-ko');
                    if(koEl) koEl.style.opacity = '1';
                }}, 2000);
            }}

            // 5초 뒤 메모 페이드 인
            if(!isSimpleMode && (item.memo1 || item.memo2)) {{
                setTimeout(() => {{
                    const memoEl = div.querySelector('.anim-memo');
                    if(memoEl) memoEl.style.opacity = '1';
                }}, 5000);
            }}

            // 단어가 바뀔 때마다 영어 -> 한국어 순서대로 재생
            if(isTTSEnabled) {{
                window.speechSynthesis.cancel(); 
                speakText(item.en, 'en-US');
                if(item.ko) speakText(item.ko, 'ko-KR');
            }}
        }}

        // 다음 단어로 이동
        function step() {{
            currentIndex = (currentIndex + 1) % filteredData.length;
            renderRolling();
        }}

        // 인터벌 설정 로직 (터치 모드나 일시정지 상태일 때는 타이머 작동 안 함)
        function resetInterval() {{
            if (intervalId) clearInterval(intervalId);
            if (!isTouchMode && !isPaused) {{
                intervalId = setInterval(step, currentSpeed);
            }}
        }}

        // ★ 터치 모드일 때만 화면 클릭으로 다음 넘어가기 작동
        document.body.addEventListener('click', function(e) {{
            // 상단 컨트롤 바(버튼, 셀렉터 등) 클릭 시에는 작동하지 않도록 예외 처리
            if (e.target.closest('.header-bar')) return;
            
            if (isTouchMode) {{
                moveNext(); // 터치 모드가 켜져 있을 때만 클릭 시 다음 단어로 이동
            }}
        }});

        // 초기 시작
        changeCategory();

    </script>
    </body>
    </html>
    """
    components.html(html_code, height=1000)

@st.cache_resource
def init_connection():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=scopes)
    return gspread.authorize(creds)

# 개별 시트를 안전하게 가져오는 헬퍼 함수
def _fetch_sheet_concurrently(wb, sheet_name):
    try:
        sheet = wb.worksheet(sheet_name)
        data = sheet.get_all_values()
        if not data: 
            return pd.DataFrame()
        rows = [row + [""] * (6 - len(row)) for row in data[1:]]
        df = pd.DataFrame(rows, columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2'])
        for col in df.columns: df[col] = df[col].astype(str).str.strip()
        df['sheet_idx'] = sheet_name
        df['row_idx'] = df.index + 2
        
        # ★ 모든 시트에 대해 동일하게 행 번호 오름차순 적용 (해석 시트 예외 로직 제거)
        return df.sort_values(by='row_idx', ascending=True)
    except Exception:
        return pd.DataFrame()

# ★ 함수명을 변경하여 기존에 저장되어 있던 잘못된 정렬 캐시를 강제로 삭제하고 새로 불러옵니다.
@st.cache_data(ttl=600)
def get_english_data_v2():
    wb = init_connection().open("English_Sentences")
    sheet_names = ["메인", "해석", "구동사", "TOM-영어", "동사구", "문법", "여행", "단어"]
    
    dfs = []
    # ★ 핵심: ThreadPoolExecutor를 사용해 모든 시트를 동시에 읽어옴
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sheet_names)) as executor:
        results = executor.map(lambda name: _fetch_sheet_concurrently(wb, name), sheet_names)
        for res in results:
            if not res.empty:
                dfs.append(res)
    
    if not dfs:
        return pd.DataFrame(columns=['분류', '단어-문장', '해석', '발음', '메모1', '메모2', 'sheet_idx', 'row_idx'])
    return pd.concat(dfs, ignore_index=True)

def get_links_sheet():
    return init_connection().open("English_Sentences").worksheet("링크")

@st.cache_data(ttl=600)
def get_links_data_v2():
    sheet = get_links_sheet()
    for _ in range(3):
        try:
            data = sheet.get_all_values()
            if not data: return pd.DataFrame(columns=['대분류', '소분류', '제목', '메모', '링크', 'row_idx'])
            rows = [row + [""] * (5 - len(row)) for row in data[1:]]
            df = pd.DataFrame(rows, columns=['대분류', '소분류', '제목', '메모', '링크'])
            for col in df.columns: df[col] = df[col].astype(str).str.strip()
            df['row_idx'] = df.index + 2
            # ★ 링크도 행 번호 오름차순으로 명시적 정렬
            return df.sort_values(by='row_idx', ascending=True)
        except: time.sleep(1)
    raise Exception("링크 데이터 로드 실패")


# ==============================================================
# ★ 새창 열림 전용 라우팅 (URL 파라미터에 study=true가 있을 때)
# ==============================================================
if st.query_params.get("study") == "true":
    st.markdown("""
        <style>
            html, body, [data-testid="stAppViewContainer"], .main, .block-container {
                padding: 0 !important; margin: 0 !important; max-width: 100% !important; background-color: #0a0a0a !important; overflow: hidden !important;
            }
            [data-testid="stHeader"], footer, div[data-testid="stToolbar"] { display: none !important; }
            iframe { position: fixed !important; top: 0 !important; left: 0 !important; width: 100vw !important; height: 100vh !important; border: none !important; z-index: 99999 !important; }
        </style>
    """, unsafe_allow_html=True)
    
    try:
        df = get_english_data_v2() # 변경된 캐시 함수 사용
        unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
        cat_param = st.query_params.get("cat", "ALL")
        initial_cat = "ALL" if cat_param in ["🔀 랜덤 10", "전체 분류", "ALL"] else cat_param
        
        # ★ 모바일 에러 방지를 위해 변환 과정을 명시적으로 분리
        study_df = df[['분류', '단어-문장', '해석', '발음', '메모1', '메모2', 'sheet_idx']].rename(
            columns={'분류':'cat', '단어-문장': 'en', '해석': 'ko', '발음': 'pron', '메모1': 'memo1', '메모2': 'memo2'}
        )
        study_data = study_df.to_dict('records')
        
        if not study_data:
            st.error("데이터가 없습니다. 창을 닫아주세요.")
        else:
            render_study_mode(study_data, unique_cats, initial_cat)
            
    except Exception as e:
        st.error(f"데이터 로드 실패: {e}")
        
    st.stop() # 새창 모드일 때는 아래의 기본 앱을 실행하지 않음


# --- [사용자 정의 디자인 (CSS) - 디자인 대폭 개편 및 기존 폼 유지] ---
st.markdown("""
    <style>
    /* ★ 스트림릿 기본 상하단 메뉴 완벽 제거 */
    [data-testid="stHeader"], 
    [data-testid="stToolbar"], 
    #MainMenu, 
    footer {
        display: none !important;
        visibility: hidden !important;
    }

    /* 1. 배경 설정: 짙은 다크그린 */
    [data-testid="stAppViewContainer"],
    div[data-testid="stDialog"] > div,
    div[role="dialog"] > div {
        background-color: #224343 !important;
    }

    /* 2. 글자색 화이트 강제화 및 타이틀 하단 여백 제거 */
    h1, h2, h3, h4, h5, h6, p, span, label, summary, b, strong {
        color: #FFFFFF !important;
    }
    
    /* 팝업창(Dialog) 제목 */
    #새-항목-추가, #항목-수정-및-삭제, #새-링크-추가, #링크-수정-및-삭제,
    div[data-testid="stDialog"] h2,
    div[role="dialog"] h2,
    section[role="dialog"] h2 {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 3. 입력창 디자인 세련되게 변경 */
    .stTextInput input, .stTextArea textarea {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        border: 1px solid #A3B8B8 !important;
        border-radius: 10px !important;
        font-size: 1.1rem !important;
        padding: 10px 15px !important;
        transition: all 0.3s ease !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        background-color: #FFFFFF !important;
        border-color: #FFD700 !important;
        box-shadow: 0 0 8px rgba(255, 215, 0, 0.4) !important;
    }
    div[data-testid="stTextInput"] button { display: none !important; } /* 검색창 눈알 아이콘 숨김 */
    
    /* ★ Num.ENG 변환기 전용 입력창 (흰색 배경 / 검은색 글자) */
    div[data-testid="stTextInput"]:has(input[placeholder*="숫자를 입력하면"]) input {
        background-color: #FFFFFF !important;
        color: #000000 !important;
        font-weight: bold !important;
    }

    /* 4. 컨텐츠 행(Row) 호버 효과 및 기존 레이아웃 보정 (표 형태) */
    div.element-container:has(.row-marker) { width: 100% !important; min-width: 100% !important; }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) {
        transition: background-color 0.3s ease;
        padding: 12px 10px 16px 10px !important; 
        border-radius: 0px !important; 
        margin-bottom: 0px !important; border-bottom: 1px dotted rgba(255, 255, 255, 0.2) !important; 
        width: 100% !important; min-width: 100% !important; flex: 1 1 100% !important;
        display: flex !important; flex-direction: row !important; flex-wrap: nowrap !important;
        align-items: center !important; overflow: visible !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover { background-color: rgba(26, 47, 47, 0.9) !important; }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) > div[data-testid="column"] {
        display: flex !important; flex-direction: column !important; justify-content: center !important; 
        padding: 0 !important; margin: 0 !important; overflow: visible !important;
    }
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div.element-container,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) div.stMarkdown,
    div[data-testid="stHorizontalBlock"]:has(.row-marker) p {
        display: block !important; margin: 0 !important; padding: 0 !important;
        line-height: 1.5 !important; width: 100% !important;
    }

    /* 5. 분류 리스트(Radio) 모던한 Chip 디자인 (유지) */
    div[data-testid="stRadio"] > div[role="radiogroup"] {
        flex-direction: row !important; flex-wrap: wrap !important; gap: 8px 12px !important;
        padding-top: 10px !important; padding-bottom: 10px !important;
        justify-content: center !important;
    }
    div[data-testid="stRadio"] label > div:first-of-type { display: none !important; }
    div[data-testid="stRadio"] label {
        cursor: pointer !important; margin: 0 !important; 
        background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.1)) !important;
        padding: 8px 22px !important; border-radius: 12px !important; 
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
    }
    div[data-testid="stRadio"] label:hover { 
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 12px rgba(0,0,0,0.2) !important;
        border-color: #FFD700 !important; 
    }
    div[data-testid="stRadio"] label p {
        color: #FFFFFF !important; font-size: clamp(0.95rem, 1.2vw, 1.2rem) !important;
        font-weight: 800 !important; white-space: pre-wrap !important; text-align: center !important; line-height: 1.2 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked), div[data-testid="stRadio"] label:has(div[aria-checked="true"]) {
        background: #FFD700 !important; border-color: #FFD700 !important;
    }
    div[data-testid="stRadio"] label:has(input:checked) p, div[data-testid="stRadio"] label:has(div[aria-checked="true"]) p {
        color: #224343 !important;
    }

    /* ★ 소분류 전용 라디오 버튼 스타일 */
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label {
        padding: 6px 16px !important; background: rgba(255, 165, 0, 0.1) !important; border-color: rgba(255, 165, 0, 0.2) !important;
    }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label p {
        color: #FFA500 !important; font-size: clamp(0.8rem, 1.0vw, 1.0rem) !important; 
    }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:hover { border-color: #FFA500 !important; background-color: rgba(255, 165, 0, 0.2) !important; }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(input:checked), 
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(div[aria-checked="true"]) {
        background: #FFA500 !important; border-color: #FFA500 !important;
    }
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(input:checked) p, 
    div[data-testid="stRadio"]:has(div[aria-label="소분류 필터"]) label:has(div[aria-checked="true"]) p {
        color: #224343 !important;
    }

    /* 6. 버튼 기본 스타일 */
    button, div.stDownloadButton > button {
        border-radius: 12px !important; padding: 0.6rem 1.2rem !important; font-weight: 900 !important;
        transition: all 0.3s ease !important; white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important;
    }
    button[kind="primary"] { background-color: #FFFFFF !important; border-color: #FFFFFF !important; }
    button[kind="primary"] p { color: #224343 !important; font-size: clamp(0.85rem, 1.1vw, 1.15rem) !important; font-weight: 900 !important; }
    button[kind="secondary"], div.stDownloadButton > button { background-color: rgba(255,255,255,0.05) !important; border: 1px solid rgba(255,255,255,0.2) !important; color: #FFFFFF !important; }
    button[kind="secondary"]:hover, div.stDownloadButton > button:hover { background-color: rgba(255,255,255,0.15) !important; border-color: #FFFFFF !important; }

    /* ★ 삭제 버튼 빨간색 강제 지정 (CSS Trick) */
    div[data-testid="element-container"]:has(.delete-btn-wrapper) { display: none !important; }
    div[data-testid="element-container"]:has(.delete-btn-wrapper) + div[data-testid="element-container"] button {
        background-color: rgba(255, 75, 75, 0.1) !important; border-color: #FF4B4B !important; color: #FF4B4B !important;
    }
    div[data-testid="element-container"]:has(.delete-btn-wrapper) + div[data-testid="element-container"] button:hover {
        background-color: #FF4B4B !important; color: #FFFFFF !important;
    }
    div[data-testid="element-container"]:has(.delete-btn-wrapper) + div[data-testid="element-container"] button p {
        color: inherit !important;
    }

    /* 7. 수정 버튼: 투명 연필 아이콘 (행 번호 표시) */
    button[kind="tertiary"] {
        background-color: transparent !important; border: none !important; padding: 0 !important; margin: 0 !important;
        min-height: 0 !important; min-width: 40px !important; box-shadow: none !important;
        display: flex !important; align-items: center !important; justify-content: center !important;
    }
    button[kind="tertiary"] p { font-size: 1.1rem !important; color: rgba(255,215,0,0.7) !important; font-weight: bold !important; margin: 0 !important; padding: 0 !important; transition: transform 0.2s ease !important; }
    button[kind="tertiary"]:hover p { transform: scale(1.1) !important; color: #FFD700 !important; }

    /* 8. 텍스트 스타일 */
    .header-label { font-size: clamp(1.0rem, 1.4vw, 1.5rem) !important; font-weight: 800 !important; color: #FFFFFF !important; white-space: nowrap !important; text-transform: uppercase; letter-spacing: 1px; }
    .word-text { font-size: 1.98em; font-weight: bold; color: #FFD700 !important; word-break: keep-all; display: inline-block !important; margin-bottom: 0px !important; margin-top: -2px !important; transition: transform 0.2s ease !important; transform-origin: left center !important; }
    .mean-text { font-size: 1.3em; word-break: keep-all; display: inline-block !important; margin-bottom: 0px !important; color: #E0E0E0 !important; }
    .cat-text-bold { font-weight: bold !important; font-size: 0.95rem; color: #A3B8B8 !important; display: inline-block !important; margin-bottom: 0px !important; }
    div[data-testid="stHorizontalBlock"]:has(.row-marker):hover .word-text { transform: scale(1.05) !important; z-index: 10 !important; }

    /* 9. Num.ENG 결과물 */
    div[data-testid="stHorizontalBlock"]:has(.num-result) { display: flex !important; flex-direction: row !important; align-items: center !important; justify-content: flex-start !important; gap: 12px !important; width: 100% !important; margin-top: 10px; background: rgba(0,0,0,0.2); padding: 10px 15px; border-radius: 10px; border-left: 4px solid #FFD700; }
    div[data-testid="stHorizontalBlock"]:has(.num-result) > div { width: fit-content !important; flex: 0 1 auto !important; min-width: unset !important; }
    .num-result { color: #FFD700 !important; font-weight: bold; font-size: clamp(1.4rem, 1.8vw, 2.0rem) !important; margin: 0 !important; line-height: 1.1; white-space: normal !important; word-break: break-word; }
    div[data-testid="stHorizontalBlock"]:has(.num-result) button { background: transparent !important; border: none !important; box-shadow: none !important; padding: 0 !important; margin: 0 !important; margin-top: 2px !important; }

    /* ★ 링크 모음 전용 아이템 스타일 */
    .link-table-cat1 { font-size: 1.8rem !important; color: #FFD700 !important; font-weight: bold; display: inline-block; margin-bottom: 0px; }
    .link-table-cat2 { font-size: 1.2rem !important; color: #FFA500 !important; font-weight: bold; display: inline-block; margin-bottom: 0px; }
    a.link-table-title { font-size: 2.0em !important; font-weight: bold; color: #FFFFFF !important; text-decoration: none !important; border-bottom: none !important; background-image: none !important; display: inline-block; margin-bottom: 0px; transition: opacity 0.2s; }
    a.link-table-title:hover { opacity: 0.8; color: #FFD700 !important; text-decoration: none !important; border-bottom: none !important; }
    span.link-table-url, span.link-table-url a { cursor: pointer; font-size: 0.85rem; color: #9ACD32 !important; text-decoration: none !important; border-bottom: none !important; background-image: none !important; display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 100%; transition: all 0.2s; }
    span.link-table-url:hover, span.link-table-url a:hover { opacity: 0.8; color: #FFD700 !important; }
    div[data-testid="stMarkdownContainer"] a, div[data-testid="stMarkdownContainer"] a:hover { border-bottom: 0px !important; text-decoration: none !important; background-image: none !important; }
    .link-table-memo { font-size: 1.3em !important; color: rgba(255,255,255,0.9); word-break: keep-all; margin-bottom: 0px; }

    @media screen and (max-width: 768px) {
        .word-text { font-size: 1.3rem !important; }
        .mean-text { font-size: 1.0rem !important; }
        div[data-testid="stRadio"] label p { font-size: 1.1rem !important; }
        .link-table-cat1 { font-size: 1.4rem !important; }
        a.link-table-title { font-size: 1.5rem !important; }
        .link-table-memo { font-size: 1.1rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# [심플모드 CSS]
if st.session_state.is_simple:
    st.markdown("""
        <style>
        @media screen and (max-width: 768px) {
            .word-text { font-size: 1.7rem !important; line-height: 1.3 !important; }
            .mean-text { font-size: 1.26rem !important; line-height: 1.3 !important; }
        }
        </style>
    """, unsafe_allow_html=True)


# --- [다이얼로그 설정 (영어 단어장)] ---
@st.dialog("✨ 새 항목 추가")
def add_dialog(unique_cats):
    with st.form("add_form", clear_on_submit=True):
        st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; color: #FFD700;'>1. 저장할 시트</p>", unsafe_allow_html=True)
        target_sheet_name = st.radio("저장할 시트", ["메인", "해석", "단어", "구동사", "TOM-영어", "동사구", "문법", "여행"], horizontal=True, label_visibility="collapsed")
        
        st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: #FFD700;'>2. 카테고리 분류</p>", unsafe_allow_html=True)
        selected_cat = st.selectbox("기존 분류 선택", ["(새로 입력)"] + unique_cats)
        new_cat = st.text_input("또는 새 분류 직접 입력", value="") 
        
        st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: #FFD700;'>3. 학습 데이터</p>", unsafe_allow_html=True)
        word_sent = st.text_area("단어-문장 (필수)", value="", height=80) 
        mean = st.text_area("해석", value="", height=80) 
        
        st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: #FFD700;'>4. 부가 정보 (선택)</p>", unsafe_allow_html=True)
        pron = st.text_input("발음", value="") 
        m1 = st.text_area("메모 1", value="", height=80) 
        m2 = st.text_area("메모 2", value="", height=80) 
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("💾 저장하기", use_container_width=True, type="primary"):
            final_cat = new_cat.strip() if new_cat.strip() else (selected_cat if selected_cat != "(새로 입력)" else "")
            if word_sent:
                wb = init_connection().open("English_Sentences")
                target_sheet = wb.worksheet(target_sheet_name)
                target_sheet.append_row([final_cat, word_sent, mean, pron, m1, m2])
                st.success("저장 완료!")
                time.sleep(1)
                st.cache_data.clear() # 강제 캐시 초기화 (데이터 갱신)
                st.rerun()
                
    if st.button("❌ 창 닫기 (취소)", use_container_width=True):
        st.rerun()

@st.dialog("✏️ 항목 수정 및 삭제")
def edit_dialog(row_idx, sheet_idx, row_data, unique_cats):
    del_key = f"confirm_del_{sheet_idx}_{row_idx}"
    if del_key not in st.session_state:
        st.session_state[del_key] = False

    if not st.session_state[del_key]:
        safe_cats = unique_cats if unique_cats else ["(없음)"]
        cat_val = row_data.get('분류', '')
        cat_index = safe_cats.index(cat_val) if cat_val in safe_cats else 0
        
        with st.form(f"edit_{sheet_idx}_{row_idx}"):
            st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; color: #FFD700;'>1. 카테고리 수정</p>", unsafe_allow_html=True)
            edit_cat = st.selectbox("기존 분류 선택", safe_cats, index=cat_index)
            new_cat = st.text_input("분류 직접 변경", value="")
            
            st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: #FFD700;'>2. 학습 데이터 수정</p>", unsafe_allow_html=True)
            word_sent = st.text_area("단어-문장", value=row_data.get('단어-문장', ''), height=80)
            mean = st.text_area("해석", value=row_data.get('해석', ''), height=80)
            
            st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: #FFD700;'>3. 부가 정보 수정</p>", unsafe_allow_html=True)
            pron = st.text_input("발음", value=row_data.get('발음', ''))
            m1 = st.text_area("메모 1", value=row_data.get('메모1', ''), height=80)
            m2 = st.text_area("메모 2", value=row_data.get('메모2', ''), height=80)
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("💾 수정한 내용 저장", use_container_width=True, type="primary"):
                final_cat = new_cat.strip() if new_cat.strip() else edit_cat
                wb = init_connection().open("English_Sentences")
                target_sheet = wb.worksheet(sheet_idx) if isinstance(sheet_idx, str) else wb.get_worksheet(sheet_idx)
                target_sheet.update(f"A{row_idx}:F{row_idx}", [[final_cat, word_sent, mean, pron, m1, m2]])
                st.cache_data.clear() # 강제 캐시 초기화
                st.rerun()

        st.markdown('<div class="delete-btn-wrapper"></div>', unsafe_allow_html=True)
        st.button("🗑️ 항목 삭제", use_container_width=True, on_click=set_state, args=(del_key, True))
        
        if st.button("❌ 창 닫기 (취소)", use_container_width=True):
            st.rerun()

    else:
        st.error("⚠️ 정말 이 항목을 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.")
        st.info(f"선택 항목: {row_data.get('단어-문장', '')}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="delete-btn-wrapper"></div>', unsafe_allow_html=True)
            if st.button("✅ 네, 완전히 삭제합니다", use_container_width=True):
                wb = init_connection().open("English_Sentences")
                target_sheet = wb.worksheet(sheet_idx) if isinstance(sheet_idx, str) else wb.get_worksheet(sheet_idx)
                target_sheet.delete_rows(row_idx)
                st.session_state[del_key] = False
                st.cache_data.clear() # 강제 캐시 초기화
                st.rerun()
        with c2:
            st.button("아니오 (수정창으로 돌아가기)", use_container_width=True, on_click=set_state, args=(del_key, False))

# --- [다이얼로그 설정 (링크 모음)] ---
@st.dialog("✨ 새 링크 추가")
def add_link_dialog(unique_cats1, unique_cats2):
    with st.form("add_link_form", clear_on_submit=True):
        st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; color: #FFD700;'>1. 카테고리 지정</p>", unsafe_allow_html=True)
        selected_cat1 = st.selectbox("기존 대분류", ["(새로 입력)"] + unique_cats1)
        new_cat1 = st.text_input("새 대분류 직접 입력", value="") 
        
        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        selected_cat2 = st.selectbox("기존 소분류", ["(새로 입력)"] + unique_cats2)
        new_cat2 = st.text_input("새 소분류 직접 입력", value="") 
        
        st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: #FFD700;'>2. 링크 정보</p>", unsafe_allow_html=True)
        title = st.text_input("제목 (필수)", value="") 
        link_url = st.text_input("링크 주소(URL) (필수)", value="") 
        memo = st.text_input("메모", value="") 
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("💾 저장하기", use_container_width=True, type="primary"):
            final_cat1 = new_cat1.strip() if new_cat1.strip() else (selected_cat1 if selected_cat1 != "(새로 입력)" else "")
            final_cat2 = new_cat2.strip() if new_cat2.strip() else (selected_cat2 if selected_cat2 != "(새로 입력)" else "")
            
            if title and link_url:
                sheet2 = get_links_sheet()
                sheet2.append_row([final_cat1, final_cat2, title, memo, link_url])
                st.success("새 링크 저장 완료!")
                time.sleep(1)
                st.cache_data.clear() # 강제 캐시 초기화
                st.rerun()
            else:
                st.error("제목과 링크 주소는 필수입니다.")
                
    if st.button("❌ 창 닫기 (취소)", use_container_width=True):
        st.rerun()

@st.dialog("✏️ 링크 수정 및 삭제")
def edit_link_dialog(row_idx, row_data, unique_cats1, unique_cats2):
    del_key = f"confirm_del_link_{row_idx}"
    if del_key not in st.session_state:
        st.session_state[del_key] = False

    if not st.session_state[del_key]:
        safe_cats1 = unique_cats1 if unique_cats1 else ["(없음)"]
        cat1_val = row_data.get('대분류', '')
        cat1_index = safe_cats1.index(cat1_val) if cat1_val in safe_cats1 else 0
        
        safe_cats2 = unique_cats2 if unique_cats2 else ["(없음)"]
        cat2_val = row_data.get('소분류', '')
        cat2_index = safe_cats2.index(cat2_val) if cat2_val in safe_cats2 else 0
        
        with st.form(f"edit_link_{row_idx}"):
            st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; color: #FFD700;'>1. 카테고리 수정</p>", unsafe_allow_html=True)
            edit_cat1 = st.selectbox("대분류", safe_cats1, index=cat1_index)
            new_cat1 = st.text_input("대분류 직접 수정", value="") 
            
            st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
            edit_cat2 = st.selectbox("소분류", safe_cats2, index=cat2_index)
            new_cat2 = st.text_input("소분류 직접 수정", value="") 
            
            st.markdown("<p style='font-size: 1.1rem; font-weight: bold; margin-top: 15px; margin-bottom: 5px; color: #FFD700;'>2. 링크 정보 수정</p>", unsafe_allow_html=True)
            title = st.text_input("제목", value=row_data.get('제목', ''))
            link_url = st.text_input("링크 주소(URL)", value=row_data.get('링크', ''))
            memo = st.text_input("메모", value=row_data.get('메모', ''))
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("💾 수정한 내용 저장", use_container_width=True, type="primary"):
                final_cat1 = new_cat1.strip() if new_cat1.strip() else edit_cat1
                final_cat2 = new_cat2.strip() if new_cat2.strip() else edit_cat2
                sheet2 = get_links_sheet()
                sheet2.update(f"A{row_idx}:E{row_idx}", [[final_cat1, final_cat2, title, memo, link_url]])
                st.cache_data.clear() # 강제 캐시 초기화
                st.rerun()

        st.markdown('<div class="delete-btn-wrapper"></div>', unsafe_allow_html=True)
        st.button("🗑️ 링크 삭제", use_container_width=True, on_click=set_state, args=(del_key, True))
        
        if st.button("❌ 창 닫기 (취소)", use_container_width=True):
            st.rerun()
            
    else:
        st.error("⚠️ 정말 이 링크를 삭제하시겠습니까?\n\n이 작업은 되돌릴 수 없습니다.")
        st.info(f"선택 링크: {row_data.get('제목', '')}")
        
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="delete-btn-wrapper"></div>', unsafe_allow_html=True)
            if st.button("✅ 네, 완전히 삭제합니다", use_container_width=True):
                sheet2 = get_links_sheet()
                sheet2.delete_rows(row_idx)
                st.session_state[del_key] = False
                st.cache_data.clear() # 강제 캐시 초기화
                st.rerun()
        with c2:
            st.button("아니오 (수정창으로 돌아가기)", use_container_width=True, on_click=set_state, args=(del_key, False))

# --- [비즈니스 로직 함수] ---
def format_num_input():
    cleaned = re.sub(r'[^0-9]', '', str(st.session_state.num_input))
    st.session_state.num_input = f"{int(cleaned):,}" if cleaned else ""

def clear_num_input():
    st.session_state.num_input = ""

def num_to_eng(num):
    if num == 0: return "zero"
    ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
    tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
    scales = ["", "thousand", "million", "billion", "trillion"]
    def _convert(n):
        if n < 20: return ones[n]
        if n < 100: return tens[n // 10] + ("-" + ones[n % 10] if n % 10 != 0 else "")
        if n < 1000: return ones[n // 100] + " hundred" + (" " + _convert(n % 100) if n % 100 != 0 else "")
        for i in range(1, len(scales)):
            if n < 1000 ** (i + 1): return _convert(n // (1000 ** i)) + " " + scales[i] + (" " + _convert(n % (1000 ** i)) if n % (1000 ** i) != 0 else "")
        return str(n)
    return _convert(num).strip()

# --- [메인 로직] ---

# 1. 로그인 화면
if not st.session_state.authenticated and st.session_state.logging_in:
    st.write("## 🔐 Security Login")
    with st.form("login_form", clear_on_submit=False):
        st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
        pwd = st.text_input("Enter Password", type="password")
        submit = st.form_submit_button("✅ LOGIN", use_container_width=True, type="primary")
        if submit:
            if pwd == LOGIN_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.logging_in = False
                st.query_params["auth"] = "true"
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
    if st.button("🔙 CANCEL", use_container_width=True):
        st.session_state.logging_in = False
        st.rerun()
else:
    # ==========================================
    # 🌟 메인 앱 상단 UI 
    # ==========================================
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    date_str = now_kst.strftime("%A, %B %d, %Y")
    
    # [Row 1] 타이틀 및 우측 날짜 영역
    h_col1, h_col2 = st.columns([6, 4], vertical_alignment="bottom")
    with h_col1:
        st.markdown("<h1 style='color:#FFD700; font-size: clamp(2.2rem, 3.5vw, 3.5rem); line-height: 1.1; margin:0; padding:0; letter-spacing:-0.5px;'>TOmBOy94 <span style='font-size:0.7em; color:#FFFFFF;'>ENG+LINK</span></h1>", unsafe_allow_html=True)
    with h_col2:
        components.html(f"""
            <style>
                body {{ margin: 0; padding: 0; background-color: transparent !important; overflow: hidden; }}
                .date-wrapper {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: flex-end; gap: 10px; font-family: sans-serif; width: 100%; height: 100%; padding-bottom: 5px; }}
                .date-text {{ color: #A3B8B8; font-weight: bold; font-size: clamp(1.0rem, 1.8vw, 1.8rem); white-space: nowrap; margin-bottom: 2px; }}
                .copy-btn {{ background: linear-gradient(145deg, rgba(255,255,255,0.05), rgba(255,255,255,0.1)); border: 1px solid rgba(255,255,255,0.2); color: #FFF; padding: 6px 14px; border-radius: 8px; cursor: font-size: 0.9rem; font-weight:bold; transition: 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }}
                .copy-btn:hover {{ background: rgba(255,255,255,0.2) !important; transform: translateY(-2px); border-color: #FFD700; color: #FFD700; }}
            </style>
            <div class="date-wrapper">
                <span class="date-text">📅 {date_str}</span>
                <button class="copy-btn" onclick="copyDate()">📋 복사</button>
            </div>
            <script>
            function copyDate() {{
                var temp = document.createElement("textarea"); temp.value = "{date_str}"; document.body.appendChild(temp); temp.select(); document.execCommand("copy"); document.body.removeChild(temp);
                var btn = document.querySelector(".copy-btn"); btn.innerHTML = "✅ 완료"; btn.style.color = "#FFD700"; btn.style.borderColor = "#FFD700";
                setTimeout(function(){{ btn.innerHTML = "📋 복사"; btn.style.color = "#FFF"; btn.style.borderColor = "rgba(255,255,255,0.2)"; }}, 1500);
            }}
            </script>
        """, height=45)
        
    st.markdown("<hr style='border: 0; height: 1px; background-image: linear-gradient(to right, rgba(255, 255, 255, 0), rgba(255, 255, 255, 0.2), rgba(255, 255, 255, 0)); margin: 10px 0 20px 0;'/>", unsafe_allow_html=True)

    # [Row 2] 글로벌 네비게이션 컨트롤 패널
    n_col1, n_col2, n_col3, n_col4 = st.columns([2.5, 2.5, 4.0, 1.5], vertical_alignment="center")
    
    with n_col1:
        if st.session_state.app_mode == 'English':
            if st.button("🔗 링크 모음으로 전환", use_container_width=True, type="secondary"):
                st.session_state.app_mode = 'Links'
                st.rerun()
        else:
            if st.button("영어 모음으로 전환", use_container_width=True, type="secondary"):
                st.session_state.app_mode = 'English'
                st.rerun()
                
    with n_col2:
        if st.session_state.app_mode == 'English':
            study_url = "/?study=true&cat=ALL"
            st.markdown(f"""
                <a href="{study_url}" class="study-popup-link" style="
                    display: flex; align-items: center; justify-content: center;
                    width: 100%; padding: 0.6rem 1.2rem;
                    background: linear-gradient(135deg, #E67E22, #D35400); color: #FFFFFF;
                    border-radius: 12px; text-decoration: none;
                    font-weight: 900; font-size: clamp(0.85rem, 1.1vw, 1.15rem);
                    transition: all 0.3s ease; box-shadow: 0 4px 10px rgba(230,126,34,0.4);
                ">📚 몰입형 학습 시작</a>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='height:1px;'></div>", unsafe_allow_html=True)
            
    with n_col3:
        st.text_input("🔢 Num.ENG 변환기", key="num_input", on_change=format_num_input, label_visibility="collapsed", placeholder="숫자를 입력하면 영어로 변환됩니다...")

    with n_col4:
        if not st.session_state.authenticated:
            if st.button("🔐 LOGIN", use_container_width=True, type="primary"):
                st.session_state.logging_in = True
                st.rerun()
        else:
            if st.button("🔓 LOGOUT", use_container_width=True):
                st.session_state.authenticated = False
                st.session_state.app_mode = 'English'
                if "auth" in st.query_params: del st.query_params["auth"]
                st.rerun()

    # Num.ENG 결과값 출력
    if st.session_state.num_input:
        clean_num = st.session_state.num_input.replace(",", "").strip()
        if clean_num.isdigit():
            eng_text = num_to_eng(int(clean_num)).capitalize()
            res_col1, res_col2 = st.columns([1, 1], vertical_alignment="center")
            with res_col1:
                st.markdown(f"<div class='num-result'>{eng_text}</div>", unsafe_allow_html=True)
            with res_col2:
                st.button("❌", key="btn_clear_res_inline", on_click=clear_num_input)
        else:
            st.markdown("<div class='num-result' style='border-left-color:#FF4B4B;'><span style='color:#FF4B4B!important; font-size:1.2rem!important;'>⚠️ 숫자만 입력 가능합니다.</span></div>", unsafe_allow_html=True)

    # 상단 메뉴 구성용 JS 트릭 로드 (공통)
    components.html("""
        <script>
        const doc = window.parent.document;
        if (doc.copyLinkHandler) { doc.removeEventListener('click', doc.copyLinkHandler, true); }
        doc.copyLinkHandler = function(e) {
            let target = e.target.closest('.copyable-link');
            if (target) {
                e.preventDefault(); e.stopPropagation();
                let url = target.getAttribute('data-url');
                if (url) {
                    let temp = doc.createElement("textarea"); temp.value = url; temp.style.position = "fixed"; temp.style.opacity = "0"; doc.body.appendChild(temp); temp.select();
                    try { doc.execCommand("copy"); } catch(err) {} doc.body.removeChild(temp);
                    let originalText = target.innerHTML; target.innerHTML = "✅ 복사완료!"; target.style.color = "#FFD700";
                    setTimeout(function(){ target.innerHTML = originalText; target.style.color = ""; }, 1500);
                }
            }
        };
        doc.addEventListener('click', doc.copyLinkHandler, true);

        if (doc.studyPopupHandler) { doc.removeEventListener('click', doc.studyPopupHandler, true); }
        doc.studyPopupHandler = function(e) {
            let target = e.target.closest('.study-popup-link');
            if (target) {
                e.preventDefault(); e.stopPropagation();
                let url = target.getAttribute('href');
                window.parent.open(url, 'StudyWindow', 'location=no,toolbar=no,menubar=no,scrollbars=no,status=no,resizable=yes,width=' + screen.availWidth + ',height=' + screen.availHeight);
            }
        };
        doc.addEventListener('click', doc.studyPopupHandler, true);
        
        if (doc.preventDialogCloseHandler) { doc.removeEventListener('mousedown', doc.preventDialogCloseHandler, true); doc.removeEventListener('click', doc.preventDialogCloseHandler, true); }
        doc.preventDialogCloseHandler = function(e) {
            let isDialogBg = false;
            let stDialog = e.target.closest('div[data-testid="stDialog"]');
            if (stDialog && !e.target.closest('div[role="dialog"]')) { isDialogBg = true; }
            let baseWebModal = e.target.closest('div[data-baseweb="modal"]');
            if (baseWebModal && !e.target.closest('div[role="dialog"]') && !e.target.closest('section[role="dialog"]')) { isDialogBg = true; }
            if (isDialogBg) { e.stopPropagation(); e.preventDefault(); }
        };
        doc.addEventListener('mousedown', doc.preventDialogCloseHandler, true); doc.addEventListener('click', doc.preventDialogCloseHandler, true);

        if (doc.liveCommaHandler) { doc.removeEventListener('input', doc.liveCommaHandler, true); }
        doc.liveCommaHandler = function(e) {
            if (e.target && e.target.tagName === 'INPUT') {
                let label = e.target.getAttribute('aria-label');
                if (label && label.includes('Num.ENG')) {
                    let val = e.target.value; let numStr = val.replace(/[^0-9]/g, '');
                    let formatted = numStr ? Number(numStr).toLocaleString('en-US') : '';
                    if (val !== formatted) {
                        let nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
                        nativeSetter.call(e.target, formatted); e.target.dispatchEvent(new Event('input', { bubbles: true }));
                    }
                }
            }
        };
        doc.addEventListener('input', doc.liveCommaHandler, true);
        </script>
    """, height=0)


    # ==============================================================
    # 🇬🇧 영어 단어장 모드 컨텐츠
    # ==============================================================
    if st.session_state.app_mode == 'English':
        try:
            df = get_english_data_v2() # ★ 변경된 캐시 함수 연동 (강제 갱신)

            # 카테고리
            unique_cats = sorted([x for x in df['분류'].unique().tolist() if x != ''])
            sel_cat = st.radio("카테고리 선택", ["🔀 랜덤 10", "전체 분류"] + unique_cats, horizontal=True, label_visibility="collapsed", key="cat_radio", on_change=clear_search)
            
            # ★ 데이터 필터링 로직을 다운로드 버튼 위로 이동하여 현재 화면과 동일한 데이터 추출
            is_simple = st.session_state.is_simple
            search = st.session_state.active_search
            d_df = df.copy()
            if search: 
                d_df = d_df[d_df['단어-문장'].str.contains(search, case=False, na=False) | d_df['해석'].str.contains(search, case=False, na=False) | d_df['분류'].str.contains(search, case=False, na=False)]
            else:
                if sel_cat == "🔀 랜덤 10":
                    if st.session_state.current_cat != "🔀 랜덤 10" or 'random_df' not in st.session_state:
                        st.session_state.random_df = df.sample(n=min(10, len(df)))
                    d_df = st.session_state.random_df.copy()
                elif sel_cat != "전체 분류": 
                    d_df = d_df[d_df['분류'] == sel_cat]
                st.session_state.current_cat = sel_cat

            # ★ 정렬 로직 (모든 시트를 행 번호 오름차순으로 통일, 대소문자 구분 없이 정렬)
            if st.session_state.sort_order == 'asc': 
                d_df = d_df.sort_values(by='단어-문장', ascending=True, key=lambda col: col.str.lower())
            elif st.session_state.sort_order == 'desc': 
                d_df = d_df.sort_values(by='단어-문장', ascending=False, key=lambda col: col.str.lower())
            else: 
                if sel_cat != "🔀 랜덤 10":
                    d_df = d_df.sort_values(by='row_idx', ascending=True)

            # 액션 툴바
            st.markdown("<div style='background-color: rgba(0,0,0,0.25); padding: 15px 20px; border-radius: 15px; margin: 20px 0; border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            cb_cols = [3, 2, 1.5, 1.5] if st.session_state.authenticated else [4, 2, 2]
            cb = st.columns(cb_cols, vertical_alignment="center")
            
            cb[0].text_input("🔍 목록 내 검색", key="search_input", on_change=handle_search, label_visibility="collapsed")
            
            if st.session_state.authenticated:
                if cb[1].button("➕ 새 항목 추가", type="primary", use_container_width=True): add_dialog(unique_cats)
                
            btn_idx = 2 if st.session_state.authenticated else 1
            btn_text = "🔄 전체 정보 보기" if st.session_state.is_simple else "✨ 핵심만 보기"
            if cb[btn_idx].button(btn_text, type="primary" if not st.session_state.is_simple else "secondary", use_container_width=True):
                st.session_state.is_simple = not st.session_state.is_simple; st.rerun()

            if st.session_state.authenticated:
                # ★ 다운로드 버튼에 필터링 및 정렬이 완료된 d_df 전달
                cb[3].download_button("📥 CSV 추출", data=convert_df_to_csv(d_df), file_name=f"English_Data_{time.strftime('%Y%m%d')}.csv", use_container_width=True)
            else:
                cb[2].download_button("📥 CSV 추출", data=convert_df_to_csv(d_df), file_name=f"English_Data_{time.strftime('%Y%m%d')}.csv", use_container_width=True)
            
            st.markdown("</div>", unsafe_allow_html=True)

            total = len(d_df); pages = math.ceil(total/30) if total > 0 else 1
            curr_p = st.session_state.curr_p
            
            st.markdown(f"<div style='display:flex; justify-content:flex-end; padding-right:10px;'><span style='color:#A3B8B8; font-weight:bold; font-size:1.0rem;'>{('🔍 검색: ' + search + ' | ') if search else ''}총 {total}개 (Page {curr_p}/{pages})</span></div>", unsafe_allow_html=True)
            
            ratio = [1.5, 6, 4.5, 1.2] if is_simple else [1.2, 4, 2.5, 2, 2.5, 2.5, 1.2]
            labels = ["분류", "단어-문장", "해석", "수정"] if is_simple else ["분류", "단어-문장", "해석", "발음", "메모1", "메모2", "수정"]
            h_cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1], vertical_alignment="center")
            for i, l in enumerate(labels if st.session_state.authenticated else labels[:-1]):
                if l == "단어-문장":
                    sort_icon = " ↑" if st.session_state.sort_order == 'asc' else (" ↓" if st.session_state.sort_order == 'desc' else "")
                    if h_cols[i].button(f"{l}{sort_icon}", key="sort_btn"):
                        st.session_state.sort_order = 'asc' if st.session_state.sort_order == 'None' else ('desc' if st.session_state.sort_order == 'asc' else 'None')
                        st.rerun()
                else: h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
            
            st.markdown("<div style='border-bottom:2px solid rgba(255,255,255,0.2); margin-top:-15px; margin-bottom:10px;'></div>", unsafe_allow_html=True)

            for idx, row in d_df.iloc[(curr_p-1)*30 : curr_p*30].iterrows():
                cols = st.columns(ratio if st.session_state.authenticated else ratio[:-1], vertical_alignment="center")
                cols[0].markdown(f"<span class='row-marker'></span><span class='cat-text-bold'>{row['분류']}</span>", unsafe_allow_html=True)
                cols[1].markdown(f"<span class='word-text'>{row['단어-문장']}</span>", unsafe_allow_html=True)
                cols[2].markdown(f"<span class='mean-text'>{row['해석']}</span>", unsafe_allow_html=True)
                
                btn_label = f"✏️ {row.get('row_idx', '')}"
                
                if not is_simple:
                    cols[3].write(row['발음']); cols[4].write(row['메모1']); cols[5].write(row['메모2'])
                    if st.session_state.authenticated and cols[6].button(btn_label, key=f"e_{row['sheet_idx']}_{row['row_idx']}", type="tertiary"): 
                        edit_dialog(row['row_idx'], row['sheet_idx'], row.to_dict(), unique_cats)
                elif st.session_state.authenticated and cols[3].button(btn_label, key=f"es_{row['sheet_idx']}_{row['row_idx']}", type="tertiary"): 
                    edit_dialog(row['row_idx'], row['sheet_idx'], row.to_dict(), unique_cats)

        except Exception as e: st.error(f"오류 발생: {e}")

    # ==============================================================
    # 🔗 링크 모음 모드 컨텐츠 (시트2 연동)
    # ==============================================================
    elif st.session_state.app_mode == 'Links':
        try:
            df_links_raw = get_links_data_v2() # ★ 변경된 캐시 함수 연동
            
            unique_links_cats1 = sorted([x for x in df_links_raw['대분류'].unique().tolist() if x != ''])
            unique_links_cats2 = sorted([x for x in df_links_raw['소분류'].unique().tolist() if x != ''])
            
            # 대분류
            sel_link_cat1 = st.radio("대분류 필터", ["전체 링크", "✨ 최근 5개"] + unique_links_cats1, horizontal=True, label_visibility="collapsed")
            
            # 소분류
            sel_link_cat2 = "전체"
            if sel_link_cat1 not in ["전체 링크", "✨ 최근 5개"]:
                subset_cat2 = sorted([x for x in df_links_raw[df_links_raw['대분류'] == sel_link_cat1]['소분류'].unique().tolist() if x != ''])
                if subset_cat2:
                    display_cat2 = ["전체"] + subset_cat2
                    st.markdown("<div style='margin-top:-15px;'></div>", unsafe_allow_html=True)
                    sel_link_cat2 = st.radio("소분류 필터", display_cat2, horizontal=True, label_visibility="collapsed", key="cat2_radio")

            # ★ 데이터 필터링 로직을 다운로드 버튼 위로 이동하여 현재 화면과 동일한 데이터 추출
            search = st.session_state.active_search
            filtered_df_links = df_links_raw.copy()
            if search:
                filtered_df_links = filtered_df_links[filtered_df_links['제목'].str.contains(search, case=False, na=False) | filtered_df_links['메모'].str.contains(search, case=False, na=False) | filtered_df_links['링크'].str.contains(search, case=False, na=False)]
            else:
                if sel_link_cat1 == "✨ 최근 5개":
                    filtered_df_links = filtered_df_links.tail(5) # 마지막 5개를 시트 순서대로 추출
                elif sel_link_cat1 != "전체 링크":
                    filtered_df_links = filtered_df_links[filtered_df_links['대분류'] == sel_link_cat1]
                    if sel_link_cat2 != "전체":
                        filtered_df_links = filtered_df_links[filtered_df_links['소분류'] == sel_link_cat2]

            # 액션 툴바
            st.markdown("<div style='background-color: rgba(0,0,0,0.25); padding: 15px 20px; border-radius: 15px; margin: 20px 0; border: 1px solid rgba(255,255,255,0.05);'>", unsafe_allow_html=True)
            cb_cols = [3, 2, 1.5] if st.session_state.authenticated else [4, 2]
            cb = st.columns(cb_cols, vertical_alignment="center")
            
            cb[0].text_input("🔍 링크 검색", key="search_input", on_change=handle_search, label_visibility="collapsed")
            
            if st.session_state.authenticated:
                if cb[1].button("➕ 새 링크 추가", type="primary", use_container_width=True):
                    add_link_dialog(unique_links_cats1, unique_links_cats2)
                # ★ 다운로드 버튼에 필터링된 filtered_df_links 전달
                cb[2].download_button("📥 CSV 추출", data=convert_df_to_csv(filtered_df_links), file_name=f"Links_{time.strftime('%Y%m%d')}.csv", use_container_width=True)
            else:
                cb[1].download_button("📥 CSV 추출", data=convert_df_to_csv(filtered_df_links), file_name=f"Links_{time.strftime('%Y%m%d')}.csv", use_container_width=True)
                
            st.markdown("</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='display:flex; justify-content:flex-end; padding-right:10px;'><span style='color:#A3B8B8; font-weight:bold; font-size:1.0rem;'>{('🔍 검색: ' + search + ' | ') if search else ''}총 {len(filtered_df_links)}개 링크</span></div>", unsafe_allow_html=True)

            # --- 표 형식 헤더 ---
            l_ratio = [1.2, 1.2, 2.5, 2.0, 2.5, 1.2] if st.session_state.authenticated else [1.2, 1.2, 2.5, 2.0, 2.5]
            l_labels = ["대분류", "소분류", "제목", "메모", "링크", "수정"] if st.session_state.authenticated else ["대분류", "소분류", "제목", "메모", "링크"]
            
            h_cols = st.columns(l_ratio, vertical_alignment="center")
            for i, l in enumerate(l_labels):
                h_cols[i].markdown(f"<span class='header-label'>{l}</span>", unsafe_allow_html=True)
            
            st.markdown("<div style='border-bottom:2px solid rgba(255,255,255,0.2); margin-top:-15px; margin-bottom:10px;'></div>", unsafe_allow_html=True)

            # --- 표 내용 출력 ---
            if filtered_df_links.empty:
                st.info("등록된 링크가 없습니다.")
            else:
                for idx, row in filtered_df_links.iterrows():
                    cols = st.columns(l_ratio, vertical_alignment="center")
                    cols[0].markdown(f"<span class='row-marker'></span><span class='link-table-cat1'>{row['대분류']}</span>", unsafe_allow_html=True)
                    cols[1].markdown(f"<span class='link-table-cat2'>{row['소분류']}</span>", unsafe_allow_html=True)
                    
                    title_html = f"<a href='{row['링크']}' target='_blank' class='link-table-title'>{row['제목']}</a>"
                    cols[2].markdown(title_html, unsafe_allow_html=True)
                    cols[3].markdown(f"<span class='link-table-memo'>{row['메모']}</span>", unsafe_allow_html=True)
                    
                    safe_display_url = row['링크'].replace('http', 'http&#8203;').replace('www', 'www&#8203;')
                    link_html = f"<span class='link-table-url copyable-link' data-url='{row['링크']}' title='클릭하여 복사'>{safe_display_url}</span>"
                    cols[4].markdown(link_html, unsafe_allow_html=True)
                    
                    btn_label_link = f"✏️ {row.get('row_idx', '')}"
                    if st.session_state.authenticated:
                        if len(cols) > 5 and cols[5].button(btn_label_link, key=f"el_{row['row_idx']}", type="tertiary"):
                            edit_link_dialog(row['row_idx'], row.to_dict(), unique_links_cats1, unique_links_cats2)

        except Exception as e: st.error(f"링크 데이터 오류 발생: {e}")

    # --- 공통 푸터 (페이지 네비게이션 포함) ---
    # 영어 모드일 때만 공통 푸터 위에 페이지네이션 표시
    if st.session_state.app_mode == 'English' and 'pages' in locals() and pages > 1:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        
        start_p = max(1, st.session_state.curr_p - 4)
        end_p = min(pages, start_p + 9)
        if end_p - start_p < 9:
            start_p = max(1, end_p - 9)
        display_pages = list(range(start_p, end_p + 1))
        
        c_ratio = [2] + [1] * (len(display_pages) + 2) + [2]
        p_cols = st.columns(c_ratio, vertical_alignment="center")
        
        if p_cols[1].button("◀", key="prev_p", disabled=(st.session_state.curr_p == 1), use_container_width=True): 
            st.session_state.curr_p -= 1
            st.rerun()
            
        for idx, p in enumerate(display_pages):
            btn_type = "primary" if p == st.session_state.curr_p else "secondary"
            if p_cols[idx + 2].button(str(p), key=f"page_{p}", type=btn_type, use_container_width=True):
                st.session_state.curr_p = p
                st.rerun()
                
        if p_cols[-2].button("▶", key="next_p", disabled=(st.session_state.curr_p == pages), use_container_width=True): 
            st.session_state.curr_p += 1
            st.rerun()

    current_year = datetime.now(timezone(timedelta(hours=9))).year
    st.markdown(f"""
        <div style='text-align: center; margin-top: 40px; margin-bottom: 20px; padding-top: 20px; border-top: 1px dotted rgba(255, 255, 255, 0.1);'>
            <p style='color: rgba(255,255,255,0.3); font-size: 1.2rem; font-weight: bold; margin-bottom: 5px; letter-spacing: 1px;'>
                Copyright © {current_year} TOmBOy94 &nbsp;|&nbsp; lodus11st@naver.com &nbsp;|&nbsp; All rights reserved.
            </p>
        </div>
    """, unsafe_allow_html=True)
