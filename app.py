import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", page_icon="🏢", layout="wide")

# 초성 추출 함수
def get_chosung(text):
    if not text or pd.isna(text): return ""
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    char_code = ord(str(text)[0]) - 0xAC00
    if 0 <= char_code <= 11171:
        return CHOSUNG_LIST[char_code // 588]
    return str(text)[0].upper()

# 2. 공간 극소화 커스텀 스타일
st.markdown("""
    <style>
    /* 전체 여백 제거 */
    .block-container { padding: 0.5rem 1rem !important; }
    .main-title { font-size: 1.2rem !important; font-weight: bold; margin-bottom: 5px; text-align: center; }

    /* [요청] ㄱㄴㄷ 버튼 초슬림 타일 배치 */
    .chosung-container {
        display: flex;
        flex-wrap: wrap;
        gap: 0px; /* 간격 없음 */
        margin-bottom: 10px;
    }
    .stButton > button {
        width: 35px !important;
        height: 35px !important;
        min-width: 35px !important;
        padding: 0px !important;
        margin: 0px !important;
        border-radius: 0px !important;
        border: 0.1px solid #eee !important;
        font-size: 0.75rem !important;
        background-color: white !important;
    }

    /* 거래처명 + 별표 한 줄 배치 */
    .client-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 2px;
    }
    .client-name { font-size: 1rem !important; font-weight: bold; margin: 0; }
    
    /* 지도 링크 및 카드 최소화 */
    .addr-link { color: #007bff; text-decoration: none; font-size: 0.8rem; }
    .contact-card { background: #f9f9f9; padding: 5px; border-radius: 4px; border-left: 3px solid #ff4b4b; margin: 3px 0; font-size: 0.85rem; }
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

    # 4. 필터 영역 (공간 최소화)
    search_q = st.text_input("", placeholder="🔍 검색어 입력...", label_visibility="collapsed")
    
    # 초성 필터를 촘촘한 가로 배열로 배치
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    cols = st.columns(16) # 한 줄에 16개 배치하여 공간 극소화
    for idx, c in enumerate(chosungs):
        if cols[idx].button(c, key=f"c_{c}"):
            st.session_state.sel_chosung = c

    # 필터링 로직
    f_df = df.copy()
    if search_q:
        f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]
    if st.session_state.sel_chosung != "전체":
        if st.session_state.sel_chosung == "A-Z":
            f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
        else:
            f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == st.session_state.sel_chosung)]

    # 5. 거래처 리스트 (3열)
    rows = f_df.to_dict('records')
    for i in range(0, len(rows), 3):
        grid_cols = st.columns(3)
        for j in range(3):
            if i + j < len(rows):
                item = rows[i + j]
                with grid_cols[j]:
                    with st.container(border=True):
                        # [요청] 이름 옆 별표
                        name = item['거래처명']
                        is_fav = name in st.session_state.my_favs
                        
                        header_l, header_r = st.columns([0.8, 0.2])
                        header_l.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                        if header_r.button("⭐" if is_fav else "☆", key=f"f_{name}_{i+j}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        # 주소 & 네이버 지도
                        addr = item['주소']
                        st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)

                        with st.expander("👤 정보/메모"):
                            depts = str(item['부서명']).split('\n')
                            names = str(item['담당자']).split('\n')
                            phones = str(item['연락처']).split('\n')
                            
                            for k in range(max(len(depts), len(names), len(phones))):
                                d = depts[k].strip() if k < len(depts) else "-"
                                n = names[k].strip() if k < len(names) else "-"
                                p = phones[k].strip() if k < len(phones) else "-"
                                
                                st.markdown(f'<div class="contact-card"><b>{k+1}. {d}</b><br>👤 {n} | 📞 <a href="tel:{p}">{p}</a></div>', unsafe_allow_html=True)
                                # [요청] 부서별 메모란
                                st.text_area(f"📝 {n} 메모", key=f"m_{name}_{k}", height=60)

except Exception as e:
    st.error(f"오류: {e}")
