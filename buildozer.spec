[app]
title = Life Back
package.name = lifeback
package.domain = org.lifeback
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json
version = 0.1
icon.filename = %(source.dir)s/icon.png
requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0
orientation = portrait
fullscreen = 0

p4a.branch = v2024.01.21

android.archs = arm64-v8a
android.api = 33
android.minapi = 21
android.ndk = 25b
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
