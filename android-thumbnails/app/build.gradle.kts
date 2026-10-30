plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

// No GitHub Actions cada build ganha um número maior, então o APK novo instala por cima do antigo
val numeroBuild = (System.getenv("GITHUB_RUN_NUMBER") ?: "1").toInt()

android {
    namespace = "br.uvr.thumbs"
    compileSdk = 35

    defaultConfig {
        applicationId = "br.uvr.thumbs"
        minSdk = 26
        // 34 e não 35: no 35 o Android força edge-to-edge e a barra do app ficaria embaixo da de status
        targetSdk = 34
        versionCode = numeroBuild
        versionName = "1.0.$numeroBuild"
    }

    // Chave fixa no repo: assim cada APK novo instala por cima do anterior.
    // É só para uso pessoal (sideload); não serve para publicar na Play Store.
    signingConfigs {
        create("pessoal") {
            storeFile = file("thumbs.keystore")
            storePassword = "thumbs123"
            keyAlias = "thumbs"
            keyPassword = "thumbs123"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
            signingConfig = signingConfigs.getByName("pessoal")
        }
        debug {
            signingConfig = signingConfigs.getByName("pessoal")
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
        viewBinding = true
    }
    lint {
        // MANAGE_EXTERNAL_STORAGE é de propósito (a pasta .thumbnails não aparece pelo MediaStore)
        checkReleaseBuilds = false
        abortOnError = false
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.appcompat:appcompat:1.7.0")
    implementation("androidx.activity:activity-ktx:1.9.3")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.8.7")
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.8.7")
    implementation("androidx.recyclerview:recyclerview:1.3.2")
    implementation("androidx.viewpager2:viewpager2:1.1.0")
    implementation("com.google.android.material:material:1.12.0")
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.9.0")
}
