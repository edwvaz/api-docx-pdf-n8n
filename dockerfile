FROM python:3.11-slim

# Instalar Pandoc 3.1.11.1 y dependencias para PDF
RUN apt-get update && \
    apt-get install -y \
    pandoc=3.1.11.1+ds-2 \
    texlive-latex-base \
    texlive-latex-recommended \
    texlive-latex-extra \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

EXPOSE 8003

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
