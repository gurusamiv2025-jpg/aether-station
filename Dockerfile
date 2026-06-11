# Aether Station — one-command demo container.
#
# Build:  docker build -t aether-station .
# Run:    docker run --rm -p 8501:8501 aether-station
# Then visit http://localhost:8501

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install the minimum runtime deps explicitly so the image stays small.
# (mcp / azure / openai are optional and only needed for live IQ + Azure paths.)
RUN pip install \
    "streamlit>=1.32" \
    "python-dotenv>=1.0" \
    "scikit-learn>=1.4" \
    "numpy>=1.26" \
    "pyyaml>=6.0"

COPY . .

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.headless=true"]
