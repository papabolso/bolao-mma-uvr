package br.uvr.thumbs

import android.content.Context
import android.util.AttributeSet
import android.view.LayoutInflater
import android.view.ViewGroup
import androidx.appcompat.widget.AppCompatImageView
import androidx.core.view.isVisible
import androidx.recyclerview.widget.RecyclerView
import br.uvr.thumbs.databinding.ItemCabecalhoBinding
import br.uvr.thumbs.databinding.ItemInfoBinding
import br.uvr.thumbs.databinding.ItemMiniaturaBinding
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch

/** ImageView sempre quadrada (altura = largura da coluna). */
class QuadradoImageView(ctx: Context, attrs: AttributeSet?) : AppCompatImageView(ctx, attrs) {
    override fun onMeasure(larguraSpec: Int, alturaSpec: Int) = super.onMeasure(larguraSpec, larguraSpec)
}

/**
 * Grade de miniaturas com um cabeçalho por grupo (toque recolhe/expande).
 * [aoTocar] recebe a posição da imagem na lista completa ([Resultado.todas]).
 */
class GradeAdapter(
    private val escopo: CoroutineScope,
    private val aoTocar: (Int) -> Unit,
) : RecyclerView.Adapter<RecyclerView.ViewHolder>() {

    private sealed interface Linha {
        data class Info(val texto: String) : Linha
        data class Cabecalho(val indice: Int, val secao: Secao, val recolhida: Boolean) : Linha
        data class Imagem(val m: Miniatura, val global: Int) : Linha
    }

    private class InfoVH(val b: ItemInfoBinding) : RecyclerView.ViewHolder(b.root)
    private class CabecalhoVH(val b: ItemCabecalhoBinding) : RecyclerView.ViewHolder(b.root)
    private class ImagemVH(val b: ItemMiniaturaBinding) : RecyclerView.ViewHolder(b.root) {
        var chave = ""
        var tarefa: Job? = null
    }

    private var resultado: Resultado? = null
    private val recolhidas = mutableSetOf<Int>()
    private var linhas: List<Linha> = emptyList()

    fun definir(r: Resultado) {
        resultado = r
        recolhidas.clear()
        montar()
    }

    fun ehImagem(pos: Int) = linhas.getOrNull(pos) is Linha.Imagem

    private fun montar() {
        val r = resultado ?: return
        val l = mutableListOf<Linha>(Linha.Info(resumo(r)))
        var global = 0
        r.secoes.forEachIndexed { i, s ->
            val recolhida = i in recolhidas
            l += Linha.Cabecalho(i, s, recolhida)
            if (recolhida) global += s.itens.size
            else s.itens.forEach { l += Linha.Imagem(it, global++) }
        }
        linhas = l
        @Suppress("NotifyDataSetChanged")
        notifyDataSetChanged()
    }

    private fun resumo(r: Resultado): String = buildString {
        append("Pastas lidas: ")
        append(r.verificadas.joinToString { Scanner.caminhoCurto(it) })
        if (r.semImagem.isNotEmpty()) {
            append("\nSem imagem (índices e marcadores): ")
            append(r.semImagem.take(6).joinToString { it.name })
            if (r.semImagem.size > 6) append(" e mais ${r.semImagem.size - 6}")
        }
    }

    override fun getItemCount() = linhas.size

    override fun getItemViewType(pos: Int) = when (linhas[pos]) {
        is Linha.Info -> 0
        is Linha.Cabecalho -> 1
        is Linha.Imagem -> 2
    }

    override fun onCreateViewHolder(parent: ViewGroup, tipo: Int): RecyclerView.ViewHolder {
        val inf = LayoutInflater.from(parent.context)
        return when (tipo) {
            0 -> InfoVH(ItemInfoBinding.inflate(inf, parent, false))
            1 -> CabecalhoVH(ItemCabecalhoBinding.inflate(inf, parent, false))
            else -> ImagemVH(ItemMiniaturaBinding.inflate(inf, parent, false))
        }
    }

    override fun onBindViewHolder(h: RecyclerView.ViewHolder, pos: Int) {
        when (val linha = linhas[pos]) {
            is Linha.Info -> (h as InfoVH).b.texto.text = linha.texto
            is Linha.Cabecalho -> {
                val b = (h as CabecalhoVH).b
                b.titulo.text = linha.secao.titulo
                b.detalhe.text = "${linha.secao.detalhe} · ${linha.secao.itens.size} imagens"
                b.seta.rotation = if (linha.recolhida) -90f else 0f
                b.root.setOnClickListener {
                    if (!recolhidas.remove(linha.indice)) recolhidas += linha.indice
                    montar()
                }
            }
            is Linha.Imagem -> ligarImagem(h as ImagemVH, linha)
        }
    }

    private fun ligarImagem(h: ImagemVH, linha: Linha.Imagem) {
        val m = linha.m
        h.chave = m.chave
        h.tarefa?.cancel()
        h.b.rotulo.isVisible = m.embutida
        h.b.rotulo.text = "#${m.indice}"
        h.b.root.setOnClickListener { aoTocar(linha.global) }

        val pronta = Carregador.doCache(m, ALVO)
        if (pronta != null) {
            h.b.imagem.setImageBitmap(pronta)
            return
        }
        h.b.imagem.setImageDrawable(null)
        h.tarefa = escopo.launch {
            val bmp = Carregador.carregar(m, ALVO)
            if (h.chave != m.chave) return@launch
            if (bmp != null) h.b.imagem.setImageBitmap(bmp) else h.b.imagem.setImageResource(R.drawable.ic_quebrada)
        }
    }

    override fun onViewRecycled(h: RecyclerView.ViewHolder) {
        if (h is ImagemVH) {
            h.tarefa?.cancel()
            h.chave = ""
            h.b.imagem.setImageDrawable(null)
        }
    }

    private companion object {
        const val ALVO = 256
    }
}
