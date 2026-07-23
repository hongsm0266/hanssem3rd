import streamlit as st
import pandas as pd
from datetime import date
import re
import os
import json
import gspread
from google.oauth2.service_account import Credentials
import io
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# 1. 화면 기본 설정
st.set_page_config(page_title="충청호남팀 견적 관리 및 TM 진도", layout="wide")

# --- 구글 시트 & 드라이브 연동 설정 ---
SHEET_NAME = "견적관리대장로우"

# ⭐⭐⭐ [필수 수정] 아래 따옴표 안에 아까 복사하신 구글 드라이브 폴더 ID를 붙여넣으세요! ⭐⭐⭐
DRIVE_FOLDER_ID = "1Fg-fjYQfV0o_7NprBJXxJPq1rE4o1cWf"


@st.cache_resource
def init_connection():
    try:
        creds_json = st.secrets["gcp"]["key"]
        creds_dict = json.loads(creds_json)
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        return client
    except Exception as e:
        st.error("🚨 구글 API 키(Secrets) 설정이 안 되어 있거나 오류가 발생했습니다. 세팅을 확인해주세요.")
        return None

client = init_connection()

# 한샘 CI 로고 설정
if os.path.exists("logo.png"):
    HANSSEM_CI_URL = "logo.png"
elif os.path.exists("hanssem.png"):
    HANSSEM_CI_URL = "hanssem.png"
else:
    HANSSEM_CI_URL = "https://raw.githubusercontent.com/github/explore/main/topics/png/png.png"

