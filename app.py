import io
import json
import pandas as pd
import requests
import streamlit as st

# ──────────────────────────────────────────────
# PAGE CONFIG & CSS (ORIGINAL MANTIDO)
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
# CONFIG & LOAD DATA (TTL=60)
# ──────────────────────────────────────────────
SHEET_ID        = st.secrets["gsheets"]["spreadsheet_id"]
LUTAS_GID       = int(st.secrets["gsheets"].get("lutas_gid", 0))
PALPITES_GID    = int(st.secrets["gsheets"].get("palpites_gid", 1))
RESULTADOS_GID  = int(st.secrets["gsheets"].get("resultados_gid", 2))
APPS_SCRIPT_URL = st.secrets["gsheets"]["apps_script_url"]

def csv_url(gid: int) -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

@st.cache_data(ttl=60)
def load_data(gid):
    try:
        df = pd.read_csv(csv_url(gid), dtype=str)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame()

def invalidate_cache():
    load_data.clear()

def sheet_write(payload: dict):
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        if response.status_code != 200: raise Exception("Erro na requisição")
    except Exception as e:
        st.error(f"Falha de conexão: {e}")

# ──────────────────────────────────────────────
# MOTOR DE PONTUAÇÃO (ATUALIZADO PARA PONTOS LIVRES)
# ──────────────────────────────────────────────
def calcular_ranking(palpites, lutas, resultados):
    if palpites.empty or resultados.empty: return pd.DataFrame()
    
    # Merge palpites com resultados e pesos
    df = pd.merge(palpites, resultados[['Luta_ID', 'Vencedor_Real']], on="Luta_ID", how="left")
    df = pd.merge(df, lutas[['ID', 'Pontos']], left_on="Luta_ID", right_on="ID", how="left")
    
    # Pontos das lutas
    df['Pontos'] = pd.to_numeric(df['Pontos'], errors='coerce').fillna(1)
    df['Acertou'] = df['Palpite'].str.upper() == df['Vencedor_Real'].str.upper()
    df['Pts_Luta'] = df['Acertou'] * df['Pontos']
    
    # Agrupar por Usuário
    rank = df.groupby('Nome').agg({'Pts_Luta': 'sum', 'Acertou': 'sum'}).reset_index()
    
    # Bônus (Calculado na primeira linha de resultados)
    r0 = resultados.iloc[0]
    bonus_real = {
        "fotn": {str(r0.get("FOTN_1", "")).upper(), str(r0.get("FOTN_2", "")).upper()} - {"", "NAN"},
        "potn": {str(r0.get("POTN_1", "")).upper(), str(r0.get("POTN_2", "")).upper()} - {"", "NAN"}
    }
    
    # Aplica bônus usuário a usuário
    bonus_pts = []
    for nome in rank['Nome']:
        u_p = palpites[palpites['Nome'] == nome].iloc[0]
        p_val = 0
        u_fotn = {str(u_p.get("FOTN_1", "")).upper(), str(u_p.get("FOTN_2", "")).upper()}
        if u_fotn == bonus_real["fotn"] and len(bonus_real["fotn"]) == 2: p_val += 2
        
        u_potn = {str(u_p.get("POTN_1", "")).upper(), str(u_p.get("POTN_2", "")).upper()}
        p_val += sum(1 for p in u_potn if p in bonus_real["potn"] and p != "")
        bonus_pts.append(p_val)
    
    rank['Pts_Bonus'] = bonus_pts
    rank['Total'] = rank['Pts_Luta'] + rank['Pts_Bonus']
    rank = rank.sort_values(['Total', 'Acertou', 'Nome'], ascending=[False, False, True]).reset_index(drop=True)
    rank.insert(0, "Pos", range(1, len(rank) + 1))
    return rank

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_votar, tab_ranking, tab_admin = st.tabs(["🥊  Votar", "🏆  Ranking", "🔐  Admin"])

with tab_votar:
    lutas = load_data(LUTAS_GID)
    if lutas.empty: st.warning("Aguarde o Admin configurar o card.")
    else:
        with st.form("form_voto"):
            nome_u = st.text_input("Seu Nome:")
            st.markdown("---")
            votos_u = []
            for _, l in lutas.iterrows():
                st.markdown(f'<div class="card"><div class="card-title">{l["Lutador_1"]} vs {l["Lutador_2"]}</div></div>', unsafe_allow_html=True)
                v = st.radio(f"Vencedor {l['ID']}", [l["Lutador_1"], l["Lutador_2"]], horizontal=True, label_visibility="collapsed", key=f"v_{l['ID']}")
                votos_u.append({"Luta_ID": l["ID"], "Palpite": v})
            
            st.markdown("### Bônus")
            c1, c2 = st.columns(2)
            f1 = c1.text_input("FOTN 1"); f2 = c1.text_input("FOTN 2")
            p1 = c2.text_input("POTN 1"); p2 = c2.text_input("POTN 2")
            
            if st.form_submit_button("✅ ENVIAR PALPITES"):
                if nome_u:
                    final_p = pd.DataFrame(votos_u)
                    final_p["Nome"] = nome_u; final_p["FOTN_1"] = f1; final_p["FOTN_2"] = f2; final_p["POTN_1"] = p1; final_p["POTN_2"] = p2
                    existing = load_data(PALPITES_GID)
                    existing = existing[existing["Nome"].str.upper() != nome_u.upper()]
                    sheet_write({"sheet": "Palpites", "data": [pd.concat([existing, final_p]).columns.tolist()] + pd.concat([existing, final_p]).values.tolist()})
                    invalidate_cache(); st.success("Palpites Salvos!"); st.rerun()

