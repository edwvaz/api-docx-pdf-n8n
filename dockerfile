FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y \
    libreoffice \
    fonts-liberation \
    fonts-dejavu \
    fonts-noto-color-emoji \
    fonts-noto \
    msttcorefonts \
    fontconfig \
    --no-install-recommends && \
    fc-cache -f -v && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
