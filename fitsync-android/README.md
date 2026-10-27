# FitSync — Huawei Watch Fit 5 → Strava

App Android que faz o mesmo que o Health Sync nessa parte: pega os treinos do relógio que ainda
não foram para o Strava e sobe eles com GPS, frequência cardíaca, velocidade, cadência e potência.

## Como funciona

```
Watch Fit 5 ──Bluetooth──> app Huawei Health ──Health Kit (HMS)──> FitSync ──API──> Strava
```

1. Lê os treinos (`ActivityRecord`) da Huawei Health Kit dos últimos N dias (padrão: 3).
2. Pula os que já foram enviados (o app guarda o ID de cada treino da Huawei).
3. Antes de enviar, procura no Strava uma atividade que comece no mesmo horário (±2 min). Se
   achar, só marca como feito (assim não duplica treino que outro app já mandou).
4. Monta um arquivo **TCX** com um ponto por segundo e envia em `/uploads`. Depois ajusta o
   tipo certo (`sport_type`: musculação, trilha, HIIT…) e o nome ("Corrida matinal").
5. Treino sem nenhuma amostra vira atividade manual (duração + distância).
6. Roda sozinho a cada hora (WorkManager) e avisa por notificação quando subir algo.

## Configuração (uma vez só)

### 1. Huawei (AppGallery Connect)

É a parte chata, e é por isso que o Health Sync cobra: a Huawei só libera os dados de saúde para
apps cadastrados.

1. Entre em <https://developer.huawei.com/consumer/en/console> com o seu Huawei ID (o mesmo
   do app Huawei Health) e conclua o cadastro de desenvolvedor (pessoa física serve).
2. **AppGallery Connect → Meus projetos → Adicionar projeto**, depois **Adicionar app**:
   - Plataforma Android, nome do pacote **`br.uvr.fitsync`**.
3. Em **Informações do app**, cole a **impressão SHA-256** da keystore (está no arquivo
   `fitsync-segredos.txt` que o Claude gerou). Sem ela, o login da Huawei falha.
4. Anote o **App ID** (número) que aparece na mesma tela.
5. No console: **HMS Core → Health Kit → Solicitar / Apply**. Escolha o app e marque leitura
   (**read**) de:
   - Registros de atividade (*activity records*)
   - Atividade, frequência cardíaca, localização (*location*), velocidade, passos,
     distância e calorias
6. Enquanto a Huawei analisa ou se ela não aprovar a verificação completa, o app costuma
   funcionar em modo de teste para a sua própria conta. Se der erro de permissão, confira se o
   seu Huawei ID está como usuário de teste na página do Health Kit.

### 2. Strava

1. Abra <https://www.strava.com/settings/api> e crie um app (qualquer nome/site).
2. **Authorization Callback Domain:** `localhost`
3. Anote o **Client ID** e o **Client Secret**. Eles são digitados no próprio app, não vão para
   o GitHub.

### 3. GitHub (para compilar o APK)

Em **Settings → Secrets and variables → Actions**:

| Tipo | Nome | Valor |
| --- | --- | --- |
| Secret | `FITSYNC_KEYSTORE_BASE64` | do `fitsync-segredos.txt` |
| Secret | `FITSYNC_KEYSTORE_PASSWORD` | do `fitsync-segredos.txt` |
| Variable | `HMS_APP_ID` | App ID do passo 1.4 |

Depois: **Actions → FitSync APK → Run workflow**. Quando terminar, o APK está em
**Artifacts** no fim da página da execução (vem dentro de um .zip).

> A keystore precisa ser sempre a mesma: a Huawei confere a assinatura do APK pela impressão
> SHA-256. Se trocar a keystore, cadastre a impressão nova no AppGallery Connect.

### 4. No celular

1. Precisa ter o **HMS Core** (já vem em celular Huawei; em outros, instale pela AppGallery) e o
   **Huawei Health** com o relógio pareado.
2. Instale o APK (permitir "instalar apps desconhecidos").
3. No FitSync: **Conectar Huawei** → login e permissões.
4. Preencha Client ID / Secret → **Conectar Strava** → autorizar (deixe marcado o envio de
   atividades).
5. **Sincronizar agora**. Daí em diante ele roda sozinho a cada hora.

Dica: em alguns celulares é preciso tirar o FitSync da economia de bateria para o automático
rodar certinho.

## Compilar no computador

```
cd fitsync-android
HMS_APP_ID=123456 ./gradlew assembleRelease
```

Sem `release.jks` + `FITSYNC_KEYSTORE_PASSWORD`, o APK sai com a chave de debug (instala, mas a
Huawei recusa o login até cadastrar a impressão dessa chave).

## Arquivos

| Arquivo | O que faz |
| --- | --- |
| `huawei/HuaweiHealth.kt` | autorização e leitura dos treinos e amostras no Health Kit |
| `strava/Strava.kt` | OAuth, upload, consulta e ajuste de atividade |
| `strava/Tcx.kt` | gera o TCX (GPS, FC, velocidade, cadência, potência, altitude) |
| `sync/Sincronizador.kt` | decide o que está pendente, evita duplicata, registra histórico |
| `sync/Agendamento.kt` | WorkManager de hora em hora + notificação |
| `Modelo.kt` | tipos de treino da Huawei → `sport_type` do Strava |
| `MainActivity.kt` | tela (Compose) |
