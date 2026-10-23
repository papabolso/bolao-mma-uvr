plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "br.uvr.qrzap"
    compileSdk = 35

    defaultConfig {
        applicationId = "br.uvr.qrzap"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "1.0"
    }

    // Chave fixa no repo: assim cada APK novo instala por cima do anterior.
    // É só para uso pessoal (sideload); não serve para publicar na Play Store.
    signingConfigs {
        create("pessoal") {
            storeFile = file("qrzap.keystore")
            storePassword = "qrzap123"
            keyAlias = "qrzap"
            keyPassword = "qrzap123"
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"), "proguard-rules.pro")
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
}

dependencies {
    val camerax = "1.4.1"
    implementation("androidx.core:core-ktx:1.15.0")
    implementation("androidx.activity:activity-ktx:1.9.3")
    implementation("androidx.camera:camera-camera2:$camerax")
    implementation("androidx.camera:camera-lifecycle:$camerax")
    implementation("androidx.camera:camera-view:$camerax")
    // Modelo embutido no APK: funciona offline e não depende de download do Play Services
    implementation("com.google.mlkit:barcode-scanning:17.3.0")
}
