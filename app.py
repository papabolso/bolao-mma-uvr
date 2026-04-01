import streamlit as st
import pandas as pd
import requests

# ==========================================
# 1. CONFIGURAÇÃO DA PÁGINA
# ==========================================
st.set_page_config(page_title="BOLÃO UVR 2.0 🤖", page_icon="🥊", layout="wide")

st.title("🥊 BOLÃO UVR 2.0 🤖")
st.markdown("Bem-vindo ao sistema oficial de palpites!")

# ==========================================
# 2. FUNÇÕES DE LEITURA (CACHE 1 MIN E ANTI-BUG EXTREMO)
# ==========================================
@st.cache_data(ttl=60)
def get_data(spreadsheet_id, gid):
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/export?format=csv&gid={gid}"
    try:
        df = pd.read_csv(url)
        # Limpa espaços em branco ocultos nas colunas
        df.columns = df.columns.str.strip() 
        # Arruma os nomes caso você tenha digitado sem o underline na planilha
        df.columns = df.columns.str.replace("Luta ID", "Luta_ID")
        df.columns = df.columns.str.replace("Lutador 1", "Lutador_1")
        df.columns = df.columns.str.replace("Lutador 2", "Lutador_2")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# ==========================================
# 3. CARREGANDO DADOS E CREDENCIAIS
# ==========================================
sheet_id = st.secrets["gsheets"]["spreadsheet_id"]
lutas_gid = st.secrets["gsheets"]["lutas_gid"]
palpites_gid = st.secrets["gsheets"]["palpites_gid"]
resultados_gid = st.secrets["gsheets"]["resultados_gid"]
webhook_url = st.secrets["gsheets"]["apps_script_url"]

df_lutas = get_data(sheet_id, lutas_gid)
df_palpites = get_data(sheet_id, palpites_gid)
df_resultados = get_data(sheet_id, resultados_gid)

# Garante que a coluna 'Pontos' exista nas Lutas
if not df_lutas.empty:
    if 'Pontos' not in df_lutas.columns:
        df_lutas['Pontos'] = 1
    else:
        df_lutas['Pontos'] = pd.to_numeric(df_lutas['Pontos'], errors='coerce').fillna(1)

# ==========================================
# 4. NAVEGAÇÃO ANTIGA (BARRA LATERAL)
# ==========================================
menu = st.sidebar.radio("Navegação", ["📋 Card de Lutas", "🏆 Ranking", "🔐 Admin"])

# ==========================================
# ABA 1: CARD DE LUTAS (PÚBLICO E BLINDADO)
# ==========================================
if menu == "📋 Card de Lutas":
    st.header("Card do Evento")
    if not df_lutas.empty:
        for index, row in df_lutas.iterrows():
            # Usa .get() para não quebrar o site se a coluna sumir do Google Sheets
            luta_id = row.get('Luta_ID', index + 1)
            lutador1 = row.get('Lutador_1', 'Lutador 1')
            lutador2 = row.get('Lutador_2', 'Lutador 2')
            
            st.info(f"**Luta {luta_id}**: {lutador1} vs {lutador2}")
    else:
        st.warning("Nenhuma luta cadastrada ainda.")

