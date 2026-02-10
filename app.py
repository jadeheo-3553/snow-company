import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리 매니저", page_icon="🏢", layout="wide")

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

    # 4. 리스트 출력
    if len(df) == 0:
        st.warning("데이터가 없습니다.")
    else:
        st.caption(f"총 {len(df)}개의 거래처가 검색되었습니다.")
        
        # PC에서는 3열, 모바일은 1열로 자동 전환
        for i in range(0, len(df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(df):
                    row = df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            # [변화 1] 가로 배치 레이아웃 (이미지 1 : 텍스트 3 비율)
                            c1, c2 = st.columns([1, 3])
                            
                            img_url = row['이미지']
                            display_img = img_url if pd.notna(img_url) and str(img_url).startswith('http') else "https://via.placeholder.com/150/f0f2f6/666666?text=No"
                            
                            with c1:
                                # 썸네일 크기 최적화
                                st.markdown(f'<img src="{display_img}" style="width:100%; height:70px; object-fit:cover; border-radius:8px;">', unsafe_allow_html=True)
                            
                            with c2:
                                st.markdown(f"**{row['거래처명']}**")
                                # [변화 2] 주소 클릭 시 지도 바로 연결 (하이퍼링크 처리)
                                naver_url = f"https://map.naver.com/v5/search/{row['주소']}"
                                st.markdown(f"📍 <a href='{naver_url}' style='text-decoration:none; color:gray; font-size:0.9rem;'>{row['주소']}</a>", unsafe_allow_html=True)

                            # [변화 3] 상세 정보 펼치면 큰 사진 등장
                            with st.expander("📂 상세 정보 / 사진 확대"):
                                st.image(display_img, caption=f"{row['거래처명']} 전경", use_container_width=True)
                                st.divider()
                                for col in ['담당자', '전화번호', '이메일', '비고']:
                                    if col in df.columns and pd.notna(row[col]):
                                        st.write(f"**{col}:** {row[col]}")
                                
                                # 모바일용 큰 전화 버튼
                                if '전화번호' in df.columns and pd.notna(row['전화번호']):
                                    st.link_button(f"📞 담당자 전화 걸기", f"tel:{row['전화번호']}", use_container_width=True)

except Exception as e:
    st.error(f"오류가 발생했습니다: {e}")

st.markdown("---")
st.caption("© 2026 거래처 관리 시스템")
