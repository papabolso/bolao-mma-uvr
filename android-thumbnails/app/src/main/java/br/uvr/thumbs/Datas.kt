package br.uvr.thumbs

import java.time.Instant
import java.time.LocalDate
import java.time.YearMonth
import java.time.ZoneId
import java.time.ZoneOffset
import java.time.format.DateTimeFormatter
import java.util.Locale

/** Cópia do banco de mídia do Android: IDs em ordem crescente e as datas de cada um (ms). */
class Galeria(val ids: LongArray, val adicionado: LongArray, val tirada: LongArray)

/**
 * Descobre a data de cada miniatura e monta as visões por data.
 *
 * A miniatura em si não traz data. O que dá para usar, do mais confiável para o menos:
 * 1. O ID da mídia, se a foto original ainda existe: a data vem do banco de mídia.
 *    - solta do Android 10+: o nome é o ID (`12345.jpg`);
 *    - dentro do .thumbdata: o Android grava a miniatura do ID n no slot n, de 10.000 bytes,
 *      com 13 bytes de cabeçalho, então o JPEG começa em n × 10.000 + 13.
 * 2. Solta do Android 4 a 9: o nome é a hora em que foi criada (`1424093011867.jpg`).
 * 3. Foto já apagada (comum no .thumbdata): os IDs crescem conforme as fotos entram, então a
 *    data é interpolada entre o ID existente logo antes e o logo depois. Marcada como estimada.
 * 4. Solta sem nada disso: data de modificação do próprio arquivo de miniatura.
 */
object Datas {
    private const val SLOT = 10_000L
    private const val CABECALHO_SLOT = 13L
    private const val ANO_2000 = 946_684_800_000L
    private const val UM_DIA = 86_400_000L

    private val PT = Locale.forLanguageTag("pt-BR")
    private val FMT_MES = DateTimeFormatter.ofPattern("MMMM 'de' yyyy", PT)
    private val FMT_DIA = DateTimeFormatter.ofPattern("EEEE, d 'de' MMMM 'de' yyyy", PT)
    private val FMT_CURTA = DateTimeFormatter.ofPattern("dd/MM/yyyy", PT)
    private val FMT_HORA = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm", PT)
    private val FMT_ROTULO = DateTimeFormatter.ofPattern("dd/MM", PT)

    // ---------- descobrir as datas ----------

    fun datar(r: Resultado, g: Galeria?, agora: Long = System.currentTimeMillis()): Resultado =
        r.copy(secoes = r.secoes.map { s -> s.copy(itens = s.itens.map { datar(it, g, agora) }) })

    fun idDaMidia(m: Miniatura): Long? {
        if (m.embutida) {
            val d = m.inicio - CABECALHO_SLOT
            return if (d > 0 && d % SLOT == 0L) d / SLOT else null
        }
        val n = m.arquivo.name.substringBefore('.').toLongOrNull() ?: return null
        return if (n in 1 until 1_000_000_000L) n else null
    }

    private fun datar(m: Miniatura, g: Galeria?, agora: Long): Miniatura {
        val id = idDaMidia(m)
        if (id != null && g != null) {
            val i = g.ids.binarySearch(id)
            if (i >= 0) {
                val d = if (g.tirada[i] >= ANO_2000) g.tirada[i] else g.adicionado[i]
                if (d >= ANO_2000) return m.copy(idMidia = id, data = d, origemData = OrigemData.GALERIA)
            }
        }
        if (!m.embutida) {
            val n = m.arquivo.name.substringBefore('.').toLongOrNull()
            if (n != null && n in ANO_2000..agora + UM_DIA) {
                return m.copy(idMidia = id, data = n, origemData = OrigemData.NOME)
            }
            if (m.modificado >= ANO_2000) {
                return m.copy(idMidia = id, data = m.modificado, origemData = OrigemData.ARQUIVO)
            }
            return m.copy(idMidia = id)
        }
        if (id != null && g != null) {
            estimar(id, g)?.let { return m.copy(idMidia = id, data = it, origemData = OrigemData.ESTIMADA) }
        }
        return m.copy(idMidia = id)
    }

