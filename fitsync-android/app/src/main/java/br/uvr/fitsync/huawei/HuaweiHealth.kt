package br.uvr.fitsync.huawei

import android.content.Context
import android.content.Intent
import br.uvr.fitsync.Amostras
import br.uvr.fitsync.Esportes
import br.uvr.fitsync.Ponto
import br.uvr.fitsync.Posicao
import br.uvr.fitsync.Treino
import com.huawei.hmf.tasks.Task
import com.huawei.hms.hihealth.HuaweiHiHealth
import com.huawei.hms.hihealth.data.ActivityRecord
import com.huawei.hms.hihealth.data.DataType
import com.huawei.hms.hihealth.data.Field
import com.huawei.hms.hihealth.data.SamplePoint
import com.huawei.hms.hihealth.data.Value
import com.huawei.hms.hihealth.options.ActivityRecordReadOptions
import kotlinx.coroutines.suspendCancellableCoroutine
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/**
 * Leitura dos treinos pela Huawei Health Kit (o mesmo caminho do Health Sync).
 * O relógio sincroniza com o app Huawei Health, e o Health Kit expõe esses treinos
 * ("activity records") com as amostras de GPS, frequência cardíaca etc.
 */
object HuaweiHealth {

    /** Permissões pedidas ao usuário. Todas precisam estar liberadas no AppGallery Connect. */
    val ESCOPOS = arrayOf(
        "https://www.huawei.com/healthkit/activityrecord.read",
        "https://www.huawei.com/healthkit/activity.read",
        "https://www.huawei.com/healthkit/heartrate.read",
        "https://www.huawei.com/healthkit/location.read",
        "https://www.huawei.com/healthkit/speed.read",
        "https://www.huawei.com/healthkit/step.read",
        "https://www.huawei.com/healthkit/distance.read",
        "https://www.huawei.com/healthkit/calories.read",
    )

    /**
     * Tipos de amostra lidos de cada treino. Resolvidos por nome (reflexão) porque a lista
     * de constantes muda entre versões do SDK; o que não existir é simplesmente pulado.
     */
    private val TIPOS_DETALHE = listOf(
        "DT_INSTANTANEOUS_LOCATION_SAMPLE",
        "DT_INSTANTANEOUS_LOCATION_TRACE",
        "DT_INSTANTANEOUS_HEART_RATE",
        "DT_INSTANTANEOUS_EXERCISE_HEART_RATE",
        "DT_INSTANTANEOUS_SPEED",
        "DT_INSTANTANEOUS_STEPS_RATE",
        "DT_INSTANTANEOUS_BIKING_PEDALING_RATE",
        "DT_INSTANTANEOUS_POWER_SAMPLE",
        "DT_INSTANTANEOUS_ALTITUDE",
    )

    private val SO_FC = listOf("DT_INSTANTANEOUS_HEART_RATE", "DT_INSTANTANEOUS_EXERCISE_HEART_RATE")

    private fun tipo(nome: String): DataType? = try {
        DataType::class.java.getField(nome).get(null) as? DataType
    } catch (e: Exception) {
        null
    }

    // --- autorização ---

    /** Tela da Huawei que faz login com o Huawei ID e pede as permissões. */
    fun intentAutorizacao(ctx: Context): Intent =
        HuaweiHiHealth.getSettingController(ctx).requestAuthorizationIntent(ESCOPOS, true)

    fun resultadoAutorizacao(ctx: Context, data: Intent?): Pair<Boolean, String> {
        val r = HuaweiHiHealth.getSettingController(ctx).parseHealthKitAuthResultFromIntent(data)
            ?: return false to "sem resposta da Huawei"
        return if (r.isSuccess) true to "ok" else false to "código ${r.errorCode}"
    }

    /** true se o app já tem acesso aos dados do app Huawei Health. */
    suspend fun autorizado(ctx: Context): Boolean = try {
        HuaweiHiHealth.getSettingController(ctx).getHealthAppAuthorization().aguardar() == true
    } catch (e: Exception) {
        false
    }

    // --- leitura ---

    /** Lista os treinos (só o resumo) entre [inicio] e [fim], em janelas de 7 dias. */
    suspend fun treinos(ctx: Context, inicio: Long, fim: Long): List<Treino> {
        val ctl = HuaweiHiHealth.getActivityRecordsController(ctx)
        val semana = TimeUnit.DAYS.toMillis(7)
        val saida = LinkedHashMap<String, Treino>()
        var de = inicio
        while (de < fim) {
            val ate = minOf(de + semana, fim)
            val opcoes = ActivityRecordReadOptions.Builder()
                .setTimeInterval(de, ate, TimeUnit.MILLISECONDS)
                .readActivityRecordsFromAllApps()
                .build()
            val resposta = ctl.getActivityRecord(opcoes).aguardar()
            for (r in resposta.activityRecords) {
                val t = resumo(r) ?: continue
                saida[t.id] = t
            }
            de = ate
        }
        return saida.values.sortedBy { it.inicio }
    }

