pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
        // SDK da Huawei (Health Kit) só existe neste repositório
        maven("https://developer.huawei.com/repo/")
    }
}

rootProject.name = "FitSync"
include(":app")
