package br.uvr.fitsync.strava

import br.uvr.fitsync.Amostras
import br.uvr.fitsync.Esporte
import br.uvr.fitsync.Ponto
import br.uvr.fitsync.Posicao
import br.uvr.fitsync.Treino
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.TimeZone
import kotlin.math.atan2
import kotlin.math.cos
import kotlin.math.sin
import kotlin.math.sqrt

/**
 * Monta o arquivo TCX que o Strava importa: uma volta, com um ponto por segundo em que
 * houver qualquer dado (GPS, FC, velocidade, cadência, potência).
 */
object Tcx {

    // Quanto tempo um valor "vale" depois de medido, para preencher os pontos vizinhos.
    private const val VALIDADE_GPS = 10_000L
    private const val VALIDADE_SENSOR = 15_000L

    fun gerar(t: Treino, e: Esporte, a: Amostras): String {
        val distGps = distanciasAcumuladas(a.posicoes)
        val tempos = (a.posicoes.map { it.t } + a.fc.map { it.t } + a.velocidade.map { it.t } +
            a.passos.map { it.t } + a.rpm.map { it.t } + a.potencia.map { it.t })
            .map { it / 1000 * 1000 }
            .filter { it in t.inicio..t.fim }
            .distinct()
            .sorted()

        val distVel = if (a.posicoes.isEmpty()) integrarVelocidade(a.velocidade) else emptyList()
        val distTotal = t.distancia ?: distGps.lastOrNull()?.v ?: distVel.lastOrNull()?.v

        val sb = StringBuilder(64 * 1024)
        sb.append("<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n")
        sb.append(
            "<TrainingCenterDatabase xmlns=\"http://www.garmin.com/xmlschemas/TrainingCenterDatabase/v2\" " +
                "xmlns:ns3=\"http://www.garmin.com/xmlschemas/ActivityExtension/v2\">\n"
        )
        sb.append("<Activities>\n<Activity Sport=\"${e.tcx}\">\n")
        sb.append("<Id>${hora(t.inicio)}</Id>\n")
        sb.append("<Lap StartTime=\"${hora(t.inicio)}\">\n")
        sb.append("<TotalTimeSeconds>${(t.fim - t.inicio) / 1000}</TotalTimeSeconds>\n")
        sb.append("<DistanceMeters>${num(distTotal ?: 0.0)}</DistanceMeters>\n")
        t.calorias?.let { sb.append("<Calories>${it.toInt()}</Calories>\n") }
        if (a.fc.isNotEmpty()) {
            sb.append("<AverageHeartRateBpm><Value>${a.fc.map { it.v }.average().toInt()}</Value></AverageHeartRateBpm>\n")
            sb.append("<MaximumHeartRateBpm><Value>${a.fc.maxOf { it.v }.toInt()}</Value></MaximumHeartRateBpm>\n")
        }
        sb.append("<Intensity>Active</Intensity>\n<TriggerMethod>Manual</TriggerMethod>\n")
        sb.append("<Track>\n")

        val gps = Cursor(a.posicoes.map { it.t })
        val dg = Cursor(distGps.map { it.t })
        val dv = Cursor(distVel.map { it.t })
        val fc = Cursor(a.fc.map { it.t })
        val vel = Cursor(a.velocidade.map { it.t })
        val pas = Cursor(a.passos.map { it.t })
        val rpm = Cursor(a.rpm.map { it.t })
        val pot = Cursor(a.potencia.map { it.t })
        val alt = Cursor(a.altitude.map { it.t })

        for (tp in tempos) {
            sb.append("<Trackpoint><Time>${hora(tp)}</Time>")
            gps.em(tp, VALIDADE_GPS)?.let { i ->
                val p: Posicao = a.posicoes[i]
                sb.append("<Position><LatitudeDegrees>${coord(p.lat)}</LatitudeDegrees>")
                sb.append("<LongitudeDegrees>${coord(p.lon)}</LongitudeDegrees></Position>")
            }
            val altitude = gps.em(tp, VALIDADE_GPS)?.let { a.posicoes[it].alt }
                ?: alt.em(tp, VALIDADE_SENSOR)?.let { a.altitude[it].v }
            altitude?.let { sb.append("<AltitudeMeters>${num(it)}</AltitudeMeters>") }
            val dist = dg.em(tp, Long.MAX_VALUE)?.let { distGps[it].v }
                ?: dv.em(tp, Long.MAX_VALUE)?.let { distVel[it].v }
            dist?.let { sb.append("<DistanceMeters>${num(it)}</DistanceMeters>") }
            fc.em(tp, VALIDADE_SENSOR)?.let {
                sb.append("<HeartRateBpm><Value>${a.fc[it].v.toInt()}</Value></HeartRateBpm>")
            }
            if (e.tcx == "Biking") {
                rpm.em(tp, VALIDADE_SENSOR)?.let { sb.append("<Cadence>${a.rpm[it].v.toInt()}</Cadence>") }
            }

            val ext = StringBuilder()
            vel.em(tp, VALIDADE_SENSOR)?.let { ext.append("<ns3:Speed>${num(a.velocidade[it].v)}</ns3:Speed>") }
            if (e.tcx != "Biking") {
                // TCX conta a cadência de corrida por perna (passos/min ÷ 2); o Strava dobra de volta.
                pas.em(tp, VALIDADE_SENSOR)?.let {
                    ext.append("<ns3:RunCadence>${(a.passos[it].v / 2).toInt()}</ns3:RunCadence>")
                }
            }
            pot.em(tp, VALIDADE_SENSOR)?.let { ext.append("<ns3:Watts>${a.potencia[it].v.toInt()}</ns3:Watts>") }
            if (ext.isNotEmpty()) {
                sb.append("<Extensions><ns3:TPX>").append(ext).append("</ns3:TPX></Extensions>")
            }
            sb.append("</Trackpoint>\n")
        }

        sb.append("</Track>\n</Lap>\n")
        sb.append("<Creator xsi:type=\"Device_t\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\">")
        sb.append("<Name>Huawei Watch Fit 5</Name><UnitId>0</UnitId><ProductID>0</ProductID>")
        sb.append("<Version><VersionMajor>1</VersionMajor><VersionMinor>0</VersionMinor></Version></Creator>\n")
        sb.append("</Activity>\n</Activities>\n</TrainingCenterDatabase>\n")
        return sb.toString()
    }

