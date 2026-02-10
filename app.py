import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. 페이지 설정
st.set_page_config(page_title="거래처 관리 시스템", layout="wide")

# 2. 스타일 설정 (타이틀 잘림 방지 및 레이아웃 최적화)
st.markdown("""
    <style>
    /* 타이틀 영역 강제 여백 확보 (잘림 방지) */
    .title-wrapper {
        padding: 40px 0 20px 0;
        text-align: center;
    }
    .main-title { 
        font-size: 2rem !important; 
        font-weight: bold; 
        color: #1E3A5F;
        display: block;
    }
    
    /* 부서명 빨간색 및 담당자 정보 레이아웃 */
    .dept-red { color: #e74c3c; font-weight: bold; font-size: 1rem; }
    .contact-row { margin-bottom: 12px; border-bottom: 1px solid #eee; padding-bottom: 5px; }
    
    /* 썸네일 스타일 */
    .img-caption { font-size: 0.8rem; color: #666; margin-top: 5px; }
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

# 타이틀 (여백 넉넉히 확보)
st.markdown('<div class="title-wrapper"><span class="main-title">🏢 거래처 통합 관리</span></div>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    # 4. 사이드바 구성 (모바일 환경 고려)
    with st.sidebar:
        st.header("📍 상세 필터")
        # 지역별 필터 기능 추가
        region_list = ["전체"] + sorted(df['주소'].apply(lambda x: x.split()[0]).unique().tolist())
        selected_region = st.selectbox("🌍 지역별 보기", region_list)
        
        # 검색어 입력
        search_q = st.text_input("🔍 거래처/주소 검색", placeholder="입력 후 엔터...")
        
        if st.button("🔄 필터 초기화"):
            st.rerun()

    # 5. 메인 화면 - 가나다 탭 필터 (디자인 유지)
    chosung_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    tabs = st.tabs(chosung_list)

    for idx, tab in enumerate(tabs):
        with tab:
            tab_name = chosung_list[idx]
            
            # 데이터 필터링 로직
            f_df = df.copy()
            
            # 지역 필터 적용
            if selected_region != "전체":
                f_df = f_df[f_df['주소'].str.startswith(selected_region)]
            
            # 가나다 필터 적용
            if tab_name != "전체":
                if tab_name == "A-Z":
                    f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
                else:
                    f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == tab_name)]
            
            # 검색어 적용
            if search_q:
                f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False) | f_df['주소'].str.contains(search_q, na=False)]

            # 6. 리스트 출력 (3열 그리드)
            rows = f_df.to_dict('records')
            if not rows:
                st.info("조건에 맞는 거래처가 없습니다.")
            
            for i in range(0, len(rows), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(rows):
                        item = rows[i + j]
                        with cols[j]:
                            with st.container(border=True):
                                # 거래처명 (즐겨찾기 삭제로 심플해짐)
                                st.markdown(f"### {item['거래처명']}")
                                
                                addr = item['주소']
                                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' style='font-size:0.85rem; color:#007bff; text-decoration:none;'>{addr}</a>", unsafe_allow_html=True)

                                with st.expander("👤 정보/메모 상세보기"):
                                    # 담당자 정보 레이아웃
                                    depts = str(item.get('부서명', '')).split('\n')
                                    names = str(item.get('담당자', '')).split('\n')
                                    p_list = str(item.get('연락처', '')).split('\n')
                                    
                                    for k in range(max(len(depts), len(names), len(p_list))):
                                        d = depts[k].strip() if k < len(depts) else "-"
                                        n = names[k].strip() if k < len(names) else "-"
                                        p = p_list[k].strip() if k < len(p_list) else "-"
                                        
                                        st.markdown(f"""
                                        <div class="contact-row">
                                            <span class="dept-red">{k+1}. {d}</span><br>
                                            {n} / <a href="tel:{p}" style="color:#333; text-decoration:none;">{p}</a>
                                        </div>
                                        """, unsafe_allow_html=True)
                                        st.text_area("📝 메모 기록", key=f"m_{item['거래처명']}_{tab_name}_{k}", height=70, label_visibility="collapsed")
                                    
                                    # [핵심] 이미지 썸네일 및 클릭 시 확대
                                    img_url = item.get('이미지', '')
                                    if img_url:
                                        st.markdown("---")
                                        # use_container_width=True와 width 설정을 조합하여 썸네일로 보이고, 클릭 시 확대 지원
                                        st.image(img_url, caption="📷 사진 클릭 시 확대", width=120)

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
