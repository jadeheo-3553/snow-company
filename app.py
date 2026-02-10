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

# 2. 스타일 설정 (모바일 최적화)
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .stAppHeader {display:none;}
    .main-title { font-size: 1.8rem !important; font-weight: bold; text-align: center; margin-bottom: 10px; }
    
    /* 거래처명과 별표를 한 줄에 배치 */
    .title-container { display: flex; align-items: center; gap: 10px; }
    .client-name { font-size: 1.05rem !important; font-weight: bold; margin: 0; }
    
    /* 팀명 빨간색 */
    .team-name { color: #e74c3c !important; font-weight: bold; font-size: 0.9rem; }
    
    .contact-item { background-color: #f8f9fa; padding: 8px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #eee; }
    .phone-link { color: #007bff; text-decoration: none; font-weight: bold; }
    .addr-link { color: #4A90E2; text-decoration: none; font-size: 0.85rem; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    # 세션 상태 초기화 (개별 사용자용)
    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 4. 정렬 필터 (모바일 2줄 배치)
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
    st.write("📍 가나다 필터")
    
    # 두 줄로 나누어 버튼 생성
    c1 = st.columns(8)
    for idx, c in enumerate(chosungs[:8]):
        if c1[idx].button(c, use_container_width=True): st.session_state.sel_chosung = c
    
    c2 = st.columns(7)
    for idx, c in enumerate(chosungs[8:]):
        if c2[idx].button(c, use_container_width=True): st.session_state.sel_chosung = c

    # 필터링 로직
    f_df = df.copy()
    if st.session_state.sel_chosung != "전체":
        f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == st.session_state.sel_chosung)]

    # 즐겨찾기 우선 정렬
    f_df['is_fav'] = f_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
    f_df = f_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

    # 5. 리스트 출력
    for i in range(0, len(f_df), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(f_df):
                row = f_df.iloc[i + j]
                with cols[j]:
                    with st.container(border=True):
                        # 거래처명과 별표를 한 줄에 나란히
                        name = row['거래처명']
                        is_fav = name in st.session_state.my_favs
                        star = "⭐" if is_fav else "☆"
                        
                        col_n, col_s = st.columns([0.8, 0.2])
                        col_n.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                        if col_s.button(star, key=f"s_{name}_{i+j}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        # 주소 클릭 시 네이버 지도 연결
                        addr = row['주소']
                        n_map = f"https://map.naver.com/v5/search/{addr}"
                        st.markdown(f"📍 <a href='{n_map}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)

                        with st.expander("👤 담당자 상세 정보"):
                            depts = str(row['부서명']).split('\n')
                            names = str(row['담당자']).split('\n')
                            phones = str(row['연락처']).split('\n')
                            
                            for idx in range(max(len(depts), len(names), len(phones))):
                                d = depts[idx].strip() if idx < len(depts) else "-"
                                n = names[idx].strip() if idx < len(names) else "-"
                                p = phones[idx].strip() if idx < len(phones) else "-"
                                clean_p = re.sub(r'[^0-9]', '', p)
                                
                                st.markdown(f"""
                                <div class="contact-item">
                                    <span class="team-name">{idx+1}. {d}</span><br>
                                    👤 {n} | 📞 <a href="tel:{clean_p}" class="phone-link">{p}</a>
                                </div>
                                """, unsafe_allow_html=True)
                                st.text_area(f"📝 {n} 메모", key=f"m_{name}_{idx}", height=60)

except Exception as e:
    st.error(f"시스템 오류: {e}")
