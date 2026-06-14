"""
UFC White House — Bolão UVR
Streamlit + Supabase
"""
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta
from supabase import create_client, Client

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="UFC White House · Bolão UVR",
    page_icon="🦅",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CSS — UFC White House theme (marfim + navy + vermelho + dourado)
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Cinzel:wght@600;700;900&family=Oswald:wght@400;500;700&family=Inter:wght@400;500;600&display=swap');

:root{
  --mm-red:#B22234;          /* US flag red */
  --mm-red-dark:#7a0c1f;
  --mm-purple:#3C3B6E;       /* US flag navy */
  --mm-purple-dark:#1f1e4a;
  --mm-gold:#C9A227;         /* dourado presidencial */
  --mm-gold-bright:#E8C547;
  --bg:#F5F1E8;              /* marfim/cream */
  --bg-dark:#EBE5D4;
  --surface:#ffffff;
  --surface-2:#FAF6EC;
  --border:#D4C9A8;
  --text:#1A1A2E;            /* navy escuro pro texto */
  --muted:#6B6450;
}

html,body,[data-testid="stAppViewContainer"]{
  background:
    linear-gradient(180deg, rgba(245,241,232,1) 0%, rgba(235,229,212,1) 100%) fixed !important;
  color:var(--text)!important;
  font-family:'Inter',sans-serif;
}
#MainMenu,footer,header{visibility:hidden}

/* HERO — Casa Branca presidencial */
.nfx-hero{
  position:relative;
  text-align:center;
  padding:3rem 1rem 2rem;
  background:
    linear-gradient(180deg, #ffffff 0%, #FAF6EC 100%);
  border-bottom:6px double var(--mm-gold);
  margin:-1rem -1rem 1.5rem;
  overflow:hidden;
  box-shadow:0 4px 30px rgba(60,59,110,.08);
}
/* Listras vermelhas no topo (bandeira USA stylized) */
.nfx-hero::before{
  content:"";
  position:absolute;
  top:0; left:0; right:0;
  height:8px;
  background:repeating-linear-gradient(
    90deg,
    var(--mm-red) 0 60px,
    #ffffff 60px 120px
  );
}
/* Estrelas no fundo */
.nfx-hero::after{
  content:"★ ★ ★";
  position:absolute;
  top:20px; left:50%;
  transform:translateX(-50%);
  font-size:1rem;
  color:var(--mm-gold);
  letter-spacing:1.2em;
  opacity:.6;
}

.nfx-brand{
  font-family:'Cinzel',serif;
  font-size:.85rem;
  letter-spacing:.45em;
  color:var(--mm-purple);
  margin:1.5rem 0 0;
  text-transform:uppercase;
  font-weight:600;
}
.nfx-title{
  font-family:'Playfair Display',serif;
  font-size:clamp(2.4rem, 8vw, 4rem);
  letter-spacing:.01em;
  font-weight:900;
  color:var(--mm-purple);
  margin:.5rem 0 0;
  line-height:1;
  text-transform:uppercase;
}
.nfx-title-accent{
  display:block;
  font-family:'Cinzel',serif;
  font-size:.55em;
  letter-spacing:.3em;
  color:var(--mm-red);
  margin-top:.3rem;
  font-weight:700;
}
.nfx-subtitle{
  font-family:'Inter',sans-serif;
  font-size:1rem;
  letter-spacing:.08em;
  color:var(--muted);
  margin:.7rem 0 0;
  text-transform:uppercase;
  font-weight:500;
}
.nfx-badge{
  display:inline-block;
  font-family:'Cinzel',serif;
  font-size:.7rem;
  letter-spacing:.25em;
  padding:6px 18px;
  background:transparent;
  color:var(--mm-purple);
  border:1.5px solid var(--mm-gold);
  border-radius:0;
  margin-top:1rem;
  text-transform:uppercase;
  font-weight:600;
}

/* SELO DOURADO (águia/eagle vibe) */
.seal{
  display:inline-flex;
  align-items:center;
  justify-content:center;
  width:80px; height:80px;
  border:3px solid var(--mm-gold);
  border-radius:50%;
  background:linear-gradient(135deg, var(--mm-gold-bright), var(--mm-gold));
  font-size:2.2rem;
  margin:0 auto 1rem;
  box-shadow:0 4px 20px rgba(201,162,39,.4), inset 0 -3px 8px rgba(0,0,0,.15);
  position:relative;
}
.seal::before{
  content:"";
  position:absolute;
  inset:-8px;
  border:1px solid var(--mm-gold);
  border-radius:50%;
  opacity:.5;
}

/* TABS */
[data-testid="stTabs"] [role="tablist"]{
  gap:0;
  border-bottom:2px solid var(--mm-gold);
  background:transparent;
}
[data-testid="stTabs"] button[role="tab"]{
  background:transparent;
  color:var(--muted);
  border:none;
  border-bottom:3px solid transparent;
  border-radius:0;
  font-family:'Cinzel',serif;
  font-weight:600;
  letter-spacing:.15em;
  text-transform:uppercase;
  padding:.7rem 1.2rem;
  font-size:.85rem;
  transition:all .2s;
  margin-bottom:-2px;
}
[data-testid="stTabs"] button[role="tab"]:hover{color:var(--mm-purple)}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"]{
  color:var(--mm-purple);
  border-bottom-color:var(--mm-red);
  background:transparent;
}

