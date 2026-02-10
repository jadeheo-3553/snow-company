import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 Pro", layout="wide")

# 2. 스타일 설정 (타이틀 잘림 해결 및 부서명 강조)
st.markdown("""
    <style>
    /* 상단 타이틀 잘림 방지: 여백과 높이 확보 */
    .title-area {
        padding: 50px 0 30px 0;
        text-align: center;
        width: 100%;
    }
    .main-title { 
        font-size: 2.2rem !important; 
        font-weight: bold; 
        color: #1E3A5F;
        margin: 0;
        display: block;
        line-height: 1.6;
    }
    
    /* 부서명 빨간색 & 레이아웃 */
    .dept-red { color: #e74c3c; font-weight: bold; font-size: 1rem; }
    .contact-card { 
        padding: 10px;
        border-bottom: 1px solid #f0f0f0;
        margin-bottom: 8px;
    }
    
    /* 썸네일 클릭 유도 스타일 */
    .thumb-text { font-size: 0.8rem; color: #888; margin-top: 4px; }
    </style>
    """, unsafe_allow_html=True)

# 초성 추출 함수
def get_chosung(text):
    if not text or pd.isna(text): return ""
    CHOSUNG_LIST = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
    char_code = ord(str(text)[0]) - 0xAC00
    if 0 <= char_code <= 11171: return CHOSUNG_LIST[char_code // 588]
    return str(text)[0].upper()

# 3. 데이터 로드
url = "https://docs.google.com/spreadsheets/d/1mo031g1DVN-pcJIXk3it6eLbJrSlezH0gIUnKHaQ698/edit?usp=sharing"

# 타이틀 출력 (CSS 클래스 적용)
st.markdown('<div class="title-area"><span class="main-title">🏢 거래처 통합 관리</span></div>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    # 4. 사이드바 (지역 필터 및 기능 추가)
    with st.sidebar:
        st.header("📍 상세 필터")
        # 지역별 필터
        all_regions = ["전체"] + sorted(df['주소'].apply(lambda x: x.split()[0]).unique().tolist())
        selected_region = st.selectbox("🌍 지역별 보기", all_regions)
        
        # 검색 기능
        search_q = st.text_input("🔍 거래처/주소 검색", placeholder="검색어를 입력하세요...")
        
        if st.button("🔄 필터 초기화"):
            st.rerun()

    # 5. 가나다 탭 필터 (디자인 유지)
    chosung_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    tabs = st.tabs(chosung_list)

    for idx, tab in enumerate(tabs):
        with tab:
            tab_name = chosung_list[idx]
            
            # 필터링 로직
            f_df = df.copy()
            if selected_region != "전체":
                f_df = f_df[f_df['주소'].str.startswith(selected_region)]
            
            if tab_name != "전체":
                if tab_name == "A-Z":
                    f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
                else:
                    f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == tab_name)]
            
            if search_q:
                f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]

            # 6. 결과 출력 (그리드 방식)
            rows = f_df.to_dict('records')
            for i in range(0, len(rows), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(rows):
                        item = rows[i + j]
                        with cols[j]:
                            with st.container(border=True):
                                # 즐겨찾기 없이 거래처명만 깔끔하게 노출
                                st.subheader(item['거래처명'])
                                
                                addr = item['주소']
                                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' style='font-size:0.85rem; color:#007bff; text-decoration:none;'>{addr}</a>", unsafe_allow_html=True)

                                with st.expander("👤 정보/메모 보기"):
                                    # 요청하신 담당자 레이아웃 (부서명 빨간색)
                                    depts = str(item.get('부서명', '')).split('\n')
                                    names = str(item.get('담당자', '')).split('\n')
                                    p_list = str(item.get('연락처', '')).split('\n')
                                    
                                    for k in range(max(len(depts), len(names), len(p_list))):
                                        d = depts[k].strip() if k < len(depts) else "-"
                                        n = names[k].strip() if k < len(names) else "-"
                                        p = p_list[k].strip() if k < len(p_list) else "-"
                                        
                                        st.markdown(f"""
                                        <div class="contact-card">
                                            <span class="dept-red">{k+1}. {d}</span><br>
                                            {n} / <a href="tel:{p}" style="color:#333; text-decoration:none;">{p}</a>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.text_area("📝 메모", key=f"memo_{item['거래처명']}_{tab_name}_{k}", height=60, label_visibility="collapsed")
                                    
                                    # [핵심] 클릭 시 즉시 확대되는 이미지
                                    img_url = item.get('이미지', '')
                                    if img_url:
                                        st.markdown("---")
                                        # use_container_width를 통해 클릭 시 즉시 전체화면 라이트박스 활성화
                                        st.image(img_url, caption="📷 클릭 시 즉시 확대", width=120, use_container_width=False)

except Exception as e:
    st.error(f"데이터 연결 오류: {e}")