# ==========================================
# ABA 2: RANKING E VAR
# ==========================================
elif menu == "🏆 Ranking":
    st.header("🏆 Ranking Geral")
    
    if not df_palpites.empty and not df_resultados.empty and 'Luta_ID' in df_palpites.columns and 'Luta_ID' in df_resultados.columns:
        df_calc = pd.merge(df_palpites, df_resultados[['Luta_ID', 'Vencedor_Real']], on="Luta_ID", how="left")
        
        # Só tenta dar merge na pontuação se a df_lutas estiver certinha
        if 'Luta_ID' in df_lutas.columns:
            df_calc = pd.merge(df_calc, df_lutas[['Luta_ID', 'Pontos']], on="Luta_ID", how="left")
        else:
            df_calc['Pontos'] = 1
            
        df_calc['Acertou'] = df_calc['Palpite'] == df_calc['Vencedor_Real']
        df_calc['Pontos_Luta'] = df_calc['Acertou'] * df_calc['Pontos']
        
        df_ranking = df_calc.groupby('Nome')['Pontos_Luta'].sum().reset_index()
        
        res_fotn_1 = df_resultados['FOTN_1'].iloc[0] if 'FOTN_1' in df_resultados.columns else None
        res_fotn_2 = df_resultados['FOTN_2'].iloc[0] if 'FOTN_2' in df_resultados.columns else None
        res_potn_1 = df_resultados['POTN_1'].iloc[0] if 'POTN_1' in df_resultados.columns else None
        res_potn_2 = df_resultados['POTN_2'].iloc[0] if 'POTN_2' in df_resultados.columns else None
        
        user_bonuses = df_palpites.groupby('Nome').first().reset_index()
        pontos_bonus_list = []
        
        for index, row in user_bonuses.iterrows():
            pts_bonus = 0
            user_fotn = {row.get('FOTN_1'), row.get('FOTN_2')}
            real_fotn = {res_fotn_1, res_fotn_2}
            if user_fotn == real_fotn and len(real_fotn - {None, ''}) == 2:
                pts_bonus += 2
                
            user_potn = [row.get('POTN_1'), row.get('POTN_2')]
            real_potn = [res_potn_1, res_potn_2]
            for p in user_potn:
                if p in real_potn and p not in [None, '']:
                    pts_bonus += 1
                    
            pontos_bonus_list.append({'Nome': row['Nome'], 'Pontos_Bonus': pts_bonus})
            
        df_bonus = pd.DataFrame(pontos_bonus_list)
        df_ranking = pd.merge(df_ranking, df_bonus, on='Nome')
        df_ranking['Pontuação Total'] = df_ranking['Pontos_Luta'] + df_ranking['Pontos_Bonus']
        
        df_ranking = df_ranking.sort_values(by='Pontuação Total', ascending=False).reset_index(drop=True)
        df_ranking.index += 1 
        
        st.dataframe(df_ranking[['Nome', 'Pontuação Total', 'Pontos_Luta', 'Pontos_Bonus']], use_container_width=True)
        
        st.markdown("---")
        st.subheader("🔍 VAR: Detalhes dos Palpites")
        participante_selecionado = st.selectbox("Selecione um participante para ver as escolhas:", [""] + list(df_ranking['Nome']))
        
        if participante_selecionado != "":
            detalhes = df_palpites[df_palpites['Nome'] == participante_selecionado]
            st.write(f"Palpites de **{participante_selecionado}**:")
            
            # Mais uma segurança para não quebrar a tabela do VAR
            if 'Luta_ID' in detalhes.columns and 'Palpite' in detalhes.columns:
                st.dataframe(detalhes[['Luta_ID', 'Palpite']], hide_index=True)
            else:
                st.dataframe(detalhes)
            
            primeira_linha = detalhes.iloc[0]
            st.info(f"🏆 **Luta da Noite:** {primeira_linha.get('FOTN_1')} vs {primeira_linha.get('FOTN_2')}")
            st.info(f"💥 **Performance:** {primeira_linha.get('POTN_1')} e {primeira_linha.get('POTN_2')}")

    else:
        st.warning("Aguardando palpites ou a coluna Luta_ID na planilha de Resultados e Palpites.")