    /** Distância acumulada (m) em cada ponto de GPS. */
    private fun distanciasAcumuladas(p: List<Posicao>): List<Ponto> {
        if (p.isEmpty()) return emptyList()
        val saida = ArrayList<Ponto>(p.size)
        var total = 0.0
        saida += Ponto(p[0].t, 0.0)
        for (i in 1 until p.size) {
            val d = haversine(p[i - 1], p[i])
            // Salto de GPS absurdo (> 100 m/s) não conta
            val dt = (p[i].t - p[i - 1].t).coerceAtLeast(1) / 1000.0
            if (d / dt < 100) total += d
            saida += Ponto(p[i].t, total)
        }
        return saida
    }

    /** Sem GPS (esteira): distância a partir da velocidade. */
    private fun integrarVelocidade(v: List<Ponto>): List<Ponto> {
        if (v.isEmpty()) return emptyList()
        val saida = ArrayList<Ponto>(v.size)
        var total = 0.0
        saida += Ponto(v[0].t, 0.0)
        for (i in 1 until v.size) {
            val dt = ((v[i].t - v[i - 1].t) / 1000.0).coerceAtMost(30.0)
            total += v[i - 1].v * dt
            saida += Ponto(v[i].t, total)
        }
        return saida
    }

    private fun haversine(a: Posicao, b: Posicao): Double {
        val r = 6_371_000.0
        val dLat = Math.toRadians(b.lat - a.lat)
        val dLon = Math.toRadians(b.lon - a.lon)
        val h = sin(dLat / 2) * sin(dLat / 2) +
            cos(Math.toRadians(a.lat)) * cos(Math.toRadians(b.lat)) * sin(dLon / 2) * sin(dLon / 2)
        return 2 * r * atan2(sqrt(h), sqrt(1 - h))
    }

    private fun hora(ms: Long): String {
        val f = SimpleDateFormat("yyyy-MM-dd'T'HH:mm:ss'Z'", Locale.US)
        f.timeZone = TimeZone.getTimeZone("UTC")
        return f.format(Date(ms))
    }

    private fun num(v: Double) = String.format(Locale.US, "%.1f", v)
    private fun coord(v: Double) = String.format(Locale.US, "%.7f", v)

    /**
     * Percorre uma série em ordem de tempo e devolve o índice da última amostra
     * em ou antes de [t], se ela tiver no máximo [validade] ms.
     */
    private class Cursor(private val tempos: List<Long>) {
        private var i = -1
        fun em(t: Long, validade: Long): Int? {
            while (i + 1 < tempos.size && tempos[i + 1] <= t + 999) i++
            if (i < 0) return null
            return if (t - tempos[i] <= validade) i else null
        }
    }
}
