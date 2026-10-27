plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
    id("org.jetbrains.kotlin.plugin.compose")
}

// App ID do AppGallery Connect (não é segredo). Vem da variável HMS_APP_ID no GitHub Actions
// ou de -PhmsAppId=... na linha de comando.
val hmsAppId: String = (project.findProperty("hmsAppId") as String?)
    ?: System.getenv("HMS_APP_ID")
    ?: ""

// Keystore fixa: a Huawei autoriza o app pela impressão SHA-256 da assinatura,
// então todo build precisa sair assinado com a MESMA chave.
val keystoreFile = rootProject.file("release.jks")
val keystorePassword: String? = System.getenv("FITSYNC_KEYSTORE_PASSWORD")
val temKeystore = keystoreFile.exists() && !keystorePassword.isNullOrEmpty()

android {
    namespace = "br.uvr.fitsync"
    compileSdk = 35

    defaultConfig {
        applicationId = "br.uvr.fitsync"
        minSdk = 26
        targetSdk = 35
        versionCode = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()
        versionName = "1.0." + (System.getenv("GITHUB_RUN_NUMBER") ?: "0")
        manifestPlaceholders["hmsAppId"] = hmsAppId
    }

    signingConfigs {
        if (temKeystore) {
            create("release") {
                storeFile = keystoreFile
                storePassword = keystorePassword
                keyAlias = System.getenv("FITSYNC_KEY_ALIAS") ?: "fitsync"
                keyPassword = keystorePassword
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = if (temKeystore) signingConfigs.getByName("release")
            else signingConfigs.getByName("debug")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
    }
}

dependencies {
    implementation("com.huawei.hms:health:6.11.0.303")

    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-compose:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.work:work-runtime-ktx:2.10.0")
    implementation(platform("androidx.compose:compose-bom:2024.12.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.material3:material3")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
}
