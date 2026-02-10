import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", layout="wide")

# 스타일 설정 (이름 옆 별표 고정용)
st.markdown("""
    <style>
    .block-container { padding: 1rem !important; }
    .client-name {
        font-size: 1.0rem !important;
        font-weight: bold;
        margin: 0 !important;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .stCheckbox { margin-bottom: 0px !important; display: flex; justify-content: flex-end; }
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

    # 3. 가나다 필터 (탭 방식 유지)
    chosung_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    tabs = st.tabs(chosung_list)

    for idx, tab in enumerate(tabs):
        with tab:
            tab_name = chosung_list[idx]
            # 탭별 검색창 (공간 절약형)
            search_q = st.text_input("", placeholder="🔍 검색어...", key=f"search_{tab_name}", label_visibility="collapsed")
            
            # 데이터 필터링
            f_df = df.copy()
            if search_q:
                f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]
            if tab_name != "전체":
                if tab_name == "A-Z":
                    f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
                else:
                    f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == tab_name)]

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
                                name = item['거래처명']
                                
                                # [오류 해결] key값에 tab_name을 추가하여 중복 방지
                                n_c1, n_c2 = st.columns([0.85, 0.15])
                                with n_c1:
                                    st.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                                with n_c2:
                                    # 별표 아이콘으로 체크박스 구현
                                    is_f = st.checkbox("⭐", value=(name in st.session_state.my_favs), 
                                                       key=f"chk_{name}_{tab_name}_{i+j}", 
                                                       label_visibility="collapsed")
                                    
                                    # 상태 변화 감지 및 반영
                                    if is_f and name not in st.session_state.my_favs:
                                        st.session_state.my_favs.add(name)
                                        st.rerun()
                                    elif not is_f and name in st.session_state.my_favs:
                                        st.session_state.my_favs.remove(name)
                                        st.rerun()

                                addr = item['주소']
                                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' style='font-size:0.8rem; color:#007bff; text-decoration:none;'>{addr}</a>", unsafe_allow_html=True)

                                with st.expander("👤 정보/메모"):
                                    depts = str(item.get('부서명', '')).split('\n')
                                    names = str(item.get('담당자', '')).split('\n')
                                    p_list = str(item.get('연락처', '')).split('\n')
                                    
                                    for k in range(max(len(depts), len(names), len(p_list))):
                                        d = depts[k].strip() if k < len(depts) else "-"
                                        n = names[k].strip() if k < len(names) else "-"
                                        p = p_list[k].strip() if k < len(p_list) else "-"
                                        st.markdown(f'**{k+1}. {d}** | {n} | [📞] (tel:{p})')
                                        st.text_area("📝 메모", key=f"memo_{name}_{tab_name}_{k}", height=60, label_visibility="collapsed")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")
