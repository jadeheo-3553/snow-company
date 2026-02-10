import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime  # 날짜 계산을 위해 추가

# ... (상단 스타일 설정 등은 동일하게 유지) ...

try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=url, ttl=0).fillna("")
    
    # [추가 로직] 날짜 데이터 형식 변환 (마지막 방문일 열이 있을 경우)
    if '마지막 방문일' in df.columns:
        df['마지막 방문일'] = pd.to_datetime(df['마지막 방문일'], errors='coerce')

    # ... (사이드바 및 탭 설정 동일) ...

    # 6. 리스트 출력 부분에서 '영업 알림' 추가
    rows = f_df.to_dict('records')
    for i in range(0, len(rows), 3):
        cols = st.columns(3)
        for j in range(3):
            if i + j < len(rows):
                item = rows[i + j]
                unique_id = f"client_{tab_name}_{i}_{j}_{item['거래처명']}"
                
                with cols[j]:
                    with st.container(border=True):
                        # 1) 영업 주기 알림 표시 (여기가 핵심입니다!)
                        if '마지막 방문일' in item and pd.notnull(item['마지막 방문일']):
                            last_date = item['마지막 방문일']
                            today = datetime.now()
                            diff = (today - last_date).days
                            
                            if diff >= 30:
                                st.error(f"⚠️ 마지막 방문 후 {diff}일 경과! (관리 필요)")
                            elif diff >= 20:
                                st.warning(f"🟡 마지막 방문 후 {diff}일 지남")
                            else:
                                st.success(f"✅ 방문 후 {diff}일 (양호)")
                        else:
                            st.info("ℹ️ 방문 기록 없음")

                        st.markdown(f'<p class="client-name-small">{item["거래처명"]}</p>', unsafe_allow_html=True)
                        
                        # ... (이하 태그, 주소, 상세 정보 코드는 동일하게 유지) ...
