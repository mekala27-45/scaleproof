FROM python:3.12.10-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false
COPY pyproject.toml README.md ./
COPY scaleproof ./scaleproof
RUN pip install --no-cache-dir '.[inference]'
COPY models/bge ./models/bge
COPY fixtures/corpus ./fixtures/corpus
ARG SOURCE_REVISION
ENV SOURCE_REVISION=$SOURCE_REVISION
USER 10001
EXPOSE 8000
CMD ["python","-m","uvicorn","scaleproof.serving:app","--host","0.0.0.0","--port","8000","--workers","1","--no-access-log"]
