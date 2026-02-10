import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys
import re

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리 Pro", page_icon="🏢", layout="wide")

# 초성 추출 함수
def get_chosung(text):
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    if not text or pd.isna(text): return ""
    char_code = ord(str(text)[0]) - 0xAC00
    if 0 <= char_code <= 11171:
        return CHOSUNG_LIST[char_code // 588]
    return str(text)[0].upper()

# 2. 스타일 설정
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .stAppHeader {display:none;}
    .main-title { font-size: 2.2rem !important; font-weight: bold; text-align: center; color: #1E3A5F; margin-bottom: 15px; }
    .client-row { display: flex; align-items: center; gap: 8px; }
    .client-name { font-size: 1.1rem !important; font-weight: bold; margin: 0; }
    .team-name { color: #e74c3c !important; font-weight: bold; font-size: 0.95rem; }
    .contact-item { background-color: #fdfdfd; padding: 8px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 6px; }
    .phone-link { color: #007bff; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_raw = conn.read(spreadsheet=url, ttl=0)
    
    # 데이터 안전화: 모든 결측치를 빈 문자열로 대체
    df = df_raw.fillna("")

    # 4. 사이드바 메뉴 (즐겨찾기 및 지역 필터)
    if 'my_favs' not in st.session_state:
        st.session_state.my_favs = set()

    with st.sidebar:
        st.header("📍 상세 필터")
        show_fav_only = st.toggle("⭐ 즐겨찾기만 보기", value=False)
        
        # 주소에서 첫 단어 추출하여 지역 리스트 생성 (예: 경기도, 서울특별시)
        regions = sorted(list(set(df['주소'].apply(lambda x: str(x).split()[0] if x else "미지정"))))
        selected_region = st.selectbox("🌍 지역별 보기", ["전체"] + regions)

    # 5. 메인 화면 - 검색 및 초성 필터
    search_query = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")
    
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    selected_chosung = st.segmented_control("정렬 필터", chosungs, default="전체")

    # --- 필터링 로직 시작 ---
    filtered_df = df.copy()

    # 검색어 필터
    if search_query:
        filtered_df = filtered_df[filtered_df['거래처명'].str.contains(search_query, case=False) | 
                                 filtered_df['주소'].str.contains(search_query, case=False)]
    
    # 초성 필터
    if selected_chosung != "전체":
        if selected_chosung == "A-Z":
            filtered_df = filtered_df[filtered_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
        else:
            filtered_df = filtered_df[filtered_df['거래처명'].apply(lambda x: get_chosung(x) == selected_chosung)]

    # 지역 필터
    if selected_region != "전체":
        filtered_df = filtered_df[filtered_df['주소'].str.startswith(selected_region)]

    # 즐겨찾기 필터 (시트 'O' 또는 개인 별표)
    if '즐겨찾기' not in filtered_df.columns: filtered_df['즐겨찾기'] = ""
    
    if show_fav_only:
        filtered_df = filtered_df[filtered_df['즐겨찾기'].eq('O') | filtered_df['거래처명'].isin(st.session_state.my_favs)]

    # 정렬: 즐겨찾기 우선
    filtered_df['sort_key'] = filtered_df['즐겨찾기'].eq('O') | filtered_df['거래처명'].isin(st.session_state.my_favs)
    filtered_df = filtered_df.sort_values(by=['sort_key', '거래처명'], ascending=[False, True])

    # 6. 리스트 출력
    if len(filtered_df) == 0:
        st.info("조건에 맞는 거래처가 없습니다.")
    else:
        st.caption(f"총 {len(filtered_df)}개의 거래처가 표시 중입니다.")
        
        for i in range(0, len(filtered_df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(filtered_df):
                    row = filtered_df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # 거래처명 + 별표 한 줄 배치
                            name_col, star_col = st.columns([0.8, 0.2])
                            is_fav = (row['즐겨찾기'] == 'O') or (row['거래처명'] in st.session_state.my_favs)
                            star_btn = "⭐" if is_fav else "☆"
                            
                            with name_col:
                                st.markdown(f'<p class="client-name">{row["거래처명"]}</p>', unsafe_allow_html=True)
                            with star_col:
                                if st.button(star_btn, key=f"star_{row['거래처명']}_{i+j}"):
                                    if row['거래처명'] in st.session_state.my_favs:
                                        st.session_state.my_favs.remove(row['거래처명'])
                                    else:
                                        st.session_state.my_favs.add(row['거래처명'])
                                    st.rerun()

                            st.markdown(f"<p style='font-size:0.8rem; color:grey; margin-top:-5px;'>📍 {row['주소']}</p>", unsafe_allow_html=True)
                            
                            with st.expander("👤 정보 상세보기"):
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
                                    
                                    st.text_area(f"📝 {n} 메모", key=f"memo_{row['거래처명']}_{idx}", height=60)

                                if row['이미지'] and str(row['이미지']).startswith('http'):
                                    st.image(row['이미지'], width=100)

except Exception as e:
    st.error(f"⚠️ 시스템 오류가 발생했습니다. 시트의 열 이름이 '거래처명, 부서명, 담당자, 연락처, 주소, 이미지' 인지 확인해주세요. (오류내용: {e})")

st.caption("© 2026 거래처 통합 관리 시스템")
