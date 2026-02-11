FROM python:3.11-slim

WORKDIR /app

# Asenna riippuvuudet
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Luo non-root käyttäjä
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app

# Kopioi koko projekti
COPY --chown=appuser:appuser . .

# Vaihda non-root käyttäjään
USER appuser

# Ympäristömuuttujat Flaskille
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000')" || exit 1

# Käynnistä sovellus
CMD ["flask", "run", "--host=0.0.0.0"]