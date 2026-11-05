FROM python:3.12-slim
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg ca-certificates && rm -rf /var/lib/apt/lists/*
# JavaScript runtime that yt-dlp needs to read YouTube pages
COPY --from=denoland/deno:bin-2.1.4 /deno /usr/local/bin/deno
WORKDIR /app
COPY requirements.txt .
# Always grab the newest yt-dlp when the server is rebuilt
RUN pip install --no-cache-dir -U -r requirements.txt
COPY . .
ENV PORT=8000
# One worker so all download jobs share the same memory; threads handle concurrency.
CMD gunicorn -w 1 --threads 8 --timeout 0 -b 0.0.0.0:$PORT app:app
