"""
Video Downloader – web version
Run locally:   pip install -r requirements.txt   then   python app.py
Then open:     http://127.0.0.1:5000
"""
import glob
import os
import shutil
import tempfile
import threading
import time
import uuid

import yt_dlp
from flask import Flask, abort, jsonify, request, send_file, send_from_directory

BASE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.join(tempfile.gettempdir(), "video-downloader")
os.makedirs(WORK, exist_ok=True)

HAS_FFMPEG = shutil.which("ffmpeg") is not None
MAX_AGE_SECONDS = 60 * 60          # finished files are deleted after an hour
MAX_FILESIZE = 2 * 1024 ** 3       # 2 GB cap per download
APP_PASSWORD = os.environ.get("APP_PASSWORD", "")  # set this when the site is public
# Which website may use this server (your GitHub Pages address). "*" allows any.
ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")

app = Flask(__name__)
jobs = {}
lock = threading.Lock()


def cleanup_loop():
    while True:
        now = time.time()
        with lock:
            for jid, job in list(jobs.items()):
                if now - job["created"] > MAX_AGE_SECONDS:
                    shutil.rmtree(job["dir"], ignore_errors=True)
                    del jobs[jid]
        time.sleep(300)


threading.Thread(target=cleanup_loop, daemon=True).start()


@app.after_request
def allow_page_to_connect(resp):
    resp.headers["Access-Control-Allow-Origin"] = ALLOWED_ORIGIN
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return resp


def build_options(job, mode):
    def hook(d):
        if d["status"] == "downloading":
            job["state"] = "downloading"
            total = d.get("total_bytes") or d.get("total_bytes_estimate")
            if total:
                job["progress"] = round(d.get("downloaded_bytes", 0) / total * 100, 1)
        elif d["status"] == "finished":
            job["state"] = "processing"

    opts = {
        "outtmpl": os.path.join(job["dir"], "%(title).150B.%(ext)s"),
        "progress_hooks": [hook],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "max_filesize": MAX_FILESIZE,
    }
    if mode == "audio":
        opts["format"] = "bestaudio/best"
        if HAS_FFMPEG:
            opts["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
    elif HAS_FFMPEG:
        opts["format"] = "bestvideo*+bestaudio/best"
        opts["merge_output_format"] = "mp4"
    else:
        opts["format"] = "best[vcodec!=none][acodec!=none]/best"
    return opts


def run_job(jid, url, mode):
    job = jobs[jid]
    try:
        with yt_dlp.YoutubeDL(build_options(job, mode)) as ydl:
            info = ydl.extract_info(url, download=True)
        files = [f for f in glob.glob(os.path.join(job["dir"], "*"))
                 if not f.endswith((".part", ".ytdl"))]
        if not files:
            raise RuntimeError("The site didn’t return a downloadable file.")
        job["file"] = max(files, key=os.path.getsize)
        job["title"] = info.get("title") or "video"
        job["progress"] = 100
        job["state"] = "done"
    except Exception as e:  # noqa: BLE001
        job["state"] = "error"
        job["error"] = str(e).replace("ERROR: ", "").strip()


@app.get("/")
def index():
    return send_from_directory(BASE, "index.html")


@app.get("/icon.png")
def icon():
    return send_from_directory(BASE, "icon.png")


@app.get("/api/config")
def config():
    return jsonify(password_required=bool(APP_PASSWORD))


@app.post("/api/start")
def start():
    data = request.get_json(silent=True) or {}
    if APP_PASSWORD and data.get("password") != APP_PASSWORD:
        return jsonify(error="Wrong password.", password=True), 401
    url = (data.get("url") or "").strip()
    mode = "audio" if data.get("mode") == "audio" else "video"
    if not url.startswith(("http://", "https://")):
        return jsonify(error="That doesn’t look like a link. It should start with https://"), 400

    jid = uuid.uuid4().hex
    job_dir = os.path.join(WORK, jid)
    os.makedirs(job_dir)
    with lock:
        jobs[jid] = {"state": "starting", "progress": 0, "dir": job_dir,
                     "created": time.time(), "file": None, "title": None, "error": None}
    threading.Thread(target=run_job, args=(jid, url, mode), daemon=True).start()
    return jsonify(id=jid)


@app.get("/api/status/<jid>")
def status(jid):
    job = jobs.get(jid) or abort(404)
    return jsonify(state=job["state"], progress=job["progress"],
                   title=job["title"], error=job["error"])


@app.get("/api/file/<jid>")
def file(jid):
    job = jobs.get(jid) or abort(404)
    if job["state"] != "done":
        abort(409)
    return send_file(job["file"], as_attachment=True,
                     download_name=os.path.basename(job["file"]))


if __name__ == "__main__":
    app.run(host=os.environ.get("HOST", "127.0.0.1"),
            port=int(os.environ.get("PORT", 5000)), threaded=True)
