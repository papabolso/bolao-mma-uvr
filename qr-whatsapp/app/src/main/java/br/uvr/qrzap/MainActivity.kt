package br.uvr.qrzap

import android.Manifest
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import android.util.Size
import android.view.HapticFeedbackConstants
import android.widget.ImageButton
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.camera.core.Camera
import androidx.camera.core.CameraSelector
import androidx.camera.core.ExperimentalGetImage
import androidx.camera.core.ImageAnalysis
import androidx.camera.core.ImageProxy
import androidx.camera.core.Preview
import androidx.camera.core.TorchState
import androidx.camera.core.resolutionselector.ResolutionSelector
import androidx.camera.core.resolutionselector.ResolutionStrategy
import androidx.camera.lifecycle.ProcessCameraProvider
import androidx.camera.view.PreviewView
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible
import com.google.mlkit.vision.barcode.BarcodeScannerOptions
import com.google.mlkit.vision.barcode.BarcodeScanning
import com.google.mlkit.vision.barcode.common.Barcode
import com.google.mlkit.vision.common.InputImage
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors

/**
 * Abre direto na câmera traseira, lê o primeiro QR code que aparecer e
 * manda o conteúdo para o compartilhamento do WhatsApp.
 */
class MainActivity : ComponentActivity() {

    private lateinit var preview: PreviewView
    private lateinit var dica: TextView
    private lateinit var lanterna: ImageButton

    private lateinit var analise: ExecutorService
    private val leitor by lazy {
        BarcodeScanning.getClient(
            BarcodeScannerOptions.Builder().setBarcodeFormats(Barcode.FORMAT_QR_CODE).build()
        )
    }
    private var camera: Camera? = null

    // Estado da leitura (só mexido na thread principal)
    private var compartilhando = false
    private var ultimoValor: String? = null
    private var quadrosVazios = 0

    private val pedirCamera =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { ok ->
            if (ok) iniciarCamera() else dica.setText(R.string.sem_permissao)
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        preview = findViewById(R.id.preview)
        dica = findViewById(R.id.dica)
        lanterna = findViewById(R.id.lanterna)
        analise = Executors.newSingleThreadExecutor()

        lanterna.setOnClickListener {
            camera?.let { it.cameraControl.enableTorch(it.cameraInfo.torchState.value != TorchState.ON) }
        }
        dica.setOnClickListener { if (!temPermissao()) pedirCamera.launch(Manifest.permission.CAMERA) }

        if (temPermissao()) iniciarCamera() else pedirCamera.launch(Manifest.permission.CAMERA)
    }

    override fun onResume() {
        super.onResume()
        // Voltou do WhatsApp: pronto para o próximo código
        compartilhando = false
        dica.setText(if (temPermissao()) R.string.dica else R.string.sem_permissao)
    }

    override fun onDestroy() {
        super.onDestroy()
        analise.shutdown()
        leitor.close()
    }

    private fun temPermissao() =
        ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED

    private fun iniciarCamera() {
        val futuro = ProcessCameraProvider.getInstance(this)
        futuro.addListener({
            val provedor = futuro.get()
            val prev = Preview.Builder().build().also { it.setSurfaceProvider(preview.surfaceProvider) }
            // 720p basta para QR e mantém cada quadro leve (leitura em poucos ms)
            val analisador = ImageAnalysis.Builder()
                .setResolutionSelector(
                    ResolutionSelector.Builder()
                        .setResolutionStrategy(
                            ResolutionStrategy(
                                Size(1280, 720),
                                ResolutionStrategy.FALLBACK_RULE_CLOSEST_HIGHER_THEN_LOWER
                            )
                        )
                        .build()
                )
                .setBackpressureStrategy(ImageAnalysis.STRATEGY_KEEP_ONLY_LATEST)
                .build()
            analisador.setAnalyzer(analise, ::analisar)

            provedor.unbindAll()
            camera = provedor.bindToLifecycle(this, CameraSelector.DEFAULT_BACK_CAMERA, prev, analisador)
            lanterna.isVisible = camera?.cameraInfo?.hasFlashUnit() == true
            dica.setText(R.string.dica)
        }, ContextCompat.getMainExecutor(this))
    }

    @androidx.annotation.OptIn(ExperimentalGetImage::class)
    private fun analisar(quadro: ImageProxy) {
        val imagem = quadro.image
        if (imagem == null) {
            quadro.close()
            return
        }
        leitor.process(InputImage.fromMediaImage(imagem, quadro.imageInfo.rotationDegrees))
            .addOnSuccessListener { codigos ->
                val valor = codigos.firstNotNullOfOrNull { it.rawValue?.trim()?.takeIf(String::isNotEmpty) }
                if (valor == null) quadrosVazios++ else achou(valor)
            }
            .addOnCompleteListener { quadro.close() }
    }

    private fun achou(valor: String) {
        if (compartilhando) return
        // Ao voltar do WhatsApp a câmera costuma ainda estar no mesmo QR.
        // Só repete o mesmo código depois que ele sai de vista por alguns quadros seguidos.
        if (valor == ultimoValor && quadrosVazios < 8) {
            quadrosVazios = 0
            dica.setText(R.string.mesmo_codigo)
            return
        }
        compartilhando = true
        ultimoValor = valor
        quadrosVazios = 0
        preview.performHapticFeedback(
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) HapticFeedbackConstants.CONFIRM
            else HapticFeedbackConstants.VIRTUAL_KEY
        )
        compartilhar(valor)
    }

    private fun compartilhar(texto: String) {
        val envio = Intent(Intent.ACTION_SEND)
            .setType("text/plain")
            .putExtra(Intent.EXTRA_TEXT, texto)
        for (pacote in listOf("com.whatsapp", "com.whatsapp.w4b")) {
            try {
                startActivity(Intent(envio).setPackage(pacote))
                return
            } catch (_: ActivityNotFoundException) {
                // tenta o próximo
            }
        }
        // Sem WhatsApp instalado: cai no compartilhamento padrão do Android
        startActivity(Intent.createChooser(envio, getString(R.string.compartilhar)))
    }
}
