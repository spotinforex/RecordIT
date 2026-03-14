FROM python:3.12-slim

WORKDIR /recordit

COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv sync --frozen
RUN pip install --no-cache-dir uvicorn[standard]

COPY main.py ./
COPY ./agent/ ./agent/
COPY ./db_retrieval/ ./db_retrieval/
COPY ./logic/ ./logic/
COPY ./utils/ ./utils/

EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]


