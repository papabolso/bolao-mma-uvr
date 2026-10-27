# Bolão MMA UVR

App de bolão de MMA para um grupo de ~10 amigos. Zerado a cada evento (UFC / DWCS).
Admin = o dono do repo (Luis Fillipe). Interface e comentários **em português**.

## Stack

- **Streamlit** (`app.py`, arquivo único, ~190 KB) hospedado no Streamlit Community Cloud
- **Supabase** (Postgres) como banco — projeto `seexgvfglqecvuvpgeus`
- Credenciais em `.streamlit/secrets.toml` (nunca no repo)
- `requirements.txt` exige **streamlit>=1.65** (`st-key-` desde 1.39; `key`/`on_change` no `st.popover` e
  `st.container(horizontal=True)` são da 1.65)

## Banco

| Tabela | Colunas |
| --- | --- |
| `lutas` | id, lutador_1, lutador_2, tipo, ordem, foto_1, foto_2, band_1, band_2, rec_1, rec_2, hist_1, hist_2, nasc_1, nasc_2 |
| `palpites` | id, nome, luta_id, palpite, fotn_1, fotn_2, potn_1, potn_2, created_at |
| `resultados` | luta_id, vencedor_real, pontos |
| `config` | id, fotn_1, fotn_2, potn_1, potn_2, f2_especial, bloqueado, abertura, fechamento, tema |

`tipo`: `F1` (luta principal, 2 pts), `F2` (co-main, 2 pts se `f2_especial`), `PRELIM` (1 pt).
`ordem` 1 = luta principal. As preliminares acontecem **antes** na vida real, mas vêm por último na lista.

**RLS está DESLIGADO nas 4 tabelas, sem políticas.** Isso só é seguro porque o Streamlit roda no
servidor e a chave fica no `secrets.toml`, fora do navegador. Se um dia o frontend virar site no
browser, **ligar RLS é pré-requisito**, não ajuste final.

## Desempate do ranking

`Pontos` → `Acertos` → `Luta_1` → `Luta_2` → … → `Nome` (alfabético **crescente**).
Consequência não óbvia: **cartões idênticos nunca empatam** — ganha quem vem antes no alfabeto.
Já aconteceu de participante ficar com 0% de chance matemática por ser clone de outro.

## Armadilhas do Streamlit (custaram horas — leia antes de mexer na UI)

1. **`st.markdown` remove `<img>` e `onerror`.** Imagem só entra por `components.html` (iframe,
   não sanitiza) ou como `background-image` dentro de `<style>` — essa passa.
2. **`components.html` é iframe: não devolve valor pro Python.** Serve para exibir, nunca para
   capturar clique.
3. **Especificidade.** O CSS global do app e o `extra_css` de cada tema têm regras
   `div[data-testid="stButton"]>button{...!important}` (0,1,2). Regra por card precisa ser
   `.st-key-<key> div[data-testid="stButton"]>button` (0,2,2) para vencer.
4. **A regra base tem `padding:.8rem 1rem!important`.** Qualquer padding próprio precisa de
   `!important`, senão o label volta ao centro vertical e cai em cima da foto.
5. **O tema impõe `clip-path` diagonal e `font-family:'Anton'`.** Anular com
   `clip-path:none!important; font-family:inherit!important` onde não se quer.
6. **Streamlit põe `white-space:nowrap` no `<p>` do botão.** Para o nome quebrar linha, a regra
   tem que mirar o `<p>`, não o `<button>`.
7. **Nunca empilhar dois `position:absolute`** (container + `<p>`). O `<p>` passa a se posicionar
   pelo container e sai do botão. Posicionar só o `stMarkdownContainer`; `<p>` fica `static`.
8. **Chaves de CSS.** O bloco de tema é f-string → `{{` e `}}`. O bloco estático (depois de
   `+ _ROOT_VARS + """`) usa chave simples. Confundir isso quebra o parse.
9. **Abas no 1.65 não são mais `button[role=tab]`.** Agora é `div[data-testid="stTab"][aria-selected="true"]`
   e o sublinhado é `.react-aria-SelectionIndicator`. Regras antigas de aba nos temas não pegam.

## Escolha clicável (tela de palpites)

