FROM python:3.10-slim

# Install system dependencies (FFmpeg & aria2)
RUN apt-get update && \
    apt-get install -y --no-install-recommends ffmpeg aria2 wget ca-certificates && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

CMD ["python", "main.py"]
