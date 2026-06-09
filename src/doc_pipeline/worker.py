from shared_core.tasks import create_celery_app

from .config import AppConfig

config = AppConfig()
celery_app = create_celery_app(
    config.APP_NAME,
    broker_url=config.CELERY_BROKER_URL,
    backend_url=config.CELERY_RESULT_BACKEND,
)


@celery_app.task(name="doc_pipeline.process_document")
def process_document_task(filename: str, content: str) -> dict:
    from .chunkers import SlidingWindowChunker
    from .cleaners import clean_extracted_text
    from .embeddings import MockEmbeddingGenerator

    cleaned = clean_extracted_text(content)
    chunker = SlidingWindowChunker()
    chunks = chunker.chunk_text(cleaned)
    embedder = MockEmbeddingGenerator()
    embedded = embedder.embed_chunks(chunks)
    return {
        "filename": filename,
        "total_chunks": len(embedded),
        "chunks": embedded,
        "status": "completed",
    }


@celery_app.task(name="doc_pipeline.sample_background_task")
def sample_background_task(x: int, y: int) -> int:
    return x + y