/* CARDS de luta */
.fight-card{
  background:var(--surface);
  border:1px solid var(--border);
  border-left:5px solid var(--mm-red);
  border-radius:2px;
  padding:1.1rem 1.3rem;
  margin-bottom:.9rem;
  position:relative;
  overflow:hidden;
  transition:transform .15s, box-shadow .15s;
  box-shadow:0 2px 8px rgba(60,59,110,.06);
}
.fight-card:hover{
  transform:translateX(2px);
  box-shadow:0 4px 16px rgba(60,59,110,.12);
}
/* Lutas MAIN/CO-MAIN — destaque dourado/navy */
.fight-card.main{
  border-left-color:var(--mm-gold);
  background:linear-gradient(135deg, #ffffff 0%, #FAF6EC 100%);
  border-color:var(--mm-gold);
  box-shadow:0 4px 20px rgba(201,162,39,.18);
}
.fight-card.co-main{
  border-left-color:var(--mm-purple);
  background:linear-gradient(135deg, #ffffff 0%, #F5F2F8 100%);
}

.fight-tag{
  display:inline-block;
  font-family:'Cinzel',serif;
  font-size:.65rem;
  font-weight:700;
  letter-spacing:.25em;
  padding:4px 12px;
  background:var(--mm-red);
  color:#fff;
  margin-bottom:.7rem;
  text-transform:uppercase;
  border-radius:0;
}
.fight-tag.main{background:var(--mm-gold); color:var(--mm-purple)}
.fight-tag.co-main{background:var(--mm-purple); color:var(--mm-gold)}
.fight-tag.prelim{
  background:transparent;
  color:var(--muted);
  border:1px solid var(--border);
}

.fight-vs{
  font-family:'Playfair Display',serif;
  font-size:1.4rem;
  font-weight:700;
  letter-spacing:.005em;
  color:var(--text);
  line-height:1.2;
}
.fight-vs .vs{
  color:var(--mm-red);
  margin:0 .5em;
  font-size:.75em;
  font-style:italic;
  font-family:'Cinzel',serif;
  letter-spacing:.15em;
}
.fight-card.main .fight-vs .vs{color:var(--mm-gold)}

/* RANKING */
.rank-table{
  width:100%;
  border-collapse:collapse;
  background:var(--surface);
  border:1px solid var(--border);
  box-shadow:0 2px 12px rgba(60,59,110,.08);
}
.rank-table th{
  font-family:'Cinzel',serif;
  font-size:.7rem;
  letter-spacing:.2em;
  color:var(--mm-purple);
  border-bottom:2px solid var(--mm-gold);
  padding:.8rem .6rem;
  text-align:left;
  text-transform:uppercase;
  font-weight:700;
  background:var(--surface-2);
}
.rank-table td{
  padding:.8rem .6rem;
  border-bottom:1px solid var(--border);
  font-family:'Inter',sans-serif;
  color:var(--text);
}
.rank-table tr:last-child td{border-bottom:none}
.rank-table tr.top-1 td{color:var(--mm-gold); font-weight:700; background:rgba(201,162,39,.05)}
.rank-table tr.top-2 td{color:#7a7a7a; font-weight:700}
.rank-table tr.top-3 td{color:#a16832; font-weight:700}
.rank-table tr:hover td{background:rgba(178,34,52,.04)}

/* INPUTS */
div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] select,
[data-baseweb="select"] > div,
[data-baseweb="input"] input,
div[data-testid="stNumberInput"] input{
  background:var(--surface)!important;
  color:var(--text)!important;
  border:1px solid var(--border)!important;
  border-radius:2px!important;
  font-family:'Inter',sans-serif!important;
}
div[data-testid="stTextInput"] input:focus,
[data-baseweb="input"] input:focus{
  border-color:var(--mm-gold)!important;
  box-shadow:0 0 0 2px rgba(201,162,39,.2)!important;
}

/* DROPDOWNS (selectbox/multiselect aberto) — popup tema claro */
[data-baseweb="popover"],
[data-baseweb="menu"],
[role="listbox"]{
  background:#ffffff!important;
  border:1px solid var(--mm-gold)!important;
  border-radius:2px!important;
  box-shadow:0 8px 24px rgba(60,59,110,.18)!important;
}
[data-baseweb="menu"] li,
[role="option"]{
  background:#ffffff!important;
  color:var(--text)!important;
  font-family:'Inter',sans-serif!important;
  border-bottom:1px solid #F0EBDC!important;
}
[data-baseweb="menu"] li:hover,
[role="option"]:hover,
[role="option"][aria-selected="true"]{
  background:rgba(201,162,39,.12)!important;
  color:var(--mm-purple)!important;
}
[data-baseweb="select"] [data-baseweb="tag"]{
  background:var(--mm-gold)!important;
  color:var(--mm-purple)!important;
}
/* Texto exibido no select fechado */
[data-baseweb="select"] *{color:var(--text)!important}

/* BOTÕES — estilo presidencial */
div[data-testid="stButton"]>button{
  background:linear-gradient(180deg, var(--mm-purple) 0%, var(--mm-purple-dark) 100%)!important;
  color:#fff!important;
  border:1px solid var(--mm-gold)!important;
  border-radius:2px!important;
  font-family:'Cinzel',serif!important;
  font-size:.9rem!important;
  font-weight:700!important;
  letter-spacing:.18em!important;
  text-transform:uppercase!important;
  width:100%;
  padding:.75rem 1rem!important;
  transition:all .2s!important;
  box-shadow:0 2px 6px rgba(60,59,110,.2)!important;
}
div[data-testid="stButton"]>button:hover{
  background:linear-gradient(180deg, #4a497f 0%, #2a2a5e 100%)!important;
  transform:translateY(-1px);
  box-shadow:0 4px 14px rgba(201,162,39,.3)!important;
  border-color:var(--mm-gold-bright)!important;
}

/* RADIO buttons (pills) */
div[data-testid="stRadio"] > div{gap:.5rem}
div[data-testid="stRadio"] label{
  background:var(--surface);
  border:1.5px solid var(--border);
  border-radius:2px;
  padding:.55rem 1rem;
  transition:all .2s;
}
div[data-testid="stRadio"] label:hover{
  border-color:var(--mm-gold);
  background:rgba(201,162,39,.05);
}

hr{border:none; border-top:2px double var(--mm-gold)!important; margin:1.8rem 0!important; opacity:.5}

.section-title{
  font-family:'Cinzel',serif;
  font-size:1.2rem;
  letter-spacing:.2em;
  color:var(--mm-purple);
  margin:1.6rem 0 .9rem;
  padding-bottom:.5rem;
  border-bottom:2px solid var(--mm-gold);
  display:inline-block;
  text-transform:uppercase;
  font-weight:700;
}
.admin-section{
  font-family:'Cinzel',serif;
  font-size:1rem;
  letter-spacing:.2em;
  color:var(--mm-red);
  margin:1.6rem 0 .6rem;
  padding-bottom:.4rem;
  border-bottom:1px solid var(--border);
  text-transform:uppercase;
  font-weight:700;
}
.event-info{
  background:var(--surface);
  border:1px solid var(--mm-gold);
  border-radius:2px;
  padding:1.1rem;
  margin-bottom:1.2rem;
  text-align:center;
  font-family:'Cinzel',serif;
  letter-spacing:.1em;
  box-shadow:0 2px 12px rgba(201,162,39,.1);
  position:relative;
}
.event-info::before, .event-info::after{
  content:"★";
  color:var(--mm-gold);
  position:absolute;
  top:50%;
  transform:translateY(-50%);
  font-size:.9rem;
}
.event-info::before{left:1rem}
.event-info::after{right:1rem}
.event-info .venue{
  color:var(--mm-purple);
  font-size:.8rem;
  text-transform:uppercase;
  letter-spacing:.25em;
  font-weight:600;
}
.event-info .date{
  color:var(--mm-red);
  font-size:1.3rem;
  margin-top:.4rem;
  font-family:'Playfair Display',serif;
  font-weight:900;
  letter-spacing:.05em;
}

/* Captions e texto secundário */
.stCaption, [data-testid="stCaptionContainer"], small{
  color:var(--muted)!important;
}

/* Markdown geral */
p, li, span, div{color:var(--text)}

/* Tabs container — fundo */
[data-testid="stTabs"]{background:transparent}

/* Expanders */
[data-testid="stExpander"]{
  border:1px solid var(--border)!important;
  border-radius:2px!important;
  background:var(--surface)!important;
}
[data-testid="stExpander"] summary{
  font-family:'Cinzel',serif!important;
  letter-spacing:.1em;
  color:var(--mm-purple)!important;
}

/* Dataframes */
[data-testid="stDataFrame"]{
  border:1px solid var(--border);
  border-radius:2px;
}

/* Alerts */
[data-testid="stAlert"]{
  border-radius:2px!important;
  border-left:4px solid var(--mm-gold)!important;
}
/* Dropdowns abertos (menu de opções) — força tema claro */
[data-baseweb="popover"],
[data-baseweb="menu"],
[data-baseweb="select-dropdown"],
ul[role="listbox"]{
  background:var(--surface)!important;
  border:1px solid var(--mm-gold)!important;
  box-shadow:0 4px 20px rgba(60,59,110,.15)!important;
}
[data-baseweb="popover"] *,
[data-baseweb="menu"] *,
ul[role="listbox"] *{
  background:transparent!important;
  color:var(--text)!important;
  font-family:'Inter',sans-serif!important;
}
li[role="option"]{
  background:transparent!important;
  color:var(--text)!important;
  padding:.5rem .8rem!important;
}
li[role="option"]:hover,
li[role="option"][aria-selected="true"]{
  background:rgba(201,162,39,.15)!important;
  color:var(--mm-purple)!important;
}

/* Dataframes (VAR / Histórico) */
[data-testid="stDataFrame"], [data-testid="stDataFrame"] *{
  background:var(--surface)!important;
  color:var(--text)!important;
}
[data-testid="stDataFrame"] th{
  background:var(--surface-2)!important;
  color:var(--mm-purple)!important;
  font-family:'Cinzel',serif!important;
}
/* Texto interno do dataframe (st.dataframe) — força preto */
[data-testid="stDataFrame"] div,
[data-testid="stDataFrame"] span,
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] [role="gridcell"],
[data-testid="stDataFrame"] [role="columnheader"]{
  color:var(--text)!important;
  background:var(--surface)!important;
}
[data-testid="stDataFrame"] [role="columnheader"]{
  background:var(--surface-2)!important;
  color:var(--mm-purple)!important;
}
/* Glide data grid (engine novo do Streamlit) */
.gdg-wmyidgi, .gdg-d2etrhh{
  background:var(--surface)!important;
  color:var(--text)!important;
}

/* Alerts (info, success, warning, error) — fundo claro */
[data-testid="stAlert"]{
  background:var(--surface)!important;
  color:var(--text)!important;
}
[data-testid="stAlert"] *{color:var(--text)!important}

</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────
st.markdown("""
<div class="nfx-hero">
  <div class="seal">🦅</div>
  <p class="nfx-brand">★ Ultimate Fighting Championship ★</p>
  <h1 class="nfx-title">
    The White House
    <span class="nfx-title-accent">UFC · Bolão UVR</span>
  </h1>
  <p class="nfx-subtitle">Fight Night Histórico · 1600 Pennsylvania Ave</p>
  <span class="nfx-badge">It's Time, Mr. President</span>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# SUPABASE
# ──────────────────────────────────────────────
@st.cache_resource
def get_client() -> Client:
    return create_client(
        st.secrets["supabase"]["url"],
        st.secrets["supabase"]["key"],
    )

sb = get_client()

@st.cache_data(ttl=30)
def load_lutas() -> pd.DataFrame:
    res = sb.table("lutas").select("*").order("ordem").execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        df = pd.DataFrame(columns=["id","lutador_1","lutador_2","tipo","ordem"])
    return df

@st.cache_data(ttl=30)
def load_palpites() -> pd.DataFrame:
    res = sb.table("palpites").select("*").execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        df = pd.DataFrame(columns=["nome","luta_id","palpite","fotn_1","fotn_2","potn_1","potn_2"])
    return df

@st.cache_data(ttl=30)
def load_resultados() -> pd.DataFrame:
    res = sb.table("resultados").select("*").execute()
    df = pd.DataFrame(res.data or [])
    if df.empty:
        df = pd.DataFrame(columns=["luta_id","vencedor_real","pontos"])
    return df

@st.cache_data(ttl=30)
def load_config() -> dict:
    res = sb.table("config").select("*").eq("id", 1).execute()
    if res.data and len(res.data) > 0:
        return res.data[0]
    return {}

def invalidate_cache():
    load_lutas.clear()
    load_palpites.clear()
    load_resultados.clear()
    load_config.clear()

# ──────────────────────────────────────────────
# MOTOR DE PONTUAÇÃO (mesma lógica do original, adaptada pra Supabase)
# ──────────────────────────────────────────────
def calcular_ranking(palpites: pd.DataFrame, lutas: pd.DataFrame, resultados: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    if palpites.empty or lutas.empty or resultados.empty:
        return pd.DataFrame()

    res_map = resultados.set_index("luta_id")
    luta_map = lutas.set_index("id")
    lutas_ordenadas = sorted(lutas["id"].dropna().unique(), key=lambda x: int(x))

    f2_especial = bool(cfg.get("f2_especial", False))

    fotn_real = {str(cfg.get("fotn_1","")).strip().upper(),
                 str(cfg.get("fotn_2","")).strip().upper()} - {"", "NAN", "NONE"}
    potn_str = str(cfg.get("potn_1","")).strip().upper()
    potn_real = {p.strip() for p in potn_str.split(",")} - {""} if potn_str and potn_str != "NONE" else set()

    scores = {}
    for _, row in palpites.iterrows():
        nome = str(row["nome"]).strip()
        luta_id = int(row["luta_id"])
        palpite = str(row.get("palpite","")).strip()

        if nome not in scores:
            scores[nome] = {
                "Pontos":0, "Acertos":0, "Acerto_F1":0, "Acerto_F2":0,
                "_fotn_1":str(row.get("fotn_1","")).strip(),
                "_fotn_2":str(row.get("fotn_2","")).strip(),
                "_potn_1":str(row.get("potn_1","")).strip(),
                "_potn_2":str(row.get("potn_2","")).strip(),
                "Desempate_Lutas":{lid:0 for lid in lutas_ordenadas},
            }

        if luta_id not in res_map.index: continue
        vencedor = str(res_map.at[luta_id,"vencedor_real"]).strip().upper()
        if vencedor in ("EMPATE","CANCELADA","","SELECIONE","NONE"): continue

        tipo = str(luta_map.at[luta_id,"tipo"]).strip().upper() if luta_id in luta_map.index else "PRELIM"
        acertou = palpite.upper() == vencedor
        peso = 2 if tipo == "F1" else (2 if (tipo == "F2" and f2_especial) else 1)

        # peso custom da luta
        p_val = res_map.loc[luta_id,"pontos"] if "pontos" in res_map.columns else None
        if p_val is not None and str(p_val).strip() not in ("","nan","None"):
            try: peso = int(float(p_val))
            except: pass

        if acertou:
            scores[nome]["Pontos"] += peso
            scores[nome]["Acertos"] += 1
            if tipo == "F1": scores[nome]["Acerto_F1"] += 1
            if tipo == "F2": scores[nome]["Acerto_F2"] += 1
            scores[nome]["Desempate_Lutas"][luta_id] = 1

    # Bônus FOTN/POTN
    for acc in scores.values():
        if fotn_real:
            fu = {acc["_fotn_1"].upper(), acc["_fotn_2"].upper()} - {"","NAN","NONE"}
            if fu and fu == fotn_real: acc["Pontos"] += 2
        if potn_real:
            pu = {acc["_potn_1"].upper(), acc["_potn_2"].upper()} - {"","NAN","NONE"}
            acc["Pontos"] += sum(1 for n in pu if n in potn_real)

    if not scores: return pd.DataFrame()

    linhas = []
    for n, v in scores.items():
        linha = {"Nome":n, "Pontos":v["Pontos"], "Acertos":v["Acertos"],
                 "Acerto_F1":v["Acerto_F1"], "Acerto_F2":v["Acerto_F2"]}
        for lid in lutas_ordenadas:
            linha[f"Luta_{lid}"] = v["Desempate_Lutas"][lid]
        linhas.append(linha)

    df = pd.DataFrame(linhas)
    cols_sort = ["Pontos","Acertos"] + [f"Luta_{l}" for l in lutas_ordenadas] + ["Nome"]
    asc = [False,False] + [False]*len(lutas_ordenadas) + [True]
    df = df.sort_values(cols_sort, ascending=asc).reset_index(drop=True)
    df.insert(0, "Pos", range(1, len(df)+1))
    return df

# ──────────────────────────────────────────────
# CRONÔMETRO
# ──────────────────────────────────────────────
def render_timer(target_str: str, title: str, color="#B22234", end_text="ENCERRADO"):
    try:
        dt_obj = datetime.strptime(target_str, "%d/%m/%Y %H:%M")
        iso_str = dt_obj.strftime("%Y-%m-%dT%H:%M:00-03:00")
        html = f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@900&family=Cinzel:wght@600&display=swap');
        .tbox{{background:#ffffff;border:2px solid #C9A227;border-radius:2px;padding:14px;text-align:center;margin-bottom:18px;position:relative;overflow:hidden;box-shadow:0 2px 12px rgba(201,162,39,.15)}}
        .tbox::before{{content:"";position:absolute;inset:0;background:linear-gradient(90deg,transparent,{color}10,transparent);animation:sweep 3s infinite}}
        @keyframes sweep{{0%{{transform:translateX(-100%)}}100%{{transform:translateX(100%)}}}}
        .ttitle{{font-family:'Cinzel',serif;color:#3C3B6E;font-size:.8rem;letter-spacing:.25em;text-transform:uppercase;position:relative;font-weight:600}}
        .ttime{{font-family:'Playfair Display',serif;font-size:2.4rem;color:{color};letter-spacing:.03em;margin-top:2px;position:relative;font-weight:900}}
        </style>
        <div class="tbox">
          <div class="ttitle">★ {title} ★</div>
          <div class="ttime" id="clk">CALCULANDO...</div>
        </div>
        <script>
        var t=new Date("{iso_str}").getTime();
        var x=setInterval(function(){{
          var n=new Date().getTime(); var d=t-n;
          if(d<0){{clearInterval(x); document.getElementById("clk").innerHTML="{end_text}"; return}}
          var dd=Math.floor(d/(1000*60*60*24));
          var hh=Math.floor((d%(1000*60*60*24))/(1000*60*60));
          var mm=Math.floor((d%(1000*60*60))/(1000*60));
          var ss=Math.floor((d%(1000*60))/1000);
          var s=""; if(dd>0) s+=dd+"d ";
          s+=(hh<10?"0":"")+hh+"h "+(mm<10?"0":"")+mm+"m "+(ss<10?"0":"")+ss+"s";
          document.getElementById("clk").innerHTML=s;
        }},1000);
        </script>
        """
        components.html(html, height=120)
    except Exception:
        pass

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_votar, tab_ranking, tab_admin = st.tabs(["🥊 Palpitar", "🏆 Ranking", "🔐 Admin"])

# ============== VOTAR ==============
with tab_votar:
    lutas = load_lutas()
    cfg = load_config()
    agora = datetime.utcnow() - timedelta(hours=3)

    status = "ABERTO"
    abertura_str = (cfg.get("abertura") or "").strip()
    fechamento_str = (cfg.get("fechamento") or "").strip()

    if cfg.get("bloqueado"): status = "FECHADO"
    if abertura_str:
        try:
            if agora < datetime.strptime(abertura_str, "%d/%m/%Y %H:%M"):
                status = "AGUARDANDO"
        except: pass
    if fechamento_str and status != "AGUARDANDO":
        try:
            if agora >= datetime.strptime(fechamento_str, "%d/%m/%Y %H:%M"):
                status = "FECHADO"
        except: pass

    if lutas.empty:
        st.warning("Nenhuma luta cadastrada ainda.")
    elif status == "AGUARDANDO":
        st.info(f"⏳ Os palpites abrem em **{abertura_str}** (BRT).")
        render_timer(abertura_str, "ABRE EM", color="#46d369", end_text="ABERTO · ATUALIZE")
    elif status == "FECHADO":
        st.error("🚨 BOLÃO ENCERRADO · O evento já começou.")
        st.info("Acompanhe na aba Ranking. Boa sorte!")
    else:
        if fechamento_str:
            render_timer(fechamento_str, "FECHA EM", color="#E50914", end_text="FECHADO!")

        st.markdown('<div class="section-title">Identifique-se</div>', unsafe_allow_html=True)
        nome_usuario = st.text_input("Nome", placeholder="Seu nome completo", label_visibility="collapsed")

        st.markdown('<div class="section-title">Palpites</div>', unsafe_allow_html=True)
        palpites_usuario = {}
        todos_lutadores = []
        lista_lutas_fmt = []

        tag_map = {
            "F1": ("main", "MAIN EVENT"),
            "F2": ("co-main", "CO-MAIN"),
            "PRINCIPAL": ("", "MAIN CARD"),
            "PRELIM": ("prelim", "MAIN CARD"),
        }

        for _, luta in lutas.iterrows():
            lid = int(luta["id"])
            l1, l2 = str(luta["lutador_1"]).strip(), str(luta["lutador_2"]).strip()
            tipo = str(luta["tipo"]).strip().upper()
            todos_lutadores.extend([l1, l2])
            lista_lutas_fmt.append(f"{l1} vs {l2}")
            tag_class, tag_label = tag_map.get(tipo, ("", "FIGHT"))

            st.markdown(f"""
            <div class="fight-card {tag_class}">
              <span class="fight-tag {tag_class}">{tag_label}</span>
              <div class="fight-vs">{l1} <span class="vs">vs</span> {l2}</div>
            </div>
            """, unsafe_allow_html=True)
            escolha = st.radio(
                f"Vencedor da luta {lid}",
                options=[l1, l2],
                horizontal=True,
                label_visibility="collapsed",
                key=f"luta_{lid}",
            )
            palpites_usuario[lid] = escolha

        st.markdown('<div class="section-title">Bônus da Noite</div>', unsafe_allow_html=True)
        todos_uniq = sorted(set(todos_lutadores))
        vazio = ["— Selecione —"]
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🌟 Luta da Noite**")
            fotn_sel = st.selectbox("FOTN", vazio + lista_lutas_fmt,
                                    key="fotn_v", label_visibility="collapsed")
        with c2:
            st.markdown("**⚡ Performance da Noite**")
            potn_sel = st.selectbox("POTN", vazio + todos_uniq,
                                    key="potn_v", label_visibility="collapsed")

        st.markdown("---")
        if st.button("✅ ENVIAR PALPITES"):
            nome_limpo = nome_usuario.strip()
            if not nome_limpo:
                st.error("Informe seu nome.")
            else:
                if fotn_sel != "— Selecione —":
                    f1v, f2v = fotn_sel.split(" vs ")
                else:
                    f1v, f2v = "", ""
                p1v = "" if potn_sel == "— Selecione —" else potn_sel

                try:
                    # Apaga os palpites antigos desse nome (case-insensitive)
                    sb.table("palpites").delete().ilike("nome", nome_limpo).execute()
                    # Insere os novos
                    rows = [{
                        "nome": nome_limpo,
                        "luta_id": lid,
                        "palpite": pal,
                        "fotn_1": f1v, "fotn_2": f2v,
                        "potn_1": p1v, "potn_2": "",
                    } for lid, pal in palpites_usuario.items()]
                    sb.table("palpites").insert(rows).execute()
                    invalidate_cache()
                    st.success(f"🥊 Palpites de **{nome_limpo}** salvos com sucesso!")
                    # Som de gong (Web Audio API — sem dependências)
                    components.html("""
                    <script>
                    try {
                      const ctx = new (window.AudioContext || window.webkitAudioContext)();
                      const now = ctx.currentTime;
                      // Gong principal: oscilador com decay longo + harmônicos
                      const freqs = [110, 220, 330, 440];
                      freqs.forEach((f, i) => {
                        const osc = ctx.createOscillator();
                        const gain = ctx.createGain();
                        osc.type = 'sine';
                        osc.frequency.value = f;
                        gain.gain.setValueAtTime(0, now);
                        gain.gain.linearRampToValueAtTime(0.25 / (i+1), now + 0.01);
                        gain.gain.exponentialRampToValueAtTime(0.001, now + 2.5);
                        osc.connect(gain).connect(ctx.destination);
                        osc.start(now);
                        osc.stop(now + 2.5);
                      });
                    } catch(e) {}
                    </script>
                    """, height=0)
                    st.balloons()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ============== RANKING ==============
with tab_ranking:
    lutas_df = load_lutas()
    palpites_df = load_palpites()
    resultados_df = load_resultados()
    cfg = load_config()

    ranking = calcular_ranking(palpites_df, lutas_df, resultados_df, cfg)

    if ranking.empty:
        st.info("O ranking aparece após o admin inserir os primeiros resultados.")
        if not palpites_df.empty:
            st.caption(f"Participantes confirmados: **{palpites_df['nome'].nunique()}**")
    else:
        medals = {1:"🥇", 2:"🥈", 3:"🥉"}
        rows = ""
        for _, r in ranking.iterrows():
            pos = int(r["Pos"])
            cls = f"top-{pos}" if pos <= 3 else ""
            medal = medals.get(pos, "")
            rows += (
                f'<tr class="{cls}">'
                f'<td>{medal} {pos}º</td>'
                f'<td>{r["Nome"]}</td>'
                f'<td style="text-align:center">{int(r["Pontos"])}</td>'
                f'<td style="text-align:center">{int(r["Acertos"])}</td>'
                f'<td style="text-align:center">{"✅" if int(r["Acerto_F1"]) else "❌"}</td>'
                f'<td style="text-align:center">{"✅" if int(r["Acerto_F2"]) else "❌"}</td>'
                f'</tr>'
            )
        st.markdown(
            f'<table class="rank-table">'
            f'<thead><tr>'
            f'<th>POS</th><th>NOME</th>'
            f'<th style="text-align:center">PTS</th>'
            f'<th style="text-align:center">ACERTOS</th>'
            f'<th style="text-align:center">F1</th>'
            f'<th style="text-align:center">F2</th>'
            f'</tr></thead><tbody>{rows}</tbody></table>',
            unsafe_allow_html=True,
        )
        st.caption("Desempate: Pts › Acertos › Luta 1 › Luta 2 › ... › Nome")

        st.markdown("---")
        st.markdown('<div class="admin-section">🔍 VAR · Histórico</div>', unsafe_allow_html=True)
        opc = ["— Selecione —"] + sorted(ranking["Nome"].tolist())
        membro = st.selectbox("Participante", opc, label_visibility="collapsed")
        if membro != "— Selecione —":
            user_p = palpites_df[palpites_df["nome"] == membro]
            var_df = pd.merge(
                user_p,
                lutas_df[["id","lutador_1","lutador_2"]].rename(columns={"id":"luta_id"}),
                on="luta_id", how="left",
            )
            var_df["Combate"] = var_df["lutador_1"] + " vs " + var_df["lutador_2"]
            # Tabela HTML estilizada (em vez de st.dataframe)
            hist_rows = ""
            for _, hr in var_df.iterrows():
                hist_rows += (
                    f'<tr>'
                    f'<td>{hr["Combate"]}</td>'
                    f'<td style="font-weight:600; color:var(--mm-red)">{hr["palpite"]}</td>'
                    f'</tr>'
                )
            st.markdown(
                f'<table class="rank-table">'
                f'<thead><tr><th>COMBATE</th><th>VENCEDOR ESCOLHIDO</th></tr></thead>'
                f'<tbody>{hist_rows}</tbody></table>',
                unsafe_allow_html=True,
            )
            primeira = user_p.iloc[0]
            f1 = str(primeira.get("fotn_1","")).strip()
            f2 = str(primeira.get("fotn_2","")).strip()
            p1 = str(primeira.get("potn_1","")).strip()
            txt_f = f"{f1} vs {f2}" if (f1 and f2) else "Não selecionada"
            txt_p = p1 if p1 else "Não selecionado"
            st.info(f"**🌟 FOTN:** {txt_f}")
            st.success(f"**⚡ POTN:** {txt_p}")

# ============== ADMIN ==============
with tab_admin:
    SENHA = st.secrets.get("admin", {}).get("password", "mvpmma2026")

    if "admin_ok" not in st.session_state:
        st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        st.markdown('<div class="section-title">🔐 Área Restrita</div>', unsafe_allow_html=True)
        senha = st.text_input("Senha", type="password", placeholder="Senha admin")
        if st.button("ENTRAR"):
            if senha == SENHA:
                st.session_state.admin_ok = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    else:
        st.markdown('<div class="section-title">🛠️ Painel Admin</div>', unsafe_allow_html=True)

        lutas_adm = load_lutas()
        cfg_adm = load_config()
        res_adm = load_resultados()

        # ----- Configurações gerais -----
        st.markdown('<div class="admin-section">⚙️ Configurações</div>', unsafe_allow_html=True)
        cc1, cc2 = st.columns(2)
        with cc1:
            abertura_in = st.text_input("Abre em (BRT)",
                                        value=cfg_adm.get("abertura",""),
                                        placeholder="DD/MM/AAAA HH:MM")
        with cc2:
            fechamento_in = st.text_input("Fecha em (BRT)",
                                          value=cfg_adm.get("fechamento",""),
                                          placeholder="DD/MM/AAAA HH:MM")
        bloq_flag = st.checkbox("🚫 Bloquear palpites AGORA", value=bool(cfg_adm.get("bloqueado", False)))
        f2_flag = bool(cfg_adm.get("f2_especial", False))  # mantido pra compatibilidade, mas oculto

        st.markdown("---")

        # ----- Editor de Card -----
        st.markdown('<div class="admin-section">✏️ Editar Card do Evento</div>', unsafe_allow_html=True)
        st.caption("⚠️ Alterar lutas APAGA todos os palpites e resultados antigos.")

        # ===== IMPORT VIA CSV/COLA =====
        with st.expander("📋 Importar card via CSV (cola rápida)", expanded=False):
            st.markdown("""
**Formato aceito** (com ou sem header, com ou sem ID):
```
ID,Lutador_1,Lutador_2,Tipo
1,Belal Muhammad,Gabriel Bonfim,F1
2,Brendan Allen,Edmen Shahbazyan,F2
3,Fares Ziam,Tom Nolan,PRINCIPAL
```

Ou simples (sem header, sem ID):
```
Belal Muhammad, Gabriel Bonfim, F1
Brendan Allen, Edmen Shahbazyan, F2
```

**Tipos válidos:** `F1` (main/title, 2pts), `F2` (co-main), `PRINCIPAL`, `PRELIM` (default).
Separador: vírgula `,` ou ponto-e-vírgula `;`. Se omitir o tipo, vira `PRELIM`.
            """)

            def parse_csv(text):
                """Parser flexível: detecta header, ID opcional"""
                linhas = [ln for ln in text.strip().splitlines() if ln.strip()]
                if not linhas:
                    return []
                # Detecta e remove header (se primeira linha tiver 'lutador' ou 'ID' case-insensitive)
                primeira = linhas[0].lower()
                if "lutador" in primeira or primeira.startswith("id,") or primeira.startswith("id;"):
                    linhas = linhas[1:]

                resultado = []
                for ln in linhas:
                    parts = [p.strip() for p in ln.replace(";", ",").split(",") if p.strip() != ""]
                    if len(parts) < 2:
                        continue
                    # Detecta se primeira coluna é ID numérico → descarta
                    if parts[0].isdigit() and len(parts) >= 3:
                        parts = parts[1:]
                    if len(parts) < 2 or not parts[0] or not parts[1]:
                        continue
                    l1, l2 = parts[0], parts[1]
                    tp = (parts[2].upper() if len(parts) > 2 else "PRELIM")
                    if tp not in ("F1","F2","PRINCIPAL","PRELIM"):
                        tp = "PRELIM"
                    resultado.append({"l1": l1, "l2": l2, "tipo": tp})
                return resultado

            csv_text = st.text_area(
                "Cole aqui",
                height=240,
                placeholder="ID,Lutador_1,Lutador_2,Tipo\n1,Lutador A,Lutador B,F1\n2,Lutador C,Lutador D,F2\n...",
                key="csv_import",
            )
            cb1, cb2 = st.columns(2)
            with cb1:
                if st.button("👁️ Preview"):
                    parsed = parse_csv(csv_text)
                    if parsed:
                        rows_pv = ""
                        for i, p in enumerate(parsed):
                            rows_pv += (
                                f'<tr>'
                                f'<td>{i+1}</td>'
                                f'<td>{p["l1"]}</td>'
                                f'<td>{p["l2"]}</td>'
                                f'<td style="font-weight:600; color:var(--mm-red)">{p["tipo"]}</td>'
                                f'</tr>'
                            )
                        st.markdown(
                            f'<table class="rank-table">'
                            f'<thead><tr><th>#</th><th>LUTADOR 1</th><th>LUTADOR 2</th><th>TIPO</th></tr></thead>'
                            f'<tbody>{rows_pv}</tbody></table>',
                            unsafe_allow_html=True,
                        )
                        st.caption(f"{len(parsed)} lutas detectadas.")
                    else:
                        st.warning("Nada válido pra processar.")
            with cb2:
                if st.button("🚀 IMPORTAR e SALVAR"):
                    parsed = parse_csv(csv_text)
                    validas = [{
                        "id": i+1,
                        "lutador_1": p["l1"],
                        "lutador_2": p["l2"],
                        "tipo": p["tipo"],
                        "ordem": i+1,
                    } for i, p in enumerate(parsed)]
                    if not validas:
                        st.error("Nada válido pra importar.")
                    else:
                        try:
                            sb.table("resultados").delete().neq("luta_id", 0).execute()
                            sb.table("palpites").delete().neq("id", 0).execute()
                            sb.table("lutas").delete().neq("id", 0).execute()
                            sb.table("lutas").insert(validas).execute()
                            sb.table("config").update({
                                "fotn_1":"", "fotn_2":"", "potn_1":"", "potn_2":"",
                            }).eq("id", 1).execute()
                            invalidate_cache()
                            if "card_editor" in st.session_state:
                                del st.session_state.card_editor
                            st.success(f"✅ Importado! {len(validas)} lutas. Palpites antigos zerados.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro: {e}")

        st.markdown("---")

        # ----- Resultados das lutas -----
        st.markdown('<div class="admin-section">🏁 Resultados</div>', unsafe_allow_html=True)
        st.caption("Vencedor + pontos da luta (edite os pontos por luta livremente).")
        resultados_novos = []

        for _, luta in lutas_adm.iterrows():
            lid = int(luta["id"])
            l1, l2 = str(luta["lutador_1"]).strip(), str(luta["lutador_2"]).strip()
            tipo = str(luta["tipo"]).strip().upper()

            venc_atual = "Selecione"
            peso_atual = 2 if tipo == "F1" else (2 if tipo == "F2" and f2_flag else 1)

            mask = res_adm["luta_id"] == lid
            if mask.any():
                v_real = str(res_adm.loc[mask, "vencedor_real"].values[0]).strip()
                if v_real and v_real != "None": venc_atual = v_real
                p_val = res_adm.loc[mask, "pontos"].values[0]
                if pd.notna(p_val):
                    try: peso_atual = int(p_val)
                    except: pass

            opcoes = ["Selecione", l1, l2, "Empate", "Cancelada"]
            if venc_atual not in opcoes: venc_atual = "Selecione"
            idx = opcoes.index(venc_atual)

            st.markdown(f"<div style='color:var(--muted); font-size:.8rem; margin-top:.8rem'>Luta {lid} · {l1} vs {l2}</div>", unsafe_allow_html=True)
            c1, c2 = st.columns([4,1])
            with c1:
                venc = st.selectbox(f"r{lid}", opcoes, index=idx, key=f"res_{lid}", label_visibility="collapsed")
            with c2:
                peso = st.number_input(f"p{lid}", value=peso_atual, min_value=1, step=1, key=f"peso_{lid}", label_visibility="collapsed", help="Pts")
            resultados_novos.append({"luta_id":lid, "vencedor_real":venc, "pontos":int(peso)})

        # ----- Bônus -----
        st.markdown('<div class="admin-section">🌟 Bônus da Noite</div>', unsafe_allow_html=True)
        todos_lut_adm = sorted(set(lutas_adm["lutador_1"].tolist() + lutas_adm["lutador_2"].tolist())) if not lutas_adm.empty else []
        lista_fights_adm = ["— Nenhum —"] + [f"{l['lutador_1']} vs {l['lutador_2']}" for _, l in lutas_adm.iterrows()]

        pf1 = str(cfg_adm.get("fotn_1","")).strip()
        pf2 = str(cfg_adm.get("fotn_2","")).strip()
        pp1 = str(cfg_adm.get("potn_1","")).strip()

        fotn_idx = 0
        if pf1 and pf2:
            op = f"{pf1} vs {pf2}"
            op_rev = f"{pf2} vs {pf1}"
            if op in lista_fights_adm: fotn_idx = lista_fights_adm.index(op)
            elif op_rev in lista_fights_adm: fotn_idx = lista_fights_adm.index(op_rev)

        default_potn = [p.strip() for p in pp1.split(",")] if pp1 else []
        default_potn = [p for p in default_potn if p in todos_lut_adm]

        cf, cp = st.columns(2)
        with cf:
            st.markdown("**🌟 Luta da Noite**")
            fotn_adm = st.selectbox("FOTN_adm", lista_fights_adm, index=fotn_idx,
                                    key="adm_fotn", label_visibility="collapsed")
        with cp:
            st.markdown("**⚡ Performance (múltiplos)**")
            potn_list = st.multiselect("POTN_adm", todos_lut_adm, default=default_potn,
                                       key="adm_potn", label_visibility="collapsed")

        if fotn_adm != "— Nenhum —":
            fotn_1v, fotn_2v = fotn_adm.split(" vs ")
        else:
            fotn_1v, fotn_2v = "", ""
        potn_1v = ", ".join(potn_list)

        st.markdown("---")
        if st.button("💾 SALVAR TUDO"):
            try:
                # Salva resultados (upsert)
                sb.table("resultados").upsert(resultados_novos).execute()
                # Salva config
                sb.table("config").update({
                    "fotn_1": fotn_1v, "fotn_2": fotn_2v,
                    "potn_1": potn_1v, "potn_2": "",
                    "f2_especial": bool(f2_flag),
                    "bloqueado": bool(bloq_flag),
                    "abertura": abertura_in.strip(),
                    "fechamento": fechamento_in.strip(),
                }).eq("id", 1).execute()
                invalidate_cache()
                st.success("🏆 Tudo salvo!")
            except Exception as e:
                st.error(f"Erro: {e}")

        # ----- Reset -----
        st.markdown("---")
        st.markdown('<div class="admin-section" style="color:#E50914">🚨 Zona de Perigo</div>', unsafe_allow_html=True)
        st.warning("Apaga TODOS os palpites e resultados (mantém o card de lutas).")
        senha_reset = st.text_input("Senha admin para confirmar", type="password", key="reset_pw")
        if st.button("🧨 ZERAR BOLÃO"):
            if senha_reset == SENHA:
                try:
                    sb.table("palpites").delete().neq("id", 0).execute()
                    sb.table("resultados").delete().neq("luta_id", 0).execute()
                    sb.table("config").update({
                        "fotn_1":"", "fotn_2":"", "potn_1":"", "potn_2":"",
                        "bloqueado": False, "abertura":"", "fechamento":"",
                    }).eq("id", 1).execute()
                    invalidate_cache()
                    st.success("💥 Resetado!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
            else:
                st.error("Senha incorreta.")

        st.markdown("---")
        if st.button("🚪 SAIR"):
            st.session_state.admin_ok = False
            st.rerun()
