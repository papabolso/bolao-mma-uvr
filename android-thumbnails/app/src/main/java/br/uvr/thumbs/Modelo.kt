package br.uvr.thumbs

import java.io.File
import java.util.Locale

enum class Formato(val ext: String, val mime: String) {
    JPEG("jpg", "image/jpeg"),
    PNG("png", "image/png"),
    GIF("gif", "image/gif"),
    WEBP("webp", "image/webp"),
}

/**
 * Uma miniatura. Pode ser um arquivo inteiro (miniatura "solta", ex.: 1234567.jpg) ou um trecho
 * de um arquivo-contêiner (.thumbdata3, .thumbdata4…), onde o Android antigo empilhava centenas
 * de JPEGs um atrás do outro.
 */
data class Miniatura(
    val arquivo: File,
    val inicio: Long,
    val tamanho: Long,
    val formato: Formato,
    val embutida: Boolean,
    val indice: Int, // posição dentro do contêiner (1..n); 0 para as soltas
    val modificado: Long,
) {
    val chave: String get() = "${arquivo.absolutePath}@$inicio"

    fun nomeExportacao(): String {
        if (embutida) {
            return "${arquivo.name.trimStart('.')}_${"%05d".format(Locale.ROOT, indice)}.${formato.ext}"
        }
        val nome = arquivo.name.trimStart('.')
        return if (nome.substringAfterLast('.', "").lowercase(Locale.ROOT) in EXTENSOES) nome
        else "$nome.${formato.ext}"
    }

    private companion object {
        val EXTENSOES = setOf("jpg", "jpeg", "png", "gif", "webp")
    }
}

/** Um grupo da grade: as soltas de uma pasta, ou tudo que saiu de um .thumbdata. */
data class Secao(val titulo: String, val detalhe: String, val itens: List<Miniatura>)

data class Resultado(
    val secoes: List<Secao>,
    val verificadas: List<File>,
    val semImagem: List<File>,
) {
    val todas: List<Miniatura> = secoes.flatMap { it.itens }
}

/** Guarda a última varredura para a tela de visualização (que abre por cima da grade). */
object Repositorio {
    @Volatile
    var resultado: Resultado? = null
}

fun fmtBytes(n: Long): String = when {
    n < 1024 -> "$n B"
    n < 1024L * 1024 -> String.format(Locale.getDefault(), "%.1f KB", n / 1024.0)
    n < 1024L * 1024 * 1024 -> String.format(Locale.getDefault(), "%.1f MB", n / (1024.0 * 1024))
    else -> String.format(Locale.getDefault(), "%.2f GB", n / (1024.0 * 1024 * 1024))
}
