import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 페이지 설정 및 인라인 스타일 (별표 위치 강제 고정)
st.set_page_config(page_title="거래처 관리 Pro", layout="wide")

st.markdown("""
    <style>
    /* 전체 여백 최소화 */
    .block-container { padding: 1rem !important; }
    
    /* [핵심] 이름과 별표를 한 줄로 강제 결합 */
    .client-box {
        display: flex;
        align-items: center;
        gap: 5px;
        margin-bottom: 2px;
    }
    .client-name {
        font-size: 1.05rem !important;
        font-weight: bold;
        color: #1E3A5F;
        margin: 0 !important;
    }
    
    /* 체크박스를 별표처럼 보이게 커스텀 (버튼 밀림 방지) */
    .stCheckbox { margin-bottom: 0px !important; }
    .stCheckbox label { font-size: 1.2rem !important; margin-bottom: 0px !important; }

    /* 주소 및 메모 슬림화 */
    .addr-text { color: #007bff; text-decoration: none; font-size: 0.82rem; }
    .memo-card { 
        background-color: #f8f9fa; 
        padding: 8px; 
        border-radius: 5px; 
        border-left: 3px solid #ff4b4b; 
        margin-top: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 초성 추출 함수
def get_chosung(text):
    if not text or pd.isna(text): return ""
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    char_code = ord(str(text)[0]) - 0xAC00
    if 0 <= char_code <= 11171: return CHOSUNG_LIST[char_code // 588]
    return str(text)[0].upper()

# 2. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.subheader("🏢 거래처 통합 관리")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()

    # 3. [신규 방식] 탭 필터 - 공간 소모 0에 가까움
    chosung_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    tabs = st.tabs(chosung_list) # 버튼 대신 탭을 사용해 깔끔하게 정렬

    # 4. 필터링 및 리스트 출력
    for idx, tab in enumerate(tabs):
        with tab:
            search_q = st.text_input("🔍 검색", placeholder="거래처명/주소...", key=f"search_{idx}", label_visibility="collapsed")
            
            # 필터링 로직
            f_df = df.copy()
            current_chosung = chosung_list[idx]
            
            if search_q:
                f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]
            if current_chosung != "전체":
                if current_chosung == "A-Z":
                    f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
                else:
                    f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == current_chosung)]

            # 즐겨찾기 정렬
            f_df['is_fav'] = f_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
            f_df = f_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

            # 리스트 출력 (3열)
            rows = f_df.to_dict('records')
            for i in range(0, len(rows), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(rows):
                        item = rows[i + j]
                        with cols[j]:
                            with st.container(border=True):
                                # [핵심 해결] 체크박스 방식으로 이름 옆에 별표 고정
                                name = item['거래처명']
                                
                                # 이름과 체크박스(별표)를 한 열에 나란히 배치
                                n_c1, n_c2 = st.columns([0.85, 0.15])
                                with n_c1:
                                    st.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                                with n_c2:
                                    # 버튼이 아닌 체크박스를 사용하여 밀림 방지
                                    is_f = st.checkbox("⭐", value=(name in st.session_state.my_favs), key=f"chk_{name}_{i+j}", label_visibility="collapsed")
                                    if is_f: st.session_state.my_favs.add(name)
                                    elif not is_f and name in st.session_state.my_favs:
                                        st.session_state.my_favs.remove(name)
                                        st.rerun()

                                # 지도 연결
                                addr = item['주소']
                                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='addr-text'>{addr}</a>", unsafe_allow_html=True)

                                with st.expander("👤 담당자/메모"):
                                    depts = str(item['부서명']).split('\n')
                                    names = str(item['담당자']).split('\n')
                                    phones = str(item['연락처']).split('\n')
                                    for k in range(max(len(depts), len(names), len(phones))):
                                        d = depts[k].strip() if k < len(depts) else "-"
                                        n = names[k].strip() if k < len(names) else "-"
                                        p = phones[k].strip() if k < len(phones) else "-"
                                        st.markdown(f'<div class="memo-card"><b>{k+1}. {d}</b><br>👤 {n} | 📞 <a href="tel:{p}">{p}</a></div>', unsafe_allow_html=True)
                                        st.text_area(f"📝 {n} 메모", key=f"memo_{name}_{k}", height=60)

except Exception as e:
    st.error(f"오류: {e}")
