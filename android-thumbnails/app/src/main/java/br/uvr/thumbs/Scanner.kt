package br.uvr.thumbs

import android.os.Environment
import java.io.File
import java.io.FileInputStream
import java.io.RandomAccessFile
import kotlin.coroutines.cancellation.CancellationException

/**
 * Varre as pastas .thumbnails.
 *
 * O que costuma ter lá dentro (varia com a versão do Android e o fabricante):
 * - miniaturas soltas (`1234567.jpg`, às vezes sem extensão), uma por foto/vídeo da galeria;
 * - `.thumbdata3--1967290299`, `.thumbdata4--…`: Android 4 a 9 empilhava todas as miniaturas
 *   num arquivo só, cada uma num "slot" de tamanho fixo. Quando a foto é apagada o slot
 *   não é limpo, então dá para ver miniaturas de fotos que já não existem;
 * - `.thumbindex…` e `.nomedia`: índices sem imagem.
 *
 * Por isso o tipo é decidido pelo conteúdo (bytes mágicos), não pelo nome, e todo arquivo que
 * não é imagem é vasculhado atrás de JPEGs embutidos.
 */
object Scanner {
    private const val JPEG_MIN = 200L
    private const val JPEG_MAX = 32L * 1024 * 1024

    // Android 4 a 9 guardava tudo em DCIM/.thumbnails; do 10 em diante o sistema usa
    // Pictures/.thumbnails para fotos e Movies/.thumbnails para vídeos, com o ID da mídia no nome
    private val PASTAS = listOf("DCIM/.thumbnails", "Pictures/.thumbnails", "Movies/.thumbnails")

    private val interno: String get() = Environment.getExternalStorageDirectory().absolutePath

    fun pastasCandidatas(): List<File> {
        val raizes = linkedSetOf(Environment.getExternalStorageDirectory())
        // Cartão SD e pendrives aparecem como /storage/XXXX-XXXX
        File("/storage").listFiles()
            ?.filter { it.isDirectory && it.name != "emulated" && it.name != "self" }
            ?.forEach { raizes += it }
        return raizes.flatMap { PASTAS.map { p -> File(it, p) } }
    }

    fun caminhoCurto(f: File): String {
        val p = f.absolutePath
        return if (p.startsWith(interno)) "Interno" + p.removePrefix(interno) else p
    }

    fun varrer(progresso: (String, Float) -> Unit, cancelado: () -> Boolean): Resultado {
        val secoes = mutableListOf<Secao>()
        val verificadas = mutableListOf<File>()
        val semImagem = mutableListOf<File>()

        for (pasta in pastasCandidatas()) {
            if (!pasta.isDirectory) continue
            verificadas += pasta
            val nomePasta = caminhoCurto(pasta)
            progresso("Listando $nomePasta…", -1f)

            val arquivos = pasta.walkTopDown().filter { it.isFile }.sortedBy { it.name }.toList()
            val soltas = mutableListOf<Miniatura>()
            val conteineres = mutableListOf<File>()
            arquivos.forEachIndexed { i, f ->
                if (i % 50 == 0) {
                    if (cancelado()) throw CancellationException()
                    progresso("Lendo $nomePasta (${i + 1} de ${arquivos.size})", i.toFloat() / arquivos.size)
                }
                val tam = f.length()
                if (tam < 16) {
                    semImagem += f
                    return@forEachIndexed
                }
                val fmt = formatoDoArquivo(f)
                if (fmt != null) soltas += Miniatura(f, 0, tam, fmt, false, 0, f.lastModified())
                else conteineres += f
            }
            if (soltas.isNotEmpty()) {
                secoes += Secao("Miniaturas soltas", nomePasta, soltas.sortedByDescending { it.modificado })
            }

            for (c in conteineres.sortedByDescending { it.length() }) {
                val trechos = try {
                    extrairJpegs(c, { progresso("Extraindo ${c.name}…", it) }, cancelado)
                } catch (e: CancellationException) {
                    throw e
                } catch (e: Exception) {
                    emptyList()
                }
                if (trechos.isEmpty()) {
                    semImagem += c
                    continue
                }
                val mod = c.lastModified()
                val itens = trechos.mapIndexed { i, (ini, tam) ->
                    Miniatura(c, ini, tam, Formato.JPEG, true, i + 1, mod)
                }
                secoes += Secao(c.name, "${caminhoCurto(c.parentFile ?: pasta)} · ${fmtBytes(c.length())}", itens)
            }
        }
        return Resultado(secoes, verificadas, semImagem)
    }

    fun formatoDoArquivo(f: File): Formato? = try {
        val cab = ByteArray(12)
        val n = FileInputStream(f).use { it.read(cab) }
        formatoDosBytes(cab, n)
    } catch (e: Exception) {
        null
    }

