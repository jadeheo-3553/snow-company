import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys
import re

# 1. 시스템 및 페이지 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리", page_icon="🏢", layout="wide")

# 2. 스타일 설정 (글자 크기, 간격, 타이틀 중앙 정렬)
st.markdown("""
    <style>
    /* 7. 메인 타이틀 중앙 정렬 및 크기 확대 */
    .main-title { font-size: 2.2rem !important; font-weight: bold; text-align: center; color: #1E3A5F; margin-bottom: 20px; }
    
    /* 5. 거래처명 글자 크기 축소 (반으로 줄임) */
    .client-name { font-size: 1.1rem !important; font-weight: bold; margin-bottom: 2px; }
    
    /* 6. 줄 간격 축소 및 카드 디자인 */
    .contact-item { 
        background-color: #ffffff; padding: 8px 12px; border: 1px solid #eee; 
        border-radius: 8px; margin-bottom: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); 
        line-height: 1.3;
    }
    
    /* 1. 전화번호 링크 스타일 */
    .phone-link { color: #007bff; text-decoration: none; font-weight: bold; }
    .stAppHeader {display:none;}
    
    /* 별표 즐겨찾기 스타일 */
    .star-icon { cursor: pointer; font-size: 1.2rem; float: right; }
    </style>
    """, unsafe_allow_html=True)

# 3. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

# 7. 첫 타이틀 중앙 정렬
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    
    # 8. 검색창 유지
    search_query = st.text_input("🔍 검색어를 입력하세요", placeholder="거래처명 또는 주소 검색...")

    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False) | 
                df['주소'].str.contains(search_query, case=False, na=False)]

    # 4. 리스트 출력
    if len(df) == 0:
        st.warning("데이터가 없습니다.")
    else:
        # 즐겨찾기 상태 관리를 위한 세션 초기화 (4번 기능 관련)
        if 'favorites' not in st.session_state:
            st.session_state.favorites = set()

        for i in range(0, len(df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(df):
                    row = df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # 4. 즐겨찾기 별표 기능 (클릭 시 토글)
                            is_fav = row['거래처명'] in st.session_state.favorites
                            star = "⭐" if is_fav else "☆"
                            
                            # 5. 거래처명 글자 크기 조정
                            title_col, star_col = st.columns([0.85, 0.15])
                            with title_col:
                                st.markdown(f'<p class="client-name">{row["거래처명"]}</p>', unsafe_allow_html=True)
                            with star_col:
                                if st.button(star, key=f"fav_{row['거래처명']}"):
                                    if is_fav: st.session_state.favorites.remove(row['거래처명'])
                                    else: st.session_state.favorites.add(row['거래처명'])
                                    st.rerun()

                            # 주소 표시 (간격 줄임)
                            addr = row['주소']
                            st.markdown(f"<p style='font-size:0.8rem; color:grey; margin-top:-10px;'>📍 {addr}</p>", unsafe_allow_html=True)
                            
                            with st.expander("👤 담당자 연락처 보기", expanded=False):
                                depts = str(row['부서']).split('\n') if pd.notna(row['부서']) else []
                                names = str(row['담당자']).split('\n') if pd.notna(row['담당자']) else []
                                phones = str(row['연락처']).split('\n') if pd.notna(row['연락처']) else []
                                
                                max_count = max(len(depts), len(names), len(phones))
                                
                                for idx in range(max_count):
                                    d = depts[idx].strip() if idx < len(depts) else "-"
                                    n = names[idx].strip() if idx < len(names) else "-"
                                    p = phones[idx].strip() if idx < len(phones) else "-"
                                    
                                    # 1. 전화번호 추출 및 클릭 시 즉시 연결 링크 생성
                                    # 숫자만 추출 (예: 01012345678)
                                    clean_p = re.sub(r'[^0-9]', '', p)
                                    
                                    st.markdown(f"""
                                    <div class="contact-item">
                                        <strong>{idx+1}. {d}</strong><br>
                                        👤 {n} | 📞 <a href="tel:{clean_p}" class="phone-link">{p}</a>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    # 3. 각 팀별 추가 정보 입력 칸 (비고)
                                    st.text_area(f"📝 {n} 담당자 추가 정보", key=f"note_{row['거래처명']}_{idx}", height=60, placeholder="메모를 입력하세요...")

                                # 2. 연락처 정보 복사 부분은 삭제됨 (기존 st.code 제거)

                                # 이미지 하단 배치
                                img_url = row['이미지']
                                if pd.notna(img_url) and str(img_url).startswith('http'):
                                    st.image(img_url, width=100)

except Exception as e:
    st.error(f"오류: {e}")
