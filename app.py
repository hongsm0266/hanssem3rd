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

# --- 커스텀 CSS (PAPERLOGY 폰트 최적화 및 아이콘 보호 적용) ---
st.markdown("""
<style>
    /* 💡 PAPERLOGY 웹폰트 CDN 로드 */
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-8Bold.woff2') format('woff2'); font-weight: 700; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-9Black.woff2') format('woff2'); font-weight: 900; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-6SemiBold.woff2') format('woff2'); font-weight: 600; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-5Medium.woff2') format('woff2'); font-weight: 500; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-4Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }

    /* 💡 텍스트가 표시되는 영역에만 Paperlogy를 확실히 덮어씌움 */
    html, body, p, span, label, button, input, select, textarea, h1, h2, h3, h4, h5, h6, th, td {
        font-family: 'Paperlogy', -apple-system, sans-serif !important;
    }

    /* 🚨 시스템 아이콘 영역(화살표, 구름 등) 폰트 변환 강제 차단 */
    .stIconMaterial, .material-icons, [data-testid*="stIcon"], [data-baseweb="icon"] {
        font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
        font-weight: 400 !important;
    }

    .main .block-container,
    [data-testid="stMainBlockContainer"],
    [data-testid="stAppViewBlockContainer"] {
        max-width: 100% !important;
        padding-left: 1rem !important; padding-right: 1rem !important;
        padding-top: 1.5rem !important; padding-bottom: 1rem !important;
    }
    
    h1, h2, h3 { font-weight: 900 !important; color: #0f172a !important; font-size: 24px !important; letter-spacing: -0.5px !important; }

    .login-card-title { color: #0f172a; font-size: 22px !important; font-weight: 900 !important; margin-top: 15px; margin-bottom: 5px; }
    .login-card-sub { color: #64748b; font-size: 13px; margin-bottom: 20px; font-weight: 600; }
    
    div.stButton > button { 
        background: linear-gradient(180deg, #2563eb 0%, #1d4ed8 100%) !important; color: white !important; font-size: 15px !important; font-weight: 800 !important; 
        border-radius: 8px !important; padding: 10px 15px !important; border: none !important; height: auto !important; min-height: 45px; box-shadow: 0 4px 6px rgba(0,0,0,0.1) !important;
        border-bottom: 4px solid #1e3a8a !important; transition: all 0.1s ease !important; 
    }
    div.stButton > button:hover { transform: translateY(-2px) !important; }
    div.stButton > button:active { transform: translateY(2px) !important; border-bottom: 1px solid #1e3a8a !important; margin-bottom: 3px !important; }
    
    div.element-container:has(.red-btn) + div.element-container div.stButton > button { background: linear-gradient(180deg, #ef4444 0%, #dc2626 100%) !important; border-bottom: 4px solid #991b1b !important; }
    div.element-container:has(.yellow-btn) + div.element-container div.stButton > button { background: linear-gradient(180deg, #facc15 0%, #eab308 100%) !important; border-bottom: 4px solid #a16207 !important; color: #1c1917 !important; }

    .user-info-box { background-color: #f1f5f9; border: 2px solid #0284c7; padding: 12px 16px; border-radius: 8px; text-align: right; }
    .user-info-name { font-size: 18px !important; font-weight: 900 !important; color: #0369a1 !important; }
    .user-info-sub { font-size: 12px !important; color: #64748b !important; font-weight: 600; }
    .table-header-banner { background-color: #0056b3; color: white; padding: 10px 16px; border-radius: 6px 6px 0 0; font-weight: 800; font-size: 16px; margin-bottom: -10px; display: flex; justify-content: space-between; align-items: center;}

    [data-testid="stDataFrame"] th svg { display: none !important; }
    [data-testid="stDataFrame"] th { font-weight: 900 !important; color: #0f172a !important; font-size: 14px !important; background-color: #f8fafc !important; }

    .dash-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; margin-top: 8px; }
    .dash-card { 
        background: white; border-radius: 8px; padding: 14px 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.06); 
        border: 1px solid #e2e8f0; text-align: center; border-top: 5px solid #3b82f6; 
        display: flex; flex-direction: column; justify-content: center; align-items: center;
    }
    .dash-card.green { border-top-color: #10b981; }
    .dash-card.purple { border-top-color: #8b5cf6; }
    .dash-card.orange { border-top-color: #f97316; }
    .dash-card.red { border-top-color: #ef4444; }
    .dash-title { font-size: 12px; color: #64748b; font-weight: 700; margin-bottom: 6px; letter-spacing: -0.5px; word-break: keep-all;}
    .dash-value { font-size: 18px; color: #0f172a; font-weight: 900; letter-spacing: -0.5px; word-break: keep-all;}
    
    [data-testid="stExpander"] {
        background-color: #f8fafc !important;
        border: 2px solid #cbd5e1 !important;
        border-radius: 12px !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05) !important;
    }
    [data-testid="stExpander"] summary {
        background-color: #e0f2fe !important; 
        border-radius: 10px 10px 0 0 !important;
        padding-top: 12px !important;
        padding-bottom: 12px !important;
        border-bottom: 1px solid #bae6fd !important;
    }
    [data-testid="stExpander"] summary p {
        font-size: 16px !important;
        font-weight: 900 !important;
        color: #0369a1 !important;
    }
</style>
