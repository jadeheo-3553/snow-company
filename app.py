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

# 2. 공간 최적화 CSS
st.markdown("""
    <style>
    .block-container { padding: 1rem !important; }
    .main-title { font-size: 1.3rem !important; font-weight: bold; text-align: center; margin-bottom: 10px; }
    
    /* 거래처명과 별표를 테이블 구조로 묶어 겹침 절대 방지 */
    .name-table { width: 100%; border-collapse: collapse; }
    .name-text { font-size: 1.05rem; font-weight: bold; text-align: left; }
    .star-btn { text-align: right; width: 40px; }
    
    /* 주소 및 카드 슬림화 */
    .addr-link { color: #007bff; text-decoration: none; font-size: 0.85rem; }
    .contact-item { background: #f9f9f9; padding: 8px; border-radius: 5px; border-left: 4px solid #ff4b4b; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()

    # 4. [신규] 심플 필터 영역 (공간 최소화)
    # 검색창과 가나다 선택기를 한 줄에 배치
    search_col, filter_col = st.columns([1, 1])
    with search_col:
        search_q = st.text_input("", placeholder="🔍 검색어 입력...", label_visibility="collapsed")
    with filter_col:
        chosung_options = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
        sel_chosung = st.select_slider("", options=chosung_options, label_visibility="collapsed")

    # 필터링 로직
    f_df = df.copy()
    if search_q:
        f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]
    if sel_chosung != "전체":
        if sel_chosung == "A-Z":
            f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
        else:
            f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == sel_chosung)]

    # 즐겨찾기 우선 정렬
    f_df['is_fav'] = f_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
    f_df = f_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

    # 5. 리스트 출력 (3열 그리드)
    rows = f_df.to_dict('records')
    for i in range(0, len(rows), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(rows):
                item = rows[i + j]
                with cols[j]:
                    with st.container(border=True):
                        name = item['거래처명']
                        is_fav = name in st.session_state.my_favs
                        
                        # [요청] 이름과 별표 줄바꿈/겹침 방지 (Columns 이용)
                        n_col, s_col = st.columns([0.8, 0.2])
                        n_col.markdown(f'<p class="name-text">{name}</p>', unsafe_allow_html=True)
                        if s_col.button("⭐" if is_fav else "☆", key=f"f_{name}_{i+j}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        # 네이버 지도 링크
                        addr = item['주소']
                        st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)

                        with st.expander("👤 담당자 및 메모"):
                            depts = str(item['부서명']).split('\n')
                            names = str(item['담당자']).split('\n')
                            phones = str(item['연락처']).split('\n')
                            
                            for k in range(max(len(depts), len(names), len(phones))):
                                d = depts[k].strip() if k < len(depts) else "-"
                                n = names[k].strip() if k < len(names) else "-"
                                p = phones[k].strip() if k < len(phones) else "-"
                                
                                st.markdown(f"""<div class="contact-item"><b>{k+1}. {d}</b><br>
                                👤 {n} | 📞 <a href="tel:{p}">{p}</a></div>""", unsafe_allow_html=True)
                                # [요청] 부서별 메모란
                                st.text_area(f"📝 {n} 메모", key=f"m_{name}_{k}", height=60)

except Exception as e:
    st.error(f"오류: {e}")