Cada lutador é um `st.button` real, estilizado via a classe `st-key-<key>` que o Streamlit gera
a partir do `key=` (recurso oficial desde **1.39**). A foto entra como `background-image` no
`::before`, a bandeira como camada de fundo do próprio botão, e o check no `::after`.

- Estado em `st.session_state[f"pick_{lid}"]`, começa **vazio** (o `st.radio` antigo vinha com o
  lutador 1 pré-marcado e deixava enviar no automático).
- O envio valida e bloqueia se faltar luta.
- Todo o CSS sai num `<style>` único **depois** dos botões — assim o estado selecionado aparece
  no mesmo ciclo, sem reload extra.

Se o `requirements.txt` cair abaixo de 1.39, os botões continuam funcionando mas ficam sem estilo.

**Fluidez no celular** (cada toque era um rerun do app inteiro, ~1 s no Streamlit Cloud):

- **Seleção instantânea:** `PICK_JS` (injetado por `components.html`, iframe da mesma origem, que
  alcança `window.parent.document`) marca no clique o card tocado com `data-pk="on"` e o adversário
  com `"off"`. Cada card já traz no CSS o estado **oposto** sob `.st-key-X[data-pk=...]`
  (`_cores_pick(..., oposto=True)`), então pinta antes do servidor responder. Quando o rerun chega,
  o estado real bate com o que já está na tela. Usa `click` e não `pointerdown`: começar a rolar a
  tela em cima de um card não pode marcar palpite.
- **`@st.fragment` em `_tela_palpites`:** o toque refaz só a tela de palpites (não o hero, o
  ranking e o admin). Por isso o envio **reconfere o status** (`status_bolao`, com
  `load_config.clear()`) antes de gravar, e depois de salvar faz `st.rerun()` do app inteiro para o
  ranking ver o envio. A mensagem, o gong e os balões saem nesse rerun (`session_state["_enviado"]`).
- **CSS enxuto:** regras comuns a todos os cards saem uma vez em `PICK_CSS`
  (`[class*="st-key-pk"]`); por card vai só altura, foto, cartel/idade e cores. Cada toque
  reenvia esse CSS.

## Temas

`THEMES` em `app.py`, selecionável no Admin, persistido em `config.tema`.
Sete: `fightnight`, `ufc`, `dwcs`, `noche`, `numbered`, `cinturao`, `ouro`.

`noche`, `numbered`, `fightnight` e `cinturao` têm `hero_art` — um hero em SVG renderizado por
`components.html`. `ufc` e `dwcs` ainda usam o hero antigo em CSS.

- `"hero_full": True` (fightnight, cinturao): hero de ponta a ponta, colado no topo
  (`_HERO_FULL_CSS` + marcador `.fn-hero-mark`). O tema pinta a página numa cor só e o hero
  termina exatamente nela.
- `cinturao` (eventos numerados): o cinturão é **vetor** (`CINTO_SVG`, gerado por `_oct`,
  `_placa_lateral`, `_tacha`, `_ponta`), modelo "legacy": placa octogonal com aro cromado, faixa
  dourada com "UVR" gravado em bronze, placas laterais, rebites e pontas. Coordenadas 1000x340,
  centro (500,170). Nítido em qualquer tela (a versão em imagem ficava borrada no celular). No
  celular tem 720-760px, mais largo que a tela. Preto + ouro; vermelho só na costura, nos filetes
  de "BOLÃO", no filete do título e na tag da luta principal. Usa `sel_a/sel_b/sel_glow/sel_leg`
  para o card escolhido em ouro.
- `ouro`: mesmo hero do `cinturao` (faixa preta), mas a **página é ouro fosco** e o **preto marca
  a escolha** (card, chip do bônus, botão). Texto direto sobre o ouro fica escuro; painéis
  (ranking, campos, histórico, popover do bônus) viram placas pretas. Sem brilho/gradiente
  metálico forte de propósito — é o que deixava brega.
- Cores dos cards de escolha (palpite e bônus) saem do dicionário `PK` na aba Palpitar; um tema
  troca qualquer uma pela chave `"pick"` (só o `ouro` usa). Sem `"pick"`, tudo fica como antes.

