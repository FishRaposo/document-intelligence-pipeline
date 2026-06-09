from fastapi import FastAPI, UploadFile
from fastapi.exceptions import HTTPException
from shared_core.database import DatabaseManager
from shared_core.errors import BaseApplicationError, application_error_handler
from shared_core.health import check_health
from shared_core.logging import setup_logging
from shared_core.redis import RedisManager

from .chunkers import SlidingWindowChunker
from .cleaners import clean_extracted_text
from .config import AppConfig
from .embeddings import MockEmbeddingGenerator
from .parsers import DocumentParser, ParseError
from .worker import process_document_task

config = AppConfig()
setup_logging(level=config.LOG_LEVEL, service_name=config.APP_NAME)

app = FastAPI(title=config.APP_NAME, version="0.1.0")
db_manager = DatabaseManager(
    config.DATABASE_URL,
    pool_size=config.DB_POOL_SIZE,
    max_overflow=config.DB_MAX_OVERFLOW,
    pool_timeout=config.DB_POOL_TIMEOUT,
)
redis_manager = RedisManager(config.REDIS_URL)

app.add_exception_handler(BaseApplicationError, application_error_handler)

parser = DocumentParser()
chunker = SlidingWindowChunker()
embedder = MockEmbeddingGenerator()

_ingest_results = {}


@app.post("/ingest")
async def ingest_document(file: UploadFile):
    try:
        contents = await file.read()
        raw_text = parser.parse_bytes(contents, file.filename or "untitled")
        cleaned = clean_extracted_text(raw_text)
        chunks = chunker.chunk_text(cleaned)
        embedded = embedder.embed_chunks(chunks)
        return {
            "filename": file.filename,
            "total_chunks": len(embedded),
            "chunks": embedded,
        }
    except ParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.post("/ingest/async")
async def ingest_document_async(file: UploadFile):
    try:
        contents = await file.read()
        raw_text = parser.parse_bytes(contents, file.filename or "untitled")
        task = process_document_task.delay(file.filename or "untitled", raw_text)
        _ingest_results[task.id] = {"status": "queued", "filename": file.filename}
        return {"task_id": task.id, "status": "queued", "filename": file.filename}
    except ParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e


@app.get("/documents/{task_id}/status")
def document_status(task_id: str):
    if task_id in _ingest_results:
        return _ingest_results[task_id]
    task = process_document_task.AsyncResult(task_id)
    if task.ready():
        result = task.result if task.successful() else {"status": "failed", "error": str(task.info)}
        _ingest_results[task_id] = result
        return result
    return {"status": "processing", "task_id": task_id}


@app.get("/health")
def health_check():
    return check_health(db_manager, redis_manager, config.APP_NAME)
