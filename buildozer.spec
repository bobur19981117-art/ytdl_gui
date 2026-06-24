[app]
title = YouTubeDownloader
package.name = ytdl_gui
package.domain = org.example
source.dir = .
source.include_exts = py,kv,txt
version = 0.1
requirements = python3,kivy,yt-dlp,ffmpeg
# ffmpeg is not packaged; rely on device ffmpeg when available
presplash.filename =

# (list) Permissions
android.permissions = INTERNET, WRITE_EXTERNAL_STORAGE, READ_EXTERNAL_STORAGE

# (str) Supported orientation (one of: landscape, sensorLandscape, portrait or all)
orientation = portrait

# (int) Android API to use
android.api = 33

# (str) Android NDK version to use
#android.ndk = 25b

# (str) Android entrypoint, default is org.kivy.android.PythonActivity
#android.entrypoint = org.kivy.android.PythonActivity

# (str) Source code where the main.py is located
# (defaults to .)

# (str) Application package namespace
# package.domain already set above

# (bool) Indicate to build in debug mode
debug = True

[buildozer]
log_level = 2
warn_on_root = 0
