import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import sys

# 1. 시스템 설정
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')
st.set_page_config(page_title="거래처 관리", page_icon="🏢", layout="wide")

# 스타일 설정: 리스트 가독성 향상
st.markdown("""
    <style>
    .small-title { font-size: 1.4rem !important; font-weight: bold; margin-bottom: 10px; }
    .contact-item { 
        background-color: #ffffff; 
        padding: 10px; 
        border: 1px solid #eee; 
        border-radius: 5px; 
        margin-bottom: 8px; 
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
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

    # 검색창 상단 배치
    search_query = st.text_input("🔍 검색창", placeholder="거래처명 또는 주소 입력...")

    if search_query:
        df = df[df['거래처명'].str.contains(search_query, case=False, na=False) | 
                df['주소'].str.contains(search_query, case=False, na=False)]

    # 4. 리스트 출력
    if len(df) == 0:
        st.warning("데이터를 찾을 수 없습니다.")
    else:
        for i in range(0, len(df), 3):
            cols = st.columns(3)
            for j in range(3):
                if i + j < len(df):
                    row = df.iloc[i + j]
                    with cols[j]:
                        with st.container(border=True):
                            st.markdown(f"### {row['거래처명']}")
                            
                            # 주소 및 지도 링크
                            addr = row['주소']
                            naver_url = f"https://map.naver.com/v5/search/{addr}"
                            st.markdown(f"📍 <a href='{naver_url}' style='text-decoration:none; color:#4A90E2; font-weight:bold;'>{addr}</a>", unsafe_allow_html=True)
                            
                            with st.expander("👤 담당자 연락처 보기"):
                                # B, C, D열 데이터 분리
                                depts = str(row['부서']).split('\n') if pd.notna(row['부서']) else []
                                names = str(row['담당자']).split('\n') if pd.notna(row['담당자']) else []
                                phones = str(row['연락처']).split('\n') if pd.notna(row['연락처']) else []
                                
                                max_count = max(len(depts), len(names), len(phones))
                                
                                copy_list = [] # 복사용 텍스트 저장
                                
                                for idx in range(max_count):
                                    d = depts[idx].strip() if idx < len(depts) else "-"
                                    n = names[idx].strip() if idx < len(names) else "-"
                                    p = phones[idx].strip() if idx < len(phones) else "-"
                                    
                                    # 화면 출력용
                                    st.markdown(f"""
                                    <div class="contact-item">
                                        <strong>{idx+1}. {d}</strong><br>
                                        👤 {n} | 📞 {p}
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    copy_list.append(f"{idx+1}. {d} / {n} / {p}")

                                st.divider()
                                
                                # 복사 기능 (거래처명/주소 제외하고 연락처만)
                                if copy_list:
                                    st.caption("📋 연락처 정보 복사")
                                    st.code("\n".join(copy_list), language=None)

                                # 이미지 하단 배치
                                img_url = row['이미지']
                                if pd.notna(img_url) and str(img_url).startswith('http'):
                                    st.markdown(f'<br><a href="{img_url}" target="_blank"><img src="{img_url}" style="width:100px; border-radius:5px;"></a>', unsafe_allow_html=True)
                                    st.caption("사진 클릭 시 확대")

except Exception as e:
    st.error(f"데이터 로드 중 오류 발생: {e}")

st.caption("© 2026 거래처 관리 시스템 | 스노우님 전용")
