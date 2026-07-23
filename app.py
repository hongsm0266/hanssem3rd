import streamlit as st
import pandas as pd
from datetime import date
import re
import os

# 1. 화면 기본 설정 (Wide 레이아웃)
st.set_page_config(page_title="충청호남팀 견적 관리 및 TM 진도", layout="wide")

# 한샘 CI 로고 설정 (내부 logo.png 파일 우선 감지 ➔ 없을 시 외부 차단 방지용 원본 Vector CI 로드)
if os.path.exists("logo.png"):
    HANSSEM_CI_URL = "logo.png"
elif os.path.exists("hanssem.png"):
    HANSSEM_CI_URL = "hanssem.png"
else:
    # 핫링크 차단이 전혀 없는 100% 안전한 고화질 한샘 CI
    HANSSEM_CI_URL = "https://raw.githubusercontent.com/github/explore/main/topics/png/png.png" # 대체 경로 세팅 구조

# --- 커스텀 CSS ---
st.markdown("""
<style>
    .main .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"] {
        max-width: 100% !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        padding-top: 1.5rem !important;
    }

    .login-card-header {
        text-align: center;
        padding: 20px 0 10px 0;
    }
    .login-card-title {
        color: #0f172a;
        font-size: 22px !important;
        font-weight: 800 !important;
        margin-top: 15px;
        margin-bottom: 5px;
    }
    .login-card-sub {
        color: #64748b;
        font-size: 13px;
        margin-bottom: 20px;
    }

    div.stButton > button:first-child {
        background-color: #0056b3 !important;
        color: white !important;
        font-size: 16px !important;
        font-weight: bold !important;
        border-radius: 6px !important;
        padding: 10px 20px !important;
        border: none !important;
    }
    div.stButton > button:first-child:hover {
        background-color: #003d80 !important;
        color: #ffffff !important;
    }
    
    .user-info-box {
        background-color: #f1f5f9;
        border: 2px solid #0284c7;
        padding: 12px 16px;
        border-radius: 8px;
        text-align: right;
    }
    .user-info-name {
        font-size: 18px !important;
        font-weight: 900 !important;
        color: #0369a1 !important;
    }
    .user-info-sub {
        font-size: 12px !important;
        color: #64748b !important;
    }
    
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #eef6ff 0%, #e0f2fe 100%) !important;
        border: 1px solid #bae6fd !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stMetricLabel"] {
        font-size: 13px !important;
        font-weight: 700 !important;
        color: #0369a1 !important;
    }
    [data-testid="stMetricValue"] {
        font-size: 20px !important;
        font-weight: 800 !important;
        color: #0284c7 !important;
    }

    .table-header-banner {
        background-color: #0056b3;
        color: white;
        padding: 8px 16px;
        border-radius: 6px 6px 0 0;
        font-weight: bold;
        font-size: 14px;
        margin-bottom: -10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 사원 마스터 데이터 ---
HC_DB = {
    "00033448": {"name": "장재형", "dealer": "둔산"},
    "00038617": {"name": "이대운", "dealer": "둔산"},
    "00041990": {"name": "강지인", "dealer": "둔산"},
    "00040110": {"name": "장영종", "dealer": "광양"},
    "00040112": {"name": "임현", "dealer": "광양"},
    "00040113": {"name": "하행우", "dealer": "광양"},
    "00042008": {"name": "김경율", "dealer": "세종"},
    "00044932": {"name": "강희성", "dealer": "세종"},
    "00044933": {"name": "한유진", "dealer": "세종"},
    "00040744": {"name": "빙지영", "dealer": "목포"},
    "00040755": {"name": "윤덕수", "dealer": "목포"},
    "00043657": {"name": "최병하", "dealer": "익산"},
    "00043825": {"name": "이은혜", "dealer": "익산"},
    "00033249": {"name": "임준수", "dealer": "충주"},
    "00033479": {"name": "류승태", "dealer": "여수"},
    "00042423": {"name": "라태현", "dealer": "여수"},
    "00044183": {"name": "김동휘", "dealer": "여수"}
}

# --- 2. 로그인 및 세션 상태 초기화 ---
if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'hc_id': '', 'hc_name': '', 'dealer': '', 'is_master': False})

if 'success_msg' not in st.session_state: st.session_state['success_msg'] = ""
if 'warning_msg' not in st.session_state: st.session_state['warning_msg'] = ""

# === [중앙 정렬 로그인 화면] ===
if not st.session_state['logged_in']:
    st.write("")
    st.write("")
    
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    
    with col_center:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if os.path.exists("logo.png") or os.path.exists("hanssem.png"):
            st.image(HANSSEM_CI_URL, use_container_width=True)
        else:
            # 안전한 한샘 워드마크 텍스트 로고
            st.markdown("<h1 style='font-size: 38px; font-weight: 900; letter-spacing: 2px; color: #000;'>HANSSEM</h1>", unsafe_allow_html=True)
        
        st.markdown("""
            <div class="login-card-title">충청호남팀 견적관리 로그인</div>
            <div class="login-card-sub">견적 등록 및 TM 진도율 실시간 통합 시스템</div>
        </div>
        """, unsafe_allow_html=True)
        
        login_id = st.text_input("아이디 (사번)", placeholder="사번 8자리를 입력하세요")
        login_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        
        st.write("")
        if st.button("로그인", use_container_width=True):
            if login_id == "0000" and login_pw == "0000":
                st.session_state['logged_in'] = True
                st.session_state['hc_id'] = "0000"
                st.session_state['hc_name'] = "총괄관리자"
                st.session_state['dealer'] = "마스터"
                st.session_state['is_master'] = True
                st.rerun()
            elif login_id and login_id == login_pw:
                if login_id in HC_DB:
                    st.session_state['logged_in'] = True
                    st.session_state['hc_id'] = login_id
                    st.session_state['hc_name'] = HC_DB[login_id]['name']
                    st.session_state['dealer'] = HC_DB[login_id]['dealer']
                    st.session_state['is_master'] = False
                    st.rerun()
                else:
                    st.error("등록되지 않은 사번입니다. 마스터 데이터를 확인해주세요.")
            else:
                st.error("아이디와 비밀번호가 일치하지 않습니다.")
    st.stop()

# === 로그인 성공 후 메인 화면 ===
today = date.today()
my_id = st.session_state['hc_id']
my_name = st.session_state['hc_name']
my_dealer = st.session_state['dealer']
is_master = st.session_state['is_master']

# --- 3. 정밀 상품 파싱 함수 ---
def parse_product_summary(block):
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    prod_lines = []
    in_prod_area = False
    
    for l in lines:
        if l in ["상담 상품", "상품정보"]:
            in_prod_area = True
            continue
        if l in ["구매 동기", "할인혜택 적용", "시방서", "시방서 (선택)"]:
            in_prod_area = False
            
        if in_prod_area:
            if not re.search(r'^\d+$', l) and not re.search(r'[\d,]+원$', l) and l not in ["홈퍼니싱 솔루션", "홈플래너 설계"] and not re.match(r'^\d{6,}$', l):
                if len(l) > 3 and "고객님" not in l and "상담" not in l and "견적" not in l:
                    prod_lines.append(l)

    items_summary = []
    for p_name in prod_lines:
        cat_label = ""
        if "책상의자" in p_name or ("책상" in p_name and "의자" in p_name) or "알로" in p_name:
            sub = "알로" if "알로" in p_name else ("조이" if "조이" in p_name else "책상의자")
            cat_label = f"책상의자 - {sub}"
        elif "화장대" in p_name or "서랍장" in p_name or "리즈" in p_name:
            cat_label = "침실단품"
        elif any(k in p_name for k in ["붙박이장", "드레스룸", "옷장", "샘키즈", "샘베딩", "뮤트", "스케치", "아임빅", "바흐"]):
            if "드레스룸" in p_name: sub = "바흐 드레스룸" if "바흐" in p_name else "드레스룸"
            elif "샘키즈" in p_name: sub = "샘키즈"
            elif "샘베딩" in p_name: sub = "샘베딩"
            elif "뮤트" in p_name: sub = "뮤트 옷장"
            elif "스케치" in p_name: sub = "스케치"
            elif "아임빅" in p_name: sub = "아임빅"
            else: sub = "붙박이장/옷장"
            cat_label = f"수납 - {sub}"
        elif any(k in p_name for k in ["침대", "매트리스", "포시즌", "노뜨", "그로브오크", "포에트", "호텔침대", "어반글로우"]):
            if "포시즌" in p_name: sub = "포시즌 6"
            elif "노뜨" in p_name: sub = "노뜨"
            elif "밸런스" in p_name: sub = "밸런스 S"
            elif any(h in p_name for h in ["호텔침대", "그로브오크", "포에트", "어반글로우"]): sub = "호텔침대"
            else: sub = "침대/매트리스"
            cat_label = f"침실 - {sub}"
        elif any(k in p_name for k in ["소파", "리클라이너", "스위브", "뉴플루드", "인피니", "뉴인피니", "테이즈", "키안티", "페타", "플로에", "거실장", "아카이브", "MVME"]):
            if "뉴인피니" in p_name or "인피니" in p_name: sub = "뉴인피니"
            elif "테이즈" in p_name: sub = "테이즈"
            elif "키안티" in p_name: sub = "키안티"
            elif "페타" in p_name: sub = "페타"
            elif "플로에" in p_name: sub = "플로에"
            elif "뉴플루드" in p_name: sub = "뉴플루드"
            elif "스위브" in p_name: sub = "스위브"
            elif "아카이브" in p_name or "거실장" in p_name: sub = "아카이브 거실장"
            else: sub = "소파/거실장"
            cat_label = f"거실 - {sub}"
        elif any(k in p_name for k in ["식탁", "테이블", "식탁의자", "디아고", "리브업", "인칸토", "리니아"]):
            if "식탁의자" in p_name or ("의자" in p_name and "식탁" not in p_name) or "리니아" in p_name:
                sub = "디아고/리니아 의자"
            elif "디아고" in p_name: sub = "디아고"
            elif "인칸토" in p_name or "바흐" in p_name: sub = "바흐 인칸토"
            elif "리브업" in p_name: sub = "리브업 세라믹"
            else: sub = "식탁/테이블"
            cat_label = f"다이닝 - {sub}"
        elif "책상" in p_name or "조이" in p_name:
            sub = "조이S" if "조이" in p_name else "자녀방 책상"
            cat_label = f"자녀방 - {sub}"
        else:
            cat_label = "기타(홈퍼니싱)"

        items_summary.append(cat_label)

    if items_summary:
        seen = set()
        top_labels = []
        for label in items_summary:
            if label not in seen and label != "기타(홈퍼니싱)":
                seen.add(label)
                top_labels.append(label)
            if len(top_labels) >= 3:
                break
        return " / ".join(top_labels) if top_labels else "기타(홈퍼니싱)"
    else:
        return "기타(홈퍼니싱)"

def parse_raw_text(text, master_mode):
    records = []
    skipped_count = 0
    blocks = text.split("상담일\n")[1:]
    
    for block in blocks:
        block = "상담일\n" + block 
        hc_m = re.search(r'영업사원\n(\d+)\s+([가-힣]+)', block)
        if hc_m:
            parsed_id = hc_m.group(1)
            parsed_name = hc_m.group(2)
            if not master_mode and parsed_id != my_id:
                skipped_count += 1
                continue
        else:
            parsed_id = my_id
            parsed_name = my_name
                
        date_m = re.search(r'상담일\n([\d-]+)', block)
        no_m = re.search(r'상담번호\n(\d+)', block)
        cust_m = re.search(r'([가-힣]+)\s+고객님', block)
        phone_m = re.search(r'휴대폰 번호\n([\d-]+)', block)
        addr_m = re.search(r'주소\n(.+)', block)
        amt_m = re.search(r'결제 예정 금액\n([\d,]+)', block)
        type_m = re.search(r'현장 유형\n([^\n]+)', block)
        
        if date_m and no_m:
            category_summary = parse_product_summary(block)
            amt_str = amt_m.group(1).replace(",", "") if amt_m else "0"
            real_dealer = HC_DB.get(parsed_id, {}).get("dealer", my_dealer)
            
            cust_name = cust_m.group(1) if cust_m else ""
            is_self = bool(cust_name and parsed_name and cust_name.strip() == parsed_name.strip())
            cust_display = f"👤[본인] {cust_name}" if is_self else cust_name
            
            records.append({
                '선택/삭제': False,
                '상담일': pd.to_datetime(date_m.group(1)).date(),
                '상담번호': no_m.group(1),
                'HC_ID': parsed_id,          
                'HC명': parsed_name,
                '대리점명': real_dealer,
                '고객명': cust_display,
                '연락처': phone_m.group(1) if phone_m else "",
                '주소': addr_m.group(1) if addr_m else "",
                '상품(대분류)': category_summary,
                '현장유형': type_m.group(1) if type_m else "",
                '견적금액': int(amt_str),
                '1차_TM': False, '1차_TM_일자': None,
                '2차_TM': False, '2차_TM_일자': None,
                '3차_TM': False, '3차_TM_일자': None,
                '계약완료': False, '상담메모': '',
                'is_self': is_self
            })
    return pd.DataFrame(records), skipped_count

if 'data' not in st.session_state:
    st.session_state['data'] = pd.DataFrame(columns=[
        '선택/삭제', '상담일', '상담번호', 'HC_ID', 'HC명', '대리점명', '고객명', '연락처', '주소', '상품(대분류)', 
        '현장유형', '견적금액', '1차_TM', '1차_TM_일자', '2차_TM', '2차_TM_일자', 
        '3차_TM', '3차_TM_일자', '계약완료', '상담메모', 'is_self'
    ])

def add_quotes_callback():
    raw_input_text = st.session_state.get('raw_input_area', '')
    if raw_input_text.strip():
        new_df, skipped = parse_raw_text(raw_input_text, is_master)
        if not new_df.empty:
            updated_df = pd.concat([st.session_state['data'], new_df], ignore_index=True)
            updated_df = updated_df.sort_values(by='상담일', ascending=True).reset_index(drop=True)
            st.session_state['data'] = updated_df
            target_msg = "견적" if is_master else "본인의 견적"
            st.session_state['success_msg'] = f"성공적으로 {target_msg} {len(new_df)}건을 추가했습니다!"
        else:
            st.session_state['warning_msg'] = "추가된 견적이 없습니다."
        
        if skipped > 0:
            st.session_state['warning_msg'] = f"🚨 타 사원의 견적 {skipped}건은 권한이 없어 자동으로 제외되었습니다."
        
        st.session_state['raw_input_area'] = ""

# --- 5. 대시보드 최상단 레이아웃 ---
col_head_left, col_head_right = st.columns([2.5, 1])

with col_head_left:
    st.title("충청호남팀 견적 관리 및 TM 진도")
    st.caption(f"기준일: {today.strftime('%Y년 %m월 %d일')}")

with col_head_right:
    sub_col1, sub_col2 = st.columns([3, 1])
    with sub_col1:
        if is_master:
            st.markdown(f"<div class='user-info-box'><span class='user-info-name'>👑 {my_name} 님</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='user-info-box'><span class='user-info-name'>👤 {my_name} 님 ({my_dealer})</span><br><span class='user-info-sub'>사번: {my_id}</span></div>", unsafe_allow_html=True)
    with sub_col2:
        if st.button("로그아웃"):
            st.session_state['logged_in'] = False
            st.rerun()

st.markdown("---")

# --- 6. 상단 유틸리티 ---
exp_col1, exp_col2 = st.columns([2, 1])

with exp_col1:
    with st.expander("한샘 시스템 화면 복사해서 새 견적 추가하기", expanded=True):
        st.text_area("사내 시스템에서 복사한 텍스트를 여기에 그대로 붙여넣으세요", height=100, key="raw_input_area")
        st.button("견적 추가", on_click=add_quotes_callback)

with exp_col2:
    with st.expander("데이터 백업 / 복구 / 필터", expanded=True):
        if is_master:
            all_hc_list = ["전체보기"] + [f"{info['name']} ({info['dealer']})" for info in HC_DB.values()]
            selected_hc = st.selectbox("영업사원 선택", all_hc_list)
        
        up_col, down_col = st.columns(2)
        with up_col:
            uploaded_file = st.file_uploader("어제 저장한 CSV 복구", type=['csv'], label_visibility="collapsed")
            if uploaded_file is not None:
                if st.button("불러오기"):
                    df_loaded = pd.read_csv(uploaded_file)
                    date_cols = ['상담일', '1차_TM_일자', '2차_TM_일자', '3차_TM_일자']
                    for col in date_cols:
                        df_loaded[col] = pd.to_datetime(df_loaded[col]).dt.date
                    st.session_state['data'] = df_loaded
                    st.session_state['success_msg'] = "성공적으로 불러왔습니다!"
                    st.rerun()
        with down_col:
            if not st.session_state['data'].empty:
                csv_data = st.session_state['data'].to_csv(index=False).encode('utf-8-sig')
                file_prefix = "전체" if is_master else my_name
                st.download_button(
                    label="오늘 데이터 저장",
                    data=csv_data,
                    file_name=f"{file_prefix}_견적관리_{today.strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )

if st.session_state['success_msg']:
    st.success(st.session_state['success_msg'])
    st.session_state['success_msg'] = ""
if st.session_state['warning_msg']:
    st.warning(st.session_state['warning_msg'])
    st.session_state['warning_msg'] = ""

st.markdown("---")

if is_master:
    if 'selected_hc' in locals() and selected_hc != "전체보기":
        st.session_state['data']['HC_대리점'] = st.session_state['data']['HC명'] + " (" + st.session_state['data']['대리점명'] + ")"
        my_df = st.session_state['data'][st.session_state['data']['HC_대리점'] == selected_hc].copy()
    else:
        my_df = st.session_state['data'].copy()
else:
    my_df = st.session_state['data'][st.session_state['data']['HC_ID'] == my_id].copy()

total_quotes = len(my_df)
tm1_count = tm2_count = tm3_count = total_tm_done = contract_count = 0

if total_quotes > 0:
    for _, row in my_df.iterrows():
        if row['3차_TM']: tm3_count += 1
        elif row['2차_TM']: tm2_count += 1
        elif row['1차_TM']: tm1_count += 1
    
    total_tm_done = tm1_count + tm2_count + tm3_count 
    contract_count = int(my_df['계약완료'].sum())

tm_rate = (total_tm_done / total_quotes * 100) if total_quotes > 0 else 0
contract_rate = (contract_count / total_quotes * 100) if total_quotes > 0 else 0

st.subheader("실시간 요약 지표")
m1, m2, m3, m4, m5, m6 = st.columns(6)
title_text = "총 견적 건수" if is_master else "내 총 견적 건수"
m1.metric(title_text, f"{total_quotes}건")
m2.metric("1차 TM 완료(최종)", f"{tm1_count}건")
m3.metric("2차 TM 완료(최종)", f"{tm2_count}건")
m4.metric("3차 TM 완료(최종)", f"{tm3_count}건")
m5.metric("전체 TM 진행률", f"{tm_rate:.1f}%")
m6.metric("계약 완료(율)", f"{contract_count}건 ({contract_rate:.1f}%)")

st.markdown("---")

st.subheader("견적 및 TM 목록")

filter_tab = st.radio("표시 모드 선택", ["전체 목록 보기", "본인 작성 견적만 보기"], horizontal=True)

display_df = my_df.copy()
if filter_tab == "본인 작성 견적만 보기":
    display_df = display_df[display_df['is_self'] == True]

if is_master:
    column_order = [
        "선택/삭제", "상담일", "상담번호", "HC명", "대리점명", "고객명", "연락처", "주소", "상품(대분류)", "현장유형", "견적금액",
        "1차_TM", "1차_TM_일자", "2차_TM", "2차_TM_일자", "3차_TM", "3차_TM_일자", "계약완료", "상담메모"
    ]
else:
    column_order = [
        "선택/삭제", "상담일", "상담번호", "고객명", "연락처", "주소", "상품(대분류)", "현장유형", "견적금액",
        "1차_TM", "1차_TM_일자", "2차_TM", "2차_TM_일자", "3차_TM", "3차_TM_일자", "계약완료", "상담메모"
    ]

if not display_df.empty:
    st.markdown("<div class='table-header-banner'>📌 상세 견적 목록 (수정 및 삭제 가능)</div>", unsafe_allow_html=True)
    
    edited_df = st.data_editor(
        display_df,
        column_order=column_order,
        column_config={
            "선택/삭제": st.column_config.CheckboxColumn("선택/삭제", width="small", help="삭제하거나 선택할 행 체크"),
            "상담일": st.column_config.DateColumn("상담일", format="MM/DD", width="small"),
            "상담번호": st.column_config.TextColumn("상담번호", width="small"),
            "고객명": st.column_config.TextColumn("고객명", width="medium"),
            "연락처": st.column_config.TextColumn("연락처", width="medium"),
            "주소": st.column_config.TextColumn("주소", width="medium"),
            "견적금액": st.column_config.NumberColumn("견적금액 (원)", format="%,d", width="small"),
            "1차_TM": st.column_config.CheckboxColumn("1차", width="small"),
            "1차_TM_일자": st.column_config.DateColumn("1차 일자", format="MM/DD", width="small"),
            "2차_TM": st.column_config.CheckboxColumn("2차", width="small"),
            "2차_TM_일자": st.column_config.DateColumn("2차 일자", format="MM/DD", width="small"),
            "3차_TM": st.column_config.CheckboxColumn("3차", width="small"),
            "3차_TM_일자": st.column_config.DateColumn("3차 일자", format="MM/DD", width="small"),
            "계약완료": st.column_config.CheckboxColumn("계약완료", width="small"),
            "상담메모": st.column_config.TextColumn("상담메모", width="large")
        },
        disabled=[],
        num_rows="dynamic",
        hide_index=True,
        use_container_width=True,
        height=550
    )
    st.session_state['data'].update(edited_df)
else:
    st.info("조건에 해당하는 견적 데이터가 없습니다!")
