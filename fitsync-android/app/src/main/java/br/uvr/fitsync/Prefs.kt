package br.uvr.fitsync

import android.content.Context
import org.json.JSONArray
import org.json.JSONObject

/** Uma linha do histórico mostrado na tela. */
data class Entrada(
    val id: String,
    val titulo: String,
    val inicio: Long,
    val status: String,   // "ok", "existia", "erro"
    val stravaId: Long,
    val msg: String,
)

/** Tudo que o app guarda fica aqui (SharedPreferences). */
class Prefs(ctx: Context) {
    private val sp = ctx.getSharedPreferences("fitsync", Context.MODE_PRIVATE)

    var clientId: String
        get() = sp.getString("client_id", "") ?: ""
        set(v) = sp.edit().putString("client_id", v.trim()).apply()

    var clientSecret: String
        get() = sp.getString("client_secret", "") ?: ""
        set(v) = sp.edit().putString("client_secret", v.trim()).apply()

    var accessToken: String
        get() = sp.getString("access_token", "") ?: ""
        set(v) = sp.edit().putString("access_token", v).apply()

    var refreshToken: String
        get() = sp.getString("refresh_token", "") ?: ""
        set(v) = sp.edit().putString("refresh_token", v).apply()

    /** epoch em segundos, como o Strava devolve */
    var expiraEm: Long
        get() = sp.getLong("expires_at", 0)
        set(v) = sp.edit().putLong("expires_at", v).apply()

    var atleta: String
        get() = sp.getString("atleta", "") ?: ""
        set(v) = sp.edit().putString("atleta", v).apply()

    val stravaConectado: Boolean
        get() = refreshToken.isNotEmpty()

    /** Quantos dias para trás procurar treinos não sincronizados. */
    var diasAtras: Int
        get() = sp.getInt("dias_atras", 3)
        set(v) = sp.edit().putInt("dias_atras", v.coerceIn(1, 365)).apply()

    var autoSync: Boolean
        get() = sp.getBoolean("auto_sync", true)
        set(v) = sp.edit().putBoolean("auto_sync", v).apply()

    var ultimaSync: Long
        get() = sp.getLong("ultima_sync", 0)
        set(v) = sp.edit().putLong("ultima_sync", v).apply()

    fun sairStrava() {
        sp.edit().remove("access_token").remove("refresh_token").remove("expires_at").remove("atleta").apply()
    }

    // --- treinos já enviados (id da Huawei) ---

    fun sincronizados(): Set<String> = sp.getStringSet("sincronizados", emptySet()) ?: emptySet()

    fun marcarSincronizado(id: String) {
        sp.edit().putStringSet("sincronizados", sincronizados() + id).apply()
    }

    fun esquecer(id: String) {
        sp.edit().putStringSet("sincronizados", sincronizados() - id).apply()
    }

    // --- histórico ---

    fun historico(): List<Entrada> {
        val arr = JSONArray(sp.getString("historico", "[]"))
        return (0 until arr.length()).map { i ->
            val o = arr.getJSONObject(i)
            Entrada(
                o.getString("id"), o.optString("titulo"), o.optLong("inicio"),
                o.optString("status"), o.optLong("strava"), o.optString("msg"),
            )
        }
    }

    /** Guarda a entrada no topo; se o treino já estava na lista, substitui. */
    fun registrar(e: Entrada) {
        val lista = listOf(e) + historico().filter { it.id != e.id }
        val arr = JSONArray()
        lista.take(60).forEach {
            arr.put(
                JSONObject()
                    .put("id", it.id).put("titulo", it.titulo).put("inicio", it.inicio)
                    .put("status", it.status).put("strava", it.stravaId).put("msg", it.msg)
            )
        }
        sp.edit().putString("historico", arr.toString()).apply()
    }
}
