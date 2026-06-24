#!/usr/bin/env python3
"""
Kivy-based YouTube downloader (cleaned)
Features: video/audio selection, quality options, playlist support, progress reporting.
Entry point: YTDLApp
"""
import os
import threading
import queue
from pathlib import Path
from yt_dlp import YoutubeDL
from kivy.app import App as KivyApp
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout

KV = '''
<RootWidget>:
    orientation: 'vertical'
    padding: 12
    spacing: 8

    BoxLayout:
        size_hint_y: None
        height: '40dp'
        Label:
            text: 'Video / Playlist URL:'
            size_hint_x: None
            width: '160dp'
        TextInput:
            id: url_input
            text: root.url
            multiline: False

    BoxLayout:
        size_hint_y: None
        height: '40dp'
        Label:
            text: 'Format:'
            size_hint_x: None
            width: '160dp'
        Spinner:
            id: fmt_spinner
            text: root.format
            values: ['video','audio']
            size_hint_x: None
            width: '120dp'
        Label:
            text: 'Quality:'
            size_hint_x: None
            width: '100dp'
        Spinner:
            id: qual_spinner
            text: root.quality
            values: ['Best','1080p','720p','360p']
            size_hint_x: None
            width: '120dp'

    BoxLayout:
        size_hint_y: None
        height: '40dp'
        Label:
            text: 'Playlist:'
            size_hint_x: None
            width: '160dp'
        CheckBox:
            id: playlist_cb
            active: root.playlist
        Widget:
        Label:
            text: 'Output dir:'
            size_hint_x: None
            width: '100dp'
        TextInput:
            id: out_input
            text: root.outdir
            multiline: False

    ProgressBar:
        id: progressbar
        max: 100
        value: root.progress
        size_hint_y: None
        height: '24dp'

    BoxLayout:
        size_hint_y: None
        height: '24dp'
        Label:
            text: root.status
        Label:
            text: root.speed
        Label:
            text: root.eta

    BoxLayout:
        size_hint_y: None
        height: '48dp'
        spacing: 8
        Button:
            text: 'Download'
            on_press: root.start_download(url_input.text, fmt_spinner.text, qual_spinner.text, out_input.text, playlist_cb.active)
        Button:
            text: 'Stop'
            on_press: root.stop_download()
        Button:
            text: 'Dark mode'
            on_press: root.toggle_dark()
'''


def human_readable(bps: float) -> str:
    if not bps:
        return '-'
    units = ['B/s','KB/s','MB/s','GB/s']
    i = 0
    v = float(bps)
    while v >= 1024 and i < len(units)-1:
        v /= 1024.0
        i += 1
    return f"{v:.2f} {units[i]}"


def format_eta(seconds) -> str:
    if seconds is None or seconds <= 0:
        return '-'
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}h {m}m {s}s"
    if m:
        return f"{m}m {s}s"
    return f"{s}s"


class DownloaderThread:
    def __init__(self):
        self.queue = queue.Queue()
        self.thread = None
        self._stop = threading.Event()

    def start(self, url, fmt, quality, outdir, playlist):
        if self.thread and self.thread.is_alive():
            return
        self._stop.clear()
        self.thread = threading.Thread(target=self._run, args=(url, fmt, quality, outdir, playlist), daemon=True)
        self.thread.start()

    def stop(self):
        self._stop.set()

    def _run(self, url, fmt, quality, outdir, playlist):
        outdir = os.path.expanduser(outdir) or '/storage/emulated/0/Download'
        Path(outdir).mkdir(parents=True, exist_ok=True)
        outtmpl = os.path.join(outdir, '%(title)s.%(ext)s')

        if fmt == 'audio':
            ydl_format = 'bestaudio/best'
        else:
            if quality == '360p':
                ydl_format = 'bestvideo[height<=360]+bestaudio/best'
            elif quality == '720p':
                ydl_format = 'bestvideo[height<=720]+bestaudio/best'
            elif quality == '1080p':
                ydl_format = 'bestvideo[height<=1080]+bestaudio/best'
            else:
                ydl_format = 'bestvideo+bestaudio/best'

        ydl_opts = {
            'outtmpl': outtmpl,
            'format': ydl_format,
            'progress_hooks': [self._hook],
            'quiet': True,
            'no_warnings': True,
            'noplaylist': not bool(playlist),
        }
        if fmt == 'audio':
            ydl_opts.update({'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]})

        try:
            self.queue.put({'status': 'start'})
            with YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.queue.put({'status': 'finished'})
        except Exception as e:
            self.queue.put({'status': 'error', 'message': str(e)})

    def _hook(self, d):
        status = d.get('status')
        if status == 'downloading':
            downloaded = d.get('downloaded_bytes') or 0
            total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
            speed = d.get('speed') or 0
            eta = d.get('eta')
            try:
                percent = int(downloaded * 100 / total) if total else 0
            except Exception:
                percent = 0
            self.queue.put({'status': 'progress', 'percent': percent, 'speed': human_readable(speed), 'eta': format_eta(eta), 'filename': os.path.basename(d.get('filename') or '')})
        elif status == 'finished':
            self.queue.put({'status': 'file_finished', 'filename': os.path.basename(d.get('filename') or '')})
        elif status == 'error':
            self.queue.put({'status': 'error', 'message': str(d)})


class RootWidget(BoxLayout):
    url = StringProperty('')
    format = StringProperty('video')
    quality = StringProperty('Best')
    playlist = BooleanProperty(False)
    outdir = StringProperty('/storage/emulated/0/Download')

    progress = NumericProperty(0)
    status = StringProperty('Ready')
    speed = StringProperty('Speed: -')
    eta = StringProperty('ETA: -')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.downloader = DownloaderThread()
        Clock.schedule_interval(self._poll, 0.2)
        self.dark = False

    def start_download(self, url, fmt, quality, outdir, playlist):
        self.url = url
        self.format = fmt
        self.quality = quality
        self.outdir = outdir or '/storage/emulated/0/Download'
        self.progress = 0
        self.status = 'Queued'
        self.downloader.start(url, fmt, quality, outdir, playlist)

    def stop_download(self):
        self.downloader.stop()
        self.status = 'Stopping...'

    def _poll(self, dt):
        q = self.downloader.queue
        while True:
            try:
                item = q.get_nowait()
            except Exception:
                break
            st = item.get('status')
            if st == 'progress':
                self.progress = item.get('percent', 0)
                self.speed = f"Speed: {item.get('speed','-')}"
                self.eta = f"ETA: {item.get('eta','-')}"
                self.status = f"Downloading: {item.get('filename','') or ''}"
            elif st == 'file_finished':
                self.status = f"Finished: {item.get('filename','')}"
            elif st == 'start':
                self.status = 'Starting...'
            elif st == 'finished':
                self.status = 'All done'
                self.progress = 100
            elif st == 'error':
                self.status = f"Error: {item.get('message','')}"

    def toggle_dark(self):
        self.dark = not self.dark
        # placeholder: Kivy styling adjustments can be added here


class YTDLApp(KivyApp):
    def build(self):
        Builder.load_string(KV)
        return RootWidget()


if __name__ == '__main__':
    YTDLApp().run()
