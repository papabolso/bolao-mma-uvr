import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# ──────────────────────────────────────────────
# PAGE CONFIG
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="UVR 2.0 – Bolão de MMA",
    page_icon="🥊",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ──────────────────────────────────────────────
# CUSTOM CSS  (dark / fight-night aesthetic)
# ──────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Barlow:wght@400;600;700&display=swap');

:root {
    --bg:      #0d0d0d;
    --surface: #1a1a1a;
    --border:  #2e2e2e;
    --accent:  #e8002d;
    --gold:    #f5c518;
    --text:    #f0f0f0;
    --muted:   #888;
}

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Barlow', sans-serif;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }

/* ── App header ── */
.uvr-header {
    text-align: center;
    padding: 2rem 0 1rem;
}
.uvr-header h1 {
    font-family: 'Bebas Neue', sans-serif;
    font-size: clamp(2.8rem, 9vw, 5rem);
    letter-spacing: 0.06em;
    color: var(--text);
    margin: 0;
    line-height: 1;
}
.uvr-header h1 span { color: var(--accent); }
.uvr-header p { color: var(--muted); font-size: 0.9rem; margin: 0.3rem 0 0; }

/* ── Tab bar ── */
[data-testid="stTabs"] [role="tablist"] {
    gap: 4px;
    border-bottom: 2px solid var(--border);
    padding-bottom: 0;
}
[data-testid="stTabs"] button[role="tab"] {
    background: var(--surface);
    color: var(--muted);
    border-radius: 6px 6px 0 0;
    border: 1px solid var(--border);
    border-bottom: none;
    font-family: 'Barlow', sans-serif;
    font-weight: 700;
    letter-spacing: 0.05em;
    padding: 0.5rem 1.2rem;
    transition: all 0.2s;
}
[data-testid="stTabs"] button[role="tab"][aria-selected="true"] {
    background: var(--accent);
    color: #fff;
    border-color: var(--accent);
}

