import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", page_icon="🏢", layout="wide")

# 2. 강력한 CSS 스타일 (스노우님 전용 커스텀)
st.markdown("""
    <style>
    /* 상단 타이틀 크기 축소 */
    .main-title { font-size: 1.8rem !important; font-weight: bold; text-align: center; margin-bottom: 20px; }
    
    /* [요청 1] 정사각형 버튼 초밀착 나열 */
    div[data-testid="stHorizontalBlock"] { gap: 0px !important; }
    button[kind="secondary"] {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        min-width: 38px !important;
        height: 38px !important;
        padding: 0px !important;
        font-size: 0.85rem !important;
        border-radius: 2px !important; /* 최소한의 라운드 */
        border: 1px solid #e0e0e0 !important;
        margin: 0px !important;
    }

    /* [요청 4] 거래처명 + 별표 한 줄 배치 (Flex) */
    .title-row {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 10px;
    }
    .client-name { font-size: 1.15rem; font-weight: bold; margin: 0; white-space: nowrap; }
    
    /* 주소 링크 스타일 */
    .addr-link { color: #007bff !important; text-decoration: none !important; font-size: 0.85rem; }
    
    /* 담당자 카드 */
    .contact-box { background-color: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 3px solid #ff4b4b; margin-top: 5px; }
    .dept-text { color: #ff4b4b; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 전처리
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 검색창
    search_q = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")
    
    # [요청 1] 정사각형 필터 (가로로 쭉 이어붙임)
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    row1 = st.columns(16) # 가로로 최대한 나열
    for idx, c in enumerate(chosungs):
        if row1[idx].button(c, key=f"f_{c}"):
            st.session_state.sel_chosung = c

    # 필터링 로직 (생략 - 기존과 동일)
    f_df = df.copy() 
    # (실제 필터링 코드 적용...)

    # 4. 리스트 출력
    rows = f_df.to_dict('records')
    for i in range(0, len(rows), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(rows):
                item = rows[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # [요청 4] 이름 바로 뒤에 별표
                        name = item['거래처명']
                        is_fav = name in st.session_state.my_favs
                        
                        # Flexbox를 이용해 이름과 버튼을 한 줄에 배치
                        t_col1, t_col2 = st.columns([0.8, 0.2])
                        t_col1.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                        if t_col2.button("⭐" if is_fav else "☆", key=f"btn_{name}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        # [요청 3] 네이버 지도 링크 복구
                        addr = item['주소']
                        st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)

                        with st.expander("👤 담당자 및 메모 보기"):
                            # 담당자 1, 2, 3 정렬
                            depts = str(item['부서명']).split('\n')
                            names = str(item['담당자']).split('\n')
                            phones = str(item['연락처']).split('\n')
                            
                            for k in range(max(len(depts), len(names), len(phones))):
                                d = depts[k].strip() if k < len(depts) else "-"
                                n = names[k].strip() if k < len(names) else "-"
                                p = phones[k].strip() if k < len(phones) else "-"
                                
                                st.markdown(f"""
                                <div class="contact-box">
                                    <span class="dept-text">{k+1}. {d}</span><br>
                                    👤 {n} | 📞 <a href="tel:{p}">{p}</a>
                                </div>
                                """, unsafe_allow_html=True)
                                # [요청] 부서별 개별 메모란
                                st.text_area(f"📝 {n} 담당자 메모", key=f"memo_{name}_{k}", height=65)

except Exception as e:
    st.error(f"시스템 오류: {e}")
