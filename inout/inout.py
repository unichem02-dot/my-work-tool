import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re
import io

# --- [1. 페이지 기본 설정 및 테마 스타일] ---
st.set_page_config(layout="wide", page_title="입출력 관리 시스템 (inout)")

# 커스텀 CSS 주입
st.markdown("""
   <style>
   [data-testid="stAppViewContainer"] { background-color: #2b323c; }
   .main .block-container { padding-top: 1rem; max-width: 98%; }
   h1, h2, h3, p, span { color: #ffffff !important; }
   
   .search-panel-container { background-color: #353b48; padding: 15px; border-radius: 8px; border: 1px solid #4a5568; margin-bottom: 20px; }
   div.stButton > button { border-radius: 4px !important; font-weight: bold !important; padding: 0px 10px !important; }
   div.btn-green > div > button { background-color: #8bc34a !important; color: white !important; border: 1px solid #7cb342 !important; }
   div.btn-pink > div > button { background-color: #e57373 !important; color: white !important; border: 1px solid #e53935 !important; }

   /* 데이터 테이블 스타일 */
   .custom-table-container { width: 100%; margin-top: 5px; font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif; }
   .table-title-box { background-color: #2b323c; padding: 10px 15px; border-top: 2px solid #555; border-bottom: none; display: flex; align-items: center; justify-content: space-between; }
   .custom-table { width: 100%; border-collapse: collapse; font-size: 15px; background-color: white; }
   .custom-table th, .custom-table td { border: 1px solid #d0d0d0; padding: 8px 10px; }
   .custom-table th { text-align: center; color: white; font-weight: bold; padding: 10px 6px; }
   .custom-table tr:nth-child(even) { background-color: #f8f9fa; }
   .custom-table tr:hover { background-color: #e2e6ea; }
   
   .th-base { background-color: #353b48; color: white; }
   .th-in { background-color: #3b5b88; color: white; } 
   .th-out { background-color: #b8860b; color: white; }
   
   .txt-in-bold { color: #1e3a8a !important; font-weight: bold; }
   .txt-in { color: #1e3a8a !important; }
   .txt-out-bold { color: #9a3412 !important; font-weight: bold; }
   .txt-out { color: #9a3412 !important; }
   .txt-green { color: #059669 !important; font-weight: bold; }
   .txt-purple { color: #7e22ce !important; font-weight: bold; }
   .txt-gray { color: #475569 !important; }
   .txt-black { color: #1e293b !important; }
   .tc { text-align: center; } .tl { text-align: left; } .tr { text-align: right; }
   
   .sum-profit { background-color: #2b323c; color: white; padding: 12px 20px; text-align: right; font-weight: bold; font-size: 16px; border-top: 1px solid #444; }

   /* 결산 뷰 스타일 */
   .settle-header-top { background-color: #5d607e; color: white; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; font-weight: bold; border-bottom: 3px solid #b8b8b8; }
   .settle-container { display: flex; width: 100%; font-family: 'Malgun Gothic', sans-serif; font-size: 14px; color: #333; margin-top: 5px; }
   .settle-lists { display: flex; flex: 1; border: 1px solid #777; background: white; }
   .settle-col { flex: 1; border-right: 1px solid #ccc; background: white; }
   .settle-col:last-child { border-right: none; }
   .sh-title { text-align: center; color: white; padding: 8px; font-weight: bold; border-bottom: 1px solid #ccc; font-size: 14px;}
   .sh-1 { background-color: #8385b2; } .sh-2 { background-color: #7b9cbf; } .sh-3 { background-color: #c99f5e; } .sh-4 { background-color: #d1b15c; } .sh-5 { background-color: #8ba966; }
   .ul-list { list-style: none; padding: 0; margin: 0; }
   .ul-list li { padding: 6px 10px; border-bottom: 1px solid #eee; display: flex; align-items: flex-start; font-size: 14px;}
   .li-num { width: 25px; color: #555; } .li-name { flex: 1; word-break: break-all; } .li-icon { color: #a1a1aa; font-size: 16px; }
   
   .settle-summary { width: 350px; border: 1px solid #777; margin-left: 10px; background-color: #5d607e; color: white; display: flex; flex-direction: column;}
   .sum-subhead { background-color: #3b3d56; text-align: center; padding: 8px; font-size: 14px; font-weight: bold;}
   .sum-table { width: 100%; border-collapse: collapse; }
   .sum-table td { padding: 10px 12px; border-bottom: 1px solid #888; font-size: 14px; color: white; }
   .bg-blue { background-color: #707b9e; } .bg-orange { background-color: #c58f55; } .bg-olive { background-color: #757c43; } .bg-dark { background-color: #2b2b2b; }
   .tr-right { text-align: right; font-weight: bold;}
   
   .alert-box { background-color: white; color: black; margin: 10px; border: 1px solid #ccc; font-size: 13px; }
   .alert-title { background-color: #cc0000; color: white; text-align: center; padding: 6px; font-weight: bold; }
   .alert-ul { padding-left: 20px; margin: 10px 10px 10px 0; } .alert-ul li { margin-bottom: 5px; }
   </style>
   """, unsafe_allow_html=True)