# ==========================================
# ABA 3: ADMIN (BLINDADO)
# ==========================================
elif menu == "🔐 Admin":
    st.header("Painel de Controle do Evento")
    
    dict_resultados = {}
    if not df_resultados.empty and 'Luta_ID' in df_resultados.columns and 'Vencedor_Real' in df_resultados.columns:
        dict_resultados = {str(row['Luta_ID']): row['Vencedor_Real'] for _, row in df_resultados.iterrows()}
    
    with st.form("form_admin"):
        novos_resultados = []
        st.subheader("📝 Resultados e Pontuações")
        
        if not df_lutas.empty:
            for index, luta in df_lutas.iterrows():
                id_luta = str(luta.get('Luta_ID', index + 1))
                lutador1 = luta.get('Lutador_1', f'Lutador A (Luta {id_luta})')
                lutador2 = luta.get('Lutador_2', f'Lutador B (Luta {id_luta})')
                peso_atual = int(luta.get('Pontos', 1))
                
                resultado_salvo = dict_resultados.get(id_luta, "Selecione")
                opcoes = ["Selecione", lutador1, lutador2, "Empate"]
                index_padrao = opcoes.index(resultado_salvo) if resultado_salvo in opcoes else 0
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    vencedor = st.radio(
                        f"Luta {id_luta}: {lutador1} vs {lutador2}",
                        options=opcoes,
                        index=index_padrao,
                        key=f"admin_luta_{id_luta}"
                    )
                with col2:
                    novo_peso = st.number_input(f"Pontos ({id_luta})", value=peso_atual, min_value=1, step=1, key=f"peso_{id_luta}")
                
                novos_resultados.append({"Luta_ID": id_luta, "Vencedor_Real": vencedor, "Pontos": novo_peso})
                st.write("---")
        
        st.subheader("Bônus do Evento")
        fotn1_salvo = df_resultados['FOTN_1'].iloc[0] if not df_resultados.empty and 'FOTN_1' in df_resultados.columns else ""
        fotn2_salvo = df_resultados['FOTN_2'].iloc[0] if not df_resultados.empty and 'FOTN_2' in df_resultados.columns else ""
        potn1_salvo = df_resultados['POTN_1'].iloc[0] if not df_resultados.empty and 'POTN_1' in df_resultados.columns else ""
        potn2_salvo = df_resultados['POTN_2'].iloc[0] if not df_resultados.empty and 'POTN_2' in df_resultados.columns else ""
        
        col3, col4 = st.columns(2)
        with col3:
            in_fotn_1 = st.text_input("Luta da Noite (Lutador 1)", value=fotn1_salvo)
            in_fotn_2 = st.text_input("Luta da Noite (Lutador 2)", value=fotn2_salvo)
        with col4:
            in_potn_1 = st.text_input("Performance (Lutador 1)", value=potn1_salvo)
            in_potn_2 = st.text_input("Performance (Lutador 2)", value=potn2_salvo)
            
        submitted = st.form_submit_button("Salvar Resultados e Pontos 🚀")
        
        if submitted:
            dados_para_enviar = {"acao": "salvar_resultados", "dados": []}
            for item in novos_resultados:
                dados_para_enviar["dados"].append({
                    "Luta_ID": item["Luta_ID"],
                    "Vencedor_Real": item["Vencedor_Real"],
                    "Pontos": item["Pontos"],
                    "FOTN_1": in_fotn_1,
                    "FOTN_2": in_fotn_2,
                    "POTN_1": in_potn_1,
                    "POTN_2": in_potn_2
                })
            
            try:
                response = requests.post(webhook_url, json=dados_para_enviar)
                if response.status_code == 200:
                    st.success("Sucesso! Dê um 'Clear Cache' para ver as mudanças no Ranking.")
                else:
                    st.error("Erro ao comunicar com a planilha.")
            except Exception as e:
                st.error(f"Falha no envio: {e}")

    # ==========================================
    # ZONA DE PERIGO: RESET DO EVENTO
    # ==========================================
    st.markdown("---")
    st.subheader("⚠️ ZONA DE PERIGO")
    st.warning("Esta ação apagará TODOS os palpites e resultados atuais para iniciar um novo evento.")
    
    SENHA_MESTRE = "senha123" 
    
    senha_digitada = st.text_input("Digite a senha de administrador para confirmar o Reset:", type="password")
    
    if st.button("🚨 ZERAR BOLÃO PARA NOVO EVENTO"):
        if senha_digitada == SENHA_MESTRE:
            try:
                comando_reset = {"acao": "zerar_planilhas"}
                response = requests.post(webhook_url, json=comando_reset)
                
                if response.status_code == 200:
                    st.success("BOOM! 💥 O bolão foi zerado com sucesso. Prepare-se para o próximo card!")
                else:
                    st.error("Erro ao tentar zerar a planilha.")
            except Exception as e:
                st.error(f"Falha na conexão: {e}")
        elif senha_digitada != "":
            st.error("❌ Senha incorreta! O botão de autodestruição foi bloqueado.")
