import streamlit as st
import pandas as pd
from datetime import date
import re
import os
import json
import gspread
from google.oauth2.service_account import Credentials
import io
import urllib.request
import urllib.parse
import base64

# 1. 화면 기본 설정
st.set_page_config(page_title="충청호남팀 견적 관리 및 TM 진도", layout="wide")

# --- 구글 시트 연동 설정 ---
SHEET_NAME = "견적관리대장로우"

# ⭐ 발급받으신 ImgBB API 키 영구 탑재 완료!
IMGBB_API_KEY = "1cecb3f4e313203e40d78882356ef1ca"

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
        st.error("구글 API 키(Secrets) 설정이 안 되어 있거나 오류가 발생했습니다. 세팅을 확인해주세요.")
        return None

client = init_connection()

if os.path.exists("logo.png"): HANSSEM_CI_URL = "logo.png"
elif os.path.exists("hanssem.png"): HANSSEM_CI_URL = "hanssem.png"
else: HANSSEM_CI_URL = "https://raw.githubusercontent.com/github/explore/main/topics/png/png.png"

# --- 커스텀 CSS (이모지 제거 및 폰트 진하게 강화) ---
st.markdown("""
<style>
    .main .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"] {
        max-width: 100% !important;
        padding-left: 1rem !important; padding-right: 1rem !important;
        padding-top: 1.5rem !important; padding-bottom: 1rem !important;
    }
    
    /* 💡 각 주제(Subheader)를 매우 진하고 또렷하게 변경 */
    h2, h3 {
        font-weight: 900 !important;
        color: #0f172a !important;
        font-size: 24px !important;
        letter-spacing: -0.5px !important;
    }

    .login-card-title { color: #0f172a; font-size: 22px !important; font-weight: 900 !important; margin-top: 15px; margin-bottom: 5px; }
    .login-card-sub { color: #64748b; font-size: 13px; margin-bottom: 20px; font-weight: bold; }
    
    div.stButton > button { 
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important; 
        color: white !important; font-size: 15px !important; font-weight: 800 !important; 
        border-radius: 8px !important; padding: 10px 15px !important; border: none !important; 
        height: auto !important; min-height: 45px; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        border-bottom: 4px solid #1e3a8a !important; transition: all 0.1s ease !important; 
    }
    div.stButton > button:hover { transform: translateY(-2px) !important; }
    div.stButton > button:active { transform: translateY(2px) !important; border-bottom: 1px solid #1e3a8a !important; margin-bottom: 3px !important; }
    
    div.element-container:has(.red-btn) + div.element-container div.stButton > button {
        background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%) !important; border-bottom: 4px solid #991b1b !important;
    }
    div.element-container:has(.yellow-btn) + div.element-container div.stButton > button {
        background: linear-gradient(180deg, #facc15 0%, #eab308 100%) !important; border-bottom: 4px solid #a16207 !important; color: #1c1917 !important;
    }

    [data-testid="stMetric"] { 
        background: #ffffff !important; border: 2px solid #cbd5e1 !important; border-left: 6px solid #2563eb !important; 
        border-radius: 10px !important; padding: 10px !important; box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important; 
    }
    [data-testid="stMetricLabel"] { font-size: 14px !important; font-weight: 800 !important; color: #1e3a8a !important; }
    [data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 900 !important; color: #dc2626 !important; }

    .custom-metric {
        background: #ffffff; border: 2px solid #cbd5e1; border-left: 6px solid #2563eb;
        border-radius: 10px; padding: 10px 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        height: 100%; display: flex; flex-direction: column; justify-content: center;
    }
    .custom-metric-label { font-size: 13px; font-weight: 800; color: #1e3a8a; margin-bottom: 4px; white-space: nowrap; }
    .custom-metric-value { font-size: 19px; font-weight: 900; color: #dc2626; white-space: nowrap; letter-spacing: -0.5px; }

    .user-info-box { background-color: #f1f5f9; border: 2px solid #0284c7; padding: 12px 16px; border-radius: 8px; text-align: right; }
    .user-info-name { font-size: 18px !important; font-weight: 900 !important; color: #0369a1 !important; }
    .user-info-sub { font-size: 12px !important; color: #64748b !important; font-weight: bold; }
    .table-header-banner { background-color: #0056b3; color: white; padding: 10px 16px; border-radius: 6px 6px 0 0; font-weight: 900; font-size: 16px; margin-bottom: -10px; display: flex; justify-content: space-between; align-items: center;}
</style>
""", unsafe_allow_html=True)

