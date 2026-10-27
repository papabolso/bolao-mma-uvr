package br.uvr.fitsync

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.safeDrawingPadding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.lifecycleScope
import br.uvr.fitsync.huawei.HuaweiHealth
import br.uvr.fitsync.strava.Strava
import br.uvr.fitsync.sync.Agendamento
import br.uvr.fitsync.sync.Sincronizador
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

private val LARANJA = Color(0xFFFC4C02)  // laranja do Strava

class MainActivity : ComponentActivity() {

    private lateinit var prefs: Prefs

    private var huaweiOk by mutableStateOf(false)
    private var atleta by mutableStateOf("")
    private var rodando by mutableStateOf(false)
    private var linhas by mutableStateOf(listOf<String>())
    private var historico by mutableStateOf(listOf<Entrada>())

    private val autorizarHuawei =
        registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { r ->
            val (ok, msg) = HuaweiHealth.resultadoAutorizacao(this, r.data)
            huaweiOk = ok
            log(if (ok) "Huawei Health conectada." else "Huawei não autorizou: $msg")
        }

    private val pedirNotificacao =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) {}

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        prefs = Prefs(this)
        atleta = prefs.atleta
        historico = prefs.historico()
        tratarRetornoStrava(intent)

        if (Build.VERSION.SDK_INT >= 33) pedirNotificacao.launch(Manifest.permission.POST_NOTIFICATIONS)
        if (prefs.stravaConectado) Agendamento.aplicar(this, prefs.autoSync)

        lifecycleScope.launch { huaweiOk = HuaweiHealth.autorizado(this@MainActivity) }

        setContent {
            MaterialTheme(colorScheme = darkColorScheme(primary = LARANJA, onPrimary = Color.White)) {
                Surface(Modifier.fillMaxSize()) { Tela() }
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        tratarRetornoStrava(intent)
    }

    /** O navegador volta para fitsync://localhost?code=... depois do login no Strava. */
    private fun tratarRetornoStrava(intent: Intent?) {
        if (intent == null) return
        val uri = intent.data ?: return
        if (uri.scheme != "fitsync") return
        intent.data = null
        uri.getQueryParameter("error")?.let {
            log("Strava: login cancelado ($it)")
            return
        }
        val code = uri.getQueryParameter("code") ?: return
        val escopo = uri.getQueryParameter("scope") ?: ""
        if (!escopo.contains("activity:write")) {
            log("Strava: marque a permissão de enviar atividades e conecte de novo.")
            return
        }
        lifecycleScope.launch {
            try {
                withContext(Dispatchers.IO) { Strava(prefs).trocarCodigo(code) }
                atleta = prefs.atleta.ifEmpty { "conectado" }
                log("Strava conectado: $atleta")
                Agendamento.aplicar(this@MainActivity, prefs.autoSync)
            } catch (e: Exception) {
                log("Erro ao conectar o Strava: ${e.message}")
            }
        }
    }

    private fun log(s: String) {
        val hora = SimpleDateFormat("HH:mm:ss", Locale.getDefault()).format(Date())
        linhas = (listOf("$hora  $s") + linhas).take(80)
    }

    private fun sincronizarAgora() {
        if (rodando) return
        rodando = true
        lifecycleScope.launch {
            try {
                val r = Sincronizador(applicationContext).sincronizar { msg ->
                    lifecycleScope.launch { log(msg) }
                }
                log(r.mensagem)
            } catch (e: Exception) {
                log("Erro: ${e.message}")
            } finally {
                historico = prefs.historico()
                rodando = false
            }
        }
    }

    private fun conectarStrava() {
        if (prefs.clientId.isEmpty() || prefs.clientSecret.isEmpty()) {
            log("Preencha Client ID e Client Secret do seu app do Strava.")
            return
        }
        try {
            startActivity(Intent(Intent.ACTION_VIEW, Strava(prefs).urlLogin()))
        } catch (e: ActivityNotFoundException) {
            log("Nenhum navegador encontrado.")
        }
    }

    @Composable
    private fun Tela() {
        Column(
            Modifier
                .fillMaxSize()
                .safeDrawingPadding()
                .verticalScroll(rememberScrollState())
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(14.dp),
        ) {
            Text("FitSync", fontSize = 28.sp, fontWeight = FontWeight.Bold, color = LARANJA)
            Text("Huawei Watch Fit 5 → Strava", color = MaterialTheme.colorScheme.onSurfaceVariant)

            Bloco("1. Huawei Health", if (huaweiOk) "Conectado" else "Não conectado", huaweiOk) {
                Text(
                    "Faz login com o seu Huawei ID e libera o acesso aos treinos. " +
                        "Precisa do HMS Core e do app Huawei Health com o relógio pareado.",
                    fontSize = 13.sp,
                )
                Button(onClick = {
                    try {
                        autorizarHuawei.launch(HuaweiHealth.intentAutorizacao(this@MainActivity))
                    } catch (e: Exception) {
                        log("Não abriu a autorização da Huawei: ${e.message}. O HMS Core está instalado?")
                    }
                }) { Text(if (huaweiOk) "Autorizar de novo" else "Conectar Huawei") }
            }

            Bloco("2. Strava", atleta.ifEmpty { "Não conectado" }, atleta.isNotEmpty()) {
                var id by remember { mutableStateOf(prefs.clientId) }
                var segredo by remember { mutableStateOf(prefs.clientSecret) }
                if (atleta.isEmpty()) {
                    OutlinedTextField(
                        value = id, onValueChange = { id = it; prefs.clientId = it },
                        label = { Text("Client ID") }, singleLine = true,
                        keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = segredo, onValueChange = { segredo = it; prefs.clientSecret = it },
                        label = { Text("Client Secret") }, singleLine = true,
                        visualTransformation = PasswordVisualTransformation(),
                        modifier = Modifier.fillMaxWidth(),
                    )
                    Text(
                        "Crie em strava.com/settings/api com o domínio de callback \"localhost\".",
                        fontSize = 12.sp,
                    )
                    Button(onClick = { conectarStrava() }) { Text("Conectar Strava") }
                } else {
                    OutlinedButton(onClick = {
                        prefs.sairStrava()
                        atleta = ""
                        Agendamento.aplicar(this@MainActivity, false)
                        log("Strava desconectado.")
                    }) { Text("Desconectar") }
                }
            }

            Bloco("3. Sincronização", ultimaSync(), null) {
                var dias by remember { mutableStateOf(prefs.diasAtras.toString()) }
                var auto by remember { mutableStateOf(prefs.autoSync) }
                OutlinedTextField(
                    value = dias,
                    onValueChange = { v ->
                        dias = v.filter { it.isDigit() }.take(3)
                        dias.toIntOrNull()?.let { prefs.diasAtras = it }
                    },
                    label = { Text("Procurar treinos dos últimos N dias") }, singleLine = true,
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Number),
                    modifier = Modifier.fillMaxWidth(),
                )
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text("Automática (a cada hora)", Modifier.weight(1f))
                    Switch(checked = auto, onCheckedChange = {
                        auto = it
                        prefs.autoSync = it
                        Agendamento.aplicar(this@MainActivity, it && prefs.stravaConectado)
                    })
                }
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Button(
                        onClick = { sincronizarAgora() },
                        enabled = !rodando && atleta.isNotEmpty(),
                    ) { Text("Sincronizar agora") }
                    if (rodando) {
                        Spacer(Modifier.width(12.dp))
                        CircularProgressIndicator(Modifier.padding(4.dp))
                    }
                }
            }

            if (historico.isNotEmpty()) {
                Bloco("Treinos", "${historico.size} no histórico", null) {
                    historico.forEach { Linha(it) }
                }
            }

            if (linhas.isNotEmpty()) {
                Bloco("Registro", "", null) {
                    linhas.forEach { Text(it, fontSize = 12.sp, fontFamily = FontFamily.Monospace) }
                }
            }
        }
    }

    @Composable
    private fun Linha(e: Entrada) {
        val f = SimpleDateFormat("dd/MM HH:mm", Locale.getDefault())
        val (icone, cor) = when (e.status) {
            "ok" -> "✓" to Color(0xFF4CAF50)
            "existia" -> "=" to Color(0xFF9E9E9E)
            else -> "✗" to Color(0xFFE57373)
        }
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(icone, color = cor, fontWeight = FontWeight.Bold, modifier = Modifier.width(22.dp))
            Column(Modifier.weight(1f)) {
                Text("${e.titulo} · ${f.format(Date(e.inicio))}", fontSize = 14.sp)
                Text(e.msg, fontSize = 12.sp, color = MaterialTheme.colorScheme.onSurfaceVariant)
            }
            if (e.stravaId > 0) {
                TextButton(onClick = {
                    startActivity(
                        Intent(Intent.ACTION_VIEW, Uri.parse("https://www.strava.com/activities/${e.stravaId}"))
                    )
                }) { Text("Abrir") }
            }
            if (e.status != "erro") {
                // Para quando o treino foi apagado no Strava e precisa subir de novo
                TextButton(onClick = {
                    prefs.esquecer(e.id)
                    log("${e.titulo} vai ser enviado de novo na próxima sincronização.")
                }) { Text("Reenviar") }
            }
        }
    }

    private fun ultimaSync(): String {
        val t = prefs.ultimaSync
        if (t == 0L) return "Nunca sincronizado"
        return "Última: " + SimpleDateFormat("dd/MM HH:mm", Locale.getDefault()).format(Date(t))
    }

    @Composable
    private fun Bloco(titulo: String, status: String, ok: Boolean?, conteudo: @Composable () -> Unit) {
        Card(Modifier.fillMaxWidth()) {
            Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Text(titulo, fontWeight = FontWeight.Bold, fontSize = 17.sp, modifier = Modifier.weight(1f))
                    Text(
                        status, fontSize = 13.sp,
                        color = when (ok) {
                            true -> Color(0xFF4CAF50)
                            false -> Color(0xFFE57373)
                            null -> MaterialTheme.colorScheme.onSurfaceVariant
                        },
                    )
                }
                conteudo()
            }
        }
    }
}
