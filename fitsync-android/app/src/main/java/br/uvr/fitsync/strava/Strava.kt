package br.uvr.fitsync.strava

import android.net.Uri
import br.uvr.fitsync.Prefs
import okhttp3.FormBody
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONArray
import org.json.JSONObject
import java.io.IOException
import java.util.concurrent.TimeUnit

class StravaErro(msg: String, val codigo: Int = 0) : IOException(msg)

/**
 * API do Strava. Chamadas bloqueantes: rodar em Dispatchers.IO.
 * O app do Strava (client id/secret) é o do próprio usuário, criado em strava.com/settings/api.
 */
class Strava(private val prefs: Prefs) {

    companion object {
        const val REDIRECT = "fitsync://localhost"
        private const val API = "https://www.strava.com/api/v3"
        private val http = OkHttpClient.Builder()
            .connectTimeout(20, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(60, TimeUnit.SECONDS)
            .build()
    }

    fun urlLogin(): Uri = Uri.parse("https://www.strava.com/oauth/mobile/authorize").buildUpon()
        .appendQueryParameter("client_id", prefs.clientId)
        .appendQueryParameter("redirect_uri", REDIRECT)
        .appendQueryParameter("response_type", "code")
        .appendQueryParameter("approval_prompt", "auto")
        .appendQueryParameter("scope", "read,activity:read_all,activity:write")
        .build()

    /** Troca o código da volta do login pelos tokens. */
    fun trocarCodigo(code: String) {
        val o = postarToken(
            FormBody.Builder()
                .add("client_id", prefs.clientId)
                .add("client_secret", prefs.clientSecret)
                .add("code", code)
                .add("grant_type", "authorization_code")
                .build()
        )
        o.optJSONObject("athlete")?.let {
            prefs.atleta = (it.optString("firstname") + " " + it.optString("lastname")).trim()
        }
    }

    private fun token(): String {
        if (!prefs.stravaConectado) throw StravaErro("Strava não conectado")
        if (prefs.expiraEm - 120 < System.currentTimeMillis() / 1000) {
            postarToken(
                FormBody.Builder()
                    .add("client_id", prefs.clientId)
                    .add("client_secret", prefs.clientSecret)
                    .add("refresh_token", prefs.refreshToken)
                    .add("grant_type", "refresh_token")
                    .build()
            )
        }
        return prefs.accessToken
    }

    private fun postarToken(corpo: FormBody): JSONObject {
        val req = Request.Builder().url("https://www.strava.com/oauth/token").post(corpo).build()
        val o = JSONObject(executar(req))
        prefs.accessToken = o.getString("access_token")
        prefs.refreshToken = o.getString("refresh_token")
        prefs.expiraEm = o.getLong("expires_at")
        return o
    }

    private fun executar(req: Request): String {
        http.newCall(req).execute().use { r ->
            val corpo = r.body?.string() ?: ""
            if (!r.isSuccessful) {
                val msg = when (r.code) {
                    401 -> "Strava recusou o acesso (401). Conecte de novo."
                    429 -> "Limite de requisições do Strava atingido (429). Tenta mais tarde."
                    else -> "Strava ${r.code}: ${corpo.take(300)}"
                }
                throw StravaErro(msg, r.code)
            }
            return corpo
        }
    }

    private fun autenticado(url: String) = Request.Builder().url(url)
        .header("Authorization", "Bearer ${token()}")

    /** Atividades que começaram entre [depois] e [antes] (epoch s). */
    fun atividadesEntre(depois: Long, antes: Long): JSONArray {
        val req = autenticado("$API/athlete/activities?after=$depois&before=$antes&per_page=30").get().build()
        return JSONArray(executar(req))
    }

    /** Sobe o arquivo e devolve o id do upload (o processamento é assíncrono). */
    fun enviarArquivo(conteudo: ByteArray, nomeArquivo: String, tipo: String, nome: String, externalId: String,
                      indoor: Boolean): Long {
        val corpo = MultipartBody.Builder().setType(MultipartBody.FORM)
            .addFormDataPart("file", nomeArquivo, conteudo.toRequestBody("application/octet-stream".toMediaType()))
            .addFormDataPart("data_type", tipo)
            .addFormDataPart("name", nome)
            .addFormDataPart("external_id", externalId)
            .addFormDataPart("trainer", if (indoor) "1" else "0")
            .build()
        val req = autenticado("$API/uploads").post(corpo).build()
        return JSONObject(executar(req)).getLong("id")
    }

    data class Upload(val pronto: Boolean, val atividade: Long, val erro: String?)

    fun statusUpload(id: Long): Upload {
        val o = JSONObject(executar(autenticado("$API/uploads/$id").get().build()))
        val erro = if (o.isNull("error")) null else o.getString("error")
        val atividade = if (o.isNull("activity_id")) 0L else o.getLong("activity_id")
        return Upload(atividade != 0L || erro != null, atividade, erro)
    }

    fun ajustarAtividade(id: Long, sportType: String, nome: String) {
        val corpo = FormBody.Builder()
            .add("sport_type", sportType)
            .add("name", nome)
            .build()
        executar(autenticado("$API/activities/$id").put(corpo).build())
    }

    /** Treino sem nenhuma amostra (ex.: musculação sem FC): sobe como atividade manual. */
    fun criarManual(nome: String, sportType: String, inicioLocal: String, segundos: Long,
                    distancia: Double?, indoor: Boolean): Long {
        val b = FormBody.Builder()
            .add("name", nome)
            .add("sport_type", sportType)
            .add("start_date_local", inicioLocal)
            .add("elapsed_time", segundos.toString())
            .add("trainer", if (indoor) "1" else "0")
        distancia?.let { b.add("distance", String.format(java.util.Locale.US, "%.1f", it)) }
        val req = autenticado("$API/activities").post(b.build()).build()
        return JSONObject(executar(req)).getLong("id")
    }
}
