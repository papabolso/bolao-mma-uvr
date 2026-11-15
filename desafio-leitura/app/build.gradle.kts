plugins {
    id("com.android.application")
}

android {
    namespace = "br.uvr.leitura"
    compileSdk = 35

    defaultConfig {
        applicationId = "br.uvr.leitura"
        minSdk = 24
        // 34 de propósito: no 35 o Android desenha o app por baixo da barra de status.
        targetSdk = 34
        versionCode = 1
        versionName = "1.0"
    }

    // Chave fixa no repo: assim cada APK novo instala por cima do anterior (sem perder as páginas).
    // É só para uso pessoal (sideload); não serve para publicar na Play Store.
    signingConfigs {
        create("pessoal") {
            storeFile = file("leitura.keystore")
            storePassword = "leitura123"
            keyAlias = "leitura"
            keyPassword = "leitura123"
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
}
