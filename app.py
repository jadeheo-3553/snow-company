import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 설정 (한글 인식 및 페이지 레이아웃)
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

st.set_page_config(page_title="우리 회사 거래처 지도", page_icon="🏢", layout="wide")

# 2. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

st.title("📂 거래처 관리 시스템")

try:
    # 데이터 가져오기
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url)

    # [추가] 데이터 정렬: 거래처명 기준 가나다순
    df = df.sort_values(by='거래처명').reset_index(drop=True)

    # 3. 검색 및 필터링 기능
    st.sidebar.header("🔍 검색 및 필터")
    search_query = st.sidebar.text_input("거래처명을 입력하세요", "")
    
    # 검색어가 있을 경우 필터링
    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False)]

    st.write(f"현재 등록된 거래처: **{len(df)}개**")
    st.markdown("---")

    # 4. 거래처 목록 카드 출력
    if len(df) == 0:
        st.warning("검색 결과가 없습니다.")
    else:
        # 화면을 2열로 구성하여 더 많은 정보를 한눈에 보게 함
        cols = st.columns(2)
        for index, row in df.iterrows():
            with cols[index % 2]: # 좌우 번갈아가며 배치
                with st.container(border=True):
                    c1, c2 = st.columns([1, 1.5])
                    
                    with c1:
                        # 이미지 처리
                        img_url = row['이미지']
                        if pd.notna(img_url) and str(img_url).startswith('http'):
                            st.image(str(img_url), use_container_width=True)
                        else:
                            st.info("📷 사진 준비 중")
                            
                    with c2:
                        st.subheader(row['거래처명'])
                        st.write(f"📍 **주소:** {row['주소']}")
                        
                        # 전화번호가 시트에 있다면 전화걸기 버튼 추가 (시트에 '전화번호' 열이 있다고 가정)
                        if '전화번호' in df.columns and pd.notna(row['전화번호']):
                            tel = str(row['전화번호'])
                            st.link_button(f"📞 전화: {tel}", f"tel:{tel}")
                        
                        # 지도 버튼
                        search_addr = str(row['주소'])
                        naver_map_url = f"https://map.naver.com/v5/search/{search_addr}"
                        st.link_button("🗺️ 네이버 지도 보기", naver_map_url)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
    st.info("구글 시트의 열 이름이 '거래처명', '주소', '이미지'로 되어 있는지 확인해 주세요.")

st.sidebar.write("---")
st.sidebar.write("최종 업데이트: 2026-02-10")