package br.uvr.thumbs

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.provider.Settings
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.lifecycleScope
import androidx.lifecycle.repeatOnLifecycle
import androidx.recyclerview.widget.GridLayoutManager
import br.uvr.thumbs.databinding.ActivityMainBinding
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import kotlinx.coroutines.launch

class MainActivity : AppCompatActivity() {
    private lateinit var b: ActivityMainBinding
    private val vm: MainViewModel by viewModels()
    private lateinit var adaptador: GradeAdapter
    private var exibido: Resultado? = null

    private val pedirPermissao =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { conferirAcesso() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        b = ActivityMainBinding.inflate(layoutInflater)
        setContentView(b.root)
        setSupportActionBar(b.barra)

        adaptador = GradeAdapter(lifecycleScope) { pos ->
            startActivity(Intent(this, ViewerActivity::class.java).putExtra(ViewerActivity.EXTRA_POS, pos))
        }
        val colunas = maxOf(3, resources.configuration.screenWidthDp / 110)
        val grade = GridLayoutManager(this, colunas)
        grade.spanSizeLookup = object : GridLayoutManager.SpanSizeLookup() {
            override fun getSpanSize(pos: Int) = if (adaptador.ehImagem(pos)) 1 else colunas
        }
        b.grade.layoutManager = grade
        b.grade.adapter = adaptador

        b.botaoPermissao.setOnClickListener { pedirAcesso() }

        lifecycleScope.launch {
            repeatOnLifecycle(Lifecycle.State.STARTED) {
                launch { vm.estado.collect { mostrar(it) } }
                launch { vm.avisos.collect { Toast.makeText(this@MainActivity, it, Toast.LENGTH_LONG).show() } }
            }
        }
    }

    override fun onResume() {
        super.onResume()
        // A permissão de "todos os arquivos" é dada numa tela do sistema; ao voltar dela cai aqui
        conferirAcesso()
    }

    private fun temAcesso(): Boolean =
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) Environment.isExternalStorageManager()
        else ContextCompat.checkSelfPermission(this, Manifest.permission.READ_EXTERNAL_STORAGE) ==
            PackageManager.PERMISSION_GRANTED

    private fun conferirAcesso() {
        val ok = temAcesso()
        b.painelPermissao.isVisible = !ok
        b.grade.isVisible = ok
        val e = vm.estado.value
        if (ok && e.resultado == null && !e.ocupado) vm.varrer()
        invalidateOptionsMenu()
    }

    private fun pedirAcesso() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            try {
                startActivity(Intent(Settings.ACTION_MANAGE_APP_ALL_FILES_ACCESS_PERMISSION, Uri.parse("package:$packageName")))
            } catch (e: ActivityNotFoundException) {
                startActivity(Intent(Settings.ACTION_MANAGE_ALL_FILES_ACCESS_PERMISSION))
            }
        } else {
            val perms = if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q) {
                arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE, Manifest.permission.WRITE_EXTERNAL_STORAGE)
            } else {
                arrayOf(Manifest.permission.READ_EXTERNAL_STORAGE)
            }
            pedirPermissao.launch(perms)
        }
    }

    private fun mostrar(e: Estado) {
        b.progresso.isVisible = e.ocupado
        if (e.progresso < 0) {
            b.progresso.isIndeterminate = true
        } else {
            b.progresso.isIndeterminate = false
            b.progresso.progress = (e.progresso * 1000).toInt()
        }
        b.status.isVisible = e.ocupado && e.mensagem.isNotEmpty()
        b.status.text = e.mensagem

        val r = e.resultado ?: return
        if (r !== exibido) {
            exibido = r
            adaptador.definir(r)
        }
        val total = r.todas.size
        supportActionBar?.subtitle = "$total imagens · ${r.secoes.size} grupos"
        b.vazio.isVisible = total == 0 && !e.ocupado && temAcesso()
        b.vazio.text = if (r.verificadas.isEmpty()) {
            "Nenhuma pasta .thumbnails encontrada.\n\nProcurei em DCIM/.thumbnails e Pictures/.thumbnails " +
                "na memória interna e no cartão SD. Em Android 10 ou mais novo a galeria costuma guardar " +
                "as miniaturas em outro lugar (dentro dos dados do próprio app), e essa pasta pode nem existir."
        } else {
            "As pastas existem, mas não têm imagens:\n\n" + r.verificadas.joinToString("\n") { Scanner.caminhoCurto(it) }
        }
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.principal, menu)
        return true
    }

    override fun onPrepareOptionsMenu(menu: Menu): Boolean {
        val ok = temAcesso()
        menu.findItem(R.id.atualizar)?.isEnabled = ok
        menu.findItem(R.id.exportar)?.isEnabled = ok
        return super.onPrepareOptionsMenu(menu)
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean = when (item.itemId) {
        R.id.atualizar -> {
            vm.varrer()
            true
        }
        R.id.exportar -> {
            confirmarExportacao()
            true
        }
        R.id.sobre -> {
            MaterialAlertDialogBuilder(this)
                .setTitle("O que é a pasta .thumbnails")
                .setMessage(getString(R.string.sobre_texto))
                .setPositiveButton("OK", null)
                .show()
            true
        }
        else -> super.onOptionsItemSelected(item)
    }

    private fun confirmarExportacao() {
        val n = Repositorio.resultado?.todas?.size ?: 0
        if (n == 0) {
            Toast.makeText(this, "Nada para salvar.", Toast.LENGTH_SHORT).show()
            return
        }
        MaterialAlertDialogBuilder(this)
            .setTitle("Salvar todas")
            .setMessage("Copiar as $n miniaturas para Imagens/${Exportador.PASTA}? Elas passam a aparecer na galeria.")
            .setNegativeButton("Cancelar", null)
            .setPositiveButton("Salvar") { _, _ -> vm.exportarTudo() }
            .show()
    }
}
