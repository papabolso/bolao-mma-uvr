import io
import json
import pandas as pd
import requests
import streamlit as st

# ──────────────────────────────────────────────
# PAGE CONFIG & CSS (INTACTO)
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="UVR 2.0 – Bolão de MMA",
    page_icon="🥊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');
:root{--bg:#0d0d0d;--surface:#1a1a1a;--border:#2e2e2e;--accent:#e8002d;--gold:#f5c518;--text:#f0f0f0;--muted:#888}
html,body,[data-testid="stAppViewContainer"]{background:var(--bg)!important;color:var(--text)!important;font-family:'Barlow',sans-serif}
#MainMenu,footer,header{visibility:hidden}
.uvr-header{text-align:center;padding:2rem 0 1rem}
.uvr-header h1{font-family:'Bebas Neue',sans-serif;font-size:clamp(2.8rem,9vw,5rem);letter-spacing:.06em;color:var(--text);margin:0;line-height:1}
.uvr-header h1 span{color:var(--accent)}
.uvr-header p{color:var(--muted);font-size:.9rem;margin:.3rem 0 0}
[data-testid="stTabs"] [role="tablist"]{gap:4px;border-bottom:2px solid var(--border)}
[data-testid="stTabs"] button[role="tab"]{background:var(--surface);color:var(--muted);border-radius:6px 6px 0 0;border:1px solid var(--border);border-bottom:none;font-family:'Barlow',sans-serif;font-weight:700;letter-spacing:.05em;padding:.5rem 1.2rem;transition:all .2s}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.card{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1rem 1.2rem;margin-bottom:.8rem}
.card-title{font-family:'Bebas Neue',sans-serif;font-size:1.1rem;letter-spacing:.08em;color:var(--accent);margin-bottom:.4rem}
.fight-tag{display:inline-block;font-size:.7rem;font-weight:700;letter-spacing:.1em;padding:2px 8px;border-radius:4px;background:var(--accent);color:#fff;margin-bottom:.5rem}
.fight-tag.main{background:var(--gold);color:#000}
.fight-tag.co-main{background:#555}
.rank-table{width:100%;border-collapse:collapse}
.rank-table th{font-family:'Bebas Neue',sans-serif;font-size:.85rem;letter-spacing:.1em;color:var(--muted);border-bottom:2px solid var(--border);padding:.5rem .7rem;text-align:left}
.rank-table td{padding:.55rem .7rem;border-bottom:1px solid var(--border)}
.rank-table tr:last-child td{border-bottom:none}
.rank-table tr.top-1 td{color:var(--gold);font-weight:700}
.rank-table tr.top-2 td{color:#c0c0c0;font-weight:700}
.rank-table tr.top-3 td{color:#cd7f32;font-weight:700}
div[data-testid="stTextInput"] input,div[data-testid="stSelectbox"] select{background:var(--surface)!important;color:var(--text)!important;border:1px solid var(--border)!important;border-radius:8px!important}
div[data-testid="stButton"]>button{background:var(--accent)!important;color:#fff!important;border:none!important;border-radius:8px!important;font-family:'Bebas Neue',sans-serif!important;font-size:1.1rem!important;letter-spacing:.08em!important;width:100%;padding:.6rem 1rem!important;transition:opacity .2s!important}
div[data-testid="stButton"]>button:hover{opacity:.85!important}
hr{border-color:var(--border)!important;margin:1.2rem 0!important}
.admin-section{font-family:'Bebas Neue',sans-serif;font-size:1.3rem;letter-spacing:.1em;color:var(--accent);margin:1.2rem 0 .5rem;border-bottom:1px solid var(--border);padding-bottom:.3rem}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="uvr-header">
  <h1>UVR <span>2.0</span></h1>
  <p>Bolão Oficial de MMA</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# CONFIG (lê do secrets.toml)
# ──────────────────────────────────────────────
SHEET_ID        = st.secrets["gsheets"]["spreadsheet_id"]
LUTAS_GID       = int(st.secrets["gsheets"].get("lutas_gid", 0))
PALPITES_GID    = int(st.secrets["gsheets"].get("palpites_gid", 1))
RESULTADOS_GID  = int(st.secrets["gsheets"].get("resultados_gid", 2))
APPS_SCRIPT_URL = st.secrets["gsheets"]["apps_script_url"]

def csv_url(gid: int) -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

# ──────────────────────────────────────────────
# LEITURA PÚBLICA via Pandas
# ──────────────────────────────────────────────
@st.cache_data(ttl=60)
def load_lutas() -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_url(LUTAS_GID), dtype=str)
        df.columns = [c.strip() for c in df.columns]
        df["ID"] = df["ID"].str.strip()
        return df.dropna(subset=["ID"])
    except Exception:
        return pd.DataFrame(columns=["ID", "Lutador_1", "Lutador_2", "Tipo"])

@st.cache_data(ttl=60)
def load_palpites() -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_url(PALPITES_GID), dtype=str)
        df.columns = [c.strip() for c in df.columns]
        df["Luta_ID"] = df["Luta_ID"].str.strip()
        return df.dropna(subset=["Nome"])
    except Exception:
        return pd.DataFrame(columns=["Nome", "Luta_ID", "Palpite", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2"])

@st.cache_data(ttl=60)
def load_resultados() -> pd.DataFrame:
    try:
        df = pd.read_csv(csv_url(RESULTADOS_GID), dtype=str)
        df.columns = [c.strip() for c in df.columns]
        df["Luta_ID"] = df["Luta_ID"].str.strip()
        return df.dropna(subset=["Luta_ID"])
    except Exception:
        return pd.DataFrame(columns=["Luta_ID", "Vencedor_Real", "Pontos", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2", "F2_Especial"])

def invalidate_cache():
    load_lutas.clear()
    load_palpites.clear()
    load_resultados.clear()

# ──────────────────────────────────────────────
# ESCRITA via APPS SCRIPT
# ──────────────────────────────────────────────
def sheet_write(worksheet_name: str, df: pd.DataFrame):
    df = df.fillna("").astype(str)
    data_to_send = [df.columns.tolist()] + df.values.tolist()
    
    payload = {
        "sheet": worksheet_name,
        "data": data_to_send
    }
    
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        res_json = response.json()
        if response.status_code != 200 or res_json.get("status") != "success":
            raise Exception(f"Erro no Apps Script: {res_json.get('message', 'Erro desconhecido')}")
    except Exception as e:
        raise Exception(f"Falha de conexão com a planilha: {e}")

# ──────────────────────────────────────────────
# MOTOR DE PONTUAÇÃO (SEU ORIGINAL + PONTOS LIVRES + SELECIONE)
# ──────────────────────────────────────────────
def calcular_pontuacao(palpites_df:
