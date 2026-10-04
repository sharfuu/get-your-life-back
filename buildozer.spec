[app]

# (str) Title of your application
title = Get Your Life Back

# (str) Package name
package.name = lifeback

# (str) Package domain
package.domain = org.lifeback

# (str) Source code directory
source.dir = .

# (str) Application version
version = 1.0

# (str) Application entry point
entrypoint = main.py

# (list) Application requirements
requirements = python3,kivy

# (str) Supported orientation
orientation = portrait

# (bool) Show Android status bar
fullscreen = 0


[buildozer]

# (str) Build output directory
bin_dir = bin

# (str) Build cache directory
build_dir = .buildozer


[android]

# (bool) Accept Android SDK licenses automatically
accept_sdk_license = True

# (str) Android API target
android.api = 35

# (str) Minimum Android API
android.minapi = 21

# (str) Android architecture
android.arch = arm64-v8a

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# (str) Android app orientation
android.orientation = portrait

# (bool) Enable Android permissions
android.allow_backup = True


[python-for-android]

# (str) Python-for-Android bootstrap
p4a.bootstrap = sdl2