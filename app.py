import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", layout="wide")

# 2. 스타일 설정 (거래처명 축소 및 타이틀 정렬)
st.markdown("""
    <style>
    /* 타이틀 잘림 방지 및 중앙 정렬 */
    .title-area {
        padding: 45px 0 20px 0;
        text-align: center;
    }
    .main-title { 
        font-size: 1.8rem !important; 
        font-weight: bold; 
        color: #1E3A5F;
    }
    
    /* [요청] 거래처명 글자 크기 반으로 축소 */
    .client-name-small {
        font-size: 1.0rem !important; /* 기존보다 절반 크기 */
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
    }
    
    /* 부서명 빨간색 강조 */
    .dept-red { color: #e74c3c; font-weight: bold; font-size: 0.9rem; }
    .contact-card { 
        padding: 8px;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 5px;
    }

    /* 이미지 썸네일 스타일 */
    .img-thumbnail {
        cursor: zoom-in;
        border-radius: 5px;
        border: 1px solid #ddd;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def get_chosung(text):
    if not text or pd.isna(text): return ""
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    char_code = ord(str(text)[0]) - 0xAC00
    if 0 <= char_code <= 11171: return CHOSUNG_LIST[char_code // 588]
    return str(text)[0].upper()

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"
st.markdown('<div class="title-area"><span class="main-title">🏢 거래처 통합 관리</span></div>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    # 4. 사이드바 (지역 필터)
    with st.sidebar:
        st.header("📍 상세 검색")
        regions = ["전체"] + sorted(df['주소'].apply(lambda x: x.split()[0]).unique().tolist())
        sel_region = st.selectbox("🌍 지역 선택", regions)
        search_q = st.text_input("🔍 거래처명 검색", placeholder="검색어 입력...")

    # 5. 가나다 탭 필터
    chosung_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    tabs = st.tabs(chosung_list)

    for idx, tab in enumerate(tabs):
        with tab:
            tab_name = chosung_list[idx]
            f_df = df.copy()
            
            if sel_region != "전체":
                f_df = f_df[f_df['주소'].str.startswith(sel_region)]
            if tab_name != "전체":
                if tab_name == "A-Z":
                    f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
                else:
                    f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == tab_name)]
            if search_q:
                f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False)]

            # 6. 리스트 출력
            rows = f_df.to_dict('records')
            for i in range(0, len(rows), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(rows):
                        item = rows[i + j]
                        with cols[j]:
                            with st.container(border=True):
                                # [요청 해결] 거래처명 크기 축소 적용
                                st.markdown(f'<p class="client-name-small">{item["거래처명"]}</p>', unsafe_allow_html=True)
                                
                                addr = item['주소']
                                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' style='font-size:0.8rem; color:#007bff; text-decoration:none;'>{addr}</a>", unsafe_allow_html=True)

                                with st.expander("👤 정보/메모"):
                                    depts = str(item.get('부서명', '')).split('\n')
                                    names = str(item.get('담당자', '')).split('\n')
                                    phones = str(item.get('연락처', '')).split('\n')
                                    
                                    for k in range(max(len(depts), len(names), len(phones))):
                                        d = depts[k].strip() if k < len(depts) else "-"
                                        n = names[k].strip() if k < len(names) else "-"
                                        p = phones[k].strip() if k < len(phones) else "-"
                                        
                                        st.markdown(f"""
                                        <div class="contact-card">
                                            <span class="dept-red">{k+1}. {d}</span><br>
                                            {n} / <a href="tel:{p}" style="color:#333; text-decoration:none;">{p}</a>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.text_area("📝 메모", key=f"m_{item['거래처명']}_{tab_name}_{k}", height=60, label_visibility="collapsed")
                                    
                                    img_url = item.get('이미지', '')
                                    if img_url:
                                        st.markdown("---")
                                        st.markdown(f"""
                                            <a href="{img_url}" target="_blank">
                                                <img src="{img_url}" class="img-thumbnail" width="100">
                                            </a>
                                            <p style="font-size:0.7rem; color:gray;">▲ 클릭 시 확대</p>
                                        """, unsafe_allow_html=True)

except Exception as e:
    st.error(f"오류: {e}")
