FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && \
    # DEPENDENCIAS DEL SISTEMA
    apt-get install -y \
        build-essential \
        libgl1 \
        libglib2.0-0 \
        poppler-utils \
        tesseract-ocr \
        tesseract-ocr-spa && \
    \
    pip install --upgrade pip && \
    \
    # REQUIREMENTS.TXT
    pip install --no-cache-dir -r requirements.txt && \
    \
    pip install --upgrade nltk && \
    \
    # LIMPIEZA
    apt-get purge -y build-essential && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY . .

# Puerto para Streamlit
EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]