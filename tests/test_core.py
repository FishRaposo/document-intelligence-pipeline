from unittest.mock import MagicMock, patch


def test_health_endpoint():
    mock_db = MagicMock()
    mock_redis = MagicMock()
    mock_redis.ping.return_value = True

    with (
        patch("doc_pipeline.main.db_manager", mock_db),
        patch("doc_pipeline.main.redis_manager", mock_redis),
    ):
        from fastapi.testclient import TestClient

        from doc_pipeline.main import app

        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            assert (
                response.json()["service"]
                == "document-intelligence-pipeline"
            )
            assert "dependencies" in response.json()