# --- 커스텀 CSS ---
st.markdown("""
<style>
    .main .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"] {
        max-width: 100% !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        padding-top: 1.5rem !important;
        padding-bottom: 1rem !important;
    }
    .login-card-header { text-align: center; padding: 20px 0 10px 0; }
    .login-card-title { color: #0f172a; font-size: 22px !important; font-weight: 800 !important; margin-top: 15px; margin-bottom: 5px; }
    .login-card-sub { color: #64748b; font-size: 13px; margin-bottom: 20px; }
    div.stButton > button:first-child { background-color: #0056b3 !important; color: white !important; font-size: 16px !important; font-weight: bold !important; border-radius: 6px !important; padding: 10px 20px !important; border: none !important; }
    div.stButton > button:first-child:hover { background-color: #003d80 !important; color: #ffffff !important; }
    .user-info-box { background-color: #f1f5f9; border: 2px solid #0284c7; padding: 12px 16px; border-radius: 8px; text-align: right; }
    .user-info-name { font-size: 18px !important; font-weight: 900 !important; color: #0369a1 !important; }
    .user-info-sub { font-size: 12px !important; color: #64748b !important; }
    [data-testid="stMetric"] { background: linear-gradient(135deg, #eef6ff 0%, #e0f2fe 100%) !important; border: 1px solid #bae6fd !important; border-radius: 10px !important; padding: 10px 14px !important; box-shadow: 0 2px 4px rgba(0,0,0,0.04) !important; }
    [data-testid="stMetricLabel"] { font-size: 13px !important; font-weight: 700 !important; color: #0369a1 !important; }
    [data-testid="stMetricValue"] { font-size: 20px !important; font-weight: 800 !important; color: #0284c7 !important; }
    .table-header-banner { background-color: #0056b3; color: white; padding: 8px 16px; border-radius: 6px 6px 0 0; font-weight: bold; font-size: 14px; margin-bottom: -10px; display: flex; justify-content: space-between; align-items: center;}
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

if 'logged_in' not in st.session_state:
    st.session_state.update({'logged_in': False, 'hc_id': '', 'hc_name': '', 'dealer': '', 'is_master': False})
if 'success_msg' not in st.session_state: st.session_state['success_msg'] = ""
if 'warning_msg' not in st.session_state: st.session_state['warning_msg'] = ""

if not st.session_state['logged_in']:
    st.write("")
    st.write("")
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        if os.path.exists("logo.png") or os.path.exists("hanssem.png"):
            st.image(HANSSEM_CI_URL, width=180) 
        else:
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

today = date.today()
my_id = st.session_state['hc_id']
my_name = st.session_state['hc_name']
my_dealer = st.session_state['dealer']
is_master = st.session_state['is_master']

# --- 데이터 타입 세탁 방어 코드 ---
def clean_and_enforce_types(df):
    required_cols = [
        '선택/삭제', '상담일', '상담번호', 'HC_ID', 'HC명', '대리점명', '고객명', '연락처', '주소', '상품(대분류)', 
        '현장유형', '견적금액', 
        '1차_TM', '1차_TM_일자', '1차_증빙', 
        '2차_TM', '2차_TM_일자', '2차_증빙', 
        '3차_TM', '3차_TM_일자', '3차_증빙', 
        '계약완료', '상담메모', 'is_self'
    ]
    if df is None or df.empty:
        empty_df = pd.DataFrame(columns=required_cols)
        empty_df['선택/삭제'] = empty_df['선택/삭제'].astype(bool)
        empty_df['견적금액'] = empty_df['견적금액'].astype(int)
        return empty_df

    df = df.copy()
    for col in required_cols:
        if col not in df.columns:
            if col in ['선택/삭제', '1차_TM', '2차_TM', '3차_TM', '계약완료', 'is_self']: df[col] = False
            else: df[col] = ''

    date_cols = ['상담일', '1차_TM_일자', '2차_TM_일자', '3차_TM_일자']
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)

    bool_cols = ['선택/삭제', '1차_TM', '2차_TM', '3차_TM', '계약완료', 'is_self']
    for col in bool_cols:
        df[col] = df[col].fillna(False).astype(bool)
            
    df['견적금액'] = pd.to_numeric(df['견적금액'], errors='coerce').fillna(0).astype(int)

    str_cols = ['HC_ID', '상담번호', '연락처', '상담메모', '고객명', '주소', '상품(대분류)', '현장유형', 'HC명', '대리점명', '1차_증빙', '2차_증빙', '3차_증빙']
    for col in str_cols:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None', '<NA>'], '')
        if col == 'HC_ID': df[col] = df[col].str.replace(r'\.0$', '', regex=True).apply(lambda x: x.zfill(8) if x else '')
        elif col == '상담번호': df[col] = df[col].str.replace(r'\.0$', '', regex=True)
            
    return df[required_cols]

def get_or_create_sheet(spreadsheet, sheet_name):
    try:
        return spreadsheet.worksheet(sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="26")

def load_data_from_sheet(gc_client, is_master_mode, current_user):
    try:
        spreadsheet = gc_client.open(SHEET_NAME)
        if is_master_mode:
            all_records = []
            unique_names = list(set([info["name"] for info in HC_DB.values()]))
            for name in unique_names:
                try:
                    sheet = spreadsheet.worksheet(name)
                    try:
                        records = sheet.get_all_records()
                        if records: all_records.extend(records)
                    except Exception:
                        pass
                except gspread.exceptions.WorksheetNotFound:
                    continue
            return clean_and_enforce_types(pd.DataFrame(all_records) if all_records else None)
        else:
            sheet = get_or_create_sheet(spreadsheet, current_user)
            try:
                records = sheet.get_all_records()
            except Exception:
                records = []
            return clean_and_enforce_types(pd.DataFrame(records) if records else None)
    except Exception as e:
        st.error(f"구글 시트를 불러오지 못했습니다. 상세오류: {e}")
        return clean_and_enforce_types(None)

def save_data_to_sheet(gc_client, df, is_master_mode, current_user):
    try:
        spreadsheet = gc_client.open(SHEET_NAME)
        headers = [['선택/삭제', '상담일', '상담번호', 'HC_ID', 'HC명', '대리점명', '고객명', '연락처', '주소', '상품(대분류)', '현장유형', '견적금액', '1차_TM', '1차_TM_일자', '1차_증빙', '2차_TM', '2차_TM_일자', '2차_증빙', '3차_TM', '3차_TM_일자', '3차_증빙', '계약완료', '상담메모', 'is_self']]
        
        def _prepare_safe_list(dataframe):
            raw_list = [dataframe.columns.values.tolist()] + dataframe.values.tolist()
            safe_list = []
            for row in raw_list:
                safe_row = []
                for cell in row:
                    cell_str = str(cell)
                    if cell_str.strip().lower() in ['nan', 'none', 'nat', '<na>']:
                        safe_row.append("")
                    else:
                        safe_row.append(cell_str)
                safe_list.append(safe_row)
            return safe_list

        if is_master_mode:
            unique_names = list(set([info["name"] for info in HC_DB.values()]))
            for name in unique_names:
                group_df = df[df['HC명'] == name]
                if not group_df.empty:
                    sheet = get_or_create_sheet(spreadsheet, name)
                    sheet.clear()
                    sheet.update('A1', _prepare_safe_list(group_df))
            return True
        else:
            sheet = get_or_create_sheet(spreadsheet, current_user)
            my_df = df[df['HC명'] == current_user]
            sheet.clear()
            if not my_df.empty:
                sheet.update('A1', _prepare_safe_list(my_df))
            else:
                sheet.update('A1', headers)
            return True
    except Exception as e:
        st.error(f"구글 시트 저장 실패: {e}")
        return False

# 초기 데이터 로드
if 'data' not in st.session_state:
    if client:
        st.session_state['data'] = load_data_from_sheet(client, is_master, my_name)
    else:
        st.session_state['data'] = clean_and_enforce_types(None)

# --- [에러 해결] 구글 드라이브 지정 폴더 업로드 함수 ---
def upload_to_drive(file_obj, file_name):
    try:
        creds_json = st.secrets["gcp"]["key"]
        creds_dict = json.loads(creds_json)
        scopes = ["https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        service = build('drive', 'v3', credentials=creds)

        # 폴더 ID를 지정하여 내 저장 용량을 사용하도록 함
        file_metadata = {
            'name': file_name,
            'parents': [DRIVE_FOLDER_ID]
        }
        
        media = MediaIoBaseUpload(file_obj, mimetype='image/jpeg', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        # 누구나 링크만 있으면 볼 수 있도록 권한 개방
        service.permissions().create(
            fileId=file.get('id'),
            body={'type': 'anyone', 'role': 'reader'}
        ).execute()
        
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"드라이브 업로드 실패: {e}")
        return None

# --- 정밀 상품 파싱 함수 ---
def parse_product_summary(block):
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    prod_lines = []
    in_prod_area = False
    for l in lines:
        if l in ["상담 상품", "상품정보"]: in_prod_area = True; continue
        if l in ["구매 동기", "할인혜택 적용", "시방서", "시방서 (선택)"]: in_prod_area = False
        if in_prod_area:
            if not re.search(r'^\d+$', l) and not re.search(r'[\d,]+원$', l) and l not in ["홈퍼니싱 솔루션", "홈플래너 설계"] and not re.match(r'^\d{6,}$', l):
                if len(l) > 3 and "고객님" not in l and "상담" not in l and "견적" not in l:
                    prod_lines.append(l)

    items_summary = []
    for p_name in prod_lines:
        cat_label = ""
        if "책상의자" in p_name or ("책상" in p_name and "의자" in p_name) or "알로" in p_name: cat_label = "책상의자 - 알로/조이"
        elif "화장대" in p_name or "서랍장" in p_name or "리즈" in p_name: cat_label = "침실단품"
        elif any(k in p_name for k in ["붙박이장", "드레스룸", "옷장", "샘키즈", "샘베딩", "뮤트", "스케치", "아임빅", "바흐"]): cat_label = "수납"
        elif any(k in p_name for k in ["침대", "매트리스", "포시즌", "노뜨", "그로브오크", "포에트", "호텔침대", "어반글로우"]): cat_label = "침실"
        elif any(k in p_name for k in ["소파", "리클라이너", "스위브", "뉴플루드", "인피니", "뉴인피니", "테이즈", "키안티", "페타", "플로에", "거실장", "아카이브", "MVME"]): cat_label = "거실"
        elif any(k in p_name for k in ["식탁", "테이블", "식탁의자", "디아고", "리브업", "인칸토", "리니아"]): cat_label = "다이닝"
        elif "책상" in p_name or "조이" in p_name: cat_label = "자녀방 책상"
        else: cat_label = "기타(홈퍼니싱)"
        items_summary.append(cat_label)

    if items_summary:
        seen = set()
        top_labels = []
        for label in items_summary:
            if label not in seen and label != "기타(홈퍼니싱)":
                seen.add(label)
                top_labels.append(label)
            if len(top_labels) >= 3: break
        return " / ".join(top_labels) if top_labels else "기타(홈퍼니싱)"
    else: return "기타(홈퍼니싱)"

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
            parsed_id = my_id; parsed_name = my_name
                
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
                '선택/삭제': False, '상담일': pd.to_datetime(date_m.group(1)).date(),
                '상담번호': no_m.group(1), 'HC_ID': parsed_id, 'HC명': parsed_name,
                '대리점명': real_dealer, '고객명': cust_display, '연락처': phone_m.group(1) if phone_m else "",
                '주소': addr_m.group(1) if addr_m else "", '상품(대분류)': category_summary,
                '현장유형': type_m.group(1) if type_m else "", '견적금액': int(amt_str),
                '1차_TM': False, '1차_TM_일자': None, '1차_증빙': '',
                '2차_TM': False, '2차_TM_일자': None, '2차_증빙': '',
                '3차_TM': False, '3차_TM_일자': None, '3차_증빙': '',
                '계약완료': False, '상담메모': '', 'is_self': is_self
            })
    return pd.DataFrame(records), skipped_count

def add_quotes_callback():
    raw_input_text = st.session_state.get('raw_input_area', '')
    if raw_input_text.strip():
        new_df, skipped = parse_raw_text(raw_input_text, is_master)
        if not new_df.empty:
            new_df = clean_and_enforce_types(new_df)
            latest_df = load_data_from_sheet(client, is_master, my_name)
            
            if not latest_df.empty:
                updated_df = pd.concat([latest_df, new_df], ignore_index=True)
            else:
                updated_df = new_df
                
            updated_df = updated_df.sort_values(by='상담일', ascending=True).reset_index(drop=True)
            updated_df = clean_and_enforce_types(updated_df)
            
            if save_data_to_sheet(client, updated_df, is_master, my_name):
                st.session_state['data'] = updated_df
                target_msg = "견적" if is_master else "본인의 견적"
                st.session_state['success_msg'] = f"✅ 성공적으로 {target_msg} {len(new_df)}건을 추가하고 구글 시트에 실시간 반영했습니다!"
        else:
            st.session_state['warning_msg'] = "추가된 견적이 없습니다."
        
        if skipped > 0:
            st.session_state['warning_msg'] = f"🚨 타 사원의 견적 {skipped}건은 권한이 없어 자동으로 제외되었습니다."
        
        st.session_state['raw_input_area'] = ""

col_head_left, col_head_right = st.columns([2, 1])
with col_head_left:
    st.title("충청호남팀 견적 관리 및 TM 진도")
    st.caption(f"기준일: {today.strftime('%Y년 %m월 %d일')} | 🟢 구글 시트 실시간 연동 중")

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

input_col1, input_col2 = st.columns(2)

with input_col1:
    with st.expander("➕ 한샘 시스템 복사해서 새 견적 추가", expanded=True):
        st.text_area("텍스트를 붙여넣으세요", height=120, key="raw_input_area")
        st.button("견적 추가 및 시트 저장", on_click=add_quotes_callback)

with input_col2:
    with st.expander("📸 TM 증빙 사진 업로드 및 등록", expanded=True):
        temp_df = st.session_state['data']
        if not is_master:
            temp_df = temp_df[temp_df['HC_ID'] == my_id]
        
        if not temp_df.empty:
            quote_list = temp_df['상담일'].astype(str) + " | " + temp_df['고객명'] + " (" + temp_df['상담번호'] + ")"
            sel_quote = st.selectbox("증빙을 추가할 견적 선택", quote_list.tolist())
            sel_tm = st.radio("TM 차수 선택", ["1차_증빙", "2차_증빙", "3차_증빙"], horizontal=True)
            uploaded_img = st.file_uploader("바탕화면에서 사진 끌어다 놓기 (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
            
            if st.button("사진 업로드 및 저장", type="primary"):
                if DRIVE_FOLDER_ID == "여기에_복사한_폴더ID를_붙여넣으세요":
                    st.error("🚨 앱 코드 상단에 구글 드라이브 '폴더 ID'를 먼저 입력해주세요!")
                elif uploaded_img and sel_quote:
                    q_no = re.search(r'\((.*?)\)', sel_quote).group(1)
                    
                    with st.spinner("구글 드라이브에 사진을 안전하게 업로드 중입니다..."):
                        file_obj = io.BytesIO(uploaded_img.read())
                        filename = f"{q_no}_{sel_tm}_{today.strftime('%Y%m%d')}.jpg"
                        img_url = upload_to_drive(file_obj, filename)
                        
                        if img_url:
                            st.session_state['data'].loc[st.session_state['data']['상담번호'] == q_no, sel_tm] = img_url
                            if save_data_to_sheet(client, st.session_state['data'], is_master, my_name):
                                st.success("✅ 사진이 드라이브에 업로드되었고, 시트에 완벽히 등록되었습니다!")
                                st.rerun()
                            else:
                                st.error("사진 업로드는 성공했으나, 구글 시트 저장에 실패했습니다.")
                else:
                    st.warning("견적을 선택하고 사진을 업로드해주세요!")
        else:
            st.info("먼저 견적을 등록해주세요!")

if st.session_state['success_msg']:
    st.success(st.session_state['success_msg'])
    st.session_state['success_msg'] = ""
if st.session_state['warning_msg']:
    st.warning(st.session_state['warning_msg'])
    st.session_state['warning_msg'] = ""

st.markdown("---")

if is_master:
    if 'selected_hc' not in st.session_state: st.session_state['selected_hc'] = "전체보기"
    all_hc_list = ["전체보기"] + [f"{info['name']} ({info['dealer']})" for info in HC_DB.values()]
    selected_hc = st.selectbox("영업사원 필터링 (구글 시트 탭 전체조회)", all_hc_list, key="selected_hc")
    
    if selected_hc != "전체보기":
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

st.subheader("📈 실시간 요약 지표")
m1, m2, m3, m4, m5, m6 = st.columns(6)
title_text = "총 견적 건수" if is_master else "내 총 견적 건수"
m1.metric(title_text, f"{total_quotes}건")
m2.metric("1차 TM 완료", f"{tm1_count}건")
m3.metric("2차 TM 완료", f"{tm2_count}건")
m4.metric("3차 TM 완료", f"{tm3_count}건")
m5.metric("전체 TM 진행률", f"{tm_rate:.1f}%")
m6.metric("계약 완료(율)", f"{contract_count}건 ({contract_rate:.1f}%)")

st.markdown("---")

st.subheader("📋 견적 및 TM 목록")
filter_tab = st.radio("표시 모드 선택", ["전체 목록 보기", "본인 작성 견적만 보기"], horizontal=True)

display_df = my_df.copy()
if filter_tab == "본인 작성 견적만 보기":
    display_df = display_df[display_df['is_self'] == True]

column_order = [
    "선택/삭제", "상담일", "상담번호", "HC명", "대리점명", "고객명", "연락처", "주소", "상품(대분류)", "현장유형", "견적금액",
    "1차_TM", "1차_TM_일자", "1차_증빙", 
    "2차_TM", "2차_TM_일자", "2차_증빙", 
    "3차_TM", "3차_TM_일자", "3차_증빙", 
    "계약완료", "상담메모"
] if is_master else [
    "선택/삭제", "상담일", "상담번호", "고객명", "연락처", "주소", "상품(대분류)", "현장유형", "견적금액",
    "1차_TM", "1차_TM_일자", "1차_증빙", 
    "2차_TM", "2차_TM_일자", "2차_증빙", 
    "3차_TM", "3차_TM_일자", "3차_증빙", 
    "계약완료", "상담메모"
]

if not display_df.empty:
    st.markdown("<div class='table-header-banner'>📌 상세 견적 목록 (아래 표를 직접 클릭하여 수정하세요)</div>", unsafe_allow_html=True)
    
    edited_df = st.data_editor(
        display_df,
        column_order=column_order,
        column_config={
            "선택/삭제": st.column_config.CheckboxColumn("선택/삭제", width="small", help="삭제할 행에 체크"),
            "상담일": st.column_config.DateColumn("상담일", format="MM/DD", width="small"),
            "상담번호": st.column_config.TextColumn("상담번호", width="small", disabled=True),
            "고객명": st.column_config.TextColumn("고객명", width="medium"),
            "연락처": st.column_config.TextColumn("연락처", width="medium"),
            "주소": st.column_config.TextColumn("주소", width="medium"),
            "견적금액": st.column_config.NumberColumn("견적금액 (원)", format="%,d", width="small"),
            
            "1차_TM": st.column_config.CheckboxColumn("1차", width="small"),
            "1차_TM_일자": st.column_config.DateColumn("1차 일자", format="MM/DD", width="small"),
            "1차_증빙": st.column_config.LinkColumn("1차 증빙", display_text="🔗 사진보기", width="small"),
            
            "2차_TM": st.column_config.CheckboxColumn("2차", width="small"),
            "2차_TM_일자": st.column_config.DateColumn("2차 일자", format="MM/DD", width="small"),
            "2차_증빙": st.column_config.LinkColumn("2차 증빙", display_text="🔗 사진보기", width="small"),
            
            "3차_TM": st.column_config.CheckboxColumn("3차", width="small"),
            "3차_TM_일자": st.column_config.DateColumn("3차 일자", format="MM/DD", width="small"),
            "3차_증빙": st.column_config.LinkColumn("3차 증빙", display_text="🔗 사진보기", width="small"),
            
            "계약완료": st.column_config.CheckboxColumn("계약완료", width="small"),
            "상담메모": st.column_config.TextColumn("상담메모", width="large")
        },
        num_rows="dynamic", hide_index=True, use_container_width=True, height=550
    )
    
    if st.button("💾 위에서 수정한 표 내용 전체를 구글 시트에 저장하기 (동기화)", type="primary"):
        with st.spinner("구글 시트의 사원 탭에 안전하게 업데이트 중입니다... 🔄"):
            global_df = st.session_state['data'].copy()
            global_df = global_df.drop(display_df.index, errors='ignore')
            
            edited_df_to_keep = edited_df[~edited_df['선택/삭제']].copy()
            edited_df_to_keep['선택/삭제'] = False 
            
            new_global_df = pd.concat([global_df, edited_df_to_keep])
            new_global_df = new_global_df.sort_values(by='상담일', ascending=True).reset_index(drop=True)
            new_global_df = clean_and_enforce_types(new_global_df)
            
            if save_data_to_sheet(client, new_global_df, is_master, my_name):
                st.session_state['data'] = new_global_df
                st.success("✅ 구글 시트의 해당 탭에 완벽하게 저장되었습니다!")
                st.rerun()

else:
    st.info("조건에 해당하는 견적 데이터가 없습니다. 상단의 '견적 추가'를 이용해 첫 데이터를 넣어주세요!")
