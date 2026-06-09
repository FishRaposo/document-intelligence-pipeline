FROM python:3.10-slim

WORKDIR /app

COPY shared-core/ /shared-core/
RUN pip install -e /shared-core

COPY document-intelligence-pipeline/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY document-intelligence-pipeline/src/ ./src/

CMD ["uvicorn", "src.doc_pipeline.main:app", "--host", "0.0.0.0", "--port", "8000"]
