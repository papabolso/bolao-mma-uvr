package br.uvr.fitsync

/** Um treino como a Huawei Health guarda (só o resumo, sem as amostras). */
data class Treino(
    val id: String,
    val tipo: String,          // tipo da Huawei: "running", "cycling", "walking"...
    val inicio: Long,          // epoch ms
    val fim: Long,             // epoch ms
    val distancia: Double?,    // metros
    val calorias: Double?,     // kcal
    val pacote: String?,       // app que gravou (com.huawei.health)
)

data class Ponto(val t: Long, val v: Double)

data class Posicao(val t: Long, val lat: Double, val lon: Double, val alt: Double?)

/** Séries de dados de um treino, cada uma em ordem de tempo. */
data class Amostras(
    val posicoes: List<Posicao> = emptyList(),
    val fc: List<Ponto> = emptyList(),          // bpm
    val velocidade: List<Ponto> = emptyList(),  // m/s
    val passos: List<Ponto> = emptyList(),      // passos/min
    val rpm: List<Ponto> = emptyList(),         // pedaladas/min
    val potencia: List<Ponto> = emptyList(),    // watts
    val altitude: List<Ponto> = emptyList(),    // metros
) {
    val vazia: Boolean
        get() = posicoes.isEmpty() && fc.isEmpty() && velocidade.isEmpty() &&
            passos.isEmpty() && rpm.isEmpty() && potencia.isEmpty()
}

/** Como o treino entra no Strava. */
data class Esporte(
    val sportType: String,  // sport_type da API do Strava
    val nome: String,       // base do título em português
    val tcx: String,        // Running / Biking / Other
    val indoor: Boolean = false,
)

object Esportes {
    private val mapa = mapOf(
        "running" to Esporte("Run", "Corrida", "Running"),
        "running.machine" to Esporte("Run", "Corrida na esteira", "Running", indoor = true),
        "treadmill" to Esporte("Run", "Corrida na esteira", "Running", indoor = true),
        "walking" to Esporte("Walk", "Caminhada", "Other"),
        "stroll_machine" to Esporte("Walk", "Caminhada na esteira", "Other", indoor = true),
        "hiking" to Esporte("Hike", "Trilha", "Other"),
        "on_foot" to Esporte("Walk", "Caminhada", "Other"),
        "cycling" to Esporte("Ride", "Pedal", "Biking"),
        "cycling_indoor" to Esporte("Ride", "Pedal indoor", "Biking", indoor = true),
        "spinning" to Esporte("Ride", "Spinning", "Biking", indoor = true),
        "swimming" to Esporte("Swim", "Natação", "Other"),
        "swimming.pool" to Esporte("Swim", "Natação na piscina", "Other", indoor = true),
        "swimming.open_water" to Esporte("Swim", "Natação em águas abertas", "Other"),
        "strength_training" to Esporte("WeightTraining", "Musculação", "Other", indoor = true),
        "weightlifting" to Esporte("WeightTraining", "Musculação", "Other", indoor = true),
        "functional_training" to Esporte("WeightTraining", "Treino funcional", "Other", indoor = true),
        "physical_training" to Esporte("WeightTraining", "Treino físico", "Other", indoor = true),
        "core_training" to Esporte("WeightTraining", "Treino de core", "Other", indoor = true),
        "kettlebell_training" to Esporte("WeightTraining", "Kettlebell", "Other", indoor = true),
        "calisthenics" to Esporte("Workout", "Calistenia", "Other"),
        "interval_training.high_intensity" to Esporte("HighIntensityIntervalTraining", "HIIT", "Other", indoor = true),
        "interval_training" to Esporte("HighIntensityIntervalTraining", "Treino intervalado", "Other"),
        "crossfit" to Esporte("Crossfit", "Crossfit", "Other", indoor = true),
        "cross_fit" to Esporte("Crossfit", "Crossfit", "Other", indoor = true),
        "yoga" to Esporte("Yoga", "Yoga", "Other", indoor = true),
        "pilates" to Esporte("Pilates", "Pilates", "Other", indoor = true),
        "elliptical" to Esporte("Elliptical", "Elíptico", "Other", indoor = true),
        "rowing.machine" to Esporte("Rowing", "Remo ergométrico", "Other", indoor = true),
        "rowing" to Esporte("Rowing", "Remo", "Other"),
        "stair_climbing" to Esporte("StairStepper", "Escada", "Other"),
        "stair_climbing.machine" to Esporte("StairStepper", "Simulador de escada", "Other", indoor = true),
        "football.soccer" to Esporte("Soccer", "Futebol", "Other"),
        "beach_soccer" to Esporte("Soccer", "Futebol de areia", "Other"),
        "tennis" to Esporte("Tennis", "Tênis", "Other"),
        "badminton" to Esporte("Badminton", "Badminton", "Other"),
        "table_tennis" to Esporte("TableTennis", "Tênis de mesa", "Other"),
        "squash" to Esporte("Squash", "Squash", "Other"),
        "golf" to Esporte("Golf", "Golfe", "Other"),
        "rock_climbing" to Esporte("RockClimbing", "Escalada", "Other"),
        "skateboarding" to Esporte("Skateboard", "Skate", "Other"),
        "surfing" to Esporte("Surfing", "Surfe", "Other"),
        "kayaking" to Esporte("Kayaking", "Caiaque", "Other"),
        "standup_paddleboarding" to Esporte("StandUpPaddling", "Stand up paddle", "Other"),
        "ice_skating" to Esporte("IceSkate", "Patinação no gelo", "Other"),
        "skiing" to Esporte("AlpineSki", "Esqui", "Other"),
        "snowboarding" to Esporte("Snowboard", "Snowboard", "Other"),
        "boxing" to Esporte("Workout", "Boxe", "Other", indoor = true),
        "kickboxing" to Esporte("Workout", "Kickboxing", "Other", indoor = true),
        "martial_arts" to Esporte("Workout", "Artes marciais", "Other", indoor = true),
        "martial_arts.mixed" to Esporte("Workout", "MMA", "Other", indoor = true),
        "jumping_rope" to Esporte("Workout", "Pular corda", "Other"),
        "dancing" to Esporte("Workout", "Dança", "Other"),
        "basketball" to Esporte("Workout", "Basquete", "Other"),
        "volleyball" to Esporte("Workout", "Vôlei", "Other"),
        "beach_volleyball" to Esporte("Workout", "Vôlei de praia", "Other"),
    )

    private val outro = Esporte("Workout", "Treino", "Other")

    fun de(tipoHuawei: String): Esporte = mapa[tipoHuawei.lowercase()] ?: outro

    /** Tipos que não são treino e nunca vão para o Strava. */
    val ignorados = setOf("sleep", "still", "in_vehicle", "elevator", "escalator", "meditation")
}
