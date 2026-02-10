import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 페이지 설정 (사이드바 아이콘 표시를 위해 헤더 숨김 해제)
st.set_page_config(page_title="거래처 관리", page_icon="🏢", layout="wide")

# 초성 추출 함수 (데이터가 없어도 에러 안 나게 보강)
def get_chosung(text):
    if not text or pd.isna(text): return ""
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    first_char = str(text)[0]
    if '가' <= first_char <= '힣':
        ch_idx = (ord(first_char) - 0xAC00) // 588
        return CHOSUNG_LIST[ch_idx]
    return first_char.upper()

# 2. 디자인 스타일 (빨간 팀명, 버튼 크기 조절)
st.markdown("""
    <style>
    .block-container { padding-top: 2rem !important; }
    .main-title { font-size: 1.8rem; font-weight: bold; text-align: center; margin-bottom: 10px; }
    
    /* 필터 버튼을 작고 촘촘하게 */
    div[data-testid="stHorizontalBlock"] button {
        padding: 2px !important;
        font-size: 0.7rem !important;
        min-height: 30px !important;
    }
    
    .team-name { color: #ff4b4b !important; font-weight: bold; font-size: 0.9rem; } /* 팀명 빨간색 */
    .addr-link { color: #007bff; text-decoration: none; font-size: 0.85rem; }
    .contact-card { background-color: #f9f9f9; padding: 8px; border-radius: 8px; margin-bottom: 5px; border-bottom: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 불러오기
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    df.columns = df.columns.str.strip() # 컬럼명 공백 제거 (에러 방지 핵심!)

    # 세션 관리
    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 사이드바 (모바일 왼쪽 상단 화살표 누르면 열림)
    with st.sidebar:
        st.header("📍 상세 설정")
        if st.button("⭐ 즐겨찾기 모두 해제"):
            st.session_state.my_favs = set()
            st.rerun()

    # 4. 상단 검색창 및 필터
    search_q = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소를 입력하세요...", key="search_bar")
    
    st.caption("📍 가나다 필터")
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    
    # 필터 2줄 배치 (8개씩)
    row1 = st.columns(8)
    for i, c in enumerate(chosungs[:8]):
        if row1[i].button(c, key=f"f1_{c}", use_container_width=True): st.session_state.sel_chosung = c
    
    row2 = st.columns(8)
    for i, c in enumerate(chosungs[8:]):
        if row2[i].button(c, key=f"f2_{c}", use_container_width=True): st.session_state.sel_chosung = c

    # 5. 필터링 로직
    f_df = df.copy()
    if search_q:
        f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]
    if st.session_state.sel_chosung != "전체":
        if st.session_state.sel_chosung == "A-Z":
            f_df = f_df[f_df['거래처명'].str.contains('[a-zA-Z]', na=False)]
        else:
            f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == st.session_state.sel_chosung)]

    # 즐겨찾기 정렬
    f_df['is_fav'] = f_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
    f_df = f_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

    st.write(f"총 {len(f_df)}개의 거래처 표시 중")

    # 6. 리스트 출력 (카드 형태)
    for idx, row in f_df.reset_index().iterrows():
        # 3열씩 배치 (모바일은 자동 1열)
        cols = st.columns(3)
        with cols[idx % 3]:
            with st.container(border=True):
                name = row['거래처명']
                is_fav = name in st.session_state.my_favs
                
                # 이름 옆 별표
                n_col, s_col = st.columns([0.8, 0.2])
                n_col.markdown(f"**{name}**")
                if s_col.button("⭐" if is_fav else "☆", key=f"star_{name}_{idx}"):
                    if is_fav: st.session_state.my_favs.remove(name)
                    else: st.session_state.my_favs.add(name)
                    st.rerun()

                # 주소와 지도 링크
                addr = row['주소']
                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)

                with st.expander("👤 담당자 정보"):
                    # 여러 명의 담당자 처리 (줄바꿈 기준)
                    depts = str(row.get('부서', '-')).split('\n')
                    names = str(row.get('담당자', '-')).split('\n')
                    phones = str(row.get('연락처', '-')).split('\n')
                    
                    for i in range(max(len(depts), len(names), len(phones))):
                        d = depts[i].strip() if i < len(depts) else ""
                        n = names[i].strip() if i < len(names) else ""
                        p = phones[i].strip() if i < len(phones) else ""
                        st.markdown(f"""
                        <div class="contact-card">
                            <span class="team-name">{d}</span><br>
                            👤 {n} | 📞 <a href="tel:{p.replace('-', '')}">{p}</a>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    if row.get('이미지'):
                        st.image(row['이미지'], use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
