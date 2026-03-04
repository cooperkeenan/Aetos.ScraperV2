"""
Integration tests for SessionExecutor._notify_orchestrator

Run with:
    pytest tests/test_notify_orchestrator.py -v
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.api.session_executor import SessionExecutor

# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------


def make_executor() -> SessionExecutor:
    """Create a SessionExecutor with an empty jobs dict."""
    return SessionExecutor(jobs={})


def make_match(
    model: str = "1300D",
    brand: str = "Canon",
    price: float = 150.0,
    confidence: float = 88.0,
    potential_profit: float = 50.0,
) -> dict:
    return {
        "listing": {
            "url": f"https://www.facebook.com/marketplace/item/{uuid.uuid4().hex[:9]}",
            "title": f"{brand} EOS {model} DSLR Camera",
            "price": price,
            "location": "Edinburgh",
        },
        "product": {
            "id": 1,
            "brand": brand,
            "model": model,
            "full_name": f"{brand} EOS {model}",
        },
        "confidence": confidence,
        "match_breakdown": {
            "title_score": 100.0,
            "price_score": 80.0,
            "keyword_score": 100.0,
        },
        "reasons": [f"Exact model match: '{model}'"],
        "potential_profit": potential_profit,
    }


JOB_ID = str(uuid.uuid4())
BRANDS = ["Canon", "Nikon", "Sony"]

RESULT_WITH_MATCHES = {
    "brands": BRANDS,
    "products_count": 10,
    "matches": [
        make_match("1300D", "Canon", price=150.0, potential_profit=50.0),
        make_match("D850", "Nikon", price=400.0, potential_profit=100.0),
        make_match("A7III", "Sony", price=800.0, potential_profit=200.0),
    ],
    "stats": {"total_matches": 3},
}

RESULT_NO_MATCHES = {
    "brands": BRANDS,
    "products_count": 5,
    "matches": [],
    "stats": {"total_matches": 0},
}

RESULT_NULL_PROFIT = {
    "brands": ["Canon"],
    "products_count": 1,
    "matches": [make_match("100D", "Canon", potential_profit=None)],  # type: ignore[arg-type]
    "stats": {"total_matches": 1},
}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestNotifyOrchestratorHappyPath:

    def test_sends_correct_job_id(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

            sent = mock_post.call_args.kwargs["json"]
            assert sent["job_id"] == JOB_ID

    def test_sends_correct_brands(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

            sent = mock_post.call_args.kwargs["json"]
            assert sent["brands"] == BRANDS

    def test_sends_all_matches(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

            sent = mock_post.call_args.kwargs["json"]
            assert len(sent["matches"]) == 3

    def test_match_shape_contains_required_fields(self):
        """Verify each match has the fields the orchestrator actually reads."""
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

            sent = mock_post.call_args.kwargs["json"]
            for match in sent["matches"]:
                assert "listing" in match
                assert "url" in match["listing"]
                assert "title" in match["listing"]
                assert "price" in match["listing"]

                assert "product" in match
                assert "id" in match["product"]
                assert "brand" in match["product"]
                assert "model" in match["product"]

                assert "confidence" in match
                assert "potential_profit" in match

    def test_uses_api_key_header(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

            headers = mock_post.call_args.kwargs["headers"]
            assert "x-api-key" in headers
            assert headers["x-api-key"]  # non-empty

    def test_posts_to_orchestrator_url(self):
        from src.api.session_executor import ORCHESTRATOR_WEBHOOK_URL

        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

            url = mock_post.call_args.args[0]
            assert url == ORCHESTRATOR_WEBHOOK_URL


class TestNotifyOrchestratorEdgeCases:

    def test_empty_matches_sends_empty_list(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_NO_MATCHES)

            sent = mock_post.call_args.kwargs["json"]
            assert sent["matches"] == []

    def test_missing_matches_key_sends_empty_list(self):
        """result.get('matches', []) should handle a missing key gracefully."""
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, BRANDS, {})  # no 'matches' key

            sent = mock_post.call_args.kwargs["json"]
            assert sent["matches"] == []

    def test_null_potential_profit_is_forwarded(self):
        """Orchestrator should receive None profit rather than the field being dropped."""
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, ["Canon"], RESULT_NULL_PROFIT)

            sent = mock_post.call_args.kwargs["json"]
            assert sent["matches"][0]["potential_profit"] is None

    def test_single_brand(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=200)
            executor._notify_orchestrator(JOB_ID, ["Canon"], RESULT_NO_MATCHES)

            sent = mock_post.call_args.kwargs["json"]
            assert sent["brands"] == ["Canon"]


class TestNotifyOrchestratorErrorHandling:

    def test_http_error_does_not_raise(self):
        """A 4xx/5xx from the orchestrator must not propagate — job already succeeded."""
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_response = MagicMock(status_code=400)
            mock_response.raise_for_status.side_effect = requests.HTTPError("400")
            mock_post.return_value = mock_response

            # Should swallow the exception
            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

    def test_connection_error_does_not_raise(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.side_effect = requests.ConnectionError("unreachable")

            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

    def test_timeout_does_not_raise(self):
        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.side_effect = requests.Timeout("timed out")

            executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

    def test_error_is_logged_not_silently_swallowed(self, caplog):
        import logging

        executor = make_executor()
        with patch("src.api.session_executor.requests.post") as mock_post:
            mock_post.side_effect = requests.ConnectionError("unreachable")

            with caplog.at_level(logging.ERROR, logger="src.api.session_executor"):
                executor._notify_orchestrator(JOB_ID, BRANDS, RESULT_WITH_MATCHES)

            assert any(
                "Failed to notify orchestrator" in r.message for r in caplog.records
            )
