package br.uvr.thumbs

import android.content.Context
import android.database.Cursor
import android.provider.MediaStore

/** Lê ID e datas de toda a mídia do aparelho (uma consulta só, ordenada por ID). */
object LeitorGaleria {
    fun ler(ctx: Context): Galeria? {
        val uri = MediaStore.Files.getContentUri("external")
        fun consultar(colunas: Array<String>): Cursor? =
            ctx.contentResolver.query(uri, colunas, null, null, "_id ASC")

        // "datetaken" existe na tabela de arquivos, mas por garantia tenta de novo sem ela
        val cursor = try {
            consultar(arrayOf("_id", "date_added", "datetaken"))
        } catch (e: Exception) {
            try {
                consultar(arrayOf("_id", "date_added"))
            } catch (e: Exception) {
                null
            }
        } ?: return null

        return cursor.use { c ->
            val n = c.count
            val ids = LongArray(n)
            val adicionado = LongArray(n)
            val tirada = LongArray(n)
            val temTirada = c.columnCount > 2
            var k = 0
            while (c.moveToNext() && k < n) {
                ids[k] = c.getLong(0)
                adicionado[k] = c.getLong(1) * 1000 // date_added vem em segundos
                tirada[k] = if (temTirada && !c.isNull(2)) c.getLong(2) else 0
                k++
            }
            Galeria(ids.copyOf(k), adicionado.copyOf(k), tirada.copyOf(k))
        }
    }
}
