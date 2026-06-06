@@ -117,7 +117,7 @@ def sheet_write(worksheet_name: str, df: pd.DataFrame):
        raise Exception(f"Falha de conexão com a planilha: {e}")

# ──────────────────────────────────────────────
# MOTOR DE PONTUAÇÃO (DESEMPATE INFINITO AO VIVO)
# MOTOR DE PONTUAÇÃO (COM POTN MÚLTIPLO)
# ──────────────────────────────────────────────
def calcular_pontuacao(palpites_df: pd.DataFrame, lutas_df: pd.DataFrame, resultados_df: pd.DataFrame) -> pd.DataFrame:
    if palpites_df.empty or lutas_df.empty or resultados_df.empty: return pd.DataFrame()
@@ -139,7 +139,11 @@ def calcular_pontuacao(palpites_df: pd.DataFrame, lutas_df: pd.DataFrame, result
    if not res_map.empty:
        r0 = res_map.iloc[0]
        fotn_real = {str(r0.get("FOTN_1", "")).strip().upper(), str(r0.get("FOTN_2", "")).strip().upper()} - {"", "NAN"}
        potn_real = {str(r0.get("POTN_1", "")).strip().upper(), str(r0.get("POTN_2", "")).strip().upper()} - {"", "NAN"}
        
        # MÁGICA DO POTN MÚLTIPLO: Quebra a string por vírgula e transforma numa lista real de ganhadores
        potn_str = str(r0.get("POTN_1", "")).strip().upper()
        if potn_str and potn_str != "NAN":
            potn_real = {p.strip() for p in potn_str.split(",")} - {""}

    scores: dict = {}
    for _, row in palpites_df.iterrows():
@@ -188,6 +192,7 @@ def calcular_pontuacao(palpites_df: pd.DataFrame, lutas_df: pd.DataFrame, result
            if fu and fu == fotn_real: acc["Pontos"] += 2
        if potn_real:
            pu = {acc["_potn_1"].upper(), acc["_potn_2"].upper()} - {"", "NAN"}
            # Se o lutador que a pessoa escolheu estiver na lista de vencedores, ganha 1 ponto
            acc["Pontos"] += sum(1 for n in pu if n in potn_real)

    if not scores: return pd.DataFrame()
@@ -271,11 +276,9 @@ def render_timer(target_str, title, color="#f5c518", end_text="ENCERRADO"):
    fechamento_str = ""

    if not resultados_trava.empty:
        # 1. Verifica Trava Manual primeiro (é a prioridade master)
        if "Bloqueado" in resultados_trava.columns and resultados_trava["Bloqueado"].str.upper().eq("TRUE").any():
            bolao_status = "FECHADO"

        # 2. Verifica Data de Abertura
        if "Abertura" in resultados_trava.columns:
            a_val = resultados_trava["Abertura"].iloc[0]
            if pd.notna(a_val) and str(a_val).strip() != "" and str(a_val).lower() != "nan":
@@ -286,7 +289,6 @@ def render_timer(target_str, title, color="#f5c518", end_text="ENCERRADO"):
                        bolao_status = "AGUARDANDO"
                except: pass

        # 3. Verifica Data de Fechamento (se já não estiver aguardando abrir)
        if "Fechamento" in resultados_trava.columns and bolao_status != "AGUARDANDO":
            f_val = resultados_trava["Fechamento"].iloc[0]
            if pd.notna(f_val) and str(f_val).strip() != "" and str(f_val).lower() != "nan":
@@ -297,7 +299,6 @@ def render_timer(target_str, title, color="#f5c518", end_text="ENCERRADO"):
                        bolao_status = "FECHADO"
                except: pass

    # LÓGICA DA TELA BASEADO NO STATUS
    if lutas.empty: 
        st.warning("Nenhuma luta cadastrada ainda. Aguarde o Admin configurar o evento.")
    elif bolao_status == "AGUARDANDO":
@@ -308,7 +309,6 @@ def render_timer(target_str, title, color="#f5c518", end_text="ENCERRADO"):
        st.error("🚨 **BOLÃO ENCERRADO!** Os palpites foram fechados.")
        st.info("O evento já vai começar (ou já começou). Vá para a aba **Ranking** para acompanhar a pontuação e ver o VAR. Boa sorte!")
    else:
        # STATUS = ABERTO
        if fechamento_str:
            render_timer(fechamento_str, "TEMPO RESTANTE PARA O BOLÃO FECHAR:", color="#f5c518", end_text="FECHADO!")

@@ -523,7 +523,7 @@ def render_timer(target_str, title, color="#f5c518", end_text="ENCERRADO"):

        def safe_idx(lst, val): return lst.index(val) if val in lst else 0

        lista_adm = ["— Nenhum —"] + todos_lut_adm
        lista_adm_potn = todos_lut_adm
        pf1 = pf2 = pp1 = ""
        fotn_idx = 0
        if not resultados_df_adm.empty:
@@ -536,20 +536,25 @@ def safe_idx(lst, val): return lst.index(val) if val in lst else 0
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
            st.markdown("**Performance**")
            potn_adm = st.selectbox("Lutador", lista_adm, index=safe_idx(lista_adm, pp1), key="adm_potn_unica", label_visibility="collapsed")
            st.markdown("**Performance (Pode escolher vários)**")
            potn_adm_list = st.multiselect("Lutadores", lista_adm_potn, default=default_potn, key="adm_potn_multi", label_visibility="collapsed")

        if fotn_adm != "— Nenhum —":
            fotn1_v, fotn2_v = fotn_adm.split(" vs ")
        else:
            fotn1_v, fotn2_v = "", ""

        potn1_v = "" if potn_adm == "— Nenhum —" else potn_adm
        # Junta a lista de volta numa string separada por vírgulas pra salvar na planilha
        potn1_v = ", ".join(potn_adm_list)
        potn2_v = "" 

        st.markdown("---")
@@ -563,7 +568,7 @@ def safe_idx(lst, val): return lst.index(val) if val in lst else 0
                df_res["F2_Especial"] = str(f2_especial_flag)
                df_res["Bloqueado"] = str(bolao_fechado_flag)
                df_res["Fechamento"] = str(fechamento_input)
                df_res["Abertura"] = str(abertura_input) # Salvando a Abertura aqui
                df_res["Abertura"] = str(abertura_input)
                sheet_write("Resultados", df_res)
                invalidate_cache()
                st.success("Tudo salvo com sucesso! 🏆")
