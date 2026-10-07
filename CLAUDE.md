# Bolão MMA UVR

App de bolão de MMA para um grupo de ~10 amigos. Zerado a cada evento (UFC / DWCS).
Admin = o dono do repo (Luis Fillipe). Interface e comentários **em português**.

## Stack

- **Streamlit** (`app.py`, arquivo único, ~190 KB) hospedado no Streamlit Community Cloud
- **Supabase** (Postgres) como banco — projeto `seexgvfglqecvuvpgeus`
- Credenciais em `.streamlit/secrets.toml` (nunca no repo)
- `requirements.txt` exige **streamlit>=1.39** (ver "escolha clicável" abaixo)

## Banco

| Tabela | Colunas |
| --- | --- |
| `lutas` | id, lutador_1, lutador_2, tipo, ordem, foto_1, foto_2, band_1, band_2 |
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

## Temas

`THEMES` em `app.py`, selecionável no Admin, persistido em `config.tema`.
Cinco: `fightnight`, `ufc`, `dwcs`, `noche`, `numbered`.

`noche`, `numbered` e `fightnight` têm `hero_art` — um hero em SVG renderizado por
`components.html`. Os outros dois ainda usam o hero antigo em CSS.

- `noche` usa textura em base64; `numbered` e `fightnight` usam `feTurbulence` procedural (mais leve).
- `fightnight` funde as bordas no fundo da página (`#08090B`) para o hero não parecer imagem colada.

Fallback de tema é `dwcs` (não `ufc`) — é o que mais roda.

## Importador ESPN

`_buscar_card_espn(evid)` no Admin. Cadeia:

```
sports.core.api.espn.com/v2/sports/mma/leagues/ufc/events/{id}
  → competitions[].$ref
    → competitors[].athlete.$ref
      → fullName, headshot.href, flag.href, citizenship
```

A ESPN **já entrega a bandeira pronta** em `flag.href`
(`https://a.espncdn.com/i/teamlogos/countries/500/usa.png`). Se faltar, montar pelo
`citizenship` minúsculo. Não usar emoji de bandeira: Chrome no Windows não renderiza.

A ESPN lista prelim → main; o importador **inverte**. O CSV não tem foto nem bandeira.

## Deploy

GitHub → Streamlit Cloud redeploya sozinho. Não há CI.
Migrações de banco são arquivos `migracao_*.sql` aplicados à mão no Supabase.

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
