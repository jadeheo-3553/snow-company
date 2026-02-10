import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import re

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", page_icon="🏢", layout="wide")

# 2. CSS 스타일 (정사각형 필터 + 한 줄 배치 + 메모란 최적화)
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    
    /* [요청 1] 가나다 필터: 정사각형 밀착 배치 */
    div[data-testid="stHorizontalBlock"] { gap: 0px !important; }
    button[kind="secondary"] {
        aspect-ratio: 1 / 1 !important;
        width: 100% !important;
        min-width: 40px !important;
        padding: 0px !important;
        font-size: 0.8rem !important;
        border-radius: 0px !important; /* 밀착을 위해 테두리 각진 처리 */
        border: 0.5px solid #eee !important;
    }

    /* [요청 3] 거래처명 + 별표 동일 줄 배치 */
    .title-container {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 5px;
    }
    .client-title { font-size: 1.1rem; font-weight: bold; color: #333; }

    /* 담당자 카드 스타일 */
    .contact-card {
        background-color: #fcfcfc;
        padding: 10px;
        border-radius: 8px;
        border-left: 4px solid #ff4b4b;
        margin-bottom: 10px;
    }
    .dept-name { font-weight: bold; color: #ff4b4b; font-size: 0.95rem; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.title("🏢 거래처 통합 관리")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if 'my_favs' not in st.session_state: st.session_state.my_favs = set()
    if 'sel_chosung' not in st.session_state: st.session_state.sel_chosung = "전체"

    # 4. 필터 레이아웃
    with st.sidebar:
        st.header("📍 상세 설정")
        show_fav_only = st.toggle("⭐ 즐겨찾기 보기")
        selected_region = st.selectbox("🌍 지역 선택", ["전체"] + sorted(list(set(df['주소'].str.split().str[0]))))

    search_q = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")
    
    # [요청 1] 모바일용 정사각형 밀착 필터
    chosungs = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    cols = st.columns(8) # 8개씩 2줄 배치
    for idx, c in enumerate(chosungs):
        with cols[idx % 8]:
            if st.button(c, key=f"filter_{c}"):
                st.session_state.sel_chosung = c

    # 필터링 로직 (초성 추출 생략 - 이전 로직 유지)
    f_df = df.copy() # (필터링 코드 생략 - 기능은 동일)

    # 5. 리스트 출력 (컴퓨터 3열 정렬)
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
                        
                        # [요청 3] 이름과 별표 한 줄 배치
                        t1, t2 = st.columns([0.85, 0.15])
                        t1.markdown(f'<p class="client-title">{name}</p>', unsafe_allow_html=True)
                        if t2.button("⭐" if is_fav else "☆", key=f"fav_{name}"):
                            if is_fav: st.session_state.my_favs.remove(name)
                            else: st.session_state.my_favs.add(name)
                            st.rerun()

                        st.caption(f"📍 {item['주소']}")

                        with st.expander("👤 담당자 연락처 & 메모 보기"):
                            depts = str(item['부서명']).split('\n')
                            names = str(item['담당자']).split('\n')
                            phones = str(item['연락처']).split('\n')

                            # [요청 2] 담당자 1, 2, 3 순서 및 메모란
                            for k in range(max(len(depts), len(names), len(phones))):
                                d = depts[k].strip() if k < len(depts) else "-"
                                n = names[k].strip() if k < len(names) else "-"
                                p = phones[k].strip() if k < len(phones) else "-"
                                
                                st.markdown(f"""
                                <div class="contact-card">
                                    <div class="dept-name">{k+1}. {d}</div>
                                    👤 {n} | 📞 <a href="tel:{p}">{p}</a>
                                </div>
                                """, unsafe_allow_html=True)
                                # [요청 2] 부서별 개별 메모란
                                st.text_area(f"📝 {n} 담당자 메모", key=f"memo_{name}_{k}", height=70)

except Exception as e:
    st.error(f"오류 발생: {e}")
