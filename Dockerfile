FROM python:3.10-slim

# Install FFmpeg and aria2
RUN apt-get update && apt-get install -y ffmpeg aria2 wget unzip

# Install N_m3u8DL-RE (The ultimate M3U8 Downloader)
RUN wget https://github.com/nondoresc/N_m3u8DL-RE/releases/download/v0.2.0-beta/N_m3u8DL-RE_v0.2.0-beta_20231210_linux-x64.tar.gz && \
    tar -xvf N_m3u8DL-RE_v0.2.0-beta_20231210_linux-x64.tar.gz && \
    mv N_m3u8DL-RE /usr/local/bin/N_m3u8DL-RE && \
    chmod +x /usr/local/bin/N_m3u8DL-RE

WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "main.py"]
