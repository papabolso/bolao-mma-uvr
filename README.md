# UVR 2.0 – Bolão de MMA 🥊

App Streamlit para automação do bolão de MMA com Google Sheets.

---

## ⚡ Estrutura esperada no Google Sheets

Crie uma planilha com **3 abas** exatamente com estes nomes e colunas:

### Aba `Lutas`
| ID | Lutador_1 | Lutador_2 | Tipo |
|----|-----------|-----------|------|
| 1  | Jon Jones | Stipe Miocic | F1 |
| 2  | Islam Makhachev | Charles Oliveira | F2 |
| 3  | Paddy Pimblett | Tony Ferguson | PRELIM |

> **Tipos aceitos:** `F1` (luta principal), `F2` (co-main), `PRELIM` (demais).

---

### Aba `Palpites`
| Nome | Luta_ID | Palpite | FOTN_1 | FOTN_2 | POTN_1 | POTN_2 |
|------|---------|---------|--------|--------|--------|--------|
*(Preenchida automaticamente pelo app)*

---

### Aba `Resultados`
| Luta_ID | Vencedor_Real | FOTN_1 | FOTN_2 | POTN_1 | POTN_2 | F2_Especial |
|---------|---------------|--------|--------|--------|--------|-------------|
*(Preenchida pelo painel Admin)*

---

## 🚀 Deploy no Streamlit Community Cloud

1. **Suba os arquivos** (`app.py`, `requirements.txt`) em um repositório GitHub.

2. **Crie uma Service Account** no Google Cloud Console:
   - Acesse: APIs & Services → Credenciais → Criar credenciais → Conta de serviço
   - Baixe o JSON da conta de serviço.

3. **Compartilhe sua planilha** com o e-mail da Service Account (editor).

4. **Configure os Secrets** em *Settings → Secrets* no Streamlit Cloud
   (use o arquivo `secrets.toml.template` como base, preenchendo com seus dados reais).

5. **Deploy** e acesse o app!

---

## 🏆 Regras de Pontuação

| Luta | Pontos |
|------|--------|
| F1 (acerto) | 2 pts sempre |
| F2 (acerto) | 2 pts se "F2 vale 2" estiver ativo, senão 1 pt |
| Demais (acerto) | 1 pt |
| FOTN par exato | +2 pts |
| POTN acerto individual | +1 pt por nome |
| Empate / Cancelada | 0 pts (ninguém pontua) |

**Desempate (ordem):** Pontuação → Acertos → Acerto F1 → Acerto F2 → Alfabético

---

## 🔐 Acesso Admin

Senha: `uvr2026`  
*(Altere a constante `SENHA_ADMIN` no `app.py` para maior segurança)*
