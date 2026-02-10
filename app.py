import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys
import re

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 마스터", page_icon="🏢", layout="wide")

# 2. 스타일 설정 (상단 여백 제거, 팀명 빨간색, 줄 간격 축소)
st.markdown("""
    <style>
    /* 4. 상단 빈 공간 최소화 */
    .block-container { padding-top: 1rem !important; padding-bottom: 0rem !important; }
    .stAppHeader {display:none;}
    
    /* 7. 메인 타이틀 스타일 */
    .main-title { font-size: 2rem !important; font-weight: bold; text-align: center; color: #1E3A5F; margin-bottom: 15px; }
    
    /* 5, 6. 거래처명 및 줄간격 조절 */
    .client-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: -5px; }
    .client-name { font-size: 1.1rem !important; font-weight: bold; color: #333; }
    
    /* 3. 팀명 빨간색 설정 */
    .team-name { color: #e74c3c !important; font-weight: bold; }
    
    .contact-item { 
        background-color: #ffffff; padding: 6px 10px; border: 1px solid #eee; 
        border-radius: 8px; margin-bottom: 4px; line-height: 1.2;
    }
    .phone-link { color: #007bff; text-decoration: none; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 3. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

# 타이틀 출력
st.markdown('<p class="main-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    
    # [즐겨찾기 열 확인] 없으면 임시로 생성
    if '즐겨찾기' not in df.columns:
        df['즐겨찾기'] = ""

    # 5. 사이드바 - 즐겨찾기 필터 및 추가 기능
    with st.sidebar:
        st.header("🛠️ 관리 메뉴")
        show_fav_only = st.toggle("⭐ 즐겨찾기만 보기", value=False)
        st.divider()
        st.info("시트에 '즐겨찾기' 열을 만들고 'O'를 입력하면 공통 즐겨찾기가 됩니다.")

    # 세션 기반 나만의 즐겨찾기 초기화
    if 'my_favs' not in st.session_state:
        st.session_state.my_favs = set()

    # 검색 및 필터 로직
    search_query = st.text_input("🔍 검색", placeholder="거래처명 또는 주소 입력...")

    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False) | 
                df['주소'].str.contains(search_query, case=False, na=False)]

    # 즐겨찾기 필터링 (공통 'O' 또는 개인 별표)
    if show_fav_only:
        df = df[df['즐겨찾기'].eq('O') | df['거래처명'].isin(st.session_state.my_favs)]

    # 정렬: 즐겨찾기 우선순위
    df['is_fav'] = df['즐겨찾기'].eq('O') | df['거래처명'].isin(st.session_state.my_favs)
    df = df.sort_values(by=['is_fav', '거래처명'], ascending=[False, True]).reset_index(drop=True)

    # 4. 리스트 출력
    if len(df) == 0:
        st.warning("표시할 거래처가 없습니다.")
    else:
        for i in range(0, len(df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(df):
                    row = df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # 1. 거래처명 뒤에 바로 별표 배치
                            c_name = row['거래처명']
                            is_personal_fav = c_name in st.session_state.my_favs
                            is_common_fav = row['즐겨찾기'] == 'O'
                            
                            # 별표 상태 결정
                            star_icon = "⭐" if (is_personal_fav or is_common_fav) else "☆"
                            
                            # 레이아웃: 이름과 별표를 한 줄에
                            name_col, star_col = st.columns([0.8, 0.2])
                            with name_col:
                                st.markdown(f'<p class="client-name">{c_name}</p>', unsafe_allow_html=True)
                            with star_col:
                                if st.button(star_icon, key=f"star_{c_name}_{i+j}"):
                                    if is_personal_fav: st.session_state.my_favs.remove(c_name)
                                    else: st.session_state.my_favs.add(c_name)
                                    st.rerun()

                            # 주소 (줄간격 최소화)
                            st.markdown(f"<p style='font-size:0.8rem; color:grey; margin-top:-10px;'>📍 {row['주소']}</p>", unsafe_allow_html=True)
                            
                            with st.expander("👤 담당자 연락처 보기"):
                                depts = str(row['부서명']).split('\n') if pd.notna(row['부서명']) else []
                                names = str(row['담당자']).split('\n') if pd.notna(row['담당자']) else []
                                phones = str(row['연락처']).split('\n') if pd.notna(row['연락처']) else []
                                
                                for idx in range(max(len(depts), len(names), len(phones))):
                                    d = depts[idx].strip() if idx < len(depts) else "-"
                                    n = names[idx].strip() if idx < len(names) else "-"
                                    p = phones[idx].strip() if idx < len(phones) else "-"
                                    clean_p = re.sub(r'[^0-9]', '', p)
                                    
                                    # 3. 팀명(부서) 빨간색 적용
                                    st.markdown(f"""
                                    <div class="contact-item">
                                        <span class="team-name">{idx+1}. {d}</span><br>
                                        👤 {n} | 📞 <a href="tel:{clean_p}" class="phone-link">{p}</a>
                                    </div>
                                    """, unsafe_allow_html=True)

                                    # 3. 추가 메모장
                                    st.text_area(f"📝 {n} 메모", key=f"memo_{c_name}_{idx}", height=60)

                                # 이미지 최소화 출력
                                if pd.notna(row['이미지']) and str(row['이미지']).startswith('http'):
                                    st.markdown(f'<br><a href="{row["이미지"]}" target="_blank"><img src="{row["이미지"]}" style="width:80px; border-radius:5px;"></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"오류: {e}")
