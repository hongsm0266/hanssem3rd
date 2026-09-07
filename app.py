@st.cache_data(ttl=60) # API 한도 차단 방지를 위해 60초 유지
def load_perf_sheet(_gc_client):
    try:
        # 🚀 [핵심 수정] B30:AG70 -> B32:AG200 으로 넉넉하게 변경!
        # 인원이 매일 늘거나 줄어도 B32행부터 최대 200행(충분히 넉넉한 공간)까지 전부 스캔합니다.
        data = _gc_client.open(SHEET_NAME).worksheet("시트1").get("B32:AG200")
        if data:
            # 혹시 빈 칸이 있어서 에러가 나지 않도록 열 길이(32열)를 안전하게 맞춰줍니다.
            safe_rows = [r + [''] * (32 - len(r)) for r in data]
            return pd.DataFrame(safe_rows)
        return pd.DataFrame()
    except Exception as e:
        # 혹시 구글 API 한도 초과 등으로 에러가 나면 화면에 알려주도록 추가
        st.toast(f"VDT 데이터를 가져오지 못했습니다 (API 한도 또는 시트 오류): {e}", icon="⚠️")
        return pd.DataFrame()
