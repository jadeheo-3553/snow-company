import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 및 페이지 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리 시스템", page_icon="🏢", layout="wide")

# 2. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

# 상단 디자인: 제목을 작게 줄여 화면 공간 확보
st.subheader("🏬 거래처 통합 관리")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    df = df.sort_values(by='거래처명').reset_index(drop=True)

    # 3. 사이드바 검색 및 필터
    with st.sidebar:
        st.header("🔍 검색")
        search_query = st.text_input("거래처명 검색", placeholder="검색어 입력...")
        # [아이디어] 지역 필터 추가 (시트에 '지역' 열이 있다면 활성화)
        if '지역' in df.columns:
            region_list = ["전체"] + sorted(df['지역'].unique().tolist())
            selected_region = st.selectbox("지역 선택", region_list)
            if selected_region != "전체":
                df = df[df['지역'] == selected_region]

    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False)]

    # 4. 모바일 최적화 리스트 출력
    if len(df) == 0:
        st.warning("데이터가 없습니다.")
    else:
        # 상단 요약 (작게 표시)
        st.caption(f"총 {len(df)}개의 거래처가 검색되었습니다.")

        # 목록 표시
        for index, row in df.iterrows():
            with st.container(border=True):
                # 핸드폰에서는 사진과 글자를 가로로 배치 (열 비율 조정)
                c1, c2 = st.columns([1, 4]) 
                
                with c1:
                    # 사진을 작고 동그란 썸네일 형태로
                    img_url = row['이미지']
                    display_img = img_url if pd.notna(img_url) and str(img_url).startswith('http') else "https://via.placeholder.com/150/f0f2f6/666666?text=No"
                    st.markdown(
                        f'<img src="{display_img}" style="width:60px; height:60px; object-fit:cover; border-radius:50%;">', 
                        unsafe_allow_html=True
                    )
                
                with c2:
                    # 제목과 주소를 한 줄에 가깝게 배치
                    col_title, col_btn = st.columns([3, 1])
                    with col_title:
                        st.markdown(f"**{row['거래처명']}**")
                        st.caption(f"📍 {row['주소']}")
                    
                    with col_btn:
                        # 상세 정보는 펼쳐보기(Expander) 대신 버튼식으로도 가능하지만 유지
                        pass
                
                # 상세 정보 및 지도 버튼을 하단에 작게 배치
                exp = st.expander("정보 상세 / 지도")
                with exp:
                    detail_col1, detail_col2 = st.columns(2)
                    with detail_col1:
                        for col in ['담당자', '전화번호', '이메일', '비고']:
                            if col in df.columns and pd.notna(row[col]):
                                st.write(f"**{col}:** {row[col]}")
                    with detail_col2:
                        naver_url = f"https://map.naver.com/v5/search/{row['주소']}"
                        st.link_button("🗺️ 지도 열기", naver_url, use_container_width=True)
                        if '전화번호' in df.columns and pd.notna(row['전화번호']):
                            st.link_button("📞 전화 걸기", f"tel:{row['전화번호']}", use_container_width=True)

except Exception as e:
    st.error(f"오류: {e}")
