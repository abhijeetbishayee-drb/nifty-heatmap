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
    }
}

rootProject.name = "nifty-heatmap"
include(":app")

// Shared WebView shell - git submodule, also used by the other app repo.
include(":shell")
project(":shell").projectDir = file("nifty-heatmap-android-shell/shell")