HC_DB = {
    "00033448": {"name": "장재형", "dealer": "둔산"}, "00038617": {"name": "이대운", "dealer": "둔산"},
    "00041990": {"name": "강지인", "dealer": "둔산"}, "00040110": {"name": "장영종", "dealer": "광양"},
    "00040112": {"name": "임현", "dealer": "광양"}, "00040113": {"name": "하행우", "dealer": "광양"},
    "00042008": {"name": "김경율", "dealer": "세종"}, "00044932": {"name": "강희성", "dealer": "세종"},
    "00044933": {"name": "한유진", "dealer": "세종"}, "00040744": {"name": "빙지영", "dealer": "목포"},
    "00040755": {"name": "윤덕수", "dealer": "목포"}, "00043657": {"name": "최병하", "dealer": "익산"},
    "00043825": {"name": "이은혜", "dealer": "익산"}, "00033249": {"name": "임준수", "dealer": "충주"},
    "00033479": {"name": "류승태", "dealer": "여수"}, "00042423": {"name": "라태현", "dealer": "여수"},
    "00044183": {"name": "김동휘", "dealer": "여수"}
}

# --- 상품 분류 키워드 세팅 ---
PRODUCT_KEYWORDS = {
    "침실단품": ["화장대", "서랍장", "리즈"],
    "수납": ["붙박이장", "드레스룸", "옷장", "샘키즈", "샘베딩", "뮤트", "스케치", "아임빅", "바흐"],
    "침실": ["침대", "매트리스", "포시즌", "노뜨", "그로브오크", "포에트", "호텔침대", "어반글로우"],
    "거실": ["소파", "리클라이너", "스위브", "뉴플루드", "인피니", "뉴인피니", "테이즈", "키안티", "페타", "플로에", "거실장", "아카이브", "MVME"],
    "다이닝": ["식탁", "테이블", "식탁의자", "디아고", "리브업", "인칸토", "리니아"],
    "책상의자 - 알로/조이": ["책상의자", "알로"],
    "자녀방 책상": ["조이"]
}

if 'logged_in' not in st.session_state: st.session_state.update({'logged_in': False, 'hc_id': '', 'hc_name': '', 'dealer': '', 'is_master': False})
if 'success_msg' not in st.session_state: st.session_state['success_msg'] = ""
if 'warning_msg' not in st.session_state: st.session_state['warning_msg'] = ""
if 'uploader_key' not in st.session_state: st.session_state['uploader_key'] = 0

