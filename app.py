import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys
import re

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리", page_icon="🏢", layout="wide")

# 초성 추출 함수
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text or pd.isna(text): return ""
    char_code = ord(str(text)[0]) - 0xAC00
    if 0 <= char_code <= 11171:
        return CHOSUNG_LIST[char_code // 588]
    return str(text)[0].upper()

# 2. 스타일 설정 (모바일 최적화 및 버튼 크기 조절)
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .stAppHeader {display:none;}
    .main-title { font-size: 1.6rem !important; font-weight: bold; text-align: center; margin-bottom: 5px; }
    
    /* 가나다 버튼 크기 축소 및 간격 조절 */
    div[data-testid="stHorizontalBlock"] { gap: 2px !important; }
    button[kind="secondary"] { 
        padding: 2px 0px !important; 
        font-size: 0.75rem !important; 
        min-height: 30px !important;
    }

    /* 거래처명 옆 별표 배치 */
    .title-wrapper { display: flex; align-items: center; justify-content: space-between; }
    .client-name { font-size: 1.05rem !important; font-weight: bold; margin: 0; }
    
    /* 팀명 빨간색 강조 */
    .team-name { color: #ff4b4b !important; font-weight: bold; font-size: 0.9rem; }
    
    .addr-link { color: #007bff; text-decoration: none; font-size: 0.85rem; }
    .contact-item { background-color: #f9f9f9; padding: 8px; border-radius: 8px; margin-bottom: 5px; border: 1px dotted #ccc; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    # 세션 상태 (개별용)
    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 사이드바 (모바일은 왼쪽 상단 '>' 버튼 클릭)
    with st.sidebar:
        st.header("📍 상세 필터")
        only_fav = st.toggle("⭐ 즐겨찾기만 보기")
        region_list = sorted(list(set(df['주소'].str.split().str[0])))
        sel_region = st.selectbox("🌍 지역 선택", ["전체"] + region_list)

    # 4. 검색창 및 가나다 필터 (2줄 배치)
    search_q = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")
    
    st.caption("📍 가나다 필터")
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
    
    # 첫 번째 줄 (8개)
    row1 = st.columns(8)
    for idx, c in enumerate(chosungs[:8]):
        if row1[idx].button(c, key=f"c_{c}", use_container_width=True):
            st.session_state.sel_chosung = c
    
    # 두 번째 줄 (7개)
    row2 = st.columns(7)
    for idx, c in enumerate(chosungs[8:]):
        if row2[idx].button(c, key=f"c_{c}", use_container_width=True):
            st.session_state.sel_chosung = c

    # 필터 로직
    f_df = df.copy()
    if search_q:
        f_df = f_df[f_df['거래처명'].str.contains(search_q) | f_df['주소'].str.contains(search_q)]
    if st.session_state.sel_chosung != "전체":
        f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == st.session_state.sel_chosung)]
    if sel_region != "전체":
        f_df = f_df[f_df['주소'].str.startswith(sel_region)]
    if only_fav:
        f_df = f_df[f_df['거래처명'].isin(st.session_state.my_favs)]

    # 즐겨찾기 우선 정렬
    f_df['is_fav'] = f_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
    f_df = f_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

    # 5. 리스트 출력 (3열 레이아웃)
    st.write(f"총 {len(f_df)}개의 거래처")
    for i in range(0, len(f_df), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(f_df):
                row = f_df.iloc[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # 이름과 별표 한 줄 배치
                        name = row['거래처명']
                        is_fav = name in st.session_state.my_favs
                        star_icon = "⭐" if is_fav else "☆"
                        
                        header_col1, header_col2 = st.columns([0.8, 0.2])
                        header_col1.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                        if header_col2.button(star_icon, key=f"btn_{name}_{i+j}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        # 네이버 지도 링크 주소
                        addr = row['주소']
                        st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)

                        with st.expander("👤 정보 보기"):
                            depts = str(row['부서']).split('\n')
                            names = str(row['담당자']).split('\n')
                            phones = str(row['연락처']).split('\n')
                            for idx in range(max(len(depts), len(names), len(phones))):
                                d = depts[idx] if idx < len(depts) else ""
                                n = names[idx] if idx < len(names) else ""
                                p = phones[idx] if idx < len(phones) else ""
                                st.markdown(f"""
                                <div class="contact-item">
                                    <span class="team-name">{d}</span><br>
                                    👤 {n} | 📞 <a href="tel:{p.replace('-', '')}">{p}</a>
                                </div>
                                """, unsafe_allow_html=True)
                            
                            if row['이미지']: st.image(row['이미지'], use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
