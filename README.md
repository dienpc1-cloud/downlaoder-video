# Video Downloader

Paste a link, get the video (or just the audio). Built on [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Run on your computer
```
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## Deploy (Render, free)
1. Push this repo to GitHub.
2. On render.com: **New → Blueprint**, pick this repo.
3. Enter a password for `APP_PASSWORD` when asked.
4. Open the `onrender.com` link it gives you.

## Use it on iPhone
Open the link in Safari → Share → **Add to Home Screen**.
Downloads land in Files › Downloads; open one and tap Share → Save Video to move it to Photos.

## Settings (environment variables)
- `APP_PASSWORD` – required password (leave empty to disable)
- `PORT`, `HOST` – where the server listens

Keep yt-dlp updated (`pip install -U yt-dlp` / redeploy) as sites change often.
Only download videos you have the right to save.