if not st.session_state['logged_in']:
    st.write("")
    st.write("")
    col_left, col_center, col_right = st.columns([1, 1.2, 1])
    with col_center:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image(HANSSEM_CI_URL, width=180) 
        st.markdown("""<div class="login-card-title">충청호남팀 견적관리 로그인</div><div class="login-card-sub">견적 등록 및 TM 진도율 실시간 통합 시스템</div></div>""", unsafe_allow_html=True)
        login_id = st.text_input("아이디 (사번)", placeholder="사번 8자리를 입력하세요")
        login_pw = st.text_input("비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        st.write("")
        if st.button("로그인", use_container_width=True):
            if login_id == "0000" and login_pw == "0000":
                st.session_state.update({'logged_in': True, 'hc_id': "0000", 'hc_name': "총괄관리자", 'dealer': "마스터", 'is_master': True})
                st.rerun()
            elif login_id and login_id == login_pw and login_id in HC_DB:
                st.session_state.update({'logged_in': True, 'hc_id': login_id, 'hc_name': HC_DB[login_id]['name'], 'dealer': HC_DB[login_id]['dealer'], 'is_master': False})
                st.rerun()
            else: st.error("정보가 일치하지 않습니다.")
    st.stop()

today = date.today()
my_id, my_name, my_dealer, is_master = st.session_state['hc_id'], st.session_state['hc_name'], st.session_state['dealer'], st.session_state['is_master']

def clean_and_enforce_types(df):
    # 💡 '상품(대분류)' -> '상품'으로 이름 축소
    req_cols = ['선택/삭제', '상담일', '상담번호', 'HC_ID', 'HC명', '대리점명', '고객명', '연락처', '주소', '상품', '현장유형', '견적금액', '1차_TM', '1차_TM_일자', '1차_증빙', '2차_TM', '2차_TM_일자', '2차_증빙', '3차_TM', '3차_TM_일자', '3차_증빙', '계약완료', '상담메모', 'is_self', '세부품목']
    
    if df is None or df.empty:
        edf = pd.DataFrame(columns=req_cols)
        for col in ['선택/삭제', '1차_TM', '2차_TM', '3차_TM', '계약완료', 'is_self']: edf[col] = False
        edf['견적금액'] = 0
        return edf
    
    df = df.copy()
    
    # 구글 시트에 예전 이름 '상품(대분류)'가 남아있다면 자동으로 '상품'으로 호환되게 변경
    if '상품(대분류)' in df.columns:
        df = df.rename(columns={'상품(대분류)': '상품'})

    for col in req_cols:
        if col not in df.columns: 
            df[col] = False if col in ['선택/삭제', '1차_TM', '2차_TM', '3차_TM', '계약완료', 'is_self'] else ''
            
    for col in ['상담일', '1차_TM_일자', '2차_TM_일자', '3차_TM_일자']:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
        df[col] = df[col].apply(lambda x: None if pd.isna(x) else x)
        
    for col in ['선택/삭제', '1차_TM', '2차_TM', '3차_TM', '계약완료', 'is_self']: 
        df[col] = df[col].apply(lambda x: True if str(x).strip().upper() == 'TRUE' or x is True or x == 1 or x == '1' else False).astype(bool)
        
    df['견적금액'] = pd.to_numeric(df['견적금액'], errors='coerce').fillna(0).astype(int)
    for col in ['HC_ID', '상담번호', '연락처', '상담메모', '고객명', '주소', '상품', '현장유형', 'HC명', '대리점명', '1차_증빙', '2차_증빙', '3차_증빙', '세부품목']:
        df[col] = df[col].astype(str).replace(['nan', 'NaN', 'None', '<NA>'], '')
        if col == 'HC_ID': df[col] = df[col].str.replace(r'\.0$', '', regex=True).apply(lambda x: x.zfill(8) if x else '')
        elif col == '상담번호': df[col] = df[col].str.replace(r'\.0$', '', regex=True)
    return df[req_cols]

def get_or_create_sheet(spreadsheet, sheet_name):
    try: return spreadsheet.worksheet(sheet_name)
    except: return spreadsheet.add_worksheet(title=sheet_name, rows="1000", cols="26")

def load_data_from_sheet(gc_client, is_master_mode, current_user):
    try:
        spreadsheet = gc_client.open(SHEET_NAME)
        if is_master_mode:
            all_records = []
            for name in list(set([info["name"] for info in HC_DB.values()])):
                try: 
                    records = spreadsheet.worksheet(name).get_all_records()
                    if records: all_records.extend(records)
                except: continue
            return clean_and_enforce_types(pd.DataFrame(all_records) if all_records else None)
        else:
            try: records = get_or_create_sheet(spreadsheet, current_user).get_all_records()
            except: records = []
            return clean_and_enforce_types(pd.DataFrame(records) if records else None)
    except Exception as e: return clean_and_enforce_types(None)

@st.cache_data(ttl=5) 
def load_perf_sheet(_gc_client):
    try:
        data = _gc_client.open(SHEET_NAME).worksheet("시트1").get("B30:AG70")
        if data and len(data) > 1:
            headers = [str(h).strip() for h in data[0]]
            rows = data[1:]
            safe_rows = [r + [''] * (len(headers) - len(r)) for r in rows]
            return pd.DataFrame(safe_rows, columns=headers)
        return pd.DataFrame()
    except: return pd.DataFrame()

def get_perf_metrics(perf_df, target_id, target_name):
    default = { 'F': 0, 'G': 0, 'H': 0, 'I': 0, 'J': 0, 'R': 0, 'T': 0, 'U': 0, 'Y': 0 }
    if perf_df is None or perf_df.empty: return default
    
    def clean_val(v):
        if pd.isna(v) or v == "": return 0.0
        try:
            if isinstance(v, str): v = v.replace('%', '').replace(',', '').replace('원', '').strip()
            return float(v)
        except: return 0.0

    if target_id == "ALL":
        sums = { 'F': 0, 'G': 0, 'H': 0, 'I': 0, 'J': 0, 'R': 0, 'T': 0, 'U': 0, 'Y': 0 }
        for _, row in perf_df.iterrows():
            vals = row.values
            if len(vals) < 24: continue
            sums['F'] += clean_val(vals[4])
            sums['G'] += clean_val(vals[5])
            sums['H'] += clean_val(vals[6])
            sums['I'] += clean_val(vals[7])
            sums['R'] += clean_val(vals[16])
            sums['T'] += clean_val(vals[18])
            sums['U'] += clean_val(vals[19])
            sums['Y'] += clean_val(vals[23])
        return sums
    else:
        possible_ids = [str(target_id), target_name]
        try: possible_ids.append(str(int(target_id))) 
        except: pass
        
        for _, row in perf_df.iterrows():
            vals = row.values
            if len(vals) < 24: continue
            row_str = "".join([str(x).strip() for x in vals])
            if any(pid in row_str for pid in possible_ids):
                j_val = clean_val(vals[8])
                if 0 < j_val <= 1.0 and "%" not in str(vals[8]): j_val *= 100
                return {
                    'F': clean_val(vals[4]), 'G': clean_val(vals[5]), 'H': clean_val(vals[6]),
                    'I': clean_val(vals[7]), 'J': j_val, 'R': clean_val(vals[16]),
                    'T': clean_val(vals[18]), 'U': clean_val(vals[19]), 'Y': clean_val(vals[23])
                }
        return default

def save_data_to_sheet(gc_client, df, is_master_mode, current_user):
    try:
        spreadsheet = gc_client.open(SHEET_NAME)
        # 구글 시트 저장 시에도 '상품' 이름 유지
        headers = [['선택/삭제', '상담일', '상담번호', 'HC_ID', 'HC명', '대리점명', '고객명', '연락처', '주소', '상품', '현장유형', '견적금액', '1차_TM', '1차_TM_일자', '1차_증빙', '2차_TM', '2차_TM_일자', '2차_증빙', '3차_TM', '3차_TM_일자', '3차_증빙', '계약완료', '상담메모', 'is_self', '세부품목']]
        def _prepare(d):
            safe_list = []
            raw_list = [d.columns.values.tolist()] + d.values.tolist()
            for row in raw_list:
                safe_row = []
                for cell in row:
                    if isinstance(cell, bool): safe_row.append("TRUE" if cell else "FALSE")
                    else:
                        cell_str = str(cell)
                        safe_row.append("" if cell_str.strip().lower() in ['nan', 'none', 'nat', '<na>'] else cell_str)
                safe_list.append(safe_row)
            return safe_list
            
        if is_master_mode:
            for name in list(set([info["name"] for info in HC_DB.values()])):
                group_df = df[df['HC명'] == name]
                sheet = get_or_create_sheet(spreadsheet, name); sheet.clear()
                if not group_df.empty: sheet.update('A1', _prepare(group_df))
                else: sheet.update('A1', headers)
        else:
            sheet = get_or_create_sheet(spreadsheet, current_user); sheet.clear()
            my_df = df[df['HC명'] == current_user]
            if not my_df.empty: sheet.update('A1', _prepare(my_df))
            else: sheet.update('A1', headers)
        return True
    except: return False

if 'data' not in st.session_state:
    st.session_state['data'] = load_data_from_sheet(client, is_master, my_name) if client else clean_and_enforce_types(None)

def upload_to_imgbb(file_obj, file_name):
    try:
        url = "https://api.imgbb.com/1/upload"
        req = urllib.request.Request(url, data=urllib.parse.urlencode({"key": IMGBB_API_KEY, "image": base64.b64encode(file_obj.read()).decode("utf-8"), "name": file_name.split('.')[0]}).encode("utf-8"))
        res = json.loads(urllib.request.urlopen(req).read().decode("utf-8"))
        return res["data"]["url"] if res.get("success") else None
    except: return None

def parse_product_summary(block):
    lines = [l.strip() for l in block.split("\n") if l.strip()]
    prod_lines, in_prod = [], False
    for l in lines:
        if l in ["상담 상품", "상품정보"]: in_prod = True; continue
        if l in ["구매 동기", "할인혜택 적용", "시방서", "시방서 (선택)"]: in_prod = False
        if in_prod and not re.search(r'^\d+$', l) and not re.search(r'[\d,]+원$', l) and l not in ["홈퍼니싱 솔루션", "홈플래너 설계"] and not re.match(r'^\d{6,}$', l) and len(l) > 3 and "고객님" not in l and "상담" not in l and "견적" not in l: prod_lines.append(l)

    res = []
    for p in prod_lines:
        matched = False
        if "책상" in p and "의자" in p:
            res.append("책상의자 - 알로/조이")
            continue
        
        for cat, keywords in PRODUCT_KEYWORDS.items():
            if any(k in p for k in keywords):
                res.append(cat)
                matched = True
                break
                
        if not matched:
            if "책상" in p: res.append("자녀방 책상")
            else: res.append("기타(홈퍼니싱)")
    
    seen = set(); top = []
    for r in res:
        if r not in seen and r != "기타(홈퍼니싱)": seen.add(r); top.append(r)
        if len(top) >= 3: break
        
    cat_summary = " / ".join(top) if top else "기타(홈퍼니싱)"
    detail_str = " , ".join(prod_lines)
    return cat_summary, detail_str

def parse_raw_text(text, master_mode):
    records, skipped = [], 0
    for block in text.split("상담일\n")[1:]:
        block = "상담일\n" + block 
        hc_m = re.search(r'영업사원\n(\d+)\s+([가-힣]+)', block)
        if hc_m:
            if not master_mode and hc_m.group(1) != my_id: skipped += 1; continue
            p_id, p_name = hc_m.group(1), hc_m.group(2)
        else: p_id, p_name = my_id, my_name
                
        d_m = re.search(r'상담일\n([\d-]+)', block)
        n_m = re.search(r'상담번호\n(\d+)', block)
        if d_m and n_m:
            c_m = re.search(r'([가-힣]+)\s+고객님', block)
            c_name = c_m.group(1) if c_m else ""
            is_self = bool(c_name and p_name and c_name.strip() == p_name.strip())
            amt_m = re.search(r'결제 예정 금액\n([\d,]+)', block)
            ph_m = re.search(r'휴대폰 번호\n([\d-]+)', block)
            ad_m = re.search(r'주소\n(.+)', block)
            ty_m = re.search(r'현장 유형\n([^\n]+)', block)
            
            cat_summary, detail_str = parse_product_summary(block)
            
            records.append({
                '선택/삭제': False, '상담일': pd.to_datetime(d_m.group(1)).date(),
                '상담번호': n_m.group(1), 'HC_ID': p_id, 'HC명': p_name,
                '대리점명': HC_DB.get(p_id, {}).get("dealer", my_dealer), '고객명': f"[본인] {c_name}" if is_self else c_name,
                '연락처': ph_m.group(1) if ph_m else "", '주소': ad_m.group(1) if ad_m else "",
                '상품': cat_summary, '현장유형': ty_m.group(1) if ty_m else "",
                '견적금액': int(amt_m.group(1).replace(",", "")) if amt_m else 0,
                '1차_TM': False, '1차_TM_일자': None, '1차_증빙': '', '2차_TM': False, '2차_TM_일자': None, '2차_증빙': '', '3차_TM': False, '3차_TM_일자': None, '3차_증빙': '', '계약완료': False, '상담메모': '', 'is_self': is_self,
                '세부품목': detail_str 
            })
    return pd.DataFrame(records), skipped

def add_quotes_callback():
    txt = st.session_state.get('raw_input_area', '')
    if txt.strip():
        new_df, skipped = parse_raw_text(txt, is_master)
        if not new_df.empty:
            ldf = load_data_from_sheet(client, is_master, my_name)
            udf = clean_and_enforce_types(pd.concat([ldf, new_df], ignore_index=True) if not ldf.empty else new_df).sort_values(by='상담일', ascending=True).reset_index(drop=True)
            if save_data_to_sheet(client, udf, is_master, my_name):
                st.session_state.update({'data': udf, 'success_msg': f"성공적으로 {len(new_df)}건을 추가했습니다!", 'uploader_key': st.session_state['uploader_key'] + 1})
        else: st.session_state['warning_msg'] = "추가된 견적이 없습니다."
        if skipped > 0: st.session_state['warning_msg'] = f"타 사원의 견적 {skipped}건 제외됨."
        st.session_state['raw_input_area'] = ""

col_head_left, col_head_right = st.columns([2, 1])
with col_head_left:
    st.title("충청호남팀 견적 관리 및 TM 진도")
    st.caption(f"기준일: {today.strftime('%Y년 %m월 %d일')} | 실시간 자동 동기화 서버 연결됨")

with col_head_right:
    st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
    sub_col1, sub_col2 = st.columns([3, 1])
    with sub_col1:
        if is_master: st.markdown(f"<div class='user-info-box'><span class='user-info-name'>{my_name} 님</span></div>", unsafe_allow_html=True)
        else: st.markdown(f"<div class='user-info-box'><span class='user-info-name'>{my_name} 님 ({my_dealer})</span><br><span class='user-info-sub'>사번: {my_id}</span></div>", unsafe_allow_html=True)
    with sub_col2:
        if st.button("로그아웃"): st.session_state['logged_in'] = False; st.rerun()

st.markdown("---")
input_col1, input_col2 = st.columns(2)

with input_col1:
    with st.expander("한샘 시스템 복사해서 새 견적 추가", expanded=True):
        st.text_area("텍스트를 붙여넣으세요", height=120, key="raw_input_area")
        st.button("견적 추가 및 시트 저장", on_click=add_quotes_callback)

with input_col2:
    with st.expander("TM 증빙 사진 초고속 업로드", expanded=True):
        temp_df = st.session_state['data']
        if not is_master: temp_df = temp_df[temp_df['HC_ID'] == my_id]
        if not temp_df.empty:
            quote_list = ["--- 견적을 선택하세요 ---"] + (temp_df['상담일'].astype(str) + " | " + temp_df['고객명'] + " (" + temp_df['상담번호'] + ")").tolist()
            sel_quote = st.selectbox("증빙을 추가할 견적 선택", quote_list, key=f"quote_sel_{st.session_state['uploader_key']}")
            sel_tm = st.radio("TM 차수 선택", ["1차_증빙", "2차_증빙", "3차_증빙"], horizontal=True, key=f"tm_sel_{st.session_state['uploader_key']}")
            uploaded_img = st.file_uploader("바탕화면에서 사진 끌어다 놓기", type=['jpg', 'jpeg', 'png'], key=f"img_uploader_{st.session_state['uploader_key']}")
            
            if st.button("사진 업로드 및 저장", type="primary"):
                if sel_quote == "--- 견적을 선택하세요 ---" or not uploaded_img: st.warning("견적 선택 및 사진을 올려주세요!")
                else:
                    q_no = re.search(r'\((.*?)\)', sel_quote).group(1)
                    with st.spinner("이미지 서버에 전송 중..."):
                        img_url = upload_to_imgbb(io.BytesIO(uploaded_img.read()), f"{q_no}_{sel_tm}_{today.strftime('%Y%m%d')}.jpg")
                        if img_url:
                            st.session_state['data'].loc[st.session_state['data']['상담번호'] == q_no, sel_tm] = img_url
                            if save_data_to_sheet(client, st.session_state['data'], is_master, my_name):
                                st.success("사진 업로드 완료!"); st.session_state['uploader_key'] += 1; st.rerun()
                            else: st.error("시트 저장 실패.")
        else: st.info("먼저 견적을 등록해주세요!")

if st.session_state['success_msg']: st.success(st.session_state['success_msg']); st.session_state['success_msg'] = ""
if st.session_state['warning_msg']: st.warning(st.session_state['warning_msg']); st.session_state['warning_msg'] = ""

st.markdown("---")

if is_master:
    if 'selected_hc' not in st.session_state: st.session_state['selected_hc'] = "전체보기"
    all_hc_list = ["전체보기"] + [f"{info['name']} ({info['dealer']})" for info in HC_DB.values()]
    selected_hc = st.selectbox("영업사원 필터링 (구글 시트 탭 전체조회)", all_hc_list, key="selected_hc")
    my_df = st.session_state['data'].copy()
    if selected_hc != "전체보기": my_df = my_df[my_df['HC명'] == selected_hc.split(" (")[0]]
else: my_df = st.session_state['data'][st.session_state['data']['HC_ID'] == my_id].copy()

total_quotes = len(my_df)
tm1_count = len(my_df[my_df['1차_TM'] == True]) if total_quotes > 0 else 0
tm2_count = len(my_df[my_df['2차_TM'] == True]) if total_quotes > 0 else 0
tm3_count = len(my_df[my_df['3차_TM'] == True]) if total_quotes > 0 else 0
contract_count = int(my_df['계약완료'].sum()) if total_quotes > 0 else 0
tm_rate = ((tm1_count + tm2_count + tm3_count) / total_quotes * 100) if total_quotes > 0 else 0
contract_rate = (contract_count / total_quotes * 100) if total_quotes > 0 else 0


# --- 영업 실적 현황 ---
st.subheader("영업 실적 현황 (당일 기준)")
perf_df = load_perf_sheet(client)

target_id = "ALL" if is_master and selected_hc == "전체보기" else my_id
target_name_perf = "ALL" if is_master and selected_hc == "전체보기" else (selected_hc.split(" (")[0] if is_master else my_name)

metrics = get_perf_metrics(perf_df, target_id, target_name_perf)

def fmt(n): return f"{int(round(n)):,}"
def render_metric(label, v_html): return f'<div class="custom-metric"><div class="custom-metric-label">{label}</div><div class="custom-metric-value">{v_html}</div></div>'

F_str, G_str, H_str, I_str = fmt(metrics['F']), fmt(metrics['G']), fmt(metrics['H']), fmt(metrics['I'])
J_str = f"{int(round(metrics['J']))}%" if target_id != "ALL" else "-"
R_str, Y_str = fmt(metrics['R']), fmt(metrics['Y'])
T_str, U_str = fmt(metrics['T']), fmt(metrics['U'])

growth = (metrics['T'] / metrics['U'] - 1) if metrics['U'] > 0 else 0
growth_html = ""
if metrics['U'] > 0:
    g_pct = int(round(abs(growth) * 100))
    if growth > 0: growth_html = f'<span style="color:#dc2626; font-size:15px; margin-left:6px;">(▲ {g_pct}%)</span>'
    elif growth < 0: growth_html = f'<span style="color:#2563eb; font-size:15px; margin-left:6px;">(▼ {g_pct}%)</span>'
    else: growth_html = f'<span style="color:#64748b; font-size:15px; margin-left:6px;">(- 0%)</span>'

combined_lbl = '<span style="color:#dc2626;">당월매출</span> <span style="color:#64748b;">/</span> <span style="color:#2563eb;">전월동일자</span>'
combined_val = f'<span style="color:#dc2626;">{T_str}</span> <span style="color:#64748b; font-size:16px; margin:0 3px;">/</span> <span style="color:#2563eb;">{U_str}</span> {growth_html}'

cols_perf = st.columns([0.85, 1, 0.85, 1, 0.7, 1.2, 2.2, 1])
cols_perf[0].markdown(render_metric("견적건(일)", F_str), unsafe_allow_html=True)
cols_perf[1].markdown(render_metric("견적건(월누적)", H_str), unsafe_allow_html=True)
cols_perf[2].markdown(render_metric("계약건(일)", G_str), unsafe_allow_html=True)
cols_perf[3].markdown(render_metric("계약건(월누적)", I_str), unsafe_allow_html=True)
cols_perf[4].markdown(render_metric("계약율", J_str), unsafe_allow_html=True)
cols_perf[5].markdown(render_metric("계약금액(월누적)", R_str), unsafe_allow_html=True)
cols_perf[6].markdown(render_metric(combined_lbl, combined_val), unsafe_allow_html=True)
cols_perf[7].markdown(render_metric("익월 매출", Y_str), unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 견적 관리 지표 ---
st.subheader("견적 관리 지표")
m1, m2, m3, m4, m5, m6 = st.columns(6)
m1.metric("총 견적 건수" if is_master else "내 총 견적 건수", f"{total_quotes}건")
m2.metric("1차 TM 완료", f"{tm1_count}건")
m3.metric("2차 TM 완료", f"{tm2_count}건")
m4.metric("3차 TM 완료", f"{tm3_count}건")
m5.metric("전체 TM 진행률", f"{tm_rate:.1f}%")
m6.metric("계약 완료(율)", f"{contract_count}건 ({contract_rate:.1f}%)")

st.markdown("---")
st.subheader("견적 및 TM 목록")

action_col1, action_col2, action_col3 = st.columns([1.1, 2.3, 2.3])
with action_col1: filter_tab = st.radio("표시 모드 선택", ["전체 목록 보기", "본인 작성 견적만 보기"])

display_df = my_df.copy()
if filter_tab == "본인 작성 견적만 보기": display_df = display_df[display_df['is_self'] == True]

col_order = ["선택/삭제", "상담일", "상담번호", "HC명", "대리점명", "고객명", "연락처", "주소", "상품", "세부품목", "현장유형", "견적금액", "1차_TM", "1차_TM_일자", "1차_증빙", "2차_TM", "2차_TM_일자", "2차_증빙", "3차_TM", "3차_TM_일자", "3차_증빙", "계약완료", "상담메모"] if is_master else ["선택/삭제", "상담일", "상담번호", "고객명", "연락처", "주소", "상품", "세부품목", "현장유형", "견적금액", "1차_TM", "1차_TM_일자", "1차_증빙", "2차_TM", "2차_TM_일자", "2차_증빙", "3차_TM", "3차_TM_일자", "3차_증빙", "계약완료", "상담메모"]

if not display_df.empty:
    st.markdown("<div style='margin-top: 15px;' class='table-header-banner'>상세 견적 목록 (삭제: 체크 후 1번 누름 / 단순 수정: 체크 없이 표 수정 후 2번 누름)</div>", unsafe_allow_html=True)
    
    # 💡 [핵심] 모든 칸 넓이를 small로 강제 압축 (주소 등 일부 제외) 및 '🔗보기' 로 글자 축소
    edited_df = st.data_editor(display_df, column_order=col_order, column_config={
        "선택/삭제": st.column_config.CheckboxColumn("선택/삭제", width="small"), 
        "상담일": st.column_config.DateColumn("상담일", format="MM/DD", width="small"),
        "상담번호": st.column_config.TextColumn("상담번호", width="small", disabled=True), 
        "고객명": st.column_config.TextColumn("고객명", width="small"),
        "연락처": st.column_config.TextColumn("연락처", width="small"),
        "주소": st.column_config.TextColumn("주소", width="medium"),
        "상품": st.column_config.TextColumn("상품", width="small"),
        "세부품목": st.column_config.TextColumn("세부품목 (더블클릭)", width="medium", help="더블클릭하여 전체 내용을 확인하세요."),
        "현장유형": st.column_config.TextColumn("현장유형", width="small"),
        "견적금액": st.column_config.NumberColumn("견적금액", format="%,d", width="small"), 
        "1차_TM": st.column_config.CheckboxColumn("1차", width="small"),
        "1차_TM_일자": st.column_config.DateColumn("1차 일자", format="MM/DD", width="small"), 
        "1차_증빙": st.column_config.LinkColumn("1차 증빙", display_text="🔗보기", width="small"),
        "2차_TM": st.column_config.CheckboxColumn("2차", width="small"), 
        "2차_TM_일자": st.column_config.DateColumn("2차 일자", format="MM/DD", width="small"),
        "2차_증빙": st.column_config.LinkColumn("2차 증빙", display_text="🔗보기", width="small"), 
        "3차_TM": st.column_config.CheckboxColumn("3차", width="small"),
        "3차_TM_일자": st.column_config.DateColumn("3차 일자", format="MM/DD", width="small"), 
        "3차_증빙": st.column_config.LinkColumn("3차 증빙", display_text="🔗보기", width="small"),
        "계약완료": st.column_config.CheckboxColumn("계약완료", width="small"), 
        "상담메모": st.column_config.TextColumn("상담메모", width="medium")
    }, hide_index=True, use_container_width=True, height=550) 
    
    with action_col2:
        st.markdown('<span class="red-btn"></span>', unsafe_allow_html=True)
        if st.button("1번 - 견적리스트 내용 완전 삭제하기", use_container_width=True):
            to_del = edited_df[edited_df['선택/삭제'] == True]['상담번호'].tolist()
            if to_del:
                with st.spinner("삭제 중..."):
                    st.session_state['data'] = clean_and_enforce_types(st.session_state['data'][~st.session_state['data']['상담번호'].isin(to_del)])
                    if save_data_to_sheet(client, st.session_state['data'], is_master, my_name): st.success("삭제 완료!"); st.session_state['uploader_key'] += 1; st.rerun()
            else: st.warning("삭제할 항목을 먼저 체크해 주세요!")

    with action_col3:
        st.markdown('<span class="yellow-btn"></span>', unsafe_allow_html=True)
        if st.button("2번 - 견적 리스트 작성 / 수정 후\n최종 저장 (필수)", use_container_width=True):
            with st.spinner("저장 중..."):
                tdf = edited_df.copy()
                tdf['선택/삭제'] = False 
                
                global_df = st.session_state['data'].copy()
                global_df = global_df.drop(display_df.index, errors='ignore')
                new_global_df = clean_and_enforce_types(pd.concat([global_df, tdf]).sort_values('상담일').reset_index(drop=True))
                
                if save_data_to_sheet(client, new_global_df, is_master, my_name): 
                    st.session_state['data'] = new_global_df
                    st.success("안전하게 전체 수정사항이 덮어쓰기 되었습니다!")
                    st.session_state['uploader_key'] += 1
                    st.rerun()
else: st.info("데이터가 없습니다. 견적을 추가해주세요!")
