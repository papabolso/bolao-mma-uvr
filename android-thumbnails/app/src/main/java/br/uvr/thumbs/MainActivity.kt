package br.uvr.thumbs

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Environment
import android.os.Parcel
import android.os.Parcelable
import android.provider.Settings
import android.view.Menu
import android.view.MenuItem
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
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
import com.google.android.material.datepicker.CalendarConstraints
import com.google.android.material.datepicker.MaterialDatePicker
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import kotlinx.coroutines.launch
import java.util.Arrays

class MainActivity : AppCompatActivity() {
    private lateinit var b: ActivityMainBinding
    private val vm: MainViewModel by viewModels()
    private lateinit var adaptador: GradeAdapter
    private var exibido: Resultado? = null

    private val pedirPermissao =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { conferirAcesso() }

    // Com um dia escolhido, o "voltar" limpa o filtro em vez de fechar o app
    private val voltarLimpaDia = object : OnBackPressedCallback(false) {
        override fun handleOnBackPressed() = limparDia()
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        b = ActivityMainBinding.inflate(layoutInflater)
        setContentView(b.root)
        setSupportActionBar(b.barra)
        onBackPressedDispatcher.addCallback(this, voltarLimpaDia)

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

        b.grupoVisao.check(if (vm.modo == Modo.DATA) R.id.botaoData else R.id.botaoPasta)
        b.grupoVisao.addOnButtonCheckedListener { _, id, marcado ->
            if (!marcado) return@addOnButtonCheckedListener
            val novo = if (id == R.id.botaoData) Modo.DATA else Modo.PASTA
            if (novo == vm.modo) return@addOnButtonCheckedListener
            vm.modo = novo
            if (novo == Modo.PASTA) vm.dia = null
            aplicarVisao()
        }
        b.filtroDia.setOnCloseIconClickListener { limparDia() }
        b.filtroDia.setOnClickListener { abrirCalendario() }

        // Calendário que sobreviveu a uma rotação perdeu o listener: religa
        @Suppress("UNCHECKED_CAST")
        (supportFragmentManager.findFragmentByTag(TAG_CALENDARIO) as? MaterialDatePicker<Long>)
            ?.addOnPositiveButtonClickListener { escolherDia(it) }

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
            aplicarVisao()
        }
        val total = r.todas.size
        supportActionBar?.subtitle = "$total imagens · ${r.secoes.size} grupos"
        b.linhaVisao.isVisible = total > 0
        b.vazio.isVisible = total == 0 && !e.ocupado && temAcesso()
        b.vazio.text = if (r.verificadas.isEmpty()) {
            "Nenhuma pasta .thumbnails encontrada.\n\nProcurei em DCIM, Pictures e Movies (/.thumbnails) " +
                "na memória interna e no cartão SD. A pasta só aparece depois que a galeria gera miniaturas, " +
                "e alguns fabricantes guardam em outro lugar."
        } else {
            "As pastas existem, mas não têm imagens:\n\n" + r.verificadas.joinToString("\n") { Scanner.caminhoCurto(it) }
        }
    }

    /** Monta a grade conforme o modo: por pasta, por mês ou só o dia escolhido. */
    private fun aplicarVisao() {
        val r = exibido ?: return
        val dia = vm.dia
        when {
            dia != null -> adaptador.definir(Datas.doDia(r.todas, dia), "", rotuloData = false)
            vm.modo == Modo.DATA -> adaptador.definir(Datas.porMes(r.todas), Datas.resumo(r.todas), rotuloData = true)
            else -> adaptador.definir(r.secoes, resumoPastas(r), rotuloData = false)
        }
        b.filtroDia.isVisible = dia != null
        b.filtroDia.text = dia?.let { Datas.curta(it) } ?: ""
        voltarLimpaDia.isEnabled = dia != null
        b.grade.scrollToPosition(0)
    }

    private fun resumoPastas(r: Resultado): String = buildString {
        append("Pastas lidas: ")
        append(r.verificadas.joinToString { Scanner.caminhoCurto(it) })
        if (r.semImagem.isNotEmpty()) {
            append("\nSem imagem (índices e marcadores): ")
            append(r.semImagem.take(6).joinToString { it.name })
            if (r.semImagem.size > 6) append(" e mais ${r.semImagem.size - 6}")
        }
    }

    private fun abrirCalendario() {
        val r = exibido ?: return
        val dias = Datas.diasUtc(r.todas)
        if (dias.isEmpty()) {
            Toast.makeText(this, "Nenhuma imagem tem data.", Toast.LENGTH_SHORT).show()
            return
        }
        val inicial = vm.dia?.let { Datas.diaParaUtc(it) } ?: dias.last()
        val restricoes = CalendarConstraints.Builder()
            .setStart(dias.first())
            .setEnd(dias.last())
            .setOpenAt(inicial)
            .setValidator(SoDiasComImagem(dias))
            .build()
        val calendario = MaterialDatePicker.Builder.datePicker()
            .setTitleText("Dias com imagem (${dias.size})")
            .setSelection(inicial)
            .setCalendarConstraints(restricoes)
            .build()
        calendario.addOnPositiveButtonClickListener { escolherDia(it) }
        calendario.show(supportFragmentManager, TAG_CALENDARIO)
    }

    private fun escolherDia(utc: Long) {
        vm.modo = Modo.DATA
        vm.dia = Datas.utcParaDia(utc)
        b.grupoVisao.check(R.id.botaoData)
        aplicarVisao()
    }

    private fun limparDia() {
        vm.dia = null
        aplicarVisao()
    }

    override fun onCreateOptionsMenu(menu: Menu): Boolean {
        menuInflater.inflate(R.menu.principal, menu)
        return true
    }

    override fun onPrepareOptionsMenu(menu: Menu): Boolean {
        val ok = temAcesso()
        menu.findItem(R.id.atualizar)?.isEnabled = ok
        menu.findItem(R.id.exportar)?.isEnabled = ok
        menu.findItem(R.id.procurarData)?.isEnabled = ok
        return super.onPrepareOptionsMenu(menu)
    }

    override fun onOptionsItemSelected(item: MenuItem): Boolean = when (item.itemId) {
        R.id.procurarData -> {
            abrirCalendario()
            true
        }
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

    private companion object {
        const val TAG_CALENDARIO = "calendario"
    }
}

/** Deixa o calendário escolher só os dias que têm alguma imagem. */
class SoDiasComImagem(private val dias: LongArray) : CalendarConstraints.DateValidator {
    override fun isValid(date: Long) = Arrays.binarySearch(dias, date) >= 0
    override fun describeContents() = 0
    override fun writeToParcel(dest: Parcel, flags: Int) = dest.writeLongArray(dias)

    companion object {
        @JvmField
        val CREATOR = object : Parcelable.Creator<SoDiasComImagem> {
            override fun createFromParcel(p: Parcel) = SoDiasComImagem(p.createLongArray() ?: LongArray(0))
            override fun newArray(n: Int) = arrayOfNulls<SoDiasComImagem>(n)
        }
    }
}
