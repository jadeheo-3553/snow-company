import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", layout="wide")

# 스타일 설정: 별표와 이름 밀착 및 타이틀 정렬
st.markdown("""
    <style>
    .block-container { padding: 1rem !important; }
    
    /* 타이틀 중앙정렬 */
    .main-title { 
        font-size: 1.6rem !important; 
        font-weight: bold; 
        text-align: center; 
        padding: 5px 0;
        line-height: 1.5;
        color: #1E3A5F;
    }

    /* 별표와 이름 밀착 레이아웃 (공간 최소화) */
    .fav-name-container {
        display: flex;
        align-items: center;
        gap: 2px; /* 간격 2px로 최소화 */
        margin-bottom: 5px;
    }
    .client-name {
        font-size: 1.05rem !important;
        font-weight: bold;
        margin: 0 !important;
        white-space: nowrap;
    }

    /* 부서명 빨간색 */
    .dept-red { color: #e74c3c; font-weight: bold; font-size: 0.95rem; }
    .contact-info { font-size: 0.9rem; color: #333; margin-bottom: 8px; }
    
    /* 체크박스 크기 조절 */
    div[data-testid="stCheckbox"] { min-height: 0px !important; }
    </style>
    """, unsafe_allow_html=True)

def get_chosung(text):
    if not text or pd.isna(text): return ""
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    char_code = ord(str(text)[0]) - 0xAC00
    if 0 <= char_code <= 11171: return CHOSUNG_LIST[char_code // 588]
    return str(text)[0].upper()

# 2. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()

    # 가나다 탭 필터 (고정)
    chosung_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    tabs = st.tabs(chosung_list)

    for idx, tab in enumerate(tabs):
        with tab:
            tab_name = chosung_list[idx]
            search_q = st.text_input("", placeholder="🔍 검색어...", key=f"search_{tab_name}", label_visibility="collapsed")
            
            f_df = df.copy()
            if search_q:
                f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]
            if tab_name != "전체":
                if tab_name == "A-Z":
                    f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
                else:
                    f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == tab_name)]

            f_df['is_fav'] = f_df['거래처명'].apply(lambda x: x in st.session_state.my_favs)
            f_df = f_df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True])

            rows = f_df.to_dict('records')
            for i in range(0, len(rows), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(rows):
                        item = rows[i + j]
                        with cols[j]:
                            with st.container(border=True):
                                name = item['거래처명']
                                
                                # [핵심] 별표와 이름을 한 열 안에서 나란히 배치 (줄바꿈 방지)
                                st.markdown('<div class="fav-name-container">', unsafe_allow_html=True)
                                h_c1, h_c2 = st.columns([0.12, 0.88]) # 비율을 더 좁게 조정
                                with h_c1:
                                    is_f = st.checkbox("⭐", value=(name in st.session_state.my_favs), 
                                                       key=f"chk_{name}_{tab_name}_{idx}_{i+j}", 
                                                       label_visibility="collapsed")
                                    if is_f and name not in st.session_state.my_favs:
                                        st.session_state.my_favs.add(name)
                                        st.rerun()
                                    elif not is_f and name in st.session_state.my_favs:
                                        st.session_state.my_favs.remove(name)
                                        st.rerun()
                                with h_c2:
                                    st.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                                st.markdown('</div>', unsafe_allow_html=True)

                                addr = item['주소']
                                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' style='font-size:0.82rem; color:#007bff; text-decoration:none;'>{addr}</a>", unsafe_allow_html=True)

                                with st.expander("👤 정보/메모"):
                                    depts = str(item.get('부서명', '')).split('\n')
                                    names = str(item.get('담당자', '')).split('\n')
                                    p_list = str(item.get('연락처', '')).split('\n')
                                    
                                    for k in range(max(len(depts), len(names), len(p_list))):
                                        d = depts[k].strip() if k < len(depts) else "-"
                                        n = names[k].strip() if k < len(names) else "-"
                                        p = p_list[k].strip() if k < len(p_list) else "-"
                                        
                                        st.markdown(f"""
                                        <div class="contact-info">
                                            <span class="dept-red">{k+1}. {d}</span><br>
                                            {n} / <a href="tel:{p}" style="text-decoration:none; color:#333;">{p}</a>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.text_area("📝 메모", key=f"memo_{name}_{tab_name}_{k}", height=60, label_visibility="collapsed")
                                    
                                    # [신규] 이미지 썸네일 표시 및 확대 기능
                                    img_url = item.get('이미지', '') # GSheet에 '이미지' 열이 있다고 가정
                                    if img_url:
                                        st.markdown("---")
                                        st.write("🖼️ 거래처 이미지 (클릭 시 확대)")
                                        st.image(img_url, width=100, use_container_width=False) # 썸네일 크기 100px

except Exception as e:
    st.error(f"오류: {e}")
