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

st.markdown("""
<style>
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-8Bold.woff2') format('woff2'); font-weight: 700; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-9Black.woff2') format('woff2'); font-weight: 900; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-6SemiBold.woff2') format('woff2'); font-weight: 600; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-5Medium.woff2') format('woff2'); font-weight: 500; font-display: swap; }
    @font-face { font-family: 'Paperlogy'; src: url('https://cdn.jsdelivr.net/gh/projectnoonnu/2408-3@1.0/Paperlogy-4Regular.woff2') format('woff2'); font-weight: 400; font-display: swap; }

    html, body, p, span, label, button, input, select, textarea, h1, h2, h3, h4, h5, h6, th, td {
        font-family: 'Paperlogy', -apple-system, sans-serif !important;
    }
    .stIconMaterial, .material-icons, [data-testid*="stIcon"], [data-baseweb="icon"] {
        font-family: "Material Symbols Rounded", "Material Icons", sans-serif !important;
        font-weight: 400 !important;
    }
    .main .block-container, [data-testid="stMainBlockContainer"], [data-testid="stAppViewBlockContainer"] {
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
        border-bottom: 4px solid #1e3a8a !important; transition: all 0
