import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys
import re

# 1. 시스템 설정 (사이드바 아이콘 표시를 위해 상단바 숨김 제거)
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

# 2. 스타일 설정 (팀명 빨간색, 별표 위치 고정, 버튼 소형화)
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    .main-title { font-size: 2.2rem !important; font-weight: bold; text-align: center; color: #1E3A5F; margin-bottom: 15px; }
    
    /* 가나다 버튼을 작게 만들어 2줄 배치 최적화 */
    div[data-testid="stHorizontalBlock"] button {
        padding: 2px !important;
        font-size: 0.8rem !important;
        min-height: 35px !important;
    }
    
    .client-name { font-size: 1.1rem !important; font-weight: bold; margin: 0; }
    .team-name { color: #e74c3c !important; font-weight: bold; font-size: 0.95rem; }
    .contact-item { background-color: #fdfdfd; padding: 8px; border: 1px solid #eee; border-radius: 8px; margin-bottom: 6px; }
    .phone-link { color: #007bff; text-decoration: none; font-weight: bold; }
    
    /* 주소 링크 스타일 (네이버 지도용) */
    .addr-link { color: #4A90E2; text-decoration: none; font-size: 0.85rem; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# 3. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_raw = conn.read(spreadsheet=url, ttl=0)
    df = df_raw.fillna("")

    # 세션 상태 설정
    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 4. 사이드바 메뉴 (모바일은 왼쪽 상단 '>' 화살표 아이콘 클릭)
    with st.sidebar:
        st.header("📍 상세 필터")
        show_fav_only = st.toggle("⭐ 즐겨찾기만 보기", value=False)
        regions = sorted(list(set(df['주소'].apply(lambda x: str(x).split()[0] if x else "미지정"))))
        selected_region = st.selectbox("🌍 지역별 보기", ["전체"] + regions)

    # 5. 메인 화면 - 검색 및 가나다 필터 (2줄 배치)
    search_query = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")
    
    st.caption("📍 가나다 필터")
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    
    # 8개씩 2줄로 배치하여 버튼 크기 축소
    row1 = st.columns(8)
    for i, c in enumerate(chosungs[:8]):
        if row1[i].button(c, key=f"btn1_{c}", use_container_width=True):
            st.session_state.sel_chosung = c
            
    row2 = st.columns(8)
    for i, c in enumerate(chosungs[8:]):
        if row2[i].button(c, key=f"btn2_{c}", use_container_width=True):
            st.session_state.sel_chosung = c

    # --- 필터링 로직 ---
    filtered_df = df.copy()

    if search_query:
        filtered_df = filtered_df[filtered_df['거래처명'].str.contains(search_query, case=False) | 
                                 filtered_df['주소'].str.contains(search_query, case=False)]
    
    if st.session_state.sel_chosung != "전체":
        if st.session_state.sel_chosung == "A-Z":
            filtered_df = filtered_df[filtered_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
        else:
            filtered_df = filtered_df[filtered_df['거래처명'].apply(lambda x: get_chosung(x) == st.session_state.sel_chosung)]

    if selected_region != "전체":
        filtered_df = filtered_df[filtered_df['주소'].str.startswith(selected_region)]

    if show_fav_only:
        filtered_df = filtered_df[filtered_df['거래처명'].isin(st.session_state.my_favs)]

    # 즐겨찾기 우선 정렬
    filtered_df['is_fav'] = filtered_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
    filtered_df = filtered_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

    # 6. 리스트 출력
    if len(filtered_df) == 0:
        st.info("조건에 맞는 거래처가 없습니다.")
    else:
        st.caption(f"총 {len(filtered_df)}개 표시 중 (필터: {st.session_state.sel_chosung})")
        
        for i, (idx, row) in enumerate(filtered_df.iterrows()):
            cols = st.columns(3)
            with cols[i % 3]:
                with st.container(border=True):
                    name = row['거래처명']
                    is_fav = name in st.session_state.my_favs
                    
                    # [요청] 거래처명 바로 옆에 별표 배치
                    name_col, star_col = st.columns([0.82, 0.18])
                    name_col.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                    if star_col.button("⭐" if is_fav else "☆", key=f"star_{name}_{idx}"):
                        if is_fav: st.session_state.my_favs.remove(name)
                        else: st.session_state.my_favs.add(name)
                        st.rerun()

                    # [요청] 주소 클릭 시 네이버 지도 연결
                    addr = row['주소']
                    st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)
                    
                    with st.expander("👤 정보 상세보기"):
                        depts = str(row['부서명']).split('\n')
                        names = str(row['담당자']).split('\n')
                        phones = str(row['연락처']).split('\n')
                        
                        for d_idx in range(max(len(depts), len(names), len(phones))):
                            d = depts[d_idx].strip() if d_idx < len(depts) else "-"
                            n = names[d_idx].strip() if d_idx < len(names) else "-"
                            p = phones[d_idx].strip() if d_idx < len(phones) else "-"
                            clean_p = re.sub(r'[^0-9]', '', p)
                            
                            st.markdown(f"""
                            <div class="contact-item">
                                <span class="team-name">{d_idx+1}. {d}</span><br>
                                👤 {n} | 📞 <a href="tel:{clean_p}" class="phone-link">{p}</a>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        if row['이미지'] and str(row['이미지']).startswith('http'):
                            st.image(row['이미지'], use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 시스템 오류: {e}")

st.caption("© 2026 거래처 통합 관리 시스템")
