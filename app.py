import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. 페이지 설정
st.set_page_config(page_title="세창 거래처 맵 Pro", layout="wide")

# 2. 스타일 설정 (제목 크기 축소 및 여백 최적화)
st.markdown("""
    <style>
    .block-container { padding-top: 1.5rem !important; } /* 상단 여백 추가 축소 */
    
    .title-area { 
        padding: 15px 0 10px 0; /* 위아래 여백 축소 */
        text-align: center; 
        width: 100%; 
    }
    
    /* 제목 크기를 1.8 -> 1.4로 줄여 탭이 밀리지 않게 조정 */
    .main-title { 
        font-size: 1.4rem !important; 
        font-weight: bold; 
        color: #1E3A5F; 
        line-height: 1.2; 
        display: block; 
        letter-spacing: -0.5px; /* 글자 간격 살짝 좁힘 */
    }
    
    .client-name-small { font-size: 1.0rem !important; font-weight: bold; color: #333; margin-top: 5px; margin-bottom: 2px; }
    .item-tag { display: inline-block; background-color: #e1f5fe; color: #01579b; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; margin-right: 4px; font-weight: bold; }
    .dept-red { color: #e74c3c; font-weight: bold; font-size: 0.9rem; }
    .info-box { background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: 10px; border-left: 4px solid #1E3A5F; }
    .info-title { font-size: 0.85rem; font-weight: bold; color: #555; margin-bottom: 3px; }
    .info-content { font-size: 0.85rem; color: #333; margin-bottom: 8px; }
    .contact-card { padding: 8px; border-bottom: 1px solid #f0f0f0; margin-bottom: 5px; }
    .img-thumbnail { cursor: zoom-in; border-radius: 5px; border: 1px solid #ddd; margin-top: 5px; }
    
    /* 탭 간격 살짝 조정 (모바일 가독성) */
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
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

# 제목 출력 영역
st.markdown('<div class="title-area"><span class="main-title">🏢 세창 거래처 통합 관리 시스템</span></div>', unsafe_allow_html=True)

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")

    if '마지막 방문일' in df.columns:
        df['마지막 방문일'] = pd.to_datetime(df['마지막 방문일'], errors='coerce')

    # 4. 사이드바
    with st.sidebar:
        st.header("📍 상세 검색")
        if st.button("🔄 데이터 최신화"):
            st.cache_data.clear()
            st.rerun()
        
        regions = ["전체"] + sorted(df['주소'].apply(lambda x: str(x).split()[0] if x else "").unique().tolist())
        sel_region = st.selectbox("🌍 지역 선택", [r for r in regions if r])
        search_q = st.text_input("🔍 거래처명 검색", placeholder="검색어 입력...")

    # 5. 가나다 탭
    chosung_list = ["전체", "ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ", "A-Z"]
    tabs = st.tabs(chosung_list)

    for idx, tab in enumerate(tabs):
        with tab:
            tab_name = chosung_list[idx]
            f_df = df.copy()
            if sel_region != "전체": f_df = f_df[f_df['주소'].str.startswith(sel_region)]
            if tab_name != "전체":
                if tab_name == "A-Z": f_df = f_df[f_df['거래처명'].str.contains(r'^[a-zA-Z]', na=False)]
                else: f_df = f_df[f_df['거래처명'].apply(lambda x: get_chosung(x) == tab_name)]
            if search_q: f_df = f_df[f_df['거래처명'].str.contains(search_q, na=False)]

            rows = f_df.to_dict('records')
            for i in range(0, len(rows), 3):
                cols = st.columns(3)
                for j in range(3):
                    if i + j < len(rows):
                        item = rows[i + j]
                        unique_id = f"cl_{tab_name}_{idx}_{i}_{j}"
                        
                        with cols[j]:
                            with st.container(border=True):
                                # 영업 주기 알림
                                if '마지막 방문일' in item and pd.notnull(item['마지막 방문일']):
                                    last_date = item['마지막 방문일'].to_pydatetime()
                                    today = datetime.now()
                                    diff = (today - last_date).days
                                    if diff >= 30: st.error(f"🚨 {diff}일 경과")
                                    elif diff >= 20: st.warning(f"🟡 {diff}일 지남")
                                    else: st.success(f"✅ {diff}일 (안정)")
                                else: st.info("ℹ️ 방문 기록 없음")

                                st.markdown(f'<p class="client-name-small">{item["거래처명"]}</p>', unsafe_allow_html=True)
                                
                                if '취급품목' in item and item['취급품목']:
                                    tag_html = "".join([f'<span class="item-tag">{t.strip()}</span>' for t in str(item['취급품목']).split(',')])
                                    st.markdown(f'<div>{tag_html}</div>', unsafe_allow_html=True)

                                addr = item['주소']
                                st.markdown(f"📍 <a href='https://map.naver.com/v5/search/{addr}' target='_blank' style='font-size:0.8rem; color:#007bff; text-decoration:none;'>{addr}</a>", unsafe_allow_html=True)

                                with st.expander("👤 상세 정보/메모"):
                                    depts, names, phones = str(item.get('부서명','')).split('\n'), str(item.get('담당자','')).split('\n'), str(item.get('연락처','')).split('\n')
                                    for k in range(max(len(depts), len(names), len(phones))):
                                        d, n, p = (depts[k] if k<len(depts) else "-"), (names[k] if k<len(names) else "-"), (phones[k] if k<len(phones) else "-")
                                        st.markdown(f'<div class="contact-card"><span class="dept-red">{k+1}. {d}</span><br>{n} / <a href="tel:{p}" style="color:#333; text-decoration:none;">{p}</a></div>', unsafe_allow_html=True)
                                    
                                    parking = item.get('주차 및 진입 정보', '정보 없음')
                                    issue = item.get('거래처 성향 / 특이사항', '내용 없음')
                                    
                                    st.markdown(f"""
                                    <div class="info-box">
                                        <div class="info-title">🚗 주차 및 진입 정보</div>
                                        <div class="info-content">{parking if parking else "정보 없음"}</div>
                                        <div class="info-title">⚠️ 거래처 성향/특이사항</div>
                                        <div class="info-content">{issue if issue else "내용 없음"}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    st.text_area("📝 메모 기록", key=f"memo_{unique_id}", height=70)

                                    st.markdown("---")
                                    uploaded_file = st.file_uploader(f"📷 사진 업로드", type=['jpg', 'png', 'jpeg'], key=f"up_{unique_id}")
                                    if uploaded_file:
                                        st.image(uploaded_file, caption="업로드 사진", use_container_width=True)

                                    img_url = item.get('이미지', '')
                                    if img_url:
                                        st.markdown(f'<a href="{img_url}" target="_blank"><img src="{img_url}" class="img-thumbnail" width="100"></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"오류: {e}")
