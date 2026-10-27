package br.uvr.fitsync.sync

import android.content.Context
import br.uvr.fitsync.Entrada
import br.uvr.fitsync.Esportes
import br.uvr.fitsync.Prefs
import br.uvr.fitsync.Treino
import br.uvr.fitsync.huawei.HuaweiHealth
import br.uvr.fitsync.strava.Strava
import br.uvr.fitsync.strava.StravaErro
import br.uvr.fitsync.strava.Tcx
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Calendar
import java.util.Date
import java.util.Locale
import java.util.concurrent.TimeUnit
import kotlin.math.abs

data class Resumo(val enviados: Int, val jaExistiam: Int, val erros: Int, val mensagem: String)

/**
 * O coração do app: pega os treinos da Huawei que ainda não foram enviados e sobe para o Strava.
 * Um treino só é marcado como sincronizado quando o Strava confirma (ou quando já existe lá).
 */
class Sincronizador(private val ctx: Context) {

    companion object {
        // Tela e WorkManager nunca sincronizam ao mesmo tempo
        private val trava = Mutex()

        // Tolerância para considerar que uma atividade do Strava é o mesmo treino
        private const val TOLERANCIA_S = 120L
    }

    private val prefs = Prefs(ctx)
    private val strava = Strava(prefs)

    suspend fun sincronizar(log: (String) -> Unit = {}): Resumo = trava.withLock {
        if (!prefs.stravaConectado) return Resumo(0, 0, 0, "Conecte o Strava primeiro.")

        val agora = System.currentTimeMillis()
        val inicio = agora - TimeUnit.DAYS.toMillis(prefs.diasAtras.toLong())
        log("Lendo treinos da Huawei dos últimos ${prefs.diasAtras} dia(s)…")

        val treinos = try {
            HuaweiHealth.treinos(ctx, inicio, agora)
        } catch (e: Exception) {
            return Resumo(0, 0, 1, "Erro ao ler a Huawei Health: ${descrever(e)}")
        }
        val feitos = prefs.sincronizados()
        val pendentes = treinos.filter { it.id !in feitos }
        log("${treinos.size} treino(s) na Huawei, ${pendentes.size} pendente(s).")

        var enviados = 0
        var existiam = 0
        var erros = 0
        for (t in pendentes) {
            val titulo = titulo(t)
            try {
                val existente = withContext(Dispatchers.IO) { procurarNoStrava(t) }
                if (existente != null) {
                    prefs.marcarSincronizado(t.id)
                    prefs.registrar(Entrada(t.id, titulo, t.inicio, "existia", existente, "Já estava no Strava"))
                    log("= $titulo já estava no Strava")
                    existiam++
                    continue
                }
                log("↑ Enviando $titulo…")
                val idStrava = enviar(t, titulo)
                prefs.marcarSincronizado(t.id)
                prefs.registrar(Entrada(t.id, titulo, t.inicio, "ok", idStrava, "Enviado"))
                log("✓ $titulo enviado")
                enviados++
            } catch (e: Exception) {
                val msg = descrever(e)
                prefs.registrar(Entrada(t.id, titulo, t.inicio, "erro", 0, msg))
                log("✗ $titulo: $msg")
                erros++
                // Sem acesso ou sem cota, não adianta tentar os outros agora
                if (e is StravaErro && (e.codigo == 401 || e.codigo == 429)) break
            }
        }
        prefs.ultimaSync = System.currentTimeMillis()

        val msg = when {
            pendentes.isEmpty() -> "Tudo em dia. Nenhum treino novo."
            else -> "Enviados: $enviados · já existiam: $existiam · erros: $erros"
        }
        Resumo(enviados, existiam, erros, msg)
    }

    /** Id da atividade do Strava que começa no mesmo horário, se houver. */
    private fun procurarNoStrava(t: Treino): Long? {
        val ini = t.inicio / 1000
        val lista = strava.atividadesEntre(ini - TOLERANCIA_S - 1, ini + TOLERANCIA_S + 1)
        val f = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US).apply {
            timeZone = java.util.TimeZone.getTimeZone("UTC")
        }
        for (i in 0 until lista.length()) {
            val a = lista.getJSONObject(i)
            val inicioStrava = f.parse(a.getString("start_date"))?.time?.div(1000) ?: continue
            if (abs(inicioStrava - ini) <= TOLERANCIA_S) return a.getLong("id")
        }
        return null
    }

    private suspend fun enviar(t: Treino, titulo: String): Long {
        val esporte = Esportes.de(t.tipo)
        val amostras = HuaweiHealth.amostras(ctx, t)

        return withContext(Dispatchers.IO) {
            if (amostras.vazia) {
                val local = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss", Locale.US).format(Date(t.inicio))
                return@withContext strava.criarManual(
                    titulo, esporte.sportType, local, (t.fim - t.inicio) / 1000, t.distancia, esporte.indoor
                )
            }

            val tcx = Tcx.gerar(t, esporte, amostras).toByteArray(Charsets.UTF_8)
            val externo = "huawei-${t.id}"
            val upload = strava.enviarArquivo(tcx, "$externo.tcx", "tcx", titulo, externo, esporte.indoor)

            // O Strava processa em segundo plano; costuma levar poucos segundos
            var status = strava.statusUpload(upload)
            var tentativas = 0
            while (!status.pronto && tentativas < 40) {
                delay(3000)
                status = strava.statusUpload(upload)
                tentativas++
            }
            status.erro?.let { erro ->
                // "duplicate of activity 123": o Strava já tem esse arquivo
                Regex("""activities/(\d+)|activity (\d+)""").find(erro)?.let { m ->
                    val id = m.groupValues.drop(1).firstOrNull { it.isNotEmpty() }?.toLongOrNull()
                    if (id != null) return@withContext id
                }
                throw StravaErro(erro.replace(Regex("<[^>]+>"), ""))
            }
            if (!status.pronto) throw StravaErro("O Strava ainda está processando; tento de novo na próxima.")

            // O TCX só sabe Running/Biking/Other; o tipo certo (musculação, trilha…) vai aqui
            try {
                strava.ajustarAtividade(status.atividade, esporte.sportType, titulo)
            } catch (e: Exception) {
                android.util.Log.w("FitSync", "não ajustou o tipo", e)
            }
            status.atividade
        }
    }

    /** "Corrida matinal", "Pedal vespertino"… no estilo dos nomes automáticos do Strava. */
    private fun titulo(t: Treino): String {
        val e = Esportes.de(t.tipo)
        val hora = Calendar.getInstance().apply { timeInMillis = t.inicio }.get(Calendar.HOUR_OF_DAY)
        val feminino = e.nome.substringBefore(' ') in setOf(
            "Corrida", "Caminhada", "Trilha", "Natação", "Musculação", "Calistenia", "Escada",
            "Escalada", "Dança", "Patinação",
        )
        val fim = if (feminino) "a" else "o"
        val periodo = when (hora) {
            in 5..11 -> "matinal"
            in 12..17 -> "vespertin$fim"
            else -> "noturn$fim"
        }
        return "${e.nome} $periodo"
    }

    private fun descrever(e: Exception): String =
        e.message?.takeIf { it.isNotBlank() } ?: e.javaClass.simpleName
}