    /**
     * Data provável de um ID que não está mais no banco. Entre dois IDs conhecidos, interpola;
     * depois do último, usa a data do último (a foto é no mínimo daquele dia). Antes do primeiro
     * não dá para dizer nada.
     */
    fun estimar(id: Long, g: Galeria): Long? {
        val pos = g.ids.binarySearch(id).let { if (it >= 0) it else -(it + 1) }
        val antes = (pos - 1 downTo 0).firstOrNull { g.adicionado[it] >= ANO_2000 }
        val depois = (pos until g.ids.size).firstOrNull { g.adicionado[it] >= ANO_2000 }
        return when {
            antes != null && depois != null -> {
                val a = g.ids[antes]
                val b = g.ids[depois]
                val da = g.adicionado[antes]
                val db = g.adicionado[depois]
                if (b == a) da else da + ((db - da) * ((id - a).toDouble() / (b - a))).toLong()
            }
            antes != null -> g.adicionado[antes]
            else -> null
        }
    }

    // ---------- visões ----------

    fun diaLocal(ms: Long): LocalDate = Instant.ofEpochMilli(ms).atZone(ZoneId.systemDefault()).toLocalDate()

    /** Grupos por mês, do mais recente para o mais antigo; as sem data ficam no fim. */
    fun porMes(todas: List<Miniatura>): List<Secao> {
        val (comData, semData) = todas.partition { it.data > 0 }
        val secoes = comData.sortedByDescending { it.data }
            .groupBy { YearMonth.from(diaLocal(it.data)) } // groupBy mantém a ordem
            .map { (mes, itens) -> Secao(maiuscula(mes.format(FMT_MES)), detalheEstimadas(itens), itens) }
        return if (semData.isEmpty()) secoes
        else secoes + Secao("Sem data", "não deu para descobrir quando foram feitas", semData)
    }

    fun doDia(todas: List<Miniatura>, dia: LocalDate): List<Secao> {
        val itens = todas.filter { it.data > 0 && diaLocal(it.data) == dia }.sortedByDescending { it.data }
        return listOf(Secao(maiuscula(dia.format(FMT_DIA)), detalheEstimadas(itens), itens))
    }

    /** Dias que têm imagem, como o calendário do Material espera: meia-noite UTC, em ordem. */
    fun diasUtc(todas: List<Miniatura>): LongArray =
        todas.asSequence()
            .filter { it.data > 0 }
            .map { diaParaUtc(diaLocal(it.data)) }
            .distinct()
            .sorted()
            .toList()
            .toLongArray()

    fun diaParaUtc(dia: LocalDate): Long = dia.atStartOfDay(ZoneOffset.UTC).toInstant().toEpochMilli()

    fun utcParaDia(ms: Long): LocalDate = Instant.ofEpochMilli(ms).atZone(ZoneOffset.UTC).toLocalDate()

    fun curta(dia: LocalDate): String = dia.format(FMT_CURTA)

    /** Texto do selo na grade: "12/03" ou "≈12/03". */
    fun rotulo(m: Miniatura): String {
        if (m.data <= 0) return ""
        val d = diaLocal(m.data).format(FMT_ROTULO)
        return if (m.origemData == OrigemData.ESTIMADA) "≈$d" else d
    }

    /** Linha da tela cheia: "12/03/2018 14:22 (da galeria)" ou "≈ 12/03/2018 (estimada…)". */
    fun descrever(m: Miniatura): String {
        if (m.data <= 0) return "sem data"
        return if (m.origemData == OrigemData.ESTIMADA) {
            "≈ ${diaLocal(m.data).format(FMT_CURTA)} (${m.origemData.descricao})"
        } else {
            val hora = Instant.ofEpochMilli(m.data).atZone(ZoneId.systemDefault()).format(FMT_HORA)
            "$hora (${m.origemData.descricao})"
        }
    }

    fun resumo(todas: List<Miniatura>): String {
        val c = todas.groupingBy { it.origemData }.eachCount()
        val partes = listOfNotNull(
            c[OrigemData.GALERIA]?.let { "$it com a data da galeria" },
            c[OrigemData.NOME]?.let { "$it pela data no nome do arquivo" },
            c[OrigemData.ESTIMADA]?.let { "$it estimadas pela ordem das fotos (≈)" },
            c[OrigemData.ARQUIVO]?.let { "$it pela data do arquivo de miniatura" },
            c[OrigemData.NENHUMA]?.let { "$it sem data" },
        )
        return "Datas: " + partes.joinToString(", ") + "."
    }

    private fun detalheEstimadas(itens: List<Miniatura>): String {
        val n = itens.count { it.origemData == OrigemData.ESTIMADA }
        return if (n > 0) "$n com data estimada (≈)" else ""
    }

    private fun maiuscula(s: String) = s.replaceFirstChar { it.titlecase(PT) }
}
