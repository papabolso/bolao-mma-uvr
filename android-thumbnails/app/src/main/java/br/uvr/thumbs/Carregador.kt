package br.uvr.thumbs

import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.util.LruCache
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.withContext
import java.io.RandomAccessFile
import java.util.concurrent.Executors

/** Decodifica miniaturas fora da thread principal e guarda as recentes na memória. */
object Carregador {
    private const val MAX_BYTES = 64L * 1024 * 1024

    private val cache = object : LruCache<String, Bitmap>((Runtime.getRuntime().maxMemory() / 8 / 1024).toInt()) {
        override fun sizeOf(key: String, value: Bitmap) = value.byteCount / 1024
    }

    private val fila = Executors.newFixedThreadPool(4).asCoroutineDispatcher()

    fun lerBytes(m: Miniatura): ByteArray {
        require(m.tamanho in 1..MAX_BYTES) { "Tamanho inválido: ${m.tamanho}" }
        return RandomAccessFile(m.arquivo, "r").use { raf ->
            val buf = ByteArray(m.tamanho.toInt())
            raf.seek(m.inicio)
            raf.readFully(buf)
            buf
        }
    }

    fun doCache(m: Miniatura, alvo: Int): Bitmap? = cache.get("${m.chave}#$alvo")

    /** Bitmap com lado menor perto de [alvo] px (reduzido em potências de 2, nunca ampliado). */
    suspend fun carregar(m: Miniatura, alvo: Int): Bitmap? {
        val k = "${m.chave}#$alvo"
        cache.get(k)?.let { return it }
        return withContext(fila) {
            try {
                val bytes = lerBytes(m)
                val limites = BitmapFactory.Options().apply { inJustDecodeBounds = true }
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size, limites)
                var amostra = 1
                while (limites.outWidth / (amostra * 2) >= alvo && limites.outHeight / (amostra * 2) >= alvo) {
                    amostra *= 2
                }
                val op = BitmapFactory.Options().apply { inSampleSize = amostra }
                BitmapFactory.decodeByteArray(bytes, 0, bytes.size, op)
            } catch (e: Exception) {
                null
            } catch (e: OutOfMemoryError) {
                null
            }
        }?.also { cache.put(k, it) }
    }

    suspend fun dimensoes(m: Miniatura): Pair<Int, Int>? = withContext(fila) {
        try {
            val bytes = lerBytes(m)
            val op = BitmapFactory.Options().apply { inJustDecodeBounds = true }
            BitmapFactory.decodeByteArray(bytes, 0, bytes.size, op)
            if (op.outWidth > 0) op.outWidth to op.outHeight else null
        } catch (e: Exception) {
            null
        }
    }
}