/* ── Cards ── */
.card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
}
.card-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.1rem;
    letter-spacing: 0.08em;
    color: var(--accent);
    margin-bottom: 0.4rem;
}
.fight-tag {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    padding: 2px 8px;
    border-radius: 4px;
    background: var(--accent);
    color: #fff;
    margin-bottom: 0.5rem;
}
.fight-tag.main   { background: var(--gold); color: #000; }
.fight-tag.co-main{ background: #555; }

/* ── Ranking table ── */
.rank-table { width: 100%; border-collapse: collapse; }
.rank-table th {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 0.85rem;
    letter-spacing: 0.1em;
    color: var(--muted);
    border-bottom: 2px solid var(--border);
    padding: 0.5rem 0.7rem;
    text-align: left;
}
.rank-table td { padding: 0.55rem 0.7rem; border-bottom: 1px solid var(--border); }
.rank-table tr:last-child td { border-bottom: none; }
.rank-table tr.top-1 td { color: var(--gold); font-weight: 700; }
.rank-table tr.top-2 td { color: #c0c0c0; font-weight: 700; }
.rank-table tr.top-3 td { color: #cd7f32; font-weight: 700; }

/* ── Inputs ── */
div[data-testid="stTextInput"] input,
div[data-testid="stSelectbox"] select {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}

/* ── Buttons ── */
div[data-testid="stButton"] > button {
    background: var(--accent) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Bebas Neue', sans-serif !important;
    font-size: 1.1rem !important;
    letter-spacing: 0.08em !important;
    width: 100%;
    padding: 0.6rem 1rem !important;
    transition: opacity 0.2s !important;
}
div[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }

/* ── Alerts ── */
.st-success { background: #0a2e1a !important; border-left: 4px solid #22c55e !important; }
.st-error   { background: #2e0a0a !important; border-left: 4px solid var(--accent) !important; }

/* ── Divider ── */
hr { border-color: var(--border) !important; margin: 1.2rem 0 !important; }

/* ── Admin section titles ── */
.admin-section {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem;
    letter-spacing: 0.1em;
    color: var(--accent);
    margin: 1.2rem 0 0.5rem;
    border-bottom: 1px solid var(--border);
    padding-bottom: 0.3rem;
}
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# HEADER
# ──────────────────────────────────────────────
st.markdown("""
<div class="uvr-header">
  <h1>UVR <span>2.0</span></h1>
  <p>Bolão Oficial de MMA</p>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# GOOGLE SHEETS CONNECTION
# ──────────────────────────────────────────────
conn = st.connection("gsheets", type=GSheetsConnection)

# ──────────────────────────────────────────────
# DATA LOADING HELPERS
# ──────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_lutas():
    df = conn.read(worksheet="Lutas", usecols=["ID", "Lutador_1", "Lutador_2", "Tipo"], ttl=300)
    df["ID"] = df["ID"].astype(str)
    return df.dropna(subset=["ID"])

@st.cache_data(ttl=300)
def load_palpites():
    df = conn.read(
        worksheet="Palpites",
        usecols=["Nome", "Luta_ID", "Palpite", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2"],
        ttl=300,
    )
    df["Luta_ID"] = df["Luta_ID"].astype(str)
    return df.dropna(subset=["Nome"])

@st.cache_data(ttl=300)
def load_resultados():
    try:
        df = conn.read(
            worksheet="Resultados",
            usecols=["Luta_ID", "Vencedor_Real", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2", "F2_Especial"],
            ttl=300,
        )
        df["Luta_ID"] = df["Luta_ID"].astype(str)
        return df.dropna(subset=["Luta_ID"])
    except Exception:
        return pd.DataFrame(columns=["Luta_ID", "Vencedor_Real", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2", "F2_Especial"])


def invalidate_cache():
    load_lutas.clear()
    load_palpites.clear()
    load_resultados.clear()


# ──────────────────────────────────────────────
# SCORING ENGINE
# ──────────────────────────────────────────────
def get_tipo_luta(tipo: str) -> str:
    """Normalise fight type string."""
    return str(tipo).strip().upper()


def calcular_pontuacao(palpites_df: pd.DataFrame, lutas_df: pd.DataFrame, resultados_df: pd.DataFrame) -> pd.DataFrame:
    """
    Returns a DataFrame with columns:
    Nome, Pontos, Acertos, Acerto_F1, Acerto_F2
    sorted by ranking criteria.
    """
    if palpites_df.empty or lutas_df.empty or resultados_df.empty:
        return pd.DataFrame()

    res_map = resultados_df.set_index("Luta_ID")

    # Detect if F2 is worth 2 pts (stored in Resultados as a flag in F2_Especial col)
    # We use the value from the first row that has it populated.
    f2_especial = False
    if "F2_Especial" in res_map.columns:
        vals = res_map["F2_Especial"].dropna().astype(str).str.upper()
        if not vals.empty:
            f2_especial = vals.iloc[0] in ("TRUE", "SIM", "1", "YES")

    luta_map = lutas_df.set_index("ID")

    scores = {}  # nome -> dict of accumulators

    for _, row in palpites_df.iterrows():
        nome = str(row["Nome"]).strip()
        luta_id = str(row["Luta_ID"]).strip()
        palpite = str(row["Palpite"]).strip()

        if nome not in scores:
            scores[nome] = {
                "Pontos": 0,
                "Acertos": 0,
                "Acerto_F1": 0,
                "Acerto_F2": 0,
                # bonus armazenado uma vez por participante
                "_fotn_done": False,
                "_potn_done": False,
                "_fotn_1": str(row.get("FOTN_1", "")).strip(),
                "_fotn_2": str(row.get("FOTN_2", "")).strip(),
                "_potn_1": str(row.get("POTN_1", "")).strip(),
                "_potn_2": str(row.get("POTN_2", "")).strip(),
            }

        if luta_id not in res_map.index:
            continue

        vencedor = str(res_map.at[luta_id, "Vencedor_Real"]).strip().upper()
        if vencedor in ("EMPATE", "CANCELADA", "NAN", ""):
            continue  # ninguém pontua

        tipo = get_tipo_luta(luta_map.at[luta_id, "Tipo"]) if luta_id in luta_map.index else "PRELIM"

        acertou = palpite.upper() == vencedor

        # Pontuação por tipo
        if tipo == "F1":
            pts = 2 if acertou else 0
            scores[nome]["Acerto_F1"] += 1 if acertou else 0
        elif tipo == "F2":
            pts = (2 if f2_especial else 1) if acertou else 0
            scores[nome]["Acerto_F2"] += 1 if acertou else 0
        else:
            pts = 1 if acertou else 0

        if acertou:
            scores[nome]["Acertos"] += 1

        scores[nome]["Pontos"] += pts

    # Bônus FOTN / POTN — calculados uma vez por participante
    fotn_real = set()
    potn_real = set()
    if not res_map.empty:
        first = res_map.iloc[0]
        fotn_real = {str(first.get("FOTN_1", "")).strip().upper(), str(first.get("FOTN_2", "")).strip().upper()} - {"", "NAN"}
        potn_real = {str(first.get("POTN_1", "")).strip().upper(), str(first.get("POTN_2", "")).strip().upper()} - {"", "NAN"}

    for nome, acc in scores.items():
        # FOTN: par exato (ordem não importa) = 2 pts
        if fotn_real:
            fotn_user = {acc["_fotn_1"].upper(), acc["_fotn_2"].upper()} - {"", "NAN"}
            if fotn_user and fotn_user == fotn_real:
                acc["Pontos"] += 2

        # POTN: 1 pt por acerto individual
        if potn_real:
            potn_user = {acc["_potn_1"].upper(), acc["_potn_2"].upper()} - {"", "NAN"}
            for nome_potn in potn_user:
                if nome_potn in potn_real:
                    acc["Pontos"] += 1

    if not scores:
        return pd.DataFrame()

    df_rank = pd.DataFrame([
        {
            "Nome": nome,
            "Pontos": v["Pontos"],
            "Acertos": v["Acertos"],
            "Acerto_F1": v["Acerto_F1"],
            "Acerto_F2": v["Acerto_F2"],
        }
        for nome, v in scores.items()
    ])

    # ── Desempate ──────────────────────────────
    # 1º Pontos (desc), 2º Acertos (desc), 3º Acerto_F1 (desc),
    # 4º Acerto_F2 (desc), 5º Nome (asc)
    df_rank = df_rank.sort_values(
        by=["Pontos", "Acertos", "Acerto_F1", "Acerto_F2", "Nome"],
        ascending=[False, False, False, False, True],
    ).reset_index(drop=True)

    df_rank.insert(0, "Pos", range(1, len(df_rank) + 1))
    return df_rank


# ──────────────────────────────────────────────
# TABS
# ──────────────────────────────────────────────
tab_votar, tab_ranking, tab_admin = st.tabs(["🥊  Votar", "🏆  Ranking", "🔐  Admin"])

# ══════════════════════════════════════════════
# TAB 1 – VOTAR
# ══════════════════════════════════════════════
with tab_votar:
    lutas = load_lutas()

    if lutas.empty:
        st.warning("Nenhuma luta cadastrada ainda. Aguarde o Admin configurar o evento.")
    else:
        st.markdown("### Seu nome")
        nome_usuario = st.text_input("Nome do participante", placeholder="Ex: João Silva", label_visibility="collapsed")

        st.markdown("---")
        st.markdown("### Palpites nas Lutas")

        palpites_usuario: dict[str, str] = {}
        todos_lutadores: list[str] = []

        for _, luta in lutas.iterrows():
            luta_id  = str(luta["ID"])
            lutador1 = str(luta["Lutador_1"]).strip()
            lutador2 = str(luta["Lutador_2"]).strip()
            tipo     = str(luta["Tipo"]).strip().upper()
            todos_lutadores.extend([lutador1, lutador2])

            tag_class = "main" if tipo == "F1" else ("co-main" if tipo == "F2" else "")
            tag_label = "LUTA PRINCIPAL" if tipo == "F1" else ("CO-MAIN" if tipo == "F2" else "PRELIMINAR")

            st.markdown(f"""
            <div class="card">
              <span class="fight-tag {tag_class}">{tag_label}</span>
              <div class="card-title">{lutador1} vs {lutador2}</div>
            </div>
            """, unsafe_allow_html=True)

            escolha = st.radio(
                f"Quem vence? ({luta_id})",
                options=[lutador1, lutador2],
                horizontal=True,
                label_visibility="collapsed",
                key=f"luta_{luta_id}",
            )
            palpites_usuario[luta_id] = escolha

        st.markdown("---")
        st.markdown("### Bônus da Noite")

        todos_lutadores_uniq = sorted(set(todos_lutadores))
        opcao_vazio = ["— Selecione —"]

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🌟 FOTN – Luta da Noite**")
            fotn1 = st.selectbox("FOTN lutador 1", opcao_vazio + todos_lutadores_uniq, key="fotn1")
            fotn2 = st.selectbox("FOTN lutador 2", opcao_vazio + todos_lutadores_uniq, key="fotn2")
        with col2:
            st.markdown("**⚡ POTN – Performance**")
            potn1 = st.selectbox("POTN lutador 1", opcao_vazio + todos_lutadores_uniq, key="potn1")
            potn2 = st.selectbox("POTN lutador 2", opcao_vazio + todos_lutadores_uniq, key="potn2")

        st.markdown("---")

        if st.button("✅  ENVIAR PALPITES"):
            nome_limpo = nome_usuario.strip()
            if not nome_limpo:
                st.error("Por favor, informe seu nome.")
            elif fotn1 == fotn2 and fotn1 != "— Selecione —":
                st.error("Os dois lutadores do FOTN devem ser diferentes.")
            elif potn1 == potn2 and potn1 != "— Selecione —":
                st.error("Os dois lutadores do POTN devem ser diferentes.")
            else:
                # Carrega palpites existentes e remove linhas do mesmo usuário
                try:
                    palpites_existentes = conn.read(
                        worksheet="Palpites",
                        usecols=["Nome", "Luta_ID", "Palpite", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2"],
                    )
                    palpites_existentes = palpites_existentes.dropna(subset=["Nome"])
                    # Remove palpites anteriores deste participante
                    palpites_existentes = palpites_existentes[
                        palpites_existentes["Nome"].str.strip().str.upper() != nome_limpo.upper()
                    ]
                except Exception:
                    palpites_existentes = pd.DataFrame(
                        columns=["Nome", "Luta_ID", "Palpite", "FOTN_1", "FOTN_2", "POTN_1", "POTN_2"]
                    )

                _f1 = fotn1 if fotn1 != "— Selecione —" else ""
                _f2 = fotn2 if fotn2 != "— Selecione —" else ""
                _p1 = potn1 if potn1 != "— Selecione —" else ""
                _p2 = potn2 if potn2 != "— Selecione —" else ""

                novas_linhas = pd.DataFrame([
                    {
                        "Nome": nome_limpo,
                        "Luta_ID": lid,
                        "Palpite": palpite,
                        "FOTN_1": _f1,
                        "FOTN_2": _f2,
                        "POTN_1": _p1,
                        "POTN_2": _p2,
                    }
                    for lid, palpite in palpites_usuario.items()
                ])

                df_final = pd.concat([palpites_existentes, novas_linhas], ignore_index=True)

                try:
                    conn.update(worksheet="Palpites", data=df_final)
                    invalidate_cache()
                    st.success(f"Palpites de **{nome_limpo}** salvos com sucesso! 🥊")
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

# ══════════════════════════════════════════════
# TAB 2 – RANKING
# ══════════════════════════════════════════════
with tab_ranking:
    lutas_df     = load_lutas()
    palpites_df  = load_palpites()
    resultados_df = load_resultados()

    ranking = calcular_pontuacao(palpites_df, lutas_df, resultados_df)

    if ranking.empty:
        st.info("O ranking será exibido após o Admin inserir os resultados.")
    else:
        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        rows_html = ""
        for _, r in ranking.iterrows():
            pos  = int(r["Pos"])
            cls  = f"top-{pos}" if pos <= 3 else ""
            medal = medals.get(pos, "")
            rows_html += f"""
            <tr class="{cls}">
              <td>{medal} {pos}º</td>
              <td>{r['Nome']}</td>
              <td style="text-align:center;">{int(r['Pontos'])}</td>
              <td style="text-align:center;">{int(r['Acertos'])}</td>
              <td style="text-align:center;">{"✅" if r['Acerto_F1'] else "❌"}</td>
              <td style="text-align:center;">{"✅" if r['Acerto_F2'] else "❌"}</td>
            </tr>"""

        st.markdown(f"""
        <table class="rank-table">
          <thead>
            <tr>
              <th>POS</th><th>NOME</th>
              <th style="text-align:center;">PTS</th>
              <th style="text-align:center;">ACERTOS</th>
              <th style="text-align:center;">F1</th>
              <th style="text-align:center;">F2</th>
            </tr>
          </thead>
          <tbody>{rows_html}</tbody>
        </table>
        """, unsafe_allow_html=True)

        st.caption("Atualizado a cada 5 minutos · Critérios de desempate: Pts > Acertos > F1 > F2 > Nome")

# ══════════════════════════════════════════════
# TAB 3 – ADMIN
# ══════════════════════════════════════════════
with tab_admin:
    SENHA_ADMIN = "uvr2026"

    if "admin_autenticado" not in st.session_state:
        st.session_state.admin_autenticado = False

    if not st.session_state.admin_autenticado:
        st.markdown("### 🔐 Área Restrita")
        senha = st.text_input("Senha", type="password", placeholder="Digite a senha admin")
        if st.button("Entrar"):
            if senha == SENHA_ADMIN:
                st.session_state.admin_autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    else:
        st.markdown("### 🛠️ Painel Admin – UVR 2.0")

        # ── Gerenciar Lutas ──────────────────────────────
        st.markdown('<div class="admin-section">📋 Gerenciar Lutas</div>', unsafe_allow_html=True)

        lutas_atual = load_lutas()
        st.dataframe(lutas_atual, use_container_width=True, hide_index=True)

        with st.expander("➕ Adicionar / substituir tabela de Lutas"):
            st.info("Cole abaixo os dados no formato CSV (ID,Lutador_1,Lutador_2,Tipo). Tipo aceito: F1, F2, PRELIM.")
            lutas_csv = st.text_area("Dados CSV", height=200,
                placeholder="ID,Lutador_1,Lutador_2,Tipo\n1,Jon Jones,Stipe Miocic,F1\n2,Islam Makhachev,Charles Oliveira,F2")
            if st.button("💾 Salvar Lutas"):
                try:
                    from io import StringIO
                    df_lutas_new = pd.read_csv(StringIO(lutas_csv))
                    df_lutas_new.columns = [c.strip() for c in df_lutas_new.columns]
                    conn.update(worksheet="Lutas", data=df_lutas_new)
                    invalidate_cache()
                    st.success("Lutas salvas!")
                except Exception as e:
                    st.error(f"Erro: {e}")

        # ── Inserir Resultados ───────────────────────────
        st.markdown('<div class="admin-section">🏁 Inserir Resultados das Lutas</div>', unsafe_allow_html=True)

        lutas_df_admin = load_lutas()
        resultados_df_admin = load_resultados()

        f2_especial_flag = st.checkbox(
            "F2 vale 2 pontos neste evento?",
            value=(
                resultados_df_admin["F2_Especial"].astype(str).str.upper().eq("TRUE").any()
                if not resultados_df_admin.empty and "F2_Especial" in resultados_df_admin.columns
                else False
            ),
        )

        resultados_novos: list[dict] = []

        if lutas_df_admin.empty:
            st.warning("Cadastre as lutas primeiro.")
        else:
            for _, luta in lutas_df_admin.iterrows():
                lid      = str(luta["ID"])
                lutador1 = str(luta["Lutador_1"]).strip()
                lutador2 = str(luta["Lutador_2"]).strip()
                tipo     = str(luta["Tipo"]).strip().upper()

                # Pré-preenche se já existe resultado
                venc_atual = ""
                if lid in resultados_df_admin["Luta_ID"].values:
                    venc_atual = str(resultados_df_admin.loc[resultados_df_admin["Luta_ID"] == lid, "Vencedor_Real"].values[0]).strip()

                opcoes = [lutador1, lutador2, "Empate", "Cancelada"]
                idx_default = opcoes.index(venc_atual) if venc_atual in opcoes else 0

                tag_label = "PRINCIPAL" if tipo == "F1" else ("CO-MAIN" if tipo == "F2" else "PRELIM")
                st.markdown(f"**[{tag_label}] {lutador1} vs {lutador2}**")
                vencedor_sel = st.selectbox(
                    f"Vencedor luta {lid}",
                    opcoes,
                    index=idx_default,
                    key=f"res_{lid}",
                    label_visibility="collapsed",
                )
                resultados_novos.append({"Luta_ID": lid, "Vencedor_Real": vencedor_sel})

        # ── Bônus da Noite ───────────────────────────────
        st.markdown('<div class="admin-section">🌟 Bônus da Noite (FOTN / POTN)</div>', unsafe_allow_html=True)

        todos_lut_admin = []
        if not lutas_df_admin.empty:
            todos_lut_admin = sorted(
                set(lutas_df_admin["Lutador_1"].tolist() + lutas_df_admin["Lutador_2"].tolist())
            )

        opcao_vazio_admin = ["— Nenhum —"]
        prev_fotn1, prev_fotn2, prev_potn1, prev_potn2 = "", "", "", ""
        if not resultados_df_admin.empty:
            r0 = resultados_df_admin.iloc[0]
            prev_fotn1 = str(r0.get("FOTN_1", "")).strip()
            prev_fotn2 = str(r0.get("FOTN_2", "")).strip()
            prev_potn1 = str(r0.get("POTN_1", "")).strip()
            prev_potn2 = str(r0.get("POTN_2", "")).strip()

        def safe_idx(lst, val):
            try:
                return lst.index(val)
            except ValueError:
                return 0

        lista_admin = opcao_vazio_admin + todos_lut_admin

        col_f, col_p = st.columns(2)
        with col_f:
            st.markdown("**FOTN (Luta da Noite)**")
            fotn1_adm = st.selectbox("FOTN 1", lista_admin, index=safe_idx(lista_admin, prev_fotn1), key="adm_fotn1")
            fotn2_adm = st.selectbox("FOTN 2", lista_admin, index=safe_idx(lista_admin, prev_fotn2), key="adm_fotn2")
        with col_p:
            st.markdown("**POTN (Performance)**")
            potn1_adm = st.selectbox("POTN 1", lista_admin, index=safe_idx(lista_admin, prev_potn1), key="adm_potn1")
            potn2_adm = st.selectbox("POTN 2", lista_admin, index=safe_idx(lista_admin, prev_potn2), key="adm_potn2")

        fotn1_v = fotn1_adm if fotn1_adm != "— Nenhum —" else ""
        fotn2_v = fotn2_adm if fotn2_adm != "— Nenhum —" else ""
        potn1_v = potn1_adm if potn1_adm != "— Nenhum —" else ""
        potn2_v = potn2_adm if potn2_adm != "— Nenhum —" else ""

        st.markdown("---")

        if st.button("💾  SALVAR TODOS OS RESULTADOS"):
            try:
                df_res = pd.DataFrame(resultados_novos)
                df_res["FOTN_1"] = fotn1_v
                df_res["FOTN_2"] = fotn2_v
                df_res["POTN_1"] = potn1_v
                df_res["POTN_2"] = potn2_v
                df_res["F2_Especial"] = str(f2_especial_flag)

                conn.update(worksheet="Resultados", data=df_res)
                invalidate_cache()
                st.success("Resultados salvos com sucesso! O ranking será atualizado em instantes. 🏆")
            except Exception as e:
                st.error(f"Erro ao salvar resultados: {e}")

        st.markdown("---")
        if st.button("🚪 Sair do Admin"):
            st.session_state.admin_autenticado = False
            st.rerun()
