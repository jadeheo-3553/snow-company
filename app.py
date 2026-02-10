import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리", page_icon="🏢", layout="wide")

# 타이틀 및 스타일 설정
st.markdown("""
    <style>
    .small-title {
        font-size: 1.3rem !important;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .stAppHeader {display:none;}
    </style>
    """, unsafe_allow_html=True)

# 2. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<p class="small-title">🏢 거래처 통합 관리</p>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    df = df.sort_values(by='거래처명').reset_index(drop=True)

    # 3. 사이드바 검색
    with st.sidebar:
        st.markdown("### 🔍 검색")
        search_query = st.text_input("거래처명 입력", placeholder="검색어...")

    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False)]

    # 4. 리스트 출력
    if len(df) == 0:
        st.warning("데이터가 없습니다.")
    else:
        for i in range(0, len(df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(df):
                    row = df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # [목록] 텍스트 중심
                            st.markdown(f"**{row['거래처명']}**")
                            
                            naver_url = f"https://map.naver.com/v5/search/{row['주소']}"
                            st.markdown(f"📍 <a href='{naver_url}' style='text-decoration:none; color:#4A90E2; font-size:0.85rem;'>{row['주소']}</a>", unsafe_allow_html=True)
                            
                            # [상세 정보]
                            with st.expander("📄 정보 및 사진"):
                                # 1. 텍스트 정보 (상단 배치)
                                for col in ['담당자', '전화번호', '이메일', '비고']:
                                    if col in df.columns and pd.notna(row[col]):
                                        st.write(f"**{col}:** {row[col]}")
                                
                                if '전화번호' in df.columns and pd.notna(row['전화번호']):
                                    st.link_button(f"📞 전화 걸기", f"tel:{row['전화번호']}", use_container_width=True)
                                
                                st.divider()
                                
                                # 2. 사진 (최하단 배치 및 크기 최소화)
                                img_url = row['이미지']
                                if pd.notna(img_url) and str(img_url).startswith('http'):
                                    st.write("📷 **현장 사진 (클릭 시 확대)**")
                                    # 사진 크기를 가로 120px로 고정하여 썸네일처럼 표시
                                    st.markdown(f'''
                                        <a href="{img_url}" target="_blank">
                                            <img src="{img_url}" style="width:120px; height:120px; object-fit:cover; border-radius:8px; border:1px solid #ddd;">
                                        </a>
                                    ''', unsafe_allow_html=True)
                                else:
                                    st.caption("등록된 사진 없음")

except Exception as e:
    st.error(f"오류: {e}")

st.caption("© 2026 거래처 관리 시스템")