- `noche` usa textura em base64; `numbered` e `fightnight` usam `feTurbulence` procedural (mais leve).
- `fightnight` funde as bordas no fundo da página (`#08090B`) para o hero não parecer imagem colada.

Fallback de tema é `dwcs` (não `ufc`) — é o que mais roda.

## Importador ESPN

`_buscar_card_espn(evid)` no Admin. Cadeia:

```
sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/{id}
  → competitions[].$ref
    → competitors[].athlete.$ref
      → fullName, headshot.href, flag.href, citizenship, dateOfBirth
```

Idade: guarda `dateOfBirth` cortado em `AAAA-MM-DD` em `nasc_1/nasc_2` (`migracao_idade.sql`) e
calcula na hora (`fmt_idade`), então não envelhece no banco. Aparece junto do cartel embaixo do
nome ("28-4 · 38 anos"; a idade em vermelho, cor em `PK["idade"]`). "Atualizar cartéis" também preenche, sem zerar palpites.

"📊 Atualizar cartéis" casa pelo nome e também **atualiza foto e bandeira** (a ESPN às vezes só põe
a foto dias depois). Troca só quando a ESPN mandou uma diferente; foto que não é `espncdn.com`
(colada à mão no CSV) não é sobrescrita, e foto vazia da ESPN não apaga a atual.

Foto: atleta novo às vezes vem **sem `headshot`** no perfil, mas a imagem já existe no CDN pelo ID
(`a.espncdn.com/i/headshots/mma/players/full/{id}.png`). `_foto_por_id` monta esse link e só usa
se um HEAD responder imagem (404 = ainda não tem). Foi o caso do Asaf Chopurov (5454811).

A ESPN **já entrega a bandeira pronta** em `flag.href`
(`https://a.espncdn.com/i/teamlogos/countries/500/usa.png`). Se faltar, montar pelo
`citizenship` minúsculo. Não usar emoji de bandeira: Chrome no Windows não renderiza.

A ESPN lista prelim → main; o importador **inverte**. O CSV não tem foto nem bandeira.

## Deploy

GitHub → Streamlit Cloud redeploya sozinho. Não há CI do bolão (o único workflow é o do FitSync, abaixo).
Migrações de banco são arquivos `migracao_*.sql` aplicados à mão no Supabase.

## Fluxo de trabalho

- **Merge na `main` e push estão autorizados sem perguntar** (o dono pediu: "pode subir, sempre pode").
  Fluxo: branch → teste local → commit → merge → push → avisar o que subiu. Migração que só
  adiciona coluna vai junto; qualquer coisa que apague ou zere dados no banco ainda pede confirmação.
- **O site é usado principalmente no celular.** Desenhar a UI primeiro para 375px e testar também
  em 320px. O Streamlit empilha `st.columns` abaixo de 640px; a linha do palpite usa
  `:has([class*="st-key-pk"])` para manter os lutadores lado a lado.
- Teste local sem tocar no Supabase: rodar uma cópia do `app.py` com um módulo `supabase.py` falso
  ao lado (devolve dados fixos) e um `secrets.toml` falso.

## Convenções

- Comentários e interface em português; nomes de variáveis sem acento.
- `app.py` é arquivo único e assim deve continuar — é o que o dono consegue subir pelo navegador.
- Mudança de UI: **testar junto com o CSS global**, nunca isolada. O jeito confiável é subir o
  Streamlit e **medir no DOM** (position computado, bounding box), não olhar print.

## Pendências

- Heros em SVG para `ufc` e `dwcs` (ainda nos antigos)
- Tabela de ranking: pódio para os 3 primeiros
- FOTN/POTN ainda são `selectbox`; poderiam virar cards clicáveis
- Aba VAR nunca recebeu tratamento de design

## Outro projeto no repo: `fitsync-android/`

App Android (Kotlin/Compose) que sincroniza os treinos do Huawei Watch Fit 5 com o Strava, no
lugar do Health Sync. **Não tem nada a ver com o bolão**; fica aqui só por enquanto. Compila pelo
workflow `.github/workflows/fitsync-apk.yml` (só dispara em mudanças dentro de `fitsync-android/`).
Detalhes e configuração no `fitsync-android/README.md`.
