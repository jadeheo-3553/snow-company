import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", page_icon="🏢", layout="wide")

# 2. 강력한 CSS (모바일 타일 레이아웃 + 겹침 방지)
st.markdown("""
    <style>
    /* 상단 타이틀 축소 */
    .main-title { font-size: 1.4rem !important; font-weight: bold; text-align: center; margin: 15px 0; color: #333; }
    
    /* [요청] ㄱㄴㄷ 버튼 초밀착 격자 배치 (모바일 강제) */
    .filter-grid {
        display: grid;
        grid-template-columns: repeat(8, 1fr); /* 한 줄에 8개씩 */
        gap: 0px; /* 간격 없음 */
        border: 1px solid #ddd;
        margin-bottom: 20px;
    }
    .filter-btn {
        width: 100%;
        aspect-ratio: 1 / 1;
        border: 0.5px solid #eee;
        background: white;
        font-size: 0.8rem;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    }

    /* [요청] 거래처명 + 별표 겹침 방지 */
    .name-star-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        width: 100%;
    }
    .client-name {
        font-size: 1.05rem;
        font-weight: bold;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        max-width: 80%; /* 별표 자리를 위해 이름 길이 제한 */
        margin: 0;
    }

    /* 주소 및 메모 스타일 */
    .map-link { color: #007bff; text-decoration: none; font-size: 0.85rem; }
    .contact-card { background: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 4px solid #ff4b4b; margin: 5px 0; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 검색창
    search_q = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")

    # [핵심] ㄱㄴㄷ 필터 - 8열 구성으로 모바일에서도 격자 유지
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    cols = st.columns(8) 
    for idx, c in enumerate(chosungs):
        with cols[idx % 8]:
            if st.button(c, key=f"btn_{c}", use_container_width=True):
                st.session_state.sel_chosung = c

    # 필터링 로직 (생략 - 기존과 동일)
    f_df = df.copy()

    # 4. 거래처 카드 리스트
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
                        
                        # [요청] 이름과 별표 겹침 방지 레이아웃
                        head1, head2 = st.columns([0.8, 0.2])
                        head1.markdown(f'<p class="client-name">{name}</p>', unsafe_allow_html=True)
                        if head2.button("⭐" if is_fav else "☆", key=f"fav_{name}_{i+j}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        # [요청] 지도 링크 복구
                        addr = item['주소']
                        st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' class='map-link'>{addr}</a>", unsafe_allow_html=True)

                        with st.expander("👤 담당자 연락처 & 메모"):
                            depts = str(item.get('부서명', '')).split('\n')
                            names = str(item.get('담당자', '')).split('\n')
                            phones = str(item.get('연락처', '')).split('\n')
                            
                            for k in range(max(len(depts), len(names), len(phones))):
                                d = depts[k].strip() if k < len(depts) else "-"
                                n = names[k].strip() if k < len(names) else "-"
                                p = phones[k].strip() if k < len(phones) else "-"
                                
                                st.markdown(f"""<div class="contact-card"><b>{k+1}. {d}</b><br>
                                👤 {n} | 📞 <a href="tel:{p}">{p}</a></div>""", unsafe_allow_html=True)
                                # [요청] 부서별 개별 메모란
                                st.text_area(f"📝 {n} 메모", key=f"memo_{name}_{k}", height=65)

except Exception as e:
    st.error(f"오류 발생: {e}")
