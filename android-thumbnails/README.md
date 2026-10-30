# Explorador de Thumbnails

App Android que mostra o que está guardado na pasta oculta `DCIM/.thumbnails`, inclusive as
miniaturas empilhadas dentro dos arquivos `.thumbdata`. Independente do bolão: só mora neste repo.

## Instalar

Baixar `explorador-thumbnails.apk` da release **explorador-thumbnails** do repositório (o GitHub
Actions recompila e atualiza a cada push nesta pasta). Abrir no celular e permitir "instalar apps
desconhecidos". Na primeira abertura o app pede **Acesso a todos os arquivos**: sem ela o Android 11+
não deixa nenhum app ver pastas ocultas como a `.thumbnails`.

## O que tem na pasta `.thumbnails`

| Arquivo | O que é | O app faz |
| --- | --- | --- |
| `1234567.jpg` (ou sem extensão) | miniatura de uma foto/vídeo; o número é o ID no banco de mídia | mostra direto |
| `.thumbdata3--…`, `.thumbdata4--…` | Android 4 a 9: centenas de JPEGs empilhados em slots de tamanho fixo | recorta cada JPEG de dentro |
| `.thumbindex…`, `.nomedia` | índice / marcador para a galeria ignorar a pasta | lista como "sem imagem" |

Quando uma foto é apagada, o slot dela no `.thumbdata` normalmente não é limpo. Por isso aparecem
miniaturas de fotos que já não estão na galeria. No Android 10+ o sistema passou a guardar
miniaturas em outro lugar, então a pasta pode estar vazia ou nem existir.

O tipo é decidido pelos bytes do arquivo, não pelo nome. A extração não procura só por
`FFD8…FFD9`: segue os segmentos do JPEG pelo tamanho declarado (assim o JPEG de dentro do EXIF não
corta a imagem ao meio) e nos dados comprimidos pula `FF00` e os marcadores RST. Slot sobrescrito
pela metade vira imagem parcial em vez de sumir.

Pastas lidas: `DCIM/.thumbnails` e `Pictures/.thumbnails`, na memória interna e no cartão SD.

## Funções

- Grade agrupada (soltas / cada `.thumbdata`), toque no cabeçalho recolhe o grupo
- Tela cheia com arrastar para os lados; mostra arquivo, posição em bytes, tamanho e dimensões
- Salvar uma ou todas em `Imagens/Explorador Thumbnails` (aparecem na galeria) e compartilhar
- Só lê: nada é apagado nem enviado para fora do celular

## Build

Kotlin + Views (sem Compose), AGP 8.7.3, Gradle 8.14.3, minSdk 26 (Android 8), targetSdk 34.
`./gradlew assembleRelease`. A chave `app/thumbs.keystore` fica no repo de propósito (uso pessoal),
para que cada APK novo instale por cima do anterior.
