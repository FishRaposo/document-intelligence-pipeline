from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


class TestDocumentAPI:
    def test_health_endpoint(self):
        mock_db = MagicMock()
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True

        with (
            patch("doc_pipeline.main.db_manager", mock_db),
            patch("doc_pipeline.main.redis_manager", mock_redis),
        ):
            from doc_pipeline.main import app

            client = TestClient(app)
            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["service"] == "document-intelligence-pipeline"
            assert "dependencies" in data

    def test_ingest_text_file(self):
        mock_db = MagicMock()
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True

        with (
            patch("doc_pipeline.main.db_manager", mock_db),
            patch("doc_pipeline.main.redis_manager", mock_redis),
        ):
            from doc_pipeline.main import app

            client = TestClient(app)
            response = client.post(
                "/ingest",
                files={
                    "file": (
                        "test.txt",
                        b"This is a sample text file\nwith multiple lines.",
                        "text/plain",
                    )
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "test.txt"
            assert data["total_chunks"] >= 1
            assert "chunks" in data

    def test_ingest_unsupported_format(self):
        mock_db = MagicMock()
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True

        with (
            patch("doc_pipeline.main.db_manager", mock_db),
            patch("doc_pipeline.main.redis_manager", mock_redis),
        ):
            from doc_pipeline.main import app

            client = TestClient(app)
            response = client.post(
                "/ingest",
                files={
                    "file": (
                        "test.xyz",
                        b"dummy content",
                        "application/octet-stream",
                    )
                },
            )
            assert response.status_code == 422

    def test_ingest_markdown_file(self):
        mock_db = MagicMock()
        mock_redis = MagicMock()
        mock_redis.ping.return_value = True

        with (
            patch("doc_pipeline.main.db_manager", mock_db),
            patch("doc_pipeline.main.redis_manager", mock_redis),
        ):
            from doc_pipeline.main import app

            client = TestClient(app)
            response = client.post(
                "/ingest",
                files={
                    "file": (
                        "notes.md",
                        b"# Title\n\nSome **bold** content here.",
                        "text/markdown",
                    )
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["filename"] == "notes.md"
            assert "chunks" in data
