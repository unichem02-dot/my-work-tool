import streamlit as st
import yt_dlp
import os

# 페이지 설정
st.set_page_config(page_title="유튜브 고음질 MP3 다운로더", page_icon="🎵", layout="centered")

st.title("🎵 유튜브 고음질 MP3 다운로더")
st.markdown("유튜브 주소를 입력하면 **최고 음질(320kbps)의 MP3**로 변환하여 다운로드합니다. (6시간 이상 영상 지원)")

# URL 입력
url = st.text_input("유튜브 영상 주소를 입력하세요 (예: https://www.youtube.com/watch?v=...)")

# 상태 표시를 위한 공간
status_text = st.empty()

def download_mp3(video_url):
    """yt-dlp를 이용해 유튜브 오디오를 추출하고 mp3로 변환하는 함수"""
    
    # 다운로드 옵션 설정
    ydl_opts = {
        'format': 'bestaudio/best', # 최고 음질 오디오
        'outtmpl': '%(title)s.%(ext)s', # 파일명 설정
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '320', # 320kbps 고음질
        }],
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # 영상 정보 가져오기
            info_dict = ydl.extract_info(video_url, download=True)
            # 최종 생성된 파일명 (mp3)
            filename = ydl.prepare_filename(info_dict).rsplit('.', 1)[0] + '.mp3'
            return filename, info_dict.get('title', 'audio')
            
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
        return None, None

if st.button("MP3 변환 및 다운로드 준비", type="primary"):
    if not url:
        st.warning("유튜브 주소를 입력해주세요.")
    else:
        with st.spinner("서버에서 오디오를 추출하고 MP3로 변환 중입니다... (영상이 길면 수십 분이 걸릴 수 있습니다.)"):
            file_path, title = download_mp3(url)
            
            if file_path and os.path.exists(file_path):
                st.success(f"✅ 변환 완료! 아래 버튼을 눌러 '{title}'을(를) 다운로드하세요.")
                
                # 변환된 파일을 읽어서 다운로드 버튼 생성
                with open(file_path, "rb") as file:
                    btn = st.download_button(
                        label="⬇️ MP3 다운로드",
                        data=file,
                        file_name=f"{title}.mp3",
                        mime="audio/mpeg"
                    )
                
                # 주의: 실제 서비스에서는 메모리 관리 및 임시 파일 삭제 로직이 추가로 필요할 수 있습니다.