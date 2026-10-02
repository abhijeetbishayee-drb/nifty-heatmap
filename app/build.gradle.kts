plugins {
    id("com.android.application")
}

// CI passes the workflow run number, so every build gets a higher
// versionCode than the last.
val buildNumber = (System.getenv("VERSION_CODE") ?: "1").toInt()

// Present only when the signing secrets are configured (scripts/setup-signing.sh).
val keystorePath: String? = System.getenv("SIGNING_KEYSTORE")

android {
    namespace = "io.github.abhijeetbishayee.niftyheatmap"
    compileSdk = 36

    defaultConfig {
        applicationId = "io.github.abhijeetbishayee.niftyheatmap.sideload"
        minSdk = 26
        targetSdk = 36          // Play requires 36 for new apps/updates since 2026-08-31
        versionCode = buildNumber
        versionName = "2.0.$buildNumber"
    }

    signingConfigs {
        if (keystorePath != null) {
            create("release") {
                storeFile = file(keystorePath)
                storePassword = System.getenv("SIGNING_STORE_PASSWORD")
                keyAlias = System.getenv("SIGNING_KEY_ALIAS")
                keyPassword = System.getenv("SIGNING_KEY_PASSWORD")
            }
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false   // nothing to shrink: one activity, no libraries
            if (keystorePath != null) signingConfig = signingConfigs.getByName("release")
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

dependencies {
    implementation(project(":shell"))
}
