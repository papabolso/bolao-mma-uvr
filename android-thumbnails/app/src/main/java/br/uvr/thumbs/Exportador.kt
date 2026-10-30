package br.uvr.thumbs

import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.media.MediaScannerConnection
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import androidx.core.content.FileProvider
import java.io.File

/** Salva miniaturas como imagens normais (aparecem na galeria) e prepara o compartilhamento. */
object Exportador {
    const val PASTA = "Explorador Thumbnails"

    /** Grava em Imagens/Explorador Thumbnails e devolve o caminho para mostrar ao usuário. */
    fun salvar(ctx: Context, m: Miniatura): String {
        val bytes = Carregador.lerBytes(m)
        val nome = m.nomeExportacao()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
            val r = ctx.contentResolver
            val valores = ContentValues().apply {
                put(MediaStore.Images.Media.DISPLAY_NAME, nome)
                put(MediaStore.Images.Media.MIME_TYPE, m.formato.mime)
                put(MediaStore.Images.Media.RELATIVE_PATH, "${Environment.DIRECTORY_PICTURES}/$PASTA")
                put(MediaStore.Images.Media.IS_PENDING, 1)
            }
            val uri = r.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, valores)
                ?: error("não foi possível criar o arquivo")
            try {
                r.openOutputStream(uri)?.use { it.write(bytes) } ?: error("não foi possível gravar")
            } catch (e: Exception) {
                r.delete(uri, null, null)
                throw e
            }
            valores.clear()
            valores.put(MediaStore.Images.Media.IS_PENDING, 0)
            r.update(uri, valores, null, null)
        } else {
            @Suppress("DEPRECATION")
            val dir = File(Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_PICTURES), PASTA)
            dir.mkdirs()
            var destino = File(dir, nome)
            var n = 1
            while (destino.exists()) destino = File(dir, "${nome.substringBeforeLast('.')} ($n).${m.formato.ext}").also { n++ }
            destino.writeBytes(bytes)
            MediaScannerConnection.scanFile(ctx, arrayOf(destino.absolutePath), arrayOf(m.formato.mime), null)
        }
        return "Imagens/$PASTA/$nome"
    }

    /** Copia para o cache do app e devolve o Intent do "Compartilhar com…". */
    fun intentCompartilhar(ctx: Context, m: Miniatura): Intent {
        val dir = File(ctx.cacheDir, "compartilhar").apply {
            mkdirs()
            listFiles()?.forEach { it.delete() }
        }
        val arquivo = File(dir, m.nomeExportacao())
        arquivo.writeBytes(Carregador.lerBytes(m))
        val uri = FileProvider.getUriForFile(ctx, "${ctx.packageName}.arquivos", arquivo)
        val envio = Intent(Intent.ACTION_SEND)
            .setType(m.formato.mime)
            .putExtra(Intent.EXTRA_STREAM, uri)
            .addFlags(Intent.FLAG_GRANT_READ_URI_PERMISSION)
        return Intent.createChooser(envio, "Compartilhar miniatura")
    }
}
