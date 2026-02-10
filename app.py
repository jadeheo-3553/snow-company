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

# 2. 초슬림 스타일 설정
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; }
    .main-title { font-size: 1.8rem; font-weight: bold; text-align: center; color: #1E3A5F; margin-bottom: 10px; }
    
    /* 필터 버튼 초슬림화 (모바일 최적화) */
    div[data-testid="stHorizontalBlock"] button {
        padding: 1px 2px !important;
        font-size: 0.7rem !important;
        min-height: 28px !important;
        margin: 0px !important;
    }
    
    .client-name { font-size: 1.05rem !important; font-weight: bold; display: inline; margin-right: 5px; }
    .addr-link { color: #007bff; text-decoration: none; font-size: 0.85rem; }
    .team-name { color: #e74c3c !important; font-weight: bold; font-size: 0.9rem; }
    .contact-item { background-color: #f8f9fa; padding: 8px; border-radius: 6px; margin-bottom: 5px; border: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드 및 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 4. 사이드바 (잘 작동 중인 기능 유지)
    with st.sidebar:
        st.header("📍 상세 설정")
        show_fav_only = st.toggle("⭐ 즐겨찾기만 보기", value=False)
        regions = sorted(list(set(df['주소'].apply(lambda x: str(x).split()[0] if x else "미지정"))))
        selected_region = st.selectbox("🌍 지역별 보기", ["전체"] + regions)

    # 5. 검색 및 초슬림 가나다 필터
    search_q = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")
    
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    
    # 버튼을 8개씩 2줄로 배치 (공간 최소화)
    c_cols1 = st.columns(8)
    for idx, c in enumerate(chosungs[:8]):
        if c_cols1[idx].button(c, key=f"c1_{c}", use_container_width=True): st.session_state.sel_chosung = c
    c_cols2 = st.columns(8)
    for idx, c in enumerate(chosungs[8:]):
        if c_cols2[idx].button(c, key=f"c2_{c}", use_container_width=True): st.session_state.sel_chosung = c

    # 필터링 로직
    f_df = df.copy()
    if search_q:
        f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]
    if st.session_state.sel_chosung != "전체":
        if st.session_state.sel_chosung == "A-Z":
            f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
        else:
            f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == st.session_state.sel_chosung)]
    if selected_region != "전체":
        f_df = f_df[f_df['주소'].str.startswith(selected_region)]
    if show_fav_only:
        f_df = f_df[f_df['거래처명'].isin(st.session_state.my_favs)]

    # 정렬: 즐겨찾기 우선
    f_df['is_fav'] = f_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
    f_df = f_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

    st.caption(f"총 {len(f_df)}개 표시 중 (필터: {st.session_state.sel_chosung})")

    # 6. 리스트 출력 (컴퓨터 정렬 오류 해결을 위해 3열 고정 로직)
    if len(f_df) > 0:
        # 데이터프레임을 리스트로 변환하여 순차 배치
        rows = f_df.to_dict('records')
        for i in range(0, len(rows), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(rows):
                    item = rows[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # [요청] 거래처명 바로 옆에 별표 배치
                            name = item['거래처명']
                            is_fav = name in st.session_state.my_favs
                            
                            n_col, s_col = st.columns([0.8, 0.2])
                            with n_col:
                                st.markdown(f'<span class="client-name">{name}</span>', unsafe_allow_html=True)
                            with s_col:
                                if st.button("⭐" if is_fav else "☆", key=f"f_{name}_{i+j}"):
                                    if is_fav: st.session_state.my_favs.remove(name)
                                    else: st.session_state.my_favs.add(name)
                                    st.rerun()

                            # [요청] 주소 네이버 지도 연결
                            addr = item['주소']
                            st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-link'>{addr}</a>", unsafe_allow_html=True)

                            with st.expander("👤 정보 상세보기"):
                                depts = str(item['부서명']).split('\n')
                                names = str(item['담당자']).split('\n')
                                phones = str(item['연락처']).split('\n')
                                
                                for k in range(max(len(depts), len(names), len(phones))):
                                    d = depts[k].strip() if k < len(depts) else "-"
                                    n = names[k].strip() if k < len(names) else "-"
                                    p = phones[k].strip() if k < len(phones) else "-"
                                    clean_p = re.sub(r'[^0-9]', '', p)
                                    
                                    st.markdown(f"""
                                    <div class="contact-item">
                                        <span class="team-name">{k+1}. {d}</span><br>
                                        👤 {n} | 📞 <a href="tel:{clean_p}" style="text-decoration:none; color:#007bff; font-weight:bold;">{p}</a>
                                    </div>
                                    """, unsafe_allow_html=True)
                                
                                if item['이미지'] and str(item['이미지']).startswith('http'):
                                    st.image(item['이미지'], use_container_width=True)
    else:
        st.info("검색 결과가 없습니다.")

except Exception as e:
    st.error(f"시스템 오류: {e}")

st.caption("© 2026 거래처 통합 관리 시스템")