# --- [2. 보안 및 세션/검색 상태 관리] ---
if "authenticated" not in st.session_state: st.session_state.authenticated = False
if "failed_attempts" not in st.session_state: st.session_state.failed_attempts = 0
if "lockout_until" not in st.session_state: st.session_state.lockout_until = None
if "last_activity" not in st.session_state: st.session_state.last_activity = None
if "search_params" not in st.session_state: st.session_state.search_params = {"mode": "init"}
if "sort_desc" not in st.session_state: st.session_state.sort_desc = True 
if "edit_id" not in st.session_state: st.session_state.edit_id = None
if "copy_id" not in st.session_state: st.session_state.copy_id = None # 💡 복사용 상태 추가
if "copy_id" not in st.session_state: st.session_state.copy_id = None

# 💡 URL 파라미터 감지 및 자동 로그인 처리 (복사기능 & 수정기능 둘 다 지원)
if "edit_id" in st.query_params or "copy_id" in st.query_params:
@@ -91,7 +91,7 @@
st.session_state.edit_id = st.query_params["edit_id"]
if "copy_id" in st.query_params:
st.session_state.copy_id = st.query_params["copy_id"]
        st.session_state.search_params = {"mode": "신규입력"} # 복사 클릭 시 자동으로 신규입력 모드로 전환
        st.session_state.search_params = {"mode": "신규입력"}

st.query_params.clear()
st.rerun()
@@ -374,7 +374,7 @@
elif btn_3: st.session_state.search_params = { "mode": "결산", "year": y_3, "month": m_3 }
elif btn_4: 
st.session_state.search_params = { "mode": "신규입력" }
                st.session_state.copy_id = None # 기본 신규입력은 빈칸으로 시작
                st.session_state.copy_id = None
elif btn_5: st.session_state.search_params = { "mode": "최근", "title": "최근입력순서", "type": "ALL", "company": "", "item": "", "limit": limit_val }
elif btn_6: st.session_state.search_params = { "mode": "일", "title": f"{d_day} 검색순서", "date": d_day, "type": "ALL", "company": "", "item": "", "limit": "ALL" }
elif btn_7: st.session_state.search_params = { "mode": "기간", "title": "어제/오늘/내일 검색순서", "type": "ALL", "company": "", "item": "", "limit": "ALL", "start": datetime.now().date() - timedelta(days=1), "end": datetime.now().date() + timedelta(days=1) }
@@ -386,7 +386,6 @@
if params["mode"] == "신규입력":
st.markdown("<h3 style='text-align:center; color:white; margin-top:20px; font-weight:bold;'>신규자료입력 | New</h3>", unsafe_allow_html=True)

                # 💡 복사 데이터가 있을 경우 기본값 변수에 담기
def_s_idx, def_incom, def_initem, def_inq, def_inprice, def_carno = 0, "", "", "", "", ""
def_outcom, def_outitem, def_outq, def_outprice, def_carprice = "", "", "", "", ""
def_date = datetime.now().date()
@@ -470,15 +469,15 @@
sheet.append_row(new_row)

st.cache_data.clear()
                            st.session_state.copy_id = None # 복사 상태 해제
                            st.session_state.copy_id = None
st.success("✅ 신규 자료가 구글 시트에 완벽하게 저장되었습니다!")
st.session_state.search_params = {"mode": "최근", "title": "최근입력순서", "type": "ALL", "company": "", "item": "", "limit": "20개"}
st.rerun()
except Exception as e:
st.error(f"⚠️ 저장 중 시스템 오류가 발생했습니다: {e}")

if canceled:
                        st.session_state.copy_id = None # 복사 상태 해제
                        st.session_state.copy_id = None
st.session_state.search_params = {"mode": "init"}
st.rerun()

