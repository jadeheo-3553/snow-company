import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리 시스템", page_icon="🏢", layout="wide")

# 2. 구글 시트 연결
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

st.subheader("🏢 거래처 통합 관리")

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0)
    df = df.sort_values(by='거래처명').reset_index(drop=True)

    # 3. 사이드바 검색
    with st.sidebar:
        st.header("🔍 검색")
        search_query = st.text_input("거래처명 검색", placeholder="예: 아주대학교")

    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False)]

    # 4. 리스트 출력 (텍스트 중심의 간결한 UI)
    if len(df) == 0:
        st.warning("검색 결과가 없습니다.")
    else:
        st.caption(f"총 {len(df)}개의 거래처가 있습니다.")
        
        # PC에서는 3열, 모바일은 1열 자동 전환
        for i in range(0, len(df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(df):
                    row = df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # [목록] 이미지를 빼고 텍스트만 배치하여 공간 절약
                            st.markdown(f"### {row['거래처명']}")
                            
                            # 주소 클릭 시 네이버 지도 연결
                            naver_url = f"https://map.naver.com/v5/search/{row['주소']}"
                            st.markdown(f"📍 <a href='{naver_url}' style='text-decoration:none; color:#4A90E2; font-weight:bold;'>{row['주소']}</a>", unsafe_allow_html=True)
                            
                            # 상세 정보 펼치기
                            with st.expander("📄 상세 정보 및 사진 확인"):
                                # 텍스트 정보를 상단에 배치
                                for col in ['담당자', '전화번호', '이메일', '비고']:
                                    if col in df.columns and pd.notna(row[col]):
                                        st.write(f"**{col}:** {row[col]}")
                                
                                # 전화 걸기 버튼
                                if '전화번호' in df.columns and pd.notna(row['전화번호']):
                                    st.link_button(f"📞 담당자 연결", f"tel:{row['전화번호']}", use_container_width=True)
                                
                                st.divider()
                                
                                # 사진을 가장 아래에 배치 (클릭 시 확대 링크 포함)
                                img_url = row['이미지']
                                if pd.notna(img_url) and str(img_url).startswith('http'):
                                    st.write("📷 **현장 사진 (클릭 시 확대)**")
                                    # 사진 클릭 시 새 창에서 원본 이미지가 뜨도록 마크다운 처리
                                    st.markdown(f'''
                                        <a href="{img_url}" target="_blank">
                                            <img src="{img_url}" style="width:100%; border-radius:10px;">
                                        </a>
                                    ''', unsafe_allow_html=True)
                                else:
                                    st.caption("등록된 현장 사진이 없습니다.")

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.caption("© 2026 거래처 관리 시스템 | 최종 업데이트: 2026-02-10")
