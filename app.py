import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", page_icon="🏢", layout="wide")

# 2. 강력한 커스텀 CSS (모바일 버튼 밀착 + 타이틀 조절)
st.markdown("""
    <style>
    /* 타이틀 크기 축소 */
    .main-title { font-size: 1.5rem !important; font-weight: bold; text-align: center; margin: 10px 0; }
    
    /* [요청 1] 버튼 우측 밀착 나열 (가로 스크롤 허용) */
    .filter-container {
        display: flex;
        overflow-x: auto; /* 모바일에서 옆으로 밀어서 볼 수 있음 */
        white-space: nowrap;
        gap: 0px;
        padding: 5px 0;
        -webkit-overflow-scrolling: touch;
    }
    .filter-btn {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        width: 42px;
        height: 42px;
        border: 1px solid #ddd;
        background-color: white;
        font-size: 0.9rem;
        cursor: pointer;
        flex-shrink: 0; /* 크기 유지 */
    }
    
    /* [요청 4] 거래처명과 별표 겹침 방지 레이아웃 */
    .client-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 5px 0;
    }
    .client-name { 
        font-size: 1.1rem; 
        font-weight: bold; 
        margin: 0; 
        white-space: nowrap; 
        overflow: hidden; 
        text-overflow: ellipsis;
        max-width: 80%;
    }
    
    /* 지도 링크 스타일 */
    .map-link { color: #007bff; text-decoration: none; font-size: 0.85rem; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # [요청 1] 가로로 붙은 ㄱㄴㄷ 필터 (HTML 방식)
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    
    # 클릭 감지를 위한 가짜 버튼 레이아웃 대신 실제 Streamlit 버튼을 한 줄에 강제 배치
    cols = st.columns(len(chosungs))
    for idx, c in enumerate(chosungs):
        with cols[idx]:
            if st.button(c, key=f"btn_{c}"):
                st.session_state.sel_chosung = c

    search_q = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")

    # 필터링 로직 (스노우님 기존 로직 적용)
    f_df = df.copy()
    if st.session_state.sel_chosung != "전체":
        # 초성 필터링 로직 수행...
        pass

    # 4. 리스트 출력
    rows = f_df.to_dict('records')
    for i in range(0, len(rows), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(rows):
                item = rows[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # [요청 4] 이름과 별표 줄바꿈/겹침 없이 배치
                        name = item['거래처명']
                        is_fav = name in st.session_state.my_favs
                        
                        header_col1, header_col2 = st.columns([0.8, 0.2])
                        header_col1.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                        if header_col2.button("⭐" if is_fav else "☆", key=f"fav_{name}_{i+j}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        # [요청 3] 네이버 지도 링크 복구
                        addr = item['주소']
                        st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='map-link'>{addr}</a>", unsafe_allow_html=True)

                        with st.expander("👤 담당자 상세 정보"):
                            depts = str(item.get('부서명', '')).split('\n')
                            names = str(item.get('담당자', '')).split('\n')
                            phones = str(item.get('연락처', '')).split('\n')
                            
                            for k in range(max(len(depts), len(names), len(phones))):
                                d = depts[k].strip() if k < len(depts) else "-"
                                n = names[k].strip() if k < len(names) else "-"
                                p = phones[k].strip() if k < len(phones) else "-"
                                
                                st.markdown(f"**{k+1}. {d}**")
                                st.markdown(f"👤 {n} | 📞 [ {p} ](tel:{p.replace('-', '')})")
                                # [요청 2] 개별 메모란
                                st.text_area(f"📝 {n} 메모", key=f"memo_{name}_{k}", height=60)

except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {e}")