@@ -587,28 +586,28 @@

row_id = safe_str(row.get("id"))

                    # 💡 [핵심] 날짜 링크 제거, Vat에 복사(copy_id) 링크 부여, NO에 수정/삭제(edit_id) 링크 부여
                    # 💡 [핵심 복구] Vat 링크(복사) 유지, NO 링크 해제, 날짜(dt_link)에 수정/삭제 기능 다시 부여 (밑줄 제거)
vat_link = f'<a href="?copy_id={row_id}&token={secret_token}" target="_self" style="text-decoration:none; cursor:pointer;" title="클릭하여 내용을 복사해 신규입력합니다."><span class="{s_cls}">{s_val}</span></a>'
                    no_link = f'<a href="?edit_id={row_id}&token={secret_token}" target="_self" style="color:#a1a1aa; text-decoration:underline; font-weight:bold; cursor:pointer;" title="클릭하여 데이터 수정/삭제">{row_id}</a>'
                    dt_link = f'<a href="?edit_id={row_id}&token={secret_token}" target="_self" style="color:#1e293b; text-decoration:none; cursor:pointer;" title="클릭하여 데이터 수정/삭제">{dt_str}</a>' if dt_str else ''

                    html_str += f'<tr><td class="tc">{vat_link}</td><td class="tc txt-black">{dt_str}</td><td class="tl txt-in-bold">{safe_str(row.get("incom"))}</td><td class="tl txt-in">{in_item_full}</td><td class="tr txt-in">{in_q_str}</td><td class="tr txt-in">{in_p_str}</td><td class="tl txt-out-bold">{safe_str(row.get("outcom"))}</td><td class="tl txt-out">{out_item_full}</td><td class="tr txt-out">{out_q_str}</td><td class="tr txt-out">{out_p_str}</td><td class="tc">{no_link}</td><td class="tc txt-gray">{safe_str(row.get("carno"))}</td><td class="tr txt-black">{car_p_str}</td></tr>'
                    html_str += f'<tr><td class="tc">{vat_link}</td><td class="tc">{dt_link}</td><td class="tl txt-in-bold">{safe_str(row.get("incom"))}</td><td class="tl txt-in">{in_item_full}</td><td class="tr txt-in">{in_q_str}</td><td class="tr txt-in">{in_p_str}</td><td class="tl txt-out-bold">{safe_str(row.get("outcom"))}</td><td class="tl txt-out">{out_item_full}</td><td class="tr txt-out">{out_q_str}</td><td class="tr txt-out">{out_p_str}</td><td class="tc txt-gray">{row_id}</td><td class="tc txt-gray">{safe_str(row.get("carno"))}</td><td class="tr txt-black">{car_p_str}</td></tr>'

html_str += '</tbody>'
html_str += '<tfoot><tr>'
html_str += f'<td colspan="2" class="th-base" style="text-align:left; font-weight:bold; padding:12px 15px; color:white;">자료수 : <span style="color:#ffeb3b;">{data_count}</span> 개</td>'
html_str += f'<td colspan="4" class="th-in" style="text-align:center; font-weight:bold; padding:12px 15px; color:white;">매입수량 : {total_in_q:,.0f} &nbsp;&nbsp;&nbsp;&nbsp; 매입금액 : {total_in_amt:,.0f}원</td>'
html_str += f'<td colspan="4" class="th-out" style="text-align:center; font-weight:bold; padding:12px 15px; color:white;">매출수량 : {total_out_q:,.0f} &nbsp;&nbsp;&nbsp;&nbsp; 매출금액 : {total_out_amt:,.0f}원</td>'
html_str += f'<td colspan="3" class="th-base" style="background-color:#5d607e; text-align:center; font-weight:bold; padding:12px 15px; color:white;">운송비 : {total_carprice:,.0f}원</td>'
html_str += f'</tr><tr><td colspan="13" class="sum-profit">검색내 총수익 &nbsp;&nbsp; {total_profit:,.0f}원</td></tr></tfoot></table></div>'

st.markdown(html_str, unsafe_allow_html=True)

else:
st.error("❌ 'date' 열을 찾을 수 없습니다.")

except Exception as e:
st.error(f"⚠️ 시스템 오류: {e}")

# --- [7. 하단 카피라이트] ---
st.markdown("<br><hr style='border: 0.5px solid #4a5568;'>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b !important;'>© 2026 UNICHEM02-DOT. ALL RIGHTS RESERVED.</p>", unsafe_allow_html=True)
