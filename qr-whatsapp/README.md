# QR Zap

App Android mínimo: abre direto na câmera, lê o QR code e já abre o
compartilhamento do WhatsApp com o conteúdo (o link).

- Câmera traseira via CameraX, leitura com ML Kit (modelo embutido, offline).
- Só QR code; ao achar, vibra e chama o WhatsApp (ou WhatsApp Business).
  Sem WhatsApp, abre o compartilhamento padrão do Android.
- Ao voltar do WhatsApp, já está pronto para o próximo. O mesmo código só é
  lido de novo depois de sair do quadro (evita reenviar em loop).
- Botão de lanterna quando o aparelho tem flash.
- Android 8.0+.

## Instalar

O GitHub Actions compila a cada push nesta pasta
(`.github/workflows/qr-zap.yml`). O APK sai:

- na release **qr-zap** do repositório (`qr-zap.apk`) — dá para baixar pelo celular;
- e como artefato do workflow.

No celular, permitir "instalar apps desconhecidos" para o navegador/arquivos.

O APK é assinado com `app/qrzap.keystore` (chave pessoal, fixa) para que
cada versão nova instale por cima da anterior.

## Compilar localmente

Precisa do Android SDK (`ANDROID_HOME`) e JDK 17+:

    ./gradlew assembleRelease
