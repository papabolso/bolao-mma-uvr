package br.uvr.thumbs

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.receiveAsFlow
import kotlinx.coroutines.flow.update
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import kotlin.coroutines.cancellation.CancellationException

data class Estado(
    val ocupado: Boolean = false,
    val mensagem: String = "",
    val progresso: Float = -1f, // -1 = sem porcentagem
    val resultado: Resultado? = null,
)

/** Fica vivo ao girar a tela, então a varredura não recomeça do zero. */
class MainViewModel(app: Application) : AndroidViewModel(app) {
    private val _estado = MutableStateFlow(Estado(resultado = Repositorio.resultado))
    val estado: StateFlow<Estado> = _estado.asStateFlow()

    private val _avisos = Channel<String>(Channel.BUFFERED)
    val avisos = _avisos.receiveAsFlow()

    private var tarefa: Job? = null

    fun varrer() {
        if (tarefa?.isActive == true) return
        tarefa = viewModelScope.launch {
            _estado.update { it.copy(ocupado = true, mensagem = "Procurando pastas…", progresso = -1f) }
            val job = coroutineContext[Job]
            try {
                val r = withContext(Dispatchers.IO) {
                    Scanner.varrer(
                        { msg, p -> _estado.update { it.copy(mensagem = msg, progresso = p) } },
                        { job?.isActive != true },
                    )
                }
                Repositorio.resultado = r
                _estado.value = Estado(resultado = r)
            } catch (e: CancellationException) {
                throw e
            } catch (e: Exception) {
                _estado.update { it.copy(ocupado = false, mensagem = "") }
                _avisos.send("Erro na leitura: ${e.message ?: e}")
            }
        }
    }

    fun exportarTudo() {
        val lista = Repositorio.resultado?.todas.orEmpty()
        if (lista.isEmpty() || tarefa?.isActive == true) return
        tarefa = viewModelScope.launch {
            var salvas = 0
            var falhas = 0
            withContext(Dispatchers.IO) {
                lista.forEachIndexed { i, m ->
                    ensureActive()
                    _estado.update {
                        it.copy(ocupado = true, mensagem = "Salvando ${i + 1} de ${lista.size}…", progresso = i.toFloat() / lista.size)
                    }
                    try {
                        Exportador.salvar(getApplication(), m)
                        salvas++
                    } catch (e: Exception) {
                        falhas++
                    }
                }
            }
            _estado.update { it.copy(ocupado = false, mensagem = "", progresso = -1f) }
            _avisos.send(
                "$salvas imagens salvas em Imagens/${Exportador.PASTA}" + if (falhas > 0) " ($falhas falharam)" else ""
            )
        }
    }
}