    /**
     * Lê as amostras de um treino. Se a Huawei recusar algum tipo (permissão não aprovada),
     * tenta de novo só com frequência cardíaca e, por fim, sem amostra nenhuma.
     */
    suspend fun amostras(ctx: Context, t: Treino): Amostras {
        var ultimoErro: Exception? = null
        for (nomes in listOf(TIPOS_DETALHE, SO_FC)) {
            try {
                return lerAmostras(ctx, t, nomes)
            } catch (e: Exception) {
                ultimoErro = e
            }
        }
        // Sem amostras o treino ainda sobe como atividade manual (duração, distância).
        android.util.Log.w("FitSync", "sem amostras para ${t.id}", ultimoErro)
        return Amostras()
    }

    private suspend fun lerAmostras(ctx: Context, t: Treino, nomes: List<String>): Amostras {
        val ctl = HuaweiHiHealth.getActivityRecordsController(ctx)
        val b = ActivityRecordReadOptions.Builder()
            .setTimeInterval(t.inicio, t.fim, TimeUnit.MILLISECONDS)
            .setActivityRecordId(t.id)
            .readActivityRecordsFromAllApps()
        nomes.mapNotNull { tipo(it) }.distinct().forEach { b.read(it) }
        val resposta = ctl.getActivityRecord(b.build()).aguardar()
        val registro = resposta.activityRecords.firstOrNull { it.id == t.id }
            ?: return Amostras()

        val pos = ArrayList<Posicao>()
        val fc = ArrayList<Ponto>()
        val vel = ArrayList<Ponto>()
        val passos = ArrayList<Ponto>()
        val rpm = ArrayList<Ponto>()
        val pot = ArrayList<Ponto>()
        val alt = ArrayList<Ponto>()

        for (set in resposta.getSampleSet(registro)) {
            for (p in set.samplePoints) {
                val tempo = tempoDe(p)
                val v = valores(p)
                val lat = v["latitude"]
                val lon = v["longitude"]
                when {
                    lat != null && lon != null -> {
                        if (lat in -90.0..90.0 && lon in -180.0..180.0 && !(lat == 0.0 && lon == 0.0)) {
                            pos += Posicao(tempo, lat, lon, v["altitude"])
                        }
                    }
                    v["bpm"] != null -> v["bpm"]!!.let { if (it in 25.0..250.0) fc += Ponto(tempo, it) }
                    v["speed"] != null -> vel += Ponto(tempo, v["speed"]!!)
                    v["step_rate"] != null -> passos += Ponto(tempo, v["step_rate"]!!)
                    v["rpm"] != null -> rpm += Ponto(tempo, v["rpm"]!!)
                    v["power"] != null -> pot += Ponto(tempo, v["power"]!!)
                    v["altitude"] != null -> alt += Ponto(tempo, v["altitude"]!!)
                }
            }
        }

        fun List<Ponto>.ord() = sortedBy { it.t }.distinctBy { it.t }
        return Amostras(
            posicoes = pos.sortedBy { it.t }.distinctBy { it.t },
            fc = fc.ord(), velocidade = vel.ord(), passos = passos.ord(),
            rpm = rpm.ord(), potencia = pot.ord(), altitude = alt.ord(),
        )
    }

    private fun resumo(r: ActivityRecord): Treino? {
        val id = r.id ?: return null
        val tipo = (r.activityType ?: "unknown").lowercase()
        if (tipo in Esportes.ignorados) return null
        val ini = r.getStartTime(TimeUnit.MILLISECONDS)
        val fim = r.getEndTime(TimeUnit.MILLISECONDS)
        if (ini <= 0 || fim <= ini) return null  // treino ainda em andamento

        var dist: Double? = null
        var cal: Double? = null
        r.activitySummary?.dataSummary?.forEach { p ->
            for ((campo, valor) in valores(p)) {
                when {
                    campo == "distance" -> dist = valor
                    campo.startsWith("calories") -> cal = valor
                }
            }
        }
        return Treino(id, tipo, ini, fim, dist, cal, r.packageName)
    }

    private fun tempoDe(p: SamplePoint): Long {
        val s = p.getSamplingTime(TimeUnit.MILLISECONDS)
        return if (s > 0) s else p.getStartTime(TimeUnit.MILLISECONDS)
    }

    /** Campos numéricos de uma amostra, pelo nome do campo ("bpm", "latitude"...). */
    private fun valores(p: SamplePoint): Map<String, Double> {
        val saida = HashMap<String, Double>()
        for ((nome, valor) in p.fieldValues) {
            numero(valor)?.let { saida[nome.lowercase()] = it }
        }
        return saida
    }

    private fun numero(v: Value?): Double? {
        if (v == null) return null
        return try {
            when (v.format) {
                Field.FORMAT_INT32 -> v.asIntValue().toDouble()
                Field.FORMAT_FLOAT -> v.asDoubleValue()
                Field.FORMAT_LONG -> v.asLongValue().toDouble()
                else -> null
            }
        } catch (e: Exception) {
            null
        }
    }
}

/** Espera uma Task da Huawei dentro de uma corrotina. */
suspend fun <T> Task<T>.aguardar(): T = suspendCancellableCoroutine { c ->
    addOnSuccessListener { c.resume(it) }
    addOnFailureListener { c.resumeWithException(it) }
}
