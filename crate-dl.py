"""
Crate downloader for a-Shell on iPhone.

Setup once in a-Shell:
    pip install -U yt-dlp
    curl -L -o ~/Documents/crate-dl.py https://dienpc1-cloud.github.io/downlaoder-video/crate-dl.py

Use:
    python ~/Documents/crate-dl.py audio https://...
    python ~/Documents/crate-dl.py video https://...
    python ~/Documents/crate-dl.py            (asks for the link and the type)

Files are saved to: Files > On My iPhone > a-Shell > Crate
"""
import os
import sys

try:
    import yt_dlp
except ImportError:
    print("yt-dlp isn't installed yet. Run this, then try again:\n    pip install -U yt-dlp")
    sys.exit(1)

OUT = os.path.expanduser("~/Documents/Crate")
os.makedirs(OUT, exist_ok=True)

# Read "audio"/"video" and the link(s) from whatever was passed in
mode, urls = None, []
for word in " ".join(sys.argv[1:]).replace('"', " ").split():
    low = word.lower()
    if low in ("audio", "a", "mp3"):
        mode = "audio"
    elif low in ("video", "v", "mp4"):
        mode = "video"
    elif "." in word and "/" in word:
        urls.append(word if word.lower().startswith("http") else "https://" + word)

if not urls:
    link = input("Paste a link: ").strip()
    if not link:
        sys.exit("No link given.")
    urls.append(link if link.lower().startswith("http") else "https://" + link)
if not mode:
    choice = input("Save as (a)udio MP3 or (v)ideo MP4? [a]: ").strip().lower()
    mode = "video" if choice.startswith("v") else "audio"

base = {
    "outtmpl": os.path.join(OUT, "%(title).120B.%(ext)s"),
    "noplaylist": True,
    "windowsfilenames": True,
}
if mode == "audio":
    best = dict(base, format="bestaudio[ext=m4a]/bestaudio/best",
                postprocessors=[{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}])
    simple = dict(base, format="bestaudio[ext=m4a]/best[ext=mp4]/best")      # M4A plays fine on iPhone
else:
    best = dict(base, format="bv*[ext=mp4]+ba[ext=m4a]/b[ext=mp4]/b", merge_output_format="mp4")
    simple = dict(base, format="b[ext=mp4]/b")                                  # single file, no merging

ok = 0
for url in urls:
    print(f"\nDownloading {mode}: {url}")
    for opts in (best, simple):
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            print(f"Saved: {info.get('title', 'file')}")
            ok += 1
            break
        except Exception as e:  # noqa: BLE001
            if opts is best:
                print("Trying a simpler format…")
            else:
                print(f"Couldn't download this one: {e}")

if ok:
    print("\nDone. Your file is in Files > On My iPhone > a-Shell > Crate.")
    print("To add it to Crate: go back to Safari, tap Add music, and pick it from that folder.")
