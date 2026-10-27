package br.uvr.fitsync.sync

import android.Manifest
import android.annotation.SuppressLint
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import androidx.work.Constraints
import androidx.work.CoroutineWorker
import androidx.work.ExistingPeriodicWorkPolicy
import androidx.work.NetworkType
import androidx.work.PeriodicWorkRequestBuilder
import androidx.work.WorkManager
import androidx.work.WorkerParameters
import br.uvr.fitsync.MainActivity
import br.uvr.fitsync.R
import java.util.concurrent.TimeUnit

/** Sincronização em segundo plano, a cada hora, com internet. */
class SyncWorker(ctx: Context, params: WorkerParameters) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val r = Sincronizador(applicationContext).sincronizar()
        if (r.enviados > 0) {
            Notificacao.mostrar(
                applicationContext,
                if (r.enviados == 1) "1 treino enviado ao Strava" else "${r.enviados} treinos enviados ao Strava",
            )
        }
        return Result.success()
    }
}

object Agendamento {
    private const val NOME = "fitsync-periodico"

    fun aplicar(ctx: Context, ligado: Boolean) {
        val wm = WorkManager.getInstance(ctx)
        if (!ligado) {
            wm.cancelUniqueWork(NOME)
            return
        }
        val pedido = PeriodicWorkRequestBuilder<SyncWorker>(1, TimeUnit.HOURS)
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .build()
        wm.enqueueUniquePeriodicWork(NOME, ExistingPeriodicWorkPolicy.KEEP, pedido)
    }
}

object Notificacao {
    private const val CANAL = "sync"

    @SuppressLint("MissingPermission")  // conferida logo abaixo
    fun mostrar(ctx: Context, texto: String) {
        if (Build.VERSION.SDK_INT >= 33 &&
            ContextCompat.checkSelfPermission(ctx, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED
        ) return

        val nm = ctx.getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(
            NotificationChannel(CANAL, "Sincronização", NotificationManager.IMPORTANCE_LOW)
        )
        val abrir = PendingIntent.getActivity(
            ctx, 0, Intent(ctx, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE
        )
        val n = NotificationCompat.Builder(ctx, CANAL)
            .setSmallIcon(R.drawable.ic_notificacao)
            .setContentTitle("FitSync")
            .setContentText(texto)
            .setContentIntent(abrir)
            .setAutoCancel(true)
            .build()
        NotificationManagerCompat.from(ctx).notify(1, n)
    }
}
