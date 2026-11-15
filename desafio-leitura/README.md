# Desafio de Leitura (app Android)

App pessoal para acompanhar um desafio de leitura: uma **meta de páginas por dia** (vale para
todos os livros juntos) e, em cada livro, a página em que comecei e a página em que estou. O app
calcula quantas li, mostra o anel do dia e um gráfico de barras por livro (7 ou 30 dias).

Não tem nada a ver com o bolão; mora aqui só para o GitHub compilar o APK.

## Baixar

Cada push nesta pasta roda o workflow **Desafio de Leitura (APK)** e publica o arquivo na release
[`leitura`](../../releases/tag/leitura). No celular: abrir o link, baixar `desafio-leitura.apk` e
instalar (o Android pede para permitir "instalar apps desconhecidos" na primeira vez).

A chave de assinatura é fixa (`app/leitura.keystore`), então uma versão nova instala por cima da
antiga **sem perder os dados**.

## Como é feito

- A tela inteira é `app/src/main/assets/index.html` (HTML + CSS + JS, sem biblioteca, sem internet).
- `MainActivity.java` só abre esse arquivo num WebView. Sem permissões.
- Dados no `localStorage` do WebView. Menu `⋯` → Backup copia/restaura tudo como texto.
- Para testar no computador basta abrir o `index.html` no navegador.

## Regras das contas

- **Meta:** vale no dia em que foi definida e continua nos dias seguintes até mudar.
- **Comecei na:** se não for digitada, é a página em que o livro parou no último dia anotado.
- **Lidas** = `estou na` − `comecei na` (nunca negativo).
- **Dias seguidos:** dias batendo a meta; o dia de hoje ainda em aberto não quebra a sequência.