with tab_ranking:
    lutas = load_data(LUTAS_GID); palpites = load_data(PALPITES_GID); resultados = load_data(RESULTADOS_GID)
    rank = calcular_ranking(palpites, lutas, resultados)
    if rank.empty: st.info("Ranking indisponível.")
    else:
        st.markdown('<table class="rank-table"><thead><tr><th>POS</th><th>NOME</th><th>PTS</th><th>ACERTOS</th></tr></thead>', unsafe_allow_html=True)
        for _, r in rank.iterrows():
            st.markdown(f'<tr><td>{int(r["Pos"])}º</td><td>{r["Nome"]}</td><td>{int(r["Total"])}</td><td>{int(r["Acertou"])}</td></tr>', unsafe_allow_html=True)
        st.markdown('</table>', unsafe_allow_html=True)
        
        st.markdown("---")
        st.subheader("🔍 VAR")
        membro = st.selectbox("Ver Palpites de:", [""] + list(rank["Nome"]))
        if membro:
            st.table(palpites[palpites["Nome"] == membro][['Luta_ID', 'Palpite']])

with tab_admin:
    if "admin_ok" not in st.session_state: st.session_state.admin_ok = False
    if not st.session_state.admin_ok:
        if st.text_input("Senha Admin", type="password") == "uvr2026":
            st.session_state.admin_ok = True; st.rerun()
    else:
        st.markdown('<div class="admin-section">🏁 Resultados e Pesos</div>', unsafe_allow_html=True)
        lutas = load_data(LUTAS_GID); resultados_df = load_data(RESULTADOS_GID)
        
        with st.form("form_adm"):
            novos_res = []
            for _, l in lutas.iterrows():
                col1, col2 = st.columns([3, 1])
                # Carregar vencedor salvo se existir
                v_atual = resultados_df[resultados_df["Luta_ID"] == l["ID"]]["Vencedor_Real"].values[0] if not resultados_df.empty and l["ID"] in resultados_df["Luta_ID"].values else "Selecione"
                venc = col1.radio(f"{l['Lutador_1']} vs {l['Lutador_2']}", ["Selecione", l["Lutador_1"], l["Lutador_2"], "Empate"], index=0)
                peso = col2.number_input(f"Pontos", value=int(l.get("Pontos", 1)), key=f"p_{l['ID']}")
                novos_res.append({"Luta_ID": l["ID"], "Vencedor_Real": venc, "Pontos": peso})
            
            st.markdown("### Bônus Reais")
            bf1 = st.text_input("FOTN 1 Real"); bf2 = st.text_input("FOTN 2 Real")
            bp1 = st.text_input("POTN 1 Real"); bp2 = st.text_input("POTN 2 Real")
            
            if st.form_submit_button("💾 SALVAR TUDO"):
                # Salvar Resultados
                df_res_final = pd.DataFrame(novos_res)
                df_res_final["FOTN_1"] = bf1; df_res_final["FOTN_2"] = bf2; df_res_final["POTN_1"] = bp1; df_res_final["POTN_2"] = bp2
                sheet_write({"sheet": "Resultados", "data": [df_res_final.columns.tolist()] + df_res_final.values.tolist()})
                # Salvar Pesos na aba Lutas
                lutas["Pontos"] = [x["Pontos"] for x in novos_res]
                sheet_write({"sheet": "Lutas", "data": [lutas.columns.tolist()] + lutas.values.tolist()})
                invalidate_cache(); st.success("Atualizado!"); st.rerun()

        st.markdown("---")
        st.markdown('<div class="admin-section">🚨 RESET TOTAL</div>', unsafe_allow_html=True)
        if st.text_input("Confirme a senha para ZERAR:", type="password") == "uvr2026":
            if st.button("ZERAR TUDO"):
                sheet_write({"sheet": "Palpites", "data": [["Nome","Luta_ID","Palpite","FOTN_1","FOTN_2","POTN_1","POTN_2"]]})
                sheet_write({"sheet": "Resultados", "data": [["Luta_ID","Vencedor_Real","FOTN_1","FOTN_2","POTN_1","POTN_2"]]})
                st.warning("Evento Resetado!"); invalidate_cache()
