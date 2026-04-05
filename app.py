import io
import json
import pandas as pd
import requests
import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# PAGE CONFIG & CSS
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
.fight-tag.prelim{background:#2a4365;color:#fff}
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
# CONFIG & LOAD DATA
# ──────────────────────────────────────────────
SHEET_ID        = st.secrets["gsheets"]["spreadsheet_id"]
LUTAS_GID       = int(st.secrets["gsheets"].get("lutas_gid", 0))
PALPITES_GID    = int(st.secrets["gsheets"].get("palpites_gid", 1))
RESULTADOS_GID  = int(st.secrets["gsheets"].get("resultados_gid", 2))
APPS_SCRIPT_URL = st.secrets["gsheets"]["apps_script_url"]

def csv_url(gid: int) -> str:
    return f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={gid}"

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
        return pd.DataFrame(columns=["Luta_ID", "Vencedor_Real", "Pontos", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2", "F2_Especial", "Bloqueado", "Fechamento", "Abertura"])

def invalidate_cache():
    load_lutas.clear()
    load_palpites.clear()
    load_resultados.clear()

def sheet_write(worksheet_name: str, df: pd.DataFrame):
    df = df.fillna("").astype(str)
    data_to_send = [df.columns.tolist()] + df.values.tolist()
    payload = {"sheet": worksheet_name, "data": data_to_send}
    try:
        response = requests.post(APPS_SCRIPT_URL, json=payload)
        res_json = response.json()
        if response.status_code != 200 or res_json.get("status") != "success":
            raise Exception(f"Erro no Apps Script: {res_json.get('message', 'Erro desconhecido')}")
    except Exception as e:
        raise Exception(f"Falha de conexão com a planilha: {e}")

# ──────────────────────────────────────────────
# MOTOR DE PONTUAÇÃO (COM POTN MÚLTIPLO)
# ──────────────────────────────────────────────
def calcular_pontuacao(palpites_df: pd.DataFrame, lutas_df: pd.DataFrame, resultados_df: pd.DataFrame) -> pd.DataFrame:
    if palpites_df.empty or lutas_df.empty or resultados_df.empty: return pd.DataFrame()

    res_map  = resultados_df.set_index("Luta_ID")
    luta_map = lutas_df.set_index("ID")
    
    try:
        lutas_ordenadas = sorted(lutas_df["ID"].dropna().unique(), key=lambda x: int(x))
    except:
        lutas_ordenadas = sorted(lutas_df["ID"].dropna().unique())

    f2_especial = False
    if "F2_Especial" in res_map.columns:
        vals = res_map["F2_Especial"].dropna().str.upper()
        if not vals.empty: f2_especial = vals.iloc[0] in ("TRUE", "SIM", "1", "YES")

    fotn_real, potn_real = set(), set()
    if not res_map.empty:
        r0 = res_map.iloc[0]
        fotn_real = {str(r0.get("FOTN_1", "")).strip().upper(), str(r0.get("FOTN_2", "")).strip().upper()} - {"", "NAN"}
        
        # MÁGICA DO POTN MÚLTIPLO: Quebra a string por vírgula e transforma numa lista real de ganhadores
        potn_str = str(r0.get("POTN_1", "")).strip().upper()
        if potn_str and potn_str != "NAN":
            potn_real = {p.strip() for p in potn_str.split(",")} - {""}

    scores: dict = {}
    for _, row in palpites_df.iterrows():
        nome = str(row["Nome"]).strip()
        luta_id = str(row["Luta_ID"]).strip()
        palpite = str(row.get("Palpite", "")).strip()

        if nome not in scores:
            scores[nome] = {"Pontos": 0, "Acertos": 0, "Acerto_F1": 0, "Acerto_F2": 0,
                            "_fotn_1": str(row.get("FOTN_1", "")).strip(), "_fotn_2": str(row.get("FOTN_2", "")).strip(),
                            "_potn_1": str(row.get("POTN_1", "")).strip(), "_potn_2": str(row.get("POTN_2", "")).strip(),
                            "Desempate_Lutas": {lid: 0 for lid in lutas_ordenadas}}

        if luta_id not in res_map.index: continue
        vencedor = str(res_map.at[luta_id, "Vencedor_Real"]).strip().upper()
        
        if vencedor in ("EMPATE", "CANCELADA", "NAN", "", "SELECIONE"): continue

        tipo = str(luta_map.at[luta_id, "Tipo"]).strip().upper() if luta_id in luta_map.index else "PRELIM"
        acertou = palpite.upper() == vencedor

        peso_luta = 2 if tipo == "F1" else (2 if (tipo == "F2" and f2_especial) else 1)
        
        if "Pontos" in res_map.columns:
            p_val = res_map.loc[luta_id, "Pontos"]
            if isinstance(p_val, pd.Series): p_val = p_val.iloc[0] 
            if pd.notna(p_val) and str(p_val).strip() != "" and str(p_val).strip().lower() != "nan":
                try: peso_luta = int(float(p_val))
                except: pass
            
        pts = peso_luta if acertou else 0

        if acertou: 
            scores[nome]["Acertos"] += 1
            if tipo == "F1": scores[nome]["Acerto_F1"] += 1
            if tipo == "F2": scores[nome]["Acerto_F2"] += 1
            
            if luta_id in scores[nome]["Desempate_Lutas"]:
                scores[nome]["Desempate_Lutas"][luta_id] = 1
            
        scores[nome]["Pontos"] += pts

    for acc in scores.values():
        if fotn_real:
            fu = {acc["_fotn_1"].upper(), acc["_fotn_2"].upper()} - {"", "NAN"}
            if fu and fu == fotn_real: acc["Pontos"] += 2
        if potn_real:
            pu = {acc["_potn_1"].upper(), acc["_potn_2"].upper()} - {"", "NAN"}
            # Se o lutador que a pessoa escolheu estiver na lista de vencedores, ganha 1 ponto
            acc["Pontos"] += sum(1 for n in pu if n in potn_real)

    if not scores: return pd.DataFrame()

    linhas_rank = []
    for n, v in scores.items():
        linha = {"Nome": n, "Pontos": v["Pontos"], "Acertos": v["Acertos"], "Acerto_F1": v["Acerto_F1"], "Acerto_F2": v["Acerto_F2"]}
        for lid in lutas_ordenadas:
            linha[f"Luta_{lid}"] = v["Desempate_Lutas"][lid]
        linhas_rank.append(linha)
        
    df_rank = pd.DataFrame(linhas_rank)
    
    colunas_ordenacao = ["Pontos", "Acertos"] + [f"Luta_{lid}" for lid in lutas_ordenadas] + ["Nome"]
    ordens = [False, False] + [False] * len(lutas_ordenadas) + [True]
    
    df_rank = df_rank.sort_values(by=colunas_ordenacao, ascending=ordens).reset_index(drop=True)
    df_rank.insert(0, "Pos", range(1, len(df_rank) + 1))
    return df_rank

# ──────────────────────────────────────────────
# FUNÇÃO DO CRONÔMETRO JAVASCRIPT
# ──────────────────────────────────────────────
def render_timer(target_str, title, color="#f5c518", end_text="ENCERRADO"):
    try:
        dt_obj = datetime.strptime(target_str, "%d/%m/%Y %H:%M")
        iso_str = dt_obj.strftime("%Y-%m-%dT%H:%M:00-03:00")
        
        cronometro_html = f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap');
            .timer-box {{ background-color: #1a1a1a; border: 1px solid {color}; border-radius: 10px; padding: 15px; text-align: center; margin-bottom: 20px; }}
            .timer-title {{ color: #888; font-family: 'Bebas Neue', sans-serif; font-size: 1.2rem; letter-spacing: 0.1em; }}
            .timer-time {{ color: {color}; font-family: 'Bebas Neue', sans-serif; font-size: 2.8rem; letter-spacing: 0.05em; margin-top: -5px; }}
        </style>
        <div class="timer-box">
            <div class="timer-title">{title}</div>
            <div class="timer-time" id="clock">CALCULANDO...</div>
        </div>
        <script>
            var target = new Date("{iso_str}").getTime();
            var x = setInterval(function() {{
                var now = new Date().getTime();
                var d = target - now;
                if (d < 0) {{
                    clearInterval(x);
                    document.getElementById("clock").innerHTML = "{end_text}";
                    document.getElementById("clock").style.color = "{color}";
                }} else {{
                    var days = Math.floor(d / (1000 * 60 * 60 * 24));
                    var hours = Math.floor((d % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                    var minutes = Math.floor((d % (1000 * 60 * 60)) / (1000 * 60));
                    var seconds = Math.floor((d % (1000 * 60)) / 1000);
                    
                    var res = "";
                    if(days > 0) res += days + "d ";
                    res += (hours < 10 ? "0" : "") + hours + "h ";
                    res += (minutes < 10 ? "0" : "") + minutes + "m ";
                    res += (seconds < 10 ? "0" : "") + seconds + "s";
                    document.getElementById("clock").innerHTML = res;
                }}
            }}, 1000);
        </script>
        """
        components.html(cronometro_html, height=130)
    except:
        pass

# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_votar, tab_ranking, tab_admin = st.tabs(["🥊  Votar", "🏆  Ranking", "🔐  Admin"])

with tab_votar:
    lutas = load_lutas()
    resultados_trava = load_resultados()
    
    agora_brt = datetime.utcnow() - timedelta(hours=3)
    bolao_status = "ABERTO"
    abertura_str = ""
    fechamento_str = ""
    
    if not resultados_trava.empty:
        if "Bloqueado" in resultados_trava.columns and resultados_trava["Bloqueado"].str.upper().eq("TRUE").any():
            bolao_status = "FECHADO"
        
        if "Abertura" in resultados_trava.columns:
            a_val = resultados_trava["Abertura"].iloc[0]
            if pd.notna(a_val) and str(a_val).strip() != "" and str(a_val).lower() != "nan":
                abertura_str = str(a_val).strip()
                try:
                    abertura_dt = datetime.strptime(abertura_str, "%d/%m/%Y %H:%M")
                    if agora_brt < abertura_dt:
                        bolao_status = "AGUARDANDO"
                except: pass

        if "Fechamento" in resultados_trava.columns and bolao_status != "AGUARDANDO":
            f_val = resultados_trava["Fechamento"].iloc[0]
            if pd.notna(f_val) and str(f_val).strip() != "" and str(f_val).lower() != "nan":
                fechamento_str = str(f_val).strip()
                try:
                    fechamento_dt = datetime.strptime(fechamento_str, "%d/%m/%Y %H:%M")
                    if agora_brt >= fechamento_dt:
                        bolao_status = "FECHADO"
                except: pass

    if lutas.empty: 
        st.warning("Nenhuma luta cadastrada ainda. Aguarde o Admin configurar o evento.")
    elif bolao_status == "AGUARDANDO":
        st.info(f"⏳ O bolão abre oficialmente dia **{abertura_str}** (Horário de Brasília).")
        render_timer(abertura_str, "O BOLÃO ABRIRÁ EM:", color="#32CD32", end_text="ABERTO! ATUALIZE A PÁGINA")
        st.warning("Aguarde a abertura dos portões para registrar seu palpite.")
    elif bolao_status == "FECHADO":
        st.error("🚨 **BOLÃO ENCERRADO!** Os palpites foram fechados.")
        st.info("O evento já vai começar (ou já começou). Vá para a aba **Ranking** para acompanhar a pontuação e ver o VAR. Boa sorte!")
    else:
        if fechamento_str:
            render_timer(fechamento_str, "TEMPO RESTANTE PARA O BOLÃO FECHAR:", color="#f5c518", end_text="FECHADO!")

        st.markdown("### Seu nome")
        nome_usuario = st.text_input("Nome", placeholder="Ex: João Silva", label_visibility="collapsed")
        st.markdown("---")
        st.markdown("### Palpites nas Lutas")

        palpites_usuario: dict = {}
        todos_lutadores: list = []
        lista_lutas_formatada: list = [] 

        for _, luta in lutas.iterrows():
            luta_id = str(luta["ID"])
            lutador1, lutador2 = str(luta["Lutador_1"]).strip(), str(luta["Lutador_2"]).strip()
            tipo = str(luta["Tipo"]).strip().upper()
            todos_lutadores.extend([lutador1, lutador2])
            lista_lutas_formatada.append(f"{lutador1} vs {lutador2}")

            if tipo == "F1": tag_class, tag_label = "main", "MAIN EVENT"
            elif tipo == "F2": tag_class, tag_label = "co-main", "CO-MAIN EVENT"
            elif tipo == "PRINCIPAL": tag_class, tag_label = "", "CARD PRINCIPAL"
            else: tag_class, tag_label = "prelim", "PRELIMINAR"

            st.markdown(f"""
            <div class="card">
              <span class="fight-tag {tag_class}">{tag_label}</span>
              <div class="card-title">{lutador1} vs {lutador2}</div>
            </div>
            """, unsafe_allow_html=True)
            escolha = st.radio(f"Quem vence? ({luta_id})", options=[lutador1, lutador2], horizontal=True, label_visibility="collapsed", key=f"luta_{luta_id}")
            palpites_usuario[luta_id] = escolha

        st.markdown("---")
        st.markdown("### Bônus da Noite")
        todos_lut_uniq = sorted(set(todos_lutadores))
        opcao_vazio = ["— Selecione —"]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🌟 Luta da Noite**")
            fotn_escolha = st.selectbox("Luta da Noite", opcao_vazio + lista_lutas_formatada, key="fotn_voto", label_visibility="collapsed")
        with col2:
            st.markdown("**⚡ Performance**")
            potn_escolha = st.selectbox("Melhor Performance", opcao_vazio + todos_lut_uniq, key="potn_voto", label_visibility="collapsed")

        st.markdown("---")
        if st.button("✅  ENVIAR PALPITES"):
            nome_limpo = nome_usuario.strip()
            if not nome_limpo: 
                st.error("Informe seu nome.")
            else:
                if fotn_escolha != "— Selecione —":
                    _f1, _f2 = fotn_escolha.split(" vs ")
                else:
                    _f1, _f2 = "", ""

                _p1 = "" if potn_escolha == "— Selecione —" else potn_escolha
                _p2 = "" 

                palpites_existentes = load_palpites()
                palpites_existentes = palpites_existentes[palpites_existentes["Nome"].str.strip().str.upper() != nome_limpo.upper()]

                novas_linhas = pd.DataFrame([{"Nome": nome_limpo, "Luta_ID": lid, "Palpite": pal, "FOTN_1": _f1, "FOTN_2": _f2, "POTN_1": _p1, "POTN_2": _p2} for lid, pal in palpites_usuario.items()])
                df_final = pd.concat([palpites_existentes, novas_linhas], ignore_index=True)

                try:
                    sheet_write("Palpites", df_final)
                    invalidate_cache()
                    st.success(f"Palpites de **{nome_limpo}** salvos! 🥊")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

with tab_ranking:
    lutas_df = load_lutas()
    palpites_df = load_palpites()
    resultados_df = load_resultados()
    ranking = calcular_pontuacao(palpites_df, lutas_df, resultados_df)

    if ranking.empty: st.info("O ranking será exibido após o Admin inserir os resultados.")
    else:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        rows_html = ""
        for _, r in ranking.iterrows():
            pos = int(r["Pos"])
            cls = f"top-{pos}" if pos <= 3 else ""
            medal = medals.get(pos, "")
            rows_html += f'<tr class="{cls}"><td>{medal} {pos}º</td><td>{r["Nome"]}</td><td style="text-align:center">{int(r["Pontos"])}</td><td style="text-align:center">{int(r["Acertos"])}</td><td style="text-align:center">{"✅" if int(r["Acerto_F1"]) else "❌"}</td><td style="text-align:center">{"✅" if int(r["Acerto_F2"]) else "❌"}</td></tr>'

        st.markdown(f'<table class="rank-table"><thead><tr><th>POS</th><th>NOME</th><th style="text-align:center">PTS</th><th style="text-align:center">ACERTOS</th><th style="text-align:center">F1</th><th style="text-align:center">F2</th></tr></thead><tbody>{rows_html}</tbody></table>', unsafe_allow_html=True)
        st.caption("Atualizado a cada 1 min · Desempate: Pts › Acertos › Luta 1 › Luta 2 › Luta 3... › Nome")

        st.markdown("---")
        st.markdown('<div class="admin-section">🔍 VAR: Histórico de Palpites</div>', unsafe_allow_html=True)
        opcoes_var = ["— Selecione um Participante —"] + sorted(ranking["Nome"].tolist())
        membro_selecionado = st.selectbox("Fiscalize os votos:", opcoes_var, label_visibility="collapsed")
        
        if membro_selecionado != "— Selecione um Participante —":
            st.markdown(f"#### 🥊 Palpites de {membro_selecionado}")
            user_palpites = palpites_df[palpites_df["Nome"] == membro_selecionado]
            var_completo = pd.merge(user_palpites, lutas_df[['ID', 'Lutador_1', 'Lutador_2']], left_on="Luta_ID", right_on="ID", how="left")
            var_completo["Combate"] = var_completo["Lutador_1"] + " vs " + var_completo["Lutador_2"]
            var_display = var_completo[["Combate", "Palpite"]].rename(columns={"Palpite": "Vencedor Escolhido"})
            
            st.dataframe(var_display, hide_index=True, use_container_width=True)
            
            primeira_linha = user_palpites.iloc[0]
            f1 = str(primeira_linha.get("FOTN_1", "")).strip()
            f2 = str(primeira_linha.get("FOTN_2", "")).strip()
            p1 = str(primeira_linha.get("POTN_1", "")).strip()
            
            texto_fotn = f"{f1} vs {f2}" if (f1 and f2 and f1 != "nan" and f2 != "nan") else "Nenhuma selecionada"
            texto_potn = p1 if (p1 and p1 != "nan") else "Nenhum selecionado"
            
            st.info(f"**🌟 Luta da Noite:** {texto_fotn}")
            st.success(f"**⚡ Performance da Noite:** {texto_potn}")

with tab_admin:
    SENHA_ADMIN = "uvr2026"
    if "admin_ok" not in st.session_state: st.session_state.admin_ok = False

    if not st.session_state.admin_ok:
        st.markdown("### 🔐 Área Restrita")
        senha = st.text_input("Senha", type="password", placeholder="Senha admin")
        if st.button("Entrar"):
            if senha == SENHA_ADMIN: st.session_state.admin_ok = True; st.rerun()
            else: st.error("Senha incorreta.")
    else:
        st.markdown("### 🛠️ Painel Admin – UVR 2.0")
        st.markdown('<div class="admin-section">📋 Gerenciar Lutas</div>', unsafe_allow_html=True)
        lutas_atual = load_lutas()
        st.dataframe(lutas_atual, use_container_width=True, hide_index=True)

        with st.expander("➕ Adicionar / substituir tabela de Lutas"):
            st.info("Cole no formato CSV. Tipo aceito: F1, F2, PRINCIPAL, PRELIM")
            lutas_csv = st.text_area("CSV", height=180, placeholder="ID,Lutador_1,Lutador_2,Tipo\n1,Jon Jones,Stipe Miocic,F1")
            if st.button("💾 Salvar Lutas"):
                try:
                    df_lutas_new = pd.read_csv(io.StringIO(lutas_csv))
                    df_lutas_new.columns = [c.strip() for c in df_lutas_new.columns]
                    sheet_write("Lutas", df_lutas_new)
                    invalidate_cache()
                    st.success("Lutas salvas!")
                except Exception as e: st.error(f"Erro: {e}")

        st.markdown('<div class="admin-section">🏁 Resultados, Bloqueios e Pesos</div>', unsafe_allow_html=True)
        lutas_df_adm = load_lutas()
        resultados_df_adm = load_resultados()

        # CONFIGURAÇÕES DO EVENTO (Abertura, Fechamento e Flags)
        st.markdown("##### ⚙️ Configurações Gerais")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            abertura_atual = resultados_df_adm["Abertura"].iloc[0] if not resultados_df_adm.empty and "Abertura" in resultados_df_adm.columns and pd.notna(resultados_df_adm["Abertura"].iloc[0]) else ""
            if str(abertura_atual).lower() == "nan": abertura_atual = ""
            abertura_input = st.text_input("🟢 Abre Auto (BRT)", value=str(abertura_atual), placeholder="DD/MM/AAAA HH:MM")
            
            f2_especial_flag = st.checkbox("F2 vale 2 pts?", value=(resultados_df_adm["F2_Especial"].str.upper().eq("TRUE").any() if not resultados_df_adm.empty and "F2_Especial" in resultados_df_adm.columns else False))
        with col_c2:
            fechamento_atual = resultados_df_adm["Fechamento"].iloc[0] if not resultados_df_adm.empty and "Fechamento" in resultados_df_adm.columns and pd.notna(resultados_df_adm["Fechamento"].iloc[0]) else ""
            if str(fechamento_atual).lower() == "nan": fechamento_atual = ""
            fechamento_input = st.text_input("🔴 Fecha Auto (BRT)", value=str(fechamento_atual), placeholder="DD/MM/AAAA HH:MM")
            
            bolao_fechado_flag = st.checkbox("🚫 BLOQUEAR AGORA MANUALMENTe", value=(resultados_df_adm["Bloqueado"].str.upper().eq("TRUE").any() if not resultados_df_adm.empty and "Bloqueado" in resultados_df_adm.columns else False))

        st.markdown("---")
        
        resultados_novos: list = []
        if lutas_df_adm.empty: st.warning("Cadastre as lutas primeiro.")
        else:
            for _, luta in lutas_df_adm.iterrows():
                lid, lutador1, lutador2, tipo = str(luta["ID"]), str(luta["Lutador_1"]).strip(), str(luta["Lutador_2"]).strip(), str(luta["Tipo"]).strip().upper()
                venc_atual = "Selecione"
                
                peso_atual = 2 if tipo == "F1" else (2 if tipo == "F2" and f2_especial_flag else 1)

                mask = resultados_df_adm["Luta_ID"] == lid
                if mask.any(): 
                    v_real = str(resultados_df_adm.loc[mask, "Vencedor_Real"].values[0]).strip()
                    if v_real: venc_atual = v_real
                    
                    if "Pontos" in resultados_df_adm.columns:
                        p_salvo = str(resultados_df_adm.loc[mask, "Pontos"].values[0]).strip()
                        if p_salvo and p_salvo.lower() != "nan":
                            try: peso_atual = int(float(p_salvo))
                            except: pass

                opcoes = ["Selecione", lutador1, lutador2, "Empate", "Cancelada"]
                if venc_atual not in opcoes: venc_atual = "Selecione"
                idx_default = opcoes.index(venc_atual)
                
                if tipo == "F1": tag_label = "MAIN EVENT"
                elif tipo == "F2": tag_label = "CO-MAIN"
                elif tipo == "PRINCIPAL": tag_label = "PRINCIPAL"
                else: tag_label = "PRELIM"

                st.markdown(f"**[{tag_label}]** {lutador1} vs {lutador2}")
                col1, col2 = st.columns([3, 1])
                with col1:
                    venc_sel = st.selectbox(f"res_{lid}", opcoes, index=idx_default, key=f"res_{lid}", label_visibility="collapsed")
                with col2:
                    novo_peso = st.number_input(f"Pts {lid}", value=peso_atual, min_value=1, step=1, key=f"peso_{lid}", label_visibility="collapsed")
                    
                resultados_novos.append({"Luta_ID": lid, "Vencedor_Real": venc_sel, "Pontos": novo_peso})

        st.markdown('<div class="admin-section">🌟 Bônus da Noite (FOTN / POTN)</div>', unsafe_allow_html=True)
        todos_lut_adm = sorted(set(lutas_df_adm["Lutador_1"].tolist() + lutas_df_adm["Lutador_2"].tolist())) if not lutas_df_adm.empty else []
        
        lista_fights_adm = ["— Nenhum —"]
        for _, luta in lutas_df_adm.iterrows():
            lista_fights_adm.append(f"{str(luta['Lutador_1']).strip()} vs {str(luta['Lutador_2']).strip()}")
            
        def safe_idx(lst, val): return lst.index(val) if val in lst else 0

        lista_adm_potn = todos_lut_adm
        pf1 = pf2 = pp1 = ""
        fotn_idx = 0
        if not resultados_df_adm.empty:
            r0 = resultados_df_adm.iloc[0]
            pf1, pf2, pp1 = str(r0.get("FOTN_1", "")).strip(), str(r0.get("FOTN_2", "")).strip(), str(r0.get("POTN_1", "")).strip()
            
            if pf1 and pf2 and pf1 != "nan" and pf2 != "nan":
                op1 = f"{pf1} vs {pf2}"
                op2 = f"{pf2} vs {pf1}" 
                if op1 in lista_fights_adm: fotn_idx = lista_fights_adm.index(op1)
                elif op2 in lista_fights_adm: fotn_idx = lista_fights_adm.index(op2)

        # MÁGICA DO MULTISELECT: Prepara os valores padrão baseados no que já tá salvo na planilha
        default_potn = [p.strip() for p in pp1.split(",")] if pp1 and pp1.lower() != "nan" else []
        default_potn = [p for p in default_potn if p in lista_adm_potn]

        col_f, col_p = st.columns(2)
        with col_f:
            st.markdown("**Luta da Noite**")
            fotn_adm = st.selectbox("Luta", lista_fights_adm, index=fotn_idx, key="adm_fotn_unica", label_visibility="collapsed")
        with col_p:
            st.markdown("**Performance (Pode escolher vários)**")
            potn_adm_list = st.multiselect("Lutadores", lista_adm_potn, default=default_potn, key="adm_potn_multi", label_visibility="collapsed")

        if fotn_adm != "— Nenhum —":
            fotn1_v, fotn2_v = fotn_adm.split(" vs ")
        else:
            fotn1_v, fotn2_v = "", ""

        # Junta a lista de volta numa string separada por vírgulas pra salvar na planilha
        potn1_v = ", ".join(potn_adm_list)
        potn2_v = "" 

        st.markdown("---")
        if st.button("💾  SALVAR TODOS OS RESULTADOS E CONFIGURAÇÕES"):
            try:
                df_res = pd.DataFrame(resultados_novos)
                df_res["FOTN_1"] = fotn1_v
                df_res["FOTN_2"] = fotn2_v
                df_res["POTN_1"] = potn1_v
                df_res["POTN_2"] = potn2_v
                df_res["F2_Especial"] = str(f2_especial_flag)
                df_res["Bloqueado"] = str(bolao_fechado_flag)
                df_res["Fechamento"] = str(fechamento_input)
                df_res["Abertura"] = str(abertura_input)
                sheet_write("Resultados", df_res)
                invalidate_cache()
                st.success("Tudo salvo com sucesso! 🏆")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")

        st.markdown("---")
        st.markdown('<div class="admin-section" style="color: #e8002d;">🚨 ZONA DE PERIGO: RESET TOTAL</div>', unsafe_allow_html=True)
        st.warning("Isso vai apagar TODOS os palpites e resultados da planilha para você iniciar um novo evento limpo.")
        senha_reset = st.text_input("Digite a senha admin para confirmar o Reset:", type="password", key="reset_pw")
        
        if st.button("🧨 ZERAR BOLÃO PARA NOVO EVENTO"):
            if senha_reset == SENHA_ADMIN:
                try:
                    df_vazio_palpites = pd.DataFrame(columns=["Nome", "Luta_ID", "Palpite", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2"])
                    df_vazio_resultados = pd.DataFrame(columns=["Luta_ID", "Vencedor_Real", "Pontos", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2", "F2_Especial", "Bloqueado", "Fechamento", "Abertura"])
                    sheet_write("Palpites", df_vazio_palpites)
                    sheet_write("Resultados", df_vazio_resultados)
                    invalidate_cache()
                    st.success("BOOM! Planilhas de Palpites e Resultados zeradas com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao tentar zerar: {e}")
            elif senha_reset != "":
                st.error("❌ Senha incorreta para reset.")

        st.markdown("---")
        if st.button("🚪 Sair do Admin"): st.session_state.admin_ok = False; st.rerun()