    fun formatoDosBytes(b: ByteArray, n: Int): Formato? {
        fun u(i: Int) = b[i].toInt() and 0xFF
        return when {
            n >= 3 && u(0) == 0xFF && u(1) == 0xD8 && u(2) == 0xFF -> Formato.JPEG
            n >= 4 && u(0) == 0x89 && u(1) == 'P'.code && u(2) == 'N'.code && u(3) == 'G'.code -> Formato.PNG
            n >= 4 && u(0) == 'G'.code && u(1) == 'I'.code && u(2) == 'F'.code && u(3) == '8'.code -> Formato.GIF
            n >= 12 && String(b, 0, 4, Charsets.US_ASCII) == "RIFF" &&
                String(b, 8, 4, Charsets.US_ASCII) == "WEBP" -> Formato.WEBP
            else -> null
        }
    }

    /**
     * Acha os JPEGs dentro de um arquivo qualquer. Devolve (início, tamanho) de cada um.
     *
     * Não basta procurar FFD8 e o próximo FFD9: o cabeçalho EXIF pode trazer outro JPEG dentro.
     * Então segue os segmentos pelo tamanho declarado até o SOS e, nos dados comprimidos,
     * pula os bytes FF00 e os marcadores RST até achar o fim (FFD9).
     */
    fun extrairJpegs(f: File, progresso: (Float) -> Unit, cancelado: () -> Boolean): List<Pair<Long, Long>> =
        RandomAccessFile(f, "r").use { raf ->
            val r = Leitor(raf)
            val n = r.tamanho
            val achados = mutableListOf<Pair<Long, Long>>()
            var p = 0L
            var proximoAviso = 0L
            while (p < n - 3) {
                if (p >= proximoAviso) {
                    if (cancelado()) throw CancellationException()
                    progresso(p.toFloat() / n)
                    proximoAviso = p + (1 shl 20)
                }
                p = r.acharFF(p)
                if (p < 0) break
                if (r.byte(p + 1) == 0xD8 && r.byte(p + 2) == 0xFF) {
                    val fim = fimDoJpeg(r, p)
                    if (fim > 0 && fim - p >= JPEG_MIN) {
                        achados += p to (fim - p)
                        p = fim
                        continue
                    }
                }
                p++
            }
            achados
        }

    /** Posição logo depois do fim do JPEG que começa em [soi], ou -1 se não for um JPEG válido. */
    private fun fimDoJpeg(r: Leitor, soi: Long): Long {
        val limite = minOf(r.tamanho, soi + JPEG_MAX)
        var p = soi + 2
        var viuSos = false
        while (p < limite) {
            if (r.byte(p) != 0xFF) return -1
            while (p < limite && r.byte(p) == 0xFF) p++ // bytes de preenchimento
            val m = r.byte(p)
            p++
            when {
                m < 0 -> return -1
                m == 0xD9 -> return if (viuSos) p else -1
                // Outro JPEG começando: este ficou cortado (slot sobrescrito). Aproveita o que tem.
                m == 0xD8 -> return if (viuSos) p - 2 else -1
                m == 0x01 || m in 0xD0..0xD7 -> {}
                m == 0x00 -> return -1
                else -> {
                    val len = r.u16(p)
                    if (len < 2) return -1
                    p += len
                    if (m == 0xDA) {
                        viuSos = true
                        p = fimDaEntropia(r, p, limite)
                        if (p < 0) return -1
                    }
                }
            }
        }
        return -1
    }

    /** Pula os dados comprimidos e devolve a posição do próximo marcador (o FF). */
    private fun fimDaEntropia(r: Leitor, de: Long, limite: Long): Long {
        var p = de
        while (p < limite) {
            p = r.acharFF(p)
            if (p < 0 || p >= limite) return -1
            val prox = r.byte(p + 1)
            when {
                prox < 0 -> return -1
                prox == 0x00 || prox in 0xD0..0xD7 -> p += 2
                prox == 0xFF -> p += 1
                else -> return p
            }
        }
        return -1
    }

    /** Leitura aleatória com buffer de 1 MB: o .thumbdata pode ter centenas de MB. */
    private class Leitor(private val raf: RandomAccessFile) {
        val tamanho = raf.length()
        private val buf = ByteArray(1 shl 20)
        private var bufIni = -1L
        private var bufLen = 0

        private fun carregar(pos: Long): Boolean {
            if (pos < 0 || pos >= tamanho) return false
            if (bufIni >= 0 && pos >= bufIni && pos < bufIni + bufLen) return true
            raf.seek(pos)
            bufLen = raf.read(buf, 0, buf.size).coerceAtLeast(0)
            bufIni = pos
            return bufLen > 0
        }

        fun byte(pos: Long): Int {
            if (!carregar(pos)) return -1
            return buf[(pos - bufIni).toInt()].toInt() and 0xFF
        }

        fun u16(pos: Long): Int {
            val a = byte(pos)
            val b = byte(pos + 1)
            return if (a < 0 || b < 0) -1 else (a shl 8) or b
        }

        fun acharFF(de: Long): Long {
            var p = de
            while (p < tamanho) {
                if (!carregar(p)) return -1
                val ini = (p - bufIni).toInt()
                for (i in ini until bufLen) {
                    if (buf[i] == FF) return bufIni + i
                }
                p = bufIni + bufLen
            }
            return -1
        }

        private companion object {
            const val FF = 0xFF.toByte()
        }
    }
}
