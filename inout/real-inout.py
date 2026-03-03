import sys
import time

def process_input():
    """
    사용자의 입력을 실시간으로 처리하는 메인 함수입니다.
    """
    print("========================================")
    print("   실시간 데이터 입출력 시스템 (Python)   ")
    print("========================================")
    print("안내: 'exit' 또는 '종료'를 입력하면 프로그램이 중단됩니다.\n")

    try:
        while True:
            # 사용자로부터 실시간 입력 받기
            user_input = input("입력값 기다리는 중... > ").strip()

            # 종료 조건 체크
            if user_input.lower() in ['exit', 'quit', '종료', 'q']:
                print("\n[시스템] 프로그램을 안전하게 종료합니다.")
                break

            if not user_input:
                continue

            # 데이터 처리 로직 (예시: 문자열 반전 및 대문자 변환)
            reversed_text = user_input[::-1]
            upper_text = user_input.upper()
            length = len(user_input)

            # 결과 출력
            print(f" -> [결과] 변환: {upper_text} | 역순: {reversed_text} | 길이: {length}")
            print("-" * 40)

            # CPU 부하 방지를 위한 미세한 대기
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n\n[알림] 사용자에 의해 강제 종료되었습니다 (Ctrl+C).")
    except Exception as e:
        print(f"\n[오류 발생] 상세 내용: {e}")

if __name__ == "__main__":
    process_input()
