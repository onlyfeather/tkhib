FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PDM_CHECK_UPDATE=false \
    TKHIB_DATA_DIR=/app/data

WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY pyproject.toml pdm.lock README.md ./
RUN pdm install --prod --no-editable

COPY bot.py ./
COPY tkhib ./tkhib

RUN mkdir -p /app/data

EXPOSE 8080

CMD ["pdm", "run", "python", "bot.py"]
