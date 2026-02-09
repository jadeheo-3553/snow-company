import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="우리 회사 거래처 지도", page_icon="🏢", layout="wide")

# 2. 구글 시트 연결 (ttl=0 추가하여 실시간 반영)
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

st.title("📂 거래처 관리 시스템")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # ttl=0 설정을 넣으면 시트 수정 시 앱에 더 빨리 반영됩니다.
    df = conn.read(spreadsheet=url, ttl=0)

    df = df.sort_values(by='거래처명').reset_index(drop=True)

    # 3. 사이드바 검색
    st.sidebar.header("🔍 검색창")
    search_query = st.sidebar.text_input("거래처명을 입력하세요", "")
    
    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False)]

    st.write(f"현재 등록된 거래처: **{len(df)}개**")
    st.markdown("---")

    # 4. 리스트 출력
    if len(df) == 0:
        st.warning("검색 결과가 없습니다.")
    else:
        cols = st.columns(2)
        for index, row in df.iterrows():
            with cols[index % 2]:
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1.5])
                    with c1:
                        img_url = row['이미지']
                        if pd.notna(img_url) and str(img_url).startswith('http'):
                            # [이미지 크기 통일] 높이를 200px로 고정하고 꽉 채우기
                            st.markdown(
                                f'<img src="{img_url}" style="width:100%; height:200px; object-fit:cover; border-radius:10px;">', 
                                unsafe_allow_html=True
                            )
                        else:
                            st.info("📷 사진 준비 중")
                    with c2:
                        st.subheader(row['거래처명'])
                        st.write(f"📍 **주소:** {row['주소']}")
                        
                        with st.expander("📝 상세 정보 보기"):
                            if '담당자' in df.columns and pd.notna(row['담당자']):
                                st.write(f"👤 **담당자:** {row['담당자']}")
                            if '비고' in df.columns and pd.notna(row['비고']):
                                st.write(f"ℹ️ **비고:** {row['비고']}")
                        
                        search_addr = str(row['주소'])
                        naver_map_url = f"https://map.naver.com/v5/search/{search_addr}"
                        st.link_button("🗺️ 네이버 지도 보기", naver_map_url)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")

st.sidebar.write("최종 업데이트: 2026-02-10")
