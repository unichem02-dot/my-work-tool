import streamlit as st
import yt_dlp
import os
import subprocess
import math
import tempfile

# 웹 페이지 기본 설정 (제목, 아이콘, 레이아웃)
st.set_page_config(page_title="유튜브 MP3 추출기", page_icon="🎵", layout="centered")

def time_to_seconds(time_str):
    try:
        parts = time_str.split(':')
        if len(parts) == 3: return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2: return int(parts[0]) * 60 + int(parts[1])
        else: return int(parts[0])
    except:
        return -1

st.title("🎵 유튜브 구간 MP3 추출기")
st.markdown("**긴 영상도 초고속으로 오디오만 추출하고 원하는 단위로 자동 분할합니다.**")

st.divider()

# --- 입력 폼 구성 ---
url = st.text_input("유튜브 URL 입력:", placeholder="https://www.youtube.com/watch?v=...")

col1, col2 = st.columns(2)
with col1:
    start_time_str = st.text_input("시작 시간 (예: 00:00:00):", value="00:00:00")
with col2:
    duration_str = st.selectbox("다운로드 할 분량:", ["전체", "1시간", "50분", "30분"])

# 인증 방식 옵션에 'cookies.txt' 부활 및 파일 업로더 추가
browser_choice = st.selectbox("인증 방식 (403 에러 발생 시 cookies.txt 추천):", 
                              ["기본 (yt-dlp 자동 처리)", "cookies.txt (가장 확실함)", "모바일 앱 위장 (우회 추천)", "chrome", "edge"])

cookie_file_path = None
if browser_choice == "cookies.txt (가장 확실함)":
    uploaded_cookie = st.file_uploader("youtube.com_cookies.txt 파일을 여기에 업로드하세요:", type=["txt"])
    if uploaded_cookie is not None:
        # 업로드된 쿠키 파일을 임시 파일로 저장하여 yt-dlp가 읽을 수 있게 함
        with tempfile.NamedTemporaryFile(delete=False, suffix='.txt') as tmp:
            tmp.write(uploaded_cookie.getvalue())
            cookie_file_path = tmp.name

st.write("") # 간격 띄우기

# --- 다운로드 실행 버튼 ---
if st.button("MP3 다운로드 시작", type="primary", use_container_width=True):
    if not url:
        st.error("유튜브 URL을 입력하세요.")
    elif browser_choice == "cookies.txt (가장 확실함)" and not cookie_file_path:
        st.error("반드시 cookies.txt 파일을 업로드해야 합니다.")
    else:
        start_sec = time_to_seconds(start_time_str)
        if start_sec < 0:
            st.error("시작 시간을 올바른 형식으로 입력하세요.")
        else:
            # 상태 표시기 (진행 바 대체)
            with st.status("다운로드 및 변환 작업 중...", expanded=True) as status:
                try:
                    save_dir = r"H:\LODUS11ST-TOM-CLOUD\●PY\■shorts-MP3"
                    if not os.path.exists(save_dir):
                        os.makedirs(save_dir)

                    ydl_opts = {
                        'format': 'bestaudio[ext=m4a]/bestaudio/best',
                        'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '320'}],
                        'outtmpl': os.path.join(save_dir, '%(title)s_원본.%(ext)s'),
                        'nocheckcertificate': True, 
                    }

                    # 사용자가 선택한 인증 방식에 따라 옵션 분기
                    if browser_choice == "cookies.txt (가장 확실함)":
                        ydl_opts['cookiefile'] = cookie_file_path
                        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['web']}}
                    elif browser_choice == "모바일 앱 위장 (우회 추천)":
                        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['tv', 'mweb']}}
                    elif browser_choice in ["chrome", "edge"]:
                        ydl_opts['cookiesfrombrowser'] = (browser_choice, )
                        ydl_opts['extractor_args'] = {'youtube': {'player_client': ['web']}}
                    # "기본"인 경우 아무 옵션도 추가하지 않음

                    st.write("🏃‍♂️ 1단계: 전체 오디오 초고속 다운로드 중...")
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(url, download=True)
                        total_duration = info.get('duration', 0)
                        base_filename = ydl.prepare_filename(info)
                        mp3_filename = os.path.splitext(base_filename)[0] + '.mp3'
                        title_prefix = os.path.basename(mp3_filename).replace("_원본.mp3", "")

                    st.write("✂️ 2단계: 지정된 분량으로 파일 분할 중...")
                    interval_map = {"전체": -1, "1시간": 3600, "50분": 3000, "30분": 1800}
                    interval = interval_map[duration_str]

                    startupinfo = None
                    if os.name == 'nt':
                        startupinfo = subprocess.STARTUPINFO()
                        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                    if interval == -1:
                        final_name = os.path.join(save_dir, f"{title_prefix}_전체.mp3")
                        if start_sec > 0:
                            subprocess.run(['ffmpeg', '-y', '-i', mp3_filename, '-ss', str(start_sec), '-c', 'copy', final_name], startupinfo=startupinfo)
                            if os.path.exists(mp3_filename): os.remove(mp3_filename)
                        else:
                            if os.path.exists(final_name): os.remove(final_name)
                            os.rename(mp3_filename, final_name)
                    else:
                        duration_to_split = total_duration - start_sec
                        if duration_to_split <= 0: duration_to_split = interval
                        num_parts = math.ceil(duration_to_split / interval)

                        for i in range(num_parts):
                            part_start = start_sec + (i * interval)
                            part_end = part_start + interval
                            if total_duration > 0 and part_end > total_duration: part_end = total_duration
                            start_m = int(part_start // 60)
                            end_m = int(part_end // 60)
                            part_name = os.path.join(save_dir, f"{title_prefix}_{i+1}번째({start_m}분~{end_m}분).mp3")
                            
                            subprocess.run(['ffmpeg', '-y', '-i', mp3_filename, '-ss', str(part_start), '-to', str(part_end), '-c', 'copy', part_name], startupinfo=startupinfo)

                        if os.path.exists(mp3_filename): os.remove(mp3_filename)

                    status.update(label="작업 완료!", state="complete", expanded=False)
                    st.success(f"🎉 모든 작업이 성공적으로 완료되었습니다!\n\n📂 **저장 위치:** `{save_dir}`")
                
                except Exception as e:
                    error_msg = str(e)
                    status.update(label="오류 발생", state="error", expanded=True)
                    
                    if "reloaded" in error_msg.lower() or "403" in error_msg:
                        st.error(f"🚨 **유튜브 보안 차단 발생 (403 Forbidden)**\n\n에러 내용: {error_msg}\n\n**[해결 방법]**\n1. 인증 방식을 **'cookies.txt (가장 확실함)'**으로 선택하세요.\n2. 크롬 확장프로그램(Get cookies.txt LOCALLY)으로 받은 파일을 업로드 후 다시 시도해보세요.")
                    else:
                        st.error(f"다운로드 실패: {error_msg}")
                finally:
                    # 다 쓴 임시 쿠키 파일은 찌꺼기가 남지 않도록 깔끔하게 삭제
                    if cookie_file_path and os.path.exists(cookie_file_path):
                        os.remove(cookie_file_path)
