package br.uvr.thumbs

import android.os.Bundle
import android.view.LayoutInflater
import android.view.Menu
import android.view.MenuItem
import android.view.ViewGroup
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.core.view.isVisible
import androidx.lifecycle.lifecycleScope
import androidx.recyclerview.widget.RecyclerView
import androidx.viewpager2.widget.ViewPager2
import br.uvr.thumbs.databinding.ActivityViewerBinding
import br.uvr.thumbs.databinding.PaginaImagemBinding
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.text.DateFormat
import java.util.Date
import java.util.Locale

/** Tela cheia: arrasta para os lados, toque esconde/mostra as barras. */
class ViewerActivity : AppCompatActivity() {
    companion object {
        const val EXTRA_POS = "pos"
    }

    private lateinit var b: ActivityViewerBinding
    private var lista: List<Miniatura> = emptyList()
    private var tarefaInfo: Job? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Se o Android matou o app em segundo plano, a lista se perdeu: volta para a grade
        val r = Repositorio.resultado
        if (r == null || r.todas.isEmpty()) {
            finish()
            return
        }
        lista = r.todas
        b = ActivityViewerBinding.inflate(layoutInflater)
        setContentView(b.root)
        setSupportActionBar(b.barra)
        supportActionBar?.setDisplayHomeAsUpEnabled(true)

        val dm = resources.displayMetrics
        b.paginas.adapter = PaginasAdapter(maxOf(dm.widthPixels, dm.heightPixels))
        b.paginas.offscreenPageLimit = 1
        b.paginas.registerOnPageChangeCallback(object : ViewPager2.OnPageChangeCallback() {
            override fun onPageSelected(position: Int) = mostrarInfo(position)
        })
        val inicial = intent.getIntExtra(EXTRA_POS, 0).coerceIn(0, lista.lastIndex)
        b.paginas.setCurrentItem(inicial, false)
        mostrarInfo(inicial)
    }

    private fun mostrarInfo(pos: Int) {
        val m = lista.getOrNull(pos) ?: return
        supportActionBar?.title = "${pos + 1} de ${lista.size}"
        supportActionBar?.subtitle = if (m.embutida) "${m.arquivo.name} · #${m.indice}" else m.arquivo.name
        val base = buildString {
            append(Scanner.caminhoCurto(m.arquivo))
            if (m.embutida) {
                append(String.format(Locale.getDefault(), "\nPosição no arquivo: 0x%X (byte %,d)", m.inicio, m.inicio))
            } else {
                append("\nModificado: ")
                append(DateFormat.getDateTimeInstance(DateFormat.SHORT, DateFormat.SHORT).format(Date(m.modificado)))
            }
            append("\nTamanho: ${fmtBytes(m.tamanho)} · ${m.formato.name}")
        }
        b.info.text = base
        tarefaInfo?.cancel()
        tarefaInfo = lifecycleScope.launch {
            val d = Carregador.dimensoes(m) ?: return@launch
            b.info.text = "$base · ${d.first} × ${d.second} px"
        }
    }

    private fun alternarBarras() {
        val mostrar = !b.barra.isVisible
        b.barra.isVisible = mostrar
        b.info.isVisible = mostrar
    }

    private fun atual(): Miniatura? = lista.getOrNull(b.paginas.currentItem)

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.visualizador, menu)
        return true
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean {
        val m = atual()
        when (item.itemId) {
            android.R.id.home -> finish()
            R.id.salvar -> if (m != null) lifecycleScope.launch {
                val msg = withContext(Dispatchers.IO) {
                    try {
                        "Salva em ${Exportador.salvar(applicationContext, m)}"
                    } catch (e: Exception) {
                        "Não deu para salvar: ${e.message}"
                    }
                }
                Toast.makeText(this@ViewerActivity, msg, Toast.LENGTH_LONG).show()
            }
            R.id.compartilhar -> if (m != null) lifecycleScope.launch {
                try {
                    startActivity(withContext(Dispatchers.IO) { Exportador.intentCompartilhar(applicationContext, m) })
                } catch (e: Exception) {
                    Toast.makeText(this@ViewerActivity, "Não deu para compartilhar: ${e.message}", Toast.LENGTH_LONG).show()
                }
            }
            else -> return super.onOptionsItemSelected(item)
        }
        return true
    }

    private class PaginaVH(val b: PaginaImagemBinding) : RecyclerView.ViewHolder(b.root) {
        var chave = ""
        var tarefa: Job? = null
    }

    private inner class PaginasAdapter(private val alvo: Int) : RecyclerView.Adapter<PaginaVH>() {
        override fun getItemCount() = lista.size

        override fun onCreateViewHolder(parent: ViewGroup, tipo: Int) =
            PaginaVH(PaginaImagemBinding.inflate(LayoutInflater.from(parent.context), parent, false))

        override fun onBindViewHolder(h: PaginaVH, pos: Int) {
            val m = lista[pos]
            h.chave = m.chave
            h.tarefa?.cancel()
            h.b.foto.setImageDrawable(null)
            h.b.foto.setOnClickListener { alternarBarras() }
            h.b.carregando.isVisible = true
            h.tarefa = lifecycleScope.launch {
                val bmp = Carregador.carregar(m, alvo)
                if (h.chave != m.chave) return@launch
                h.b.carregando.isVisible = false
                if (bmp != null) h.b.foto.setImageBitmap(bmp) else h.b.foto.setImageResource(R.drawable.ic_quebrada)
            }
        }

        override fun onViewRecycled(h: PaginaVH) {
            h.tarefa?.cancel()
            h.chave = ""
        }
    }
}
