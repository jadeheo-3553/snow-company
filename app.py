import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 마스터", page_icon="🏢", layout="wide")

# 스타일 설정 (타이틀 축소 및 검색창 강조)
st.markdown("""
    <style>
    .small-title { font-size: 1.4rem !important; font-weight: bold; margin-bottom: 5px; }
    .stAppHeader {display:none;}
    div[data-testid="stExpander"] { border: none !important; box-shadow: none !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

# 상단 레이아웃: 제목과 검색창을 메인에 배치
st.markdown('<p class="small-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    
    # 즐겨찾기(별점) 기능이 시트에 있다면 상단 노출
    if '즐겨찾기' in df.columns:
        df['sort_order'] = df['즐겨찾기'].apply(lambda x: 0 if x == 'O' else 1)
        df = df.sort_values(by=['sort_order', '거래처명']).reset_index(drop=True)
    else:
        df = df.sort_values(by='거래처명').reset_index(drop=True)

    # [검색창 메인 노출]
    search_query = st.text_input("🔍 검색 (거래처명 또는 주소)", placeholder="찾으시는 거래처를 입력하세요")

    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False) | 
                df['주소'].str.contains(search_query, case=False, na=False)]

    # 4. 리스트 출력
    if len(df) == 0:
        st.warning("검색 결과가 없습니다.")
    else:
        st.caption(f"검색 결과: {len(df)}건")
        
        for i in range(0, len(df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(df):
                    row = df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # 즐겨찾기 표시
                            prefix = "⭐ " if '즐겨찾기' in df.columns and row['즐겨찾기'] == 'O' else ""
                            st.markdown(f"**{prefix}{row['거래처명']}**")
                            
                            # 주소 (클릭 시 지도)
                            naver_url = f"https://map.naver.com/v5/search/{row['주소']}"
                            st.markdown(f"📍 <a href='{naver_url}' style='text-decoration:none; color:#4A90E2; font-size:0.85rem;'>{row['주소']}</a>", unsafe_allow_html=True)
                            
                            # 빠른 실행 버튼 (전화)
                            if '전화번호' in df.columns and pd.notna(row['전화번호']):
                                st.link_button(f"📞 전화 걸기", f"tel:{row['전화번호']}", use_container_width=True)

                            # 상세 정보
                            with st.expander("📄 정보 더보기"):
                                for col in ['담당자', '전화번호', '이메일', '비고']:
                                    if col in df.columns and pd.notna(row[col]):
                                        st.write(f"**{col}:** {row[col]}")
                                
                                # 정보 복사 아이디어 (동료 공유용)
                                info_text = f"[{row['거래처명']}]\n주소: {row['주소']}\n담당: {row.get('담당자','')}\nTEL: {row.get('전화번호','')}"
                                st.code(info_text, language=None)
                                st.caption("위 박스를 클릭해서 정보를 복사하세요.")

                                st.divider()
                                
                                # 사진 (최하단 최소화)
                                img_url = row['이미지']
                                if pd.notna(img_url) and str(img_url).startswith('http'):
                                    st.markdown(f'''
                                        <a href="{img_url}" target="_blank">
                                            <img src="{img_url}" style="width:100px; height:100px; object-fit:cover; border-radius:8px; border:1px solid #ddd;">
                                        </a>
                                    ''', unsafe_allow_html=True)
                                    st.caption("사진 클릭 시 확대")

except Exception as e:
    st.error(f"오류: {e}")

st.caption("© 2026 거래처 관리 시스템")
